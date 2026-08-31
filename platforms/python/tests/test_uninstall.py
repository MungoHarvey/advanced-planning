# -*- coding: utf-8 -*-
"""The uninstaller must remove the mechanism and leave the user's work.

There was no uninstall path at all until now; both reviewers on the follow-up
round reported that independently, and one made the point that decides the
design: the mechanism files live in the *same directory* as the planning
record. ``.advanced-plans/`` holds ``bin/ap.py`` and ``runtime.json``, which are
ours, next to ``phases/``, ``specs/``, ``state/``, ``logs/`` and ``PLANNING.md``,
which are the user's and which the installer itself creates and migrates legacy
plans into. So uninstalling cannot be a directory removal. It has to be the
removal of a known set of names, and the tests that matter are the ones about
what is still there afterwards.

Three properties are pinned here:

  1. **Dry run is the default.** Run without the confirmation flag, nothing is
     deleted. Tested by running it, not by reading it.
  2. **Only what this checkout provides is removed.** A file in
     ``.claude/commands/`` that the checkout does not supply was not installed
     from here, and survives.
  3. **The launcher goes last.** Commands that invoke a launcher which is no
     longer there produce the interpreter's own "can't open file" and exit
     before any of this system's code runs, so nothing can name the cause. That
     is the exact failure the shared-runtime work exists to eliminate, and a
     partial uninstall is a way back into it. A launcher with no commands is
     inert instead, so the ordering is chosen to fail in the harmless
     direction.
"""

import os
import shutil
import subprocess
import sys
import pathlib

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]

_UNINSTALL_SH = _REPO_ROOT / "setup" / "claude-code" / "uninstall.sh"
_UNINSTALL_PS1 = _REPO_ROOT / "setup" / "claude-code" / "uninstall.ps1"

# Names under .advanced-plans/ that are the user's planning record. An
# uninstaller that mentions any of these in a removal is deleting work.
_USER_DATA = ["phases", "specs", "state", "logs", "PLANNING.md"]


def _read(path):
    with open(str(path), encoding="utf-8", newline="") as handle:
        return handle.read().replace("\r\n", "\n")


def test_both_uninstallers_exist():
    """Parity with the installers, which ship .sh and .ps1 side by side.

    A shell-only uninstaller is not an uninstaller on the platform most of this
    system's Windows users are on, and the project has been bitten by exactly
    that asymmetry before.
    """
    assert _UNINSTALL_SH.exists(), "no setup/claude-code/uninstall.sh"
    assert _UNINSTALL_PS1.exists(), (
        "no setup/claude-code/uninstall.ps1 -- install.ps1 exists, so a "
        "shell-only uninstall path leaves Windows users with no supported way "
        "to remove what they installed")


@pytest.mark.parametrize("path,flag", [
    (_UNINSTALL_SH, "--yes"),
    (_UNINSTALL_PS1, "Yes"),
])
def test_deleting_requires_an_explicit_confirmation(path, flag):
    text = _read(path)
    assert flag in text, (
        "%s has no %s flag. This deletes files under a home directory and "
        "inside a project; acting without an explicit confirmation is not a "
        "default this should have." % (path.name, flag))


@pytest.mark.parametrize("path", [_UNINSTALL_SH, _UNINSTALL_PS1],
                         ids=["sh", "ps1"])
def test_the_launcher_is_removed_after_the_commands(path):
    """Ordering, checked by position in the file.

    Crude, and the right crudeness: both scripts are linear, and the property
    is exactly "the text that removes commands comes before the text that
    removes the launcher".
    """
    text = _read(path)
    commands_at = text.index("Slash commands:")
    launcher_at = text.index("Shared Python runtime:")
    assert commands_at < launcher_at, (
        "%s removes the shared runtime before the slash commands. If it fails "
        "in between, the project is left with commands whose launcher is gone "
        "-- the one state this system cannot diagnose, because the interpreter "
        "exits before any of its code runs." % path.name)


@pytest.mark.parametrize("name", _USER_DATA)
@pytest.mark.parametrize("path", [_UNINSTALL_SH, _UNINSTALL_PS1],
                         ids=["sh", "ps1"])
