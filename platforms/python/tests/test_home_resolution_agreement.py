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

import atexit
import os
import re
import shutil
import subprocess
import sys
import tempfile
import pathlib

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from platforms.python import ap_launcher  # noqa: E402

_MARKER_UP = "ap_marker_userprofile"
_MARKER_HOME = "ap_marker_home"

# These have to be directories that REALLY EXIST, and the reason is not the
# obvious one. pwsh builds its own per-user state under $HOME while it starts;
# point HOME at a path that is not there and it exits 70 ("The shell cannot be
# started") before Get-ApGlobalHome is ever reached. Windows pwsh does not care,
# so the literal "M:/ap_marker_home" that used to sit here passed on this
# machine and failed on every Linux run of the workflow from the commit that
# introduced this module. A check that cannot pass on the platform CI runs on is
# not a weaker check than one that can -- it is not a check at all, and it is
# the same defect as an audit pointed at a layer the runner cannot have.
#
# What is asserted does not change. It was never the path: it is WHICH VARIABLE
# the answer came from, read off a marker token, so the marker only has to
# survive in the path. It is the last segment of each directory, and cygpath
# preserves it in either direction on Windows.
_MARKER_ROOT = tempfile.mkdtemp(prefix="ap_home_agreement_")
atexit.register(shutil.rmtree, _MARKER_ROOT, True)
_UP_VALUE = (_MARKER_ROOT + os.sep + _MARKER_UP).replace("\\", "/")
_HOME_VALUE = (_MARKER_ROOT + os.sep + _MARKER_HOME).replace("\\", "/")
os.makedirs(_UP_VALUE)
os.makedirs(_HOME_VALUE)

# (case id, env overrides, expected marker). ``None`` for a variable means
# "remove it from the child's environment entirely" -- distinct from "" which
# is the empty-string case the rule treats as absent.
_CASES = [
    ("both-set", {"USERPROFILE": _UP_VALUE, "HOME": _HOME_VALUE}, _MARKER_UP),
    ("userprofile-only", {"USERPROFILE": _UP_VALUE, "HOME": None}, _MARKER_UP),
    ("home-only", {"USERPROFILE": None, "HOME": _HOME_VALUE}, _MARKER_HOME),
    ("userprofile-empty", {"USERPROFILE": "", "HOME": _HOME_VALUE}, _MARKER_HOME),
]

def _missing_interpreter(name):
    """Reason to skip for a missing interpreter, or None if it is present.

    Under AP_REQUIRE_ADAPTER_INTERPRETERS=1 -- which the workflow sets -- a
    missing interpreter raises here instead, at import, failing collection for
    the whole module. The point is that "pwsh was not installed" and "the
    PowerShell copy agrees with the launcher" must not produce the same green.
    test_adapter_lifecycle.py already draws that line; this module did not.
    """
    if shutil.which(name) is not None:
        return None
    if os.environ.get("AP_REQUIRE_ADAPTER_INTERPRETERS") == "1":
        raise RuntimeError(
            "AP_REQUIRE_ADAPTER_INTERPRETERS=1 but %r was not found, so the "
            "copies this module exists to pin would go unchecked" % name)
    return "no %s available" % name


_NO_SH = _missing_interpreter("sh")
_NO_PWSH = _missing_interpreter("pwsh")


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


def test_the_marker_homes_are_real_directories():
    """The premise the PowerShell cases rest on, asserted rather than assumed.

    Linux pwsh will not start when HOME names a directory that is not there --
    it exits 70 during initialisation, before any function under test runs. So
    a marker value that is merely a plausible-looking string turns the six
    HOME-setting cases from checks into guaranteed failures, on the platform
    the workflow runs on and on no platform a developer here is likely to try.

    Windows pwsh starts regardless, which is exactly why this needs to be an
    assertion: the machine most likely to edit these constants is the one that
    cannot observe the consequence.
    """
    for name, value in (("USERPROFILE", _UP_VALUE), ("HOME", _HOME_VALUE)):
        assert os.path.isdir(value), (
            "the %s marker %r is not a directory. On Linux, pwsh exits 70 "
            "while starting rather than running Get-ApGlobalHome, so every "
            "case that sets HOME fails for a reason that has nothing to do "
            "with the code being pinned." % (name, value))


# ---------------------------------------------------------------------------
# The three unpinned copies, run rather than read.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(_NO_SH is not None, reason=_NO_SH or "")
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


@pytest.mark.skipif(_NO_PWSH is not None, reason=_NO_PWSH or "")
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

@pytest.mark.skipif(_NO_SH is not None, reason=_NO_SH or "")
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


@pytest.mark.skipif(_NO_PWSH is not None, reason=_NO_PWSH or "")
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
