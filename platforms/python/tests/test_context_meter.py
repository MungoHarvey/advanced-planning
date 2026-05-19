"""Unit tests for platforms.python.context_meter (Loop 037 extension)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3]))

from platforms.python.context_meter import (
    occupancy,
    last_usage,
    detect_segments,
    content_type_breakdown,
    activity_attribution,
    format_line,
    format_report,
    find_current_transcript,
    _load_records,
    _is_compaction_boundary,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_assistant_record(usage_dict: dict, content=None) -> dict:
    """Build a minimal assistant-message JSONL record."""
    msg: dict = {"role": "assistant", "usage": usage_dict}
    if content is not None:
        msg["content"] = content
    return {"type": "message", "message": msg}


def _write_jsonl(path: Path, records: list) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")


# ---------------------------------------------------------------------------
# occupancy
# ---------------------------------------------------------------------------

class TestOccupancy:
    def test_sums_all_three_fields(self):
        usage = {
            "input_tokens": 1000,
            "cache_read_input_tokens": 500,
            "cache_creation_input_tokens": 200,
        }
        assert occupancy(usage) == 1700

    def test_missing_fields_default_to_zero(self):
        assert occupancy({}) == 0
        assert occupancy({"input_tokens": 300}) == 300

    def test_zero_usage(self):
        usage = {
            "input_tokens": 0,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        }
        assert occupancy(usage) == 0

    def test_partial_fields(self):
        usage = {"cache_read_input_tokens": 800, "cache_creation_input_tokens": 200}
        assert occupancy(usage) == 1000


# ---------------------------------------------------------------------------
# last_usage
# ---------------------------------------------------------------------------

class TestLastUsage:
    def test_returns_last_assistant_usage(self, tmp_path):
        t = tmp_path / "session.jsonl"
        r1 = _make_assistant_record({"input_tokens": 100})
        r2 = _make_assistant_record({"input_tokens": 200})
        _write_jsonl(t, [r1, r2])
        result = last_usage(t)
        assert result == {"input_tokens": 200}

    def test_skips_non_assistant_records(self, tmp_path):
        t = tmp_path / "session.jsonl"
        user_rec = {"type": "message", "message": {"role": "user", "content": "hi"}}
        asst_rec = _make_assistant_record({"input_tokens": 50})
        _write_jsonl(t, [user_rec, asst_rec])
        result = last_usage(t)
        assert result == {"input_tokens": 50}

    def test_returns_none_when_no_usage_blocks(self, tmp_path):
        t = tmp_path / "session.jsonl"
        _write_jsonl(t, [{"type": "other", "data": 1}])
        assert last_usage(t) is None

    def test_returns_none_on_empty_file(self, tmp_path):
        t = tmp_path / "empty.jsonl"
        t.write_text("")
        assert last_usage(t) is None

    def test_skips_malformed_lines(self, tmp_path):
        t = tmp_path / "session.jsonl"
        with t.open("w") as fh:
            fh.write("not-json\n")
            fh.write(json.dumps(_make_assistant_record({"input_tokens": 77})) + "\n")
        result = last_usage(t)
        assert result == {"input_tokens": 77}


# ---------------------------------------------------------------------------
# detect_segments
# ---------------------------------------------------------------------------

class TestDetectSegments:
    def _compaction_record(self) -> dict:
        """A record that marks a compaction boundary."""
        return _make_assistant_record(
            {"input_tokens": 10},
            content="The session is being continued from a previous conversation."
        )

    def test_single_segment_no_boundary(self):
        records = [
            _make_assistant_record({"input_tokens": 100}),
            _make_assistant_record({"input_tokens": 200}),
        ]
        segs = detect_segments(records)
        assert len(segs) == 1
        assert segs[0]["start"] == 0
        assert segs[0]["end"] == 1
        assert segs[0]["record_count"] == 2

    def test_two_segments_one_boundary(self):
        records = [
            _make_assistant_record({"input_tokens": 100}),
            self._compaction_record(),
            _make_assistant_record({"input_tokens": 200}),
        ]
        segs = detect_segments(records)
        assert len(segs) == 2
        assert segs[0]["end"] == 0
        assert segs[1]["start"] == 1

    def test_approx_tokens_summed_per_segment(self):
        records = [
            _make_assistant_record({"input_tokens": 100}),
            _make_assistant_record({"input_tokens": 200}),
            self._compaction_record(),
            _make_assistant_record({"input_tokens": 50}),
        ]
        segs = detect_segments(records)
        assert segs[0]["approx_tokens"] == 300
        # Segment 1 includes the compaction boundary record + last record
        # (boundary record has input_tokens=10; last has 50)
        assert segs[1]["approx_tokens"] == 60

    def test_empty_records(self):
        assert detect_segments([]) == []

    def test_segment_index_increments(self):
        cmp = self._compaction_record()
        records = [
            _make_assistant_record({"input_tokens": 1}),
            cmp,
            _make_assistant_record({"input_tokens": 2}),
            cmp,
            _make_assistant_record({"input_tokens": 3}),
        ]
        segs = detect_segments(records)
        assert [s["index"] for s in segs] == [0, 1, 2]


# ---------------------------------------------------------------------------
# _is_compaction_boundary
# ---------------------------------------------------------------------------

class TestIsCompactionBoundary:
    def test_detects_string_content(self):
        rec = _make_assistant_record({"input_tokens": 0}, content="The session is being continued from a previous conversation.")
        assert _is_compaction_boundary(rec) is True

    def test_detects_list_content_text_block(self):
        rec = _make_assistant_record(
            {"input_tokens": 0},
            content=[{"type": "text", "text": "The previous conversation has been compacted."}]
        )
        assert _is_compaction_boundary(rec) is True

    def test_non_boundary(self):
        rec = _make_assistant_record({"input_tokens": 0}, content="Just a normal reply.")
        assert _is_compaction_boundary(rec) is False

    def test_non_message_record(self):
        assert _is_compaction_boundary({"type": "tool_result"}) is False


# ---------------------------------------------------------------------------
# content_type_breakdown
# ---------------------------------------------------------------------------

class TestContentTypeBreakdown:
    def test_counts_tool_use_and_tool_result(self):
        records = [
            _make_assistant_record({"input_tokens": 0}, content=[
                {"type": "tool_use", "id": "1"},
                {"type": "tool_result", "content": "ok"},
            ]),
            _make_assistant_record({"input_tokens": 0}, content=[
                {"type": "text", "text": "hi"},
            ]),
        ]
        ct = content_type_breakdown(records)
        assert ct["tool_use"] == 1
        assert ct["tool_result"] == 1
        assert ct["text"] == 1

    def test_counts_string_content_as_str(self):
        records = [_make_assistant_record({"input_tokens": 0}, content="plain string")]
        ct = content_type_breakdown(records)
        assert ct["str"] == 1

    def test_empty_records(self):
        ct = content_type_breakdown([])
        assert all(v == 0 for v in ct.values())

    def test_thinking_counted(self):
        records = [
            _make_assistant_record({"input_tokens": 0}, content=[
                {"type": "thinking", "thinking": "..."},
            ])
        ]
        ct = content_type_breakdown(records)
        assert ct["thinking"] == 1

    def test_unknown_type_goes_to_other(self):
        records = [
            _make_assistant_record({"input_tokens": 0}, content=[
                {"type": "image", "source": "..."},
            ])
        ]
        ct = content_type_breakdown(records)
        assert ct.get("other", 0) >= 1


# ---------------------------------------------------------------------------
# activity_attribution
# ---------------------------------------------------------------------------

class TestActivityAttribution:
    def test_tool_result_goes_to_raw_tool_io(self):
        records = [
            _make_assistant_record({"input_tokens": 0}, content=[
                {"type": "tool_result", "content": "file contents here"}
            ])
        ]
        act = activity_attribution(records)
        assert act["raw_tool_io"] == 1

    def test_skill_body_goes_to_skill_command_bodies(self):
        records = [
            _make_assistant_record({"input_tokens": 0}, content=[
                {"type": "text", "text": "## When to Use\nThis skill is for XYZ."}
            ])
        ]
        act = activity_attribution(records)
        assert act["skill_command_bodies"] == 1

    def test_decision_text_goes_to_decisions(self):
        records = [
            _make_assistant_record({"input_tokens": 0}, content=[
                {"type": "text", "text": "Gate pass: all criteria met. verdict: pass"}
            ])
        ]
        act = activity_attribution(records)
        assert act["decisions"] == 1

    def test_all_buckets_present(self):
        act = activity_attribution([])
        assert "raw_tool_io" in act
        assert "skill_command_bodies" in act
        assert "decisions" in act
        assert "other" in act


# ---------------------------------------------------------------------------
# format_line
# ---------------------------------------------------------------------------

class TestFormatLine:
    def test_contains_token_count(self):
        usage = {"input_tokens": 100_000, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
        line = format_line(usage, 200_000)
        assert "100.0k" in line
        assert "50%" in line

    def test_zero_limit_doesnt_crash(self):
        usage = {"input_tokens": 50}
        line = format_line(usage, 0)
        assert "Context:" in line

    def test_contains_breakdown(self):
        usage = {
            "input_tokens": 10,
            "cache_read_input_tokens": 20,
            "cache_creation_input_tokens": 30,
            "output_tokens": 5,
        }
        line = format_line(usage, 200_000)
        assert "input 10" in line
        assert "cache_read 20" in line
        assert "cache_creation 30" in line


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------

class TestFormatReport:
    def _make_records(self, n: int = 5) -> list:
        return [_make_assistant_record({"input_tokens": 1000 * (i + 1)}) for i in range(n)]

    def test_contains_occupancy_line(self):
        usage = {"input_tokens": 50_000, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
        report = format_report(usage, 200_000, self._make_records())
        assert "50.0k" in report
        assert "25%" in report

    def test_contains_segment_section(self):
        report = format_report(
            {"input_tokens": 1000},
            200_000,
            self._make_records(),
        )
        assert "Segments" in report

    def test_contains_content_type_breakdown(self):
        report = format_report({"input_tokens": 1000}, 200_000, self._make_records())
        assert "Content-type breakdown" in report

    def test_contains_activity_section(self):
        report = format_report({"input_tokens": 1000}, 200_000, self._make_records())
        assert "Activity attribution" in report

    def test_contains_projected_saving(self):
        report = format_report({"input_tokens": 1000}, 200_000, self._make_records())
        assert "Projected post-compaction" in report

    def test_ascii_only(self):
        report = format_report({"input_tokens": 5000}, 200_000, self._make_records())
        # Ensure no non-ASCII characters (Windows cp1252 safe)
        report.encode("ascii")

    def test_no_exception_with_empty_records(self):
        usage = {"input_tokens": 1000}
        report = format_report(usage, 200_000, [])
        assert "Context Occupancy Report" in report


# ---------------------------------------------------------------------------
# find_current_transcript
# ---------------------------------------------------------------------------

class TestFindCurrentTranscript:
    def test_returns_none_when_no_project_dir(self, tmp_path, monkeypatch):
        # Point home to a temp dir where no .claude/projects subdir exists
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        result = find_current_transcript(cwd=tmp_path / "myproject")
        assert result is None

    def test_returns_newest_jsonl(self, tmp_path, monkeypatch):
        import time
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        # Create the project slug directory
        cwd = Path("C:/myproject")  # fake cwd
        slug = str(cwd).replace(":", "-").replace("\\", "-").replace("/", "-")
        proj_dir = tmp_path / ".claude" / "projects" / slug
        proj_dir.mkdir(parents=True)
        f1 = proj_dir / "old.jsonl"
        f2 = proj_dir / "new.jsonl"
        f1.write_text("{}\n")
        time.sleep(0.01)
        f2.write_text("{}\n")
        result = find_current_transcript(cwd=cwd)
        assert result == f2

    def test_returns_none_when_dir_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        cwd = Path("C:/myproject2")
        slug = str(cwd).replace(":", "-").replace("\\", "-").replace("/", "-")
        proj_dir = tmp_path / ".claude" / "projects" / slug
        proj_dir.mkdir(parents=True)
        result = find_current_transcript(cwd=cwd)
        assert result is None


# ---------------------------------------------------------------------------
# missing-transcript degrade (no exception)
# ---------------------------------------------------------------------------

class TestMissingTranscriptDegrade:
    def test_last_usage_missing_file_raises_on_open(self, tmp_path):
        """last_usage on missing file raises FileNotFoundError (caller handles)."""
        with pytest.raises(FileNotFoundError):
            last_usage(tmp_path / "nonexistent.jsonl")

    def test_load_records_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _load_records(tmp_path / "nonexistent.jsonl")

    def test_main_missing_transcript_prints_unavailable(self, tmp_path, monkeypatch, capsys):
        """main() with no transcript found prints 'unavailable' and returns 1."""
        # Ensure find_current_transcript returns None
        monkeypatch.setattr(
            "platforms.python.context_meter.find_current_transcript",
            lambda cwd=None: None,
        )
        from platforms.python.context_meter import main
        ret = main([])
        captured = capsys.readouterr()
        assert ret == 1
        assert "unavailable" in captured.out

    def test_main_with_nonexistent_transcript_path_returns_1(self, tmp_path, capsys):
        from platforms.python.context_meter import main
        ret = main([str(tmp_path / "no_such.jsonl")])
        assert ret == 1
        assert "unavailable" in capsys.readouterr().out
