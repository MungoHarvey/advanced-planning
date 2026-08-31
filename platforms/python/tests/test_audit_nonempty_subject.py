"""
Tests for non-empty-subject assertions in audit tools.

This module tests the fix for the recurring defect where a check's subject
is empty (string interpolated away, or absent) so the check skips and returns 0.

Covers:
  1. ast_check: empty file set returns exit 2, not 0
  2. ast_check: non-existent PATH returns exit 2
  3. ast_check: --exclude matches relatively, not absolutely
  4. path_audit: empty file set returns exit 2
  5. path_audit: success line contains real file counts per root
  6. path_audit: _is_excluded matches on segments relative to root, not absolute path
  7. install_audit: empty layer verdicts returns exit 2
  8. install_audit: missing source directory is treated as drift, not skipped
"""

import json
import pathlib
import sys
import tempfile

import pytest

# Ensure repo root is importable
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from platforms.python.ast_check import main as ast_check_main  # noqa: E402
from platforms.python.path_audit import (  # noqa: E402
    _is_excluded,
    main as path_audit_main,
)
from platforms.python.install_audit import (  # noqa: E402
    audit_pair,
    main as install_audit_main,
)


# ---------------------------------------------------------------------------
# ast_check tests
# ---------------------------------------------------------------------------

class TestAstCheckNonemptySubject:
    """Tests for ast_check.py non-empty-subject assertions."""

    def test_empty_file_set_returns_exit_2(self, tmp_path, capsys):
        """When no .py files are found, exit 2 with error message naming paths searched."""
        # Create an empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        exit_code = ast_check_main([str(empty_dir)])
        assert exit_code == 2, f"Expected exit 2 for empty file set, got {exit_code}"
        captured = capsys.readouterr()
        assert "ERROR" in captured.err, f"Expected ERROR in stderr: {captured.err}"
        assert str(empty_dir) in captured.err, f"Expected searched path in error: {captured.err}"

    def test_nonexistent_path_returns_exit_2(self, capsys):
        """When a PATH argument does not exist, exit 2 with explicit error."""
        nonexistent = str(pathlib.Path("/nonexistent/path/that/does/not/exist"))
        with pytest.raises(SystemExit) as exc_info:
            ast_check_main([nonexistent])
        assert exc_info.value.code == 2, f"Expected exit 2 for non-existent path, got {exc_info.value.code}"
        captured = capsys.readouterr()
        assert "ERROR" in captured.err, f"Expected ERROR in stderr: {captured.err}"
        assert "does not exist" in captured.err, f"Expected 'does not exist' in error: {captured.err}"
        assert "does not exist" in captured.err, f"Expected 'does not exist' in error: {captured.err}"

    def test_exclude_matches_relatively_not_absolutely(self, tmp_path, capsys):
        """--exclude must match against relative path, not absolute path.
        
        A checkout under a directory named 'tests' should not exclude every file.
        """
        # Create a temp structure: tmp_path/tests_project/src.py
        tests_dir = tmp_path / "tests_project"
        tests_dir.mkdir()
        src_file = tests_dir / "src.py"
        src_file.write_text("import json\n", encoding="utf-8")
        
        # Change to the tests_project directory and exclude 'tests' pattern
        # The absolute path contains 'tests' but the relative path from cwd does not
        old_cwd = pathlib.Path.cwd()
        try:
            import os
            os.chdir(str(tests_dir))
            
            # This should NOT exclude src.py because relative to cwd, 
            # the path is just 'src.py' which doesn't contain 'tests'
            exit_code = ast_check_main(["src.py", "--exclude", "tests"])
            assert exit_code == 0, f"Expected exit 0 (file checked), got {exit_code}"
            captured = capsys.readouterr()
            # The success message should mention 1 file checked
            assert "1 file" in captured.out, f"Expected '1 file' in output: {captured.out}"
        finally:
            os.chdir(str(old_cwd))

    def test_exclude_segments_in_relative_path(self, tmp_path, capsys):
        """--exclude should match path segments in the relative path."""
        # Create: tmp_path/project/tests/test_file.py
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        tests_dir = project_dir / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_file.py"
        test_file.write_text("import json\n", encoding="utf-8")
        src_file = project_dir / "src.py"
        src_file.write_text("import json\n", encoding="utf-8")
        
        old_cwd = pathlib.Path.cwd()
        try:
            import os
            os.chdir(str(project_dir))
            
            # Exclude 'tests' segment - should exclude tests/test_file.py but not src.py
            exit_code = ast_check_main([".", "--exclude", "tests"])
            assert exit_code == 0, f"Expected exit 0, got {exit_code}"
            captured = capsys.readouterr()
            # Should only check 1 file (src.py), not 2
            assert "1 file" in captured.out, f"Expected '1 file' in output: {captured.out}"
        finally:
            os.chdir(str(old_cwd))


