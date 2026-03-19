"""Unit tests for platforms.python.handoff"""

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parents[3]))

from platforms.python.handoff import (
    make_empty_handoff,
    read_handoff,
    inject_handoff,
    inject_handoff_from_file,
    build_context_block,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def loop_complete_file(tmp_path):
    """Write a minimal loop-complete.json and return its path."""
    data = {
        "loop_name": "ralph-loop-001",
        "loop_file": "plans/phase-1-ralph-loops.md",
        "status": "completed",
        "todos_done": 4,
        "todos_failed": 0,
        "completed_at": "2024-03-15T14:30:00+00:00",
        "handoff": {
            "done": "4 schema files created in core/schemas/.",
            "failed": "",
            "needed": "Run plan-todos on loop-002.",
        },
    }
    f = tmp_path / "loop-complete.json"
    f.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return f


SAMPLE_TEMPLATE = """\
## Context from prior loop
Done: [inject prior.handoff_summary.done]
Failed: [inject prior.handoff_summary.failed]
Needed: [inject prior.handoff_summary.needed]

## Objective
Do the work.
"""


# ── make_empty_handoff ─────────────────────────────────────────────────────────

class TestMakeEmptyHandoff:
    def test_returns_three_empty_strings(self):
        h = make_empty_handoff()
        assert h == {"done": "", "failed": "", "needed": ""}


# ── read_handoff ───────────────────────────────────────────────────────────────

class TestReadHandoff:
    def test_reads_all_three_fields(self, loop_complete_file):
        h = read_handoff(loop_complete_file)
        assert h["done"] == "4 schema files created in core/schemas/."
        assert h["failed"] == ""
        assert h["needed"] == "Run plan-todos on loop-002."

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_handoff(tmp_path / "nonexistent.json")


# ── inject_handoff ─────────────────────────────────────────────────────────────

class TestInjectHandoff:
    def test_replaces_all_three_placeholders(self):
        handoff = {
            "done": "Work completed.",
            "failed": "Nothing failed.",
            "needed": "Continue with loop-002.",
        }
        result = inject_handoff(SAMPLE_TEMPLATE, handoff)
        assert "Work completed." in result
        assert "Nothing failed." in result
        assert "Continue with loop-002." in result
        assert "[inject prior.handoff_summary.done]" not in result
        assert "[inject prior.handoff_summary.failed]" not in result
        assert "[inject prior.handoff_summary.needed]" not in result

    def test_empty_handoff_replaces_with_empty_string(self):
        result = inject_handoff(SAMPLE_TEMPLATE, make_empty_handoff())
        assert "Done: \n" in result
        assert "[inject prior.handoff_summary" not in result

    def test_no_placeholders_returns_template_unchanged(self):
        template = "No placeholders here."
        result = inject_handoff(template, {"done": "X", "failed": "Y", "needed": "Z"})
        assert result == template

    def test_preserves_rest_of_template(self):
        result = inject_handoff(SAMPLE_TEMPLATE, make_empty_handoff())
        assert "## Objective" in result
        assert "Do the work." in result


# ── inject_handoff_from_file ───────────────────────────────────────────────────

class TestInjectHandoffFromFile:
    def test_reads_file_and_injects(self, loop_complete_file):
        result = inject_handoff_from_file(SAMPLE_TEMPLATE, loop_complete_file)
        assert "4 schema files created in core/schemas/." in result
        assert "Run plan-todos on loop-002." in result

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            inject_handoff_from_file(SAMPLE_TEMPLATE, tmp_path / "missing.json")


# ── build_context_block ────────────────────────────────────────────────────────

class TestBuildContextBlock:
    def test_default_prefix(self):
        block = build_context_block({"done": "D", "failed": "F", "needed": "N"})
        assert block.startswith("## Context from prior loop\n")
        assert "Done: D\n" in block
        assert "Failed: F\n" in block
        assert "Needed: N\n" in block

    def test_custom_prefix(self):
        block = build_context_block({"done": "D", "failed": "", "needed": ""}, prefix="# Prior")
        assert block.startswith("# Prior\n")
