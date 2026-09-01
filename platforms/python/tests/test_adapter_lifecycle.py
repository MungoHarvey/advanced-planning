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
import re
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


def _parse_removed_count(output, label):
    """Parse the removed count out of an uninstaller's "Done." line.

    The count is the token immediately before "path(s)".  Anchoring there
    reads every shipped wording -- codex and opencode print
    "Done. N path(s) removed, M kept.", claude-code prints
    "Done. N path(s) removed." -- without grabbing an unrelated digit that
    happens to appear earlier on the line.

    Raises rather than returning None.  The nested helper this replaces
    anchored on the literal token "removed," and returned None when it was
    absent, so a wording change made both sides None and the differential
    assertion compared nothing.
    """
    saw_done = False
    for line in output.split("\n"):
        if "Done." not in line:
            continue
        saw_done = True
        tokens = line.split()
        for i, token in enumerate(tokens):
            if token == "path(s)" and i > 0 and tokens[i - 1].isdigit():
                return int(tokens[i - 1])
    if saw_done:
        raise AssertionError(
            "%s: a 'Done.' line was printed but carried no 'N path(s)' "
            "count, so this differential test would otherwise compare "
            "nothing. Output was:\n%s" % (label, output))
    raise AssertionError(
        "%s: no 'Done. N path(s)' line in uninstaller output; the wording "
        "changed and this differential test would otherwise compare "
        "nothing. Output was:\n%s" % (label, output))


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
    
    def test_ap_py_survives_for_the_other_adapter(self, shared_fixture):
        """B.10: bin/ap.py SURVIVES while another adapter still owns a skill.

        B.5, B.7 and B.8 above establish that the other adapter's skill and
        its registration outlive this uninstall.  Every one of those skills
        invokes .advanced-plans/bin/ap.py, so removing the launcher here
        would leave that adapter installed but inert.
        """
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
        assert launcher.exists(), (
            "bin/ap.py was removed while %s still owns advanced-planning; "
            "that adapter is now installed but inert" % _FOREIGN)
        runtime = project / ".advanced-plans" / "runtime.json"
        assert runtime.exists(), (
            "runtime.json was removed while %s still owns advanced-planning"
            % _FOREIGN)
    
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
        
        # A fresh single-adapter install already registers this adapter as
        # sole owner of every approved skill, so nothing needs forcing here.
        # This called _set_owners until F4, which plants a foreign entry as a
        # side effect -- so D.15 below asserted "no entry has any owner left"
        # against a registry that still had one, and passed only because the
        # file was being deleted with that entry inside it.  That deletion is
        # the defect; a genuinely empty registry is what D.15 means to test.
        
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
        count_sh = _parse_removed_count(out_sh, "sh")
        count_ps1 = _parse_removed_count(out_ps1, "ps1")
        
        assert count_sh == count_ps1, (
            "removal counts disagree: sh=%s, ps1=%s" % (count_sh, count_ps1))
    
    def test_registry_contents_agree(self, differential_fixture):
        """E.18: They leave the same registry contents."""
        proj_sh, proj_ps1, adapter = differential_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter
        
        # Run both uninstallers and assert they succeeded
        ret_sh, out_sh, err_sh = _run_script(
            uninstall_sh, ["--project", str(proj_sh), "--yes"],
        )
        assert ret_sh == 0, "sh uninstall failed: %s" % err_sh
        
        ret_ps1, out_ps1, err_ps1 = _run_script(
            uninstall_ps1, ["-Project", str(proj_ps1), "-Yes"],
        )
        assert ret_ps1 == 0, "ps1 uninstall failed: %s" % err_ps1
        
        # Compare registries
        try:
            owners_sh = _owners(proj_sh, "advanced-planning")
        except FileNotFoundError:
            owners_sh = None
        
        try:
            owners_ps1 = _owners(proj_ps1, "advanced-planning")
        except FileNotFoundError:
            owners_ps1 = None
        
        # Both-absent is now a meaningful agreement because both uninstallers
        # are known to have succeeded (ret == 0 asserted above).
        assert owners_sh == owners_ps1, (
            "registry contents disagree: sh=%s, ps1=%s" % (owners_sh, owners_ps1))
    
    def test_removed_count_parser_rejects_missing_wording(self):
        """E.19: the count parser must raise, not return None, when the wording is absent."""
        # Both shipped wordings parse.  claude-code omits the ", M kept."
        # clause and is absent from _ADAPTERS, so this pins the parser
        # against an adapter the suite does not otherwise exercise.
        assert _parse_removed_count("Done. 7 path(s) removed, 2 kept.", "x") == 7
        assert _parse_removed_count("Done. 7 path(s) removed.", "x") == 7
        assert _parse_removed_count("Done. 0 path(s) removed, 8 kept.", "x") == 0
        
        # The count is the token before "path(s)", not merely the first
        # digit on the line.  A looser parser returns 9 here, and nothing
        # in the suite would see it.
        assert _parse_removed_count(
            "Done. Pruned 9 entries; 7 path(s) removed, 2 kept.", "x") == 7
        
        # Absent wording raises rather than returning None.
        for absent in ("", "Removed 7 things.\n",
                       "Uninstall finished.\n"):
            with pytest.raises(AssertionError) as exc_info:
                _parse_removed_count(absent, "x")
            assert "compare nothing" in str(exc_info.value)
        
        # A Done. line carrying no count raises too -- the branch a parser
        # that guessed at the first digit would never reach.
        with pytest.raises(AssertionError) as exc_info:
            _parse_removed_count("Done. all path(s) removed.\n", "x")
        assert "compare nothing" in str(exc_info.value)


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

    def test_launcher_removed_when_sole_owner(self, sole_owner_fixture):
        """F.22: the sole owner still takes bin/ap.py and runtime.json with it.

        The opposite direction of B.10.  Without this, a guard that never fires
        -- keeping the launcher unconditionally -- would leave the repository
        with no failing test.
        """
        proj_sh, proj_ps1, adapter = sole_owner_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter

        ret_sh, out_sh, err_sh = _run_script(
            uninstall_sh, ["--project", str(proj_sh), "--yes"])
        assert ret_sh == 0, "sh uninstall failed: %s" % err_sh
        ret_ps1, out_ps1, err_ps1 = _run_script(
            uninstall_ps1, ["-Project", str(proj_ps1), "-Yes"])
        assert ret_ps1 == 0, "ps1 uninstall failed: %s" % err_ps1

        for label, project in (("sh", proj_sh), ("ps1", proj_ps1)):
            launcher = project / ".advanced-plans" / "bin" / "ap.py"
            runtime = project / ".advanced-plans" / "runtime.json"
            assert not launcher.exists(), (
                "%s uninstall left bin/ap.py behind with no remaining owner"
                % label)
            assert not runtime.exists(), (
                "%s uninstall left runtime.json behind with no remaining owner"
                % label)

