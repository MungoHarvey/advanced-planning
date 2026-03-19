"""
plan_io.py — Plan file reading and writing for the planning system
==================================================================

Provides functions to locate, parse, and update loop plan files.
Loop plans are Markdown files with YAML frontmatter blocks containing
``todos[]`` arrays, ``handoff_summary``, and loop metadata.

The YAML frontmatter is delimited by triple-backtick yaml fences (not ---),
matching the format used throughout the planning system's plan files.

Typical usage::

    from pathlib import Path
    from platforms.python.plan_io import find_next_loop, get_pending_todos, update_todo_status

    plans_dir = Path("plans")
    loop_info = find_next_loop(plans_dir)
    if loop_info:
        todos = get_pending_todos(loop_info["file"], loop_info["loop_name"])
        update_todo_status(loop_info["file"], loop_info["loop_name"], "loop-001-1", "completed")
"""

import re
from pathlib import Path
from typing import Any, Optional

# ── YAML frontmatter parsing ───────────────────────────────────────────────────
# The plan files use ```yaml ... ``` fences inside Markdown ## sections,
# NOT the standard --- ... --- YAML front matter convention.
# Each ralph loop appears as a ## section with a ```yaml block.

_LOOP_BLOCK_RE = re.compile(
    r"##\s+(?P<heading>[^\n]+)\n+```yaml\n(?P<yaml_block>.*?)```",
    re.DOTALL,
)
_LOOP_NAME_RE = re.compile(r'^name:\s*"?(?P<name>[^"\n]+)"?', re.MULTILINE)
_FIELD_RE = re.compile(r'^(?P<key>\w[\w_]*):\s*(?P<value>.+)$', re.MULTILINE)


