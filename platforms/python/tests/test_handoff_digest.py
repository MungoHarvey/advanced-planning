"""Unit tests for platforms.python.handoff_digest.

Tests cover:
- Basic generation produces schema-conforming output
- Token ceiling enforcement: over-ceiling fails with offending sections listed
- Gate-fail path: status: failed_vM with non-empty Errors & issues section
- ascii_safe removes non-ASCII characters
- estimate_tokens is ceil(len/4)
- check_ceiling returns empty list when within ceiling

Uses phase-9 as the canonical fixture via tmp_path copies.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3]))

from platforms.python.handoff_digest import (
    ascii_safe,
    check_ceiling,
    enforce_ceiling,
    estimate_tokens,
    generate_handoff_digest,
    _compact_bullets,
    _parse_frontmatter,
    _body_sections,
)


# ---------------------------------------------------------------------------
# Repo root / fixture paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parents[3]
PHASE9_DIR = REPO_ROOT / ".advanced-plans" / "phases" / "phase-9"
VERDICTS_DIR = REPO_ROOT / ".advanced-plans" / "gate-verdicts"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_phase_dir(tmp_path: Path, phase_num: int = 99) -> Path:
    """Create a minimal phase directory with plan.md and complete.md."""
    phase_dir = tmp_path / f"phase-{phase_num}"
    phase_dir.mkdir(parents=True)

    (phase_dir / "plan.md").write_text(
        f"---\nphase: {phase_num}\nname: \"Test Phase {phase_num}\"\n"
        f"status: draft\nloops: []\n---\n\n"
        f"## Key Deliverables\n\n"
        f"## Skills Required (Broad Categories)\n\n"
        f"- `test-skill`: used for testing\n",
        encoding="utf-8",
    )
    (phase_dir / "complete.md").write_text(
        f"---\nphase: {phase_num}\ntitle: \"Test Phase {phase_num}\"\n"
        f"status: passed\n---\n\n"
        f"## Goals met\n- First goal achieved -- commit abc1234\n"
        f"- Second goal achieved -- path/to/file.md\n\n"
        f"## Deferred\n- (none)\n\n"
        f"## Opened\n- (none)\n",
        encoding="utf-8",
    )
    (phase_dir / "loops.md").write_text(
        f"# Phase {phase_num} Loops\n",
        encoding="utf-8",
    )
    return phase_dir


def _make_verdict_dir(tmp_path: Path, phase_num: int, verdict: str = "pass") -> Path:
    """Create a minimal gate-verdicts directory under tmp_path."""
    adv = tmp_path / ".advanced-plans"
    gv = adv / "gate-verdicts"
    gv.mkdir(parents=True, exist_ok=True)
    # Also need .git sentinel for repo-root detection
    (tmp_path / ".git").mkdir(exist_ok=True)
    v_data = {
        "phase": f"phase-{phase_num}",
        "attempt": 1,
        "agent": "phase-goals-agent",
        "verdict": verdict,
        "confidence": 85,
        "failure_notes": [] if verdict == "pass" else ["Criterion X not met"],
        "loops_to_revert": [],
        "findings": [],
    }
    vpath = gv / f"phase-{phase_num}-attempt-1-phase-goals-agent.json"
    vpath.write_text(json.dumps(v_data), encoding="utf-8")
    return gv


# ---------------------------------------------------------------------------
# estimate_tokens
# ---------------------------------------------------------------------------

class TestEstimateTokens:
    def test_empty(self):
        assert estimate_tokens("") == 0

    def test_exact_multiple(self):
        assert estimate_tokens("abcd") == 1

    def test_ceil(self):
        # 5 chars -> ceil(5/4) = 2
        assert estimate_tokens("abcde") == 2

    def test_larger(self):
        text = "x" * 400
        assert estimate_tokens(text) == 100


# ---------------------------------------------------------------------------
# ascii_safe
# ---------------------------------------------------------------------------

class TestAsciiSafe:
    def test_em_dash_replaced(self):
        result = ascii_safe("hello—world")
        assert "--" in result
        assert "—" not in result

    def test_arrow_replaced(self):
        result = ascii_safe("goes → there")
        assert "->" in result
        assert "→" not in result

    def test_pure_ascii_unchanged(self):
        text = "hello world 123 !@#$"
        assert ascii_safe(text) == text

    def test_unknown_nonascii_replaced(self):
        result = ascii_safe("café")
        assert "?" in result
        assert "é" not in result


# ---------------------------------------------------------------------------
# check_ceiling
# ---------------------------------------------------------------------------

class TestCheckCeiling:
    def test_within_ceiling(self):
        text = "a" * 100
        # estimate_tokens("a"*100) = 25
        offenders = check_ceiling(text, 50)
        assert offenders == []

    def test_over_ceiling_returns_offenders(self):
        text = "a" * 4000  # ~1000 tokens
        offenders = check_ceiling(text, 50)
        assert len(offenders) >= 1
        assert "TOTAL" in offenders[0]
        assert "1000" in offenders[0]

    def test_exact_ceiling(self):
        # exactly at ceiling
        text = "a" * 400  # exactly 100 tokens
        offenders = check_ceiling(text, 100)
        assert offenders == []

    def test_one_over(self):
        text = "a" * 401  # ceil(401/4)=101 > 100
        offenders = check_ceiling(text, 100)
        assert len(offenders) >= 1


# ---------------------------------------------------------------------------
# enforce_ceiling
# ---------------------------------------------------------------------------

class TestEnforceCeiling:
    def test_no_raise_within_ceiling(self):
        # Should not raise
        enforce_ceiling("a" * 100, 50)  # 25 tokens < 50

    def test_raises_on_over_ceiling(self):
        with pytest.raises(SystemExit) as exc_info:
            enforce_ceiling("a" * 4000, 50)
        msg = str(exc_info.value)
        assert "token_ceiling=50" in msg
        assert "TOTAL" in msg

    def test_error_message_lists_sections(self):
        # Build text with multiple ## sections
        text = (
            "---\nphase: 1\n---\n\n"
            "## What was done & why\n" + ("- bullet\n" * 100) +
            "\n## Outcomes\n" + ("- outcome\n" * 100)
        )
        with pytest.raises(SystemExit) as exc_info:
            enforce_ceiling(text, 10)
        msg = str(exc_info.value)
        # Should mention at least one section
        assert "What was done" in msg or "Outcomes" in msg or "TOTAL" in msg


# ---------------------------------------------------------------------------
# _compact_bullets
# ---------------------------------------------------------------------------

class TestCompactBullets:
    def test_bullets_preserved(self):
        text = "- first bullet\n- second bullet"
        result = _compact_bullets(text)
        assert "- first bullet" in result
        assert "- second bullet" in result

    def test_long_bullet_truncated(self):
        long = "- " + "x" * 200
        result = _compact_bullets(long, max_len=160)
        assert result.endswith("...")
        assert len(result) <= 163  # 160 + "..."

    def test_empty_section(self):
        result = _compact_bullets("")
        assert result == "- (see complete.md)"

    def test_non_bullet_lines_skipped(self):
        text = "prose paragraph\n- bullet line"
        result = _compact_bullets(text)
        assert "bullet line" in result
        assert "prose paragraph" not in result


# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------

class TestParseFrontmatter:
    def test_basic_fields(self):
        text = "---\nphase: 9\ntitle: \"Test\"\nstatus: passed\n---\n"
        fm = _parse_frontmatter(text)
        assert fm.get("phase") == "9"
        assert fm.get("title") == '"Test"'
        assert fm.get("status") == "passed"

    def test_no_frontmatter(self):
        fm = _parse_frontmatter("plain text, no frontmatter")
        assert fm == {}

    def test_list_field(self):
        text = "---\ngate_verdict_refs:\n  - path/a.json\n  - path/b.json\n---\n"
        fm = _parse_frontmatter(text)
        refs = fm.get("gate_verdict_refs")
        assert isinstance(refs, list)
        assert "path/a.json" in refs


# ---------------------------------------------------------------------------
# generate_handoff_digest (integration, uses real phase-9 fixture)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not PHASE9_DIR.exists(),
    reason="phase-9 fixture not available"
)
class TestGenerateHandoffDigestPhase9:
    def test_generates_without_error(self, tmp_path):
        out = tmp_path / "handoff.md"
        digest = generate_handoff_digest(PHASE9_DIR, output_path=out)
        assert out.exists()
        assert len(digest) > 100

    def test_output_is_ascii_safe(self, tmp_path):
        out = tmp_path / "handoff.md"
        digest = generate_handoff_digest(PHASE9_DIR, output_path=out)
        # Should be encodable as ASCII (after sanitization)
        digest.encode("ascii")

    def test_contains_required_sections(self, tmp_path):
        out = tmp_path / "handoff.md"
        digest = generate_handoff_digest(PHASE9_DIR, output_path=out)
        for section in [
            "## What was done & why",
            "## Outcomes",
            "## Errors & issues encountered",
            "## Files touched",
            "## Gate review",
            "## Skills & methods used",
            "## Resume pointers",
        ]:
            assert section in digest, f"Missing section: {section}"

    def test_status_passed_for_pass(self, tmp_path):
        out = tmp_path / "handoff.md"
        digest = generate_handoff_digest(PHASE9_DIR, output_path=out, gate_verdict="passed")
        assert "status: passed" in digest

    def test_within_default_ceiling(self, tmp_path):
        out = tmp_path / "handoff.md"
        digest = generate_handoff_digest(PHASE9_DIR, output_path=out)
        from platforms.python.handoff_digest import DEFAULT_TOKEN_CEILING
        tok = estimate_tokens(digest)
        assert tok <= DEFAULT_TOKEN_CEILING, f"Digest is {tok} tokens, exceeds {DEFAULT_TOKEN_CEILING}"

    def test_dry_run_does_not_write(self, tmp_path):
        out = tmp_path / "handoff_dryrun.md"
        generate_handoff_digest(PHASE9_DIR, output_path=out, dry_run=True)
        assert not out.exists()

    def test_frontmatter_phase_field(self, tmp_path):
        out = tmp_path / "handoff.md"
        digest = generate_handoff_digest(PHASE9_DIR, output_path=out)
        assert "phase: 9" in digest

    def test_token_ceiling_violation_raises(self, tmp_path):
        out = tmp_path / "handoff.md"
        with pytest.raises(SystemExit) as exc_info:
            generate_handoff_digest(PHASE9_DIR, output_path=out, token_ceiling=10)
        msg = str(exc_info.value)
        assert "token_ceiling=10" in msg
        assert "TOTAL" in msg

    def test_token_ceiling_error_lists_sections(self, tmp_path):
        out = tmp_path / "handoff.md"
        with pytest.raises(SystemExit) as exc_info:
            generate_handoff_digest(PHASE9_DIR, output_path=out, token_ceiling=50)
        msg = str(exc_info.value)
        # At least one section should be named
        assert "What was done" in msg or "Outcomes" in msg or "Skills" in msg or "TOTAL" in msg

    def test_gate_fail_status(self, tmp_path):
        out = tmp_path / "handoff.md"
        digest = generate_handoff_digest(
            PHASE9_DIR, output_path=out, gate_verdict="failed_v1"
        )
        assert "status: failed_v1" in digest

    def test_gate_fail_nonempty_errors(self, tmp_path):
        out = tmp_path / "handoff.md"
        digest = generate_handoff_digest(
            PHASE9_DIR, output_path=out, gate_verdict="failed_v1"
        )
        # Errors & issues section must be non-empty (not just the heading)
        sections = _body_sections(digest)
        errors = sections.get("Errors & issues encountered", "")
        assert errors.strip() != ""
        assert "(none)" not in errors  # gate fail must have real content


# ---------------------------------------------------------------------------
# generate_handoff_digest (unit, uses tmp_path minimal fixture)
# ---------------------------------------------------------------------------

class TestGenerateHandoffDigestMinimal:
    def test_minimal_fixture_generates(self, tmp_path):
        phase_dir = _make_minimal_phase_dir(tmp_path, phase_num=99)
        _make_verdict_dir(tmp_path, phase_num=99)
        # Move .advanced-plans to tmp_path (already there from _make_verdict_dir)
        # Move phase dir under .advanced-plans
        adv = tmp_path / ".advanced-plans"
        phases = adv / "phases"
        phases.mkdir(parents=True, exist_ok=True)
        import shutil
        dest = phases / "phase-99"
        if not dest.exists():
            shutil.copytree(phase_dir, dest)
        out = tmp_path / "out_handoff.md"
        digest = generate_handoff_digest(dest, output_path=out, dry_run=True)
        assert "phase: 99" in digest
        assert "## Errors & issues encountered" in digest

    def test_missing_plan_raises(self, tmp_path):
        phase_dir = tmp_path / "phase-x"
        phase_dir.mkdir()
        (phase_dir / "complete.md").write_text("---\nphase: 0\n---\n", encoding="utf-8")
        with pytest.raises(FileNotFoundError):
            generate_handoff_digest(phase_dir, dry_run=True)

    def test_missing_complete_raises(self, tmp_path):
        phase_dir = tmp_path / "phase-y"
        phase_dir.mkdir()
        (phase_dir / "plan.md").write_text("---\nphase: 0\n---\n", encoding="utf-8")
        with pytest.raises(FileNotFoundError):
            generate_handoff_digest(phase_dir, dry_run=True)

    def test_gate_fail_minimal(self, tmp_path):
        phase_dir = _make_minimal_phase_dir(tmp_path, phase_num=98)
        (tmp_path / ".git").mkdir(exist_ok=True)
        out = tmp_path / "hf98.md"
        digest = generate_handoff_digest(
            phase_dir, output_path=out, gate_verdict="failed_v2", dry_run=True
        )
        assert "status: failed_v2" in digest
        # Errors section non-empty
        sections = _body_sections(digest)
        errors = sections.get("Errors & issues encountered", "")
        assert errors.strip() != ""

    def test_ceiling_fail_no_file_written(self, tmp_path):
        phase_dir = _make_minimal_phase_dir(tmp_path, phase_num=97)
        (tmp_path / ".git").mkdir(exist_ok=True)
        out = tmp_path / "hf97.md"
        with pytest.raises(SystemExit):
            generate_handoff_digest(phase_dir, output_path=out, token_ceiling=5)
        # File should NOT have been written
        assert not out.exists()
