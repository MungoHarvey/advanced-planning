"""
handoff.py — Handoff injection for the planning system
=======================================================

Reads a prior loop's ``handoff_summary`` and injects the three fields
(``done``, ``failed``, ``needed``) into a prompt template string.

Template placeholders use the format::

    [inject prior.handoff_summary.done]
    [inject prior.handoff_summary.failed]
    [inject prior.handoff_summary.needed]

This is the canonical placeholder syntax used across all loop plan files,
orchestrator prompts, and worker prompts in the planning system.

Typical usage::

    from platforms.python.handoff import read_handoff, inject_handoff
    from platforms.python.plan_io import get_loop_handoff

    # Read handoff from plan file
    handoff = get_loop_handoff("plans/phase-1-ralph-loops.md", "ralph-loop-001")

    # Or read from loop-complete.json via state_manager
    from platforms.python.state_manager import read_loop_complete
    complete = read_loop_complete("state")
    handoff = complete["handoff"] if complete else {"done": "", "failed": "", "needed": ""}

    # Inject into a prompt template
    prompt = inject_handoff(template_string, handoff)
"""

import re
from pathlib import Path
from typing import Optional

# ── Placeholder patterns ───────────────────────────────────────────────────────

_PLACEHOLDER_MAP = {
    "[inject prior.handoff_summary.done]": "done",
    "[inject prior.handoff_summary.failed]": "failed",
    "[inject prior.handoff_summary.needed]": "needed",
}


# ── Public API ─────────────────────────────────────────────────────────────────

def make_empty_handoff() -> dict[str, str]:
    """Return an empty handoff dict suitable for the first loop in a programme."""
    return {"done": "", "failed": "", "needed": ""}


def read_handoff(loop_complete_path: Path | str) -> dict[str, str]:
    """Read the handoff block from a ``loop-complete.json`` file.

    Parameters
    ----------
    loop_complete_path:
        Path to a ``loop-complete.json`` file.

    Returns
    -------
    dict with keys ``done``, ``failed``, ``needed``.
    Raises FileNotFoundError if the file does not exist.
    Raises KeyError if the ``handoff`` block is missing.
    """
    import json
    content = Path(loop_complete_path).read_text(encoding="utf-8")
    data = json.loads(content)
    return {
        "done": data["handoff"].get("done", ""),
        "failed": data["handoff"].get("failed", ""),
        "needed": data["handoff"].get("needed", ""),
    }


def inject_handoff(template: str, handoff: dict[str, str]) -> str:
    """Replace handoff placeholders in a template string with actual values.

    Placeholders replaced:

    - ``[inject prior.handoff_summary.done]`` → ``handoff["done"]``
    - ``[inject prior.handoff_summary.failed]`` → ``handoff["failed"]``
    - ``[inject prior.handoff_summary.needed]`` → ``handoff["needed"]``

    Parameters
    ----------
    template:
        A string (typically a prompt) containing zero or more placeholders.
    handoff:
        Dict with keys ``done``, ``failed``, ``needed``.

    Returns
    -------
    str
        The template with all placeholders replaced.
    """
    result = template
    for placeholder, key in _PLACEHOLDER_MAP.items():
        result = result.replace(placeholder, handoff.get(key, ""))
    return result


def inject_handoff_from_file(template: str, loop_complete_path: Path | str) -> str:
    """Convenience wrapper: read handoff from file and inject into template.

    Parameters
    ----------
    template:
        A string containing zero or more handoff placeholders.
    loop_complete_path:
        Path to ``loop-complete.json``.

    Returns
    -------
    str
        The template with all placeholders replaced.
    Raises FileNotFoundError if loop-complete.json does not exist.
    """
    handoff = read_handoff(loop_complete_path)
    return inject_handoff(template, handoff)


def build_context_block(handoff: dict[str, str], prefix: str = "## Context from prior loop") -> str:
    """Build a formatted context block from a handoff dict.

    Produces the standard three-line context section used in loop prompts::

        ## Context from prior loop
        Done: [value]
        Failed: [value]
        Needed: [value]

    Parameters
    ----------
    handoff:
        Dict with keys ``done``, ``failed``, ``needed``.
    prefix:
        The heading line (default: ``## Context from prior loop``).

    Returns
    -------
    str
        Multi-line context block ready to prepend to a prompt.
    """
    return (
        f"{prefix}\n"
        f"Done: {handoff.get('done', '')}\n"
        f"Failed: {handoff.get('failed', '')}\n"
        f"Needed: {handoff.get('needed', '')}\n"
    )
