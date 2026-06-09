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

    def test_returns_none_on_multiple_differing_fenced_blocks(self):
        """Path 4: multiple *differing* fenced json blocks -> ambiguous, returns None"""
        block1 = json.dumps({"verdict": "pass"})
        block2 = json.dumps({"verdict": "fail"})
        stdout = f"```json\n{block1}\n```\n```json\n{block2}\n```"
        result = extract_verdict_json(stdout)
        assert result is None

    def test_collapses_identical_duplicate_fenced_blocks(self):
        """Path 4b: multiple *identical* fenced json blocks -> returns the block.

        The codex CLI echoes the same verdict block twice; identical duplicates
        are not genuine ambiguity (Phase 14 parser hardening).
        """
        block = json.dumps({"verdict": "pass", "agent": "codex"})
        stdout = f"```json\n{block}\n```\n```json\n{block}\n```"
        result = extract_verdict_json(stdout)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["verdict"] == "pass"

    def test_returns_none_on_malformed_among_multiple_blocks(self):
        """Path 4c: a malformed block among several -> ambiguous/unsafe, returns None"""
        good = json.dumps({"verdict": "pass"})
        stdout = f"```json\n{good}\n```\n```json\n{{not valid json}}\n```"
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


# ===========================================================================
# 5. Degrade path — codex absent (gate proceeds on two in-house agents only)
# ===========================================================================

class TestDegradePath:
    """Degrade E2E: codex unavailable — gate uses only two in-house verdicts.

    These tests confirm aggregate_verdicts behaves correctly when only the two
    standard subagent verdict files are present (no codex.json).  This is the
    load-bearing guarantee: the gate must never block on Codex absence.

    Run-gate.md degrade trace (Step 6a → Step 7):
      - `which codex` returns non-zero (or auth check fails)
      - codex_available is set to False
      - Steps 7.2 (launch Codex background) and 8a (write codex.json) are skipped
      - No phase-N-attempt-M-codex.json is written
      - A gate_codex_skipped event is appended to history.jsonl (Step 8a failure branch)
      - Step 9 calls aggregate_verdicts with only the two in-house verdict files
      - aggregate_verdicts returns the correct pass/fail AND with no conflicts
    """

    def test_degrade_two_agent_pass(self, tmp_path):
        """Degrade pass: two in-house agents pass, no codex -> result='pass', no conflicts."""
        p1 = _write_verdict_file(
            tmp_path, "phase-12-attempt-1-code-review-agent.json",
            _make_verdict(agent="code-review-agent", verdict="pass")
        )
        p2 = _write_verdict_file(
            tmp_path, "phase-12-attempt-1-phase-goals-agent.json",
            _make_verdict(agent="phase-goals-agent", verdict="pass")
        )
        # Simulate: codex.json is NOT present (degrade — codex was skipped)
        codex_path = tmp_path / "phase-12-attempt-1-codex.json"
        assert not codex_path.exists(), "codex.json must not exist on degrade path"

        result = aggregate_verdicts([p1, p2])
        assert result["result"] == "pass", (
            f"Expected 'pass' on degrade path with two passing in-house verdicts, got {result['result']}"
        )
        assert result["conflicts"] == [], "No conflicts expected when codex is absent"
        assert result["missing"] == [], "No missing files expected"

    def test_degrade_two_agent_fail(self, tmp_path):
        """Degrade fail: one in-house agent fails, no codex -> result='fail', no conflicts."""
        p1 = _write_verdict_file(
            tmp_path, "phase-12-attempt-1-code-review-agent.json",
            _make_verdict(agent="code-review-agent", verdict="pass")
        )
        p2 = _write_verdict_file(
            tmp_path, "phase-12-attempt-1-phase-goals-agent.json",
            _make_verdict(agent="phase-goals-agent", verdict="fail")
        )
        result = aggregate_verdicts([p1, p2])
        assert result["result"] == "fail"
        assert result["conflicts"] == [], "No conflicts when codex is absent (no codex verdict to disagree)"
        assert result["missing"] == []

    def test_degrade_signal_no_codex_file(self, tmp_path):
        """Degrade signal: aggregate_verdicts over two files returns no codex conflicts.

        On the degrade path, run-gate.md skips Step 7.2 and 8a entirely.
        The aggregate_verdicts call in Step 9 receives exactly two paths.
        There is no codex verdict to detect conflicts against, so conflicts == [].
        This test explicitly asserts that behaviour.
        """
        p1 = _write_verdict_file(
            tmp_path, "v1.json",
            _make_verdict(agent="code-review-agent", verdict="pass")
        )
        p2 = _write_verdict_file(
            tmp_path, "v2.json",
            _make_verdict(agent="phase-goals-agent", verdict="pass")
        )
        result = aggregate_verdicts([p1, p2])
        # Key degrade assertion: no codex conflicts because codex was never present
        assert result["conflicts"] == [], (
            "Degrade path must produce zero conflicts (codex absent means no codex-vs-subagent disagreement)"
        )
        assert result["result"] == "pass"


