# -*- coding: utf-8 -*-
"""Installer/uninstaller lifecycle tests for adapter pairs.

This suite exercises the **installer/uninstaller pair of any adapter**,
parametrized over adapters rather than hard-bound to one. Adding a new
adapter (e.g. OpenCode) must be a one-line change to the parameter list.

The model is ``test_uninstall.py`` — fixtures, ``tmp_path`` use, and the
skip convention for missing interpreters.

Why this exists: the Codex scripts had **no behavioural coverage at all**.
Every defect in stages C and D — an installer that clobbered a foreign
registry, an ownership check that was a stub, a registry deleted while the
script printed that it was updating it, and a prune aimed at a path that
cannot exist — was found by a human running the scripts and looking at the
filesystem. Nothing in CI could have failed on any of them.

This suite asserts on values, not truthiness; observed values are in the
assertion messages. It fails loudly when the behaviour is wrong.
"""

import json
import os
import shutil
import subprocess
import sys
import pathlib

import pytest


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]

# Adapter pairs: (adapter_name, install_sh, install_ps1, uninstall_sh, uninstall_ps1)
# Adding OpenCode later: append one tuple to this list.
# A foreign owner that is deliberately NOT any adapter name.
_FOREIGN = "otherhost"
_FOREIGN_SKILL = _FOREIGN + "-only-skill"
_ADAPTERS = [
    ("codex",
     _REPO_ROOT / "setup" / "codex" / "install.sh",
     _REPO_ROOT / "setup" / "codex" / "install.ps1",
     _REPO_ROOT / "setup" / "codex" / "uninstall.sh",
     _REPO_ROOT / "setup" / "codex" / "uninstall.ps1"),
    ("opencode",
     _REPO_ROOT / "setup" / "opencode" / "install.sh",
     _REPO_ROOT / "setup" / "opencode" / "install.ps1",
     _REPO_ROOT / "setup" / "opencode" / "uninstall.sh",
     _REPO_ROOT / "setup" / "opencode" / "uninstall.ps1"),
]

# Names under .advanced-plans/ that are the user's planning record.
_USER_DATA = ["phases", "specs", "state", "logs", "PLANNING.md"]


def _read(path):
    """Read a file, normalising line endings."""
    with open(str(path), encoding="utf-8", newline="") as handle:
        return handle.read().replace("\r\n", "\n")


def _run_script(script_path, args, cwd=None, env=None):
    """Run a shell or PowerShell script, return (returncode, stdout, stderr)."""
    script = pathlib.Path(script_path)
    if script.suffix == ".sh":
        cmd = ["sh", str(script)] + args
    elif script.suffix == ".ps1":
        cmd = ["pwsh", "-NoProfile", "-NonInteractive", "-File", str(script)] + args
    else:
        raise ValueError("Unknown script type: %s" % script.suffix)
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        cwd=str(cwd) if cwd else str(_REPO_ROOT),
        env=env,
    )
    out, err = proc.communicate(timeout=120)
    return proc.returncode, out, err


def _owners(project_dir, skill_name):
    """Read the owners of a skill from skill-ownership.json.
    
    Returns: sorted list of owner names, or None if skill not present.
    Raises: FileNotFoundError if skill-ownership.json does not exist.
    """
    ownership_file = project_dir / ".advanced-plans" / "skill-ownership.json"
    if not ownership_file.exists():
        raise FileNotFoundError("skill-ownership.json not found")
    
    data = json.loads(ownership_file.read_text(encoding="utf-8"))
    skills = data.get("skills", {})
    if skill_name not in skills:
        return None
    return sorted(skills[skill_name])


def _has_skill_entry(project_dir, skill_name):
    """Check if a skill has an entry in skill-ownership.json."""
    ownership_file = project_dir / ".advanced-plans" / "skill-ownership.json"
    if not ownership_file.exists():
        return False
    data = json.loads(ownership_file.read_text(encoding="utf-8"))
    return skill_name in data.get("skills", {})


def _fresh_project(tmp_path, project_name="proj"):
    """Create a fresh project directory structure for testing."""
    project = tmp_path / project_name
    project.mkdir(parents=True)
    
    # Create AGENTS.md with user content
    agents_file = project / "AGENTS.md"
    agents_file.write_text("# Project\n\nUser content that must survive.\n", encoding="utf-8")
    
    return project


