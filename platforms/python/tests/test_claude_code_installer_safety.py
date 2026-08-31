"""Tests for installer safety fixes (S1, S3, S3b) in setup/claude-code/.

  - S1  : an existing settings.json is preserved byte-identical; the planning
          settings go to settings.planning.json instead.
  - S3  : Do-Junction refuses a destination that is not a reparse point, and
          the self-install path does not delete it before asking.
  - S3b : do_ln refuses a real directory instead of creating a nested link
          inside it.

Every test here drives a real installer as a subprocess and asserts on what
ended up on disk. Each fails against the pre-fix scripts.

**On Windows the `bash` on PATH is WSL, not Git Bash.** WSL resolves
`/mnt/c/...`, so a Windows path handed to it fails with "No such file or
directory" -- which reads as "bash is unreliable here" and is not. Git Bash is
resolved explicitly by path below and accepts `C:/...` with forward slashes.
Getting this wrong is what previously caused every bash test in this file to be
skipped on the only platform anyone runs them on, leaving S3b covered by
nothing while the file reported green.

Skips are loud and narrow: a host is skipped only when its interpreter is
genuinely absent, and `test_at_least_one_host_was_exercised` fails if that left
the run proving nothing.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Interpreter resolution
# ---------------------------------------------------------------------------

def _find_git_bash():
    """Return a path to Git Bash, or None.

    Deliberately does not use shutil.which("bash"): on Windows that finds WSL,
    which cannot resolve Windows paths.
    """
    if sys.platform != "win32":
        return shutil.which("bash")
    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Git" / "bin" / "bash.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Git" / "bin" / "bash.exe",
    ]
    for candidate in candidates:
        try:
            if candidate.is_file():
                return str(candidate)
        except OSError:
            continue
    return None


GIT_BASH = _find_git_bash()
PWSH = shutil.which("pwsh")


def _bash_available() -> bool:
    return GIT_BASH is not None


def _pwsh_available() -> bool:
    return PWSH is not None


def _skip_bash():
    if not _bash_available():
        pytest.skip(
            "Git Bash not found (looked in Program Files, "
            "LOCALAPPDATA/Programs, Program Files (x86)) - skipping POSIX "
            "installer tests. This is a skip, not a pass: nothing about "
            "install.sh was verified."
        )


def _skip_pwsh():
    if not _pwsh_available():
        pytest.skip(
            "pwsh not found on PATH - skipping PowerShell installer tests. "
            "This is a skip, not a pass: nothing about install.ps1 was verified."
        )


def _fwd(path) -> str:
    """A Windows path in the forward-slash form Git Bash accepts."""
    return str(path).replace(os.sep, "/")


def _run(args, cwd=None):
    """Subprocess with decoding that survives the installers' non-ASCII output."""
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_sh(script: Path, *args, cwd: Path):
    return _run([GIT_BASH, _fwd(script), *args], cwd=cwd)


