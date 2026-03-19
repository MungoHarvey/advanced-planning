"""Unit tests for platforms.python.plan_io"""

import textwrap
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parents[3]))

from platforms.python.plan_io import (
    parse_loop_frontmatter,
    get_pending_todos,
    get_all_todos,
    update_todo_status,
    find_next_loop,
    get_loop_handoff,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

SAMPLE_PLAN = textwrap.dedent('''\
    # Phase 1 — Ralph Loops

    ## ralph-loop-001: Schema Definitions

    ```yaml
    name: "ralph-loop-001"
    task_name: "Schema Definitions"
    max_iterations: 3
    on_max_iterations: escalate

    handoff_summary:
      done: "4 schema files created."
      failed: ""
      needed: ""

    todos:
      - id: "loop-001-1"
        content: "Create phase-plan.schema.md"
        skill: "NA"
        agent: "NA"
        outcome: "File exists at core/schemas/phase-plan.schema.md"
        status: completed
        priority: high

      - id: "loop-001-2"
        content: "Create ralph-loop.schema.md"
        skill: "NA"
        agent: "NA"
        outcome: "File exists at core/schemas/ralph-loop.schema.md"
        status: completed
        priority: high
    ```

    ## ralph-loop-002: Planning Skills

    ```yaml
    name: "ralph-loop-002"
    task_name: "Planning Skills"
    max_iterations: 3
    on_max_iterations: escalate

    handoff_summary:
      done: ""
      failed: ""
      needed: ""

    todos:
      - id: "loop-002-1"
        content: "Create phase-plan-creator/SKILL.md"
        skill: "skill-creator"
        agent: "NA"
        outcome: "File exists at core/skills/phase-plan-creator/SKILL.md"
        status: pending
        priority: high

      - id: "loop-002-2"
        content: "Create ralph-loop-planner/SKILL.md"
        skill: "skill-creator"
        agent: "NA"
        outcome: "File exists at core/skills/ralph-loop-planner/SKILL.md"
        status: pending
        priority: high
    ```
''')


@pytest.fixture
def plan_file(tmp_path):
    """Write SAMPLE_PLAN to a temp file and return its path."""
    f = tmp_path / "phase-1-ralph-loops.md"
    f.write_text(SAMPLE_PLAN, encoding="utf-8")
    return f


@pytest.fixture
def plans_dir(tmp_path, plan_file):
    """Return the plans directory containing the sample plan."""
    return tmp_path


# ── parse_loop_frontmatter ─────────────────────────────────────────────────────

class TestParseLoopFrontmatter:
    def test_parses_known_loop(self, plan_file):
        fm = parse_loop_frontmatter(plan_file, "ralph-loop-001")
        assert fm is not None
        assert fm["task_name"] == "Schema Definitions"
        assert fm["max_iterations"] == 3
        assert fm["on_max_iterations"] == "escalate"

    def test_returns_none_for_unknown_loop(self, plan_file):
        assert parse_loop_frontmatter(plan_file, "ralph-loop-999") is None

    def test_parses_handoff_summary(self, plan_file):
        fm = parse_loop_frontmatter(plan_file, "ralph-loop-001")
        hs = fm["handoff_summary"]
        assert hs["done"] == "4 schema files created."
        assert hs["failed"] == ""
        assert hs["needed"] == ""

    def test_parses_todos(self, plan_file):
        fm = parse_loop_frontmatter(plan_file, "ralph-loop-001")
        todos = fm["todos"]
        assert len(todos) == 2
        assert todos[0]["id"] == "loop-001-1"
        assert todos[1]["status"] == "completed"


# ── get_pending_todos ──────────────────────────────────────────────────────────

class TestGetPendingTodos:
    def test_completed_loop_has_no_pending(self, plan_file):
        pending = get_pending_todos(plan_file, "ralph-loop-001")
        assert pending == []

    def test_pending_loop_returns_todos(self, plan_file):
        pending = get_pending_todos(plan_file, "ralph-loop-002")
        assert len(pending) == 2
        assert all(t["status"] == "pending" for t in pending)

    def test_unknown_loop_returns_empty(self, plan_file):
        assert get_pending_todos(plan_file, "ralph-loop-999") == []


# ── update_todo_status ─────────────────────────────────────────────────────────

class TestUpdateTodoStatus:
    def test_updates_status_in_file(self, plan_file):
        result = update_todo_status(plan_file, "ralph-loop-002", "loop-002-1", "in_progress")
        assert result is True
        pending = get_pending_todos(plan_file, "ralph-loop-002")
        # Only loop-002-2 should still be pending
        assert len(pending) == 1
        assert pending[0]["id"] == "loop-002-2"

    def test_returns_false_for_unknown_todo(self, plan_file):
        result = update_todo_status(plan_file, "ralph-loop-002", "loop-999-1", "completed")
        assert result is False

    def test_invalid_status_raises(self, plan_file):
        with pytest.raises(ValueError, match="Invalid status"):
            update_todo_status(plan_file, "ralph-loop-002", "loop-002-1", "bad")


# ── find_next_loop ─────────────────────────────────────────────────────────────

class TestFindNextLoop:
    def test_finds_first_pending_loop(self, plans_dir):
        result = find_next_loop(plans_dir)
        assert result is not None
        assert result["loop_name"] == "ralph-loop-002"
        assert result["todos_count"] == 2

    def test_returns_none_when_all_complete(self, tmp_path):
        # Write a plan where all todos are completed
        all_done = SAMPLE_PLAN.replace("status: pending", "status: completed")
        f = tmp_path / "phase-1-ralph-loops.md"
        f.write_text(all_done, encoding="utf-8")
        assert find_next_loop(tmp_path) is None


# ── get_loop_handoff ───────────────────────────────────────────────────────────

class TestGetLoopHandoff:
    def test_returns_handoff_for_known_loop(self, plan_file):
        hs = get_loop_handoff(plan_file, "ralph-loop-001")
        assert hs["done"] == "4 schema files created."

    def test_returns_empty_for_unknown_loop(self, plan_file):
        hs = get_loop_handoff(plan_file, "ralph-loop-999")
        assert hs == {"done": "", "failed": "", "needed": ""}
