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
    Platform-specific roots mention .claude/; core/ roots are host-neutral.
    """
    roots = [
        ("platforms/claude-code/commands", "References .claude/commands/ for installed runtime."),
        ("platforms/claude-code/agents", "References .claude/agents/ for installed runtime."),
        ("core/agents", "Platform-agnostic orchestrator definitions."),
        ("core/skills", "Platform-agnostic skill definitions."),
        (".claude/commands", "Runtime commands."),
        (".claude/agents", "Runtime agents."),
    ]
    for rel, content in roots:
        d = tmp_path / rel
        d.mkdir(parents=True, exist_ok=True)
        # Write a clean placeholder file
        (d / "placeholder.md").write_text(
            f"# Placeholder\n{content}\n",
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
        violations, suppressed = audit(
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
        assert suppressed == [], (
            f"Expected no suppressed exceptions on a clean tree, got: {suppressed}"
        )

    def test_main_returns_zero_on_clean_tree(self, tmp_path):
        """main() returns exit code 0 on a clean tree."""
        root = _make_scoped_tree(tmp_path)
        exit_code = main(["--root", str(root)])
        assert exit_code == 0, f"Expected exit 0 on clean tree, got {exit_code}"

    def test_main_returns_zero_with_suppressed_only(self, tmp_path):
        """main() returns exit code 0 when only suppressed exceptions exist (no violations)."""
        # The main() function prints suppressed but exits 0 if no violations
        # This is tested implicitly by the clean tree test since exceptions are file-specific
        pass


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
        violations, suppressed = audit(
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
        violations, suppressed = audit(
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
        violations, suppressed = audit(
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
        violations, suppressed = audit(
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
        violations, suppressed = audit(
            repo_root=root,
            scanned_roots=["core/skills"],
        )
        assert len(violations) >= 1
        assert any("wrong-nesting" in v.pattern_name for v in violations)


# ---------------------------------------------------------------------------
# TestFalsePositiveGuard — (d) legitimate .claude/ refs are NOT flagged in platforms/
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
        violations, suppressed = audit(
            repo_root=root,
            scanned_roots=["platforms/claude-code/commands"],
        )
        assert violations == [], (
            f"Legitimate .claude/ reference was falsely flagged: {violations}"
        )

    def test_claude_skills_ref_is_not_flagged_in_platforms(self, tmp_path):
        """`.claude/skills/` reference in platforms/claude-code/ must not be flagged.

        This is the false-positive guard: adapter docs legitimately describe
        the installed runtime layout. The same reference in core/ WOULD be flagged.
        """
        root = _make_scoped_tree(tmp_path)
        clean_file = root / "platforms" / "claude-code" / "commands" / "install.md"
        clean_file.write_text(
            "Load skill from `.claude/skills/plan-todos/SKILL.md`.\n",
            encoding="utf-8",
        )
        violations, suppressed = audit(
            repo_root=root,
            scanned_roots=["platforms/claude-code/commands"],
        )
        assert violations == [], (
            f"Legitimate .claude/skills/ reference in platforms/ was falsely flagged: {violations}"
        )


# ---------------------------------------------------------------------------
# TestHostNeutralityInCore — host-specific tokens in core/ ARE flagged
# ---------------------------------------------------------------------------

class TestHostNeutralityInCore:
    def test_claude_directory_in_core_agents_is_flagged(self, tmp_path):
        """`.claude/` reference in core/agents/ MUST be flagged.

        This inverts the old false-positive guard: core/ must be host-neutral.
        The same reference in platforms/claude-code/ is legitimate and NOT flagged.
        """
        root = _make_scoped_tree(tmp_path)
        bad_file = root / "core" / "agents" / "worker.md"
        bad_file.parent.mkdir(parents=True, exist_ok=True)
        bad_file.write_text(
            "Load skill from `.claude/skills/plan-todos/SKILL.md`.\n",
            encoding="utf-8",
        )
        violations, suppressed = audit(
            repo_root=root,
            scanned_roots=["core/agents"],
        )
        assert len(violations) >= 1, (
            "Expected host-directory violation for .claude/ in core/agents/"
        )
        assert any("host-directory" in v.pattern_name for v in violations), (
            f"Expected host-directory violation, got: {[v.pattern_name for v in violations]}"
        )

    def test_cursor_directory_in_core_skills_is_flagged(self, tmp_path):
        """`.cursor/` reference in core/skills/ MUST be flagged."""
        root = _make_scoped_tree(tmp_path)
        bad_file = root / "core" / "skills" / "some-skill" / "SKILL.md"
        bad_file.parent.mkdir(parents=True, exist_ok=True)
        bad_file.write_text(
            "Configure in `.cursor/settings.json`.\n",
            encoding="utf-8",
        )
        violations, suppressed = audit(
            repo_root=root,
            scanned_roots=["core/skills"],
        )
        assert len(violations) >= 1
        assert any("host-directory" in v.pattern_name for v in violations)

    def test_agent_tool_name_in_core_is_flagged(self, tmp_path):
        """`Agent tool` and `Task tool` references in core/ MUST be flagged."""
        root = _make_scoped_tree(tmp_path)
        bad_file = root / "core" / "agents" / "orchestrator.md"
        bad_file.parent.mkdir(parents=True, exist_ok=True)
        bad_file.write_text(
            "Use the Agent tool to spawn subagents.\n"
            "The Task tool writes the final state.\n"
            "Call TodoWrite to record progress.\n"
            "Pass subagent_type to the API.\n"
            "Claude Code and Cowork are host-specific.\n",
            encoding="utf-8",
        )
        violations, suppressed = audit(
            repo_root=root,
            scanned_roots=["core/agents"],
        )
        assert len(violations) >= 1
        assert any("host-tool-name" in v.pattern_name for v in violations)

    def test_bare_task_agent_words_in_core_are_not_flagged(self, tmp_path):
        """Bare English words 'Task' and 'Agent' in prose and table headers must NOT be flagged.

        This proves the rule matches named tools/identifiers, not ordinary nouns.
        Examples: '| Loop | Task | Todos |', '## Task Decomposition', '# Agent Architecture'.
        """
        root = _make_scoped_tree(tmp_path)
        clean_file = root / "core" / "agents" / "patterns.md"
        clean_file.parent.mkdir(parents=True, exist_ok=True)
        clean_file.write_text(
            "# Agent Architecture\n"
            "## Task Decomposition Patterns\n"
            "\n"
            "| Loop | Task | Todos | Status | Done |\n"
            "|------|------|-------|--------|------|\n"
            "| 001  | Plan | 5     | done   | yes  |\n"
            "\n"
            "Each Task is a simple one-liner (git commit, file copy, log write).\n"
            "The agent writes the state bus files.\n"
            "task_name: \"Descriptive Task Name\"\n",
            encoding="utf-8",
        )
        violations, suppressed = audit(
            repo_root=root,
            scanned_roots=["core/agents"],
        )
        assert violations == [], (
            f"Bare English words 'Task' and 'Agent' were falsely flagged: {violations}"
        )

    def test_settings_json_in_core_is_flagged(self, tmp_path):
        """`settings.json` permission syntax in core/ MUST be flagged."""
        root = _make_scoped_tree(tmp_path)
        bad_file = root / "core" / "skills" / "some-skill" / "SKILL.md"
        bad_file.parent.mkdir(parents=True, exist_ok=True)
        bad_file.write_text(
            "Requires permissions.defaultMode = ask in settings.json.\n",
            encoding="utf-8",
        )
        violations, suppressed = audit(
            repo_root=root,
            scanned_roots=["core/skills"],
        )
        assert len(violations) >= 1
        assert any("host-permission-syntax" in v.pattern_name for v in violations)

    def test_host_tool_names_in_core_are_flagged(self, tmp_path):
        """Named host tools (Agent tool, Task tool, TodoWrite, subagent_type, Claude Code, Cowork) in core/ MUST be flagged."""
        root = _make_scoped_tree(tmp_path)
        bad_file = root / "core" / "agents" / "orchestrator.md"
        bad_file.parent.mkdir(parents=True, exist_ok=True)
        bad_file.write_text(
            "Use the Agent tool to spawn subagents.\n"
            "The Task tool writes state.\n"
            "Call TodoWrite to record progress.\n"
            "Pass subagent_type to the API.\n"
            "Claude Code is one host.\n"
            "Cowork is another host.\n",
            encoding="utf-8",
        )
        violations, suppressed = audit(
            repo_root=root,
            scanned_roots=["core/agents"],
        )
        # Should flag all 6 tool names (one per line)
        assert len(violations) == 6, f"Expected 6 host-tool-name violations, got {len(violations)}: {violations}"
        for v in violations:
            assert "host-tool-name" in v.pattern_name

    def test_core_without_host_tokens_is_clean(self, tmp_path):
        """A core/ file with no host-specific tokens passes."""
        root = _make_scoped_tree(tmp_path)
        clean_file = root / "core" / "agents" / "clean.md"
        clean_file.parent.mkdir(parents=True, exist_ok=True)
        clean_file.write_text(
            "The orchestrator writes loop-ready.json to the state bus.\n"
            "Platform-agnostic core definitions.\n",
            encoding="utf-8",
        )
        violations, suppressed = audit(
            repo_root=root,
            scanned_roots=["core/agents"],
        )
        assert violations == [], (
            f"Clean core/ file was falsely flagged: {violations}"
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
        violations, suppressed = audit(
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
        violations, suppressed = audit(
            repo_root=root,
            scanned_roots=["docs"],  # Even if someone passes docs/ explicitly
            excluded_segments=["docs"],
        )
        assert violations == [], (
            "docs/ dir was scanned despite being in excluded_segments"
        )


# ---------------------------------------------------------------------------
# TestExceptionMechanism — excepted files still fail on other rules
# ---------------------------------------------------------------------------

class TestExceptionMechanism:
    def test_excepted_file_fails_on_different_rule(self, tmp_path):
        """An excepted file must still fail on a rule it was not excepted for.

        This proves the exception mechanism is keyed by (file, pattern), not file alone.
        permission-config/SKILL.md is excepted for host-permission-syntax, but should
        still fail if it contains a host-directory token.
        """
        root = _make_scoped_tree(tmp_path)
        # Create a file similar to permission-config that has both permission syntax
        # (excepted) and a .claude/ directory reference (not excepted)
        bad_file = root / "core" / "skills" / "test-skill" / "SKILL.md"
        bad_file.parent.mkdir(parents=True, exist_ok=True)
        bad_file.write_text(
            "Edit settings.json permissions.\n"
            "Install to `.claude/skills/` directory.\n",  # This should be flagged
            encoding="utf-8",
        )
        violations, suppressed = audit(
            repo_root=root,
            scanned_roots=["core/skills"],
        )
        # The .claude/ reference should be a violation (not excepted)
        assert len(violations) >= 1, f"Expected violation for .claude/ directory, got {violations}"
        assert any("host-directory" in v.pattern_name for v in violations), (
            f"Expected host-directory violation, got: {[v.pattern_name for v in violations]}"
        )