# ===========================================================================
# 6. Codex-present path — three-verdict AND aggregation
#    (live codex exec: SKIP — codex binary found but unauthed in this environment;
#     see loop-050-2 handoff for details)
# ===========================================================================

class TestCodexPresentPath:
    """Codex present: three verdicts (code-review + phase-goals + codex) ANDed correctly.

    Live codex execution is skipped in this environment (codex binary present but
    no ~/.codex/auth.json, $CODEX_API_KEY, or $OPENAI_API_KEY found).
    The unit-level 3-verdict AND test is the load-bearing guarantee.
    """

    def test_three_verdicts_all_pass(self, tmp_path):
        """Three verdicts (incl. codex) all pass -> result='pass', no conflicts."""
        p1 = _write_verdict_file(
            tmp_path, "phase-12-attempt-1-code-review-agent.json",
            _make_verdict(agent="code-review-agent", verdict="pass")
        )
        p2 = _write_verdict_file(
            tmp_path, "phase-12-attempt-1-phase-goals-agent.json",
            _make_verdict(agent="phase-goals-agent", verdict="pass")
        )
        p3 = _write_verdict_file(
            tmp_path, "phase-12-attempt-1-codex.json",
            _make_verdict(agent="codex", verdict="pass", backend="codex")
        )
        result = aggregate_verdicts([p1, p2, p3])
        assert result["result"] == "pass"
        assert result["conflicts"] == []
        assert result["missing"] == []

    def test_three_verdicts_codex_fails(self, tmp_path):
        """Three verdicts, codex fails -> result='fail' (AND: any fail -> fail)."""
        p1 = _write_verdict_file(
            tmp_path, "phase-12-attempt-1-code-review-agent.json",
            _make_verdict(agent="code-review-agent", verdict="pass")
        )
        p2 = _write_verdict_file(
            tmp_path, "phase-12-attempt-1-phase-goals-agent.json",
            _make_verdict(agent="phase-goals-agent", verdict="pass")
        )
        p3 = _write_verdict_file(
            tmp_path, "phase-12-attempt-1-codex.json",
            _make_verdict(agent="codex", verdict="fail", backend="codex")
        )
        result = aggregate_verdicts([p1, p2, p3])
        assert result["result"] == "fail"
        # Codex fails but both subagents pass -> conflict detected
        assert len(result["conflicts"]) > 0, "Expected conflict: codex=fail vs subagents=pass"

    def test_three_verdicts_subagent_fails_codex_passes(self, tmp_path):
        """Three verdicts, subagent fails, codex passes -> fail + conflict."""
        p1 = _write_verdict_file(
            tmp_path, "code-review.json",
            _make_verdict(agent="code-review-agent", verdict="pass")
        )
        p2 = _write_verdict_file(
            tmp_path, "phase-goals.json",
            _make_verdict(agent="phase-goals-agent", verdict="fail")
        )
        p3 = _write_verdict_file(
            tmp_path, "codex.json",
            _make_verdict(agent="codex", verdict="pass", backend="codex")
        )
        result = aggregate_verdicts([p1, p2, p3])
        assert result["result"] == "fail"  # any-fail rule
        assert len(result["conflicts"]) > 0, "Expected conflict: codex=pass vs phase-goals-agent=fail"