def test_no_uninstaller_removes_the_planning_record(path, name):
    """The planning record may only appear in the "left in place" list."""
    text = _read(path)
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if name not in stripped:
            continue
        lowered = stripped.lower()
        is_removal = any(tok in lowered for tok in
                         ("rm -", "rm_", "remove-item", "remove-appath",
                          "remove_path", "rmdir", "directory]::delete"))
        assert not is_removal, (
            "%s appears to remove %r: %s\nThat is the user's planning record, "
            "not part of the install." % (path.name, name, stripped))


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX sh available")
def test_a_dry_run_deletes_nothing(tmp_path):
    """Run it. The default has to be safe in fact, not in intent."""
    project = tmp_path / "proj"
    claude = project / ".claude" / "commands"
    ap_bin = project / ".advanced-plans" / "bin"
    phases = project / ".advanced-plans" / "phases"
    for directory in (claude, ap_bin, phases):
        directory.mkdir(parents=True)

    # One real command name, so there is something the uninstaller recognises.
    commands_src = _REPO_ROOT / "platforms" / "claude-code" / "commands"
    real = sorted(commands_src.glob("*.md"))[0].name
    (claude / real).write_text("installed", encoding="utf-8")
    (claude / "not-ours.md").write_text("foreign", encoding="utf-8")
    (ap_bin / "ap.py").write_text("launcher", encoding="utf-8")
    (project / ".advanced-plans" / "runtime.json").write_text("{}", encoding="utf-8")
    (phases / "my-phase.md").write_text("my work", encoding="utf-8")

    before = sorted(str(p.relative_to(project))
                    for p in project.rglob("*") if p.is_file())

    proc = subprocess.Popen(
        ["sh", str(_UNINSTALL_SH), "--project", str(project)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True, cwd=str(_REPO_ROOT))
    out, err = proc.communicate(timeout=120)
    assert proc.returncode == 0, "dry run exited %d: %s" % (proc.returncode, err)

    after = sorted(str(p.relative_to(project))
                   for p in project.rglob("*") if p.is_file())
    assert before == after, (
        "the dry run deleted files. Removed: %s"
        % sorted(set(before) - set(after)))
    assert "DRY RUN" in out, "the dry run does not say that it is one"


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX sh available")
def test_a_confirmed_run_removes_the_mechanism_and_keeps_the_work(tmp_path):
    project = tmp_path / "proj"
    claude = project / ".claude" / "commands"
    ap_bin = project / ".advanced-plans" / "bin"
    phases = project / ".advanced-plans" / "phases"
    for directory in (claude, ap_bin, phases):
        directory.mkdir(parents=True)

    commands_src = _REPO_ROOT / "platforms" / "claude-code" / "commands"
    real = sorted(commands_src.glob("*.md"))[0].name
    (claude / real).write_text("installed", encoding="utf-8")
    (claude / "not-ours.md").write_text("foreign", encoding="utf-8")
    (ap_bin / "ap.py").write_text("launcher", encoding="utf-8")
    (project / ".advanced-plans" / "runtime.json").write_text("{}", encoding="utf-8")
    (phases / "my-phase.md").write_text("my work", encoding="utf-8")
    settings = project / ".claude" / "settings.json"
    settings.write_text("{}", encoding="utf-8")

    proc = subprocess.Popen(
        ["sh", str(_UNINSTALL_SH), "--project", str(project), "--yes"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True, cwd=str(_REPO_ROOT))
    out, err = proc.communicate(timeout=120)
    assert proc.returncode == 0, "uninstall exited %d: %s" % (proc.returncode, err)

    assert not (claude / real).exists(), "the installed command was not removed"
    assert not (ap_bin / "ap.py").exists(), "the launcher was not removed"
    assert not (project / ".advanced-plans" / "runtime.json").exists(), (
        "the runtime record was not removed")

    assert (claude / "not-ours.md").exists(), (
        "a command this checkout never provided was removed. The uninstaller "
        "may only remove names the installer would have written.")
    assert (phases / "my-phase.md").exists(), (
        "the user's planning record was removed")
    assert settings.exists(), (
        "settings.json was removed. It may be entirely the user's, and nothing "
        "records which, so it is reported rather than deleted.")


def _make_dir_link(link, target):
    """A directory link, by whatever means this host allows. False if none.

    Returning False rather than faking one matters: the tests below exist to
    prove the uninstaller does not delete *through* a link, and a fixture that
    is quietly a plain copy proves nothing while still passing. That failure
    mode is not hypothetical -- ``ln -s`` under Git Bash produces a copy here,
    which is how the defect these tests cover survived its first fixture.
    """
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
        return True
    except (OSError, AttributeError, NotImplementedError):
        pass
    if os.name != "nt":
        return False
    # A junction needs no privilege where a symlink does, and Git Bash reports
    # one as both -L and -d, so it exercises the same branch.
    proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         "New-Item -ItemType Junction -Path '%s' -Target '%s' | Out-Null"
         % (str(link), str(target))],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    proc.communicate(timeout=120)
    return proc.returncode == 0 and os.path.isdir(str(link))


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX sh available")
def test_a_linked_command_dir_is_unlinked_not_walked(tmp_path):
    """The destination itself can be a link into the source checkout.

    install.sh replaces .claude/commands, skills and schemas wholesale with
    symlinks in self-install mode -- the mode this repository installs itself
    in -- and install.ps1 uses junctions for the same thing. ``[ -d ]`` follows
    a link, so an uninstaller that walks the destination would resolve each
    name through it and delete the *source* file. The files inside are not
    themselves links, so the per-path guard does not catch this; the check has
    to be at the destination.

    The link here points at a fixture copy rather than the real
    platforms/claude-code/commands, deliberately: if this regresses, the test
    must fail, not delete the checkout it is running in.
    """
    real_names = [p.name for p in
                  sorted((_REPO_ROOT / "platforms" / "claude-code" / "commands").glob("*.md"))]
    assert real_names, "no commands in the source checkout to model"

    stand_in = tmp_path / "stand-in-checkout"
    stand_in.mkdir()
    for name in real_names:
        (stand_in / name).write_text("source copy", encoding="utf-8")

    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    (project / ".advanced-plans" / "bin").mkdir(parents=True)

    if not _make_dir_link(project / ".claude" / "commands", stand_in):
        pytest.skip("this host cannot create a directory link "
                    "(no symlink privilege and no junction support)")

    proc = subprocess.Popen(
        ["sh", str(_UNINSTALL_SH), "--project", str(project), "--yes"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True, cwd=str(_REPO_ROOT))
    out, err = proc.communicate(timeout=180)
    assert proc.returncode == 0, "uninstall exited %d: %s" % (proc.returncode, err)

    survivors = sorted(p.name for p in stand_in.glob("*.md"))
    assert survivors == sorted(real_names), (
        "the uninstaller deleted through the link. %d of %d source files are "
        "gone: %s" % (len(real_names) - len(survivors), len(real_names),
                      sorted(set(real_names) - set(survivors))))
    assert not os.path.lexists(str(project / ".claude" / "commands")), (
        "the link itself was not removed; unlinking it is the whole uninstall "
        "for a linked destination")
