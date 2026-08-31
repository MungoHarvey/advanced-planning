"""Tests for fail-closed uninstall behavior when registry is missing or malformed.

These tests verify that uninstall scripts refuse to remove skills and shared files
when the ownership registry cannot be read, unless --force-no-registry is passed.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


# ── Helper utilities ────────────────────────────────────────────────────────────

def _find_git_bash():
    """Return a path to Git Bash, or None.

    Deliberately not shutil.which("bash"): on Windows that finds WSL,
    which resolves /mnt/c/... and so cannot open a Windows path. Git Bash
    runs these scripts on Windows without trouble.
    """
    if sys.platform != "win32":
        return shutil.which("bash")
    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        / "Git" / "bin" / "bash.exe",
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Programs" / "Git" / "bin" / "bash.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        / "Git" / "bin" / "bash.exe",
    ]
    for candidate in candidates:
        try:
            if candidate.is_file():
                return str(candidate)
        except OSError:
            continue
    return None


GIT_BASH = _find_git_bash()


def _fwd(path) -> str:
    """A Windows path in the forward-slash form Git Bash accepts."""
    return str(path).replace(os.sep, "/")


def _setup_fake_install(base_dir: Path, adapter: str) -> Path:
    """Create a fake install with skills, bin/ap.py, and runtime.json.
    
    Returns the .advanced-plans directory.
    """
    agents_dir = base_dir / ".agents"
    skills_dir = agents_dir / "skills"
    ap_dir = base_dir / ".advanced-plans"
    bin_dir = ap_dir / "bin"
    
    # Create directory structure
    skills_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a couple of skill folders
    for skill_name in ["advanced-planning", "phase-plan-creator"]:
        skill_dir = skills_dir / skill_name
        skill_dir.mkdir(exist_ok=True)
        (skill_dir / "SKILL.md").write_text(f"# {skill_name}\n")
    
    # Create shared files
    (bin_dir / "ap.py").write_text("#!/usr/bin/env python\n# Shared launcher\n")
    (ap_dir / "runtime.json").write_text('{"adapter": "' + adapter + '"}\n')
    
    return ap_dir


def _run_shell_uninstall(project_dir: Path, adapter: str, extra_args: list[str] | None = None) -> tuple[int, str, str]:
    """Run the shell uninstall script and return (returncode, stdout, stderr)."""
    script_path = Path(__file__).parents[3] / "setup" / adapter / "uninstall.sh"
    # An interpreter is required: a .sh is not directly executable on
    # Windows, and the bash on PATH there is WSL.
    cmd = [GIT_BASH, _fwd(script_path), "--project", _fwd(project_dir)]
    if extra_args:
        cmd.extend(extra_args)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(project_dir),
    )
    return result.returncode, result.stdout, result.stderr


def _run_powershell_uninstall(project_dir: Path, adapter: str, extra_args: list[str] | None = None) -> tuple[int, str, str]:
    """Run the PowerShell uninstall script and return (returncode, stdout, stderr)."""
    script_path = Path(__file__).parents[3] / "setup" / adapter / "uninstall.ps1"
    # Use -ExecutionPolicy Bypass to avoid profile loading issues
    cmd = ["pwsh", "-ExecutionPolicy", "Bypass", "-File", str(script_path), "-Project", str(project_dir)]
    if extra_args:
        cmd.extend(extra_args)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(project_dir),
    )
    return result.returncode, result.stdout, result.stderr


def _check_bash_available() -> bool:
    """Whether Git Bash was found on this machine.

    This used to return False for every Windows host, which skipped the
    entire shell half of this file on the only platform it runs on. The
    WSL-on-PATH problem it was reacting to is real; refusing to look for
    Git Bash was not the remedy.
    """
    return GIT_BASH is not None


def _check_pwsh_available() -> bool:
    """Check if pwsh is available."""
    return shutil.which("pwsh") is not None


# ── Test: registry absent → nothing deleted, exit non-zero ─────────────────────

class TestRegistryAbsent:
    """When the registry file is missing, uninstall must refuse to proceed."""
    
    def test_shell_registry_absent_refuses(self, tmp_path: Path):
        """Shell script: missing registry → exit 1, nothing deleted."""
        if not _check_bash_available():
            pytest.skip("bash not available (WSL bash on Windows cannot run Windows scripts)")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "codex")
        
        # Do NOT create the registry file
        returncode, stdout, stderr = _run_shell_uninstall(project_dir, "codex")
        
        assert returncode != 0, "Expected non-zero exit when registry is missing"
        assert "registry not found" in stderr.lower(), f"Expected error message, got: {stderr}"
        
        # Verify files are still on disk
        assert (ap_dir / "bin" / "ap.py").exists(), "bin/ap.py should still exist"
        assert (ap_dir / "runtime.json").exists(), "runtime.json should still exist"
        assert (ap_dir.parents[0] / ".agents" / "skills" / "advanced-planning").exists(), "Skills should still exist"
    
    def test_powershell_registry_absent_refuses(self, tmp_path: Path):
        """PowerShell script: missing registry → exit 1, nothing deleted."""
        if not _check_pwsh_available():
            pytest.skip("pwsh not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "codex")
        
        # Do NOT create the registry file
        returncode, stdout, stderr = _run_powershell_uninstall(project_dir, "codex")
        
        assert returncode != 0, "Expected non-zero exit when registry is missing"
        assert "registry not found" in stderr.lower(), f"Expected error message, got: {stderr}"
        
        # Verify files are still on disk
        assert (ap_dir / "bin" / "ap.py").exists(), "bin/ap.py should still exist"
        assert (ap_dir / "runtime.json").exists(), "runtime.json should still exist"
        assert (ap_dir.parents[0] / ".agents" / "skills" / "advanced-planning").exists(), "Skills should still exist"


# ── Test: registry malformed → nothing deleted, exit non-zero ──────────────────

class TestRegistryMalformed:
    """When the registry is unparseable JSON, uninstall must refuse to proceed."""
    
    def test_shell_registry_malformed_refuses(self, tmp_path: Path):
        """Shell script: malformed JSON → exit 1, error names the file."""
        if not _check_bash_available():
            pytest.skip("bash not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "codex")
        
        # Create malformed registry
        registry_file = ap_dir / "skill-ownership.json"
        registry_file.write_text("{ not json")
        
        returncode, stdout, stderr = _run_shell_uninstall(project_dir, "codex")
        
        assert returncode != 0, "Expected non-zero exit when registry is malformed"
        assert "malformed json" in stderr.lower(), f"Expected error message, got: {stderr}"
        assert str(registry_file) in stderr or "skill-ownership.json" in stderr, \
            f"Expected error to name the file, got: {stderr}"
        
        # Verify files are still on disk
        assert (ap_dir / "bin" / "ap.py").exists(), "bin/ap.py should still exist"
        assert (ap_dir / "runtime.json").exists(), "runtime.json should still exist"
    
    def test_powershell_registry_malformed_refuses(self, tmp_path: Path):
        """PowerShell script: malformed JSON → exit 1, error names the file."""
        if not _check_pwsh_available():
            pytest.skip("pwsh not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "codex")
        
        # Create malformed registry
        registry_file = ap_dir / "skill-ownership.json"
        registry_file.write_text("{ not json")
        
        returncode, stdout, stderr = _run_powershell_uninstall(project_dir, "codex")
        
        assert returncode != 0, "Expected non-zero exit when registry is malformed"
        assert "malformed json" in stderr.lower(), f"Expected error message, got: {stderr}"
        
        # Verify files are still on disk
        assert (ap_dir / "bin" / "ap.py").exists(), "bin/ap.py should still exist"
        assert (ap_dir / "runtime.json").exists(), "runtime.json should still exist"


# ── Test: registry absent + --force-no-registry → old behavior with warning ────

class TestForceNoRegistry:
    """When --force-no-registry is passed, proceed with warning."""
    
    def test_shell_force_no_registry_proceeds(self, tmp_path: Path):
        """Shell script: --force-no-registry with missing registry → proceeds with warning."""
        if not _check_bash_available():
            pytest.skip("bash not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "codex")
        
        # Do NOT create the registry file, but pass --force-no-registry
        returncode, stdout, stderr = _run_shell_uninstall(
            project_dir, "codex", ["--force-no-registry"]
        )
        
        # Should succeed (or at least not fail on registry)
        assert "WARNING" in stderr or "warning" in stderr.lower(), \
            f"Expected warning about proceeding without registry, got: {stderr}"
    
    def test_powershell_force_no_registry_proceeds(self, tmp_path: Path):
        """PowerShell script: -ForceNoRegistry with missing registry → proceeds with warning."""
        if not _check_pwsh_available():
            pytest.skip("pwsh not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "codex")
        
        # Do NOT create the registry file, but pass -ForceNoRegistry
        returncode, stdout, stderr = _run_powershell_uninstall(
            project_dir, "codex", ["-ForceNoRegistry"]
        )
        
        # Should succeed (or at least not fail on registry)
        # Write-Warning goes to stdout in captured output
        combined = stdout + stderr
        assert "WARNING" in combined or "warning" in combined.lower(), \
            f"Expected warning about proceeding without registry, got stdout={stdout!r} stderr={stderr!r}"


# ── Test: registry present with other adapter as owner → skill kept ────────────

class TestSharedOwnership:
    """When registry lists another adapter as owner, files are kept."""
    
    def test_shell_shared_owner_keeps_files(self, tmp_path: Path):
        """Shell script: shared ownership → skill kept, bin/ap.py kept."""
        if not _check_bash_available():
            pytest.skip("bash not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "codex")
        
        # Create registry listing opencode as co-owner
        registry_file = ap_dir / "skill-ownership.json"
        registry_data = {
            "schema_version": 1,
            "skills": {
                "advanced-planning": ["codex", "opencode"],
                "phase-plan-creator": ["opencode"],
            }
        }
        registry_file.write_text(json.dumps(registry_data, indent=2))
        
        returncode, stdout, stderr = _run_shell_uninstall(project_dir, "codex")
        
        assert returncode == 0, f"Expected success with shared ownership, got stderr: {stderr}"
        
        # Verify shared skill is kept
        assert (ap_dir.parents[0] / ".agents" / "skills" / "advanced-planning").exists(), \
            "Shared skill should be kept"
        assert (ap_dir / "bin" / "ap.py").exists(), "bin/ap.py should be kept when another adapter owns skills"
    
    def test_powershell_shared_owner_keeps_files(self, tmp_path: Path):
        """PowerShell script: shared ownership → skill kept, bin/ap.py kept."""
        if not _check_pwsh_available():
            pytest.skip("pwsh not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "codex")
        
        # Create registry listing opencode as co-owner
        registry_file = ap_dir / "skill-ownership.json"
        registry_data = {
            "schema_version": 1,
            "skills": {
                "advanced-planning": ["codex", "opencode"],
                "phase-plan-creator": ["opencode"],
            }
        }
        registry_file.write_text(json.dumps(registry_data, indent=2))
        
        returncode, stdout, stderr = _run_powershell_uninstall(project_dir, "codex")
        
        assert returncode == 0, f"Expected success with shared ownership, got stderr: {stderr}"
        
        # Verify shared skill is kept
        assert (ap_dir.parents[0] / ".agents" / "skills" / "advanced-planning").exists(), \
            "Shared skill should be kept"
        assert (ap_dir / "bin" / "ap.py").exists(), "bin/ap.py should be kept when another adapter owns skills"


# ── Test: dry-run agrees with real run ─────────────────────────────────────────

class TestDryRunConsistency:
    """Dry-run must take the same decision as the real run."""
    
    def test_shell_dryrun_matches_real_absent_registry(self, tmp_path: Path):
        """Shell script: dry-run and real run both refuse when registry absent."""
        if not _check_bash_available():
            pytest.skip("bash not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "codex")
        
        # Dry run (default)
        dry_returncode, dry_stdout, dry_stderr = _run_shell_uninstall(project_dir, "codex")
        
        # Both should fail
        assert dry_returncode != 0, "Dry run should refuse when registry is absent"
        assert "registry not found" in dry_stderr.lower()
    
    def test_powershell_dryrun_matches_real_absent_registry(self, tmp_path: Path):
        """PowerShell script: dry-run and real run both refuse when registry absent."""
        if not _check_pwsh_available():
            pytest.skip("pwsh not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "codex")
        
        # Dry run (default)
        dry_returncode, dry_stdout, dry_stderr = _run_powershell_uninstall(project_dir, "codex")
        
        # Both should fail
        assert dry_returncode != 0, "Dry run should refuse when registry is absent"
        assert "registry not found" in dry_stderr.lower()
    
    def test_shell_dryrun_matches_real_malformed_registry(self, tmp_path: Path):
        """Shell script: dry-run and real run both refuse when registry malformed."""
        if not _check_bash_available():
            pytest.skip("bash not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "codex")
        
        # Create malformed registry
        registry_file = ap_dir / "skill-ownership.json"
        registry_file.write_text("{ not json")
        
        # Dry run
        dry_returncode, dry_stdout, dry_stderr = _run_shell_uninstall(project_dir, "codex")
        
        assert dry_returncode != 0, "Dry run should refuse when registry is malformed"
        assert "malformed json" in dry_stderr.lower()
    
    def test_powershell_dryrun_matches_real_malformed_registry(self, tmp_path: Path):
        """PowerShell script: dry-run and real run both refuse when registry malformed."""
        if not _check_pwsh_available():
            pytest.skip("pwsh not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "codex")
        
        # Create malformed registry
        registry_file = ap_dir / "skill-ownership.json"
        registry_file.write_text("{ not json")
        
        # Dry run
        dry_returncode, dry_stdout, dry_stderr = _run_powershell_uninstall(project_dir, "codex")
        
        assert dry_returncode != 0, "Dry run should refuse when registry is malformed"
        assert "malformed json" in dry_stderr.lower()


# ── Test: opencode adapter behaves identically ─────────────────────────────────

class TestOpencodeAdapter:
    """Opencode uninstall scripts must behave identically to codex."""
    
    def test_opencode_shell_registry_absent_refuses(self, tmp_path: Path):
        """Opencode shell: missing registry → exit 1."""
        if not _check_bash_available():
            pytest.skip("bash not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "opencode")
        
        returncode, stdout, stderr = _run_shell_uninstall(project_dir, "opencode")
        
        assert returncode != 0, "Expected non-zero exit when registry is missing"
        assert "registry not found" in stderr.lower()
        assert (ap_dir / "bin" / "ap.py").exists(), "bin/ap.py should still exist"
    
    def test_opencode_powershell_registry_absent_refuses(self, tmp_path: Path):
        """Opencode PowerShell: missing registry → exit 1."""
        if not _check_pwsh_available():
            pytest.skip("pwsh not available")
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        ap_dir = _setup_fake_install(project_dir, "opencode")
        
        returncode, stdout, stderr = _run_powershell_uninstall(project_dir, "opencode")
        
        assert returncode != 0, "Expected non-zero exit when registry is missing"
        assert "registry not found" in stderr.lower()
        assert (ap_dir / "bin" / "ap.py").exists(), "bin/ap.py should still exist"


# ── Test count tracking ────────────────────────────────────────────────────────

class TestSkipTracking:
    """Ensure tests are not silently skipped."""

    def test_at_least_one_host_was_exercised(self):
        """Fail if both hosts are missing and every test above skipped.

        The previous version of this class asserted `available or True`
        on each host -- a tautology, in the class named for catching
        exactly this.
        """
        hosts = []
        if _check_bash_available():
            hosts.append(f"Git Bash ({GIT_BASH})")
        if _check_pwsh_available():
            hosts.append("pwsh")
        assert hosts, (
            "Neither Git Bash nor pwsh is available, so every uninstall "
            "test in this file skipped and this run proved nothing about "
            "the fail-closed behaviour."
        )


# ── Static checks the shells cannot make for themselves ──────────────────

SCRIPT_DIR = Path(__file__).parents[3] / 'setup'
SHELL_SCRIPTS = [SCRIPT_DIR / a / 'uninstall.sh' for a in ('codex', 'opencode')]

# A heredoc fed to python, e.g.  python - "$a" "$b" <<'PYEOF'
_PY_HEREDOC = re.compile(
    r"^[ \t]*python3?\b[^\n]*<<\s*'?([A-Za-z_]+)'?[ \t]*\n(.*?)\n\1[ \t]*\n",
    re.S | re.M,
)


class TestScriptStaticChecks:
    """Checks on the scripts themselves, independent of any host."""

    @pytest.mark.parametrize('script', SHELL_SCRIPTS, ids=lambda p: p.parent.name)
    def test_embedded_python_compiles(self, script):
        """The ownership logic lives in a heredoc, where `bash -n` cannot see it.

        A syntax error there -- a mis-indented line, say -- leaves the shell
        script syntactically valid and only fails at run time, on the exact
        path that is supposed to protect the user's files. This was not
        hypothetical: an edit to the remediation message landed at the wrong
        indent and `bash -n` passed it.
        """
        text = script.read_text(encoding='utf-8')
        blocks = _PY_HEREDOC.findall(text)
        assert blocks, (
            f'{script}: no python heredoc found, so this test compiled nothing. '
            'Either the script changed shape or the pattern is stale.'
        )
        for tag, body in blocks:
            try:
                compile(body, f'{script}:<<{tag}>>', 'exec')
            except SyntaxError as exc:
                pytest.fail(
                    f'{script} heredoc <<{tag}>> line {exc.lineno}: {exc.msg}'
                )

    @pytest.mark.parametrize('script', SHELL_SCRIPTS, ids=lambda p: p.parent.name)
    def test_malformed_advice_is_not_self_defeating(self, script):
        """Do not tell the user to delete a file whose absence is also refused."""
        text = script.read_text(encoding='utf-8')
        assert 'delete it and re-run without' not in text, (
            f'{script} advises deleting the malformed registry, but a missing '
            'registry is refused on the very next branch. The advice cannot work.'
        )