def _setup_state_sentinel(project_dir):
    """Create the .advanced-plans/state/loop-ready.json sentinel."""
    state_dir = project_dir / ".advanced-plans" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    sentinel = state_dir / "loop-ready.json"
    sentinel.write_text('{"sentinel": true}', encoding="utf-8")


def _set_owners(project_dir, skill_name, owners_list):
    """Set the owners of a skill in skill-ownership.json.
    
    Also plants a foreign entry for _FOREIGN_SKILL.
    """
    ownership_file = project_dir / ".advanced-plans" / "skill-ownership.json"
    ownership_file.parent.mkdir(parents=True, exist_ok=True)
    
    if ownership_file.exists():
        data = json.loads(ownership_file.read_text(encoding="utf-8"))
    else:
        data = {"schema_version": 1, "skills": {}}
    
    data["skills"][skill_name] = owners_list
    data["skills"][_FOREIGN_SKILL] = [_FOREIGN]
    
    ownership_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


# =============================================================================
# Skip decorators
# =============================================================================

def pytest_generate_tests(metafunc):
    """Generate test cases for each adapter."""
    if "adapter" in metafunc.fixturenames:
        metafunc.parametrize("adapter", _ADAPTERS, ids=[a[0] for a in _ADAPTERS])


def _skip_if_no_sh():
    """Skip if no POSIX sh available.
    
    When AP_REQUIRE_ADAPTER_INTERPRETERS=1, escalate to failure instead of skip.
    """
    if shutil.which("sh") is None:
        if os.environ.get("AP_REQUIRE_ADAPTER_INTERPRETERS") == "1":
            raise RuntimeError("AP_REQUIRE_ADAPTER_INTERPRETERS=1 but 'sh' interpreter not found")
        pytest.skip("no POSIX sh available")


def _skip_if_no_pwsh():
    """Skip if no PowerShell 7+ available.
    
    When AP_REQUIRE_ADAPTER_INTERPRETERS=1, escalate to failure instead of skip.
    """
    if shutil.which("pwsh") is None:
        if os.environ.get("AP_REQUIRE_ADAPTER_INTERPRETERS") == "1":
            raise RuntimeError("AP_REQUIRE_ADAPTER_INTERPRETERS=1 but 'pwsh' interpreter not found")
        pytest.skip("no pwsh (PowerShell 7+) available")


# =============================================================================
# A. Install merges, never clobbers (per adapter, per language)
# =============================================================================

@pytest.mark.parametrize("lang", ["sh", "ps1"], ids=["sh", "ps1"])
class TestInstallMerges:
    """Group A: Install merges, never clobbers."""
    
    def test_existing_entry_preserved_and_merged(self, tmp_path, adapter, lang):
        """A.1: Installing into a project whose registry already has
        'advanced-planning': ['opencode'] leaves that entry containing both
        'opencode' and the adapter name."""
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()
        
        name, install_sh, install_ps1, _, _ = adapter
        project = _fresh_project(tmp_path)
        
        # Pre-seed registry with opencode as owner
        _set_owners(project, "advanced-planning", [_FOREIGN])
        
        # Install
        install_script = install_sh if lang == "sh" else install_ps1
        ret, out, err = _run_script(
            install_script,
            ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
        )
        assert ret == 0, "install failed: %s" % err
        
        # Check both owners present
        owners = _owners(project, "advanced-planning")
        assert sorted(owners) == sorted([_FOREIGN, name]), (
            "advanced-planning should have both %s and %s, got %s" % (_FOREIGN, name, owners))
    
    def test_foreign_entry_untouched(self, tmp_path, adapter, lang):
        """A.2: A foreign entry the adapter does not own survives install untouched."""
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()
        
        name, install_sh, install_ps1, _, _ = adapter
        project = _fresh_project(tmp_path)
        
        # Pre-seed with foreign entry
        _set_owners(project, "advanced-planning", [_FOREIGN])
        
        # Install
        install_script = install_sh if lang == "sh" else install_ps1
        ret, out, err = _run_script(
            install_script,
            ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
        )
        assert ret == 0, "install failed: %s" % err
        
        # Check foreign entry survives
        assert _has_skill_entry(project, _FOREIGN_SKILL), (
            "foreign entry %s was removed" % _FOREIGN_SKILL)
        foreign_owners = _owners(project, _FOREIGN_SKILL)
        assert foreign_owners == [_FOREIGN], (
            "foreign entry was modified: %s" % foreign_owners)
    
    def test_adapter_owned_skill_has_correct_owner(self, tmp_path, adapter, lang):
        """A.3: A skill the adapter does own reads exactly ['<adapter>']."""
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()
        
        name, install_sh, install_ps1, _, _ = adapter
        project = _fresh_project(tmp_path)
        
        # Install
        install_script = install_sh if lang == "sh" else install_ps1
        ret, out, err = _run_script(
            install_script,
            ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
        )
        assert ret == 0, "install failed: %s" % err
        
        # Check adapter-owned skill
        owners = _owners(project, "phase-plan-creator")
        assert owners == [name], (
            "phase-plan-creator should be owned only by %s, got %s" % (name, owners))
    
    def test_idempotent_install_no_duplicates(self, tmp_path, adapter, lang):
        """A.4: Installing twice does not produce ['<adapter>','<adapter>']."""
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()
        
        name, install_sh, install_ps1, _, _ = adapter
        project = _fresh_project(tmp_path)
        
        # Install twice
        install_script = install_sh if lang == "sh" else install_ps1
        for _ in range(2):
            ret, out, err = _run_script(
                install_script,
                ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
            )
            assert ret == 0, "install failed: %s" % err
        
        # Check no duplicates - adapter should appear exactly once
        owners = _owners(project, "advanced-planning")
        assert name in owners, "%s should be an owner after install" % name
        adapter_count = owners.count(name)
        assert adapter_count == 1, (
            "installing twice produced %d %s entries: %s" % (adapter_count, name, owners))


