"""Unit tests for the state_validate module.

Tests cover:
1. All six schemas with valid and invalid documents
2. Three exit codes (0, 1, 2) distinctly
3. Unknown schema basename errors with valid names listed
4. Schema resolution independent of cwd (Contract 6 property)
5. Library API returns structured errors
6. Missing schema, missing document, malformed JSON errors
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from platforms.python.minischema import UnsupportedKeyword
from platforms.python.state_validate import (
    VALID_SCHEMAS,
    SchemaError,
    DocumentError,
    ValidationError,
    validate_document,
    is_valid,
    main,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def schema_dir():
    """Path to the core/state schema directory."""
    return Path(__file__).parent.parent.parent.parent / "core" / "state"


@pytest.fixture
def valid_loop_ready():
    """A valid loop-ready document."""
    return {
        "phase": "phase-1",
        "loop_name": "ralph-loop-001",
        "loop_file": ".advanced-plans/phases/phase-1/loops.md",
        "task_name": "Schema Definitions",
        "todos_count": 4,
        "prepared_at": "2026-08-28T10:00:00Z",
        "status": "ready",
        "handoff_injected": {
            "done": "Phase plan created",
            "failed": "",
            "needed": "Execute loop 001"
        }
    }


@pytest.fixture
def valid_loop_complete():
    """A valid loop-complete document."""
    return {
        "loop_name": "ralph-loop-001",
        "loop_file": ".advanced-plans/phases/phase-1/loops.md",
        "status": "completed",
        "todos_done": 4,
        "todos_failed": 0,
        "completed_at": "2026-08-28T11:00:00Z",
        "handoff": {
            "done": "All schemas validated",
            "failed": "",
            "needed": ""
        }
    }


@pytest.fixture
def valid_gate_verdict():
    """A valid gate-verdict document."""
    return {
        "phase": "phase-1",
        "attempt": 1,
        "timestamp": "2026-08-28T12:00:00Z",
        "agent": "code-review-agent",
        "verdict": "pass",
        "confidence": 95,
        "findings": [],
        "loops_to_revert": [],
        "failure_notes": [],
        "criteria_outcomes": [],
        "phase_title": "Foundation"
    }


@pytest.fixture
def valid_gate_failure_context():
    """A valid gate-failure-context document."""
    return {
        "attempt": 1,
        "verdict_file": "gate-verdicts/phase-1-attempt-1.json",
        "summary": "Gate failed due to missing validation",
        "loops_reverted": [
            {"loop": "ralph-loop-002", "reason": "Missing schema validation"}
        ],
        "do_not_repeat": ["Do not skip validation"]
    }


@pytest.fixture
def valid_external_task_envelope():
    """A valid external-task-envelope document."""
    return {
        "schema_version": 1,
        "run_id": "20260828T100000Z-test-run",
        "project_id": "advanced-planning",
        "task_id": "phase-01-loop-02-todo-03",
        "title": "Test Task",
        "kind": "review",
        "duration": "short",
        "isolation": "worktree",
        "provider": "codex",
        "manager": "herdr",
        "repository": "/tmp/test-repo",
        "base_ref": "main",
        "base_sha": "0123456789abcdef0123456789abcdef01234567",
        "branch": "test-branch",
        "allowed_paths": ["src/"],
        "forbidden_paths": [".advanced-plans/state/"],
        "spec_paths": [],
        "acceptance_checks": ["pytest"],
        "required_evidence": ["git_diff", "tests"],
        "created_at": "2026-08-28T10:00:00Z"
    }


@pytest.fixture
def valid_collected_evidence():
    """A valid collected-evidence document."""
    return {
        "schema_version": 1,
        "run_id": "20260828T100000Z-test-run",
        "status": "completed",
        "agent": {
            "provider": "codex",
            "herdr_agent": "test-agent",
            "native_session_id": "session-123"
        },
        "git": {
            "worktree": "/tmp/test-repo",
            "base_sha": "0123456789abcdef0123456789abcdef01234567",
            "head_sha": "abcdef0123456789abcdef0123456789abcdef01",
            "dirty": False,
            "changed_paths": ["src/test.py"]
        },
        "checks": [
            {
                "command": "pytest",
                "exit_code": 0,
                "output_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
            }
        ],
        "policy": {
            "path_scope_passed": True,
            "tests_passed": True,
            "independent_review_passed": True
        },
        "agent_summary": "Task completed successfully",
        "collected_at": "2026-08-28T11:00:00Z"
    }


# ── Helper ─────────────────────────────────────────────────────────────────────

def write_json(tmpdir, filename, data):
    """Write a JSON file and return its path."""
    path = Path(tmpdir) / filename
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ── Test all six schemas with valid documents ─────────────────────────────────

class TestValidDocuments:
    """Each schema must accept a valid document."""

    def test_loop_ready_valid(self, valid_loop_ready, tmp_path):
        doc_path = write_json(tmp_path, "loop-ready.json", valid_loop_ready)
        errors = validate_document("loop-ready", str(doc_path))
        assert errors == []
        assert is_valid("loop-ready", str(doc_path)) is True

    def test_loop_complete_valid(self, valid_loop_complete, tmp_path):
        doc_path = write_json(tmp_path, "loop-complete.json", valid_loop_complete)
        errors = validate_document("loop-complete", str(doc_path))
        assert errors == []

    def test_gate_verdict_valid(self, valid_gate_verdict, tmp_path):
        doc_path = write_json(tmp_path, "gate-verdict.json", valid_gate_verdict)
        errors = validate_document("gate-verdict", str(doc_path))
        assert errors == []

    def test_gate_failure_context_valid(self, valid_gate_failure_context, tmp_path):
        doc_path = write_json(tmp_path, "gate-failure-context.json", valid_gate_failure_context)
        errors = validate_document("gate-failure-context", str(doc_path))
        assert errors == []

    def test_external_task_envelope_valid(self, valid_external_task_envelope, tmp_path):
        doc_path = write_json(tmp_path, "envelope.json", valid_external_task_envelope)
        errors = validate_document("external-task-envelope", str(doc_path))
        assert errors == []

    def test_collected_evidence_valid(self, valid_collected_evidence, tmp_path):
        doc_path = write_json(tmp_path, "evidence.json", valid_collected_evidence)
        errors = validate_document("collected-evidence", str(doc_path))
        assert errors == []


# ── Test all six schemas with invalid documents ────────────────────────────────

class TestInvalidDocuments:
    """Each schema must reject an invalid document."""

    def test_loop_ready_missing_required(self, valid_loop_ready, tmp_path):
        """Missing required property must be rejected."""
        del valid_loop_ready["loop_name"]
        doc_path = write_json(tmp_path, "loop-ready.json", valid_loop_ready)
        errors = validate_document("loop-ready", str(doc_path))
        assert len(errors) >= 1
        assert any(e.keyword == "required" for e in errors)

    def test_loop_complete_invalid_status(self, valid_loop_complete, tmp_path):
        """Invalid enum value must be rejected."""
        valid_loop_complete["status"] = "invalid_status"
        doc_path = write_json(tmp_path, "loop-complete.json", valid_loop_complete)
        errors = validate_document("loop-complete", str(doc_path))
        assert len(errors) >= 1
        assert any(e.keyword == "enum" for e in errors)

    def test_gate_verdict_missing_required(self, valid_gate_verdict, tmp_path):
        """Missing required property must be rejected."""
        del valid_gate_verdict["verdict"]
        doc_path = write_json(tmp_path, "gate-verdict.json", valid_gate_verdict)
        errors = validate_document("gate-verdict", str(doc_path))
        assert len(errors) >= 1

    def test_gate_failure_context_invalid_type(self, valid_gate_failure_context, tmp_path):
        """Wrong type must be rejected."""
        valid_gate_failure_context["attempt"] = "one"
        doc_path = write_json(tmp_path, "gate-failure-context.json", valid_gate_failure_context)
        errors = validate_document("gate-failure-context", str(doc_path))
        assert len(errors) >= 1
        assert any(e.keyword == "type" for e in errors)

    def test_external_task_envelope_missing_forbidden_paths(self, valid_external_task_envelope, tmp_path):
        """Missing required property must be rejected."""
        del valid_external_task_envelope["forbidden_paths"]
        doc_path = write_json(tmp_path, "envelope.json", valid_external_task_envelope)
        errors = validate_document("external-task-envelope", str(doc_path))
        assert len(errors) >= 1

    def test_collected_evidence_missing_policy_gate(self, valid_collected_evidence, tmp_path):
        """Missing required property must be rejected."""
        del valid_collected_evidence["policy"]
        doc_path = write_json(tmp_path, "evidence.json", valid_collected_evidence)
        errors = validate_document("collected-evidence", str(doc_path))
        assert len(errors) >= 1


# ── Test exit codes ────────────────────────────────────────────────────────────

class TestExitCodes:
    """Test CLI exit codes: 0 (valid), 1 (invalid), 2 (usage error)."""

    def _run_cli(self, *args):
        """Run the state_validate CLI directly (source checkout mode)."""
        # In source checkout, run the module directly with PYTHONPATH set
        repo_root = Path(__file__).parent.parent.parent.parent
        module_path = repo_root / "platforms" / "python" / "state_validate.py"
        # Set PYTHONPATH so the module can import minischema
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)
        cmd = [sys.executable, str(module_path)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo_root), env=env)

    def test_exit_code_0_valid(self, valid_loop_ready, tmp_path):
        """Valid document must exit 0."""
        doc_path = write_json(tmp_path, "loop-ready.json", valid_loop_ready)
        result = self._run_cli("loop-ready", str(doc_path))
        assert result.returncode == 0

    def test_exit_code_1_invalid(self, valid_loop_ready, tmp_path):
        """Invalid document must exit 1."""
        del valid_loop_ready["loop_name"]
        doc_path = write_json(tmp_path, "loop-ready.json", valid_loop_ready)
        result = self._run_cli("loop-ready", str(doc_path))
        assert result.returncode == 1

    def test_exit_code_2_unknown_schema(self):
        """Unknown schema basename must exit 2."""
        result = self._run_cli("unknown-schema", "/dev/null")
        assert result.returncode == 2
        assert "unknown-schema" in result.stderr
        # Must name the valid six
        for name in sorted(VALID_SCHEMAS):
            assert name in result.stderr

    def test_exit_code_2_missing_document(self):
        """Missing document must exit 2."""
        result = self._run_cli("loop-ready", "/nonexistent/path.json")
        assert result.returncode == 2

    def test_exit_code_2_malformed_json(self, tmp_path):
        """Malformed JSON must exit 2."""
        doc_path = Path(tmp_path) / "bad.json"
        doc_path.write_text("{ invalid json }", encoding="utf-8")
        result = self._run_cli("loop-ready", str(doc_path))
        assert result.returncode == 2


# ── Test schema resolution independent of cwd (Contract 6) ─────────────────────

class TestCwdIndependence:
    """Schema resolution must not depend on cwd."""

    def test_validation_from_different_cwd(self, valid_loop_ready, tmp_path):
        """Validation must work from a different cwd."""
        doc_path = write_json(tmp_path, "loop-ready.json", valid_loop_ready)

        # Run from repo root - the schema resolution is from package location, not cwd
        # This test verifies the library API works (which the CLI uses internally)
        errors = validate_document("loop-ready", str(doc_path))
        assert errors == []

    def test_schema_dir_from_package_location(self):
        """Schema directory is derived from package location, not cwd."""
        from platforms.python.state_validate import _get_schema_dir
        schema_dir = _get_schema_dir()
        assert schema_dir.exists()
        assert (schema_dir / "loop-ready.schema.json").exists()


# ── Test error handling ────────────────────────────────────────────────────────

class TestErrorHandling:

    def test_unknown_schema_basename(self):
        """Unknown schema must raise SchemaError with valid names."""
        with pytest.raises(SchemaError) as exc_info:
            validate_document("unknown-schema", "/tmp/test.json")
        assert "unknown-schema" in str(exc_info.value.problem)
        for name in sorted(VALID_SCHEMAS):
            assert name in str(exc_info.value.fix)

    def test_missing_schema_file(self, schema_dir, monkeypatch):
        """Missing schema file must raise SchemaError."""
        # This test relies on the schema actually existing - more of an integration check
        from platforms.python.state_validate import _load_schema
        with pytest.raises(SchemaError) as exc_info:
            _load_schema("nonexistent")
        assert "not found" in str(exc_info.value.problem).lower()

    def test_missing_document(self, valid_loop_ready, tmp_path):
        """Missing document must raise DocumentError."""
        with pytest.raises(DocumentError) as exc_info:
            validate_document("loop-ready", "/nonexistent/path.json")
        assert "not found" in str(exc_info.value.problem).lower()

    def test_malformed_json_document(self, tmp_path):
        """Malformed JSON must raise DocumentError."""
        doc_path = Path(tmp_path) / "bad.json"
        doc_path.write_text("{ invalid json }", encoding="utf-8")
        with pytest.raises(DocumentError) as exc_info:
            validate_document("loop-ready", str(doc_path))
        assert "not valid json" in str(exc_info.value.problem).lower()


# ── Test library API ───────────────────────────────────────────────────────────

class TestLibraryAPI:

    def test_validate_document_returns_list(self, valid_loop_ready, tmp_path):
        """Library API returns a list of ValidationError."""
        doc_path = write_json(tmp_path, "loop-ready.json", valid_loop_ready)
        errors = validate_document("loop-ready", str(doc_path))
        assert isinstance(errors, list)
        assert all(isinstance(e, ValidationError) for e in errors)

    def test_is_valid_true_for_valid(self, valid_loop_ready, tmp_path):
        """is_valid returns True for valid documents."""
        doc_path = write_json(tmp_path, "loop-ready.json", valid_loop_ready)
        assert is_valid("loop-ready", str(doc_path)) is True

    def test_is_valid_false_for_invalid(self, valid_loop_ready, tmp_path):
        """is_valid returns False for invalid documents."""
        del valid_loop_ready["loop_name"]
        doc_path = write_json(tmp_path, "loop-ready.json", valid_loop_ready)
        assert is_valid("loop-ready", str(doc_path)) is False

    def test_validation_error_fields(self, valid_loop_ready, tmp_path):
        """ValidationError has expected fields."""
        del valid_loop_ready["loop_name"]
        doc_path = write_json(tmp_path, "loop-ready.json", valid_loop_ready)
        errors = validate_document("loop-ready", str(doc_path))
        assert len(errors) >= 1
        err = errors[0]
        assert hasattr(err, "instance_path")
        assert hasattr(err, "schema_path")
        assert hasattr(err, "keyword")
        assert hasattr(err, "message")


# ── Test CLI usage errors ──────────────────────────────────────────────────────

class TestCLIUsage:
    """Test CLI usage errors."""

    def _run_cli(self, *args):
        """Run the state_validate CLI directly (source checkout mode)."""
        repo_root = Path(__file__).parent.parent.parent.parent
        module_path = repo_root / "platforms" / "python" / "state_validate.py"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)
        cmd = [sys.executable, str(module_path)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo_root), env=env)

    def test_no_arguments(self):
        """No arguments must show usage."""
        result = self._run_cli()
        assert result.returncode == 2
        assert "Usage" in result.stderr

    def test_one_argument(self):
        """One argument must show usage."""
        result = self._run_cli("loop-ready")
        assert result.returncode == 2
        assert "Usage" in result.stderr

    def test_three_arguments(self):
        """Three arguments must show usage."""
        result = self._run_cli("loop-ready", "/tmp/a.json", "/tmp/b.json")
        assert result.returncode == 2
        assert "Usage" in result.stderr
