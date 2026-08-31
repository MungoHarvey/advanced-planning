"""
test_remediation_guards.py — Tests for the three guard defects (B1, B2, B3).

These tests verify the fixes for:
- B1: validate_diff_allowlist never consults the allowlist
- B2: validate_regateverdict_criteria_outcomes passes on empty criteria
- B3: archive_cross_phase_state skips when phase field is absent

Each test is designed to fail against the buggy behavior and pass after the fix.
"""

import json
import re
import tempfile
from pathlib import Path

import pytest

from platforms.python.remediation_controller import (
    validate_diff_allowlist,
    validate_regateverdict_criteria_outcomes,
)
from platforms.python.state_manager import (
    write_loop_ready,
    archive_cross_phase_state,
)


# ---------------------------------------------------------------------------
# B1: validate_diff_allowlist must consult both never-touch AND allowlist
# ---------------------------------------------------------------------------

class TestB1ValidateDiffAllowlist:
    """B1 fix: validate_diff_allowlist must reject paths not on the allowlist."""

    def test_github_workflows_ci_yml_is_not_ok(self):
        """
        Regression: .github/workflows/ci.yml was incorrectly allowed.
        This path is NOT on the allowlist, so it must be a violation.
        """
        ok, violations = validate_diff_allowlist([".github/workflows/ci.yml"])
        assert not ok, ".github/workflows/ci.yml must NOT pass allowlist check"
        assert any(v[0] == ".github/workflows/ci.yml" and v[1] == "not_allowlisted" 
                   for v in violations), \
            ".github/workflows/ci.yml must be flagged as not_allowlisted"

    def test_never_touch_path_is_violation(self):
        """A never-touch path is a violation with reason 'never_touch'."""
        ok, violations = validate_diff_allowlist([
            ".advanced-plans/phases/phase-13/loops.md"
        ])
        assert not ok
        assert any(v[0] == ".advanced-plans/phases/phase-13/loops.md" and v[1] == "never_touch" 
                   for v in violations)

    def test_not_allowlisted_path_is_violation(self):
        """A path not on the allowlist (and not never-touch) is a violation."""
        ok, violations = validate_diff_allowlist([
            ".github/workflows/ci.yml"
        ])
        assert not ok
        assert any(v[0] == ".github/workflows/ci.yml" and v[1] == "not_allowlisted" 
                   for v in violations)

    def test_allowlisted_non_never_touch_passes(self):
        """An allowlisted, non-never-touch path still passes."""
        ok, violations = validate_diff_allowlist([
            "platforms/python/state_manager.py"
        ])
        assert ok, "platforms/python/state_manager.py should pass (allowlisted, not never-touch)"
        assert violations == []

    def test_never_touch_and_not_allowlisted_are_distinguishable(self):
        """The two violation types must be distinguishable by reason."""
        ok, violations = validate_diff_allowlist([
            ".advanced-plans/phases/phase-13/loops.md",  # never_touch
            ".github/workflows/ci.yml",  # not_allowlisted
        ])
        assert not ok
        reasons = {v[1] for v in violations}
        assert "never_touch" in reasons, "never_touch reason must be present"
        assert "not_allowlisted" in reasons, "not_allowlisted reason must be present"


# ---------------------------------------------------------------------------
# B2: validate_regateverdict_criteria_outcomes must fail on empty criteria
# ---------------------------------------------------------------------------

class TestB2EmptyCriteria:
    """B2 fix: empty frozen_criteria must not report ok."""

    def test_empty_frozen_criteria_is_not_ok(self):
        """
        An empty frozen_criteria list means the criteria file was empty,
        unparsed, or never loaded — this is a failure, not success.
        """
        verdict = {"criteria_outcomes": []}
        ok, missing = validate_regateverdict_criteria_outcomes(verdict, [])
        assert not ok, "Empty frozen_criteria must not report ok"
        assert "empty_criteria" in missing, \
            "Missing list must contain 'empty_criteria' as the reason"

    def test_non_empty_frozen_criteria_works_normally(self):
        """Non-empty criteria list works as before."""
        verdict = {
            "criteria_outcomes": [
                {"criterion": "criterion A", "status": "met", "evidence": "e1"},
                {"criterion": "criterion B", "status": "met", "evidence": "e2"},
            ]
        }
        ok, missing = validate_regateverdict_criteria_outcomes(
            verdict, ["criterion A", "criterion B"]
        )
        assert ok
        assert missing == []

    def test_missing_criterion_still_detected(self):
        """Missing criteria are still detected after the empty check."""
        verdict = {
            "criteria_outcomes": [
                {"criterion": "criterion A", "status": "met", "evidence": "e1"},
            ]
        }
        ok, missing = validate_regateverdict_criteria_outcomes(
            verdict, ["criterion A", "criterion B"]
        )
        assert not ok
        assert "criterion B" in missing


