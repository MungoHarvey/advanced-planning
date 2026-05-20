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

    Returns
    -------
    Path
        Absolute path to the written file.
    """
    payload: dict[str, Any] = {
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

    if not old_phase or old_phase == current_phase:
        # Phase matches or field absent -- nothing to archive.
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
