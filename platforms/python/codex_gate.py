"""
codex_gate.py - Codex verdict extraction, validation, and aggregation
======================================================================

Zero-dependency helper (stdlib only: json, re, pathlib) for parsing Codex
stdout, validating gate verdict JSON, and aggregating multiple verdict files.

Called by run-gate.md after capturing Codex stdout. The four public functions
correspond to the four stages of the Codex gate workflow:

  1. extract_verdict_json  -- pull one JSON object out of Codex stdout
  2. validate_verdict      -- lenient structural check (required fields + types)
  3. extract_and_validate  -- combined extract + validate + identity-overfit check
  4. aggregate_verdicts    -- AND of all verdict files; detect conflicts + missing

Design notes
------------
- Validator is LENIENT: rejects only real problems (missing required field, wrong
  type, verdict not in {pass, fail}, agent != "codex", identity overfit).
  Unknown extra fields (``backend``, ``evaluated_by``) are silently tolerated.
- extract_verdict_json accepts either a fenced ```json block (preferred) or a
  bare JSON object (brace fallback). Ambiguity (multiple fenced blocks) is
  rejected: returns None.
- aggregate_verdicts detects Codex-vs-subagent disagreement (one pass, one fail)
  and reports it in the ``conflicts`` list. The overall result is always the AND
  of all verdicts (any fail -> fail).
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS: Dict[str, type] = {
    "phase": str,
    "attempt": int,
    "timestamp": str,
    "agent": str,
    "verdict": str,
    "confidence": int,
    "findings": list,
    "loops_to_revert": list,
    "failure_notes": list,
}

_VERDICT_ENUM = {"pass", "fail"}

# Regex for a single fenced ```json ... ``` block
_FENCED_JSON_RE = re.compile(r"```json\s*([\s\S]*?)```", re.MULTILINE)

# Regex for the outermost JSON object (brace fallback)
# Matches from the first { to the last } in the string
_BRACE_RE = re.compile(r"\{[\s\S]*\}")


# ---------------------------------------------------------------------------
# 1. extract_verdict_json
# ---------------------------------------------------------------------------

def extract_verdict_json(stdout: str) -> Optional[str]:
    """Extract a single JSON string from Codex stdout.

    Parameters
    ----------
    stdout:
        Raw Codex process stdout.

    Returns
    -------
    str or None
        A JSON-parseable string if exactly one block was found, or ``None``
        if zero or multiple blocks were found, or if the string is empty.

    Notes
    -----
    Strategy:
    1. Look for fenced ```json ... ``` blocks.
    2. If exactly one fenced block is found, return its content.
    3. If multiple fenced blocks are found but they are all structurally
       identical (parse to the same JSON object), return the last one --
       the codex CLI sometimes echoes the same verdict block twice, which
       is not genuine ambiguity.
    4. If zero fenced blocks, try the brace fallback (first { to last }).
    5. If multiple fenced blocks genuinely differ (or any is malformed),
       return None (ambiguous).
    """
    if not stdout or not stdout.strip():
        return None

    fenced_matches = _FENCED_JSON_RE.findall(stdout)

    if len(fenced_matches) == 1:
        candidate = fenced_matches[0].strip()
        # Verify it is valid JSON before returning
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            return None

    if len(fenced_matches) > 1:
        # Multiple fenced blocks. The codex CLI sometimes echoes the same
        # verdict block twice; that is not genuine ambiguity. Parse them all
        # and, if they are structurally identical, return the last block.
        # Only treat as ambiguous when the blocks differ (or any is malformed).
        parsed_blocks = []
        for match in fenced_matches:
            try:
                parsed_blocks.append(json.loads(match.strip()))
            except json.JSONDecodeError:
                return None
        if all(block == parsed_blocks[0] for block in parsed_blocks):
            return fenced_matches[-1].strip()
        return None

    # Zero fenced blocks: try brace fallback
    brace_match = _BRACE_RE.search(stdout)
    if brace_match:
        candidate = brace_match.group(0)
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            return None

    return None


# ---------------------------------------------------------------------------
# 2. validate_verdict
# ---------------------------------------------------------------------------

def validate_verdict(d: Any) -> Tuple[bool, str]:
    """Validate a gate verdict dict with a lenient structural check.

    Parameters
    ----------
    d:
        Parsed verdict object (expected dict).

    Returns
    -------
    (ok, reason):
        ok is True if the verdict is structurally valid.
        reason is an empty string on success, or a short description of the
        first problem found on failure.

    Notes
    -----
    Lenient: unknown extra fields are silently ignored.
    Rejects only:
    - Missing required field
    - Wrong type on a required field
    - ``verdict`` not in {"pass", "fail"}
    - ``agent`` != "codex"
    """
    if not isinstance(d, dict):
        return False, "verdict must be a JSON object (dict)"

    # Check required fields and types
    for field, expected_type in _REQUIRED_FIELDS.items():
        if field not in d:
            return False, f"missing required field: '{field}'"
        if not isinstance(d[field], expected_type):
            actual = type(d[field]).__name__
            return False, (
                f"field '{field}' must be {expected_type.__name__}, got {actual}"
            )

    # Check verdict enum
    if d["verdict"] not in _VERDICT_ENUM:
        return False, (
            f"verdict must be one of {sorted(_VERDICT_ENUM)}, got '{d['verdict']}'"
        )

    # Check agent identity
    if d["agent"] != "codex":
        return False, f"agent must be 'codex', got '{d['agent']}'"

    return True, ""


# ---------------------------------------------------------------------------
# 3. extract_and_validate
# ---------------------------------------------------------------------------

def extract_and_validate(
    stdout: str,
    expected_phase: str,
    expected_attempt: int,
) -> Dict[str, Any]:
    """Extract, validate, and identity-check a Codex verdict from stdout.

    Parameters
    ----------
    stdout:
        Raw Codex process stdout.
    expected_phase:
        The phase identifier the gate is currently reviewing (e.g. "phase-12").
    expected_attempt:
        The current attempt number.

    Returns
    -------
    dict
        On success: ``{"ok": True, "verdict": <parsed dict>}``
        On any failure: ``{"ok": False, "reason": <str>}``

    Notes
    -----
    Identity-overfit check: if Codex returns a verdict whose ``phase`` or
    ``attempt`` does not match the expected values, the verdict is rejected.
    This prevents Codex from copying a sample verdict verbatim.
    """
    # Step 1: extract
    raw = extract_verdict_json(stdout)
    if raw is None:
        return {
            "ok": False,
            "reason": "no valid JSON block found in Codex stdout",
        }

    # Step 2: parse
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {"ok": False, "reason": f"JSON parse error: {exc}"}

    # Step 3: validate structure
    ok, reason = validate_verdict(d)
    if not ok:
        return {"ok": False, "reason": reason}

    # Step 4: identity-overfit check
    if d.get("phase") != expected_phase:
        return {
            "ok": False,
            "reason": (
                f"identity mismatch: expected phase '{expected_phase}', "
                f"got '{d.get('phase')}' — possible identity overfit"
            ),
        }
    if d.get("attempt") != expected_attempt:
        return {
            "ok": False,
            "reason": (
                f"identity mismatch: expected attempt {expected_attempt}, "
                f"got {d.get('attempt')} — possible identity overfit"
            ),
        }

    return {"ok": True, "verdict": d}


# ---------------------------------------------------------------------------
# 4. aggregate_verdicts
# ---------------------------------------------------------------------------

def aggregate_verdicts(paths: List[Any]) -> Dict[str, Any]:
    """Aggregate multiple gate verdict files into a single result.

    Parameters
    ----------
    paths:
        List of Path objects (or path-like strings) pointing to verdict JSON
        files. Files that do not exist are reported in ``missing``.

    Returns
    -------
    dict
        ``{
            "result":    "pass" | "fail",
            "conflicts": [list of conflict descriptions],
            "missing":   [list of missing paths as strings],
        }``

    Notes
    -----
    Aggregation rules:
    - Any fail -> overall result is "fail"
    - All pass -> overall result is "pass"
    - No readable verdicts -> "fail" (safe default)
    - Codex-vs-subagent disagreement is detected and reported in ``conflicts``:
      a conflict occurs when Codex returns "pass" and at least one subagent
      returns "fail", or vice versa.
    """
    missing: List[str] = []
    verdicts: List[Dict[str, Any]] = []

    for p in paths:
        path = Path(p)
        if not path.exists():
            missing.append(str(path))
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            verdicts.append(data)
        except (json.JSONDecodeError, OSError):
            missing.append(str(path))

    if not verdicts:
        return {"result": "fail", "conflicts": [], "missing": missing}

    # Determine overall result: AND of all verdicts; any missing file -> fail
    overall = (
        "pass"
        if not missing and all(v.get("verdict") == "pass" for v in verdicts)
        else "fail"
    )

    # Detect Codex-vs-subagent conflicts
    codex_verdicts = [v for v in verdicts if v.get("agent") == "codex"]
    subagent_verdicts = [v for v in verdicts if v.get("agent") != "codex"]

    conflicts: List[str] = []
    for cv in codex_verdicts:
        codex_result = cv.get("verdict")
        for sv in subagent_verdicts:
            subagent_result = sv.get("verdict")
            if codex_result != subagent_result:
                conflicts.append(
                    f"codex verdict='{codex_result}' disagrees with "
                    f"agent='{sv.get('agent')}' verdict='{subagent_result}'"
                )

    return {"result": overall, "conflicts": conflicts, "missing": missing}
