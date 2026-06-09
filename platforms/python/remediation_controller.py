"""
remediation_controller.py — Predicate helpers for the bounded gate-remediation controller.
===========================================================================================

Provides zero-dependency helper functions that encode the key guard-rail predicates
described in the ``## Control Flow``, ``## Remediation Safety``, and ``## Git-State Policy``
sections of the self-correcting gate design spec.

These helpers are used by ``/next-phase --auto`` (the markdown command) and are
independently unit-tested.  They are pure functions: no I/O, no side effects, no
external dependencies.

Zero external dependencies (stdlib only: json, pathlib, re, hashlib).
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Union

__all__ = [
    "count_gate_fail_cycles",
    "is_path_in_allowlist",
    "is_path_never_touch",
    "validate_diff_allowlist",
    "compute_criteria_hash",
    "validate_criteria_hash",
    "validate_regateverdict_criteria_outcomes",
    "has_sentinel",
    "is_transient_path",
    "has_allowlisted_source_changes",
]


# ---------------------------------------------------------------------------
# Cycle counting
# ---------------------------------------------------------------------------

def count_gate_fail_cycles(history_path: Union[str, Path], phase: str) -> int:
    """Count the number of ``gate_fail`` events in history.jsonl for a given phase.

    Parameters
    ----------
    history_path:
        Path to ``.advanced-plans/state/history.jsonl``.
    phase:
        Phase identifier string, e.g. ``"phase-13"``.

    Returns
    -------
    int
        Number of ``gate_fail`` events recorded for this phase (0 if file absent).
    """
    path = Path(history_path)
    if not path.exists():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("event") == "gate_fail" and event.get("phase") == phase:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Path allowlist / never-touch
# ---------------------------------------------------------------------------

# Patterns for the NEVER-TOUCH list.  Each is a callable(path_str) -> bool.
_NEVER_TOUCH_PATTERNS = [
    # plan.md files anywhere under phases
    re.compile(r"\.advanced-plans/phases/[^/]+/plan\.md$"),
    # loops*.md files anywhere under phases (including versioned)
    re.compile(r"\.advanced-plans/phases/[^/]+/loops.*\.md$"),
    # criteria-frozen.md
    re.compile(r"\.advanced-plans/phases/[^/]+/criteria-frozen\.md$"),
    # core/schemas/**
    re.compile(r"core/schemas/"),
    # core/state/**
    re.compile(r"core/state/"),
    # gate-reviewer.md (core agent)
    re.compile(r"core/agents/gate-reviewer\.md$"),
    # CC gate agent docs
    re.compile(r"platforms/claude-code/agents/.*-agent\.md$"),
    # gate-verdict files
    re.compile(r"\.advanced-plans/gate-verdicts/"),
    # history.jsonl
    re.compile(r"\.advanced-plans/state/history\.jsonl$"),
    # loop-ready.json / loop-complete.json
    re.compile(r"\.advanced-plans/state/loop-(ready|complete)\.json$"),
    # gate-review-mode sentinel
    re.compile(r"\.advanced-plans/state/gate-review-mode$"),
]

# Patterns for transient files excluded from no-change detection.
_TRANSIENT_PATTERNS = [
    re.compile(r"\.advanced-plans/phases/[^/]+/retry-context\.json$"),
    re.compile(r"\.advanced-plans/state/history\.jsonl$"),
    re.compile(r"\.advanced-plans/gate-verdicts/"),
    re.compile(r"\.advanced-plans/state/loop-(ready|complete)\.json$"),
    re.compile(r"\.advanced-plans/state/gate-review-mode$"),
]


def _normalise(path: Union[str, Path]) -> str:
    """Normalise a path to forward-slash POSIX-style for pattern matching."""
    return str(path).replace("\\", "/")


def is_path_never_touch(path: Union[str, Path]) -> bool:
    """Return True if the path matches the NEVER-TOUCH list.

    Parameters
    ----------
    path:
        File path (relative or absolute) to check.

    Returns
    -------
    bool
        True if the path matches any never-touch pattern.
    """
    norm = _normalise(path)
    return any(p.search(norm) for p in _NEVER_TOUCH_PATTERNS)


def is_path_in_allowlist(path: Union[str, Path]) -> bool:
    """Return True if the path is on the remediation allowlist.

    Allowlisted paths:
    - Anything under ``platforms/`` (source modules, non-test)
    - Anything under ``core/skills/`` or ``core/agents/``
    - Anything under ``.claude/`` (skills, commands, agents)
    - ``retry-context.json`` sidecar

    Note: a path can be in the allowlist AND the never-touch list simultaneously
    (e.g. ``platforms/python/tests/`` test files asserting failed criteria).
    Always check ``is_path_never_touch`` first; never-touch takes precedence.

    Parameters
    ----------
    path:
        File path to check.

    Returns
    -------
    bool
        True if the path is on the allowlist.
    """
    norm = _normalise(path)
    allowlist_patterns = [
        re.compile(r"^platforms/"),
        re.compile(r"^core/skills/"),
        re.compile(r"^core/agents/"),
        re.compile(r"^\.claude/"),
        re.compile(r"\.advanced-plans/phases/[^/]+/retry-context\.json$"),
    ]
    return any(p.search(norm) for p in allowlist_patterns)


def validate_diff_allowlist(
    changed_paths: list,
) -> tuple:
    """Validate that all changed paths are in the allowlist and none are in never-touch.

    Parameters
    ----------
    changed_paths:
        List of file path strings from ``git diff --name-only``.

    Returns
    -------
    tuple (ok: bool, violations: list[str])
        ``ok`` is True only if no violations were found.
        ``violations`` lists the forbidden paths found (empty if ok).
    """
    violations = []
    for p in changed_paths:
        if is_path_never_touch(p):
            violations.append(p)
    return (len(violations) == 0, violations)


def is_transient_path(path: Union[str, Path]) -> bool:
    """Return True if the path is a transient file excluded from no-change detection.

    Parameters
    ----------
    path:
        File path to check.

    Returns
    -------
    bool
        True if the path is transient (excluded from no-change detection).
    """
    norm = _normalise(path)
    return any(p.search(norm) for p in _TRANSIENT_PATTERNS)


def has_allowlisted_source_changes(changed_paths: list) -> bool:
    """Return True if at least one non-transient allowlisted source path changed.

    This implements the no-change detection: a fix that changes ONLY transient
    files (retry-context.json, history.jsonl, verdicts, etc.) is treated as
    "no change" and triggers an escalation.

    Parameters
    ----------
    changed_paths:
        List of file path strings from ``git diff --name-only``.

    Returns
    -------
    bool
        True if there is at least one real source change.
    """
    for p in changed_paths:
        if not is_transient_path(p) and is_path_in_allowlist(p):
            return True
    return False


# ---------------------------------------------------------------------------
# Criteria hash
# ---------------------------------------------------------------------------

def compute_criteria_hash(criteria_content: Union[str, bytes]) -> str:
    """Compute the SHA-256 hash of the criteria-frozen.md content.

    Parameters
    ----------
    criteria_content:
        The raw bytes or text of criteria-frozen.md.

    Returns
    -------
    str
        Hex-encoded SHA-256 digest.
    """
    if isinstance(criteria_content, str):
        data = criteria_content.encode("utf-8")
    else:
        data = criteria_content
    return hashlib.sha256(data).hexdigest()


def validate_criteria_hash(
    criteria_path: Union[str, Path],
    expected_hash: str,
) -> bool:
    """Return True if the live criteria-frozen.md matches the expected hash.

    Parameters
    ----------
    criteria_path:
        Path to ``.advanced-plans/phases/phase-N/criteria-frozen.md``.
    expected_hash:
        The SHA-256 hex digest recorded at freeze time.

    Returns
    -------
    bool
        True if the file matches the expected hash; False otherwise.
    """
    path = Path(criteria_path)
    live_hash = compute_criteria_hash(path.read_bytes())
    return live_hash == expected_hash


# ---------------------------------------------------------------------------
# Re-gate verdict validation
# ---------------------------------------------------------------------------

def validate_regateverdict_criteria_outcomes(
    verdict: dict[str, Any],
    frozen_criteria: list,
) -> tuple:
    """Validate that a re-gate verdict covers all frozen criteria in criteria_outcomes.

    Parameters
    ----------
    verdict:
        The parsed verdict JSON dict from a gate agent.
    frozen_criteria:
        List of criterion identifier strings (e.g. the bullet points from
        criteria-frozen.md).

    Returns
    -------
    tuple (ok: bool, missing: list[str])
        ``ok`` is True if all criteria are present in ``criteria_outcomes``.
        ``missing`` lists criteria not found in the verdict's criteria_outcomes.

    Notes
    -----
    Per ``gate-verdict.schema.json``, ``criteria_outcomes`` is an array of
    objects, each carrying a ``criterion`` string (plus ``status``/``evidence``).
    The set of covered criteria is the union of those ``criterion`` values. A
    legacy dict form (criterion-string keys) is also tolerated so older verdicts
    validate unchanged; malformed entries are skipped rather than raising.
    """
    outcomes = verdict.get("criteria_outcomes", [])
    if isinstance(outcomes, dict):
        # Legacy form: criterion strings as dict keys.
        covered = set(outcomes.keys())
    else:
        # Schema form: array of {criterion, status, evidence} objects.
        covered = {
            entry["criterion"]
            for entry in outcomes
            if isinstance(entry, dict) and "criterion" in entry
        }
    missing = [c for c in frozen_criteria if c not in covered]
    return (len(missing) == 0, missing)


# ---------------------------------------------------------------------------
# Sentinel check
# ---------------------------------------------------------------------------

def has_sentinel(sentinel_path: Union[str, Path]) -> bool:
    """Return True if the gate-review-mode sentinel file exists.

    Parameters
    ----------
    sentinel_path:
        Path to ``.advanced-plans/state/gate-review-mode``.

    Returns
    -------
    bool
        True if the sentinel file exists (fix dispatch must be blocked).
    """
    return Path(sentinel_path).exists()
