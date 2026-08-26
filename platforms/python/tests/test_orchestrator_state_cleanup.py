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

    # ---- Phase-boundary scenario (059 guard) -----------------------------------

    def test_prior_phase_ready_moved_to_archive_not_read_as_current(
        self, tmp_path: Path
    ) -> None:
        """Regression guard for the Loop-059 requirement.

        At a phase boundary, a loop-ready.json that belongs to a prior phase
        must be moved into archive/ — it must NOT remain in state_dir where the
        new phase's orchestrator would consume it as if it were the current loop
        assignment.

        Scenario: phase-14 leaves loop-ready.json in state/; phase-15 starts.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Simulate prior-phase remnant (phase-14 left this behind)
        prior_ready_content = {
            "phase": "phase-14",
            "loop_name": "ralph-loop-058",
            "status": "ready",
            "task_name": "Witnessed Exercise + v0.14.0 Release",
        }
        ready_path = state_dir / "loop-ready.json"
        ready_path.write_text(json.dumps(prior_ready_content), encoding="utf-8")

        # Phase-15 orchestrator calls archive at startup
        result = archive_cross_phase_state(state_dir, current_phase="phase-15")

        # The file must have been moved — not readable as current assignment
        assert result is not None, "archive_cross_phase_state must return the archived path"
        assert not ready_path.exists(), (
            "Prior-phase loop-ready.json must no longer exist in state_dir; "
            "it would otherwise be consumed as the current phase's assignment"
        )

        # The archived file must be in archive/ and contain the original data intact
        archive_dir = state_dir / "archive"
        assert archive_dir.is_dir()
        archived_data = json.loads(result.read_text(encoding="utf-8"))
        assert archived_data["phase"] == "phase-14"
        assert archived_data["loop_name"] == "ralph-loop-058"


class TestPhaseKeyIsWrittenByBothWriters:
    """The guard reads loop-ready.json["phase"]. Both writers must supply it.

    write_loop_ready() (the orchestrator path) omitted it while
    prepare_loop_ready() (the fast path) supplied it, so archive_cross_phase_state
    silently returned None for every file the orchestrator produced -- exactly the
    files it exists to catch. These tests pin both halves of the fix.
    """

    def test_write_loop_ready_records_the_phase(self, tmp_path: Path) -> None:
        from platforms.python.state_manager import write_loop_ready

        path = write_loop_ready(
            tmp_path / "state",
            loop_name="ralph-loop-003",
            loop_file=".advanced-plans/phases/phase-2/loops.md",
            task_name="whatever",
            todos_count=6,
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["phase"] == "phase-2"

    def test_orchestrator_written_state_is_archived_across_phases(
        self, tmp_path: Path
    ) -> None:
        """End-to-end: the guard fires on a file write_loop_ready produced."""
        from platforms.python.state_manager import write_loop_ready

        state_dir = tmp_path / "state"
        write_loop_ready(
            state_dir,
            loop_name="ralph-loop-003",
            loop_file=".advanced-plans/phases/phase-2/loops.md",
            task_name="a finished phase's loop",
            todos_count=6,
        )

        result = archive_cross_phase_state(state_dir, current_phase="phase-5")

        assert result is not None, "stale phase-2 state must not survive into phase-5"
        assert "phase-2" in result.name
        assert not (state_dir / "loop-ready.json").exists()

    def test_both_writers_agree_on_the_phase_key(self, tmp_path: Path) -> None:
        """prepare_loop_ready and write_loop_ready must not disagree on schema."""
        from platforms.python.state_manager import write_loop_ready

        loop_file = ".advanced-plans/phases/phase-7/loops.md"
        path = write_loop_ready(
            tmp_path / "state",
            loop_name="ralph-loop-001",
            loop_file=loop_file,
            task_name="t",
            todos_count=1,
        )
        written = json.loads(path.read_text(encoding="utf-8"))
        # prepare_loop_ready builds its payload with "phase" set from the same
        # source; the key and its derivation must match.
        from platforms.python.state_manager import _phase_from_loop_file

        assert written["phase"] == _phase_from_loop_file(loop_file) == "phase-7"


class TestPhaseFallbackFromLoopFile:
    """State files already on disk have no "phase" key and never will.

    Deriving it from loop_file is what lets the guard fire on them.
    """

    def test_legacy_file_without_phase_key_is_still_archived(
        self, tmp_path: Path
    ) -> None:
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        (state_dir / "loop-ready.json").write_text(
            json.dumps(
                {
                    "loop_name": "ralph-loop-003",
                    "loop_file": ".advanced-plans/phases/phase-2/loops.md",
                    "status": "ready",
                }
            ),
            encoding="utf-8",
        )

        result = archive_cross_phase_state(state_dir, current_phase="phase-5")

        assert result is not None
        assert "phase-2" in result.name

    def test_explicit_phase_key_wins_over_the_path(self, tmp_path: Path) -> None:
        """The recorded phase is authoritative; the path is only a fallback."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        (state_dir / "loop-ready.json").write_text(
            json.dumps(
                {
                    "phase": "phase-9",
                    "loop_file": ".advanced-plans/phases/phase-2/loops.md",
                    "status": "ready",
                }
            ),
            encoding="utf-8",
        )

        result = archive_cross_phase_state(state_dir, current_phase="phase-5")

        assert result is not None
        assert "phase-9" in result.name

    def test_no_phase_anywhere_is_left_alone(self, tmp_path: Path) -> None:
        """Unattributable state is not archived -- silence is not evidence."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        (state_dir / "loop-ready.json").write_text(
            json.dumps({"loop_name": "ralph-loop-001", "status": "ready"}),
            encoding="utf-8",
        )

        assert archive_cross_phase_state(state_dir, current_phase="phase-5") is None
        assert (state_dir / "loop-ready.json").exists()

    def test_matching_phase_from_path_is_not_archived(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        (state_dir / "loop-ready.json").write_text(
            json.dumps(
                {
                    "loop_file": ".advanced-plans/phases/phase-5/loops.md",
                    "status": "ready",
                }
            ),
            encoding="utf-8",
        )

        assert archive_cross_phase_state(state_dir, current_phase="phase-5") is None
        assert (state_dir / "loop-ready.json").exists()
