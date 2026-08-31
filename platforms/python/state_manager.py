"""
state_manager.py — Filesystem state bus for the planning system
===============================================================

Manages the three state files that coordinate orchestrator and worker:

  loop-ready.json     — written by orchestrator; read by worker as assignment
  loop-complete.json  — written by worker; read by main thread to advance state
  history.jsonl       — append-only log of all loop completions

All functions accept a ``state_dir`` parameter (pathlib.Path or str) pointing
to the directory that contains these files. The directory is created if absent.

Typical usage::

    from pathlib import Path
    from platforms.python.state_manager import write_loop_ready, read_loop_complete

    state = Path(".advanced-plans/state")
    write_loop_ready(state, loop_name="ralph-loop-001",
                     loop_file=".advanced-plans/phases/phase-1/loops.md",
                     task_name="Schema Definitions", todos_count=4)
    result = read_loop_complete(state)
    print(result["status"])  # "completed"
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ── Internal helpers ───────────────────────────────────────────────────────────

def _state_path(state_dir: Path | str, filename: str) -> Path:
    """Return an absolute path for a state file, creating the directory if needed."""
    d = Path(state_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d / filename


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ── loop-ready.json ────────────────────────────────────────────────────────────

def write_loop_ready(
    state_dir: Path | str,
    *,
    loop_name: str,
    loop_file: str,
    task_name: str,
    todos_count: int,
    handoff_done: str = "",
    handoff_failed: str = "",
    handoff_needed: str = "",
    phase: str | None = None,
) -> Path:
    """Write ``loop-ready.json`` to signal the worker that a loop is prepared.

    Parameters
    ----------
    state_dir:
        Directory where state files live (created if absent).
    loop_name:
        Loop identifier, e.g. ``"ralph-loop-001"``.
    loop_file:
        Workspace-relative path to the loop plan file, e.g.
        ``.advanced-plans/phases/phase-1/loops.md``.
    task_name:
        Human-readable name for this loop.
    todos_count:
        Number of pending todos the worker should expect.
    handoff_done:
        ``done`` field from the prior loop's handoff_summary (empty string if none).
    handoff_failed:
        ``failed`` field from the prior loop's handoff_summary.
    handoff_needed:
        ``needed`` field from the prior loop's handoff_summary.
    phase:
        Explicit phase identifier (e.g. ``"phase-16"``). If not provided, derived
        from ``loop_file`` (the directory name under ``phases/``). If the path does
        not match the expected shape and no explicit phase is given, raises.

    Returns
    -------
    Path
        Absolute path to the written file.

    Raises
    ------
    ValueError
        If ``phase`` is not provided and ``loop_file`` does not contain a
        ``phase-N`` segment, since a state file without a phase cannot be
        shown to belong to any phase.
    """
    # Derive phase from loop_file if not explicitly provided
    if phase is None:
        phase_match = re.search(r"phases/(phase-\d+)/", loop_file.replace("\\", "/"))
        if phase_match:
            phase = phase_match.group(1)
        else:
            raise ValueError(
                f"loop_file {loop_file!r} does not contain a phase-N segment; "
                "an explicit phase= keyword must be provided"
            )
    
    payload: dict[str, Any] = {
        "phase": phase,
        "loop_name": loop_name,
        "loop_file": loop_file,
        "task_name": task_name,
        "todos_count": todos_count,
        "prepared_at": _now_iso(),
        "status": "ready",
        "handoff_injected": {
            "done": handoff_done,
            "failed": handoff_failed,
            "needed": handoff_needed,
        },
    }
    path = _state_path(state_dir, "loop-ready.json")
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def prepare_loop_ready(
    loops_md_path: Path | str,
    prior_handoff: dict[str, str],
    state_dir: Path | str = ".advanced-plans/state",
) -> dict[str, Any]:
    """Parse a loops.md file and write ``loop-ready.json`` for the first pending loop.

    Applies a conservative *populated predicate*: the loop's ``todos[]`` must be
    non-empty AND every todo must have non-empty ``id``, ``content``, ``outcome``,
    and a ``status`` field.  If the predicate fails the file is **not** written.

    The ``phase`` field is derived from the loops.md path (e.g.
    ``…/phases/phase-16/loops.md`` → ``"phase-16"``).  If the path does not
    contain a ``phase-N`` segment the field is set to ``"unknown"``.

    Parameters
    ----------
    loops_md_path:
        Path to a ``loops.md`` file containing one or more loop YAML blocks.
    prior_handoff:
        Dict with keys ``done``, ``failed``, ``needed`` from the previous loop's
        handoff_summary.  Missing keys are filled with empty strings.
    state_dir:
        Directory where state files live (created if absent).

    Returns
    -------
    dict
        One of three shapes:

        ``{"ok": True, "loop_ready": <dict>}``
            Loop was populated; ``loop-ready.json`` has been written.

        ``{"ok": False, "reason": "all_complete"}``
            No loop with any pending todos was found in the file.

        ``{"ok": False, "reason": "agent_needed", "loop_name": <str>}``
            First pending loop was found but failed the populated predicate;
            ``loop-ready.json`` was **not** written.
    """
    # ── Inline minimal YAML parsing (mirrors plan_io._parse_simple_yaml_block) ──
    _LOOP_BLOCK_RE = re.compile(
        r"```yaml\n(?P<yaml_block>.*?)```",
        re.DOTALL,
    )
    _NAME_RE = re.compile(r'^name:\s*"?(?P<name>[^"\n]+)"?', re.MULTILINE)
    _TASK_RE = re.compile(r'^task_name:\s*"?(?P<v>[^"\n]+)"?', re.MULTILINE)

    def _parse_todos_inline(yaml_text: str) -> list[dict[str, str]]:
        """Extract the todos[] array from a YAML block."""
        todos: list[dict[str, str]] = []
        lines = yaml_text.splitlines()
        in_todos = False
        current: dict[str, str] = {}
        for line in lines:
            if re.match(r"^todos:\s*$", line):
                in_todos = True
                continue
            if in_todos:
                stripped = line.strip()
                if not stripped:
                    continue
                # Exit todos block when we hit an unindented non-list line
                if line and not line.startswith(" ") and not line.startswith("\t") and not stripped.startswith("-"):
                    break
                if stripped.startswith("- id:"):
                    if current:
                        todos.append(current)
                    current = {}
                    m = re.match(r'-\s+id:\s*"?([^"]+)"?', stripped)
                    if m:
                        current["id"] = m.group(1)
                elif stripped and not stripped.startswith("-") and current is not None:
                    m = re.match(r'(\w[\w_]*):\s*"?(.*?)"?\s*$', stripped)
                    if m:
                        current[m.group(1)] = m.group(2)
        if current:
            todos.append(current)
        return todos

    def _populated(todos: list[dict[str, str]]) -> bool:
        """Return True if todos is non-empty and every todo has the required fields."""
        if not todos:
            return False
        required = {"id", "content", "outcome", "status"}
        for todo in todos:
            for field in required:
                if not todo.get(field, "").strip():
                    return False
        return True

    # ── Derive phase from path ────────────────────────────────────────────────
    loops_md_path = Path(loops_md_path)
    phase_match = re.search(r"(phase-\d+)", str(loops_md_path).replace("\\", "/"))
    phase = phase_match.group(1) if phase_match else "unknown"
    # Relative loop_file for portability (forward-slash)
    try:
        loop_file_rel = loops_md_path.as_posix()
    except Exception:
        loop_file_rel = str(loops_md_path).replace("\\", "/")

    # ── Normalise prior_handoff ───────────────────────────────────────────────
    handoff: dict[str, str] = {
        "done": prior_handoff.get("done", "") or "",
        "failed": prior_handoff.get("failed", "") or "",
        "needed": prior_handoff.get("needed", "") or "",
    }

    # ── Scan loops in document order ─────────────────────────────────────────
    content = loops_md_path.read_text(encoding="utf-8")
    first_pending_loop_name: str | None = None
    first_pending_loop_task: str = ""
    first_pending_todos: list[dict[str, str]] = []

    for block_match in _LOOP_BLOCK_RE.finditer(content):
        yaml_block = block_match.group("yaml_block")
        name_m = _NAME_RE.search(yaml_block)
        if not name_m:
            continue
        loop_name = name_m.group("name").strip()
        todos = _parse_todos_inline(yaml_block)
        done_statuses = {"completed", "cancelled"}
        # A loop is "fully done" only when it has at least one todo AND every
        # todo is completed or cancelled.  An empty todos[] is an unpopulated
        # stub — it counts as "needs work" (not done).
        all_done = (
            len(todos) > 0
            and all(t.get("status", "") in done_statuses for t in todos)
        )
        if all_done:
            continue  # This loop is complete — skip
        # Found a loop that needs work (empty stub or has pending todos)
        task_m = _TASK_RE.search(yaml_block)
        first_pending_loop_name = loop_name
        first_pending_loop_task = task_m.group("v").strip() if task_m else ""
        first_pending_todos = todos
        break

    if first_pending_loop_name is None:
        return {"ok": False, "reason": "all_complete"}

    # Filter to only pending todos for the count and predicate check
    pending_todos = [t for t in first_pending_todos if t.get("status") == "pending"]

    if not _populated(pending_todos):
        return {
            "ok": False,
            "reason": "agent_needed",
            "loop_name": first_pending_loop_name,
        }

    # ── Build and write loop-ready.json ──────────────────────────────────────
    payload: dict[str, Any] = {
        "phase": phase,
        "loop_name": first_pending_loop_name,
        "loop_file": loop_file_rel,
        "task_name": first_pending_loop_task,
        "todos_count": len(pending_todos),
        "prepared_at": _now_iso(),
        "status": "ready",
        "handoff_injected": handoff,
    }
    path = _state_path(state_dir, "loop-ready.json")
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"ok": True, "loop_ready": payload}


def read_loop_ready(state_dir: Path | str) -> Optional[dict[str, Any]]:
    """Read ``loop-ready.json`` and return its contents as a dict.

    Returns ``None`` if the file does not exist.
    """
    path = _state_path(state_dir, "loop-ready.json")
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# ── loop-complete.json ─────────────────────────────────────────────────────────

def write_loop_complete(
    state_dir: Path | str,
    *,
    loop_name: str,
    loop_file: str,
    status: str,
    todos_done: int,
    todos_failed: int,
    handoff_done: str,
    handoff_failed: str,
    handoff_needed: str,
    duration_seconds: Optional[float] = None,
) -> Path:
    """Write ``loop-complete.json`` to signal loop completion to the main thread.

    Parameters
    ----------
    state_dir:
        Directory where state files live.
    loop_name:
        Loop identifier matching the one in ``loop-ready.json``.
    loop_file:
        Workspace-relative path to the loop plan file.
    status:
        One of ``"completed"``, ``"partial"``, or ``"failed"``.
    todos_done:
        Count of todos with ``status: completed``.
    todos_failed:
        Count of todos with ``status: cancelled``.
    handoff_done:
        What was completed — artefact-focused, one sentence.
    handoff_failed:
        What failed and why. Empty string if nothing failed.
    handoff_needed:
        Precise first action for the next loop. Empty string if fully done.
    duration_seconds:
        Optional elapsed seconds since worker start.

    Returns
    -------
    Path
        Absolute path to the written file.
    """
    if status not in ("completed", "partial", "failed"):
        raise ValueError(f"Invalid status {status!r}; expected completed|partial|failed")

    payload: dict[str, Any] = {
        "loop_name": loop_name,
        "loop_file": loop_file,
        "status": status,
        "todos_done": todos_done,
        "todos_failed": todos_failed,
        "completed_at": _now_iso(),
        "handoff": {
            "done": handoff_done,
            "failed": handoff_failed,
            "needed": handoff_needed,
        },
    }
    if duration_seconds is not None:
        payload["duration_seconds"] = duration_seconds

    path = _state_path(state_dir, "loop-complete.json")
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def read_loop_complete(state_dir: Path | str) -> Optional[dict[str, Any]]:
    """Read ``loop-complete.json`` and return its contents as a dict.

    Returns ``None`` if the file does not exist.
    """
    path = _state_path(state_dir, "loop-complete.json")
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# ── history.jsonl ──────────────────────────────────────────────────────────────

def append_history(state_dir: Path | str, record: dict[str, Any]) -> Path:
    """Append a JSON record to ``history.jsonl`` (one JSON object per line).

    Parameters
    ----------
    state_dir:
        Directory where state files live.
    record:
        A dict to serialise as a single JSON line. A ``recorded_at`` timestamp
        is added automatically if not already present.

    Returns
    -------
    Path
        Absolute path to the history file.
    """
    if "recorded_at" not in record:
        record = {**record, "recorded_at": _now_iso()}

    path = _state_path(state_dir, "history.jsonl")
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return path


def read_history(state_dir: Path | str) -> list[dict[str, Any]]:
    """Read all records from ``history.jsonl`` and return as a list of dicts.

    Returns an empty list if the file does not exist.
    """
    path = _state_path(state_dir, "history.jsonl")
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


# ── Stale-state cleanup (S9) ──────────────────────────────────────────────────

def archive_cross_phase_state(
    state_dir: Path | str,
    current_phase: str,
) -> Optional[Path]:
    """Archive loop-ready.json (and loop-complete.json if present) when they
    belong to a phase other than ``current_phase``.

    Called by the orchestrator at startup (Step 0 of the stale-state cleanup
    protocol documented in core/agents/orchestrator.md).

    A state file with no ``phase`` field (or an empty one) cannot be shown to
    belong to this phase, so it is archived as stale.

    Parameters
    ----------
    state_dir:
        Directory where state files live.
    current_phase:
        The phase currently active, e.g. ``"phase-11"``.  Read from
        ``.advanced-plans/PLANNING.md`` ``current_phase`` frontmatter field.

    Returns
    -------
    Path or None
        If archiving occurred: path to the archived loop-ready.json file.
        If no archiving was needed (phase matches or no loop-ready.json):
        returns ``None``.
    """
    d = Path(state_dir)
    ready_path = d / "loop-ready.json"

    if not ready_path.exists():
        return None

    data = json.loads(ready_path.read_text(encoding="utf-8"))
    old_phase = data.get("phase", "")

    # A missing or empty phase field means the file cannot be shown to belong
    # to this phase — archive it as stale.
    if not old_phase:
        # Phase field absent or empty — treat as stale and archive
        pass  # Continue to archive
    elif old_phase == current_phase:
        # Phase matches — this is the current phase's file, do not archive
        return None

    # Build archive directory and timestamp.
    archive_dir = d / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")  # noqa: DTZ005

    # Archive loop-ready.json.
    archived_ready = archive_dir / f"{old_phase}-{ts}-loop-ready.json"
    ready_path.rename(archived_ready)

    # Archive loop-complete.json if present.
    complete_path = d / "loop-complete.json"
    if complete_path.exists():
        archived_complete = archive_dir / f"{old_phase}-{ts}-loop-complete.json"
        complete_path.rename(archived_complete)

    return archived_ready


# ── Resume detection (S8 IRON RULE) ───────────────────────────────────────────

def detect_mid_loop_death(state_dir: Path | str, dirty: bool) -> bool:
    """Detect the Loop-035 failure mode: worker died mid-loop.

    Returns True if BOTH of the following conditions hold:
    - ``loop-ready.json`` exists AND its mtime is strictly newer than
      ``loop-complete.json`` mtime (or loop-complete.json is absent)
    - ``dirty`` is True (the working tree has uncommitted changes)

    When True, ``/next-loop`` must invoke resume-review and require operator
    acknowledgment before spawning a new orchestrator.

    Parameters
    ----------
    state_dir:
        Directory where state files live.
    dirty:
        Whether the git working tree has uncommitted changes.  The caller
        (the ``/next-loop`` command) is responsible for determining this
        (e.g. by running ``git status --porcelain``).

    Returns
    -------
    bool
        True if mid-loop death is suspected, False if state is clean.
    """
    d = Path(state_dir)
    ready_path = d / "loop-ready.json"
    complete_path = d / "loop-complete.json"

    if not ready_path.exists():
        # No loop-ready at all — state bus is clean.
        return False

    ready_mtime = ready_path.stat().st_mtime
    if complete_path.exists():
        complete_mtime = complete_path.stat().st_mtime
        ready_is_newer = ready_mtime > complete_mtime
    else:
        # loop-complete.json absent means no loop ever finished — treat as
        # potentially stale if working tree is dirty.
        ready_is_newer = True

    return ready_is_newer and dirty


# ── Status query ───────────────────────────────────────────────────────────────

def get_status(state_dir: Path | str) -> dict[str, Any]:
    """Return a summary of the current state bus contents.

    Returns a dict with keys:
    - ``has_loop_ready`` (bool)
    - ``has_loop_complete`` (bool)
    - ``loop_ready`` (dict or None)
    - ``loop_complete`` (dict or None)
    - ``history_count`` (int)
    """
    ready = read_loop_ready(state_dir)
    complete = read_loop_complete(state_dir)
    history = read_history(state_dir)
    return {
        "has_loop_ready": ready is not None,
        "has_loop_complete": complete is not None,
        "loop_ready": ready,
        "loop_complete": complete,
        "history_count": len(history),
    }
