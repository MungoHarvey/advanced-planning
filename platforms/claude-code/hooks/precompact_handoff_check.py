#!/usr/bin/env python3
"""PreCompact hook: validate latest handoff.md and emit retention note.

Behaviour:
- Finds the most recently written .advanced-plans/phases/phase-*/handoff.md
- Validates it is within its declared token_ceiling
- Emits a short stderr note naming the digest + CLAUDE.md ## Compaction
  Instructions block as the retention target
- No-ops cleanly if no handoff.md exists (pre-first-gate / mid-phase)
- ALWAYS exits 0 -- never blocks compaction under any code path

stdlib only: json, pathlib, sys, re, os, datetime
"""

import json
import os
import pathlib
import re
import sys
import datetime


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #

def _find_latest_handoff(base: pathlib.Path) -> pathlib.Path | None:
    """Return the most recently modified handoff.md under base, or None."""
    candidates = list(base.glob("phases/phase-*/handoff.md"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter key:value pairs (simple scalar values only)."""
    fm: dict = {}
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return fm
    for line in match.group(1).splitlines():
        kv = re.match(r"^\s*(\w[\w_-]*):\s*(.*)\s*$", line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip()
    return fm


def _count_tokens_approx(text: str) -> int:
    """Approximate token count: words / 0.75 (rough 1 token ~ 0.75 words)."""
    words = len(text.split())
    return int(words / 0.75)


MANDATORY_SECTIONS = [
    "## What was done & why",
    "## Outcomes",
    "## Errors & issues encountered",
    "## Files touched",
    "## Gate review",
    "## Skills & methods used",
    "## Resume pointers",
]


def _validate_handoff(path: pathlib.Path) -> list[str]:
    """Return list of validation failures (empty = OK)."""
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"cannot read file: {exc}"]

    fm = _parse_frontmatter(text)

    # Check mandatory frontmatter keys
    for key in ("phase", "title", "status", "token_ceiling"):
        if key not in fm:
            issues.append(f"frontmatter missing: {key}")

    # Check token ceiling
    ceiling_raw = fm.get("token_ceiling", "")
    try:
        ceiling = int(ceiling_raw)
        approx = _count_tokens_approx(text)
        if approx > ceiling:
            issues.append(
                f"token ceiling exceeded: ~{approx} tokens vs ceiling {ceiling}"
            )
    except ValueError:
        issues.append(f"token_ceiling not an integer: {ceiling_raw!r}")

    # Check mandatory sections present
    for section in MANDATORY_SECTIONS:
        if section not in text:
            issues.append(f"missing section: {section}")

    return issues


# --------------------------------------------------------------------------- #
# Main                                                                          #
# --------------------------------------------------------------------------- #

def main() -> None:
    try:
        # Locate the advanced-plans base directory relative to CWD
        cwd = pathlib.Path(os.getcwd())
        base = cwd / ".advanced-plans"

        if not base.is_dir():
            # No .advanced-plans directory -- no-op
            sys.stderr.write(
                "[PreCompact] .advanced-plans not found; no handoff digest available.\n"
            )
            return

        handoff = _find_latest_handoff(base)

        if handoff is None:
            # Pre-first-gate or mid-phase: no-op, CLAUDE.md block steers retention
            sys.stderr.write(
                "[PreCompact] No handoff.md found (pre-gate / mid-phase). "
                "Retention steered by CLAUDE.md ## Compaction Instructions only.\n"
            )
            return

        # Validate the handoff
        issues = _validate_handoff(handoff)

        rel = handoff.relative_to(cwd)
        timestamp = datetime.datetime.fromtimestamp(
            handoff.stat().st_mtime
        ).strftime("%Y-%m-%d %H:%M")

        if issues:
            warn_lines = "\n  ".join(issues)
            sys.stderr.write(
                f"[PreCompact] WARNING: {rel} has validation issues:\n"
                f"  {warn_lines}\n"
                f"  Retention note: keep '{rel}' and CLAUDE.md ## Compaction "
                f"Instructions as retention targets (issues noted above).\n"
            )
        else:
            sys.stderr.write(
                f"[PreCompact] Retention targets for this compaction:\n"
                f"  1. {rel} (validated phase resume digest, {timestamp})\n"
                f"  2. CLAUDE.md ## Compaction Instructions (persistent policy)\n"
                f"  The digest is current and within its token ceiling.\n"
            )

    except Exception as exc:
        # Safety net: hook MUST NOT block compaction under any circumstances
        sys.stderr.write(
            f"[PreCompact] Internal error (non-blocking): {exc}\n"
            f"  Compaction proceeds without hook validation.\n"
        )
    # Always return cleanly -- sys.exit(0) is implicit


if __name__ == "__main__":
    main()
