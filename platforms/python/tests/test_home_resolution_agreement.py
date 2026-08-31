# -*- coding: utf-8 -*-
"""The USERPROFILE-before-HOME rule has five implementations. Pin all five.

``ap_launcher.global_home`` and ``install_audit.resolve_global_home`` are
already pinned against each other by ``test_global_home_agrees_with_install_audit``.
That test covers two of the five copies. The other three are the ones that
actually write to disk:

  * ``ap_home_fs`` / ``ap_home_native`` in ``setup/claude-code/install.sh``
  * ``ap_home_fs`` / ``ap_home_native`` in ``platforms/claude-code/install.sh``
  * ``Get-ApGlobalHome`` in ``setup/claude-code/install.ps1``

A cross-vendor reviewer put the reason for this module in one sentence: "the
real drift risk is the shell/PowerShell copies, which is how this class of bug
actually ships." Writing the record from one home and reading it from another
is the original unreachable-runtime defect wearing a different hat, so the
agreement is a correctness property, not tidiness.

Two failures were live when this module was written, and both were found by
running the implementations rather than reading them:

  1. ``Get-ApGlobalHome`` never consulted ``$env:HOME`` at all -- it fell back
     to PowerShell's *automatic* ``$HOME``, which is derived from
     HOMEDRIVE/HOMEPATH and is empty when those are unset. With USERPROFILE
     unset and HOME set, Python resolved the HOME path and PowerShell resolved
     to the empty string, whereupon ``Join-Path`` threw and the install aborted
     somewhere Python would have succeeded.
  2. Both shell copies returned the *empty string* when neither variable was
     set, and the caller then built ``"$(ap_home_fs)/.claude"`` -- so
     ``mkdir -p`` was pointed at ``/.claude``, at the filesystem root. Silent,
     and the one failure mode here that writes outside the user's profile.

Comparing exact strings across platforms is not possible: on Windows these
functions run under Git Bash and route through ``cygpath``, so ``C:/x`` becomes
``/c/x``. What is portable, and what actually matters, is *which variable the
answer came from* -- so each case uses a distinct marker token and asserts the
token, not the path.
"""

import os
import re
import shutil
import subprocess
import sys
import pathlib

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from platforms.python import ap_launcher  # noqa: E402

_MARKER_UP = "ap_marker_userprofile"
_MARKER_HOME = "ap_marker_home"

# Native-looking values so the Windows path conversion has something to chew
# on; the marker segment survives cygpath in either direction.
_UP_VALUE = "C:/" + _MARKER_UP
_HOME_VALUE = "M:/" + _MARKER_HOME

# (case id, env overrides, expected marker). ``None`` for a variable means
# "remove it from the child's environment entirely" -- distinct from "" which
# is the empty-string case the rule treats as absent.
_CASES = [
    ("both-set", {"USERPROFILE": _UP_VALUE, "HOME": _HOME_VALUE}, _MARKER_UP),
    ("userprofile-only", {"USERPROFILE": _UP_VALUE, "HOME": None}, _MARKER_UP),
    ("home-only", {"USERPROFILE": None, "HOME": _HOME_VALUE}, _MARKER_HOME),
    ("userprofile-empty", {"USERPROFILE": "", "HOME": _HOME_VALUE}, _MARKER_HOME),
]

_SH_IMPLEMENTATIONS = [
    ("setup/claude-code/install.sh", "ap_home_fs"),
    ("setup/claude-code/install.sh", "ap_home_native"),
    ("platforms/claude-code/install.sh", "ap_home_fs"),
    ("platforms/claude-code/install.sh", "ap_home_native"),
    # The uninstaller resolves the same home, and getting it wrong there is
    # quieter than getting it wrong in the installer: it would remove nothing
    # from a home nothing was installed into, and report success.
    ("setup/claude-code/uninstall.sh", "ap_home_fs"),
]

