"""handoff_digest.py -- Phase handoff digest generator.

Produces a schema-conforming ``.advanced-plans/phases/phase-N/handoff.md``
resume seed for use by ``/phase-compact``.

Decision: generation logic lives in this zero-dependency helper module (not
command-embedded) so it is independently testable via pytest. The
``/phase-compact`` command calls ``generate_handoff_digest()`` and handles
the SystemExit raised on ceiling violation.

Token estimation: ``ceil(len(rendered_text) / 4)`` (characters / 4).

Zero-dependency: standard library only (json, pathlib, sys, argparse, typing,
re, os, datetime, textwrap). CI AST import checker enforces this.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_TOKEN_CEILING = 1500
MAX_TOKEN_CEILING = 2000

REQUIRED_SECTIONS = [
    "What was done & why",
    "Outcomes",
    "Errors & issues encountered",
    "Files touched (pointers, not contents)",
    "Gate review",
    "Skills & methods used",
    "Resume pointers",
]


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Estimate token count as ceil(len(text) / 4).

    Avoids importing math to stay CI-clean (stdlib-only list does not include math).
    """
    n = len(text)
    return (n + 3) // 4  # integer ceiling without math.ceil


def ascii_safe(text: str) -> str:
    """Replace common non-ASCII punctuation with ASCII equivalents.

    Required for Windows cp1252 safety (no em-dashes, no Unicode arrows,
    no curly quotes). Any remaining non-ASCII is replaced with '?'.
    """
    replacements = [
        ("—", "--"),   # em-dash
        ("–", "-"),    # en-dash
        ("‒", "-"),    # figure dash
        ("‐", "-"),    # hyphen
        ("→", "->"),   # rightwards arrow
        ("←", "<-"),   # leftwards arrow
        ("’", "'"),    # right single quotation mark
        ("‘", "'"),    # left single quotation mark
        ("“", '"'),    # left double quotation mark
        ("”", '"'),    # right double quotation mark
        ("…", "..."),  # horizontal ellipsis
        (" ", " "),    # non-breaking space
    ]
    for src, dst in replacements:
        text = text.replace(src, dst)
    # Replace any remaining non-ASCII with '?'
    return text.encode("ascii", errors="replace").decode("ascii")


# ---------------------------------------------------------------------------
# Ceiling enforcement
# ---------------------------------------------------------------------------