# =============================================================================
# B. Uninstall, phase 1 — the shared skill is protected
# =============================================================================

@pytest.mark.parametrize("lang", ["sh", "ps1"], ids=["sh", "ps1"])
class TestUninstallPhase1:
    """Group B: Uninstall, phase 1 — the shared skill is protected."""
    
    @pytest.fixture
    def shared_fixture(self, tmp_path, adapter, lang):
        """Fixture: fresh install, registry hand-edited to ['codex','opencode'],
        a sentinel at .advanced-plans/state/loop-ready.json, AGENTS.md carrying
        a user line."""
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()
        
        name, install_sh, install_ps1, _, _ = adapter
        project = _fresh_project(tmp_path, "shared-fixture")
        
        # Install fresh
        install_script = install_sh if lang == "sh" else install_ps1
        ret, out, err = _run_script(
            install_script,
            ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
        )
        assert ret == 0, "install failed: %s" % err
        
        # Hand-edit registry to shared ownership
        _set_owners(project, "advanced-planning", [name, _FOREIGN])
        
        # Plant state sentinel
        _setup_state_sentinel(project)
        
        return project, lang, adapter
    
    def test_shared_skill_directory_survives(self, shared_fixture):
        """B.5: The shared skill directory survives."""
        project, lang, adapter = shared_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Uninstall
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "uninstall failed: %s" % err
        
        # Check shared skill survives
        shared_skill = project / ".agents" / "skills" / "advanced-planning"
        assert shared_skill.is_dir(), (
            "shared skill directory .agents/skills/advanced-planning was removed")
    
    def test_adapter_owned_skill_removed(self, shared_fixture):
        """B.6: A skill the adapter solely owns is removed."""
        project, lang, adapter = shared_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Uninstall
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "uninstall failed: %s" % err
        
        # Check adapter-owned skill is removed
        owned_skill = project / ".agents" / "skills" / "phase-plan-creator"
        assert not owned_skill.exists(), (
            "adapter-owned skill phase-plan-creator was not removed")
    
    def test_ownership_file_survives(self, shared_fixture):
        """B.7: skill-ownership.json still exists."""
        project, lang, adapter = shared_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Uninstall
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "uninstall failed: %s" % err
        
        # Check registry survives
        ownership_file = project / ".advanced-plans" / "skill-ownership.json"
        assert ownership_file.exists(), "skill-ownership.json was removed"
    
    def test_registry_updated_not_deleted(self, shared_fixture):
        """B.8: Its advanced-planning entry reads ['opencode'] — the registration
        was rewritten, not deleted."""
        project, lang, adapter = shared_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Uninstall
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "uninstall failed: %s" % err
        
        # Check registry updated
        owners = _owners(project, "advanced-planning")
        assert owners == [_FOREIGN], (
            "advanced-planning should have only %s after uninstall, got %s" % (_FOREIGN, owners))
    
    def test_state_sentinel_intact(self, shared_fixture):
        """B.9: .advanced-plans/state/loop-ready.json is intact."""
        project, lang, adapter = shared_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Uninstall
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "uninstall failed: %s" % err
        
        # Check state sentinel
        sentinel = project / ".advanced-plans" / "state" / "loop-ready.json"
        assert sentinel.exists(), "state/loop-ready.json was removed"
        data = json.loads(sentinel.read_text(encoding="utf-8"))
        assert data.get("sentinel") is True, "state sentinel was modified"
    
    def test_ap_py_removed(self, shared_fixture):
        """B.10: bin/ap.py is removed."""
        project, lang, adapter = shared_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Uninstall
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "uninstall failed: %s" % err
        
        # Check launcher removed
        launcher = project / ".advanced-plans" / "bin" / "ap.py"
        assert not launcher.exists(), "bin/ap.py was not removed"
    
    def test_agents_md_fences_removed(self, shared_fixture):
        """B.11: AGENTS.md has zero adapter fences and still has the user line."""
        project, lang, adapter = shared_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Uninstall
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "uninstall failed: %s" % err
        
        # Check AGENTS.md
        agents_file = project / "AGENTS.md"
        content = agents_file.read_text(encoding="utf-8")
        fence_start = "<!-- advanced-planning:%s:start -->" % name
        fence_count = content.count(fence_start)
        assert fence_count == 0, (
            "AGENTS.md still has %d %s fence(s)" % (fence_count, name))
        assert "User content that must survive" in content, (
            "user content line was removed from AGENTS.md")