def _parse_simple_yaml_block(yaml_text: str) -> dict[str, Any]:
    """Parse a simplified YAML block into a dict.

    Handles scalar fields, quoted strings, and the ``todos[]`` array.
    Does not handle nested dicts beyond ``handoff_summary`` and todo items.
    """
    result: dict[str, Any] = {}
    lines = yaml_text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip blank lines and comments
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue

        # Detect todos: list start
        if re.match(r"^todos:\s*$", line):
            todos, i = _parse_todos(lines, i + 1)
            result["todos"] = todos
            continue

        # Detect handoff_summary block
        if re.match(r"^handoff_summary:\s*$", line):
            hs, i = _parse_handoff_summary(lines, i + 1)
            result["handoff_summary"] = hs
            continue

        # Scalar field
        m = re.match(r'^(\w[\w_]*):\s*"?([^"#\n]*)"?\s*$', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            # Attempt int coercion
            try:
                result[key] = int(val)
            except ValueError:
                result[key] = val
        i += 1

    return result


def _parse_handoff_summary(lines: list[str], start: int) -> tuple[dict[str, str], int]:
    """Parse a ``handoff_summary:`` block from indented lines. Returns (dict, next_index)."""
    result: dict[str, str] = {}
    i = start
    while i < len(lines):
        line = lines[i]
        if line and not line.startswith(" ") and not line.startswith("\t"):
            break
        m = re.match(r'^\s+(done|failed|needed):\s*"?(.*?)"?\s*$', line)
        if m:
            result[m.group(1)] = m.group(2)
        i += 1
    return result, i


def _parse_todos(lines: list[str], start: int) -> tuple[list[dict[str, Any]], int]:
    """Parse a ``todos:`` list block. Returns (list_of_todos, next_index)."""
    todos: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    i = start

    while i < len(lines):
        line = lines[i]

        # Empty line or non-indented non-list line = end of todos block
        if line and not line.startswith(" ") and not line.startswith("\t") and not line.strip().startswith("-"):
            break

        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        # New todo item
        if stripped.startswith("- id:"):
            if current:
                todos.append(current)
            current = {}
            m = re.match(r'-\s+id:\s*"?([^"]+)"?', stripped)
            if m:
                current["id"] = m.group(1)

        # Other fields within a todo item
        elif stripped and not stripped.startswith("-"):
            m = re.match(r'(\w[\w_]*):\s*"?(.*?)"?\s*$', stripped)
            if m and current is not None:
                key, val = m.group(1), m.group(2)
                current[key] = val

        i += 1

    if current:
        todos.append(current)

    return todos, i


# ── Public API ─────────────────────────────────────────────────────────────────

def parse_loop_frontmatter(loop_file: Path | str, loop_name: str) -> Optional[dict[str, Any]]:
    """Parse the YAML frontmatter block for a named loop within a plan file.

    Parameters
    ----------
    loop_file:
        Path to the Markdown plan file containing the loop.
    loop_name:
        The ``name:`` field value to locate, e.g. ``"ralph-loop-001"``.

    Returns
    -------
    dict or None
        Parsed frontmatter as a dict, or None if the loop was not found.
    """
    content = Path(loop_file).read_text(encoding="utf-8")
    for m in _LOOP_BLOCK_RE.finditer(content):
        yaml_block = m.group("yaml_block")
        name_match = _LOOP_NAME_RE.search(yaml_block)
        if name_match and name_match.group("name").strip() == loop_name:
            return _parse_simple_yaml_block(yaml_block)
    return None


def get_pending_todos(loop_file: Path | str, loop_name: str) -> list[dict[str, Any]]:
    """Return all todos with ``status: pending`` for the named loop.

    Parameters
    ----------
    loop_file:
        Path to the Markdown plan file.
    loop_name:
        Loop name to extract todos from.

    Returns
    -------
    list of dict
        Todos in declaration order, filtered to status == "pending".
        Returns empty list if loop not found.
    """
    frontmatter = parse_loop_frontmatter(loop_file, loop_name)
    if not frontmatter:
        return []
    return [t for t in frontmatter.get("todos", []) if t.get("status") == "pending"]


def get_all_todos(loop_file: Path | str, loop_name: str) -> list[dict[str, Any]]:
    """Return all todos for the named loop, regardless of status."""
    frontmatter = parse_loop_frontmatter(loop_file, loop_name)
    if not frontmatter:
        return []
    return frontmatter.get("todos", [])


def update_todo_status(
    loop_file: Path | str, loop_name: str, todo_id: str, new_status: str
) -> bool:
    """Update the ``status:`` field of a specific todo in-place within the plan file.

    Parameters
    ----------
    loop_file:
        Path to the Markdown plan file.
    loop_name:
        Loop name containing the todo.
    todo_id:
        The ``id:`` field value of the todo to update.
    new_status:
        New status value, e.g. ``"in_progress"``, ``"completed"``, ``"cancelled"``.

    Returns
    -------
    bool
        True if the update was made; False if the todo was not found.
    """
    valid_statuses = {"pending", "in_progress", "completed", "cancelled"}
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status {new_status!r}; expected one of {valid_statuses}")

    path = Path(loop_file)
    content = path.read_text(encoding="utf-8")

    # Locate the specific todo block by id and replace its status line
    # Pattern: find the id line, then find the status: line before the next id/section
    id_pattern = re.compile(
        rf'(- id:\s*"?{re.escape(todo_id)}"?.*?status:\s*)(\w+)',
        re.DOTALL,
    )
    new_content, count = id_pattern.subn(rf'\g<1>{new_status}', content, count=1)

    if count == 0:
        return False

    path.write_text(new_content, encoding="utf-8")
    return True


def find_next_loop(plans_dir: Path | str) -> Optional[dict[str, Any]]:
    """Scan plan files and return metadata for the first loop with pending todos.

    Searches all ``*.md`` files in ``plans_dir`` in alphabetical order.
    Within each file, inspects loops in document order.

    Parameters
    ----------
    plans_dir:
        Directory containing plan Markdown files.

    Returns
    -------
    dict or None
        A dict with keys ``loop_name``, ``loop_file``, ``task_name``,
        ``todos_count``, and ``frontmatter`` — or None if no pending loops exist.
    """
    plans_path = Path(plans_dir)
    for plan_file in sorted(plans_path.glob("*.md")):
        content = plan_file.read_text(encoding="utf-8")
        for m in _LOOP_BLOCK_RE.finditer(content):
            yaml_block = m.group("yaml_block")
            name_match = _LOOP_NAME_RE.search(yaml_block)
            if not name_match:
                continue
            loop_name = name_match.group("name").strip()
            frontmatter = _parse_simple_yaml_block(yaml_block)
            pending = [t for t in frontmatter.get("todos", []) if t.get("status") == "pending"]
            if pending:
                return {
                    "loop_name": loop_name,
                    "loop_file": str(plan_file),
                    "task_name": frontmatter.get("task_name", ""),
                    "todos_count": len(pending),
                    "frontmatter": frontmatter,
                }
    return None


def get_loop_handoff(loop_file: Path | str, loop_name: str) -> dict[str, str]:
    """Return the ``handoff_summary`` dict for a named loop.

    Returns ``{"done": "", "failed": "", "needed": ""}`` if not found.
    """
    frontmatter = parse_loop_frontmatter(loop_file, loop_name)
    empty: dict[str, str] = {"done": "", "failed": "", "needed": ""}
    if not frontmatter:
        return empty
    return frontmatter.get("handoff_summary", empty)
