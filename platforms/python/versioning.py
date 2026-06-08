"""
versioning.py — Versioned retry and failure context utilities for the planning system
======================================================================================

Provides functions for creating versioned retry loop files, writing gate failure
context to the worker-only retry sidecar, querying the active loop file for a
phase, and freezing loop files when a phase fails gate review.

These utilities are called by /next-phase when a gate review returns ``fail``.

Typical usage::

    from pathlib import Path
    from platforms.python.versioning import (
        create_retry_version,
        inject_failure_context,
        get_active_version,
        freeze_loop_file,
    )

    plans = Path("plans")
    new_file = create_retry_version(plans / "phase-2-ralph-loops.md", attempt_number=2)
    inject_failure_context(new_file, verdict={"attempt": 1, "verdict_file": "...", ...})
    freeze_loop_file(plans / "phase-2-ralph-loops.md")
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ── Internal helpers ───────────────────────────────────────────────────────────

_VERSION_SUFFIX_RE = re.compile(r"-v\d+$")
"""Matches a trailing -vN suffix on a loop file stem (without the .md extension)."""


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _strip_version_suffix(stem: str) -> str:
    """Remove a trailing -vN suffix from a file stem, if present."""
    return _VERSION_SUFFIX_RE.sub("", stem)


# ── create_retry_version ───────────────────────────────────────────────────────

def create_retry_version(loop_file: Path | str, *, attempt_number: int) -> Path:
    """Create a versioned copy of a loop file for a retry attempt.

    Given ``.advanced-plans/phases/phase-2/loops.md`` and
    ``attempt_number=2``, creates ``loops-v2.md`` in the same phase
    directory. Any existing
    ``-vN`` suffix on the source file is stripped before the new version
    suffix is appended, so re-versioning a versioned file works correctly.

    Parameters
    ----------
    loop_file:
        Path to the source loop file (e.g. ``.advanced-plans/phases/phase-2/loops.md``).
    attempt_number:
        Version number to append, e.g. ``2`` yields ``-v2``. Must be >= 2
        (version 1 is the original unversioned file).

    Returns
    -------
    Path
        Absolute path to the newly created versioned file.

    Raises
    ------
    FileNotFoundError
        If ``loop_file`` does not exist.
    ValueError
        If ``attempt_number`` is less than 2.
    """
    if attempt_number < 2:
        raise ValueError(
            f"attempt_number must be >= 2; got {attempt_number!r}. "
            "Version 1 is the original unversioned file."
        )

    source = Path(loop_file)
    if not source.exists():
        raise FileNotFoundError(f"Loop file not found: {source}")

    base_stem = _strip_version_suffix(source.stem)
    versioned_name = f"{base_stem}-v{attempt_number}{source.suffix}"
    dest = source.parent / versioned_name

    dest.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return dest.resolve()


# ── inject_failure_context ─────────────────────────────────────────────────────

def inject_failure_context(loop_file: Path | str, *, verdict: dict[str, Any]) -> Path:
    """Write gate failure context to the worker-only ``retry-context.json`` sidecar.

    Writes the failure context as a JSON file at
    ``<loop_file_parent>/retry-context.json`` — the phase directory for the
    given loop file.  This is the worker-only sidecar channel: re-gate agents
    never read it (blindness by omission), while re-run workers and focused-fix
    agents read it directly.

    The function does **not** modify ``loop_file`` or any other Markdown file.

    Parameters
    ----------
    loop_file:
        Path to the loop file whose **parent directory** is the phase directory
        where ``retry-context.json`` will be written (e.g.
        ``.advanced-plans/phases/phase-2/loops.md`` → writes to
        ``.advanced-plans/phases/phase-2/retry-context.json``).
    verdict:
        Dict matching the gate-failure-context schema. Expected keys:
        ``attempt`` (int), ``verdict_file`` (str), ``summary`` (str),
        ``loops_reverted`` (list of dicts with ``loop`` and ``reason``),
        ``do_not_repeat`` (list of str).

    Returns
    -------
    Path
        Absolute path to the written ``retry-context.json`` file.

    Raises
    ------
    FileNotFoundError
        If ``loop_file`` does not exist.
    """
    path = Path(loop_file)
    if not path.exists():
        raise FileNotFoundError(f"Loop file not found: {path}")

    context = {
        "attempt": verdict.get("attempt", 1),
        "verdict_file": verdict.get("verdict_file", ""),
        "summary": verdict.get("summary", ""),
        "loops_reverted": verdict.get("loops_reverted", []),
        "do_not_repeat": verdict.get("do_not_repeat", []),
    }

    sidecar = path.parent / "retry-context.json"
    sidecar.write_text(json.dumps(context, indent=2), encoding="utf-8")
    return sidecar.resolve()


# ── get_active_version ─────────────────────────────────────────────────────────

# Matches a markdown table row: | phase | loop_file | other columns... |
_TABLE_ROW_RE = re.compile(
    r"^\|\s*(?P<phase>[^|]+?)\s*\|\s*(?P<loop_file>[^|]+?)\s*\|",
    re.MULTILINE,
)


def get_active_version(plans_index: Path | str, *, phase: str) -> Optional[str]:
    """Return the active loop file path for a phase from PLANS-INDEX.md.

    Reads a PLANS-INDEX.md file and searches its markdown table for a row
    matching ``phase``. Returns the loop file path in the second column, or
    ``None`` if the phase is not found.

    Parameters
    ----------
    plans_index:
        Path to the PLANS-INDEX.md file.
    phase:
        Phase identifier to search for (e.g. ``"phase-2"``). Compared
        case-insensitively after stripping whitespace.

    Returns
    -------
    str or None
        The loop file path from the table, or None if not found.

    Raises
    ------
    FileNotFoundError
        If ``plans_index`` does not exist.
    """
    path = Path(plans_index)
    if not path.exists():
        raise FileNotFoundError(f"Plans index not found: {path}")

    content = path.read_text(encoding="utf-8")
    phase_lower = phase.strip().lower()

    for m in _TABLE_ROW_RE.finditer(content):
        row_phase = m.group("phase").strip().lower()
        # Skip header separator rows (e.g. "---" or ":---:")
        if re.match(r"^[-:]+$", row_phase):
            continue
        if row_phase == phase_lower:
            loop_file = m.group("loop_file").strip()
            # Skip header rows like "Loop File" or "File"
            if re.match(r"^[-:]+$", loop_file) or loop_file.lower() in (
                "loop file", "file", "loop_file"
            ):
                continue
            return loop_file if loop_file else None

    return None


# ── freeze_loop_file ───────────────────────────────────────────────────────────

_FREEZE_RE = re.compile(r"\bstatus:\s*(pending|in_progress)\b")


def freeze_loop_file(loop_file: Path | str) -> Path:
    """Replace all pending and in_progress todo statuses with frozen.

    Uses direct regex substitution to replace every occurrence of
    ``status: pending`` and ``status: in_progress`` with ``status: frozen``.
    Leaves ``status: completed`` and ``status: cancelled`` unchanged.
    Does not use ``plan_io.update_todo_status()``.

    Parameters
    ----------
    loop_file:
        Path to the loop Markdown file to modify in-place.

    Returns
    -------
    Path
        Absolute path to the modified file.

    Raises
    ------
    FileNotFoundError
        If ``loop_file`` does not exist.
    """
    path = Path(loop_file)
    if not path.exists():
        raise FileNotFoundError(f"Loop file not found: {path}")

    content = path.read_text(encoding="utf-8")
    new_content = _FREEZE_RE.sub("status: frozen", content)
    path.write_text(new_content, encoding="utf-8")
    return path.resolve()
