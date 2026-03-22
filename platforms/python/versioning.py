"""
versioning.py — Versioned retry and failure context utilities for the planning system
======================================================================================

Provides functions for creating versioned retry loop files, injecting gate failure
context into frontmatter, querying the active loop file for a phase, and freezing
loop files when a phase fails gate review.

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

    Given ``phase-2-ralph-loops.md`` and ``attempt_number=2``, creates
    ``phase-2-ralph-loops-v2.md`` in the same directory. Any existing
    ``-vN`` suffix on the source file is stripped before the new version
    suffix is appended, so re-versioning a versioned file works correctly.

    Parameters
    ----------
    loop_file:
        Path to the source loop file (e.g. ``plans/phase-2-ralph-loops.md``).
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
    """Inject a ``gate_failure_context`` YAML block into a loop file's frontmatter.

    Builds a ``gate_failure_context:`` YAML block from the provided verdict dict
    and inserts it immediately after the frontmatter opening delimiter. Works with
    both ``---`` (standard YAML) and `` ```yaml `` (fenced code block) delimiters
    used in the planning system's plan files.

    Parameters
    ----------
    loop_file:
        Path to the loop file to modify in-place.
    verdict:
        Dict matching the gate-failure-context schema. Expected keys:
        ``attempt`` (int), ``verdict_file`` (str), ``summary`` (str),
        ``loops_reverted`` (list of dicts with ``loop`` and ``reason``),
        ``do_not_repeat`` (list of str).

    Returns
    -------
    Path
        Absolute path to the modified file.

    Raises
    ------
    FileNotFoundError
        If ``loop_file`` does not exist.
    ValueError
        If no recognisable frontmatter delimiter is found.
    """
    path = Path(loop_file)
    if not path.exists():
        raise FileNotFoundError(f"Loop file not found: {path}")

    content = path.read_text(encoding="utf-8")

    # Build the gate_failure_context YAML block
    block_lines = ["gate_failure_context:"]
    block_lines.append(f"  attempt: {verdict.get('attempt', 1)}")
    block_lines.append(f"  verdict_file: \"{verdict.get('verdict_file', '')}\"")
    block_lines.append(f"  summary: \"{verdict.get('summary', '')}\"")

    loops_reverted = verdict.get("loops_reverted", [])
    if loops_reverted:
        block_lines.append("  loops_reverted:")
        for item in loops_reverted:
            block_lines.append(f"    - loop: \"{item.get('loop', '')}\"")
            block_lines.append(f"      reason: \"{item.get('reason', '')}\"")
    else:
        block_lines.append("  loops_reverted: []")

    do_not_repeat = verdict.get("do_not_repeat", [])
    if do_not_repeat:
        block_lines.append("  do_not_repeat:")
        for item in do_not_repeat:
            block_lines.append(f"    - \"{item}\"")
    else:
        block_lines.append("  do_not_repeat: []")

    block_text = "\n".join(block_lines) + "\n"

    # Insert after the frontmatter opening delimiter.
    # Priority: ```yaml fence (used by plan files), then --- (standard YAML).
    yaml_fence_re = re.compile(r"(```yaml\n)")
    dashes_re = re.compile(r"(---\n)")

    if yaml_fence_re.search(content):
        new_content = yaml_fence_re.sub(r"\1" + block_text, content, count=1)
    elif dashes_re.search(content):
        new_content = dashes_re.sub(r"\1" + block_text, content, count=1)
    else:
        raise ValueError(
            f"No recognisable frontmatter delimiter found in {path}. "
            "Expected '```yaml' or '---'."
        )

    path.write_text(new_content, encoding="utf-8")
    return path.resolve()


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