class TestGlobalDualAdapterInstall:
    """G.1-G.2: both adapters install --global into one profile and share it.

    Nothing else in this suite passes --global, and nothing anywhere compares
    one adapter's installed output against the other's, so this path had no
    coverage at all.  It was broken: --global rewrites the COPIED markdown to
    an absolute launcher, and the next adapter to install then compared the raw
    repo source against that rewritten copy, called it a fork, and exited 1.
    The two adapters rewrite to the same launcher, so they do agree -- the
    comparison was of the wrong two things.
    """

    def _install_global(self, lang, home, adapter):
        name, install_sh, install_ps1, _, _ = adapter
        env = dict(os.environ)
        # USERPROFILE first: that is the order both installers resolve in.
        env["USERPROFILE"] = str(home)
        env["HOME"] = str(home)
        if lang == "sh":
            return _run_script(install_sh, ["--global"], env=env)
        return _run_script(install_ps1, ["-Global"], env=env)

    @pytest.mark.parametrize("lang", ["sh", "ps1"])
    def test_second_adapter_shares_the_global_skill(self, tmp_path, lang):
        """G.1: the second --global install succeeds and both owners are recorded."""
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()
        home = tmp_path / "profile"
        home.mkdir()

        first, second = _ADAPTERS[0], _ADAPTERS[1]

        ret, out, err = self._install_global(lang, home, first)
        assert ret == 0, "first global install (%s) failed: %s" % (
            first[0], err or out)

        ret, out, err = self._install_global(lang, home, second)
        assert ret == 0, (
            "second global install (%s) exited %d. The first adapter rewrote "
            "the shared skill's call sites, so comparing the raw repo source "
            "against the installed copy reports a fork that is not one:\n%s"
            % (second[0], ret, err or out))

        # Exit 0 alone would also be satisfied by silently overwriting the
        # first adapter's copy, so require the installer to say it shared.
        assert "shared; unchanged: advanced-planning" in out, (
            "second global install did not report sharing the skill:\n%s" % out)

        owners = _owners(home, "advanced-planning")
        assert owners == sorted([first[0], second[0]]), (
            "global ownership is %r, expected both adapters" % (owners,))

    @pytest.mark.parametrize("lang", ["sh", "ps1"])
    def test_global_skill_keeps_an_absolute_launcher(self, tmp_path, lang):
        """G.2: sharing must not be bought by dropping the rewrite.

        A global skill is read from whatever directory the agent is working in,
        so a relative `.advanced-plans/bin/ap.py` call site would not resolve.
        Deleting the rewrite would make G.1 pass and leave every global install
        inert, so assert the installed call sites are absolute.  This is the
        direction that keeps G.1 from passing vacuously.
        """
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()
        home = tmp_path / "profile"
        home.mkdir()

        ret, out, err = self._install_global(lang, home, _ADAPTERS[0])
        assert ret == 0, "global install failed: %s" % (err or out)

        skill_md = home / ".agents" / "skills" / "advanced-planning" / "SKILL.md"
        assert skill_md.exists(), "global install left no SKILL.md"
        text = _read(skill_md)

        # Both installers emit forward slashes for the embedded path.
        expected = str(home).replace("\\", "/") + "/.advanced-plans/bin/ap.py"
        assert expected in text, (
            "installed SKILL.md does not call the absolute launcher %s" % expected)
        assert 'python ".advanced-plans/bin/ap.py"' not in text, (
            "installed SKILL.md still has a project-relative call site, which "
            "cannot resolve when the skill is invoked from another directory")


# =============================================================================
# H. Nested file collision detection — sh and ps1 agree
# =============================================================================

class TestNestedCollisionDetection:
    """H.1-H.2: check_collision walks the source tree recursively.

    The defect: sh's check_collision iterated only top-level files
    (`for _src_file in "$_src"/*`), while PowerShell's Test-ApCollision
    used `Get-ChildItem -Recurse`. The shared skill has a references/
    subdirectory. Those nested files ARE installed and rewritten by
    --global, but on POSIX they were never compared, so a divergent
    nested file installed silently. This test proves both languages
    now detect the same collision.
    """

    @pytest.mark.parametrize("lang", ["sh", "ps1"])
    def test_nested_file_divergence_detected(self, tmp_path, adapter, lang):
        """H.1: modifying an installed references/*.md file is detected."""
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()

        name, install_sh, install_ps1, _, _ = adapter
        project = _fresh_project(tmp_path, "nested-collision")

        # Install fresh
        install_script = install_sh if lang == "sh" else install_ps1
        ret, out, err = _run_script(
            install_script,
            ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
        )
        assert ret == 0, "install failed: %s" % err

        # Modify a nested file in the installed skill
        nested_file = project / ".agents" / "skills" / "advanced-planning" / "references" / "orchestrator-prompt.md"
        assert nested_file.exists(), "nested file references/orchestrator-prompt.md was not installed"
        original_content = _read(nested_file)
        nested_file.write_text(original_content + "\n\nMODIFIED FOR TEST", encoding="utf-8")

        # Run installer again - should fail with collision error
        ret, out, err = _run_script(
            install_script,
            ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
        )
        assert ret != 0, (
            "installer exited 0 despite nested file divergence - sh is not walking recursively")
        assert "collision" in (err + out).lower(), (
            "installer failed but did not report collision:\nstdout: %s\nstderr: %s" % (out, err))
        assert "references/orchestrator-prompt.md" in (err + out) or "orchestrator-prompt.md" in (err + out), (
            "collision error did not name the nested file:\nstdout: %s\nstderr: %s" % (out, err))

    @pytest.mark.parametrize("lang", ["sh", "ps1"])
    def test_nested_file_identical_shared_unchanged(self, tmp_path, adapter, lang):
        """H.2: unmodified nested files report 'shared; unchanged'."""
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()

        name, install_sh, install_ps1, _, _ = adapter
        project = _fresh_project(tmp_path, "nested-same")

        # Install fresh
        install_script = install_sh if lang == "sh" else install_ps1
        ret, out, err = _run_script(
            install_script,
            ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
        )
        assert ret == 0, "install failed: %s" % err

        # Run installer again without modification - should report shared; unchanged
        ret, out, err = _run_script(
            install_script,
            ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
        )
        assert ret == 0, (
            "installer exited non-zero despite no changes:\nstdout: %s\nstderr: %s" % (out, err))
        # The check_collision function says "shared; unchanged" for identical skills
        assert "shared; unchanged" in out, (
            "installer did not report 'shared; unchanged' for identical nested files:\nstdout: %s" % out)


# =============================================================================
# I. Third-party registration survives sole-owner uninstall
# =============================================================================