_ALL_IMPLEMENTATIONS = [
    ("platforms/python/ap_launcher.py", "global_home"),
    ("platforms/python/install_audit.py", "resolve_global_home"),
    ("setup/claude-code/install.sh", "ap_home_fs"),
    ("setup/claude-code/install.sh", "ap_home_native"),
    ("platforms/claude-code/install.sh", "ap_home_fs"),
    ("platforms/claude-code/install.sh", "ap_home_native"),
    ("setup/claude-code/install.ps1", "Get-ApGlobalHome"),
    ("setup/claude-code/uninstall.sh", "ap_home_fs"),
    ("setup/claude-code/uninstall.ps1", "Get-ApGlobalHome"),
]


def _read(rel):
    path = _REPO_ROOT / rel
    with open(str(path), encoding="utf-8", newline="") as handle:
        return handle.read().replace("\r\n", "\n")


def _extract_sh_function(rel, name):
    """The text of one POSIX shell function, so it can be run in isolation.

    Running the installer itself is not an option -- it would install. The
    functions are self-contained by construction, which is what makes this
    possible and is worth keeping true.
    """
    text = _read(rel)
    pattern = re.compile(
        r"^" + re.escape(name) + r"\(\)\s*\{.*?^\}", re.M | re.S)
    match = pattern.search(text)
    assert match, "%s: no POSIX function named %s()" % (rel, name)
    return match.group(0)


def _extract_ps_function(rel, name):
    text = _read(rel)
    pattern = re.compile(
        r"^function\s+" + re.escape(name) + r"\s*\{.*?^\}", re.M | re.S)
    match = pattern.search(text)
    assert match, "%s: no PowerShell function named %s" % (rel, name)
    return match.group(0)


def _child_env(overrides):
    env = dict(os.environ)
    for key, value in overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return env


def _run(argv, env):
    proc = subprocess.Popen(
        argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True)
    out, err = proc.communicate(timeout=60)
    return proc.returncode, out, err


# ---------------------------------------------------------------------------
# The reference: what every other copy has to agree with.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case_id,overrides,expected", _CASES,
                         ids=[c[0] for c in _CASES])
def test_the_python_reference_picks_the_expected_variable(
        case_id, overrides, expected):
    """Guards the test's own premise before it is used to judge others."""
    env = {k: v for k, v in overrides.items() if v is not None}
    assert expected in ap_launcher.global_home(env), (
        "the reference implementation does not resolve %s as this module "
        "assumes; every assertion below is built on it" % case_id)


# ---------------------------------------------------------------------------
# The three unpinned copies, run rather than read.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX sh available")
@pytest.mark.parametrize("script,func", _SH_IMPLEMENTATIONS,
                         ids=["%s:%s" % (s.split("/")[0], f)
                              for s, f in _SH_IMPLEMENTATIONS])
@pytest.mark.parametrize("case_id,overrides,expected", _CASES,
                         ids=[c[0] for c in _CASES])
def test_a_shell_copy_resolves_the_same_variable_as_the_launcher(
        script, func, case_id, overrides, expected):
    body = _extract_sh_function(script, func)
    rc, out, err = _run(["sh", "-c", body + "\n" + func],
                        _child_env(overrides))
    assert rc == 0, "%s:%s exited %d for %s: %s" % (
        script, func, rc, case_id, err.strip())
    assert expected in out, (
        "%s:%s resolved %r for the %s case, which does not come from the "
        "variable the launcher picks (%s). The installer would write the "
        "runtime record to one home while the launcher reads it from "
        "another -- the unreachable-runtime defect, reintroduced through "
        "the installer rather than the call sites."
        % (script, func, out.strip(), case_id, expected))


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="no pwsh available")
@pytest.mark.parametrize("script", ["setup/claude-code/install.ps1",
                                    "setup/claude-code/uninstall.ps1"])
@pytest.mark.parametrize("case_id,overrides,expected", _CASES,
                         ids=[c[0] for c in _CASES])
def test_the_powershell_copy_resolves_the_same_variable_as_the_launcher(
        script, case_id, overrides, expected):
    body = _extract_ps_function(script, "Get-ApGlobalHome")
    rc, out, err = _run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command",
         body + "\nGet-ApGlobalHome"],
        _child_env(overrides))
    assert rc == 0, "Get-ApGlobalHome exited %d for %s: %s" % (
        rc, case_id, err.strip())
    assert expected in out, (
        "Get-ApGlobalHome resolved %r for the %s case rather than the %s the "
        "launcher picks. PowerShell's automatic $HOME is not $env:HOME: it is "
        "derived from HOMEDRIVE/HOMEPATH and is empty when those are unset, "
        "so falling back to it does not implement the documented "
        "USERPROFILE-before-HOME rule."
        % (out.strip(), case_id, expected))