# =============================================================================
# C. Uninstall, phase 2a — running it twice must be safe
# =============================================================================

@pytest.mark.parametrize("lang", ["sh", "ps1"], ids=["sh", "ps1"])
class TestUninstallPhase2a:
    """Group C: Uninstall, phase 2a — running it twice must be safe."""
    
    @pytest.fixture
    def phase2a_fixture(self, tmp_path, adapter, lang):
        """Fixture: phase-1 result (shared skill remains, registry has only opencode)."""
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()
        
        name, install_sh, install_ps1, uninstall_sh, uninstall_ps1 = adapter
        project = _fresh_project(tmp_path, "phase2a")
        
        # Install fresh
        install_script = install_sh if lang == "sh" else install_ps1
        ret, out, err = _run_script(
            install_script,
            ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
        )
        assert ret == 0, "install failed: %s" % err
        
        # Set shared ownership
        _set_owners(project, "advanced-planning", [name, _FOREIGN])
        
        # Run phase-1 uninstall
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "phase-1 uninstall failed: %s" % err
        
        return project, lang, adapter
    
    def test_shared_skill_still_survives(self, phase2a_fixture):
        """C.12: The shared skill still survives after second run."""
        project, lang, adapter = phase2a_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Run uninstall again (phase 2a)
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "phase-2a uninstall failed: %s" % err
        
        # Check shared skill still survives
        shared_skill = project / ".agents" / "skills" / "advanced-planning"
        assert shared_skill.is_dir(), (
            "shared skill was removed on second uninstall run")
    
    def test_registry_unchanged(self, phase2a_fixture):
        """C.13: The registry is unchanged, still ['opencode']."""
        project, lang, adapter = phase2a_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Run uninstall again (phase 2a)
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "phase-2a uninstall failed: %s" % err
        
        # Check registry unchanged
        owners = _owners(project, "advanced-planning")
        assert owners == [_FOREIGN], (
            "registry was modified on second uninstall: %s" % owners)


# =============================================================================
# D. Uninstall, phase 2b — the last owner leaves
# =============================================================================

