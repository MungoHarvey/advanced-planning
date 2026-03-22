"""Unit tests for platforms.python.versioning"""

import sys
from pathlib import Path

import pytest

# Adjust path so we can import from the package root when running from repo root
sys.path.insert(0, str(Path(__file__).parents[3]))

from platforms.python.versioning import (
    create_retry_version,
    freeze_loop_file,
    get_active_version,
    inject_failure_context,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

_SAMPLE_LOOP_CONTENT = """\
## Ralph Loop 001

```yaml
---
name: "ralph-loop-001"
task_name: "Sample Loop"

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-001-1"
    content: "Do something"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Something done"
    status: pending
    priority: high
  - id: "loop-001-2"
    content: "Do another thing"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Another thing done"
    status: in_progress
    priority: medium
  - id: "loop-001-3"
    content: "Already done"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Was done"
    status: completed
    priority: low
  - id: "loop-001-4"
    content: "Cancelled"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Was cancelled"
    status: cancelled
    priority: low
```
"""

_SAMPLE_VERDICT = {
    "attempt": 1,
    "verdict_file": "gate-verdicts/phase-1-attempt-1.json",
    "summary": "Code review found critical issues in schema definitions.",
    "loops_reverted": [
        {"loop": "ralph-loop-001", "reason": "Schema file contained invalid JSON."}
    ],
    "do_not_repeat": [
        "Do not use single quotes in JSON.",
        "Validate schemas before committing.",
    ],
}

_PLANS_INDEX_CONTENT = """\
# PLANS-INDEX

| Phase | Loop File | Status |
|-------|-----------|--------|
| phase-1 | plans/phase-1-ralph-loops.md | completed |
| phase-2 | plans/phase-2-ralph-loops-v2.md | active |
| phase-3 | plans/phase-3-ralph-loops.md | pending |
"""


# ── TestCreateRetryVersion ─────────────────────────────────────────────────────

class TestCreateRetryVersion:
    def test_creates_v2_file(self, tmp_path):
        source = tmp_path / "phase-2-ralph-loops.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        result = create_retry_version(source, attempt_number=2)

        assert result.name == "phase-2-ralph-loops-v2.md"
        assert result.exists()

    def test_preserves_original(self, tmp_path):
        source = tmp_path / "phase-2-ralph-loops.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        create_retry_version(source, attempt_number=2)

        assert source.exists()
        assert source.read_text(encoding="utf-8") == _SAMPLE_LOOP_CONTENT

    def test_content_is_copied(self, tmp_path):
        source = tmp_path / "phase-1-ralph-loops.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        dest = create_retry_version(source, attempt_number=2)

        assert dest.read_text(encoding="utf-8") == _SAMPLE_LOOP_CONTENT

    def test_raises_file_not_found_for_missing_source(self, tmp_path):
        missing = tmp_path / "does-not-exist.md"

        with pytest.raises(FileNotFoundError, match="does-not-exist"):
            create_retry_version(missing, attempt_number=2)

    def test_raises_value_error_when_attempt_less_than_2(self, tmp_path):
        source = tmp_path / "phase-1-ralph-loops.md"
        source.write_text("content", encoding="utf-8")

        with pytest.raises(ValueError, match="attempt_number must be >= 2"):
            create_retry_version(source, attempt_number=1)

    def test_raises_value_error_for_attempt_zero(self, tmp_path):
        source = tmp_path / "phase-1-ralph-loops.md"
        source.write_text("content", encoding="utf-8")

        with pytest.raises(ValueError):
            create_retry_version(source, attempt_number=0)

    def test_strips_existing_version_suffix(self, tmp_path):
        # A v2 file being re-versioned to v3 should strip -v2 first
        source = tmp_path / "phase-2-ralph-loops-v2.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        dest = create_retry_version(source, attempt_number=3)

        assert dest.name == "phase-2-ralph-loops-v3.md"
        assert dest.exists()

    def test_returns_absolute_path(self, tmp_path):
        source = tmp_path / "phase-1-ralph-loops.md"
        source.write_text("content", encoding="utf-8")

        dest = create_retry_version(source, attempt_number=2)

        assert dest.is_absolute()

    def test_creates_v3_file(self, tmp_path):
        source = tmp_path / "phase-1-ralph-loops.md"
        source.write_text("content", encoding="utf-8")

        dest = create_retry_version(source, attempt_number=3)

        assert dest.name == "phase-1-ralph-loops-v3.md"


# ── TestInjectFailureContext ───────────────────────────────────────────────────

class TestInjectFailureContext:
    def test_injects_block_into_yaml_fence(self, tmp_path):
        source = tmp_path / "phase-1-ralph-loops-v2.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        inject_failure_context(source, verdict=_SAMPLE_VERDICT)

        result = source.read_text(encoding="utf-8")
        assert "gate_failure_context:" in result

    def test_verdict_fields_present(self, tmp_path):
        source = tmp_path / "loop.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        inject_failure_context(source, verdict=_SAMPLE_VERDICT)

        result = source.read_text(encoding="utf-8")
        assert 'verdict_file:' in result
        assert 'summary:' in result
        assert 'loops_reverted:' in result
        assert 'do_not_repeat:' in result
        assert 'phase-1-attempt-1.json' in result
        assert 'ralph-loop-001' in result

    def test_preserves_existing_content(self, tmp_path):
        source = tmp_path / "loop.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        inject_failure_context(source, verdict=_SAMPLE_VERDICT)

        result = source.read_text(encoding="utf-8")
        # Original name field should still be present
        assert 'name: "ralph-loop-001"' in result

    def test_handles_empty_findings(self, tmp_path):
        source = tmp_path / "loop.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        verdict_empty = {
            "attempt": 1,
            "verdict_file": "gate-verdicts/x.json",
            "summary": "No issues found.",
            "loops_reverted": [],
            "do_not_repeat": [],
        }
        inject_failure_context(source, verdict=verdict_empty)

        result = source.read_text(encoding="utf-8")
        assert "gate_failure_context:" in result
        assert "loops_reverted: []" in result
        assert "do_not_repeat: []" in result

    def test_handles_dashes_delimiter(self, tmp_path):
        # Plan file using --- instead of ```yaml
        content = "---\nname: \"ralph-loop-001\"\n---\nSome content.\n"
        source = tmp_path / "loop.md"
        source.write_text(content, encoding="utf-8")

        inject_failure_context(source, verdict=_SAMPLE_VERDICT)

        result = source.read_text(encoding="utf-8")
        assert "gate_failure_context:" in result

    def test_returns_absolute_path(self, tmp_path):
        source = tmp_path / "loop.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        result = inject_failure_context(source, verdict=_SAMPLE_VERDICT)

        assert result.is_absolute()

    def test_raises_file_not_found_for_missing_file(self, tmp_path):
        missing = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            inject_failure_context(missing, verdict=_SAMPLE_VERDICT)