class TestThirdPartySurvivesSoleOwnerUninstall:
    """I.1-I.4: a foreign adapter's skill registration survives uninstall
    when this adapter is sole owner of every approved skill, whether that
    registration is well formed (I.1-I.3) or malformed (I.4).

    The defect: any_remaining was set True ONLY when an approved skill still
    had owners after removal. So when this adapter was sole owner of every
    approved skill, any_remaining was False and the ownership file was deleted,
    destroying third-party registrations. The foreign skill's files survive
    (only approved skills are removed), leaving it installed but unregistered.
    """

    @pytest.fixture
    def sole_owner_with_foreign_fixture(self, tmp_path, adapter, lang):
        """Fixture: adapter is sole owner of every approved skill, but a
        third-party entry exists in the registry."""
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()

        name, install_sh, install_ps1, uninstall_sh, uninstall_ps1 = adapter
        project = _fresh_project(tmp_path, "sole-with-foreign")

        # Install fresh
        install_script = install_sh if lang == "sh" else install_ps1
        ret, out, err = _run_script(
            install_script,
            ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
        )
        assert ret == 0, "install failed: %s" % err

        # The install already made this adapter sole owner of every approved
        # skill.  Take the list from the registry it wrote rather than
        # restating it here, so this cannot drift from the installers, and
        # assert the sole ownership the whole test depends on.
        ownership_file = project / ".advanced-plans" / "skill-ownership.json"
        data = json.loads(ownership_file.read_text(encoding="utf-8"))
        approved_before = sorted(data["skills"])
        assert approved_before, "install registered no skills; fixture is vacuous"
        for skill in approved_before:
            assert data["skills"][skill] == [name], (
                "fixture needs sole ownership, but %s is owned by %s"
                % (skill, data["skills"][skill]))

        # Plant the third-party entry explicitly.  _set_owners does this as a
        # side effect, which is precisely how D.15 came to assert the defect.
        data["skills"][_FOREIGN_SKILL] = [_FOREIGN]
        ownership_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Plant state sentinel
        _setup_state_sentinel(project)

        return project, lang, adapter, approved_before

    @pytest.mark.parametrize("lang", ["sh", "ps1"], ids=["sh", "ps1"])
    def test_foreign_registration_survives(self, sole_owner_with_foreign_fixture):
        """I.1: the ownership file still exists and the foreign entry is preserved."""
        project, lang, adapter, approved_before = sole_owner_with_foreign_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter

        # Uninstall
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "uninstall failed: %s" % err

        # Ownership file must still exist
        ownership_file = project / ".advanced-plans" / "skill-ownership.json"
        assert ownership_file.exists(), (
            "skill-ownership.json was deleted despite third-party entry")

        # Foreign entry must be preserved
        assert _has_skill_entry(project, _FOREIGN_SKILL), (
            "foreign entry %s was removed" % _FOREIGN_SKILL)
        foreign_owners = _owners(project, _FOREIGN_SKILL)
        assert foreign_owners == [_FOREIGN], (
            "foreign entry was modified: expected [%s], got %s" % (_FOREIGN, foreign_owners))

    @pytest.mark.parametrize("lang", ["sh", "ps1"], ids=["sh", "ps1"])
    def test_approved_skills_removed_from_registry(self, sole_owner_with_foreign_fixture):
        """I.2: the adapter's own approved skills are gone from the registry."""
        project, lang, adapter, approved_before = sole_owner_with_foreign_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter

        # Uninstall
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "uninstall failed: %s" % err

        # Adapter's approved skills should be gone from the registry.
        # The list is what the install actually registered, read in the fixture.
        ownership_file = project / ".advanced-plans" / "skill-ownership.json"
        data = json.loads(ownership_file.read_text(encoding="utf-8"))
        for skill in approved_before:
            assert skill not in data["skills"], (
                "approved skill %s should be removed from registry" % skill)

    @pytest.mark.parametrize("lang", ["sh", "ps1"], ids=["sh", "ps1"])
    def test_only_foreign_entry_remains(self, sole_owner_with_foreign_fixture):
        """I.3: only the foreign entry remains in the registry."""
        project, lang, adapter, approved_before = sole_owner_with_foreign_fixture
        name, _, _, uninstall_sh, uninstall_ps1 = adapter

        # Uninstall
        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh" else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "uninstall failed: %s" % err

        # Only foreign entry should remain
        ownership_file = project / ".advanced-plans" / "skill-ownership.json"
        data = json.loads(ownership_file.read_text(encoding="utf-8"))
        assert list(data["skills"].keys()) == [_FOREIGN_SKILL], (
            "registry should contain only %s, got %s" % (_FOREIGN_SKILL, list(data["skills"].keys())))

    @pytest.mark.parametrize("lang", ["sh", "ps1"], ids=["sh", "ps1"])
    def test_malformed_foreign_entry_is_not_destroyed(self, tmp_path, adapter, lang):
        """I.4: the two hosts must agree about a malformed third-party entry.

        The schema wants a list of owners.  A bare string is malformed, but
        it is still somebody else's registration, and the PowerShell twin
        normalises it to a list and keeps it.  The POSIX side dropped it --
        and being the last entry left, it took the whole ownership file with
        it.  That is the same data loss as I.1 by a different route, and it
        was invisible to every test because they all wrote well-formed
        entries.
        """
        _skip_if_no_sh() if lang == "sh" else _skip_if_no_pwsh()
        name, install_sh, install_ps1, uninstall_sh, uninstall_ps1 = adapter
        project = _fresh_project(tmp_path, "malformed-foreign")

        install_script = install_sh if lang == "sh" else install_ps1
        ret, out, err = _run_script(
            install_script,
            ["--project", str(project)] if lang == "sh" else ["-Project", str(project)],
        )
        assert ret == 0, "install failed: %s" % err

        # A bare string, not a list.
        ownership_file = project / ".advanced-plans" / "skill-ownership.json"
        data = json.loads(ownership_file.read_text(encoding="utf-8"))
        data["skills"][_FOREIGN_SKILL] = _FOREIGN
        ownership_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        uninstall_script = uninstall_sh if lang == "sh" else uninstall_ps1
        ret, out, err = _run_script(
            uninstall_script,
            ["--project", str(project), "--yes"] if lang == "sh"
            else ["-Project", str(project), "-Yes"],
        )
        assert ret == 0, "uninstall failed: %s" % err

        assert ownership_file.exists(), (
            "the registry was deleted along with a malformed third-party entry")
        data = json.loads(ownership_file.read_text(encoding="utf-8"))
        assert _FOREIGN_SKILL in data["skills"], (
            "the malformed third-party entry was dropped")
        assert data["skills"][_FOREIGN_SKILL] == [_FOREIGN], (
            "expected the entry normalised to a list, got %r"
            % (data["skills"][_FOREIGN_SKILL],))


# =============================================================================
# F.1: documentation pointers printed by installers
# =============================================================================


class TestDocumentationPointersResolve:
    """Every "See <dir>/<file>.md" an installer prints must exist."""

    def test_every_see_pointer_resolves(self):
        """F.1: no installer may advertise documentation that is not there.

        Four installers pointed at setup/<adapter>/README.md, which has
        never existed for codex or opencode -- their documentation lives
        under platforms/.  Three other pointers in the identical shape are
        correct, so this asserts that each target RESOLVES rather than that
        it is spelled a particular way: rewriting a pointer to a different
        wrong place cannot satisfy it.
        """
        # Requires a directory component, so the bare "See README.md" that
        # an installer writes into a generated file is not matched here --
        # that one is relative to the directory it is written into.
        pattern = re.compile(r"See ([\w.-]+/[\w./-]+\.md)\b")
        setup_dir = _REPO_ROOT / "setup"
        checked, broken = [], []
        for script in sorted(setup_dir.rglob("*")):
            if script.suffix not in (".sh", ".ps1"):
                continue
            text = script.read_text(encoding="utf-8", errors="replace")
            for match in pattern.finditer(text):
                target = match.group(1)
                checked.append(target)
                if not (_REPO_ROOT / target).is_file():
                    broken.append("%s points at %s"
                                  % (script.relative_to(_REPO_ROOT), target))

        # Without this floor the test passes having checked nothing the
        # moment the wording drifts -- the failure mode E.17 and E.18 had.
        assert len(checked) >= 7, (
            "expected at least 7 documentation pointers under setup/, found "
            "%d: %s. The pattern stopped matching and this test would "
            "otherwise pass having checked nothing." % (len(checked), checked))
        assert not broken, (
            "installer(s) advertise documentation that does not exist:\n  "
            + "\n  ".join(broken))


# =============================================================================
# F.2 / F.3: the POSIX rewrite must not convert line endings
# =============================================================================


def _sh_function_body(path, name):
    """Return the text of a POSIX shell function, brace to closing brace.

    Reads the shipped installer rather than a copy of it, so a test built on
    this cannot drift away from what actually runs.
    """
    text = path.read_text(encoding="utf-8")
    opener = "%s() {\n" % name
    start = text.find(opener)
    if start < 0:
        return None
    end = text.find("\n}\n", start)
    assert end > start, "%s: %s has no closing brace at column 0" % (path, name)
    return text[start:end + len("\n}\n")]


def _code_lines(text):
    """The lines of a shell script with comments dropped.

    A comment that NAMES a forbidden construct in order to explain why it is
    forbidden must not read as a use of it.
    """
    return [ln for ln in text.split("\n") if not ln.lstrip().startswith("#")]


def _posix_installers_defining_rewrite():
    """Every setup/*/install.sh that defines ap_rewrite_call_sites.

    Discovered from the filesystem, not from a list written here, so an adapter
    added later is covered without anyone remembering to edit this file.
    """
    found = {}
    for script in sorted((_REPO_ROOT / "setup").glob("*/install.sh")):
        body = _sh_function_body(script, "ap_rewrite_call_sites")
        if body is not None:
            found[str(script.relative_to(_REPO_ROOT)).replace("\\", "/")] = body
    return found