# ---------------------------------------------------------------------------
# B3: write_loop_ready must emit phase; archive must handle missing phase
# ---------------------------------------------------------------------------

class TestB3PhaseField:
    """B3 fix: phase field must be emitted and missing phase must be archived."""

    def test_write_loop_ready_emits_phase_derived_from_loop_file(self):
        """phase is derived from loop_file path when not explicitly provided."""
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            result_path = write_loop_ready(
                state_dir,
                loop_name="ralph-loop-001",
                loop_file=".advanced-plans/phases/phase-16/loops.md",
                task_name="Test Task",
                todos_count=4,
            )
            data = json.loads(result_path.read_text(encoding="utf-8"))
            assert data["phase"] == "phase-16", \
                f"phase should be derived as 'phase-16', got {data.get('phase')}"

    def test_write_loop_ready_explicit_phase_wins(self):
        """Explicit phase= keyword overrides the derived value."""
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            result_path = write_loop_ready(
                state_dir,
                loop_name="ralph-loop-001",
                loop_file=".advanced-plans/phases/phase-16/loops.md",
                task_name="Test Task",
                todos_count=4,
                phase="phase-99",
            )
            data = json.loads(result_path.read_text(encoding="utf-8"))
            assert data["phase"] == "phase-99", \
                f"explicit phase should win, got {data.get('phase')}"

    def test_write_loop_ready_raises_if_no_phase_and_path_invalid(self):
        """If loop_file doesn't match phase-N pattern and no explicit phase, raise."""
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with pytest.raises(ValueError, match="phase"):
                write_loop_ready(
                    state_dir,
                    loop_name="ralph-loop-001",
                    loop_file="some/other/path/loops.md",
                    task_name="Test Task",
                    todos_count=4,
                )

    def test_loop_ready_validates_against_schema(self):
        """The written payload validates against loop-ready.schema.json."""
        schema_path = Path("core/state/loop-ready.schema.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            result_path = write_loop_ready(
                state_dir,
                loop_name="ralph-loop-001",
                loop_file=".advanced-plans/phases/phase-16/loops.md",
                task_name="Test Task",
                todos_count=4,
            )
            data = json.loads(result_path.read_text(encoding="utf-8"))
            
            # Basic validation: check all required fields are present
            required = schema.get("required", [])
            for field in required:
                assert field in data, f"Required field '{field}' missing from payload"
            
            # Check phase field specifically
            assert "phase" in data
            assert re.match(r"^phase-\d+$", data["phase"]), \
                f"phase '{data['phase']}' does not match pattern"

    def test_loop_ready_with_missing_phase_is_archived(self):
        """
        A loop-ready.json with no 'phase' field IS archived as stale.
        This test inverts the old test_no_archive_when_phase_field_absent.
        """
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "state"
            state_dir.mkdir()
            
            # Write a loop-ready.json WITHOUT a phase field
            ready = state_dir / "loop-ready.json"
            ready.write_text(
                json.dumps({
                    "loop_name": "ralph-loop-001",
                    "status": "ready",
                    # No 'phase' field — this is the bug condition
                }),
                encoding="utf-8",
            )
            
            result = archive_cross_phase_state(state_dir, current_phase="phase-11")
            
            assert result is not None, \
                "loop-ready.json without phase must be archived as stale"
            assert result.exists(), "Archived file must exist"
            assert ready.exists() is False, \
                "Original file must no longer exist in state_dir"


# ---------------------------------------------------------------------------
# Integration: schema validation
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    """Validate that written files conform to the schema."""

    def test_loop_ready_schema_required_fields(self):
        """All required fields in loop-ready.schema.json are present."""
        schema_path = Path("core/state/loop-ready.schema.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        
        # Check that 'phase' is in required
        assert "phase" in schema.get("required", []), \
            "'phase' must be in the required fields of loop-ready.schema.json"
        
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            result_path = write_loop_ready(
                state_dir,
                loop_name="ralph-loop-001",
                loop_file=".advanced-plans/phases/phase-16/loops.md",
                task_name="Test Task",
                todos_count=4,
            )
            data = json.loads(result_path.read_text(encoding="utf-8"))
            
            # Validate all required fields
            for field in schema.get("required", []):
                assert field in data, f"Missing required field: {field}"