def _run_ps1(script: Path, *args, cwd: Path):
    return _run(
        [PWSH, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *args],
        cwd=cwd,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

EXISTING_USER_SETTINGS = {
    "permissions": {"allow": ["Read(**)", "Write(**)"]},
    "myCustomKey": "userValue",
}


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def install_sh(repo_root: Path) -> Path:
    return repo_root / "setup" / "claude-code" / "install.sh"


@pytest.fixture(scope="module")
def install_ps1(repo_root: Path) -> Path:
    return repo_root / "setup" / "claude-code" / "install.ps1"


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """An empty target project with a .claude/ directory."""
    target = tmp_path / "project"
    (target / ".claude").mkdir(parents=True)
    return target


def _seed_settings(project: Path):
    """Write a user-authored settings.json; return (path, exact content)."""
    settings = project / ".claude" / "settings.json"
    content = json.dumps(EXISTING_USER_SETTINGS, indent=2)
    settings.write_text(content, encoding="utf-8")
    return settings, content


@pytest.fixture
def fake_repo(tmp_path: Path, repo_root: Path) -> Path:
    """A throwaway git repo carrying just enough of the tree to install from.

    Self-install fires when --project resolves to the same git toplevel as the
    script's own repo root, so this is how that branch gets exercised without
    touching the real checkout.
    """
    fake = tmp_path / "fake_repo"
    fake.mkdir()
    for rel in ("setup/claude-code", "core", "platforms/claude-code"):
        source = repo_root / rel
        if source.exists():
            shutil.copytree(source, fake / rel, dirs_exist_ok=True)
    # ap_launcher.py is copied to .advanced-plans/bin/ap.py well before the
    # runtime-dirs block. Omitting it stops the installer early, which would
    # leave every test below passing because the code under test never ran.
    for rel in ("VERSION", "platforms/python/ap_launcher.py"):
        source = repo_root / rel
        if source.exists():
            (fake / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, fake / rel)
    subprocess.run(["git", "init", "-q"], cwd=str(fake), capture_output=True)
    return fake


def _assert_reached_runtime_dirs(result, host: str):
    """Guard against the installer dying before the code under test.

    Every assertion in the self-install tests is about what the runtime-dirs
    block does. If the installer exits before reaching it, those assertions
    hold trivially and the test passes without testing anything.
    """
    assert "Installing runtime dirs" in result.stdout, (
        f"{host} never reached the runtime-dirs block, so this test proved "
        f"nothing about it.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# S1 - settings.json preservation
# ---------------------------------------------------------------------------

class TestS1BashSettingsPreservation:
    """install.sh must never truncate a settings.json it did not write."""

    def test_no_existing_settings_json_is_written_normally(
        self, project_dir: Path, install_sh: Path, repo_root: Path
    ):
        _skip_bash()
        result = _run_sh(install_sh, "--project", _fwd(project_dir), cwd=repo_root)
        assert result.returncode == 0, f"install failed: {result.stderr}"

        settings = project_dir / ".claude" / "settings.json"
        planning = project_dir / ".claude" / "settings.planning.json"
        assert settings.exists(), f"settings.json should be written. stderr: {result.stderr}"
        assert not planning.exists(), (
            "settings.planning.json must NOT be written when settings.json was "
            "the installer's own to create"
        )
        content = json.loads(settings.read_text(encoding="utf-8"))
        assert "permissions" in content
        assert "planning" in content

    def test_existing_settings_json_preserved_byte_identical(
        self, project_dir: Path, install_sh: Path, repo_root: Path
    ):
        _skip_bash()
        settings, original = _seed_settings(project_dir)

        result = _run_sh(install_sh, "--project", _fwd(project_dir), cwd=repo_root)
        assert result.returncode == 0, f"install failed: {result.stderr}"

        assert settings.read_text(encoding="utf-8") == original, (
            "settings.json must be preserved byte-identical"
        )
        planning = project_dir / ".claude" / "settings.planning.json"
        assert planning.exists(), (
            "settings.planning.json should carry the planning config instead. "
            f"stdout: {result.stdout}"
        )
        planning_content = json.loads(planning.read_text(encoding="utf-8"))
        assert "permissions" in planning_content
        assert "planning" in planning_content

    def test_dry_run_reports_the_planning_branch_and_writes_nothing(
        self, project_dir: Path, install_sh: Path, repo_root: Path
    ):
        _skip_bash()
        settings, original = _seed_settings(project_dir)

        result = _run_sh(
            install_sh, "--project", _fwd(project_dir), "--dry-run", cwd=repo_root
        )

        assert "settings.planning.json" in result.stdout, (
            f"dry-run must name the branch it would take. stdout: {result.stdout}"
        )
        assert settings.read_text(encoding="utf-8") == original
        assert not (project_dir / ".claude" / "settings.planning.json").exists(), (
            "a dry run must not write the planning file it only described"
        )


class TestS1PwshSettingsPreservation:
    """install.ps1 must behave identically to install.sh."""

    def test_no_existing_settings_json_is_written_normally(
        self, project_dir: Path, install_ps1: Path, repo_root: Path
    ):
        _skip_pwsh()
        result = _run_ps1(install_ps1, "-Project", str(project_dir), cwd=repo_root)
        assert result.returncode == 0, f"install failed: {result.stderr}"

        settings = project_dir / ".claude" / "settings.json"
        planning = project_dir / ".claude" / "settings.planning.json"
        assert settings.exists(), f"settings.json should be written. stderr: {result.stderr}"
        assert not planning.exists()
        content = json.loads(settings.read_text(encoding="utf-8"))
        assert "permissions" in content
        assert "planning" in content

    def test_existing_settings_json_preserved_byte_identical(
        self, project_dir: Path, install_ps1: Path, repo_root: Path
    ):
        _skip_pwsh()
        settings, original = _seed_settings(project_dir)

        result = _run_ps1(install_ps1, "-Project", str(project_dir), cwd=repo_root)
        assert result.returncode == 0, f"install failed: {result.stderr}"

        assert settings.read_text(encoding="utf-8") == original, (
            "settings.json must be preserved byte-identical"
        )
        planning = project_dir / ".claude" / "settings.planning.json"
        assert planning.exists(), f"stdout: {result.stdout}"
        planning_content = json.loads(planning.read_text(encoding="utf-8"))
        assert "permissions" in planning_content
        assert "planning" in planning_content

    def test_dry_run_reports_the_planning_branch_and_writes_nothing(
        self, project_dir: Path, install_ps1: Path, repo_root: Path
    ):
        _skip_pwsh()
        settings, original = _seed_settings(project_dir)

        result = _run_ps1(
            install_ps1, "-Project", str(project_dir), "-DryRun", cwd=repo_root
        )

        assert "settings.planning.json" in result.stdout, (
            f"dry-run must name the branch it would take. stdout: {result.stdout}"
        )
        assert settings.read_text(encoding="utf-8") == original
        assert not (project_dir / ".claude" / "settings.planning.json").exists()


# ---------------------------------------------------------------------------
# S3b - do_ln must refuse a real directory rather than nest inside it
# ---------------------------------------------------------------------------

class TestS3bBashLnSafety:
    """`ln -sf SRC DEST` where DEST is a real directory silently creates
    DEST/basename(SRC). The pre-fix installer did exactly that and exited 0."""

    def test_refuses_real_directory_and_creates_no_nested_link(
        self, project_dir: Path, install_sh: Path, repo_root: Path
    ):
        _skip_bash()
        skills = project_dir / ".claude" / "skills"
        skills.mkdir()
        keeper = skills / "keep.txt"
        keeper.write_text("must not be deleted", encoding="utf-8")

        result = _run_sh(
            install_sh, "--project", _fwd(project_dir), "--symlink", cwd=repo_root
        )

        assert result.returncode != 0, (
            "installing over a real skills directory must fail, not succeed "
            f"quietly. stdout: {result.stdout}"
        )
        assert "real directory" in result.stderr.lower(), (
            f"the error must say why it refused. stderr: {result.stderr}"
        )
        assert _fwd(skills) in _fwd(result.stderr), (
            f"the error must name the path it refused. stderr: {result.stderr}"
        )
        assert keeper.read_text(encoding="utf-8") == "must not be deleted", (
            "the user's directory contents must survive"
        )
        assert not (skills / "skills").exists(), (
            "a nested link inside the real directory is the S3b bug"
        )

    def test_dry_run_reports_the_refusal_it_would_make(
        self, project_dir: Path, install_sh: Path, repo_root: Path
    ):
        _skip_bash()
        skills = project_dir / ".claude" / "skills"
        skills.mkdir()

        result = _run_sh(
            install_sh, "--project", _fwd(project_dir), "--symlink", "--dry-run",
            cwd=repo_root,
        )

        assert "would refuse" in result.stdout, (
            "a dry run that reports a link where the real run refuses is a "
            f"report of work that will not happen. stdout: {result.stdout}"
        )
        assert not (skills / "skills").exists()

    def test_replaces_an_existing_symlink(
        self, project_dir: Path, install_sh: Path, repo_root: Path, tmp_path: Path
    ):
        _skip_bash()
        old_target = tmp_path / "old_target"
        old_target.mkdir()
        link = project_dir / ".claude" / "skills"
        try:
            link.symlink_to(old_target, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            pytest.skip(
                f"cannot create a directory symlink here ({exc}) - on Windows "
                "this needs Developer Mode or elevation. This is a skip, not a "
                "pass: the replace-a-symlink path was not verified."
            )

        result = _run_sh(
            install_sh, "--project", _fwd(project_dir), "--symlink", cwd=repo_root
        )

        assert result.returncode == 0, (
            f"replacing an existing symlink must succeed. stderr: {result.stderr}"
        )
        assert link.is_symlink() or link.is_dir(), "the link must still be there"
        resolved = link.resolve()
        assert resolved != old_target.resolve(), (
            f"the link must be repointed away from the old target, got {resolved}"
        )
        assert any(resolved.iterdir()), "the link must point at the real skills tree"


# ---------------------------------------------------------------------------
# S3 / self-install - the caller must not bypass the junction guard
# ---------------------------------------------------------------------------

class TestSelfInstallDoesNotBypassGuards:
    """Do-Junction refuses a non-reparse-point destination, but that guard is
    worth nothing if its caller has already deleted the directory."""

    def test_ps1_self_install_refuses_a_real_skills_directory(self, fake_repo: Path):
        _skip_pwsh()
        skills = fake_repo / ".claude" / "skills"
        skills.mkdir(parents=True)
        keeper = skills / "keep.txt"
        keeper.write_text("must not be deleted", encoding="utf-8")

        script = fake_repo / "setup" / "claude-code" / "install.ps1"
        result = _run_ps1(script, "-Project", str(fake_repo), cwd=fake_repo)

        assert "SELF-INSTALL" in result.stdout, (
            "the fixture must actually reach the self-install branch. "
            f"stdout: {result.stdout}"
        )
        _assert_reached_runtime_dirs(result, "install.ps1")
        assert keeper.exists() and keeper.read_text(encoding="utf-8") == "must not be deleted", (
            "self-install recursively deleted a real skills directory: the "
            f"Do-Junction guard was bypassed by its caller. stdout: {result.stdout}"
        )
        assert result.returncode != 0, (
            "refusing to install over a real directory must be reported as failure"
        )

    def test_ps1_self_install_refuses_a_real_agents_directory(self, fake_repo: Path):
        _skip_pwsh()
        agents = fake_repo / ".claude" / "agents"
        agents.mkdir(parents=True)
        keeper = agents / "my-own-agent.md"
        keeper.write_text("# mine", encoding="utf-8")

        script = fake_repo / "setup" / "claude-code" / "install.ps1"
        result = _run_ps1(script, "-Project", str(fake_repo), cwd=fake_repo)

        assert "SELF-INSTALL" in result.stdout, f"stdout: {result.stdout}"
        _assert_reached_runtime_dirs(result, "install.ps1")
        assert keeper.exists(), (
            "self-install recursively deleted a real agents directory, taking "
            f"the user's own agents with it. stdout: {result.stdout}"
        )

    def test_sh_self_install_refuses_a_real_skills_directory(self, fake_repo: Path):
        _skip_bash()
        skills = fake_repo / ".claude" / "skills"
        skills.mkdir(parents=True)
        keeper = skills / "keep.txt"
        keeper.write_text("must not be deleted", encoding="utf-8")

        script = fake_repo / "setup" / "claude-code" / "install.sh"
        result = _run_sh(script, "--project", _fwd(fake_repo), cwd=fake_repo)

        assert "Self-install detected" in result.stdout, (
            "the fixture must actually reach the self-install branch. "
            f"stdout: {result.stdout}"
        )
        _assert_reached_runtime_dirs(result, "install.sh")
        assert result.returncode != 0
        assert keeper.read_text(encoding="utf-8") == "must not be deleted"


# ---------------------------------------------------------------------------
# Syntax and coverage
# ---------------------------------------------------------------------------

class TestSyntaxAndCoverage:

    def test_sh_syntax(self, install_sh: Path):
        _skip_bash()
        result = _run([GIT_BASH, "-n", _fwd(install_sh)])
        assert result.returncode == 0, f"install.sh syntax error:\n{result.stderr}"

    def test_ps1_syntax(self, install_ps1: Path, tmp_path: Path):
        _skip_pwsh()
        checker = tmp_path / "check.ps1"
        checker.write_text(
            "$errors = $null\n"
            f"$content = Get-Content -Raw -LiteralPath '{install_ps1}'\n"
            "$null = [System.Management.Automation.PSParser]::Tokenize("
            "$content, [ref]$errors)\n"
            "if ($errors.Count -gt 0) { $errors | ForEach-Object "
            "{ Write-Error $_.Message }; exit 1 }\n"
            "exit 0\n",
            encoding="utf-8",
        )
        result = _run(
            [PWSH, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(checker)]
        )
        assert result.returncode == 0, f"install.ps1 syntax error:\n{result.stderr}"

    def test_at_least_one_host_was_exercised(self):
        """Fail if every installer test in this file skipped.

        A file of skipped tests reports green and proves nothing, which is the
        exact defect class these tests exist to catch.
        """
        hosts = []
        if _bash_available():
            hosts.append(f"Git Bash ({GIT_BASH})")
        if _pwsh_available():
            hosts.append(f"pwsh ({PWSH})")
        assert hosts, (
            "Neither Git Bash nor pwsh is available, so every installer test in "
            "this file skipped and this run proved nothing about the "
            "installers. Install one, or run these tests on a host that has one."
        )


# ---------------------------------------------------------------------------
# S3b in the OTHER installer - platforms/claude-code/install.sh
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def adapter_install_sh(repo_root: Path) -> Path:
    """The second installer.

    setup/claude-code/install.sh got the S3b fix in the commit that added
    TestS3bBashLnSafety above. This one did not, and no test named it, so it
    kept the original defect for the whole time the fixed script sat beside it
    under test.
    """
    return repo_root / "platforms" / "claude-code" / "install.sh"


def _core_skill_names(repo_root: Path):
    return sorted(p.name for p in (repo_root / "core" / "skills").iterdir() if p.is_dir())


class TestAdapterInstallerSkillPlacement:
    """`ln -sf SRC DEST` where DEST already exists as a real directory does not
    replace it - it creates DEST/basename(SRC) inside it and exits 0. `cp -r`
    nests identically. The pre-fix adapter installer did both, and announced
    "Symlinked" either way."""

    def test_second_install_creates_no_nested_skill(
        self, tmp_path: Path, adapter_install_sh: Path, repo_root: Path
    ):
        _skip_bash()
        project = tmp_path / "project"
        (project / ".claude").mkdir(parents=True)

        first = _run_sh(adapter_install_sh, "--project", _fwd(project), cwd=repo_root)
        assert first.returncode == 0, f"first install failed: {first.stderr}"
        second = _run_sh(adapter_install_sh, "--project", _fwd(project), cwd=repo_root)
        assert second.returncode == 0, (
            f"re-installing an unchanged project must succeed: {second.stderr}"
        )

        names = _core_skill_names(repo_root)
        assert names, "core/skills is empty, so this test would prove nothing"
        skills = project / ".claude" / "skills"
        nested = [n for n in names if (skills / n / n).exists()]
        assert not nested, (
            f"installing twice nested a copy of each skill inside itself: {nested}"
        )

    def test_message_names_what_is_actually_on_disk(
        self, tmp_path: Path, adapter_install_sh: Path, repo_root: Path
    ):
        """Whether ln links or silently copies is the host's business; claiming
        the wrong one is the installer's.

        MSYS ln on Windows copies and exits 0, so the pre-fix script printed
        "Symlinked" for a plain copy - a claim about the machine that nothing
        had read back off it. This asserts agreement, not which branch ran, so
        it holds on every host.
        """
        _skip_bash()
        project = tmp_path / "project"
        (project / ".claude").mkdir(parents=True)

        result = _run_sh(adapter_install_sh, "--project", _fwd(project), cwd=repo_root)
        assert result.returncode == 0, f"install failed: {result.stderr}"

        claims = {}
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if "✓" not in stripped:
                continue
            for verb in ("Symlinked", "Copied"):
                marker = verb + " "
                if marker in stripped:
                    claims[stripped.split(marker, 1)[1].strip()] = verb
        assert claims, (
            f"installer reported no skill placements at all:\n{result.stdout}"
        )

        skills = project / ".claude" / "skills"
        wrong = []
        for name, verb in sorted(claims.items()):
            dest = skills / name
            if verb == "Symlinked" and not dest.is_symlink():
                wrong.append(f"{name}: said Symlinked, is not a symlink")
            if verb == "Copied" and dest.is_symlink():
                wrong.append(f"{name}: said Copied, is a symlink")
        assert not wrong, (
            "the installer's success line disagrees with the filesystem:\n  "
            + "\n  ".join(wrong)
        )

    def test_refuses_a_diverged_skill_directory(
        self, tmp_path: Path, adapter_install_sh: Path, repo_root: Path
    ):
        _skip_bash()
        project = tmp_path / "project"
        (project / ".claude").mkdir(parents=True)
        first = _run_sh(adapter_install_sh, "--project", _fwd(project), cwd=repo_root)
        assert first.returncode == 0, f"first install failed: {first.stderr}"

        skills = project / ".claude" / "skills"
        target = None
        for name in _core_skill_names(repo_root):
            candidate = skills / name / "SKILL.md"
            if candidate.exists() and not (skills / name).is_symlink():
                target = (name, candidate)
                break
        if target is None:
            pytest.skip(
                "every skill installed as a symlink here, so editing one would "
                "write through the link into core/skills in the source repo. "
                "This is a skip, not a pass: the divergence refusal was not "
                "verified on this host."
            )

        name, edited = target
        edited.write_text(
            edited.read_text(encoding="utf-8") + "\nDRIFT\n", encoding="utf-8"
        )

        result = _run_sh(adapter_install_sh, "--project", _fwd(project), cwd=repo_root)

        assert result.returncode != 0, (
            "installing over a diverged skill must fail, not nest a copy inside "
            f"it. stdout: {result.stdout}"
        )
        assert "differ" in result.stderr.lower(), (
            f"the error must say why it refused. stderr: {result.stderr}"
        )
        assert name in result.stderr, (
            f"the error must name the skill it refused. stderr: {result.stderr}"
        )
        assert not (skills / name / name).exists(), (
            "a refusal that still nests a copy has refused nothing"
        )

    def test_refuses_a_regular_file_at_the_destination(
        self, tmp_path: Path, adapter_install_sh: Path, repo_root: Path
    ):
        _skip_bash()
        project = tmp_path / "project"
        skills = project / ".claude" / "skills"
        skills.mkdir(parents=True)
        names = _core_skill_names(repo_root)
        assert names, "core/skills is empty, so this test would prove nothing"

        squatter = skills / names[0]
        squatter.write_text("user content that must survive", encoding="utf-8")

        result = _run_sh(adapter_install_sh, "--project", _fwd(project), cwd=repo_root)

        assert result.returncode != 0, (
            f"installing over a user's file must fail. stdout: {result.stdout}"
        )
        assert "regular file" in result.stderr.lower(), (
            f"the error must say why it refused. stderr: {result.stderr}"
        )
        assert squatter.is_file(), "the user's file must not become a directory"
        assert squatter.read_text(encoding="utf-8") == "user content that must survive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