class TestRewriteUsesNoInPlaceStripper:
    """F.2: static, and meaningful on every platform including Linux CI."""

    def test_no_posix_installer_rewrites_a_file_in_place(self):
        """`sed -i` (and friends) cannot be used on files whose endings matter.

        Under MSYS, sed opens files in text mode and rewrites every CRLF as LF
        -- measured even for a substitution matching nothing.  The same GNU sed
        4.9 on Linux preserves CR, so the fault is the platform rather than the
        tool and there is no safe sed invocation for this job.  The PowerShell
        twin Set-ApCallSites always preserved endings, so the two hosts
        produced byte-different installs from the same source.

        This is the guard that still bites on Linux CI, where F.3 must skip.
        """
        installers = _posix_installers_defining_rewrite()

        # Without a floor this passes having checked nothing the moment the
        # function is renamed -- the failure mode E.17, E.18 and F.1 all had.
        assert len(installers) >= 3, (
            "expected at least 3 POSIX installers defining "
            "ap_rewrite_call_sites, found %d: %s. Either the function was "
            "renamed or the layout moved, and this test would otherwise pass "
            "having checked nothing." % (len(installers), sorted(installers)))

        banned = ("sed -i", "sed --in-place", "-i.bak", "gawk -i inplace")
        offenders = []
        for rel, body in sorted(installers.items()):
            for line in _code_lines(body):
                for token in banned:
                    if token in line:
                        offenders.append("%s: %s" % (rel, line.strip()))
        assert not offenders, (
            "the rewrite must not edit a file in place -- under MSYS that "
            "strips CR from every line, including on a no-op substitution:\n  "
            + "\n  ".join(offenders))

    def test_every_adapter_carries_the_same_rewrite(self):
        """F.2/F8: the copies must not drift apart again.

        claude-code's copy already carried a comment the other two lacked;
        three hand-maintained duplicates is exactly how one gets fixed and the
        others do not.
        """
        installers = _posix_installers_defining_rewrite()
        assert len(installers) >= 3, "see the floor above: found %d" % len(installers)

        bodies = {}
        for rel, body in installers.items():
            bodies.setdefault(body, []).append(rel)
        assert len(bodies) == 1, (
            "the POSIX installers carry %d different versions of "
            "ap_rewrite_call_sites; they must be identical:\n%s"
            % (len(bodies), "\n".join(
                "  group %d: %s" % (i, sorted(v))
                for i, v in enumerate(bodies.values(), 1))))


