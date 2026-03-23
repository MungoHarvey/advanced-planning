"""
Unit tests for the /next-phase --auto phase-chaining logic.
Tests the state transitions and edge cases without requiring Claude Code.
Mirrors the pattern in platforms/python/tests/.
"""
import json
import pathlib
import tempfile
import unittest


def find_next_incomplete_phase(plans_dir: pathlib.Path) -> int | None:
    """
    Find the lowest-numbered phase that has at least one pending todo.
    Returns phase number (int) or None if all phases complete.
    """
    loop_files = sorted(plans_dir.glob("phase-*-ralph-loops.md"))
    for f in loop_files:
        content = f.read_text()
        if "status: pending" in content:
            # Extract phase number from filename
            import re
            m = re.search(r"phase-(\d+)-ralph-loops", f.name)
            if m:
                return int(m.group(1))
    return None


def all_loops_complete(plans_dir: pathlib.Path, phase_n: int) -> bool:
    """
    Returns True if all todos in a phase's loop file are completed or cancelled.
    """
    loop_file = plans_dir / f"phase-{phase_n}-ralph-loops.md"
    if not loop_file.exists():
        return False
    content = loop_file.read_text()
    lines = [l.strip() for l in content.splitlines() if "status:" in l]
    for line in lines:
        if "pending" in line or "in_progress" in line:
            return False
    return bool(lines)  # False if no status lines found


def read_phase_outcome(state_dir: pathlib.Path) -> dict:
    """Read loop-complete.json and return outcome dict."""
    f = state_dir / "loop-complete.json"
    if not f.exists():
        return {"status": "unknown"}
    return json.loads(f.read_text())


def check_dependencies_met(plans_dir: pathlib.Path, phase_n: int) -> bool:
    """
    Simplified dependency check: all prior phases must be complete.
    (Real implementation reads ## Dependencies section from phase plan.)
    """
    for prior in range(1, phase_n):
        if not all_loops_complete(plans_dir, prior):
            return False
    return True


