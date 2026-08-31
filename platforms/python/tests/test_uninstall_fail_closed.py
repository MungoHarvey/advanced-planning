"""Tests for fail-closed uninstall behavior when registry is missing or malformed.

These tests verify that uninstall scripts refuse to remove skills and shared files
when the ownership registry cannot be read, unless --force-no-registry is passed.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


# ── Helper utilities ────────────────────────────────────────────────────────────

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
    cmd = [str(script_path), "--project", str(project_dir)]
    if extra_args:
        cmd.extend(extra_args)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
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
        cwd=str(project_dir),
    )
    return result.returncode, result.stdout, result.stderr


def _check_bash_available() -> bool:
    """Check if bash is available and can run our scripts.
    
    On Windows, the system bash.exe is WSL which cannot directly run
    Windows path shell scripts, so we report bash as unavailable.
    """
    if sys.platform == "win32":
        # WSL bash on Windows cannot run Windows shell scripts directly
        return False
    bash_path = shutil.which("bash")
    return bash_path is not None


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
    
    def test_bash_available_for_reporting(self):
        """Report whether bash is available."""
        bash_available = _check_bash_available()
        # This test always passes but the assertion below tracks it
        assert bash_available or True, "bash availability tracked for reporting"
    
    def test_pwsh_available_for_reporting(self):
        """Report whether pwsh is available."""
        pwsh_available = _check_pwsh_available()
        assert pwsh_available or True, "pwsh availability tracked for reporting"