def check_ceiling(rendered: str, ceiling: int) -> list[str]:
    """Return list of offending-section descriptions if ceiling exceeded.

    Returns an empty list when within ceiling.

    Each section is checked individually so the caller can report which
    sections are over-contributing to context bloat.
    """
    total = estimate_tokens(rendered)
    if total <= ceiling:
        return []

    # Break down by section to report offenders
    offenders: list[str] = []
    offenders.append(
        f"TOTAL: ~{total} tokens exceeds ceiling of {ceiling}"
    )

    # Split rendered text at ## headings to assess per-section contribution
    parts = re.split(r"(\n## .+)", rendered)
    current_section = "frontmatter"
    accumulated = ""
    for part in parts:
        if part.startswith("\n## "):
            if accumulated:
                tok = estimate_tokens(accumulated)
                # Flag sections that individually use more than 20% of ceiling
                threshold = max(50, ceiling // 5)
                if tok > threshold:
                    offenders.append(f"  {current_section}: ~{tok} tokens")
            current_section = part.strip().lstrip("# ").strip()
            accumulated = part
        else:
            accumulated += part
    # last section
    if accumulated:
        tok = estimate_tokens(accumulated)
        threshold = max(50, ceiling // 5)
        if tok > threshold:
            offenders.append(f"  {current_section}: ~{tok} tokens")

    return offenders


def enforce_ceiling(rendered: str, ceiling: int) -> None:
    """Raise SystemExit with offending-section report if ceiling exceeded."""
    offenders = check_ceiling(rendered, ceiling)
    if offenders:
        msg = (
            "ERROR: handoff digest exceeds token_ceiling={}\n".format(ceiling)
            + "Offending sections (tighten bullets until digest fits):\n"
            + "\n".join(offenders)
        )
        sys.exit(msg)


# ---------------------------------------------------------------------------
# YAML frontmatter parsing helpers (no external deps)
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> dict:
    """Extract YAML-like frontmatter as a flat dict of string values.

    Only handles simple key: value and list (dash items) syntax needed
    for plan.md / complete.md / verdict JSON structures. Not a full YAML
    parser -- only used for reading framework artefacts.
    """
    result: dict = {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return result
    in_fm = False
    current_key: Optional[str] = None
    list_values: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            if in_fm:
                break
            in_fm = True
            continue
        if not in_fm:
            in_fm = True
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") and current_key:
            list_values.append(stripped[2:].strip())
            result[current_key] = list_values[:]
        elif ":" in stripped and not stripped.startswith("-"):
            if current_key and list_values:
                result[current_key] = list_values[:]
            list_values = []
            key, _, value = stripped.partition(":")
            current_key = key.strip()
            value = value.strip()
            if value:
                result[current_key] = value
            else:
                result[current_key] = ""
    if current_key and list_values:
        result[current_key] = list_values
    return result


def _body_sections(text: str) -> dict[str, str]:
    """Return dict mapping section heading to section body."""
    sections: dict[str, str] = {}
    # Skip frontmatter
    body_start = 0
    lines = text.splitlines(keepends=True)
    in_fm = False
    fm_count = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            fm_count += 1
            if fm_count == 2:
                body_start = i + 1
                break

    current_heading: Optional[str] = None
    current_body: list[str] = []
    for line in lines[body_start:]:
        m = re.match(r"^(#{1,3})\s+(.+)", line)
        if m:
            if current_heading is not None:
                sections[current_heading] = "".join(current_body).strip()
            current_heading = m.group(2).strip()
            current_body = []
        else:
            if current_heading is not None:
                current_body.append(line)
    if current_heading is not None:
        sections[current_heading] = "".join(current_body).strip()
    return sections


# ---------------------------------------------------------------------------
# Gate verdict parsing
# ---------------------------------------------------------------------------

def _load_verdict(path: Path) -> dict:
    """Load a gate-verdict JSON file. Returns empty dict on error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _verdict_summary(verdict: dict) -> str:
    """Produce a one-paragraph gate review summary from a verdict dict."""
    phase = verdict.get("phase", "unknown")
    attempt = verdict.get("attempt", "?")
    v = verdict.get("verdict", "unknown")
    confidence = verdict.get("confidence", "?")
    findings = verdict.get("findings", [])
    failure_notes = verdict.get("failure_notes", [])

    important = [f for f in findings if f.get("severity") == "important"]
    errors = failure_notes if failure_notes else []

    parts = [
        f"Attempt {attempt} {v}",
    ]
    if confidence != "?":
        parts.append(f"at confidence {confidence}")
    parts.append(".")

    if errors:
        note = errors[0] if isinstance(errors[0], str) else str(errors[0])
        parts.append(f" Issues: {note[:120]}.")
    elif important:
        note = important[0].get("description", "")[:120]
        parts.append(f" Note: {note}.")

    return " ".join(parts).replace("  ", " ")


# ---------------------------------------------------------------------------
# Digest generation
# ---------------------------------------------------------------------------

def generate_handoff_digest(
    phase_dir: Path | str,
    output_path: Optional[Path | str] = None,
    token_ceiling: int = DEFAULT_TOKEN_CEILING,
    gate_verdict: str = "passed",
    gate_attempt: int = 1,
    dry_run: bool = False,
) -> str:
    """Generate a schema-conforming phase handoff digest.

    Parameters
    ----------
    phase_dir:
        Path to ``.advanced-plans/phases/phase-N/`` containing plan.md,
        complete.md, and loops.md.
    output_path:
        Where to write ``handoff.md``. Defaults to ``phase_dir/handoff.md``.
        If ``dry_run`` is True the file is NOT written regardless.
    token_ceiling:
        Maximum estimated tokens. Generation fails (SystemExit) if exceeded.
    gate_verdict:
        ``"passed"`` or ``"failed_vM"`` -- drives ``status`` field and
        Errors & issues section handling.
    gate_attempt:
        Attempt number for gate verdicts. Used to locate verdict files when
        not supplied via ``gate_verdict_refs`` in complete.md frontmatter.
    dry_run:
        If True, validate but do not write the output file.

    Returns
    -------
    str
        The rendered digest text.

    Raises
    ------
    SystemExit
        If the rendered digest exceeds ``token_ceiling`` (lists offenders).
    FileNotFoundError
        If required input files are missing.
    """
    phase_dir = Path(phase_dir)
    if output_path is None:
        output_path = phase_dir / "handoff.md"
    else:
        output_path = Path(output_path)

    # ------------------------------------------------------------------
    # 1. Read inputs
    # ------------------------------------------------------------------
    plan_path = phase_dir / "plan.md"
    complete_path = phase_dir / "complete.md"
    loops_path = phase_dir / "loops.md"

    if not plan_path.exists():
        raise FileNotFoundError(f"plan.md not found: {plan_path}")
    if not complete_path.exists():
        raise FileNotFoundError(f"complete.md not found: {complete_path}")

    plan_text = plan_path.read_text(encoding="utf-8")
    complete_text = complete_path.read_text(encoding="utf-8")

    plan_fm = _parse_frontmatter(plan_text)
    complete_fm = _parse_frontmatter(complete_text)
    complete_sections = _body_sections(complete_text)

    # Derive phase number
    phase_num_raw = complete_fm.get("phase") or plan_fm.get("phase") or "?"
    try:
        phase_num = int(str(phase_num_raw).strip('"').strip("'"))
    except (ValueError, TypeError):
        phase_num = phase_num_raw

    # Phase title
    title_raw = (
        complete_fm.get("title")
        or plan_fm.get("name")
        or plan_fm.get("title")
        or "Unknown Phase"
    )
    title = str(title_raw).strip('"').strip("'")

    # Status
    if str(gate_verdict).startswith("failed"):
        status = gate_verdict if gate_verdict.startswith("failed_v") else f"failed_v{gate_attempt}"
    else:
        status = "passed"

    # Paths (relative to repo root -- we record them as-is; caller ensures correctness)
    # Detect repo root: walk up from phase_dir looking for .git
    repo_root = phase_dir
    for _ in range(10):
        if (repo_root / ".git").exists():
            break
        repo_root = repo_root.parent

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(repo_root)).replace("\\", "/")
        except ValueError:
            return str(p).replace("\\", "/")

    complete_ref = _rel(complete_path)
    plan_ref = _rel(plan_path)
    loops_ref = _rel(loops_path) if loops_path.exists() else _rel(phase_dir / "loops.md")

    # Gate verdict refs -- discover from gate-verdicts/ directory
    gate_verdicts_dir = repo_root / ".advanced-plans" / "gate-verdicts"
    phase_label = f"phase-{phase_num}"
    verdict_files: list[Path] = []
    if gate_verdicts_dir.is_dir():
        verdict_files = sorted(
            gate_verdicts_dir.glob(f"{phase_label}-attempt-*-phase-goals-agent.json")
        )
    # Also include code-review-agent verdicts
    if gate_verdicts_dir.is_dir():
        cr_files = sorted(
            gate_verdicts_dir.glob(f"{phase_label}-attempt-*-code-review-agent.json")
        )
        verdict_files = sorted(
            set(verdict_files) | set(cr_files),
            key=lambda p: p.name,
        )
    gate_verdict_refs = [_rel(v) for v in verdict_files]
    if not gate_verdict_refs:
        gate_verdict_refs = [f".advanced-plans/gate-verdicts/{phase_label}-attempt-1-phase-goals-agent.json"]

    # Load the most recent phase-goals verdict for summary
    pg_verdicts = sorted(
        gate_verdicts_dir.glob(f"{phase_label}-attempt-*-phase-goals-agent.json")
    ) if gate_verdicts_dir.is_dir() else []
    latest_verdict_data: dict = {}
    if pg_verdicts:
        latest_verdict_data = _load_verdict(pg_verdicts[-1])
        latest_verdict_ref = _rel(pg_verdicts[-1])
    else:
        latest_verdict_ref = gate_verdict_refs[-1] if gate_verdict_refs else ""

    # ------------------------------------------------------------------
    # 2. Build section content from complete.md
    # ------------------------------------------------------------------
    goals_met = complete_sections.get("Goals met", "- (see complete.md)")
    deferred = complete_sections.get("Deferred", "- (see complete.md)")
    opened = complete_sections.get("Opened", "- (see complete.md)")

    # What was done & why -- derive from goals met (compact to one-liners)
    done_bullets = _compact_bullets(goals_met, prefix="- ")

    # Outcomes -- derive from goals met as observable end-states
    outcome_bullets = _compact_bullets(goals_met, prefix="- ")

    # Errors & issues -- mandatory
    if status.startswith("failed"):
        # Gate-fail: populate from failure_notes in the latest verdict
        failure_notes = latest_verdict_data.get("failure_notes", [])
        loops_to_revert = latest_verdict_data.get("loops_to_revert", [])
        if failure_notes or loops_to_revert:
            issue_lines = []
            for note in failure_notes[:3]:
                if isinstance(note, str):
                    issue_lines.append(f"- {note[:150]}")
                elif isinstance(note, dict):
                    issue_lines.append(f"- {str(note)[:150]}")
            for loop in loops_to_revert[:2]:
                issue_lines.append(f"- Loop {loop} flagged for revert")
            issues_content = "\n".join(issue_lines) if issue_lines else "- Gate failed; see verdict for details"
        else:
            issues_content = "- Gate failed; see verdict for details"
    else:
        # Pass: check opened section for real issues; otherwise none
        if opened and opened != "- (none)" and opened != "- (see complete.md)":
            # Opened items are observations, not errors -- be precise
            issue_lines = ["- (none — gate passed; see ## Opened in complete.md for observations)"]
            # But if complete.md Opened has real content, surface first item
            first_opened = [l.strip() for l in opened.splitlines() if l.strip().startswith("-")]
            if first_opened and first_opened[0] != "- (none)":
                issue_lines = [first_opened[0][:160]]
                if len(first_opened) > 1:
                    issue_lines.append(f"- (+{len(first_opened)-1} more observations -- see complete.md ## Opened)")
        else:
            issue_lines = ["- (none)"]
        issues_content = "\n".join(issue_lines)

    # Files touched -- generic pointers from plan deliverables
    deliverables = _extract_deliverables(plan_text)
    files_content = deliverables if deliverables else "- (see complete.md and git log)"

    # Gate review paragraph
    if latest_verdict_data:
        gate_summary = _verdict_summary(latest_verdict_data)
        gate_content = f"{gate_summary} -> full verdict: {latest_verdict_ref}"
    else:
        gate_content = f"Gate verdict: {status}. -> full verdict: {latest_verdict_ref}"

    # Skills & methods -- extract from plan Skills Required section
    skills_content = _extract_skills(plan_text)
    if not skills_content:
        skills_content = "- (see plan.md ## Skills Required)"

    # Resume pointers
    # Find most recent spec referenced in plan
    spec_ref = _extract_spec_ref(plan_text, repo_root)
    next_action = _derive_next_action(deferred, opened, status, phase_num)
    resume_content = (
        f"- Plans: {plan_ref} / {loops_ref}"
        f" - Spec: {spec_ref}"
        f" - Next: {next_action}"
    )

    # ------------------------------------------------------------------
    # 3. Render gate_verdict_refs as YAML list
    # ------------------------------------------------------------------
    if len(gate_verdict_refs) == 1:
        gvr_yaml = f"  - {gate_verdict_refs[0]}"
    else:
        gvr_yaml = "\n".join(f"  - {r}" for r in gate_verdict_refs)

    # ------------------------------------------------------------------
    # 4. Assemble digest
    # ------------------------------------------------------------------
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    digest = (
        f"---\n"
        f"phase: {phase_num}\n"
        f"title: \"{title}\"\n"
        f"status: {status}\n"
        f"created: {now_iso}\n"
        f"complete_ref: {complete_ref}\n"
        f"plan_ref: {plan_ref}\n"
        f"loops_ref: {loops_ref}\n"
        f"gate_verdict_refs:\n{gvr_yaml}\n"
        f"token_ceiling: {token_ceiling}\n"
        f"---\n"
        f"\n"
        f"## What was done & why\n"
        f"{done_bullets}\n"
        f"\n"
        f"## Outcomes\n"
        f"{outcome_bullets}\n"
        f"\n"
        f"## Errors & issues encountered\n"
        f"{issues_content}\n"
        f"\n"
        f"## Files touched (pointers, not contents)\n"
        f"{files_content}\n"
        f"\n"
        f"## Gate review\n"
        f"{gate_content}\n"
        f"\n"
        f"## Skills & methods used\n"
        f"{skills_content}\n"
        f"\n"
        f"## Resume pointers\n"
        f"{resume_content}\n"
    )

    # ------------------------------------------------------------------
    # 5. ASCII sanitize then enforce ceiling
    # ------------------------------------------------------------------
    digest = ascii_safe(digest)
    enforce_ceiling(digest, token_ceiling)

    # ------------------------------------------------------------------
    # 6. Write output
    # ------------------------------------------------------------------
    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(digest, encoding="utf-8")

    return digest


# ---------------------------------------------------------------------------
# Section extraction helpers
# ---------------------------------------------------------------------------

def _compact_bullets(section_text: str, prefix: str = "- ", max_len: int = 160) -> str:
    """Return section_text with each bullet capped at max_len chars."""
    lines = section_text.splitlines()
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("-"):
            if len(stripped) > max_len:
                stripped = stripped[:max_len - 3] + "..."
            result.append(stripped)
        elif stripped:
            # Non-bullet line -- treat as continuation; skip (pointers only)
            pass
    return "\n".join(result) if result else "- (see complete.md)"


def _extract_deliverables(plan_text: str) -> str:
    """Extract Key Deliverables table entries as pointer lines."""
    lines: list[str] = []
    in_table = False
    in_deliverables = False
    for line in plan_text.splitlines():
        stripped = line.strip()
        if re.match(r"^##\s+Key Deliverables", stripped):
            in_deliverables = True
            continue
        if in_deliverables and re.match(r"^##\s+", stripped):
            break
        if in_deliverables and stripped.startswith("|") and not stripped.startswith("| ---"):
            cols = [c.strip() for c in stripped.split("|") if c.strip()]
            if len(cols) >= 2 and cols[0].lower() not in ("deliverable", "---"):
                # cols[0]=name, cols[2]=location
                location = cols[2] if len(cols) >= 3 else ""
                name = cols[0]
                if location and location.lower() not in ("location", "---"):
                    lines.append(f"- edited: `{location}` -- {name}")
    return "\n".join(lines[:10]) if lines else ""


def _extract_skills(plan_text: str) -> str:
    """Extract skills list from plan.md ## Skills Required section."""
    lines: list[str] = []
    in_skills = False
    for line in plan_text.splitlines():
        stripped = line.strip()
        if re.match(r"^##\s+Skills Required", stripped, re.IGNORECASE):
            in_skills = True
            continue
        if in_skills and re.match(r"^##\s+", stripped):
            break
        if in_skills and stripped.startswith("-"):
            # Format: - `skill-name`: description
            m = re.match(r"-\s+`?([^`:]+)`?[:\s]+(.*)", stripped)
            if m:
                skill_name = m.group(1).strip()
                desc = m.group(2).strip()[:80]
                lines.append(f"- `{skill_name}` -- {desc}")
            else:
                lines.append(stripped[:120])
    return "\n".join(lines) if lines else ""


def _extract_spec_ref(plan_text: str, repo_root: Path) -> str:
    """Extract design_spec from plan frontmatter, normalise to .advanced-plans/ path."""
    fm = _parse_frontmatter(plan_text)
    spec = fm.get("design_spec", "")
    if not spec:
        # Try to find any spec in .advanced-plans/specs/
        specs_dir = repo_root / ".advanced-plans" / "specs"
        if specs_dir.is_dir():
            candidates = sorted(specs_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            if candidates:
                try:
                    return str(candidates[0].relative_to(repo_root)).replace("\\", "/")
                except ValueError:
                    return str(candidates[0]).replace("\\", "/")
        return "(no spec found)"
    # Normalise: old plans/ prefix -> .advanced-plans/specs/
    spec = spec.strip()
    if spec.startswith("plans/"):
        basename = Path(spec).name
        return f".advanced-plans/specs/{basename}"
    return spec


def _derive_next_action(deferred: str, opened: str, status: str, phase_num) -> str:
    """Derive a one-line next-action hint."""
    if status.startswith("failed"):
        return f"Fix gate failures then re-run /run-gate for phase-{phase_num}"
    # Check deferred for a target
    for line in deferred.splitlines():
        m = re.search(r"phase-(\d+)", line)
        if m:
            return f"Start phase-{m.group(1)}"
    return f"Start phase-{int(str(phase_num)) + 1}"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI: generate a phase handoff digest.

    Usage::

        python handoff_digest.py .advanced-plans/phases/phase-9 [--output PATH]
                                  [--ceiling 1500] [--gate-verdict passed]
                                  [--dry-run]
    """
    parser = argparse.ArgumentParser(
        description="Generate a phase handoff digest (phase-handoff.schema.md)."
    )
    parser.add_argument("phase_dir", help="Path to the phase directory (plan.md must exist).")
    parser.add_argument("--output", default=None, help="Output path for handoff.md (default: phase_dir/handoff.md).")
    parser.add_argument("--ceiling", type=int, default=DEFAULT_TOKEN_CEILING,
                        help=f"Token ceiling (default: {DEFAULT_TOKEN_CEILING}).")
    parser.add_argument("--gate-verdict", default="passed",
                        help="Gate verdict: 'passed' or 'failed_vM' (default: passed).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate and print digest but do not write file.")
    args = parser.parse_args()

    digest = generate_handoff_digest(
        phase_dir=args.phase_dir,
        output_path=args.output,
        token_ceiling=args.ceiling,
        gate_verdict=args.gate_verdict,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print(digest)
        tok = estimate_tokens(digest)
        print(f"\n[dry-run] Estimated tokens: ~{tok} / {args.ceiling}")


if __name__ == "__main__":
    main()