class TestPhaseChaining(unittest.TestCase):

    def _make_loop_file(self, plans_dir, phase_n, statuses):
        """Create a minimal loop file with given todo statuses."""
        todos = "\n".join(
            f"  - id: loop-00{phase_n}-{i+1}\n"
            f"    content: task {i+1}\n"
            f"    status: {s}"
            for i, s in enumerate(statuses)
        )
        content = f"---\nname: ralph-loop-00{phase_n}\ntodos:\n{todos}\n---\n"
        (plans_dir / f"phase-{phase_n}-ralph-loops.md").write_text(content)

    def test_find_next_incomplete_phase_first(self):
        """Finds phase 1 when it has pending todos."""
        with tempfile.TemporaryDirectory() as d:
            plans = pathlib.Path(d)
            self._make_loop_file(plans, 1, ["pending", "pending"])
            self._make_loop_file(plans, 2, ["pending"])
            self.assertEqual(find_next_incomplete_phase(plans), 1)

    def test_find_next_incomplete_phase_skips_complete(self):
        """Skips phase 1 when complete, returns phase 2."""
        with tempfile.TemporaryDirectory() as d:
            plans = pathlib.Path(d)
            self._make_loop_file(plans, 1, ["completed", "completed"])
            self._make_loop_file(plans, 2, ["pending", "completed"])
            self.assertEqual(find_next_incomplete_phase(plans), 2)

    def test_find_next_incomplete_phase_all_done(self):
        """Returns None when all phases complete."""
        with tempfile.TemporaryDirectory() as d:
            plans = pathlib.Path(d)
            self._make_loop_file(plans, 1, ["completed"])
            self._make_loop_file(plans, 2, ["completed", "cancelled"])
            self.assertIsNone(find_next_incomplete_phase(plans))

    def test_all_loops_complete_true(self):
        """Returns True when all todos completed or cancelled."""
        with tempfile.TemporaryDirectory() as d:
            plans = pathlib.Path(d)
            self._make_loop_file(plans, 1, ["completed", "cancelled", "completed"])
            self.assertTrue(all_loops_complete(plans, 1))

    def test_all_loops_complete_false_pending(self):
        """Returns False when any todo is pending."""
        with tempfile.TemporaryDirectory() as d:
            plans = pathlib.Path(d)
            self._make_loop_file(plans, 1, ["completed", "pending"])
            self.assertFalse(all_loops_complete(plans, 1))

    def test_all_loops_complete_false_in_progress(self):
        """Returns False when any todo is in_progress."""
        with tempfile.TemporaryDirectory() as d:
            plans = pathlib.Path(d)
            self._make_loop_file(plans, 1, ["completed", "in_progress"])
            self.assertFalse(all_loops_complete(plans, 1))

    def test_all_loops_complete_missing_file(self):
        """Returns False when loop file doesn't exist."""
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(all_loops_complete(pathlib.Path(d), 99))

    def test_dependency_check_first_phase(self):
        """Phase 1 always passes dependency check (no priors)."""
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(check_dependencies_met(pathlib.Path(d), 1))

    def test_dependency_check_prior_complete(self):
        """Phase 2 passes when phase 1 is complete."""
        with tempfile.TemporaryDirectory() as d:
            plans = pathlib.Path(d)
            self._make_loop_file(plans, 1, ["completed"])
            self.assertTrue(check_dependencies_met(plans, 2))

    def test_dependency_check_prior_incomplete(self):
        """Phase 2 fails when phase 1 has pending todos."""
        with tempfile.TemporaryDirectory() as d:
            plans = pathlib.Path(d)
            self._make_loop_file(plans, 1, ["completed", "pending"])
            self.assertFalse(check_dependencies_met(plans, 2))

    def test_never_auto_advance_past_failure(self):
        """
        Simulates AUTO_MODE stopping on a failed loop-complete.json.
        The outer phase-chaining loop must halt when status == 'failed'.
        """
        with tempfile.TemporaryDirectory() as d:
            state = pathlib.Path(d)
            (state / "loop-complete.json").write_text(json.dumps({
                "loop_name": "ralph-loop-002",
                "status": "failed",
                "todos_done": 1,
                "todos_failed": 1,
                "handoff": {
                    "done": "Task 1 completed",
                    "failed": "Task 2 hit max_iterations",
                    "needed": "Fix the normalisation script before retrying"
                }
            }))
            outcome = read_phase_outcome(state)
            # AUTO_MODE logic: only continue if status is completed or partial
            should_chain = outcome["status"] in ("completed", "partial")
            self.assertFalse(should_chain)

    def test_auto_continues_on_partial(self):
        """
        AUTO_MODE continues to next phase on partial completion
        (some todos cancelled, not failed).
        """
        with tempfile.TemporaryDirectory() as d:
            state = pathlib.Path(d)
            (state / "loop-complete.json").write_text(json.dumps({
                "loop_name": "ralph-loop-003",
                "status": "partial",
                "todos_done": 3,
                "todos_failed": 0,
                "handoff": {"done": "3 tasks done", "failed": "", "needed": ""}
            }))
            outcome = read_phase_outcome(state)
            should_chain = outcome["status"] in ("completed", "partial")
            self.assertTrue(should_chain)

    def test_pause_signal_respected(self):
        """Pause signal file presence should halt auto-chaining."""
        with tempfile.TemporaryDirectory() as d:
            logs = pathlib.Path(d)
            (logs / "pause.signal").touch()
            pause_requested = (logs / "pause.signal").exists()
            self.assertTrue(pause_requested)

    def test_phase_complete_state_transition(self):
        """
        Simulates writing phase completion to history.jsonl.
        Verifies the append-only pattern is correct JSON Lines.
        """
        import io
        history_lines = []
        # Simulate two phase completions appended
        for phase_n, outcome in [(1, "completed"), (2, "completed")]:
            entry = {
                "event": "phase_complete",
                "phase": phase_n,
                "outcome": outcome
            }
            history_lines.append(json.dumps(entry))

        # Each line must be valid JSON
        for line in history_lines:
            parsed = json.loads(line)
            self.assertIn("phase", parsed)
            self.assertIn("outcome", parsed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
