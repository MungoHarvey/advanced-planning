"""Measure live conversation-context occupancy from a Claude Code session transcript.

Zero-dependency (standard library only) to honour the project CI invariant.

The Claude Code transcript is a JSONL file where each assistant message records the
API's real ``usage`` block. The effective context occupancy for a turn is::

    input_tokens + cache_read_input_tokens + cache_creation_input_tokens

This is the same figure ``/usage`` surfaces in the terminal, but read from the
transcript so it can be emitted into a command's output and seen by the agent
inline. Intended to be invoked once at phase end (e.g. by ``/phase-compact``),
not every turn.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


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


def last_usage(transcript: Path) -> Optional[dict]:
    """Return the ``usage`` block of the most recent assistant message, or None."""
    found = None
    with transcript.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
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


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Report live context occupancy.")
    parser.add_argument("transcript", nargs="?", help="Path to session .jsonl")
    parser.add_argument("--limit", type=int, default=200_000,
                        help="Context window limit in tokens (default 200000)")
    parser.add_argument("--stdin-hook", action="store_true",
                        help="Read transcript_path from a hook JSON payload on stdin")
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

    print(format_line(usage, args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
