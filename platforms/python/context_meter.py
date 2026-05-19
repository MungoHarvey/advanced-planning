"""Measure live conversation-context occupancy from a Claude Code session transcript.

Zero-dependency (standard library only) to honour the project CI invariant.

The Claude Code transcript is a JSONL file where each assistant message records the
API's real ``usage`` block. The effective context occupancy for a turn is::

    input_tokens + cache_read_input_tokens + cache_creation_input_tokens

This is the same figure ``/usage`` surfaces in the terminal, but read from the
transcript so it can be emitted into a command's output and seen by the agent
inline. Intended to be invoked once at phase end (e.g. by ``/phase-compact``),
not every turn.

Extensions (Loop 037):
- Segment detection: split transcript at compaction-summary boundaries
- Content-type breakdown: tool_use / tool_result / text / thinking / str token shares
- Activity attribution: raw tool I/O / skill+command bodies / decisions / other
- --report mode: occupancy + how-used narrative + projected post-compaction saving
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _dasherize_cwd(cwd: Path) -> str:
    """Reproduce Claude Code's project-dir slug (drive colon and separators -> '-')."""
    return str(cwd).replace(":", "-").replace("\\", "-").replace("/", "-")


def find_current_transcript(cwd: Optional[Path] = None) -> Optional[Path]:
    """Newest top-level ``*.jsonl`` for this project (excludes subagent transcripts)."""
    cwd = cwd or Path.cwd()
    projects = Path.home() / ".claude" / "projects" / _dasherize_cwd(cwd)
    if not projects.is_dir():
        return None
    candidates = [p for p in projects.glob("*.jsonl") if p.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


# ---------------------------------------------------------------------------
# Basic transcript reading
# ---------------------------------------------------------------------------

def _load_records(transcript: Path) -> list:
    """Return all non-empty parsed JSONL records from *transcript*."""
    records = []
    with transcript.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def last_usage(transcript: Path) -> Optional[dict]:
    """Return the ``usage`` block of the most recent assistant message, or None."""
    found = None
    for obj in _load_records(transcript):
        msg = obj.get("message")
        if isinstance(msg, dict) and isinstance(msg.get("usage"), dict):
            found = msg["usage"]
    return found


def occupancy(usage: dict) -> int:
    """Effective context tokens held on the measured turn."""
    return (
        usage.get("input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
    )


# ---------------------------------------------------------------------------
# Segment detection
# ---------------------------------------------------------------------------

_COMPACTION_MARKERS = (
    "session is being continued",
    "previous conversation has been compacted",
    "conversation has been compacted",
)


def _is_compaction_boundary(record: dict) -> bool:
    """Return True if *record* contains a Claude-emitted compaction summary."""
    msg = record.get("message")
    if not isinstance(msg, dict):
        return False
    content = msg.get("content")
    if isinstance(content, str):
        low = content.lower()
        return any(m in low for m in _COMPACTION_MARKERS)
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                text = block.get("text", "")
                if isinstance(text, str) and any(m in text.lower() for m in _COMPACTION_MARKERS):
                    return True
    return False


def _record_timestamp(record: dict) -> Optional[str]:
    """Best-effort ISO timestamp from a record (common field names)."""
    for field in ("timestamp", "created_at", "time"):
        val = record.get(field)
        if val:
            return str(val)
    return None


def _usage_for_record(record: dict) -> int:
    """Occupancy contribution of a single record (0 if not an assistant message)."""
    msg = record.get("message")
    if isinstance(msg, dict):
        usage = msg.get("usage")
        if isinstance(usage, dict):
            return occupancy(usage)
    return 0


def detect_segments(records: list) -> list:
    """Split *records* at compaction-summary boundaries.

    Returns a list of dicts::

        {
            "index": int,          # 0-based segment number
            "start": int,          # first record index (inclusive)
            "end": int,            # last record index (inclusive)
            "record_count": int,
            "start_time": str | None,
            "end_time": str | None,
            "approx_tokens": int,  # sum of occupancy of assistant messages in segment
        }
    """
    if not records:
        return []

    segments = []
    seg_start = 0

    for i, rec in enumerate(records):
        if i > 0 and _is_compaction_boundary(rec):
            # close previous segment
            seg_records = records[seg_start:i]
            segments.append(_make_segment(len(segments), seg_start, i - 1, seg_records))
            seg_start = i

    # final segment
    seg_records = records[seg_start:]
    segments.append(_make_segment(len(segments), seg_start, len(records) - 1, seg_records))
    return segments


def _make_segment(index: int, start: int, end: int, seg_records: list) -> dict:
    tok = sum(_usage_for_record(r) for r in seg_records)
    timestamps = [_record_timestamp(r) for r in seg_records if _record_timestamp(r)]
    return {
        "index": index,
        "start": start,
        "end": end,
        "record_count": len(seg_records),
        "start_time": timestamps[0] if timestamps else None,
        "end_time": timestamps[-1] if timestamps else None,
        "approx_tokens": tok,
    }


# ---------------------------------------------------------------------------
# Content-type breakdown
# ---------------------------------------------------------------------------

_CONTENT_TYPES = ("tool_use", "tool_result", "text", "thinking", "str")


def content_type_breakdown(records: list) -> dict:
    """Count content blocks by type across all messages in *records*.

    Returns dict mapping type -> count.  'str' catches string-valued content
    that has no explicit type block.
    """
    counts: dict = {t: 0 for t in _CONTENT_TYPES}
    counts["other"] = 0

    for record in records:
        msg = record.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if isinstance(content, str):
            counts["str"] += 1
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    btype = block.get("type", "other")
                    if btype in counts:
                        counts[btype] += 1
                    else:
                        counts["other"] += 1
                elif isinstance(block, str):
                    counts["str"] += 1

    return counts


# ---------------------------------------------------------------------------
# Activity attribution
# ---------------------------------------------------------------------------

# Heuristic keywords that indicate skill/command injected bodies
_SKILL_KEYWORDS = (
    "## when to use",
    "## process",
    "## output format",
    "skill.md",
    "slash command",
    "## overview",
)

_DECISION_KEYWORDS = (
    "## decision",
    "approved",
    "rejected",
    "verdict",
    "gate pass",
    "gate fail",
    "chosen",
)


def _classify_block_text(text: str) -> str:
    """Return activity bucket for a single text string."""
    low = text.lower()
    for kw in _SKILL_KEYWORDS:
        if kw in low:
            return "skill_command_bodies"
    for kw in _DECISION_KEYWORDS:
        if kw in low:
            return "decisions"
    # tool result / file read heuristic: large blocks of raw content
    # (we can't know for certain; approximate by block length)
    if len(text) > 500:
        return "raw_tool_io"
    return "other"


def activity_attribution(records: list) -> dict:
    """Attribute content blocks to activity buckets.

    Buckets:
        raw_tool_io         -- tool_result blocks + large str content (file reads)
        skill_command_bodies -- blocks that appear to be injected skill/command text
        decisions           -- blocks containing decision/verdict language
        other               -- everything else

    Returns dict bucket -> count.
    """
    buckets: dict = {
        "raw_tool_io": 0,
        "skill_command_bodies": 0,
        "decisions": 0,
        "other": 0,
    }

    for record in records:
        msg = record.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        blocks = []
        if isinstance(content, str):
            blocks = [{"type": "str", "text": content}]
        elif isinstance(content, list):
            for b in content:
                if isinstance(b, str):
                    blocks.append({"type": "str", "text": b})
                elif isinstance(b, dict):
                    blocks.append(b)

        for block in blocks:
            btype = block.get("type", "")
            if btype == "tool_result":
                buckets["raw_tool_io"] += 1
            elif btype == "tool_use":
                # tool_use is overhead but not "raw I/O"
                buckets["other"] += 1
            elif btype in ("text", "thinking", "str"):
                text = block.get("text", "") or block.get("content", "") or ""
                if not isinstance(text, str):
                    text = str(text)
                bucket = _classify_block_text(text)
                buckets[bucket] += 1
            else:
                buckets["other"] += 1

    return buckets


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_line(usage: dict, limit: int) -> str:
    ctx = occupancy(usage)
    pct = (ctx / limit * 100.0) if limit else 0.0
    return (
        f"Context: ~{ctx/1000:.1f}k tokens (~{pct:.0f}% of {limit//1000}k limit) "
        f"- measured from transcript "
        f"[input {usage.get('input_tokens',0)} + "
        f"cache_read {usage.get('cache_read_input_tokens',0)} + "
        f"cache_creation {usage.get('cache_creation_input_tokens',0)}; "
        f"last output {usage.get('output_tokens',0)}]"
    )


def _pct(numerator: int, denominator: int) -> str:
    if not denominator:
        return "0%"
    return f"{numerator/denominator*100:.0f}%"


def _bar(pct_float: float, width: int = 20) -> str:
    """Simple ASCII progress bar."""
    filled = int(pct_float / 100 * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def format_report(usage: dict, limit: int, records: list) -> str:
    """Return a multi-line transparency report (ASCII-only)."""
    lines = []

    ctx = occupancy(usage)
    pct = (ctx / limit * 100.0) if limit else 0.0
    bar = _bar(pct)

    lines.append("=" * 60)
    lines.append("  Context Occupancy Report")
    lines.append("=" * 60)
    lines.append(f"  Occupancy : ~{ctx/1000:.1f}k / {limit//1000}k tokens  ({pct:.0f}%)")
    lines.append(f"              {bar}")
    lines.append(f"  Breakdown : input={usage.get('input_tokens',0):,}  "
                 f"cache_read={usage.get('cache_read_input_tokens',0):,}  "
                 f"cache_creation={usage.get('cache_creation_input_tokens',0):,}")
    lines.append(f"  Output    : {usage.get('output_tokens',0):,} tokens (last turn)")
    lines.append("")

    # Segment table
    segs = detect_segments(records)
    lines.append(f"  Segments  : {len(segs)} (split at compaction boundaries)")
    if segs:
        lines.append(f"  {'Seg':>3}  {'Records':>7}  {'Approx Tok':>11}  Time span")
        for s in segs:
            span = ""
            if s["start_time"] and s["end_time"]:
                span = f"{s['start_time'][:19]} -> {s['end_time'][:19]}"
            elif s["start_time"]:
                span = s["start_time"][:19]
            lines.append(
                f"  {s['index']:>3}  {s['record_count']:>7}  "
                f"{s['approx_tokens']:>11,}  {span}"
            )
    lines.append("")

    # Content-type breakdown
    ct = content_type_breakdown(records)
    total_blocks = sum(ct.values()) or 1
    lines.append("  Content-type breakdown (blocks):")
    for ctype, count in sorted(ct.items(), key=lambda x: -x[1]):
        if count:
            lines.append(f"    {ctype:<20} {count:>6}  ({_pct(count, total_blocks)})")
    lines.append("")

    # Activity attribution
    act = activity_attribution(records)
    total_act = sum(act.values()) or 1
    lines.append("  Activity attribution (blocks):")
    for bucket, count in sorted(act.items(), key=lambda x: -x[1]):
        lines.append(f"    {bucket:<24} {count:>6}  ({_pct(count, total_act)})")
    lines.append("")

    # How-used narrative
    raw_pct = int(act.get("raw_tool_io", 0) / total_act * 100)
    skill_pct = int(act.get("skill_command_bodies", 0) / total_act * 100)
    lines.append("  How context is being used:")
    lines.append(f"    ~{raw_pct}% raw tool I/O (file reads + bash output) -- recoverable from disk")
    lines.append(f"    ~{skill_pct}% injected skill/command bodies -- reload on demand")
    lines.append("    Remaining: decisions, summaries, and assistant reasoning")
    lines.append("")

    # Projected post-compaction saving
    # Heuristic: raw tool I/O + skill bodies are the recoverable fraction
    recoverable_frac = (
        act.get("raw_tool_io", 0) + act.get("skill_command_bodies", 0)
    ) / total_act
    saved_tokens = int(ctx * recoverable_frac)
    post_compact = ctx - saved_tokens
    post_pct = (post_compact / limit * 100.0) if limit else 0.0
    lines.append("  Projected post-compaction occupancy:")
    lines.append(f"    Recoverable (tool I/O + skill bodies): ~{saved_tokens/1000:.1f}k tokens")
    lines.append(f"    Estimated post-compact: ~{post_compact/1000:.1f}k / {limit//1000}k "
                 f"({post_pct:.0f}%)")
    lines.append(f"    Compaction would free ~{saved_tokens/1000:.1f}k tokens "
                 f"(~{int(recoverable_frac*100)}% of current occupancy)")
    lines.append("")
    lines.append("  Note: projections are heuristic estimates; actual saving depends on")
    lines.append("        compaction prompt and model behaviour.")
    lines.append("=" * 60)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# stdin hook
# ---------------------------------------------------------------------------

def _read_stdin_transcript_path() -> Optional[Path]:
    """Hook mode: Claude Code passes a JSON payload on stdin with transcript_path."""
    if sys.stdin.isatty():
        return None
    raw = sys.stdin.read().strip()
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    tp = payload.get("transcript_path")
    return Path(tp) if tp else None


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Report live context occupancy.")
    parser.add_argument("transcript", nargs="?", help="Path to session .jsonl")
    parser.add_argument("--limit", type=int, default=200_000,
                        help="Context window limit in tokens (default 200000)")
    parser.add_argument("--stdin-hook", action="store_true",
                        help="Read transcript_path from a hook JSON payload on stdin")
    parser.add_argument("--report", action="store_true",
                        help="Print full transparency report (occupancy + breakdown + projection)")
    args = parser.parse_args(argv)

    transcript: Optional[Path] = None
    if args.transcript:
        transcript = Path(args.transcript)
    elif args.stdin_hook:
        transcript = _read_stdin_transcript_path()
    if transcript is None:
        transcript = find_current_transcript()

    if transcript is None or not transcript.is_file():
        print("Context: unavailable (no session transcript found)")
        return 1

    usage = last_usage(transcript)
    if usage is None:
        print(f"Context: unavailable (no usage block in {transcript.name})")
        return 1

    if args.report:
        records = _load_records(transcript)
        print(format_report(usage, args.limit, records))
    else:
        print(format_line(usage, args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