# ── TestGetActiveVersion ───────────────────────────────────────────────────────

class TestGetActiveVersion:
    def test_returns_active_loop_file(self, tmp_path):
        index = tmp_path / "PLANS-INDEX.md"
        index.write_text(_PLANS_INDEX_CONTENT, encoding="utf-8")

        result = get_active_version(index, phase="phase-1")

        assert result == "plans/phase-1-ralph-loops.md"

    def test_returns_none_for_missing_phase(self, tmp_path):
        index = tmp_path / "PLANS-INDEX.md"
        index.write_text(_PLANS_INDEX_CONTENT, encoding="utf-8")

        result = get_active_version(index, phase="phase-99")

        assert result is None

    def test_handles_versioned_entries(self, tmp_path):
        index = tmp_path / "PLANS-INDEX.md"
        index.write_text(_PLANS_INDEX_CONTENT, encoding="utf-8")

        result = get_active_version(index, phase="phase-2")

        assert result == "plans/phase-2-ralph-loops-v2.md"

    def test_case_insensitive_phase_lookup(self, tmp_path):
        index = tmp_path / "PLANS-INDEX.md"
        index.write_text(_PLANS_INDEX_CONTENT, encoding="utf-8")

        result = get_active_version(index, phase="Phase-1")

        assert result == "plans/phase-1-ralph-loops.md"

    def test_raises_file_not_found_for_missing_index(self, tmp_path):
        missing = tmp_path / "NO-INDEX.md"

        with pytest.raises(FileNotFoundError):
            get_active_version(missing, phase="phase-1")

    def test_returns_third_phase_entry(self, tmp_path):
        index = tmp_path / "PLANS-INDEX.md"
        index.write_text(_PLANS_INDEX_CONTENT, encoding="utf-8")

        result = get_active_version(index, phase="phase-3")

        assert result == "plans/phase-3-ralph-loops.md"


# ── TestFreezeLoopFile ─────────────────────────────────────────────────────────

class TestFreezeLoopFile:
    def test_freezes_pending(self, tmp_path):
        source = tmp_path / "loop.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        freeze_loop_file(source)

        result = source.read_text(encoding="utf-8")
        assert "status: pending" not in result
        assert "status: frozen" in result

    def test_freezes_in_progress(self, tmp_path):
        source = tmp_path / "loop.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        freeze_loop_file(source)

        result = source.read_text(encoding="utf-8")
        assert "status: in_progress" not in result
        assert "status: frozen" in result

    def test_leaves_completed_unchanged(self, tmp_path):
        source = tmp_path / "loop.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        freeze_loop_file(source)

        result = source.read_text(encoding="utf-8")
        assert "status: completed" in result

    def test_leaves_cancelled_unchanged(self, tmp_path):
        source = tmp_path / "loop.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        freeze_loop_file(source)

        result = source.read_text(encoding="utf-8")
        assert "status: cancelled" in result

    def test_returns_absolute_path(self, tmp_path):
        source = tmp_path / "loop.md"
        source.write_text(_SAMPLE_LOOP_CONTENT, encoding="utf-8")

        result = freeze_loop_file(source)

        assert result.is_absolute()

    def test_raises_file_not_found_for_missing_file(self, tmp_path):
        missing = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            freeze_loop_file(missing)

    def test_no_op_on_all_completed(self, tmp_path):
        content = "status: completed\nstatus: completed\n"
        source = tmp_path / "loop.md"
        source.write_text(content, encoding="utf-8")

        freeze_loop_file(source)

        result = source.read_text(encoding="utf-8")
        assert "status: frozen" not in result
        assert result == content

    def test_multiple_pending_all_frozen(self, tmp_path):
        content = "status: pending\nstatus: pending\nstatus: pending\n"
        source = tmp_path / "loop.md"
        source.write_text(content, encoding="utf-8")

        freeze_loop_file(source)

        result = source.read_text(encoding="utf-8")
        assert result.count("status: frozen") == 3
        assert "status: pending" not in result