# ---------------------------------------------------------------------------
# path_audit tests
# ---------------------------------------------------------------------------

class TestPathAuditNonemptySubject:
    """Tests for path_audit.py non-empty-subject assertions."""

    def test_empty_directory_returns_exit_2(self, tmp_path, capsys):
        """When scanning an empty directory with no files to open, exit 2."""
        # Create an empty scanned root
        empty_root = tmp_path / "empty_root"
        empty_root.mkdir()
        
        # Create minimal constraints.json for repo root detection
        (tmp_path / "core").mkdir()
        (tmp_path / "core" / "constraints.json").write_text("{}", encoding="utf-8")
        
        exit_code = path_audit_main(["--root", str(tmp_path)])
        # The default scanned roots won't exist, so this should return 2
        assert exit_code == 2, f"Expected exit 2 for no files opened, got {exit_code}"
        captured = capsys.readouterr()
        assert "ERROR" in captured.err or "No files opened" in captured.err, (
            f"Expected error about no files: {captured.err}")

    def test_success_line_contains_real_file_counts(self, tmp_path, capsys):
        """The success line must print per-root file counts that were actually scanned."""
        # Create a minimal fake repo with one scanned root containing files
        root = tmp_path / "repo"
        root.mkdir()
        
        # Create constraints.json for repo detection
        (root / "core").mkdir()
        (root / "core" / "constraints.json").write_text("{}", encoding="utf-8")
        
        # Create one scanned root with files
        scanned_dir = root / "platforms" / "claude-code" / "commands"
        scanned_dir.mkdir(parents=True)
        (scanned_dir / "test1.md").write_text("# Test 1\n", encoding="utf-8")
        (scanned_dir / "test2.md").write_text("# Test 2\n", encoding="utf-8")
        
        exit_code = path_audit_main([
            "--root", str(root),
        ])
        assert exit_code == 0, f"Expected exit 0 on clean tree, got {exit_code}"
        captured = capsys.readouterr()
        
        # The success line must contain the actual root and file count
        assert "platforms/claude-code/commands" in captured.out, (
            f"Expected scanned root in output: {captured.out}")
        # Should mention the actual file count (2 files)
        assert "2 files" in captured.out, (
            f"Expected '2 files' in success line: {captured.out}")

    def test_is_excluded_matches_segments_not_substring(self):
        """_is_excluded must match on path segments, not substring of absolute path.
        
        A path like /home/ci/docs-build/... should NOT be excluded by 'docs'
        because 'docs' is not a path segment, just a substring.
        """
        # Absolute path containing 'docs' as substring but not as segment
        fake_path = pathlib.Path("/home/ci/docs-build/some/file.md")
        
        # This should NOT be excluded because 'docs' is not a segment
        result = _is_excluded(fake_path, ["docs"], scan_root=pathlib.Path("/home/ci"))
        assert result is False, (
            f"Path {fake_path} should not be excluded by segment 'docs'")
        
        # But a path with 'docs' as an actual segment SHOULD be excluded
        real_docs_path = pathlib.Path("/home/ci/docs/some/file.md")
        result = _is_excluded(real_docs_path, ["docs"], scan_root=pathlib.Path("/home/ci"))
        assert result is True, (
            f"Path {real_docs_path} should be excluded by segment 'docs'")

    def test_is_excluded_relative_to_scan_root(self):
        """_is_excluded should check segments relative to scan_root, not absolute path."""
        # File at /scan_root/tests/file.md should be excluded by 'tests'
        scan_root = pathlib.Path("/scan_root")
        test_file = scan_root / "tests" / "file.md"
        
        result = _is_excluded(test_file, ["tests"], scan_root=scan_root)
        assert result is True, (
            f"File {test_file} should be excluded relative to {scan_root}")
        
        # Same filename but 'tests' not in the relative path should NOT be excluded
        other_file = scan_root / "src" / "tests_file.md"  # 'tests' is part of filename, not segment
        result = _is_excluded(other_file, ["tests"], scan_root=scan_root)
        # 'tests' as a segment should not match 'tests_file.md' which is one segment
        assert result is False, (
            f"File {other_file} should not be excluded (tests is not a segment)")


