"""Tests for install.sh idempotency over an existing .advanced-plans/ tree.

Coverage:
- Pre-existing .advanced-plans/ tree is byte-unchanged after install.sh runs
- .claude/commands/ is populated after install.sh runs on a fresh project
- Negative (fresh) case: install on an empty dir creates .advanced-plans/ scaffold
- Skip on platforms where bash is not available (e.g. Windows without Git Bash)

Skip condition:
    import shutil; shutil.which("bash") is None
"""

import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

# ---------------------------------------------------------------------------
# Locate repo root: tests/ -> python/ -> platforms/ -> repo-root
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_INSTALL_SH = _REPO_ROOT / "setup" / "claude-code" / "install.sh"

# ---------------------------------------------------------------------------
# Skip guard: bail out on platforms without bash
# ---------------------------------------------------------------------------
_BASH = shutil.which("bash")
_BASH_AVAILABLE = _BASH is not None

pytestmark = pytest.mark.skipif(
    not _BASH_AVAILABLE,
    reason="bash not available on this platform; skipping install.sh idempotency tests",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_bash_path_prefix() -> str:
    """Detect the drive-letter prefix scheme used by the available bash.

    Git Bash / MSYS2 uses /c/... ; WSL uses /mnt/c/... .
    Returns the prefix for the C: drive (e.g. '/c' or '/mnt/c').
    Returns '' if the bash is not found or not Windows.
    """
    if sys.platform != "win32":
        return ""
    bash = shutil.which("bash")
    if bash is None:
        return ""
    # Probe: try to ls a known Windows file using both conventions
    for prefix in ("/mnt/c", "/c"):
        probe = subprocess.run(
            ["bash", "-c", f"test -d {prefix}/Windows"],
            capture_output=True,
        )
        if probe.returncode == 0:
            return prefix
    return "/mnt/c"  # WSL default fallback


_BASH_DRIVE_PREFIX = _detect_bash_path_prefix()


def _to_bash_path(p: pathlib.Path) -> str:
    """Convert a pathlib.Path to a bash-compatible path string.

    On Windows, the conversion depends on the bash flavour detected by
    _detect_bash_path_prefix():
    - WSL:       C:\\foo\\bar  ->  /mnt/c/foo/bar
    - MSYS2/Git: C:\\foo\\bar  ->  /c/foo/bar
    On Unix the path is returned unchanged.
    """
    p_str = str(p)
    if sys.platform != "win32" or not _BASH_DRIVE_PREFIX:
        return p_str
    if len(p_str) >= 2 and p_str[1] == ":":
        drive = p_str[0].lower()
        # _BASH_DRIVE_PREFIX is '/mnt/c' or '/c' — strip the trailing drive
        # letter to get the base ('/mnt' or ''), then append /drive/rest
        base = _BASH_DRIVE_PREFIX[:-1] if _BASH_DRIVE_PREFIX[-1].isalpha() else _BASH_DRIVE_PREFIX
        rest = p_str[2:].replace("\\", "/")
        return f"{base}{drive}{rest}"
    return p_str.replace("\\", "/")


def _run_install(project_dir: pathlib.Path) -> subprocess.CompletedProcess:
    """Invoke install.sh against *project_dir* and return the result."""
    return subprocess.run(
        [
            "bash",
            _to_bash_path(_INSTALL_SH),
            "--project",
            _to_bash_path(project_dir),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _make_existing_planning_tree(base: pathlib.Path) -> dict:
    """Create a minimal .advanced-plans/ tree under *base*.

    Returns a dict mapping relative-path-string -> bytes of each created file,
    so the test can byte-compare after install.
    """
    ap = base / ".advanced-plans"
    phase_dir = ap / "phases" / "phase-1"
    phase_dir.mkdir(parents=True, exist_ok=True)

    plan_content = b"# phase-1 plan\nstatus: testing\n"
    plan_file = phase_dir / "plan.md"
    plan_file.write_bytes(plan_content)

    index_content = b"# PLANS-INDEX\n\n- phase-1: in-progress\n"
    index_file = ap / "PLANS-INDEX.md"
    index_file.write_bytes(index_content)

    return {
        ".advanced-plans/phases/phase-1/plan.md": plan_content,
        ".advanced-plans/PLANS-INDEX.md": index_content,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestInstallIdempotency:
    """install.sh must never overwrite an existing .advanced-plans/ tree."""

    def test_existing_planning_data_preserved(self, tmp_path):
        """Pre-existing .advanced-plans/ files are byte-unchanged after install."""
        expected = _make_existing_planning_tree(tmp_path)

        result = _run_install(tmp_path)
        assert result.returncode == 0, (
            f"install.sh exited {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # Verify every pre-existing file is byte-unchanged
        for rel_path, expected_bytes in expected.items():
            actual_file = tmp_path / rel_path
            assert actual_file.exists(), f"File disappeared after install: {rel_path}"
            actual_bytes = actual_file.read_bytes()
            assert actual_bytes == expected_bytes, (
                f"File was modified by install.sh: {rel_path}\n"
                f"Expected: {expected_bytes!r}\n"
                f"Got:      {actual_bytes!r}"
            )

    def test_claude_commands_populated(self, tmp_path):
        """install.sh populates .claude/commands/ regardless of existing data."""
        _make_existing_planning_tree(tmp_path)

        result = _run_install(tmp_path)
        assert result.returncode == 0, (
            f"install.sh exited {result.returncode}\n{result.stderr}"
        )

        commands_dir = tmp_path / ".claude" / "commands"
        assert commands_dir.exists(), ".claude/commands/ was not created"
        md_files = list(commands_dir.glob("*.md"))
        assert len(md_files) > 0, ".claude/commands/ contains no .md files"

    def test_stdout_reports_preserving(self, tmp_path):
        """install.sh stdout contains the 'Preserving existing' message."""
        _make_existing_planning_tree(tmp_path)

        result = _run_install(tmp_path)
        assert result.returncode == 0
        assert "Preserving existing planning data" in result.stdout, (
            "Expected scaffold-skip message not found in stdout.\n"
            f"stdout: {result.stdout}"
        )


class TestInstallFreshProject:
    """install.sh creates the .advanced-plans/ scaffold on a fresh project."""

    def test_scaffold_created_when_absent(self, tmp_path):
        """Empty project gets .advanced-plans/ scaffold after install."""
        ap = tmp_path / ".advanced-plans"
        assert not ap.exists(), "Precondition: .advanced-plans/ must not exist"

        result = _run_install(tmp_path)
        assert result.returncode == 0, (
            f"install.sh exited {result.returncode}\n{result.stderr}"
        )

        assert ap.exists(), ".advanced-plans/ was not created"
        assert (ap / "phases").exists(), ".advanced-plans/phases/ missing"
        assert (ap / "state").exists(), ".advanced-plans/state/ missing"
        assert (ap / "PLANNING.md").exists(), ".advanced-plans/PLANNING.md missing"

    def test_stdout_reports_creating_scaffold(self, tmp_path):
        """install.sh stdout contains the scaffold-creation message."""
        result = _run_install(tmp_path)
        assert result.returncode == 0
        assert "Creating .advanced-plans" in result.stdout, (
            "Expected scaffold-creation message not found in stdout.\n"
            f"stdout: {result.stdout}"
        )