class TestRewritePreservesLineEndings:
    """F.3: behavioural, and honest about the platforms where it cannot bite."""

    _PY_CALL = 'python ".advanced-plans/bin/ap.py"'
    _RP_CALL = "runpy.run_path(r'.advanced-plans/bin/ap.py')"

    def _sed_strips_cr(self, tmp_path):
        """Does THIS platform's sed -i strip CR from a CRLF file?

        The probe is a substitution that matches nothing, because that is the
        measured Windows behaviour: the stripping is text-mode I/O, not the
        edit.  A platform where this returns False cannot exhibit F10 at all.
        """
        probe = tmp_path / "sed-probe.txt"
        probe.write_bytes(b"alpha\r\nbeta\r\n")
        try:
            proc = subprocess.Popen(
                ["sed", "-i", "-e", "s#no-such-string-anywhere#x#g", str(probe)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True)
            proc.communicate(timeout=30)
        except (OSError, subprocess.SubprocessError):
            return None  # no usable sed; cannot tell either way
        if proc.returncode != 0:
            return None
        return probe.read_bytes().count(b"\r") == 0

    def _run_rewrite(self, tmp_path, installer, target, launcher):
        """Run the REAL shipped function, lifted out of the real installer."""
        parts = []
        for name in ("ap_subst", "ap_rewrite_call_sites"):
            body = _sh_function_body(installer, name)
            assert body is not None, (
                "%s does not define %s" % (installer, name))
            parts.append(body)
        harness = tmp_path / "harness.sh"
        harness.write_bytes(
            ("set -e\n" + "\n".join(parts)
             + '\nap_rewrite_call_sites "$1" "$2"\n').encode("utf-8"))
        ret, out, err = _run_script(
            harness, [str(target), launcher], cwd=tmp_path)
        assert ret == 0, "rewrite harness failed: %s%s" % (out, err)

    def test_rewrite_preserves_crlf(self, tmp_path):
        """F.3: a CRLF file keeps its CRLF, and still gets rewritten."""
        strips = self._sed_strips_cr(tmp_path)
        if strips is None:
            pytest.skip(
                "no usable `sed` on this platform, so the probe cannot "
                "establish whether F10 could occur here. This guard is INERT, "
                "not passing; TestRewriteUsesNoInPlaceStripper is what covers "
                "the regression in this environment.")
        if not strips:
            pytest.skip(
                "this platform's `sed -i` PRESERVES CR (measured just now on a "
                "planted CRLF file), so the F10 defect cannot occur here and "
                "this end-to-end assertion would hold whether or not the fix "
                "were present. This guard is INERT, not passing -- reverting "
                "the fix to `sed -i` would not fail it here. "
                "TestRewriteUsesNoInPlaceStripper is what covers the "
                "regression in this environment.")

        launcher = "/opt/global/.advanced-plans/bin/ap.py"
        installers = _posix_installers_defining_rewrite()
        assert installers, "no installer defines the rewrite"

        for rel in sorted(installers):
            installer = _REPO_ROOT / rel

            # 1. CRLF, with a call site: endings survive AND the edit happens.
            hit = tmp_path / "hit.md"
            hit.write_bytes(
                ("prose\r\nrun %s now\r\nmore\r\n" % self._PY_CALL).encode())
            before = hit.read_bytes().count(b"\r")
            self._run_rewrite(tmp_path, installer, hit, launcher)
            after = hit.read_bytes()
            assert after.count(b"\r") == before, (
                "%s: rewriting a CRLF file dropped %d of %d CR bytes -- a "
                "shell install now produces byte-different files from a "
                "PowerShell one" % (rel, before - after.count(b"\r"), before))
            assert launcher.encode() in after, (
                "%s: line endings survived but the substitution did not "
                "happen, so the rewrite is preserving by doing nothing" % rel)
            assert self._PY_CALL.encode() not in after, (
                "%s: the original call site survives the rewrite" % rel)

            # 2. CRLF, no call site: byte-identical, not merely equal text.
            miss = tmp_path / "miss.md"
            original = b"nothing\r\nto\r\nsee\r\n"
            miss.write_bytes(original)
            self._run_rewrite(tmp_path, installer, miss, launcher)
            assert miss.read_bytes() == original, (
                "%s: a file with no call site was modified" % rel)

            # 3. LF stays LF -- the fix must not convert in the other
            #    direction either, which is what a naive CRLF-restore would do.
            lf = tmp_path / "lf.md"
            lf.write_bytes(("prose\nrun %s now\n" % self._RP_CALL).encode())
            self._run_rewrite(tmp_path, installer, lf, launcher)
            got = lf.read_bytes()
            assert b"\r" not in got, (
                "%s: CR was introduced into an LF file" % rel)
            assert launcher.encode() in got, (
                "%s: the runpy call site was not rewritten" % rel)


# =============================================================================
# G.1: the worker commit contract must not contradict itself across copies
# =============================================================================


def _hard_contract_clause_a(path):
    """Clause (a) of a Hard Contract, or None if the file carries no contract.

    Read with universal newlines so the comparison is about what the clause
    SAYS; line endings are F.2 and F.3's subject, not this one's.
    """
    text = path.read_text(encoding="utf-8")
    if "## Hard Contract" not in text:
        return None
    start = text.find("**(a) ")
    if start < 0:
        return None
    end = text.find("**(b) ", start)
    assert end > start, "%s: clause (a) is not followed by a clause (b)" % path
    return text[start:end].strip()


def _role_contracts(role):
    """Every Hard Contract for a role, discovered from the filesystem.

    A file is a contract for the role if its NAME carries the role word and it
    actually contains a Hard Contract. That second condition is what excludes
    platforms/cowork/agents/worker-prompt.md, deliberately: Cowork is git-free
    and checkpoints by snapshot, so it states no commit policy and must not be
    held to one. platforms/claude-code/agents/analysis-worker.md is excluded the
    same way -- it is a different agent with no contract.
    """
    found = {}
    for root in (_REPO_ROOT / "core" / "agents", _REPO_ROOT / "platforms"):
        if not root.is_dir():
            continue
        for md in sorted(root.rglob("*.md")):
            if role not in md.name.lower():
                continue
            clause = _hard_contract_clause_a(md)
            if clause is not None:
                rel = str(md.relative_to(_REPO_ROOT)).replace("\\", "/")
                found[rel] = clause
    return found


class TestWorkerCommitContract:
    """G.1: one policy on committing, stated identically wherever it is shipped."""

    def test_every_worker_contract_states_the_same_policy(self):
        """The three copies are hand-maintained; that is how they drift.

        This is the F5 defect in its general form: two shipped documents said
        opposite things about whether a worker may commit, and nothing noticed.
        """
        contracts = _role_contracts("worker")
        assert len(contracts) >= 3, (
            "expected at least 3 worker Hard Contracts, found %d: %s. Either "
            "they were renamed or the layout moved, and this test would "
            "otherwise pass having compared nothing."
            % (len(contracts), sorted(contracts)))

        groups = {}
        for rel, clause in contracts.items():
            groups.setdefault(clause, []).append(rel)
        assert len(groups) == 1, (
            "the worker contracts state %d different commit policies; they "
            "must agree:\n%s" % (len(groups), "\n".join(
                "  group %d: %s" % (i, sorted(v))
                for i, v in enumerate(groups.values(), 1))))

    def test_worker_contract_requires_attribution_and_forbids_blanket_staging(self):
        """A worker may commit, but the commit must say who made it.

        Permitting commits without attribution would reintroduce exactly what
        the old rule was adopted after: ralph-loop-worker.md records that the
        Loops 056/061 self-commits damaged this repo's history precisely
        because they were unattributed and staged the whole tree.
        """
        contracts = _role_contracts("worker")
        assert len(contracts) >= 3, "see the floor above: found %d" % len(contracts)

        missing = []
        for rel, clause in sorted(contracts.items()):
            for token, why in (
                    ("Agent:", "no `Agent:` trailer, so a commit cannot be "
                               "traced to the agent that made it"),
                    ("Loop:", "no `Loop:` trailer, so a commit cannot be tied "
                              "to the loop it came from"),
                    ("git add -A", "does not forbid the blanket stage that "
                                   "made the Loops 056/061 self-commits "
                                   "damaging"),
            ):
                if token not in clause:
                    missing.append("%s: %s" % (rel, why))
        assert not missing, (
            "worker contracts permit committing without the safeguards that "
            "make it safe:\n  " + "\n  ".join(missing))

    def test_orchestrator_contract_still_forbids_commits(self):
        """The change was scoped to workers, and must stay scoped.

        The orchestrator really does not commit -- it writes loop-ready.json and
        nothing else -- so relaxing its contract too would be over-applying the
        decision rather than implementing it.
        """
        contracts = _role_contracts("orchestrator")
        assert len(contracts) >= 3, (
            "expected at least 3 orchestrator Hard Contracts, found %d: %s"
            % (len(contracts), sorted(contracts)))

        relaxed = [rel for rel, clause in sorted(contracts.items())
                   if "NEVER commit" not in clause]
        assert not relaxed, (
            "the orchestrator does not commit; its contract must still say so, "
            "but these no longer do: %s" % relaxed)

    def test_no_adapter_readme_contradicts_the_worker_contract(self):
        """G.1/F5 proper: the README is where the contradiction actually was.

        An adapter README that documents checkpoint ownership must not assert
        the superseded policy, and must name the attribution the contract now
        requires -- otherwise a reader following the README alone would produce
        untraceable commits.
        """
        readmes = {}
        for readme in sorted((_REPO_ROOT / "platforms").glob("*/README.md")):
            text = readme.read_text(encoding="utf-8")
            if "## Checkpoint Ownership" in text:
                rel = str(readme.relative_to(_REPO_ROOT)).replace("\\", "/")
                readmes[rel] = text
        assert len(readmes) >= 2, (
            "expected at least 2 adapter READMEs documenting checkpoint "
            "ownership, found %d: %s. The heading changed and this test would "
            "otherwise pass having checked nothing."
            % (len(readmes), sorted(readmes)))

        problems = []
        for rel, text in sorted(readmes.items()):
            section = text.split("## Checkpoint Ownership", 1)[1]
            section = section.split("\n## ", 1)[0]
            if "never commits" in section.lower():
                problems.append(
                    "%s: asserts as POLICY that a worker never commits, which "
                    "the worker contract no longer says. A runtime that is "
                    "merely unable to commit should say it cannot, not that it "
                    "never does." % rel)
            if "Agent:" not in section:
                problems.append(
                    "%s: documents checkpoint ownership without naming the "
                    "`Agent:` trailer, so a reader following this README alone "
                    "would produce commits that cannot be attributed." % rel)
        assert not problems, (
            "adapter README(s) disagree with the worker commit contract:\n  "
            + "\n  ".join(problems))


# =============================================================================
# H: the two adapters are near-duplicates and nothing compared them
# =============================================================================

_ADAPTER_FILES = ("install.sh", "install.ps1", "uninstall.sh", "uninstall.ps1")

# Display name as it appears in prose, per adapter directory name.
_ADAPTER_DISPLAY = {"codex": "Codex", "opencode": "OpenCode"}


def _normalise_adapter_identity(text):
    """Replace every adapter's own name and token with a shared placeholder.

    BOTH adapters are normalised to the SAME placeholder, not to self/peer
    markers. That is deliberate: the uninstaller headers say "may be registered
    by both Codex and OpenCode", naming the two in a fixed order, so a
    self/peer scheme would report correct prose as drift. The hole this opens
    -- one adapter writing the other's token -- is what the second test covers.
    """
    for name in sorted(_ADAPTER_DISPLAY, key=len, reverse=True):
        text = text.replace(_ADAPTER_DISPLAY[name], "@ADAPTERNAME@")
        text = text.replace(name, "@ADAPTER@")
    return text


def _adapter_pairs():
    """Every (filename, {adapter: text}) the two adapters both ship."""
    root = _REPO_ROOT / "setup"
    pairs = []
    for filename in _ADAPTER_FILES:
        texts = {}
        for adapter in sorted(_ADAPTER_DISPLAY):
            path = root / adapter / filename
            if path.is_file():
                texts[adapter] = path.read_text(encoding="utf-8")
        if len(texts) == len(_ADAPTER_DISPLAY):
            pairs.append((filename, texts))
    return pairs


class TestAdaptersHaveNotDrifted:
    """H: codex and opencode are the same script with a different name in it."""

    def test_every_shared_script_is_identical_once_the_name_is_normalised(self):
        """The duplication is ~1880 lines per adapter with no guard on it.

        TestLanguagesAgree compares sh against ps1 within ONE adapter. Nothing
        compared one adapter against the other, and by the time this was
        written they had already diverged.
        """
        pairs = _adapter_pairs()
        assert len(pairs) == len(_ADAPTER_FILES), (
            "expected %d shared scripts present in BOTH adapters, found %d: %s. "
            "A file was renamed or an adapter moved, and this test would "
            "otherwise pass having compared nothing."
            % (len(_ADAPTER_FILES), len(pairs), [f for f, _ in pairs]))

        drifted = []
        for filename, texts in pairs:
            normalised = {a: _normalise_adapter_identity(t)
                          for a, t in texts.items()}
            distinct = set(normalised.values())
            if len(distinct) > 1:
                lines = {a: t.count("\n") for a, t in texts.items()}
                drifted.append(
                    "%s: %s differ once the adapter name is normalised away "
                    "(%s)" % (filename, sorted(texts),
                              ", ".join("%s=%d lines" % (a, n)
                                        for a, n in sorted(lines.items()))))
        assert not drifted, (
            "the adapters are maintained as copies of one another, so a change "
            "made to one and not the other is a defect:\n  "
            + "\n  ".join(drifted))

    def test_no_adapter_names_its_peer_in_code(self):
        """Closes the hole the shared placeholder opens.

        Because both adapters normalise to the same token, the first test
        cannot tell codex's installer writing an `opencode` fence from it
        writing its own. This can: on a code line, an adapter must only ever
        name itself. Comments are exempt -- the uninstaller headers correctly
        explain that a shared skill may be owned by both.
        """
        pairs = _adapter_pairs()
        assert len(pairs) == len(_ADAPTER_FILES), (
            "see the floor above: found %d" % len(pairs))

        leaks = []
        for filename, texts in pairs:
            for adapter, text in sorted(texts.items()):
                peers = [p for p in _ADAPTER_DISPLAY if p != adapter]
                for number, line in enumerate(text.split("\n"), 1):
                    stripped = line.lstrip()
                    if stripped.startswith("#"):
                        continue
                    for peer in peers:
                        if peer in line or _ADAPTER_DISPLAY[peer] in line:
                            leaks.append(
                                "setup/%s/%s:%d names %s on a code line: %s"
                                % (adapter, filename, number, peer,
                                   line.strip()[:80]))
        assert not leaks, (
            "an adapter must only ever write its own token; naming the peer in "
            "code means the wrong owner or the wrong fence:\n  "
            + "\n  ".join(leaks))


# =============================================================================
# J: claude-code is a different adapter, not a third instance of the same one
# =============================================================================

_CC_DIR = _REPO_ROOT / "setup" / "claude-code"

# Every file the adapter is expected to ship. Kept explicit because the point of
# the check is that one of them has NOT quietly disappeared; globbing for
# "whatever is there" would pass for an empty directory.
_CC_SURFACE = ("README.md", "install.sh", "install.ps1",
               "uninstall.sh", "uninstall.ps1")

# Tokens belonging to the shared-agent layout that codex and opencode
# implement. claude-code must not drift into it -- it installs into .claude/,
# does not maintain skill-ownership.json, and writes no AGENTS.md fences.
_SHARED_LAYOUT_TOKENS = ("AGENTS.md", "skill-ownership", ".agents/skills")

# $REPO_ROOT/<path> in sh; Join-Path $RepoRoot "<path>" in PowerShell, where the
# path is a separate argument and so needs its own pattern.
_CC_SRC_SH = re.compile(r"\$REPO_ROOT/([A-Za-z0-9_./*-]+)")
_CC_SRC_PS = re.compile(r'Join-Path \$RepoRoot "([^"]+)"')
_CC_DEST_SH = re.compile(r"\$CLAUDE_DIR/([A-Za-z0-9_.-]+)")
_CC_FLAG_SH = re.compile(r"^\s+(--[a-z-]+)\)", re.MULTILINE)
_CC_FLAG_PS = re.compile(r"^\s*\[(?:switch|string)\]\$([A-Za-z]+)", re.MULTILINE)


def _cc_read(name):
    return (_CC_DIR / name).read_text(encoding="utf-8")


def _cc_repo_paths(text, pattern):
    """Repo-relative paths a script reads from, with glob tails removed."""
    found = set()
    for match in pattern.finditer(text):
        parts = [p for p in match.group(1).replace("\\", "/").split("/") if p]
        while parts and ("*" in parts[-1] or parts[-1].startswith("$")):
            parts.pop()
        if parts:
            found.add("/".join(parts))
    return found


def _cc_canonical_flag(flag):
    """--dry-run and -DryRun are the same flag in two spellings."""
    return flag.lstrip("-").replace("-", "").lower()


class TestClaudeCodeAdapter:
    """J: cover what claude-code does, rather than what it does not do.

    It installs core/skills/* into .claude/skills/ and supports --symlink,
    where codex and opencode install platforms/shared/agent-skills into
    .agents/skills/ and maintain a shared ownership registry. Parametrising it
    alongside them would mostly assert that it never touches machinery it was
    never meant to touch.
    """

    def test_the_adapter_ships_its_whole_surface(self):
        """A missing script is the failure every check below would mask."""
        missing = [n for n in _CC_SURFACE if not (_CC_DIR / n).is_file()]
        assert not missing, (
            "setup/claude-code is missing %s. Every other check in this class "
            "reads these files, so they would pass having read nothing."
            % missing)

    def test_every_repo_path_the_installer_reads_from_exists(self):
        """A moved source directory is a silent install of nothing.

        Both installers copy from fixed repo paths. If one is renamed, the
        loops that read it simply iterate zero times -- `[ -f "$x" ] || continue`
        skips everything and the install reports success having written no
        skills at all.
        """
        for script, pattern, floor in (("install.sh", _CC_SRC_SH, 5),
                                       ("install.ps1", _CC_SRC_PS, 5)):
            paths = _cc_repo_paths(_cc_read(script), pattern)
            assert len(paths) >= floor, (
                "setup/claude-code/%s: found only %d repo paths (expected at "
                "least %d). The script was rewritten to build its paths some "
                "other way, and this check is now reading nothing: %s"
                % (script, len(paths), floor, sorted(paths)))
            gone = sorted(p for p in paths if not (_REPO_ROOT / p).exists())
            assert not gone, (
                "setup/claude-code/%s reads from paths that no longer exist: "
                "%s. The installer would report success having copied nothing."
                % (script, gone))

    def test_the_uninstaller_names_every_directory_the_installer_writes(self):
        """Anything install creates and uninstall does not name is left behind."""
        install = _cc_read("install.sh")
        uninstall = _cc_read("uninstall.sh")
        dests = set(_CC_DEST_SH.findall(install))
        assert len(dests) >= 5, (
            "found only %d $CLAUDE_DIR destinations in install.sh (expected at "
            "least 5); the installer no longer names its targets this way and "
            "this check is comparing nothing: %s" % (len(dests), sorted(dests)))
        orphans = sorted(d for d in dests if d not in uninstall)
        assert not orphans, (
            "install.sh names $CLAUDE_DIR/%s but uninstall.sh never mentions "
            "it. Either the uninstaller leaves it behind, or the installer "
            "describes something it does not actually create -- a dry-run "
            "message that does not match a real run is the second case, and "
            "is just as much a defect."
            % ", $CLAUDE_DIR/".join(orphans))

    def test_both_languages_offer_the_same_flags(self):
        """A flag in one host and not the other is a platform-only feature."""
        sh_flags = set(_CC_FLAG_SH.findall(_cc_read("install.sh")))
        ps_flags = set(_CC_FLAG_PS.findall(_cc_read("install.ps1")))
        for label, flags in (("install.sh", sh_flags), ("install.ps1", ps_flags)):
            assert len(flags) >= 4, (
                "setup/claude-code/%s: parsed only %d flags (expected at least "
                "4). The argument parser was restructured and this check no "
                "longer sees it: %s" % (label, len(flags), sorted(flags)))
        sh_canon = {_cc_canonical_flag(f): f for f in sh_flags}
        ps_canon = {_cc_canonical_flag(f): f for f in ps_flags}
        sh_only = sorted(sh_canon[k] for k in set(sh_canon) - set(ps_canon))
        ps_only = sorted(ps_canon[k] for k in set(ps_canon) - set(sh_canon))
        assert not sh_only and not ps_only, (
            "the two installers do not offer the same flags: only in "
            "install.sh %s, only in install.ps1 %s" % (sh_only, ps_only))

    def test_the_readme_documents_every_flag_the_installers_accept(self):
        """claude-code is the only adapter shipping a README; it must be true.

        Documentation drift is not cosmetic here: the README is the only place
        --symlink is explained, and a flag that exists but is undocumented is
        indistinguishable from one that does not exist.
        """
        readme = _cc_read("README.md")
        sh_flags = sorted(_CC_FLAG_SH.findall(_cc_read("install.sh")))
        ps_flags = sorted("-" + f
                          for f in _CC_FLAG_PS.findall(_cc_read("install.ps1")))
        assert len(sh_flags) >= 4 and len(ps_flags) >= 4, (
            "parsed %d sh and %d ps1 flags (expected at least 4 each); this "
            "check would otherwise pass having looked for nothing in the "
            "README" % (len(sh_flags), len(ps_flags)))
        undocumented = [f for f in sh_flags + ps_flags if f not in readme]
        assert not undocumented, (
            "setup/claude-code/README.md does not mention %s, which the "
            "installers accept" % undocumented)

    def test_it_installs_into_dot_claude_and_stays_out_of_the_shared_layout(self):
        """The structural boundary, asserted in both directions.

        The negative half alone would be vacuous -- it passes for a file that
        does nothing at all. The positive half is what gives it a subject: each
        script must actually name .claude, and each must name the skills source
        it installs from, in its own path syntax.
        """
        for script, skills_src in (("install.sh", "core/skills"),
                                   ("install.ps1", "core\\skills"),
                                   ("uninstall.sh", "core/skills"),
                                   ("uninstall.ps1", "core\\skills")):
            text = _cc_read(script)
            assert ".claude" in text, (
                "setup/claude-code/%s never names .claude, so this check has "
                "no subject and the absences below prove nothing" % script)
            if script.startswith("install"):
                assert skills_src in text, (
                    "setup/claude-code/%s never names %s -- it no longer "
                    "installs the core skills, or it builds the path some "
                    "other way" % (script, skills_src))
            intruders = [t for t in _SHARED_LAYOUT_TOKENS if t in text]
            assert not intruders, (
                "setup/claude-code/%s names %s. That is codex and opencode's "
                "shared-agent layout; claude-code installs into .claude/ and "
                "maintains no ownership registry. If this adapter genuinely "
                "needs to join that protocol, the shared tests in this file "
                "apply to it and this class is the wrong home for it."
                % (script, intruders))


# =============================================================================
# K: a deprecated companion must not survive as a live recommendation
# =============================================================================

# Companions this project has deprecated, and the date it happened. The name is
# what appears in an install URL or a slash command, lowercased.
_DEPRECATED_COMPANIONS = {
    "plannotator": "2026-08-26",
}

# Where a user-facing instruction can live. Discovered by glob, so a new adapter
# or skill is covered the day it is added rather than the day someone remembers
# to list it here.
_INSTRUCTION_GLOBS = ("platforms/*/**/*.md", "core/skills/**/*.md", "CLAUDE.md")

# Directories that hold the RECORD rather than instructions. History is not
# rewritten -- the deprecation note, the changelog and the programme record must
# all keep saying the name.
_RECORD_PREFIXES = ("docs/", ".advanced-plans/", "CHANGELOG.md")


def _actionable_refs(text, name):
    """Ways a document tells a reader to actually go and use `name`.

    Deliberately narrow. Naming a deprecated tool is fine and often necessary;
    handing someone a command that installs or invokes it is not.
    """
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        if name not in low:
            continue
        if re.search(r"(?:git\s+clone|pip\s+install|npm\s+i(?:nstall)?|"
                     r"/plugin\s+install)\s+\S*" + re.escape(name), low):
            hits.append((i, "install command", line.strip()))
        elif re.search(r"(?<![\w/])/" + re.escape(name) + r"[\w-]*", low):
            hits.append((i, "slash-command invocation", line.strip()))
        elif re.search(r"--plugin-dir\s+\S*" + re.escape(name), low):
            hits.append((i, "plugin-dir launch", line.strip()))
        elif re.search(r"commands/" + re.escape(name), low):
            hits.append((i, "command-file reference", line.strip()))
    return hits


def _instruction_files():
    seen = {}
    for pattern in _INSTRUCTION_GLOBS:
        for path in _REPO_ROOT.glob(pattern):
            if not path.is_file():
                continue
            rel = path.relative_to(_REPO_ROOT).as_posix()
            if rel.startswith(_RECORD_PREFIXES):
                continue
            seen[rel] = path
    return seen


class TestDeprecatedCompanionsAreNotRecommended:
    """K: the deprecation reached the shipped surface, not just the record.

    Plannotator was declared removed on 2026-08-26 in this project's own
    deprecation note, and in Advanced AI Workflows' ARCHITECTURE.md, which
    stated that /plan-and-phase Step 5b "was removed". It was not. Step 5b was
    still detecting the plugin and invoking /plannotator-annotate, and
    companion-detection was still telling a user without it installed to
    git clone it -- on the same branch whose codex and opencode READMEs assert
    "No Plannotator: the deprecated review companion is not installed or
    invoked". Two adapters asserting a property the third violated.
    """

    def test_the_detector_actually_detects(self):
        """Without this, every assertion below passes for a broken regex.

        The scan's whole output is "no matches". That is indistinguishable
        from a pattern that can no longer match anything, which is how a
        check quietly stops being a check.
        """
        must_catch = [
            "> git clone https://github.com/MungoHarvey/plannotator.git",
            "claude --plugin-dir plannotator/apps/hook",
            "Invoke `/plannotator-annotate .advanced-plans/phases/phase-1/plan.md`",
            "- Look for `.claude/commands/plannotator-annotate.md` (plugin command)",
            "/plugin install plannotator@plannotator",
        ]
        for line in must_catch:
            assert _actionable_refs(line, "plannotator"), (
                "the detector no longer catches a live recommendation: %r" % line)

        must_not_catch = [
            "Plannotator was deprecated on 2026-08-26.",
            "**No Plannotator**: The deprecated review companion is not installed",
            "the review gate it provided is now `/run-gate`",
            "plannotator remains in the diagrams below, marked (v0.1, deprecated)",
            "a plannotator install elsewhere on the machine is left untouched",
        ]
        for line in must_not_catch:
            assert not _actionable_refs(line, "plannotator"), (
                "the detector fires on prose that merely names the tool, which "
                "would force the deprecation record to stop describing it: %r" % line)

    def test_no_shipped_instruction_recommends_a_deprecated_companion(self):
        files = _instruction_files()
        assert len(files) >= 20, (
            "found only %d instruction files (expected at least 20). The globs "
            "%s no longer match the shipped surface, so this check is scanning "
            "almost nothing: %s"
            % (len(files), list(_INSTRUCTION_GLOBS), sorted(files)))
        assert _DEPRECATED_COMPANIONS, (
            "the deprecated-companion registry is empty, so this check has "
            "nothing to look for and passes unconditionally")

        offences = []
        for rel, path in sorted(files.items()):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for name in _DEPRECATED_COMPANIONS:
                for line_no, kind, line in _actionable_refs(text, name):
                    offences.append("%s:%d: %s -- %s" % (rel, line_no, kind, line[:90]))
        assert not offences, (
            "%d shipped instruction(s) still tell a reader to install or invoke "
            "a companion this project deprecated:\n  %s\n\nDeprecated: %s. The "
            "record in docs/ and CHANGELOG.md is exempt and must keep naming "
            "them; these are live instructions."
            % (len(offences), "\n  ".join(offences),
               ", ".join("%s (%s)" % kv for kv in
                         sorted(_DEPRECATED_COMPANIONS.items()))))

    def test_the_scan_actually_reads_the_adapters(self):
        """The floor above counts files; this one names the ones that matter.

        A glob that silently stopped matching platforms/ would still clear a
        count of 20 on core/skills/ alone, and claude-code -- the adapter that
        carried the defect -- is exactly what would go unscanned.
        """
        scanned = set(_instruction_files())
        for adapter in ("claude-code", "codex", "opencode"):
            covered = [r for r in scanned if r.startswith("platforms/%s/" % adapter)]
            assert covered, (
                "no file under platforms/%s/ was scanned. The glob no longer "
                "reaches that adapter, and a live recommendation there would "
                "not be seen." % adapter)


# ---------------------------------------------------------------------------
# F16 / F17 -- the comparison helpers the collision check is built on
# ---------------------------------------------------------------------------

def _extract_shell_functions(script_path, names):
    """Pull named top-level functions out of a shell script, verbatim.

    The alternative -- retyping the helpers into the test -- would let the test
    pass while the shipped script did something else, which is the defect class
    this whole suite exists for. Anchoring on a line that is exactly ``}`` is
    safe here because every nested close in these functions is indented.
    """
    text = _read(script_path)
    out = {}
    wanted = set(names)
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        name = None
        for candidate in wanted:
            if line == "%s() {" % candidate:
                name = candidate
                break
        if name is None:
            i += 1
            continue
        body = [line]
        i += 1
        while i < len(lines) and lines[i] != "}":
            body.append(lines[i])
            i += 1
        if i >= len(lines):
            raise AssertionError(
                "%s: function %s() has no closing brace at column 0"
                % (script_path.name, name))
        body.append("}")
        out[name] = "\n".join(body)
        i += 1
    missing = wanted - set(out)
    if missing:
        raise AssertionError(
            "%s: could not extract %s. The helpers were renamed or reshaped; "
            "this test is now measuring nothing and must be updated rather "
            "than deleted." % (script_path, ", ".join(sorted(missing))))
    return out


def _run_harness(tmp_path, script_path, functions, driver):
    """Source the extracted functions and run a driver script against them."""
    funcs = _extract_shell_functions(script_path, functions)
    harness = tmp_path / "harness.sh"
    parts = ["#!/bin/sh", "set -u", ""]
    for name in functions:
        parts.append(funcs[name])
        parts.append("")
    parts.append(driver)
    with open(str(harness), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(parts) + "\n")
    proc = subprocess.Popen(
        ["sh", str(harness)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True, cwd=str(tmp_path),
    )
    out, err = proc.communicate(timeout=120)
    return proc.returncode, out, err


class TestComparisonHelpers:
    """The two helpers `check_collision` decides on.

    Both installers carry a byte-identical copy of these, and only one copy of
    an earlier guard was ever maintained -- which is exactly how
    platforms/claude-code/install.sh kept a defect that setup/claude-code had
    already fixed. Parametrising over both is the point of this class, not a
    convenience.
    """

    def test_a_hash_is_a_hash_or_says_it_is_not(self, tmp_path, adapter):
        """F17: the same file, named two ways, must hash the same.

        GNU coreutils escapes a checksum line whose filename contains a
        backslash: it prefixes the line with `\\` and escapes the name. The old
        `sha256sum "$1" | cut -d' ' -f1` therefore returned `\\<64 hex>` for any
        Windows-style path -- not a hash, and printed straight into the
        collision error the operator is meant to act on. Measured on this
        machine: bfe5ed57e6e3... by the POSIX name, \\bfe5ed57e6e3... by the
        Windows one, for one unchanged file.
        """
        _skip_if_no_sh()
        _name, script, _ps1, _u1, _u2 = adapter

        driver = (
            'printf "contents\\n" > plain.txt\n'
            'PLAIN="$(sha256_file plain.txt)"\n'
            'echo "PLAIN=$PLAIN"\n'
            '# A name containing a backslash is what triggers the escaping.\n'
            '# Creatable directly on POSIX; on Windows the same shape arrives\n'
            '# as an ordinary native path, so use cygpath there.\n'
            'ODD=""\n'
            'if printf "contents\\n" > "odd\\\\name.txt" 2>/dev/null && '
            '[ -f "odd\\\\name.txt" ]; then\n'
            '    ODD="odd\\\\name.txt"; echo "VIA=literal-backslash"\n'
            'elif command -v cygpath >/dev/null 2>&1; then\n'
            '    ODD="$(cygpath -w "$PWD/plain.txt")"; echo "VIA=cygpath"\n'
            'else\n'
            '    echo "VIA=none"\n'
            'fi\n'
            'if [ -n "$ODD" ]; then\n'
            '    echo "ODD=$(sha256_file "$ODD")"\n'
            'fi\n'
        )
        rc, out, err = _run_harness(tmp_path, script,
                                    ["sha256_file"], driver)
        assert rc == 0, "harness failed: %s" % err
        values = dict(
            line.split("=", 1) for line in out.strip().split("\n") if "=" in line
        )
        if values.get("VIA") == "none":
            pytest.skip(
                "no way to present a backslash-bearing path on this host: "
                "the filesystem refused the name and cygpath is absent")

        plain = values["PLAIN"]
        assert len(plain) == 64 and all(c in "0123456789abcdefABCDEF" for c in plain), (
            "sha256_file returned %r for an ordinary path, which is not a "
            "64-character hex digest" % plain)

        odd = values["ODD"]
        if values["VIA"] == "cygpath":
            assert odd == plain, (
                "the same file hashed to %r by its POSIX name and %r by its "
                "Windows name. A leading backslash is coreutils' escape marker "
                "for the line, not part of the digest." % (plain, odd))
        else:
            assert odd == "UNREADABLE" or (
                len(odd) == 64
                and all(c in "0123456789abcdefABCDEF" for c in odd)), (
                "sha256_file returned %r for a backslash-bearing filename. It "
                "must return a real digest or say it could not, never a string "
                "that merely looks like one." % odd)

    def test_no_hash_tool_does_not_make_every_file_identical(
            self, tmp_path, adapter):
        """The fallback branch has to be able to report a difference.

        With neither diff nor sha256sum nor shasum on PATH, the old code hashed
        both files to the literal "NO_SHA256", compared them equal, and returned
        "identical" -- so every collision in the tree was silently waved
        through. A check that cannot fail is not a check.
        """
        _skip_if_no_sh()
        _name, script, _ps1, _u1, _u2 = adapter

        driver = (
            'printf "a\\n" > f1\n'
            'printf "b\\n" > f2\n'
            'mkdir -p emptybin\n'
            'OLD="$PATH"\n'
            'PATH="$PWD/emptybin"; export PATH\n'
            'if command -v diff >/dev/null 2>&1 || '
            'command -v sha256sum >/dev/null 2>&1 || '
            'command -v shasum >/dev/null 2>&1; then\n'
            '    RESULT="SKIP"\n'
            'else\n'
            '    if files_identical f1 f2; then RC=0; else RC=$?; fi\n'
            '    RESULT="$RC"\n'
            'fi\n'
            'PATH="$OLD"; export PATH\n'
            'echo "RESULT=$RESULT"\n'
        )
        rc, out, err = _run_harness(tmp_path, script,
                                    ["sha256_file", "files_identical"], driver)
        assert rc == 0, "harness failed: %s" % err
        result = out.strip().split("RESULT=")[-1].strip()
        if result == "SKIP":
            pytest.skip("could not clear diff/sha256sum/shasum from PATH here")
        assert result == "2", (
            "with no tool available to compare them, files_identical returned "
            "%s for two files whose contents genuinely differ. 0 means it "
            "claimed they were identical; 1 means it claimed a comparison it "
            "never made. The only honest answer is 2, could not compare."
            % result)

    def test_the_three_outcomes_are_distinct(self, tmp_path, adapter):
        """identical / differ / could-not-compare must not collapse into two.

        The diff branch already returned diff's own status, so this half is a
        regression guard rather than proof of the fix; the missing-file guard
        and the fallback branch above are what changed.
        """
        _skip_if_no_sh()
        _name, script, _ps1, _u1, _u2 = adapter

        driver = (
            'printf "a\\n" > f1\n'
            'printf "a\\n" > f2\n'
            'printf "b\\n" > f3\n'
            'mkdir -p adir\n'
            'probe() { if files_identical "$2" "$3"; then echo "$1=0"; '
            'else echo "$1=$?"; fi; }\n'
            'probe SAME f1 f2\n'
            'probe DIFF f1 f3\n'
            'probe GONE f1 nope\n'
            'probe DIR  f1 adir\n'
        )
        rc, out, err = _run_harness(tmp_path, script,
                                    ["sha256_file", "files_identical"], driver)
        assert rc == 0, "harness failed: %s" % err
        got = dict(
            line.split("=", 1) for line in out.strip().split("\n") if "=" in line
        )
        assert got == {"SAME": "0", "DIFF": "1", "GONE": "2", "DIR": "2"}, (
            "files_identical returned %r. Expected 0 identical, 1 differ, "
            "2 could-not-compare." % got)

    def test_could_not_compare_is_not_announced_as_a_collision(
            self, tmp_path, adapter):
        """F16: the caller must not turn "no answer" into "they diverged".

        `check_collision` tested `if ! files_identical`, which reads 1 and 2
        alike, so a comparison that never happened was reported to the operator
        as an observed divergence -- with two SHA-256 values printed beneath it
        as if they were the evidence. files_identical is stubbed here so the
        caller's own branch is what is under test.
        """
        _skip_if_no_sh()
        _name, script, _ps1, _u1, _u2 = adapter

        driver = (
            'say() { echo "$*"; }\n'
            'files_identical() { return 2; }\n'
            'mkdir -p src dst\n'
            'printf "x\\n" > src/thing.md\n'
            'printf "y\\n" > dst/thing.md\n'
            'if check_collision "$PWD/src" "$PWD/dst" demo-skill; then '
            'echo "RC=0"; else echo "RC=$?"; fi\n'
        )
        rc, out, err = _run_harness(
            tmp_path, script,
            ["sha256_file", "files_identical", "check_collision"], driver)
        assert rc == 0, "harness failed: %s" % err
        assert "RC=1" in out, (
            "check_collision returned %r; it must still refuse when it could "
            "not compare." % out.strip())
        assert "could not compare" in err, (
            "check_collision said %r. When no comparison was obtained it must "
            "say so, not assert a divergence nobody observed." % err.strip())
        assert "collision detected" not in err, (
            "check_collision announced a collision it never observed: %r"
            % err.strip())