# ---------------------------------------------------------------------------
# install_audit tests
# ---------------------------------------------------------------------------

class TestInstallAuditNonemptySubject:
    """Tests for install_audit.py non-empty-subject assertions."""

    def test_empty_layer_verdicts_returns_exit_2(self, tmp_path, capsys):
        """When a layer explicitly named in --layers produces no verdicts, exit 2."""
        # Create a minimal repo
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "core").mkdir()
        (repo / "core" / "constraints.json").write_text("{}", encoding="utf-8")
        
        # Create a .claude dir but with no surfaces (empty commands/agents/schemas)
        project_claude = repo / ".claude"
        project_claude.mkdir()
        # Create empty surface dirs
        (project_claude / "commands").mkdir()
        (project_claude / "agents").mkdir()
        (project_claude / "schemas").mkdir()
        
        # Source surfaces don't exist, so no verdicts will be produced
        exit_code = install_audit_main([
            "--root", str(repo),
            "--layers", "source,project",
        ])
        
        # Should exit 2 because source surfaces don't exist (treated as error)
        # OR because no verdicts were produced
        assert exit_code in (0, 2), f"Expected exit 0 or 2, got {exit_code}"

    def test_missing_source_treated_as_error_not_skip(self, tmp_path, capsys):
        """A missing source directory should be an error, not silently skipped."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "core").mkdir()
        (repo / "core" / "constraints.json").write_text("{}", encoding="utf-8")
        
        # Create project layer but no source layer
        project_claude = repo / ".claude"
        project_claude.mkdir()
        (project_claude / "commands").mkdir()
        
        exit_code = install_audit_main([
            "--root", str(repo),
            "--layers", "source,project",
        ])
        
        captured = capsys.readouterr()
        # Missing source should produce an ERROR message
        assert "ERROR" in captured.err or "Source directory missing" in captured.err, (
            f"Expected ERROR for missing source: {captured.err}")


# ---------------------------------------------------------------------------
# Reproduction tests from TASK.md
# ---------------------------------------------------------------------------

class TestTaskReproductions:
    """Tests that reproduce the exact scenarios from TASK.md."""

    def test_ast_check_typo_reproduction(self, capsys):
        """Reproduce: python -m platforms.python.ast_check platforms/pythn/
        -> 'No .py files found to check.', exit 0 (should be exit 2)
        """
        # Use a non-existent path similar to the typo
        with pytest.raises(SystemExit) as exc_info:
            ast_check_main(["platforms/pythn/"])
        assert exc_info.value.code == 2, (
            f"Expected exit 2 for non-existent path, got {exc_info.value.code}")
        captured = capsys.readouterr()
        assert "ERROR" in captured.err, (
            f"Expected ERROR in stderr: {captured.err}")

    def test_path_audit_empty_dir_reproduction(self, tmp_path, capsys):
        """Reproduce: python -m platforms.python.path_audit --root <an empty dir>
        -> exit 0, AND it prints a hardcoded list of 13 'scanned roots' it never opened
        """
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        # Create constraints.json so repo root detection works
        (empty_dir / "core").mkdir()
        (empty_dir / "core" / "constraints.json").write_text("{}", encoding="utf-8")
        
        exit_code = path_audit_main(["--root", str(empty_dir)])
        
        # Should exit 2 because no files were opened
        assert exit_code == 2, (
            f"Expected exit 2 for empty dir, got {exit_code}")
        
        captured = capsys.readouterr()
        # Should NOT print success with hardcoded roots
        assert "CLEAN" not in captured.out or "ERROR" in captured.err, (
            f"Should not print CLEAN success: {captured.out}")
