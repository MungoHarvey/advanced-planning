"""Unit tests for platforms.python.state_manager"""

import json
import tempfile
from pathlib import Path

import pytest

# Adjust path so we can import from the package root when running from repo root
import sys
sys.path.insert(0, str(Path(__file__).parents[3]))

from platforms.python.state_manager import (
    write_loop_ready,
    read_loop_ready,
    write_loop_complete,
    read_loop_complete,
    append_history,
    read_history,
    get_status,
)


@pytest.fixture
def state_dir(tmp_path):
    """Provide a fresh temporary state directory for each test."""
    return tmp_path / "state"


# ── write_loop_ready / read_loop_ready ─────────────────────────────────────────

class TestWriteReadLoopReady:
    def test_write_creates_file(self, state_dir):
        path = write_loop_ready(
            state_dir,
            loop_name="ralph-loop-001",
            loop_file="plans/phase-1-ralph-loops.md",
            task_name="Schema Definitions",
            todos_count=4,
        )
        assert path.exists()

    def test_round_trip_fields(self, state_dir):
        write_loop_ready(
            state_dir,
            loop_name="ralph-loop-001",
            loop_file="plans/phase-1-ralph-loops.md",
            task_name="Schema Definitions",
            todos_count=4,
            handoff_done="Prior work done.",
            handoff_failed="",
            handoff_needed="Start with schemas.",
        )
        data = read_loop_ready(state_dir)
        assert data["loop_name"] == "ralph-loop-001"
        assert data["loop_file"] == "plans/phase-1-ralph-loops.md"
        assert data["task_name"] == "Schema Definitions"
        assert data["todos_count"] == 4
        assert data["status"] == "ready"
        assert data["handoff_injected"]["done"] == "Prior work done."
        assert data["handoff_injected"]["needed"] == "Start with schemas."

    def test_read_returns_none_when_absent(self, state_dir):
        assert read_loop_ready(state_dir) is None

    def test_prepared_at_is_iso(self, state_dir):
        write_loop_ready(
            state_dir,
            loop_name="ralph-loop-001",
            loop_file="plans/x.md",
            task_name="T",
            todos_count=1,
        )
        data = read_loop_ready(state_dir)
        # ISO 8601 strings contain 'T' separator
        assert "T" in data["prepared_at"]

    def test_creates_state_dir_if_absent(self, tmp_path):
        new_state = tmp_path / "new" / "nested" / "state"
        write_loop_ready(
            new_state,
            loop_name="ralph-loop-001",
            loop_file="plans/x.md",
            task_name="T",
            todos_count=1,
        )
        assert (new_state / "loop-ready.json").exists()


# ── write_loop_complete / read_loop_complete ───────────────────────────────────

class TestWriteReadLoopComplete:
    def test_round_trip(self, state_dir):
        write_loop_complete(
            state_dir,
            loop_name="ralph-loop-001",
            loop_file="plans/phase-1-ralph-loops.md",
            status="completed",
            todos_done=4,
            todos_failed=0,
            handoff_done="4 schema files created.",
            handoff_failed="",
            handoff_needed="",
        )
        data = read_loop_complete(state_dir)
        assert data["status"] == "completed"
        assert data["todos_done"] == 4
        assert data["todos_failed"] == 0
        assert data["handoff"]["done"] == "4 schema files created."

    def test_invalid_status_raises(self, state_dir):
        with pytest.raises(ValueError, match="Invalid status"):
            write_loop_complete(
                state_dir,
                loop_name="ralph-loop-001",
                loop_file="plans/x.md",
                status="bad_status",
                todos_done=0,
                todos_failed=0,
                handoff_done="",
                handoff_failed="",
                handoff_needed="",
            )

    def test_read_returns_none_when_absent(self, state_dir):
        assert read_loop_complete(state_dir) is None

    def test_partial_status_accepted(self, state_dir):
        write_loop_complete(
            state_dir,
            loop_name="ralph-loop-002",
            loop_file="plans/x.md",
            status="partial",
            todos_done=2,
            todos_failed=1,
            handoff_done="2 of 3 done.",
            handoff_failed="todo-002-3 cancelled.",
            handoff_needed="Retry todo-002-3.",
        )
        data = read_loop_complete(state_dir)
        assert data["status"] == "partial"

    def test_optional_duration_included_when_provided(self, state_dir):
        write_loop_complete(
            state_dir,
            loop_name="ralph-loop-001",
            loop_file="plans/x.md",
            status="completed",
            todos_done=1,
            todos_failed=0,
            handoff_done="Done.",
            handoff_failed="",
            handoff_needed="",
            duration_seconds=42.5,
        )
        data = read_loop_complete(state_dir)
        assert data["duration_seconds"] == 42.5


# ── append_history / read_history ─────────────────────────────────────────────

class TestHistory:
    def test_append_and_read(self, state_dir):
        append_history(state_dir, {"loop_name": "ralph-loop-001", "status": "completed"})
        append_history(state_dir, {"loop_name": "ralph-loop-002", "status": "completed"})
        records = read_history(state_dir)
        assert len(records) == 2
        assert records[0]["loop_name"] == "ralph-loop-001"
        assert records[1]["loop_name"] == "ralph-loop-002"

    def test_adds_recorded_at(self, state_dir):
        append_history(state_dir, {"loop_name": "ralph-loop-001"})
        records = read_history(state_dir)
        assert "recorded_at" in records[0]

    def test_read_empty_when_absent(self, state_dir):
        assert read_history(state_dir) == []


# ── get_status ─────────────────────────────────────────────────────────────────

class TestGetStatus:
    def test_empty_state(self, state_dir):
        s = get_status(state_dir)
        assert s["has_loop_ready"] is False
        assert s["has_loop_complete"] is False
        assert s["history_count"] == 0

    def test_with_ready_file(self, state_dir):
        write_loop_ready(
            state_dir,
            loop_name="ralph-loop-001",
            loop_file="plans/x.md",
            task_name="T",
            todos_count=2,
        )
        s = get_status(state_dir)
        assert s["has_loop_ready"] is True
        assert s["loop_ready"]["loop_name"] == "ralph-loop-001"
