"""Append structured events to the history.jsonl audit log.

Public API:
    append_event(history_path, event_dict)  -- appends one line to history.jsonl

CLI:
    python -m platforms.python.history_log <history_path> '<json>'
"""

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Optional, Union


def append_event(history_path: Union[str, pathlib.Path], event_dict: dict) -> None:
    """Append one event to the JSONL history file.

    Parameters
    ----------
    history_path : str or pathlib.Path
        Path to the history.jsonl file.  Parent directories are created if
        they do not exist.
    event_dict : dict
        The event to append.  A ``"timestamp"`` key (ISO-8601 UTC, e.g.
        ``"2026-06-10T14:00:00Z"``) is injected when absent; existing values
        are preserved verbatim.

    Notes
    -----
    Events are serialised with compact separators (``(",", ":")``) so that
    each line is grep-friendly, matching the existing history.jsonl style
    (e.g. ``{"event":"loop_complete","phase":"phase-10",...}``).

    The function is append-only: it never rewrites existing lines.
    """
    path = pathlib.Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    record = dict(event_dict)
    if "timestamp" not in record:
        record["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    line = json.dumps(record, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m platforms.python.history_log",
        description="Append a JSON event to a history.jsonl file.",
    )
    parser.add_argument("history_path", help="Path to the history.jsonl file.")
    parser.add_argument("event_json", help="JSON string representing the event.")
    return parser


def main(argv: Optional[list] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        event = json.loads(args.event_json)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 1
    append_event(args.history_path, event)
    return 0


if __name__ == "__main__":
    sys.exit(main())
