"""Tests for platforms/python/path_audit.py.

Coverage:
  (a) Clean scoped tree passes (exit 0 / empty violations).
  (b) Planted `.advanced-.advanced-plans` (doubled-prefix) token fails.
  (c) Planted `.claude/plans/` (deprecated-token) token fails.
  (d) Legitimate `.claude/commands/` reference does NOT trip the audit
      (false-positive guard).
  (e) `.claude/.advanced-plans` (wrong-nesting) token fails.

Each test uses tmp_path to build an isolated scoped tree so the real repo
state does not affect results.
"""

import pathlib
import sys

import pytest

# Ensure repo root is importable.
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from platforms.python.path_audit import (  # noqa: E402
    PathViolation,
    audit,
    check_file,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_scoped_tree(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a minimal clean scoped tree under tmp_path and return its root.

    Mirrors the DEFAULT_SCANNED_ROOTS structure with one clean file each.
    """
    roots = [
        "platforms/claude-code/commands",
        "platforms/claude-code/agents",
        "core/agents",
        "core/skills",
        ".claude/commands",
        ".claude/agents",
    ]
    for rel in roots:
        d = tmp_path / rel
        d.mkdir(parents=True, exist_ok=True)
        # Write a clean placeholder file
        (d / "placeholder.md").write_text(
            "# Placeholder\n"
            "References .advanced-plans/state/ and .claude/commands/ correctly.\n",
            encoding="utf-8",
        )
    return tmp_path


# ---------------------------------------------------------------------------
# TestCleanTreePasses — (a) a tree with no violations exits clean
# ---------------------------------------------------------------------------

class TestCleanTreePasses:
    def test_clean_tree_returns_no_violations(self, tmp_path):
        """A scoped tree with only canonical references produces zero violations."""
        root = _make_scoped_tree(tmp_path)
        violations = audit(
            repo_root=root,
            scanned_roots=[
                "platforms/claude-code/commands",
                "platforms/claude-code/agents",
                "core/agents",
                "core/skills",
                ".claude/commands",
                ".claude/agents",
            ],
        )
        assert violations == [], (
            f"Expected no violations on a clean tree, got: {violations}"
        )

    def test_main_returns_zero_on_clean_tree(self, tmp_path):
        """main() returns exit code 0 on a clean tree."""
        root = _make_scoped_tree(tmp_path)
        exit_code = main(["--root", str(root)])
        assert exit_code == 0, f"Expected exit 0 on clean tree, got {exit_code}"


# ---------------------------------------------------------------------------
# TestDoubledPrefixFails — (b) .advanced-.advanced-plans is flagged
# ---------------------------------------------------------------------------

class TestDoubledPrefixFails:
    def test_doubled_prefix_in_command_file_is_flagged(self, tmp_path):
        """A `.advanced-.advanced-plans` token in a scoped file is a violation."""
        root = _make_scoped_tree(tmp_path)
        bad_file = root / "platforms" / "claude-code" / "commands" / "bad_cmd.md"
        bad_file.write_text(
            "# Bad command\n"
            "Read files from .advanced-.advanced-plans/state/loop-ready.json\n",
            encoding="utf-8",
        )
        violations = audit(
            repo_root=root,
            scanned_roots=["platforms/claude-code/commands"],
        )
        assert len(violations) >= 1, (
            "Expected at least one violation for doubled-prefix token"
        )
        pattern_names = [v.pattern_name for v in violations]
        assert any("doubled-prefix" in n for n in pattern_names), (
            f"Expected a doubled-prefix violation, got: {pattern_names}"
        )

    def test_doubled_prefix_in_agent_file_is_flagged(self, tmp_path):
        """Doubled-prefix token in a core/agents file is also caught."""
        root = _make_scoped_tree(tmp_path)
        agent_file = root / "core" / "agents" / "bad_agent.md"
        agent_file.parent.mkdir(parents=True, exist_ok=True)
        agent_file.write_text(
            "---\nagent: bad\n---\n"
            "Write to .advanced-.advanced-plans/state/\n",
            encoding="utf-8",
        )
        violations = audit(
            repo_root=root,
            scanned_roots=["core/agents"],
        )
        assert len(violations) >= 1
        assert any("doubled-prefix" in v.pattern_name for v in violations)

    def test_violation_records_file_and_line(self, tmp_path):
        """PathViolation namedtuple contains correct file and line number."""
        root = _make_scoped_tree(tmp_path)
        bad_file = root / "platforms" / "claude-code" / "commands" / "bug.md"
        bad_file.write_text(
            "line one\n"
            "line two\n"
            "bad: .advanced-.advanced-plans/state\n"
            "line four\n",
            encoding="utf-8",
        )
        violations = audit(
            repo_root=root,
            scanned_roots=["platforms/claude-code/commands"],
        )
        assert len(violations) >= 1
        v = violations[0]
        assert isinstance(v, PathViolation)
        assert v.file == bad_file
        assert v.line == 3  # The bad token is on line 3


# ---------------------------------------------------------------------------
# TestDeprecatedTokenFails — (c) .claude/plans/ is flagged
# ---------------------------------------------------------------------------

class TestDeprecatedTokenFails:
    def test_claude_plans_in_command_file_is_flagged(self, tmp_path):
        """`.claude/plans/` in a scoped command file is a violation."""
        root = _make_scoped_tree(tmp_path)
        bad_file = root / ".claude" / "commands" / "stale_cmd.md"
        bad_file.write_text(
            "# Stale command\n"
            "Read the plan from .claude/plans/phase-9/loops.md\n",
            encoding="utf-8",
        )
        violations = audit(
            repo_root=root,
            scanned_roots=[".claude/commands"],
        )
        assert len(violations) >= 1
        assert any("deprecated-token" in v.pattern_name for v in violations)

    def test_main_returns_one_on_deprecated_token(self, tmp_path):
        """main() exits 1 when a deprecated-token violation is present."""
        root = _make_scoped_tree(tmp_path)
        bad_file = root / ".claude" / "commands" / "broken.md"
        bad_file.write_text(
            "Read from .claude/plans/foo\n",
            encoding="utf-8",
        )
        exit_code = main(["--root", str(root)])
        assert exit_code == 1, f"Expected exit 1 on violation, got {exit_code}"


# ---------------------------------------------------------------------------
# TestWrongNestingFails — (e) .claude/.advanced-plans is flagged
# ---------------------------------------------------------------------------

class TestWrongNestingFails:
    def test_wrong_nesting_in_skill_file_is_flagged(self, tmp_path):
        """`.claude/.advanced-plans` in a scoped file is a violation."""
        root = _make_scoped_tree(tmp_path)
        skill_dir = root / "core" / "skills" / "some-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "# Some skill\n"
            "Write output to .claude/.advanced-plans/state/\n",
            encoding="utf-8",
        )
        violations = audit(
            repo_root=root,
            scanned_roots=["core/skills"],
        )
        assert len(violations) >= 1
        assert any("wrong-nesting" in v.pattern_name for v in violations)


# ---------------------------------------------------------------------------
# TestFalsePositiveGuard — (d) legitimate .claude/ refs are NOT flagged
# ---------------------------------------------------------------------------

class TestFalsePositiveGuard:
    def test_claude_commands_ref_is_not_flagged(self, tmp_path):
        """A legitimate `.claude/commands/` reference must not be flagged."""
        root = _make_scoped_tree(tmp_path)
        clean_file = root / "platforms" / "claude-code" / "commands" / "clean.md"
        clean_file.write_text(
            "# Install\n"
            "Commands are installed to `.claude/commands/` in the target project.\n"
            "Skills live at `.claude/skills/` and agents at `.claude/agents/`.\n",
            encoding="utf-8",
        )
        violations = audit(
            repo_root=root,
            scanned_roots=["platforms/claude-code/commands"],
        )
        assert violations == [], (
            f"Legitimate .claude/ reference was falsely flagged: {violations}"
        )

    def test_claude_skills_ref_is_not_flagged(self, tmp_path):
        """`.claude/skills/` reference must not be flagged."""
        root = _make_scoped_tree(tmp_path)
        clean_file = root / "core" / "agents" / "worker.md"
        clean_file.parent.mkdir(parents=True, exist_ok=True)
        clean_file.write_text(
            "Load skill from `.claude/skills/plan-todos/SKILL.md`.\n",
            encoding="utf-8",
        )
        violations = audit(
            repo_root=root,
            scanned_roots=["core/agents"],
        )
        assert violations == [], (
            f"Legitimate .claude/skills/ reference was falsely flagged: {violations}"
        )

    def test_advanced_plans_state_ref_is_not_flagged(self, tmp_path):
        """A canonical `.advanced-plans/state/` reference must not be flagged."""
        root = _make_scoped_tree(tmp_path)
        clean_file = root / "core" / "agents" / "orchestrator.md"
        clean_file.parent.mkdir(parents=True, exist_ok=True)
        clean_file.write_text(
            "Write to `.advanced-plans/state/loop-ready.json`.\n",
            encoding="utf-8",
        )
        violations = audit(
            repo_root=root,
            scanned_roots=["core/agents"],
        )
        assert violations == [], (
            f"Canonical .advanced-plans/ reference was falsely flagged: {violations}"
        )

    def test_docs_dir_is_excluded(self, tmp_path):
        """Files under docs/ must be excluded even if they contain the bad tokens."""
        root = tmp_path
        docs_dir = root / "docs"
        docs_dir.mkdir()
        (docs_dir / "path-conventions.md").write_text(
            "Deprecated: `.claude/plans/` and `.advanced-.advanced-plans`.\n",
            encoding="utf-8",
        )
        violations = audit(
            repo_root=root,
            scanned_roots=["docs"],  # Even if someone passes docs/ explicitly
            excluded_segments=["docs"],
        )
        assert violations == [], (
            "docs/ dir was scanned despite being in excluded_segments"
        )
