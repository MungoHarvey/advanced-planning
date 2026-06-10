"""Unit tests for state_manager.prepare_loop_ready"""

import json
import textwrap
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parents[3]))

from platforms.python.state_manager import prepare_loop_ready

# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_loops_md(tmp_path: Path, loops_content: str) -> Path:
    """Write a loops.md file under a fake phase directory and return its path."""
    phase_dir = tmp_path / "phases" / "phase-99"
    phase_dir.mkdir(parents=True, exist_ok=True)
    loops_md = phase_dir / "loops.md"
    loops_md.write_text(loops_content, encoding="utf-8")
    return loops_md


_POPULATED_LOOPS_MD = textwrap.dedent("""\
    # Phase 99 Loops

    ---

    ```yaml
    ---
    name: "ralph-loop-099"
    task_name: "Test Task"
    max_iterations: 3
    on_max_iterations: escalate

    handoff_summary:
      done: ""
      failed: ""
      needed: ""

    todos:
      - id: "loop-099-1"
        content: "Do the first thing"
        skill: "NA"
        agent: "NA"
        outcome: "First thing is done"
        status: pending
        complexity: low
        priority: high
      - id: "loop-099-2"
        content: "Do the second thing"
        skill: "NA"
        agent: "NA"
        outcome: "Second thing is done"
        status: pending
        complexity: low
        priority: medium
    ```
""")

_EMPTY_TODOS_LOOPS_MD = textwrap.dedent("""\
    # Phase 99 Loops

    ---

    ```yaml
    ---
    name: "ralph-loop-099"
    task_name: "Test Task"
    max_iterations: 3
    on_max_iterations: escalate

    handoff_summary:
      done: ""
      failed: ""
      needed: ""

    todos:
    ```
""")

_MISSING_OUTCOME_LOOPS_MD = textwrap.dedent("""\
    # Phase 99 Loops

    ---

    ```yaml
    ---
    name: "ralph-loop-099"
    task_name: "Test Task"
    max_iterations: 3
    on_max_iterations: escalate

    handoff_summary:
      done: ""
      failed: ""
      needed: ""

    todos:
      - id: "loop-099-1"
        content: "Do the first thing"
        skill: "NA"
        agent: "NA"
        status: pending
        complexity: low
        priority: high
    ```
""")

_ALL_COMPLETE_LOOPS_MD = textwrap.dedent("""\
    # Phase 99 Loops

    ---

    ```yaml
    ---
    name: "ralph-loop-099"
    task_name: "Test Task"
    max_iterations: 3
    on_max_iterations: escalate

    handoff_summary:
      done: "All done"
      failed: ""
      needed: ""

    todos:
      - id: "loop-099-1"
        content: "Do the first thing"
        skill: "NA"
        agent: "NA"
        outcome: "First thing is done"
        status: completed
        complexity: low
        priority: high
      - id: "loop-099-2"
        content: "Do the second thing"
        skill: "NA"
        agent: "NA"
        outcome: "Second thing is done"
        status: completed
        complexity: low
        priority: medium
    ```
""")


# ── Test cases ─────────────────────────────────────────────────────────────────

class TestPrepareLoopReady:

    def test_populated_loop_writes_loop_ready_json(self, tmp_path):
        """Case (a): fully-populated todos -> loop-ready.json written with valid fields."""
        loops_md = _make_loops_md(tmp_path, _POPULATED_LOOPS_MD)
        state_dir = tmp_path / "state"
        prior = {"done": "prior done", "failed": "", "needed": "next step"}

        result = prepare_loop_ready(loops_md, prior, state_dir=state_dir)

        assert result["ok"] is True, f"Expected ok=True, got: {result}"
        loop_ready_path = state_dir / "loop-ready.json"
        assert loop_ready_path.exists(), "loop-ready.json should be written"

        data = json.loads(loop_ready_path.read_text(encoding="utf-8"))

        # Schema-valid required fields
        assert data["loop_name"] == "ralph-loop-099"
        assert "phase-99" in data["loop_file"]
        assert data["task_name"] == "Test Task"
        assert data["todos_count"] == 2
        assert data["status"] == "ready"
        assert "prepared_at" in data

        # Handoff injected
        hi = data["handoff_injected"]
        assert hi["done"] == "prior done"
        assert hi["failed"] == ""
        assert hi["needed"] == "next step"

    def test_empty_todos_returns_agent_needed_no_file(self, tmp_path):
        """Case (b): empty todos[] -> agent_needed, loop-ready.json NOT written."""
        loops_md = _make_loops_md(tmp_path, _EMPTY_TODOS_LOOPS_MD)
        state_dir = tmp_path / "state"

        result = prepare_loop_ready(loops_md, {}, state_dir=state_dir)

        assert result["ok"] is False
        assert result["reason"] == "agent_needed"
        assert result.get("loop_name") == "ralph-loop-099"
        assert not (state_dir / "loop-ready.json").exists(), "No file should be written"

    def test_todo_missing_outcome_returns_agent_needed_no_file(self, tmp_path):
        """Case (c): todo with missing `outcome` field -> agent_needed, no file."""
        loops_md = _make_loops_md(tmp_path, _MISSING_OUTCOME_LOOPS_MD)
        state_dir = tmp_path / "state"

        result = prepare_loop_ready(loops_md, {}, state_dir=state_dir)

        assert result["ok"] is False
        assert result["reason"] == "agent_needed"
        assert not (state_dir / "loop-ready.json").exists(), "No file should be written"

    def test_all_loops_completed_returns_all_complete(self, tmp_path):
        """Case (d): all todos completed -> all_complete, no file."""
        loops_md = _make_loops_md(tmp_path, _ALL_COMPLETE_LOOPS_MD)
        state_dir = tmp_path / "state"

        result = prepare_loop_ready(loops_md, {}, state_dir=state_dir)

        assert result["ok"] is False
        assert result["reason"] == "all_complete"
        assert not (state_dir / "loop-ready.json").exists(), "No file should be written"

    def test_handoff_fields_all_carried(self, tmp_path):
        """All three handoff fields (done/failed/needed) are carried into handoff_injected."""
        loops_md = _make_loops_md(tmp_path, _POPULATED_LOOPS_MD)
        state_dir = tmp_path / "state"
        prior = {"done": "d", "failed": "f", "needed": "n"}

        result = prepare_loop_ready(loops_md, prior, state_dir=state_dir)

        assert result["ok"] is True
        data = json.loads((state_dir / "loop-ready.json").read_text(encoding="utf-8"))
        assert data["handoff_injected"] == {"done": "d", "failed": "f", "needed": "n"}

    def test_missing_handoff_keys_default_to_empty_string(self, tmp_path):
        """Missing keys in prior_handoff default to empty strings."""
        loops_md = _make_loops_md(tmp_path, _POPULATED_LOOPS_MD)
        state_dir = tmp_path / "state"

        result = prepare_loop_ready(loops_md, {}, state_dir=state_dir)

        assert result["ok"] is True
        data = json.loads((state_dir / "loop-ready.json").read_text(encoding="utf-8"))
        hi = data["handoff_injected"]
        assert hi["done"] == ""
        assert hi["failed"] == ""
        assert hi["needed"] == ""
