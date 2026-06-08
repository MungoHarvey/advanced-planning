"""
test_codex_gate.py - Tests for platforms/python/codex_gate.py
==============================================================

Covers all 20 paths described in the loop-047 design spec:
  - 5 extraction cases
  - 6 validation cases (including extra-field tolerance)
  - 3 extract_and_validate cases (including identity-overfit reject)
  - 6 aggregate_verdicts cases (including the 2 CRITICAL regression cases)
"""

import json
import pytest
from pathlib import Path
import tempfile
import os

from platforms.python.codex_gate import (
    extract_verdict_json,
    validate_verdict,
    extract_and_validate,
    aggregate_verdicts,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_verdict(**overrides):
    """Return a minimal valid Codex verdict dict."""
    base = {
        "phase": "phase-12",
        "attempt": 1,
        "timestamp": "2026-06-08T12:00:00Z",
        "agent": "codex",
        "verdict": "pass",
        "confidence": 90,
        "findings": [],
        "loops_to_revert": [],
        "failure_notes": [],
    }
    base.update(overrides)
    return base


def _write_verdict_file(tmp_path, filename, data):
    """Write a verdict dict to a JSON file and return the Path."""
    p = tmp_path / filename
    p.write_text(json.dumps(data))
    return p


# ===========================================================================
# 1. extract_verdict_json — 5 cases
# ===========================================================================

class TestExtractVerdictJson:
    """Path 1-5: extract_verdict_json(stdout) -> str | None"""

    def test_extracts_fenced_json_block(self):
        """Path 1: clean fenced json block -> returns json string"""
        payload = json.dumps({"verdict": "pass"})
        stdout = f"Some prefix text\n```json\n{payload}\n```\nSome suffix"
        result = extract_verdict_json(stdout)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["verdict"] == "pass"

    def test_returns_none_when_no_fenced_block(self):
        """Path 2: no fenced block at all -> returns None"""
        stdout = "Codex said nothing useful here."
        result = extract_verdict_json(stdout)
        assert result is None

    def test_brace_fallback_when_no_fence(self):
        """Path 3: no fence but raw JSON object present -> brace fallback extracts it"""
        payload = json.dumps({"verdict": "fail", "agent": "codex"})
        stdout = f"Here is the result: {payload} end"
        result = extract_verdict_json(stdout)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["verdict"] == "fail"

    def test_returns_none_on_multiple_fenced_blocks(self):
        """Path 4: multiple fenced json blocks -> ambiguous, returns None"""
        block1 = json.dumps({"verdict": "pass"})
        block2 = json.dumps({"verdict": "fail"})
        stdout = f"```json\n{block1}\n```\n```json\n{block2}\n```"
        result = extract_verdict_json(stdout)
        assert result is None

    def test_returns_none_on_empty_stdout(self):
        """Path 5: empty stdout -> returns None"""
        result = extract_verdict_json("")
        assert result is None


# ===========================================================================
# 2. validate_verdict — 6 cases
# ===========================================================================

class TestValidateVerdict:
    """Path 6-11: validate_verdict(d) -> (ok: bool, reason: str)"""

    def test_valid_verdict_passes(self):
        """Path 6: all required fields present and correct -> ok=True"""
        d = _make_verdict()
        ok, reason = validate_verdict(d)
        assert ok is True
        assert reason == ""

    def test_missing_required_field_fails(self):
        """Path 7: missing required field -> ok=False"""
        d = _make_verdict()
        del d["verdict"]
        ok, reason = validate_verdict(d)
        assert ok is False
        assert "verdict" in reason.lower() or "missing" in reason.lower()

    def test_wrong_verdict_enum_fails(self):
        """Path 8: verdict not in {pass, fail} -> ok=False"""
        d = _make_verdict(verdict="maybe")
        ok, reason = validate_verdict(d)
        assert ok is False
        assert "verdict" in reason.lower() or "enum" in reason.lower() or "pass" in reason.lower()

    def test_wrong_agent_fails(self):
        """Path 9: agent != 'codex' -> ok=False"""
        d = _make_verdict(agent="phase-goals-agent")
        ok, reason = validate_verdict(d)
        assert ok is False
        assert "agent" in reason.lower() or "codex" in reason.lower()

    def test_wrong_type_fails(self):
        """Path 10: wrong type on a field (attempt as string) -> ok=False"""
        d = _make_verdict(attempt="one")
        ok, reason = validate_verdict(d)
        assert ok is False
        assert "attempt" in reason.lower() or "type" in reason.lower() or "int" in reason.lower()

    def test_extra_field_tolerated(self):
        """Path 11: extra unknown field present (e.g. backend, evaluated_by) -> ok=True (lenient)"""
        d = _make_verdict()
        d["backend"] = "codex"
        d["evaluated_by"] = "gpt-5.5"
        ok, reason = validate_verdict(d)
        assert ok is True, f"Expected extra fields to be tolerated but got: {reason}"


# ===========================================================================
# 3. extract_and_validate — 3 cases
# ===========================================================================

class TestExtractAndValidate:
    """Path 12-14: extract_and_validate(stdout, expected_phase, expected_attempt) -> result dict"""

    def test_valid_extraction_and_validation(self):
        """Path 12: clean stdout with matching phase/attempt -> ok=True, verdict returned"""
        d = _make_verdict(phase="phase-12", attempt=1)
        payload = json.dumps(d)
        stdout = f"```json\n{payload}\n```"
        result = extract_and_validate(stdout, expected_phase="phase-12", expected_attempt=1)
        assert result["ok"] is True
        assert result["verdict"]["verdict"] == "pass"

    def test_extraction_failure_returns_skip(self):
        """Path 13: unparseable stdout -> ok=False with reason"""
        stdout = "Codex output was completely garbled. No JSON here."
        result = extract_and_validate(stdout, expected_phase="phase-12", expected_attempt=1)
        assert result["ok"] is False
        assert "reason" in result

    def test_identity_overfit_rejected(self):
        """Path 14: Codex copies the sample verdict's phase/attempt (overfit) -> ok=False"""
        # Codex returns a verdict with a different phase/attempt (the sample one)
        # e.g. phase-0 attempt-99 as a planted sample that Codex echoed back
        d = _make_verdict(phase="phase-0", attempt=99)  # sample identity, not expected
        payload = json.dumps(d)
        stdout = f"```json\n{payload}\n```"
        result = extract_and_validate(stdout, expected_phase="phase-12", expected_attempt=1)
        assert result["ok"] is False
        assert "reason" in result
        # The reason should indicate identity mismatch / overfit
        assert any(word in result["reason"].lower() for word in ["phase", "attempt", "mismatch", "identity", "overfit"])


# ===========================================================================
# 4. aggregate_verdicts — 6 cases (including 2 CRITICAL regressions)
# ===========================================================================

class TestAggregateVerdicts:
    """Path 15-20: aggregate_verdicts(paths) -> {result, conflicts, missing}"""

    def test_all_pass_returns_pass(self, tmp_path):
        """Path 15 (CRITICAL regression): all verdicts pass -> result='pass'"""
        p1 = _write_verdict_file(tmp_path, "v1.json", _make_verdict(agent="code-review-agent", verdict="pass"))
        p2 = _write_verdict_file(tmp_path, "v2.json", _make_verdict(agent="phase-goals-agent", verdict="pass"))
        result = aggregate_verdicts([p1, p2])
        assert result["result"] == "pass"
        assert result["conflicts"] == []
        assert result["missing"] == []

    def test_any_fail_returns_fail(self, tmp_path):
        """Path 16 (CRITICAL regression): any verdict fails -> result='fail'"""
        p1 = _write_verdict_file(tmp_path, "v1.json", _make_verdict(agent="code-review-agent", verdict="pass"))
        p2 = _write_verdict_file(tmp_path, "v2.json", _make_verdict(agent="phase-goals-agent", verdict="fail"))
        result = aggregate_verdicts([p1, p2])
        assert result["result"] == "fail"
        assert result["conflicts"] == []

    def test_empty_paths_returns_missing(self):
        """Path 17: no paths -> missing list populated, result='fail'"""
        result = aggregate_verdicts([])
        assert result["result"] == "fail"
        assert len(result["missing"]) == 0  # no expected paths, no missing entries
        # With no verdicts, fail is the safe default

    def test_missing_file_reported(self, tmp_path):
        """Path 18: one path doesn't exist -> reported in missing"""
        p1 = _write_verdict_file(tmp_path, "v1.json", _make_verdict(verdict="pass"))
        p2 = tmp_path / "nonexistent.json"
        result = aggregate_verdicts([p1, p2])
        assert result["result"] == "fail"
        missing_strs = [str(m) for m in result["missing"]]
        assert any("nonexistent" in s for s in missing_strs)

    def test_codex_subagent_conflict_detected(self, tmp_path):
        """Path 19: codex passes but subagent fails -> conflict detected"""
        p1 = _write_verdict_file(tmp_path, "codex.json",
                                  _make_verdict(agent="codex", verdict="pass", backend="codex"))
        p2 = _write_verdict_file(tmp_path, "phase-goals.json",
                                  _make_verdict(agent="phase-goals-agent", verdict="fail"))
        result = aggregate_verdicts([p1, p2])
        assert result["result"] == "fail"  # any-fail rule
        # Conflict: codex=pass but subagent=fail (disagreement)
        assert len(result["conflicts"]) > 0

    def test_all_fail_returns_fail(self, tmp_path):
        """Path 20: all verdicts fail -> result='fail'"""
        p1 = _write_verdict_file(tmp_path, "v1.json", _make_verdict(agent="code-review-agent", verdict="fail"))
        p2 = _write_verdict_file(tmp_path, "v2.json", _make_verdict(agent="phase-goals-agent", verdict="fail"))
        result = aggregate_verdicts([p1, p2])
        assert result["result"] == "fail"
        assert result["conflicts"] == []  # uniform fail, no disagreement
