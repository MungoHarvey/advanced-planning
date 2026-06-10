"""Tests for platforms.python.history_log."""

import json
import subprocess
import sys

import pytest

from platforms.python.history_log import append_event


class TestCompactFormat:
    """Events are serialised without spaces around separators."""

    def test_no_space_after_comma(self, tmp_path):
        out = tmp_path / "history.jsonl"
        append_event(out, {"event": "loop_complete", "phase": "phase-16"})
        line = out.read_text(encoding="utf-8").rstrip("\n")
        assert ", " not in line, f"Space after comma found: {line!r}"

    def test_no_space_after_colon(self, tmp_path):
        out = tmp_path / "history.jsonl"
        append_event(out, {"event": "gate_pass", "phase": "phase-16"})
        line = out.read_text(encoding="utf-8").rstrip("\n")
        assert ": " not in line, f"Space after colon found: {line!r}"

    def test_line_is_valid_json(self, tmp_path):
        out = tmp_path / "history.jsonl"
        append_event(out, {"event": "phase_planned", "phase": "phase-16", "loops": 5})
        line = out.read_text(encoding="utf-8").rstrip("\n")
        parsed = json.loads(line)
        assert parsed["event"] == "phase_planned"


class TestTimestampInjection:
    """Timestamp is injected when absent and preserved when present."""

    def test_timestamp_injected_when_absent(self, tmp_path):
        out = tmp_path / "history.jsonl"
        append_event(out, {"event": "loop_complete", "phase": "phase-16"})
        line = out.read_text(encoding="utf-8").rstrip("\n")
        record = json.loads(line)
        assert "timestamp" in record
        ts = record["timestamp"]
        # Basic ISO-8601 UTC shape: YYYY-MM-DDTHH:MM:SSZ
        assert len(ts) == 20 and ts.endswith("Z"), f"Unexpected timestamp shape: {ts!r}"

    def test_timestamp_preserved_when_present(self, tmp_path):
        out = tmp_path / "history.jsonl"
        fixed_ts = "2026-01-01T00:00:00Z"
        append_event(out, {"event": "gate_pass", "timestamp": fixed_ts, "phase": "phase-16"})
        line = out.read_text(encoding="utf-8").rstrip("\n")
        record = json.loads(line)
        assert record["timestamp"] == fixed_ts


class TestAppendOnly:
    """Existing lines are never modified; new events are appended."""

    def test_existing_lines_byte_untouched(self, tmp_path):
        out = tmp_path / "history.jsonl"
        first_event = {"event": "gate_pass", "phase": "phase-15", "timestamp": "2026-06-09T18:20:18Z"}
        first_line = json.dumps(first_event, separators=(",", ":")) + "\n"
        out.write_text(first_line, encoding="utf-8")

        append_event(out, {"event": "loop_complete", "phase": "phase-16"})

        lines = out.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        assert lines[0] == first_line.rstrip("\n"), (
            f"First line was modified: {lines[0]!r}"
        )

    def test_multiple_appends_grow_file(self, tmp_path):
        out = tmp_path / "history.jsonl"
        for i in range(3):
            append_event(out, {"event": "loop_complete", "phase": f"phase-{i}"})
        lines = out.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 3

    def test_parent_dir_created_if_missing(self, tmp_path):
        nested = tmp_path / "state" / "subdir" / "history.jsonl"
        append_event(nested, {"event": "test"})
        assert nested.exists()


class TestGreppability:
    """Events can be found by grepping for quoted field values."""

    def test_phase_field_greppable(self, tmp_path):
        out = tmp_path / "history.jsonl"
        append_event(out, {"event": "gate_pass", "phase": "phase-16"})
        content = out.read_text(encoding="utf-8")
        assert '"phase":"phase-16"' in content

    def test_event_field_greppable(self, tmp_path):
        out = tmp_path / "history.jsonl"
        append_event(out, {"event": "loop_complete", "phase": "phase-16"})
        content = out.read_text(encoding="utf-8")
        assert '"event":"loop_complete"' in content


class TestCLIInvocation:
    """CLI appends the event supplied as a JSON string argument."""

    def test_cli_appends_event(self, tmp_path):
        out = tmp_path / "history.jsonl"
        event_json = '{"event":"loop_complete","phase":"phase-16","loop":"ralph-loop-065"}'
        result = subprocess.run(
            [sys.executable, "-m", "platforms.python.history_log", str(out), event_json],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        lines = out.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["event"] == "loop_complete"
        assert record["phase"] == "phase-16"

    def test_cli_invalid_json_exits_nonzero(self, tmp_path):
        out = tmp_path / "history.jsonl"
        result = subprocess.run(
            [sys.executable, "-m", "platforms.python.history_log", str(out), "not-json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert not out.exists()

    def test_cli_timestamp_injected(self, tmp_path):
        out = tmp_path / "history.jsonl"
        event_json = '{"event":"phase_planned","phase":"phase-16"}'
        subprocess.run(
            [sys.executable, "-m", "platforms.python.history_log", str(out), event_json],
            check=True,
        )
        record = json.loads(out.read_text(encoding="utf-8").strip())
        assert "timestamp" in record