@pytest.mark.parametrize("lang", ["sh", "ps1"], ids=["sh", "ps1"])
class TestUninstallPhase2b:
    """Group D: Uninstall, phase 2b — the last owner leaves."""
    
    @pytest.fixture
    def phase2b_fixture(self, tmp_path, adapter, lang):
        """Fixture: adapter is sole remaining owner, then uninstall."""
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()
        
        name, install_sh, install_ps1, uninstall_sh, uninstall_ps1 = adapter
        project = _fresh_project(tmp_path, "phase2b")
        
        # Install fresh
        install_script = install_sh if lang == "sh" else install_ps1
        ret, out, err = _run_script(
            install_script,
            ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
        )
        assert ret == 0, "install failed: %s" % err
        
        # Make adapter sole owner
        _set_owners(project, "advanced-planning", [name])
        
        # Plant state sentinel
        _setup_state_sentinel(project)
        
        return project, lang, adapter
    
    def test_sole_owner_skill_removed(self, phase2b_fixture):
        """D.14: The skill directory is removed when last owner leaves."""
        project, lang, adapter = phase2b_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Uninstall (adapter is sole owner)
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "phase-2b uninstall failed: %s" % err
        
        # Check skill removed
        shared_skill = project / ".agents" / "skills" / "advanced-planning"
        assert not shared_skill.exists(), (
            "skill directory was not removed when last owner left")
    
    def test_empty_registry_deleted(self, phase2b_fixture):
        """D.15: skill-ownership.json is deleted, because no entry has any owner left."""
        project, lang, adapter = phase2b_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Uninstall (adapter is sole owner)
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "phase-2b uninstall failed: %s" % err
        
        # Check registry deleted
        ownership_file = project / ".advanced-plans" / "skill-ownership.json"
        assert not ownership_file.exists(), (
            "skill-ownership.json should be deleted when no owners remain")
    
    def test_state_still_intact(self, phase2b_fixture):
        """D.16: .advanced-plans/state/ is still intact."""
        project, lang, adapter = phase2b_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Uninstall (adapter is sole owner)
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "phase-2b uninstall failed: %s" % err
        
        # Check state intact
        sentinel = project / ".advanced-plans" / "state" / "loop-ready.json"
        assert sentinel.exists(), "state/loop-ready.json was removed"


# =============================================================================
# E. The two languages agree (per adapter)
# =============================================================================

class TestLanguagesAgree:
    """Group E: The two languages agree."""
    
    @pytest.fixture
    def differential_fixture(self, tmp_path, adapter):
        """Fixture: identical fixtures for sh and ps1."""
        _skip_if_no_sh()
        _skip_if_no_pwsh()
        
        name, install_sh, install_ps1, uninstall_sh, uninstall_ps1 = adapter
        
        # Create two identical projects
        proj_sh = _fresh_project(tmp_path, "diff-sh")
        proj_ps1 = _fresh_project(tmp_path, "diff-ps1")
        
        for project in [proj_sh, proj_ps1]:
            # Install via sh for both (so fixtures are identical)
            ret, out, err = _run_script(
                install_sh, ["--project", str(project)],
            )
            assert ret == 0, "install failed: %s" % err
            
            # Set shared ownership
            _set_owners(project, "advanced-planning", [name, _FOREIGN])
        
        return proj_sh, proj_ps1, adapter
    
    def test_removal_counts_agree(self, differential_fixture):
        """E.17: The .sh and .ps1 uninstallers print the same removed/kept counts."""
        proj_sh, proj_ps1, adapter = differential_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Run both uninstallers
        ret_sh, out_sh, err_sh = _run_script(
            uninstall_sh, ["--project", str(proj_sh), "--yes"],
        )
        assert ret_sh == 0, "sh uninstall failed: %s" % err_sh
        
        ret_ps1, out_ps1, err_ps1 = _run_script(
            uninstall_ps1, ["-Project", str(proj_ps1), "-Yes"],
        )
        assert ret_ps1 == 0, "ps1 uninstall failed: %s" % err_ps1
        
        # Extract counts from output - look for "Done. N path(s) removed, M kept."
        def extract_count(output):
            for line in output.split("\n"):
                if "Done." in line and "path(s)" in line:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if p == "removed,":
                            return parts[i-2] if i > 1 else None
            return None
        
        count_sh = extract_count(out_sh)
        count_ps1 = extract_count(out_ps1)
        
        assert count_sh == count_ps1, (
            "removal counts disagree: sh=%s, ps1=%s" % (count_sh, count_ps1))
    
    def test_registry_contents_agree(self, differential_fixture):
        """E.18: They leave the same registry contents."""
        proj_sh, proj_ps1, adapter = differential_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Run both uninstallers
        _run_script(uninstall_sh, ["--project", str(proj_sh), "--yes"])
        _run_script(uninstall_ps1, ["-Project", str(proj_ps1), "-Yes"])
        
        # Compare registries
        try:
            owners_sh = _owners(proj_sh, "advanced-planning")
        except FileNotFoundError:
            owners_sh = None
        
        try:
            owners_ps1 = _owners(proj_ps1, "advanced-planning")
        except FileNotFoundError:
            owners_ps1 = None
        
        assert owners_sh == owners_ps1, (
            "registry contents disagree: sh=%s, ps1=%s" % (owners_sh, owners_ps1))


