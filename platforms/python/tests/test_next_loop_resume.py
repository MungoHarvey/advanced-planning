"""
test_next_loop_resume.py -- IRON-RULE regression test for the Loop-035 failure mode.

Guards against: worker dies after orchestrator writes loop-ready.json but before
(or during) execution, leaving the working tree dirty.  /next-loop must detect this
before spawning a new orchestrator.

Detection logic lives in state_manager.detect_mid_loop_death().

References:
  - docs/tool-friction-log.md: "Worker durability (mid-loop death)" entry
  - .advanced-plans/specs/2026-05-20-phase-11-friction-remediation-design.md: S8
  - platforms/claude-code/commands/next-loop.md: Step 3a (resume-detection)
"""

import os
import time
import tempfile
from pathlib import Path

import pytest

from platforms.python.state_manager import detect_mid_loop_death


class TestDetectMidLoopDeath:
    """Regression tests for the Loop-035 failure mode detection."""

    def _write_json(self, path: Path, content: str = "{}") -> None:
        path.write_text(content, encoding="utf-8")

    def test_detects_mid_loop_death_ready_newer_and_dirty(self, tmp_path: Path) -> None:
        """Core failure mode: loop-ready.json is newer than loop-complete.json
        AND the working tree is dirty.  Must return True (= pause for operator).

        This is the exact scenario that bit Loop-035: the orchestrator wrote
        loop-ready.json, the worker started (making tree dirty), then died.
        The next /next-loop run must catch this before overwriting state.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Create loop-complete first (older)
        complete_path = state_dir / "loop-complete.json"
        self._write_json(complete_path, '{"status": "completed"}')

        # Brief sleep to ensure mtime difference is measurable
        time.sleep(0.05)

        # Create loop-ready second (newer)
        ready_path = state_dir / "loop-ready.json"
        self._write_json(ready_path, '{"status": "ready"}')

        assert detect_mid_loop_death(state_dir, dirty=True) is True

    def test_clean_when_complete_newer_than_ready(self, tmp_path: Path) -> None:
        """Normal post-completion state: loop-complete.json is newer.
        Must return False even if tree is dirty (unrelated changes are OK).
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Create loop-ready first (older)
        ready_path = state_dir / "loop-ready.json"
        self._write_json(ready_path, '{"status": "ready"}')

        time.sleep(0.05)

        # Create loop-complete second (newer)
        complete_path = state_dir / "loop-complete.json"
        self._write_json(complete_path, '{"status": "completed"}')

        # Dirty tree but loop-complete is newer -- /next-loop must proceed
        assert detect_mid_loop_death(state_dir, dirty=True) is False

    def test_clean_when_complete_newer_and_tree_clean(self, tmp_path: Path) -> None:
        """Clean state (loop-complete newer) AND clean tree.  Must return False."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        ready_path = state_dir / "loop-ready.json"
        self._write_json(ready_path)
        time.sleep(0.05)
        complete_path = state_dir / "loop-complete.json"
        self._write_json(complete_path)

        assert detect_mid_loop_death(state_dir, dirty=False) is False

    def test_clean_when_no_loop_ready(self, tmp_path: Path) -> None:
        """No loop-ready.json at all means the state bus has never been primed.
        Must return False regardless of tree state.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # No loop-ready.json present
        assert detect_mid_loop_death(state_dir, dirty=True) is False
        assert detect_mid_loop_death(state_dir, dirty=False) is False

    def test_ready_newer_but_tree_clean_is_not_death(self, tmp_path: Path) -> None:
        """If loop-ready is newer but the tree is clean, do NOT fire the alert.
        This can happen if the user manually reset the tree after a failure.
        /next-loop should proceed without operator prompt.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        complete_path = state_dir / "loop-complete.json"
        self._write_json(complete_path)
        time.sleep(0.05)
        ready_path = state_dir / "loop-ready.json"
        self._write_json(ready_path)

        assert detect_mid_loop_death(state_dir, dirty=False) is False

    def test_no_loop_complete_and_dirty_is_death(self, tmp_path: Path) -> None:
        """loop-ready.json exists but loop-complete.json does not AND tree is
        dirty.  This means the worker never completed even once -- treat as
        potential failure.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        ready_path = state_dir / "loop-ready.json"
        self._write_json(ready_path, '{"status": "ready"}')
        # No loop-complete.json

        assert detect_mid_loop_death(state_dir, dirty=True) is True

    def test_no_loop_complete_and_clean_tree_is_not_death(self, tmp_path: Path) -> None:
        """loop-ready.json exists, loop-complete absent, tree clean.
        Operator may have just started a fresh run -- do not block.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        ready_path = state_dir / "loop-ready.json"
        self._write_json(ready_path)
        # No loop-complete.json

        assert detect_mid_loop_death(state_dir, dirty=False) is False
