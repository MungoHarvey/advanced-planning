"""
test_orchestrator_state_cleanup.py -- Tests for the orchestrator stale-state cleanup
protocol (S9).

Guards against: a previous phase's loop-ready.json being consumed by the next phase's
orchestrator, producing a "Phase N starts with Phase N-1's state" failure mode.

Cleanup logic lives in state_manager.archive_cross_phase_state().

References:
  - core/agents/orchestrator.md: Step 0 (stale-state cleanup)
  - platforms/claude-code/agents/ralph-orchestrator.md: Step 0
  - .advanced-plans/specs/2026-05-20-phase-11-friction-remediation-design.md: S9
"""

import json
import re
import tempfile
from pathlib import Path

import pytest

from platforms.python.state_manager import archive_cross_phase_state


class TestArchiveCrossPhaseState:
    """Tests for stale-state archival at phase boundaries."""

    def _write_ready(self, state_dir: Path, phase: str) -> Path:
        """Write a minimal loop-ready.json with the given phase."""
        ready = state_dir / "loop-ready.json"
        ready.write_text(
            json.dumps({"phase": phase, "loop_name": "ralph-loop-001", "status": "ready"}),
            encoding="utf-8",
        )
        return ready

    def _write_complete(self, state_dir: Path) -> Path:
        """Write a minimal loop-complete.json."""
        complete = state_dir / "loop-complete.json"
        complete.write_text(
            json.dumps({"loop_name": "ralph-loop-001", "status": "completed"}),
            encoding="utf-8",
        )
        return complete

    # ---- Positive cases (archiving should happen) ----------------------------

    def test_cross_phase_ready_is_archived(self, tmp_path: Path) -> None:
        """When loop-ready.json phase != current_phase, the file is archived."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        self._write_ready(state_dir, phase="phase-old")

        result = archive_cross_phase_state(state_dir, current_phase="phase-11")

        assert result is not None
        assert result.exists(), "Archived file must exist at the returned path"
        assert "phase-old" in result.name
        assert (state_dir / "loop-ready.json").exists() is False

    def test_archive_dir_created_if_absent(self, tmp_path: Path) -> None:
        """The archive/ subdirectory is created automatically if it does not exist."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        self._write_ready(state_dir, phase="phase-10")

        archive_cross_phase_state(state_dir, current_phase="phase-11")

        archive_dir = state_dir / "archive"
        assert archive_dir.is_dir()

    def test_loop_complete_also_archived_when_present(self, tmp_path: Path) -> None:
        """When both loop-ready.json and loop-complete.json are present and stale,
        both are archived.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        self._write_ready(state_dir, phase="phase-10")
        self._write_complete(state_dir)

        archive_cross_phase_state(state_dir, current_phase="phase-11")

        assert (state_dir / "loop-ready.json").exists() is False
        assert (state_dir / "loop-complete.json").exists() is False

        archive_dir = state_dir / "archive"
        archived_files = list(archive_dir.iterdir())
        assert len(archived_files) == 2

    def test_archive_filename_matches_documented_format(self, tmp_path: Path) -> None:
        """Archived filename must match the documented format:
        <old-phase>-<YYYY-MM-DDTHH-MM-SS>-loop-ready.json
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        self._write_ready(state_dir, phase="phase-old")

        result = archive_cross_phase_state(state_dir, current_phase="phase-new")

        # Pattern: phase-old-<timestamp>-loop-ready.json
        pattern = r"^phase-old-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-loop-ready\.json$"
        assert re.match(pattern, result.name), (
            f"Archive filename {result.name!r} does not match expected format"
        )

    def test_archived_content_is_intact(self, tmp_path: Path) -> None:
        """The archived file must contain the original JSON content."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        self._write_ready(state_dir, phase="phase-9")

        result = archive_cross_phase_state(state_dir, current_phase="phase-11")

        data = json.loads(result.read_text(encoding="utf-8"))
        assert data["phase"] == "phase-9"

    # ---- Negative cases (no archiving should happen) -------------------------

    def test_no_archive_when_phase_matches(self, tmp_path: Path) -> None:
        """When the phase matches, loop-ready.json must NOT be touched."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        self._write_ready(state_dir, phase="phase-11")
        self._write_complete(state_dir)

        result = archive_cross_phase_state(state_dir, current_phase="phase-11")

        assert result is None
        assert (state_dir / "loop-ready.json").exists() is True
        assert (state_dir / "loop-complete.json").exists() is True

    def test_no_archive_when_no_loop_ready(self, tmp_path: Path) -> None:
        """When loop-ready.json does not exist, return None immediately."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        result = archive_cross_phase_state(state_dir, current_phase="phase-11")

        assert result is None

    def test_no_archive_when_phase_field_absent(self, tmp_path: Path) -> None:
        """If loop-ready.json lacks a 'phase' field, treat as matching and skip
        archive.  This maintains backwards compatibility with older state files.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        ready = state_dir / "loop-ready.json"
        ready.write_text(
            json.dumps({"loop_name": "ralph-loop-001", "status": "ready"}),
            encoding="utf-8",
        )

        result = archive_cross_phase_state(state_dir, current_phase="phase-11")

        assert result is None
        assert ready.exists() is True

    def test_loop_complete_not_touched_when_only_ready_is_stale(
        self, tmp_path: Path
    ) -> None:
        """If loop-complete.json is absent but loop-ready.json is stale, only
        loop-ready.json should be archived (no error on missing complete).
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        self._write_ready(state_dir, phase="phase-old")
        # No loop-complete.json

        result = archive_cross_phase_state(state_dir, current_phase="phase-new")

        assert result is not None
        assert (state_dir / "loop-ready.json").exists() is False
        # loop-complete was never created -- archive dir should only have one file
        archive_dir = state_dir / "archive"
        archived_files = list(archive_dir.iterdir())
        assert len(archived_files) == 1
