"""
remediate.py — Triage helper for the self-correcting gate pipeline.
==========================================================================

Provides ``triage_findings(verdict)`` which routes gate-verdict data into
four triage buckets:

- ``structural``  : loop ids from ``loops_to_revert`` (re-run required)
- ``localized``   : critical findings with an actionable file/line in ``location``
- ``unfixable``   : critical findings with no actionable location AND not covered
                    by a structurally reverted loop
- ``conflict``    : critical findings at the same location from different finding
                    entries (contradictory prescriptions — escalate, do not fix)

Severity ``"warning"`` and ``"info"`` findings are ignored entirely.

Zero external dependencies (stdlib only: json, re, pathlib are available but
only ``re`` is needed here).
"""

import re
from typing import Any, Union

__all__ = ["triage_findings"]


# A location string is considered "actionable" when it is non-empty and
# looks like it contains a file path component (any non-whitespace content).
_ACTIONABLE_RE = re.compile(r"\S")


def _is_actionable(location: str) -> bool:
    """Return True if the location string is non-empty and contains non-whitespace."""
    return bool(location and _ACTIONABLE_RE.search(location))


def triage_findings(
    verdict: Union[dict[str, Any], list[dict[str, Any]]],
) -> dict[str, list]:
    """Triage gate-verdict data into remediation buckets.

    Parameters
    ----------
    verdict:
        A single gate-verdict dict **or** a list of gate-verdict dicts (for
        multi-agent union).  Each dict must have at least ``findings`` and
        ``loops_to_revert`` keys (matching the gate-verdict schema).

    Returns
    -------
    dict with keys:
        ``structural``  – list of loop ids (str) from ``loops_to_revert``
        ``localized``   – list of critical finding dicts with an actionable location
        ``unfixable``   – list of critical finding dicts with no actionable location
                          AND not already covered by a reverted loop
        ``conflict``    – list of dicts describing contradictory same-location findings
    """
    # Normalise to a list of verdicts for uniform processing
    if isinstance(verdict, dict):
        verdicts: list[dict[str, Any]] = [verdict]
    else:
        verdicts = list(verdict)

    # ── 1. Collect structural (loops_to_revert) with deduplication ────────────
    structural_set: set[str] = set()
    for v in verdicts:
        for loop_id in v.get("loops_to_revert", []):
            structural_set.add(loop_id)
    structural: list[str] = sorted(structural_set)

    # ── 2. Collect all critical findings from all verdicts ────────────────────
    critical_findings: list[dict[str, Any]] = []
    for v in verdicts:
        for finding in v.get("findings", []):
            if finding.get("severity") == "critical":
                critical_findings.append(finding)

    # ── 3. Detect contradictory findings (same location, multiple entries) ─────
    # Group by location; if a location has >1 finding, those are conflicts.
    location_groups: dict[str, list[dict]] = {}
    for f in critical_findings:
        loc = f.get("location", "")
        if _is_actionable(loc):
            if loc not in location_groups:
                location_groups[loc] = []
            location_groups[loc].append(f)

    conflicting_locations: set[str] = set()
    conflict: list[dict[str, Any]] = []
    for loc, group in location_groups.items():
        if len(group) > 1:
            conflicting_locations.add(loc)
            conflict.append({
                "location": loc,
                "findings": group,
            })

    # ── 4. Route remaining critical findings ──────────────────────────────────
    localized: list[dict[str, Any]] = []
    unfixable: list[dict[str, Any]] = []

    for f in critical_findings:
        loc = f.get("location", "")
        if _is_actionable(loc):
            if loc not in conflicting_locations:
                localized.append(f)
            # else: already captured in conflict
        else:
            # No actionable location — unfixable unless covered by structural
            # "Covered" means: loops_to_revert is non-empty (structural re-run
            # will address phase-level issues).  Per spec: critical finding with
            # no actionable location AND not covered by a reverted loop -> unfixable.
            if not structural_set:
                unfixable.append(f)
            # else: structural re-run covers it; omit from unfixable

    return {
        "structural": structural,
        "localized": localized,
        "unfixable": unfixable,
        "conflict": conflict,
    }