# ---------------------------------------------------------------------------
# The empty home. This is the case that writes outside the user's profile.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX sh available")
@pytest.mark.parametrize("script,func", _SH_IMPLEMENTATIONS,
                         ids=["%s:%s" % (s.split("/")[0], f)
                              for s, f in _SH_IMPLEMENTATIONS])
def test_a_shell_copy_never_resolves_the_home_to_nothing(script, func):
    """With neither variable set, an empty answer aims mkdir at ``/``.

    The callers build ``"$(ap_home_fs)/.claude"`` and ``mkdir -p`` it. An empty
    resolution therefore does not fail -- it succeeds, at the filesystem root,
    which is the only path in this mechanism that writes outside the profile it
    was asked to install into. Failing loudly is the agreement; a non-empty
    answer is also acceptable, since the launcher has its own fallback.
    """
    # `unset` INSIDE the shell, not a stripped child environment: Git Bash
    # repopulates HOME from the Windows profile during startup, so removing it
    # from the child env leaves this case unreachable on Windows and reachable
    # only on the POSIX runners -- a test that would pass here for a reason
    # having nothing to do with the code. Unsetting after init is
    # deterministic on both.
    body = _extract_sh_function(script, func)
    rc, out, err = _run(
        ["sh", "-c", "unset HOME USERPROFILE\n" + body + "\n" + func],
        dict(os.environ))
    if rc == 0:
        assert out.strip(), (
            "%s:%s succeeded with empty output when neither USERPROFILE nor "
            "HOME is set. The caller appends '/.claude' to this and runs "
            "mkdir -p, so the install lands at the filesystem root."
            % (script, func))


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="no pwsh available")
@pytest.mark.parametrize("script", ["setup/claude-code/install.ps1",
                                    "setup/claude-code/uninstall.ps1"])
def test_the_powershell_copy_never_resolves_the_home_to_nothing(script):
    body = _extract_ps_function(script, "Get-ApGlobalHome")
    rc, out, err = _run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command",
         body + "\nGet-ApGlobalHome"],
        _child_env({"USERPROFILE": None, "HOME": None}))
    if rc == 0:
        assert out.strip(), (
            "Get-ApGlobalHome succeeded with empty output when neither "
            "USERPROFILE nor HOME is set. Join-Path then throws, so the "
            "install aborts with a binding error that names neither the "
            "cause nor the repair.")


# ---------------------------------------------------------------------------
# The backstop that needs no interpreter, so it runs everywhere CI does.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("script,func", _ALL_IMPLEMENTATIONS,
                         ids=["%s:%s" % (s.split("/")[-1], f)
                              for s, f in _ALL_IMPLEMENTATIONS])
def test_every_copy_of_the_rule_reads_userprofile_before_home(script, func):
    """Textual, and deliberately so.

    The executable tests above skip when their interpreter is missing. This one
    cannot skip, which makes it the check that is guaranteed to run in CI --
    weaker, but never absent. It fails on the ordering, which is the property
    the rule is named for.
    """
    text = _read(script)
    if script.endswith(".ps1"):
        body = _extract_ps_function(script, func)
    elif script.endswith(".sh"):
        body = _extract_sh_function(script, func)
    else:
        # Python: from the def to the next top-level def.
        match = re.search(
            r"^def\s+" + re.escape(func) + r"\(.*?(?=^def |\Z)",
            text, re.M | re.S)
        assert match, "%s: no def %s" % (script, func)
        body = match.group(0)

    up = body.find("USERPROFILE")
    home = re.search(r"\bHOME\b", body)
    assert up != -1, "%s:%s never mentions USERPROFILE" % (script, func)
    assert home, "%s:%s never mentions HOME" % (script, func)
    assert up < home.start(), (
        "%s:%s consults HOME before USERPROFILE. On Windows $HOME is routinely "
        "a mapped network drive while the launcher uses the local profile, so "
        "this ordering decides whether the record is written where it is read."
        % (script, func))