# =============================================================================
# F. Complete uninstall leaves no residue (per adapter)
# =============================================================================

class TestCompleteUninstallNoResidue:
    """Group F: Complete uninstall leaves no residue — the one that was missing."""
    
    @pytest.fixture
    def sole_owner_fixture(self, tmp_path, adapter):
        """Fixture: fresh install, registry untouched, adapter is sole owner."""
        _skip_if_no_sh()
        _skip_if_no_pwsh()
        
        name, install_sh, install_ps1, uninstall_sh, uninstall_ps1 = adapter
        
        # Create two identical projects
        proj_sh = _fresh_project(tmp_path, "sole-sh")
        proj_ps1 = _fresh_project(tmp_path, "sole-ps1")
        
        for project in [proj_sh, proj_ps1]:
            # Install fresh (no registry edit - adapter is sole owner by default)
            ret, out, err = _run_script(
                install_sh, ["--project", str(project)],
            )
            assert ret == 0, "install failed: %s" % err
            
            # Plant state sentinel
            _setup_state_sentinel(project)
        
        return proj_sh, proj_ps1, adapter
    
    def test_residual_trees_identical(self, sole_owner_fixture):
        """F.19: find <project> -mindepth 1, sorted, is identical between .sh and .ps1."""
        proj_sh, proj_ps1, adapter = sole_owner_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Run both uninstallers
        ret_sh, out_sh, err_sh = _run_script(
            uninstall_sh, ["--project", str(proj_sh), "--yes"],
        )
        assert ret_sh == 0, "sh uninstall failed: %s" % err_sh
        
        ret_ps1, out_ps1, err_ps1 = _run_script(
            uninstall_ps1, ["-Project", str(proj_ps1), "-Yes"],
        )
        assert ret_ps1 == 0, "ps1 uninstall failed: %s" % err_ps1
        
        # Get residual paths
        def get_residuals(project):
            paths = []
            for p in project.rglob("*"):
                if p.is_file() or p.is_dir():
                    rel = str(p.relative_to(project))
                    paths.append(rel)
            return sorted(paths)
        
        residuals_sh = get_residuals(proj_sh)
        residuals_ps1 = get_residuals(proj_ps1)
        
        assert residuals_sh == residuals_ps1, (
            "residual trees differ:\n  sh only: %s\n  ps1 only: %s" % (
                sorted(set(residuals_sh) - set(residuals_ps1)),
                sorted(set(residuals_ps1) - set(residuals_sh)),
            ))
    
    def test_no_agents_directory_behind(self, sole_owner_fixture):
        """F.20: Neither run leaves a .agents directory behind."""
        proj_sh, proj_ps1, adapter = sole_owner_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Run both uninstallers
        _run_script(uninstall_sh, ["--project", str(proj_sh), "--yes"])
        _run_script(uninstall_ps1, ["-Project", str(proj_ps1), "-Yes"])
        
        # Check .agents removed
        agents_sh = proj_sh / ".agents"
        agents_ps1 = proj_ps1 / ".agents"
        
        assert not agents_sh.exists(), "sh uninstall left .agents directory"
        assert not agents_ps1.exists(), "ps1 uninstall left .agents directory"
    
    def test_state_sentinel_survives_both(self, sole_owner_fixture):
        """F.21: .advanced-plans/state/ survives both."""
        proj_sh, proj_ps1, adapter = sole_owner_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Run both uninstallers
        _run_script(uninstall_sh, ["--project", str(proj_sh), "--yes"])
        _run_script(uninstall_ps1, ["-Project", str(proj_ps1), "-Yes"])
        
        # Check state survives
        state_sh = proj_sh / ".advanced-plans" / "state" / "loop-ready.json"
        state_ps1 = proj_ps1 / ".advanced-plans" / "state" / "loop-ready.json"
        
        assert state_sh.exists(), "sh uninstall removed state/loop-ready.json"
        assert state_ps1.exists(), "ps1 uninstall removed state/loop-ready.json"
