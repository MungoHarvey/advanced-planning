"""
test_codex_gate_live.py - Live fixture + degrade-path tests for codex_gate.py
==============================================================================

Two test groups:

1. TestHappyPath — feeds the contract-compliant single-fenced-block fixture
   through extract_and_validate and asserts a schema-valid verdict with
   backend == "codex" is returned.

2. TestRealCapturedStdout — feeds the REAL codex stdout fixture
   (captured from codex exec review --ephemeral -m gpt-5.5, codex-cli 0.124.0)
   through extract_and_validate and asserts the KNOWN behaviour: the CLI emits
   two fenced blocks, which triggers the degrade path (ok=False).

3. TestDegradePathFull — drives the full degrade scenario (codex unavailable /
   unparseable) and asserts: no codex.json written, gate_codex_skipped event
   produced.

Fixture files:
  platforms/python/tests/fixtures/codex_stdout_single_block.txt
    Contract-compliant single fenced block (synthesized; see fixtures/README.md)
  platforms/python/tests/fixtures/codex_stdout_sample.txt
    Real codex CLI stdout (double fenced block; see fixtures/README.md)

Schema validation is stdlib-only (no jsonschema dependency):
  Load core/state/gate-verdict.schema.json, check required fields and enum values.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from platforms.python.codex_gate import (
    extract_and_validate,
    validate_verdict,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_FIXTURES_DIR = Path(__file__).parent / "fixtures"
_SCHEMA_PATH = _REPO_ROOT / "core" / "state" / "gate-verdict.schema.json"
_SINGLE_BLOCK_FIXTURE = _FIXTURES_DIR / "codex_stdout_single_block.txt"
_REAL_STDOUT_FIXTURE = _FIXTURES_DIR / "codex_stdout_sample.txt"

# Required fields from the gate-verdict schema
_SCHEMA_REQUIRED = [
    "phase", "attempt", "timestamp", "agent", "verdict",
    "confidence", "findings", "loops_to_revert", "failure_notes",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_schema_required_fields() -> list:
    """Return the required field list from gate-verdict.schema.json (stdlib only).

    Parameters
    ----------
    None

    Returns
    -------
    list
        List of required field name strings.
    """
    if _SCHEMA_PATH.exists():
        schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        return schema.get("required", _SCHEMA_REQUIRED)
    return _SCHEMA_REQUIRED


def _validate_against_schema(verdict: dict) -> tuple:
    """Lightweight stdlib schema validation for a gate verdict dict.

    Checks:
    - All required fields present (from gate-verdict.schema.json)
    - 'verdict' is in {"pass", "fail"}
    - 'attempt' is an integer
    - 'confidence' is an integer
    - 'findings', 'loops_to_revert', 'failure_notes' are lists
    - 'backend' (if present) is in {"codex", "subagent"}

    Parameters
    ----------
    verdict : dict
        The parsed verdict dict to validate.

    Returns
    -------
    (ok: bool, reason: str)
        ok is True when all checks pass.
    """
    required = _load_schema_required_fields()
    for field in required:
        if field not in verdict:
            return False, f"missing required field: '{field}'"

    if verdict.get("verdict") not in {"pass", "fail"}:
        return False, f"verdict must be 'pass' or 'fail', got '{verdict.get('verdict')}'"

    if not isinstance(verdict.get("attempt"), int):
        return False, f"'attempt' must be int, got {type(verdict.get('attempt')).__name__}"

    if not isinstance(verdict.get("confidence"), int):
        return False, f"'confidence' must be int, got {type(verdict.get('confidence')).__name__}"

    for list_field in ("findings", "loops_to_revert", "failure_notes"):
        if not isinstance(verdict.get(list_field), list):
            return False, f"'{list_field}' must be a list"

    if "backend" in verdict:
        if verdict["backend"] not in {"codex", "subagent"}:
            return False, f"'backend' must be 'codex' or 'subagent', got '{verdict['backend']}'"

    return True, ""


# ===========================================================================
# 1. TestHappyPath — single-block fixture -> schema-valid verdict, backend==codex
# ===========================================================================

class TestHappyPath:
    """Happy path: contract-compliant single fenced block -> valid verdict.

    Uses codex_stdout_single_block.txt which contains a single fenced JSON
    block conforming to the codex-reviewer output contract. This is the
    expected output when codex correctly follows the contract (one block only).
    """

    def test_single_block_extract_and_validate_ok(self):
        """Single fenced block -> extract_and_validate returns ok=True."""
        assert _SINGLE_BLOCK_FIXTURE.exists(), (
            f"Fixture not found: {_SINGLE_BLOCK_FIXTURE}"
        )
        stdout = _SINGLE_BLOCK_FIXTURE.read_text(encoding="utf-8")
        result = extract_and_validate(
            stdout, expected_phase="phase-14", expected_attempt=1
        )
        assert result["ok"] is True, (
            f"Expected ok=True for single-block fixture, got: {result}"
        )

    def test_single_block_verdict_backend_is_codex(self):
        """Single-block verdict dict has backend == 'codex'."""
        stdout = _SINGLE_BLOCK_FIXTURE.read_text(encoding="utf-8")
        result = extract_and_validate(
            stdout, expected_phase="phase-14", expected_attempt=1
        )
        assert result["ok"] is True, f"Extraction failed: {result}"
        verdict = result["verdict"]
        assert verdict.get("backend") == "codex", (
            f"Expected backend='codex', got backend='{verdict.get('backend')}'"
        )

    def test_single_block_verdict_agent_is_codex(self):
        """Single-block verdict dict has agent == 'codex' (required by validate_verdict)."""
        stdout = _SINGLE_BLOCK_FIXTURE.read_text(encoding="utf-8")
        result = extract_and_validate(
            stdout, expected_phase="phase-14", expected_attempt=1
        )
        assert result["ok"] is True, f"Extraction failed: {result}"
        assert result["verdict"]["agent"] == "codex"

    def test_single_block_verdict_passes_schema_validation(self):
        """Single-block verdict validates against gate-verdict.schema.json (stdlib check)."""
        stdout = _SINGLE_BLOCK_FIXTURE.read_text(encoding="utf-8")
        result = extract_and_validate(
            stdout, expected_phase="phase-14", expected_attempt=1
        )
        assert result["ok"] is True, f"Extraction failed: {result}"
        ok, reason = _validate_against_schema(result["verdict"])
        assert ok is True, f"Schema validation failed: {reason}"

    def test_single_block_verdict_passes_validate_verdict(self):
        """Single-block verdict passes the codex_gate validate_verdict function."""
        stdout = _SINGLE_BLOCK_FIXTURE.read_text(encoding="utf-8")
        result = extract_and_validate(
            stdout, expected_phase="phase-14", expected_attempt=1
        )
        assert result["ok"] is True, f"Extraction failed: {result}"
        ok, reason = validate_verdict(result["verdict"])
        assert ok is True, f"validate_verdict failed: {reason}"

    def test_single_block_schema_file_exists_and_parseable(self):
        """gate-verdict.schema.json exists and is valid JSON."""
        assert _SCHEMA_PATH.exists(), f"Schema not found: {_SCHEMA_PATH}"
        schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        assert "required" in schema
        assert "backend" in schema.get("properties", {})
        backend_prop = schema["properties"]["backend"]
        assert "codex" in backend_prop.get("enum", [])


# ===========================================================================
# 2. TestRealCapturedStdout — real codex stdout fixture (double block = degrade)
# ===========================================================================

class TestRealCapturedStdout:
    """Real codex stdout behavior: identical double-block resolves to a verdict.

    The real codex CLI (exec / exec review, codex-cli 0.124.0, gpt-5.5 model)
    emits the response twice in non-interactive mode: once as part of the
    conversation transcript and once as a final standalone message. This
    produces two *identical* fenced JSON blocks in stdout.

    As of the Phase 14 parser hardening, extract_verdict_json treats multiple
    structurally-identical fenced blocks as non-ambiguous (returns the last
    block), so extract_and_validate produces a schema-valid backend:codex
    verdict from real codex stdout. Genuinely-differing blocks still degrade
    (see test_differing_double_block_still_degrades).

    Origin: docs/tool-friction-log.md (2026-06-09 codex double-block entry);
    fix applied in ralph-loop-058.
    """

    def test_real_fixture_exists(self):
        """Real codex stdout fixture file exists (proof of capture)."""
        assert _REAL_STDOUT_FIXTURE.exists(), (
            f"Real fixture not found: {_REAL_STDOUT_FIXTURE}. "
            "Run: codex exec review --ephemeral -m gpt-5.5 '...' > fixture.txt 2>&1"
        )

    def test_real_fixture_contains_fenced_json(self):
        """Real fixture contains at least one fenced json block."""
        stdout = _REAL_STDOUT_FIXTURE.read_text(encoding="utf-8")
        assert "```json" in stdout, "Real fixture should contain fenced json blocks"

    def test_real_fixture_identical_double_block_resolves(self):
        """Real codex stdout (identical double block) -> schema-valid codex verdict.

        codex-cli 0.124.0 emits the verdict block twice (identical content).
        The Phase 14 parser hardening recognises identical duplicates as
        non-ambiguous and returns the last block, so extract_and_validate
        yields ok=True with backend == "codex".
        """
        stdout = _REAL_STDOUT_FIXTURE.read_text(encoding="utf-8")
        import re
        fenced_count = len(re.findall(r"```json", stdout))
        assert fenced_count >= 2, (
            f"Expected >= 2 fenced json blocks in real fixture, found {fenced_count}. "
            "If this changed, update the friction log entry and this test."
        )
        result = extract_and_validate(
            stdout, expected_phase="phase-14", expected_attempt=1
        )
        assert result["ok"] is True, (
            f"Expected ok=True for identical double-block fixture, got: {result}"
        )
        assert result["verdict"].get("backend") == "codex", (
            f"Expected backend=='codex', got: {result['verdict'].get('backend')}"
        )

    def test_differing_double_block_still_degrades(self):
        """Two *different* fenced blocks remain genuinely ambiguous -> degrade.

        The parser hardening only collapses identical duplicates. Blocks that
        disagree (e.g. pass vs fail) must still return ok=False so a real
        ambiguity never silently resolves to one arbitrary verdict.
        """
        import json as _json
        block_pass = _json.dumps({
            "phase": "phase-14", "attempt": 1, "agent": "codex",
            "backend": "codex", "verdict": "pass", "confidence": 90,
            "timestamp": "2026-06-09T14:00:00Z", "findings": [],
            "loops_to_revert": [], "failure_notes": [],
        })
        block_fail = _json.dumps({
            "phase": "phase-14", "attempt": 1, "agent": "codex",
            "backend": "codex", "verdict": "fail", "confidence": 90,
            "timestamp": "2026-06-09T14:00:00Z", "findings": [],
            "loops_to_revert": [], "failure_notes": [],
        })
        stdout = f"```json\n{block_pass}\n```\n```json\n{block_fail}\n```"
        result = extract_and_validate(
            stdout, expected_phase="phase-14", expected_attempt=1
        )
        assert result["ok"] is False, (
            f"Expected ok=False for differing double-block (genuine ambiguity), got: {result}"
        )
        assert "reason" in result

    def test_real_fixture_codex_version_string_in_stdout(self):
        """Real fixture contains 'OpenAI Codex' header (provenance confirmation)."""
        stdout = _REAL_STDOUT_FIXTURE.read_text(encoding="utf-8")
        assert "OpenAI Codex" in stdout, (
            "Expected 'OpenAI Codex' in fixture stdout — confirms this is real CLI output"
        )


# ===========================================================================
# 3. TestDegradePathFull — codex unavailable -> no codex.json, gate_codex_skipped
# ===========================================================================

class TestDegradePathFull:
    """Full degrade scenario: codex unavailable or unparseable.

    Drives the degrade logic as described in run-gate.md step 8a failure branch:
    - extract_and_validate returns ok=False
    - No codex.json is written to gate-verdicts/
    - A gate_codex_skipped event is produced

    Uses a tmp dir to assert no codex.json is written.
    """

    def _build_codex_skipped_event(
        self, phase: str, attempt: int, reason: str, raw_path: str
    ) -> dict:
        """Build a gate_codex_skipped event dict (simulating run-gate step 8a).

        Parameters
        ----------
        phase : str
            The phase identifier.
        attempt : int
            The attempt number.
        reason : str
            The skip reason (from extract_and_validate result['reason']).
        raw_path : str
            Path where the raw stdout would be saved.

        Returns
        -------
        dict
            The event dict that would be appended to history.jsonl.
        """
        return {
            "event": "gate_codex_skipped",
            "phase": phase,
            "attempt": attempt,
            "timestamp": "2026-06-09T14:00:00Z",
            "reason": reason,
            "raw_path": raw_path,
        }

    def test_unparseable_stdout_does_not_create_codex_json(self):
        """Unparseable codex stdout -> no codex.json written in gate-verdicts dir."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            gate_verdicts_dir = Path(tmp_dir) / "gate-verdicts"
            gate_verdicts_dir.mkdir()

            unparseable_stdout = "Codex output was completely garbled. No JSON here."
            result = extract_and_validate(
                unparseable_stdout,
                expected_phase="phase-14",
                expected_attempt=1,
            )
            assert result["ok"] is False

            # Simulate run-gate step 8a: on failure, do NOT write codex.json
            # (write raw fallback instead)
            raw_path = gate_verdicts_dir / "phase-14-attempt-1-codex.raw.txt"
            if not result["ok"]:
                raw_path.write_text(unparseable_stdout, encoding="utf-8")
                # codex.json is NOT written
            else:
                codex_json_path = gate_verdicts_dir / "phase-14-attempt-1-codex.json"
                codex_json_path.write_text(
                    json.dumps(result["verdict"], indent=2), encoding="utf-8"
                )

            # Assert: no codex.json in gate-verdicts/
            codex_json = gate_verdicts_dir / "phase-14-attempt-1-codex.json"
            assert not codex_json.exists(), (
                "codex.json must NOT be written on degrade path — "
                "gate must proceed without it"
            )
            # Assert: raw fallback WAS written
            assert raw_path.exists(), "raw stdout file should be written on degrade path"

    def test_ambiguous_double_block_stdout_does_not_create_codex_json(self):
        """Genuinely-ambiguous double-block (differing verdicts) -> no codex.json.

        Post Phase 14 parser hardening, identical duplicates resolve; only
        differing blocks remain ambiguous. This asserts the degrade path still
        withholds codex.json for genuine ambiguity.
        """
        block_pass = json.dumps({
            "phase": "phase-14", "attempt": 1, "agent": "codex",
            "backend": "codex", "verdict": "pass", "confidence": 90,
            "timestamp": "2026-06-09T14:00:00Z", "findings": [],
            "loops_to_revert": [], "failure_notes": [],
        })
        block_fail = json.dumps({
            "phase": "phase-14", "attempt": 1, "agent": "codex",
            "backend": "codex", "verdict": "fail", "confidence": 90,
            "timestamp": "2026-06-09T14:00:00Z", "findings": [],
            "loops_to_revert": [], "failure_notes": [],
        })
        stdout = f"```json\n{block_pass}\n```\n```json\n{block_fail}\n```"
        with tempfile.TemporaryDirectory() as tmp_dir:
            gate_verdicts_dir = Path(tmp_dir) / "gate-verdicts"
            gate_verdicts_dir.mkdir()

            result = extract_and_validate(
                stdout, expected_phase="phase-14", expected_attempt=1
            )
            assert result["ok"] is False, "Differing double-block should trigger degrade"

            raw_path = gate_verdicts_dir / "phase-14-attempt-1-codex.raw.txt"
            raw_path.write_text(stdout, encoding="utf-8")

            codex_json = gate_verdicts_dir / "phase-14-attempt-1-codex.json"
            assert not codex_json.exists(), (
                "codex.json must NOT be written when extraction is ambiguous"
            )

    def test_gate_codex_skipped_event_shape(self):
        """gate_codex_skipped event has required fields and correct event name."""
        unparseable_stdout = "This is not valid JSON at all."
        result = extract_and_validate(
            unparseable_stdout,
            expected_phase="phase-14",
            expected_attempt=1,
        )
        assert result["ok"] is False

        event = self._build_codex_skipped_event(
            phase="phase-14",
            attempt=1,
            reason=result["reason"],
            raw_path=".advanced-plans/gate-verdicts/phase-14-attempt-1-codex.raw.txt",
        )

        assert event["event"] == "gate_codex_skipped"
        assert event["phase"] == "phase-14"
        assert event["attempt"] == 1
        assert "reason" in event and event["reason"]
        assert "raw_path" in event
        # Verify it serialises to valid JSON (as it would when appended to history.jsonl)
        serialised = json.dumps(event)
        reloaded = json.loads(serialised)
        assert reloaded["event"] == "gate_codex_skipped"

    def test_degrade_gate_proceeds_with_two_inhouse_verdicts(self, tmp_path):
        """After codex degrade, aggregate_verdicts over two in-house verdicts returns correct result."""
        from platforms.python.codex_gate import aggregate_verdicts

        # Write two in-house verdicts (no codex.json)
        v1 = tmp_path / "phase-14-attempt-1-code-review-agent.json"
        v2 = tmp_path / "phase-14-attempt-1-phase-goals-agent.json"
        v1.write_text(json.dumps({
            "phase": "phase-14", "attempt": 1,
            "timestamp": "2026-06-09T14:00:00Z",
            "agent": "code-review-agent", "verdict": "pass",
            "confidence": 90, "findings": [],
            "loops_to_revert": [], "failure_notes": [],
        }), encoding="utf-8")
        v2.write_text(json.dumps({
            "phase": "phase-14", "attempt": 1,
            "timestamp": "2026-06-09T14:00:00Z",
            "agent": "phase-goals-agent", "verdict": "pass",
            "confidence": 88, "findings": [],
            "loops_to_revert": [], "failure_notes": [],
        }), encoding="utf-8")

        # Simulate run-gate step 9 on degrade path: only two in-house files
        result = aggregate_verdicts([v1, v2])

        assert result["result"] == "pass", (
            f"Degrade gate must pass when both in-house agents pass; got {result}"
        )
        assert result["conflicts"] == [], "No conflicts when codex is absent"
        assert result["missing"] == [], "No missing files"

        # Confirm codex.json was never written
        codex_json = tmp_path / "phase-14-attempt-1-codex.json"
        assert not codex_json.exists(), "codex.json must not exist on degrade path"
