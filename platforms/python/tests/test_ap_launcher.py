# -*- coding: utf-8 -*-
"""Tests for platforms/python/ap_launcher.py -- the shared-runtime launcher.

These exist because of a defect, so they are written to fail if the defect
comes back rather than only to exercise the happy path.

The defect: the slash commands shell out to ``python -m
platforms.python.<module>`` with the *project* as the working directory, and no
installer ships ``platforms/python/`` into a project. Every such invocation
therefore died with ``ModuleNotFoundError: No module named 'platforms'`` in any
project that was not the source checkout.

Coverage:
  (a) A module runs from a project directory that has only a manifest -- the
      reproduction of the original failure, now expected to pass.
  (b) ``--path`` prints the resolved root, which is what the inline ``python
      -c`` call sites use.
  (c) The manifest is found from a *subdirectory*, not only the project root.
  (d) A manifest pointing at a checkout that has moved fails with exit 3 and
      names the manifest, the key and the repair -- mechanism (d), the guard.
  (e) A malformed manifest does the same rather than raising a traceback.
  (f) A missing manifest does the same.
  (g) ``$ADVANCED_PLANNING_ROOT`` overrides the manifest, and a bogus value of
      it is refused rather than silently ignored.
  (h) **The regression test proper**: every command call site invokes the
      runtime through the launcher. A site that goes back to bare ``-m`` fails
      here, which is the failure mode that produced this work.
  (i) Both installers write the manifest OUTSIDE the scaffold guard, so an
      upgrade into a project that already has ``.advanced-plans/`` still
      refreshes the recorded path. That guard skipping the manifest would be a
      silent no-op upgrade.

Every test builds an isolated project in tmp_path. None of them import the
launcher's own package first: the point is that it works before the runtime is
reachable.
"""

import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from platforms.python import ap_launcher  # noqa: E402

LAUNCHER_SRC = _REPO_ROOT / "platforms" / "python" / "ap_launcher.py"
COMMANDS_DIR = _REPO_ROOT / "platforms" / "claude-code" / "commands"
EXIT_UNREACHABLE = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_env(home=None):
    """os.environ without the things that would mask a resolution failure.

    `home` also pins USERPROFILE and HOME. Without that these tests read the
    developer's real profile: the global record at ~/.advanced-plans/ is now
    part of resolution, so a machine that happens to have one would turn every
    "this must fail" assertion green for the wrong reason. Defaults to a fresh
    empty directory, which is the "no global install" case.
    """
    environ = dict(os.environ)
    environ.pop("ADVANCED_PLANNING_ROOT", None)
    environ.pop("PYTHONPATH", None)
    if home is None:
        home = tempfile.mkdtemp(prefix="ap-nohome-")
    environ["USERPROFILE"] = str(home)
    environ["HOME"] = str(home)
    return environ


def make_decoy_checkout(tmp_path, name="decoy-checkout"):
    """A second, otherwise-empty Advanced Planning checkout.

    Resolution tests that expect the global record must not assert against
    _REPO_ROOT: the own-checkout fallback returns that too, so the assertion
    would pass with the global step deleted. Pointing the global record at a
    decoy makes the two routes distinguishable.
    """
    root = tmp_path / name
    (root / "platforms" / "python").mkdir(parents=True)
    (root / "platforms" / "python" / "__init__.py").write_text(
        "", encoding="utf-8")
    return root


def make_loose_launcher(tmp_path, name="installed"):
    """A launcher copy with no source checkout above it.

    The installed copy is what these tests are about; running the source file
    at platforms/python/ap_launcher.py silently enables the own-checkout
    fallback and hides whatever the test meant to prove.
    """
    d = tmp_path / name
    d.mkdir(parents=True, exist_ok=True)
    ap = d / "ap.py"
    ap.write_bytes(LAUNCHER_SRC.read_bytes())
    return ap


def make_global_record(home, source_root):
    """Write the record a `--global` install leaves in the user profile."""
    home = pathlib.Path(home)
    (home / ".advanced-plans" / "bin").mkdir(parents=True, exist_ok=True)
    (home / ".advanced-plans" / "runtime.json").write_text(
        json.dumps({"schema_version": 1, "source_root": str(source_root),
                    "written_by": "test"}), encoding="utf-8")
    return home / ".advanced-plans" / "runtime.json"


def make_project(tmp_path, source_root, name="proj"):
    """A project with the launcher installed and a manifest, and nothing else.

    Deliberately no ``platforms/`` -- that absence *is* the condition under
    test. A project that happened to contain the package would pass even with
    the mechanism removed.
    """
    proj = tmp_path / name
    ap = proj / ".advanced-plans"
    (ap / "bin").mkdir(parents=True)
    (ap / "state").mkdir(parents=True)
    (ap / "bin" / "ap.py").write_bytes(LAUNCHER_SRC.read_bytes())
    if source_root is not None:
        (ap / "runtime.json").write_text(json.dumps({
            "schema_version": 1,
            "source_root": str(source_root),
            "version": "test",
            "written_by": "test_ap_launcher.py",
        }), encoding="utf-8")
    return proj


def run_launcher(proj, args, env=None, cwd=None):
    """Invoke the installed launcher exactly as a slash command would."""
    environ = dict(os.environ)
    environ.pop("ADVANCED_PLANNING_ROOT", None)
    # A stray PYTHONPATH would resolve `platforms` for free and hide the very
    # failure these tests are for.
    environ.pop("PYTHONPATH", None)
    environ.update(env or {})
    return subprocess.run(
        [sys.executable, str(pathlib.Path(".advanced-plans") / "bin" / "ap.py")] + args,
        cwd=str(cwd or proj), env=environ,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)


# ---------------------------------------------------------------------------
# (a)-(c) the mechanism works
# ---------------------------------------------------------------------------

def test_module_runs_from_a_project_that_only_has_the_manifest(tmp_path):
    """The original failure, reproduced and now expected to succeed."""
    proj = make_project(tmp_path, _REPO_ROOT)
    hist = proj / ".advanced-plans" / "state" / "history.jsonl"
    r = run_launcher(proj, ["history_log", str(hist),
                            '{"event":"probe","phase":"test"}'])
    assert r.returncode == 0, (
        "the launcher could not reach the runtime from an installed "
        "project:\nstdout=%s\nstderr=%s" % (r.stdout, r.stderr))
    assert "No module named" not in r.stderr
    written = io.open(str(hist), encoding="utf-8").read()
    assert '"probe"' in written, "the module ran but wrote nothing: %r" % written


def test_bare_dash_m_still_fails_there(tmp_path):
    """The control. Without the launcher the invocation must still die.

    If this ever passes, something on the machine is putting the package on
    the path and every other test here has stopped proving anything.
    """
    proj = make_project(tmp_path, _REPO_ROOT)
    environ = dict(os.environ)
    environ.pop("PYTHONPATH", None)
    r = subprocess.run([sys.executable, "-m", "platforms.python.history_log"],
                       cwd=str(proj), env=environ, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, universal_newlines=True)
    assert r.returncode != 0
    assert "No module named" in r.stderr


def test_path_prints_the_resolved_root(tmp_path):
    proj = make_project(tmp_path, _REPO_ROOT)
    r = run_launcher(proj, ["--path"])
    assert r.returncode == 0, r.stderr
    assert pathlib.Path(r.stdout.strip()) == _REPO_ROOT


def test_the_global_record_is_read_beside_the_launcher_not_from_the_caller_home(tmp_path):
    """An install under one profile must be readable from another.

    Found live, not by review: a `--global` install into one profile was
    called from a shell holding a different one, and the launcher looked for
    the record under the CALLER's profile - so a correctly installed global
    runtime was invisible. Same failure in CI, in a container, under a service
    account, and under Git Bash whose $HOME is a mapped drive when the install
    ran from PowerShell.

    The installed launcher knows where it lives; the record sits two
    directories above it. Reading it there makes the two homes irrelevant.
    """
    install_home = tmp_path / "install-profile"
    decoy = make_decoy_checkout(tmp_path)
    make_global_record(install_home, decoy)
    launcher = install_home / ".advanced-plans" / "bin" / "ap.py"
    launcher.write_bytes(LAUNCHER_SRC.read_bytes())

    project = tmp_path / "elsewhere"
    project.mkdir()

    # The caller's profile is a DIFFERENT, empty one.
    r = subprocess.run(
        [sys.executable, str(launcher), "--path"],
        cwd=str(project), env=_clean_env(tmp_path / "caller-profile"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True)

    assert r.returncode == 0, (
        "the global record was not found beside the launcher; the caller's "
        "profile was consulted instead:\nstderr=%s" % r.stderr)
    assert pathlib.Path(r.stdout.strip()) == decoy


def test_the_inline_call_sites_get_the_guard_not_a_traceback(tmp_path):
    """`runpy.run_path(...)['bootstrap']()` must fail the way ap.py does.

    Six of the thirteen call sites are that inline form. bootstrap() used to
    let Unreachable propagate, so those six printed a traceback naming a line
    inside ap_launcher.py and exited 1 - the raw-internal-failure that
    mechanism (d) exists to replace, alive at half the sites and missed by
    three independent reviewers reading the diff. Found by running one.
    """
    launcher = make_loose_launcher(tmp_path)
    project = tmp_path / "uninstalled"
    project.mkdir()

    r = subprocess.run(
        [sys.executable, "-c",
         "import runpy; runpy.run_path(r'%s')['bootstrap']()" % launcher],
        cwd=str(project), env=_clean_env(tmp_path / "empty-home"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True)

    assert "Traceback" not in r.stderr, (
        "an inline call site raised instead of reporting:\n%s" % r.stderr)
    assert r.returncode == EXIT_UNREACHABLE, r.stderr
    assert "advanced-planning: fix:" in r.stderr


def test_global_home_agrees_with_install_audit(monkeypatch):
    """The duplicated home resolution must not drift from its original.

    ap_launcher cannot import install_audit - it is copied out of the checkout
    and runs before the runtime is reachable - so the USERPROFILE-first rule
    exists twice. The launcher's own design notes warn that a second copy of
    logic is the thing most likely to drift, so the agreement is asserted
    rather than assumed. If either side is edited alone, this fails.
    """
    from platforms.python import install_audit

    cases = [
        {"USERPROFILE": r"C:\Users\alice", "HOME": "/m/networkdrive"},
        {"HOME": "/home/bob"},
        {"USERPROFILE": r"C:\Users\carol"},
    ]
    for env in cases:
        assert (os.path.normcase(ap_launcher.global_home(env))
                == os.path.normcase(str(install_audit.resolve_global_home(env)))), env

    # And the ordering itself, stated once so a reader need not diff two files.
    assert ap_launcher.global_home(
        {"USERPROFILE": r"C:\Users\alice", "HOME": "/m/net"}
    ).lower().endswith("alice")


def test_a_project_without_a_manifest_falls_through_to_the_global_record(tmp_path):
    """The boundary stop must not make global installs illegal.

    Found by the cross-vendor panel (cursor) against the FIRST draft of the
    boundary stop, which raised outright. The documented `--global` path is
    "try it out, no project changes" - and the first command that writes
    planning data scaffolds `.advanced-plans/`. Under the first draft, that
    directory then became a boundary and every later command died with "run
    this project's own installer", even though the global launcher and the
    global record both existed. The stop means "do not steal the enclosing
    project's checkout", not "a global install stops working once you use it".
    """
    home = tmp_path / "home"
    decoy = make_decoy_checkout(tmp_path)
    make_global_record(home, decoy)

    project = tmp_path / "scaffolded"
    (project / ".advanced-plans" / "state").mkdir(parents=True)

    r = subprocess.run(
        [sys.executable, str(make_loose_launcher(tmp_path)), "--path"],
        cwd=str(project), env=_clean_env(home), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, universal_newlines=True)

    assert r.returncode == 0, (
        "a scaffolded but never-project-installed directory did not reach the "
        "global record:\nstdout=%s\nstderr=%s" % (r.stdout, r.stderr))
    # The decoy, not _REPO_ROOT: asserting _REPO_ROOT here would pass with the
    # global step deleted, because the own-checkout fallback returns it too.
    assert pathlib.Path(r.stdout.strip()) == decoy


def test_without_a_global_record_the_boundary_is_still_an_error(tmp_path):
    """The fall-through must not become a way to fail silently.

    Same shape as the test above with the global record removed. The point of
    the pair is that the boundary is not itself the verdict: it is the verdict
    only when there is nothing to fall through to, and then it must say both
    halves - this is a project, AND there is no global record.
    """
    project = tmp_path / "scaffolded"
    (project / ".advanced-plans").mkdir(parents=True)

    r = subprocess.run(
        [sys.executable, str(make_loose_launcher(tmp_path)), "--path"],
        cwd=str(project), env=_clean_env(tmp_path / "empty-home"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True)

    assert r.returncode == EXIT_UNREACHABLE, r.stdout
    assert "no global record" in r.stderr
    assert "--global" in r.stderr
    assert "Traceback" not in r.stderr


def test_a_nested_repository_does_not_inherit_the_enclosing_checkout(tmp_path):
    """A separate repo inside a project is not part of that project.

    Found by the cross-vendor panel (cursor), which pointed out that the
    project-marker stop only catches nested *Advanced Planning* projects. The
    commoner shape is a monorepo service or a submodule: an independent
    repository with no `.advanced-plans/` of its own, which the walk sailed
    straight through - resolving successfully, exit 0, against a checkout that
    has nothing to do with it. That is the silent-wrong-answer failure this
    design is most exposed to, so `.git` is a boundary too.
    """
    outer = make_project(tmp_path, _REPO_ROOT, name="outer")
    inner = outer / "services" / "api"
    inner.mkdir(parents=True)
    (inner / ".git").mkdir()

    r = subprocess.run(
        [sys.executable, str(outer / ".advanced-plans" / "bin" / "ap.py"),
         "--path"],
        cwd=str(inner), env=_clean_env(tmp_path / "empty-home"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True)

    assert r.returncode == EXIT_UNREACHABLE, (
        "the nested repository inherited the enclosing project's checkout:\n"
        "stdout=%s\nstderr=%s" % (r.stdout, r.stderr))
    assert "repository root" in r.stderr


def test_a_nested_repository_still_reaches_the_global_record(tmp_path):
    """...but the boundary sends it to the global record, not to a dead end.

    The pair with the test above: stopping the walk must not mean a nested
    repository can never be driven by globally-installed commands. It falls
    through to the machine-level record like any other uninstalled directory.
    """
    home = tmp_path / "home"
    decoy = make_decoy_checkout(tmp_path)
    make_global_record(home, decoy)
    outer = make_project(tmp_path, _REPO_ROOT, name="outer")
    inner = outer / "services" / "api"
    inner.mkdir(parents=True)
    (inner / ".git").write_text("gitdir: ../../.git/modules/api\n",
                                encoding="utf-8")

    r = subprocess.run(
        [sys.executable, str(outer / ".advanced-plans" / "bin" / "ap.py"),
         "--path"],
        cwd=str(inner), env=_clean_env(home), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, universal_newlines=True)

    assert r.returncode == 0, r.stderr
    # The decoy proves the global record was used, not the enclosing project's
    # manifest - which is the thing the boundary stop exists to refuse.
    assert pathlib.Path(r.stdout.strip()) == decoy


def test_the_profile_directory_is_never_adopted_as_a_checkout(tmp_path):
    """`<home>/.advanced-plans/bin/ap.py` is three dirnames below `<home>`.

    So the own-checkout fallback, which walks exactly three dirnames up from
    __file__, resolves to the user profile for the globally-installed copy. It
    is guarded by a marker file, which makes this harmless for most people and
    silent for anyone who keeps a `platforms/python/` tree in their profile -
    they would get their home directory adopted as the runtime with no
    diagnostic. Raised by the panel (cursor) as a latent false positive.
    """
    home = tmp_path / "home"
    (home / ".advanced-plans" / "bin").mkdir(parents=True)
    shutil.copy(str(_REPO_ROOT / "platforms" / "python" / "ap_launcher.py"),
                str(home / ".advanced-plans" / "bin" / "ap.py"))
    # Make the profile look like a checkout, which is the whole trap.
    (home / "platforms" / "python").mkdir(parents=True)
    (home / "platforms" / "python" / "__init__.py").write_text(
        "", encoding="utf-8")

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    r = subprocess.run(
        [sys.executable, str(home / ".advanced-plans" / "bin" / "ap.py"),
         "--path"],
        cwd=str(elsewhere), env=_clean_env(home), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, universal_newlines=True)

    assert r.returncode == EXIT_UNREACHABLE, (
        "the profile directory was adopted as the runtime: %s" % r.stdout)


def test_the_walk_stops_at_a_project_that_has_no_manifest(tmp_path):
    """A vendored project must not borrow its host's checkout.

    Found by a cross-vendor review panel and reproduced before being fixed:
    an inner project with its own `.advanced-plans/` but no manifest walked
    straight past itself, adopted the OUTER project's manifest, and ran that
    checkout - exit 0, no diagnostic. Silent resolution to the wrong runtime
    is the failure this whole design is most exposed to, so it is now the one
    case the walk refuses.
    """
    outer = make_project(tmp_path, _REPO_ROOT, name="outer")
    inner = outer / "vendor" / "inner"
    (inner / ".advanced-plans").mkdir(parents=True)

    r = subprocess.run(
        [sys.executable, str(outer / ".advanced-plans" / "bin" / "ap.py"),
         "--path"],
        cwd=str(inner), env=_clean_env(), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, universal_newlines=True)

    assert r.returncode == EXIT_UNREACHABLE, (
        "the inner project resolved to something instead of refusing; it "
        "borrowed the enclosing project's runtime:\nstdout=%s\nstderr=%s"
        % (r.stdout, r.stderr))
    assert "has no" in r.stderr and ".advanced-plans" in r.stderr
    assert "fix:" in r.stderr
    assert "Traceback" not in r.stderr


def test_a_plain_subdirectory_still_walks_up(tmp_path):
    """The boundary stop must not break the feature it guards.

    Only a directory holding `.advanced-plans/` is a boundary. An ordinary
    subdirectory - src/, tests/, docs/ - must still find the project's
    manifest above it, or the stop has cured the disease by killing the
    patient.
    """
    proj = make_project(tmp_path, _REPO_ROOT)
    sub = proj / "src" / "deep" / "deeper"
    sub.mkdir(parents=True)
    r = subprocess.run(
        [sys.executable, str(proj / ".advanced-plans" / "bin" / "ap.py"),
         "--path"],
        cwd=str(sub), env=_clean_env(), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, universal_newlines=True)
    assert r.returncode == 0, r.stderr
    assert pathlib.Path(r.stdout.strip()) == _REPO_ROOT


def test_walk_up_works_when_the_launcher_is_named_by_absolute_path(tmp_path):
    """find_manifest() walks upward, and this proves it -- but only for an
    *absolute* launcher path.

    Read the next test before believing this one covers subdirectories. The
    shipped call sites say `python .advanced-plans/bin/ap.py`, which is
    relative to the working directory, so from a subdirectory the interpreter
    fails to open the file before any of this code runs. This test named
    itself `..._from_a_subdirectory` in its first draft and was caught in
    review overclaiming exactly that.

    The walk-up is not dead code: it is what an absolute invocation needs, and
    it is the route a launcher living outside the project would take.
    """
    proj = make_project(tmp_path, _REPO_ROOT)
    sub = proj / "src" / "deep"
    sub.mkdir(parents=True)
    r = subprocess.run(
        [sys.executable, str(proj / ".advanced-plans" / "bin" / "ap.py"), "--path"],
        cwd=str(sub), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True)
    assert r.returncode == 0, r.stderr
    assert pathlib.Path(r.stdout.strip()) == _REPO_ROOT


def test_the_relative_call_site_form_requires_the_project_root(tmp_path):
    """Pin the real limit of the shipped invocation, rather than hiding it.

    Every path in every command -- `.advanced-plans/PLANNING.md`,
    `.advanced-plans/state/history.jsonl`, and now the launcher -- is relative
    to the project root, so requiring that cwd is consistent, not a new
    constraint. What is not acceptable is claiming coverage of the other case.
    If a future change makes the relative form work from a subdirectory, this
    test fails and should be replaced with the positive assertion.
    """
    proj = make_project(tmp_path, _REPO_ROOT)
    sub = proj / "src" / "deep"
    sub.mkdir(parents=True)
    environ = dict(os.environ)
    environ.pop("ADVANCED_PLANNING_ROOT", None)
    r = subprocess.run(
        [sys.executable, os.path.join(".advanced-plans", "bin", "ap.py"), "--path"],
        cwd=str(sub), env=environ, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, universal_newlines=True)
    assert r.returncode != 0
    assert "ap.py" in r.stderr
    # The interpreter, not the guard: exit 3 here would mean the launcher ran.
    assert r.returncode != EXIT_UNREACHABLE, (
        "the launcher ran from a subdirectory -- the relative form now works, "
        "so replace this test with the positive assertion:" + r.stderr)


def test_every_command_that_calls_the_launcher_runs_from_the_project_root():
    """The constraint above only holds if the commands actually say so.

    A call site that told the reader to `cd` somewhere first would break the
    relative form silently, and the failure would be Python's `can't open
    file`, which names neither the command nor the cause.
    """
    offenders = []
    for md in sorted(COMMANDS_DIR.glob("*.md")):
        text = io.open(str(md), encoding="utf-8", newline="").read()
        if ".advanced-plans/bin/ap.py" not in text:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("cd ") and not stripped.startswith("cd -"):
                offenders.append("%s:%d: %s" % (md.name, i, stripped))
    assert not offenders, (
        "these commands invoke the launcher by a project-root-relative path "
        "but also change directory: " + "; ".join(offenders))


# ---------------------------------------------------------------------------
# (d)-(f) the guard
# ---------------------------------------------------------------------------

def _assert_actionable(r, *must_mention):
    assert r.returncode == EXIT_UNREACHABLE, (
        "expected exit %d, got %d\nstdout=%s\nstderr=%s"
        % (EXIT_UNREACHABLE, r.returncode, r.stdout, r.stderr))
    assert "Traceback" not in r.stderr, "guard leaked a traceback:\n" + r.stderr
    assert "fix:" in r.stderr, "the diagnostic names no repair:\n" + r.stderr
    for token in must_mention:
        assert token in r.stderr, "%r missing from:\n%s" % (token, r.stderr)


def test_moved_checkout_is_named_not_a_module_error(tmp_path):
    gone = tmp_path / "checkout-that-moved"
    proj = make_project(tmp_path, gone)
    r = run_launcher(proj, ["history_log"])
    _assert_actionable(r, "runtime.json", "source_root", "moved")
    assert "No module named" not in r.stderr, (
        "the guard did not fire and the raw ModuleNotFoundError came back")


def test_malformed_manifest_is_reported_as_such(tmp_path):
    proj = make_project(tmp_path, _REPO_ROOT)
    (proj / ".advanced-plans" / "runtime.json").write_text("{ not json",
                                                           encoding="utf-8")
    r = run_launcher(proj, ["history_log"])
    _assert_actionable(r, "runtime.json", "JSON")


def test_missing_manifest_is_reported_as_such(tmp_path):
    proj = make_project(tmp_path, None)
    r = run_launcher(proj, ["history_log"])
    _assert_actionable(r, "runtime.json", "installer")


@pytest.mark.parametrize("document,noun", [
    ("[]", "list"),
    ('{"source_root": 1}', "int"),
    ('"a string"', "str"),
    ("null", "NoneType"),
])
def test_valid_json_of_the_wrong_shape_is_reported_as_such(tmp_path, document,
                                                           noun):
    """Parsing is not validating, and the first draft conflated them.

    Only a JSONDecodeError was caught, so a manifest holding `[]` reached
    `data.get` and raised AttributeError -- a raw traceback naming a launcher
    internal, which is precisely the failure mode the guard exists to replace.
    A hand-edited or half-written manifest is the realistic source.
    """
    proj = make_project(tmp_path, _REPO_ROOT)
    manifest = proj / ".advanced-plans" / "runtime.json"
    io.open(str(manifest), "w", encoding="utf-8").write(document)
    r = run_launcher(proj, ["--path"])
    _assert_actionable(r, "runtime.json", "source_root")
    assert noun in r.stderr, (
        "the diagnostic does not say what shape it found: " + r.stderr)


def test_manifest_without_the_key_is_reported_as_such(tmp_path):
    proj = make_project(tmp_path, _REPO_ROOT)
    (proj / ".advanced-plans" / "runtime.json").write_text(
        json.dumps({"schema_version": 1}), encoding="utf-8")
    r = run_launcher(proj, ["history_log"])
    _assert_actionable(r, "source_root")


def test_unknown_module_blames_the_module_not_the_path(tmp_path):
    """Resolution succeeded, so the diagnostic must not send the reader to the
    manifest -- that would be the wrong file entirely."""
    proj = make_project(tmp_path, _REPO_ROOT)
    r = run_launcher(proj, ["no_such_module_here"])
    assert r.returncode == EXIT_UNREACHABLE
    assert "is not in the runtime" in r.stderr
    assert "runtime.json" not in r.stderr


# ---------------------------------------------------------------------------
# (g) the environment escape hatch
# ---------------------------------------------------------------------------

def test_env_var_overrides_a_stale_manifest(tmp_path):
    proj = make_project(tmp_path, tmp_path / "checkout-that-moved")
    r = run_launcher(proj, ["--path"],
                     env={"ADVANCED_PLANNING_ROOT": str(_REPO_ROOT)})
    assert r.returncode == 0, r.stderr
    assert pathlib.Path(r.stdout.strip()) == _REPO_ROOT


def test_bogus_env_var_is_refused_not_ignored(tmp_path):
    """Falling back to the manifest here would make a typo in the variable
    look like it worked, which is worse than failing."""
    proj = make_project(tmp_path, _REPO_ROOT)
    r = run_launcher(proj, ["--path"],
                     env={"ADVANCED_PLANNING_ROOT": str(tmp_path / "nope")})
    _assert_actionable(r, "ADVANCED_PLANNING_ROOT")


# ---------------------------------------------------------------------------
# (h) the regression test proper
# ---------------------------------------------------------------------------

BARE_M = re.compile(r"python\s+-m\s+platforms\.python\.")
BARE_SYS_PATH = re.compile(r"""sys\.path\.insert\(\s*0\s*,\s*['"]\.['"]\s*\)""")


def test_no_command_invokes_the_runtime_by_bare_dash_m():
    """Every call site must go through the launcher.

    This is the check that would have caught the defect. `python -m
    platforms.python.X` resolves only when the working directory is the source
    checkout, which is never true of an installed project.
    """
    offenders = []
    for md in sorted(COMMANDS_DIR.glob("*.md")):
        text = io.open(str(md), encoding="utf-8", newline="").read()
        for n, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
            if BARE_M.search(line):
                offenders.append("%s:%d: %s" % (md.name, n, line.strip()))
    assert not offenders, (
        "these call sites invoke the shared runtime by bare -m, which fails in "
        "any installed project. Use `python .advanced-plans/bin/ap.py "
        "<module>`:\n  " + "\n  ".join(offenders))


def test_no_command_relies_on_cwd_being_the_checkout():
    """`sys.path.insert(0, '.')` is the same defect wearing a hat."""
    offenders = []
    for md in sorted(COMMANDS_DIR.glob("*.md")):
        text = io.open(str(md), encoding="utf-8", newline="").read()
        for n, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
            if BARE_SYS_PATH.search(line):
                offenders.append("%s:%d: %s" % (md.name, n, line.strip()))
    assert not offenders, (
        "these call sites put '.' on sys.path, which only reaches the runtime "
        "when the working directory is the source checkout:\n  "
        + "\n  ".join(offenders))


def test_every_launcher_call_site_names_a_real_module():
    """A call site naming a module that was never written would fail exactly
    like the path defect and be diagnosed as the wrong thing."""
    available = {p.stem for p in (_REPO_ROOT / "platforms" / "python").glob("*.py")}
    # The optional closing quote: source call sites are quoted so the global
    # installer's rewrite is a pure path swap and install_audit sees no drift.
    # An installed copy carries an absolute path inside the same quotes.
    pattern = re.compile(r'bin/ap\.py"?\s+([a-z_][a-z0-9_]*)')
    seen, missing = set(), []
    for md in sorted(COMMANDS_DIR.glob("*.md")):
        text = io.open(str(md), encoding="utf-8", newline="").read()
        for m in pattern.finditer(text):
            seen.add(m.group(1))
            if m.group(1) not in available:
                missing.append("%s: %s" % (md.name, m.group(1)))
    assert seen, "no launcher call sites found at all - did the rewrite land?"
    assert not missing, "call sites name modules that do not exist: %s" % missing


def test_every_source_call_site_is_in_the_substitutable_form():
    """The global installers rewrite the launcher path in the commands they
    copy. That rewrite must change the PATH and nothing else, because
    install_audit normalises exactly one canonical path back out before
    hashing -- so a call site the installer has to requote is a call site the
    audit will report as drift forever.

    This was not theory: the first pass rewrote bare call sites into quoted
    ones and the audit reported 6 stale files that no /sync-install could
    settle. The repair was to quote the SOURCE, which is what this pins.
    """
    shell = re.compile(r'python\s+(?!")\S*\.advanced-plans/bin/ap\.py')
    inline = re.compile(r"runpy\.run_path\((?!r')")
    offenders = []
    for md in sorted(COMMANDS_DIR.glob("*.md")):
        text = io.open(str(md), encoding="utf-8", newline="").read()
        for label, pattern in (("unquoted shell", shell),
                               ("non-raw runpy", inline)):
            if pattern.search(text):
                offenders.append("%s: %s" % (md.name, label))
    assert not offenders, (
        "these call sites are not in the form the installers substitute, so "
        "install_audit will see permanent drift after a --global install: %s"
        % offenders)


# The environment an installer is allowed to read without assigning it.
_INSTALLER_ENV = frozenset([
    "HOME", "USERPROFILE", "PATH", "PWD", "TARGET", "CLAUDE_DIR",
    "PLANNING_SKILLS_PATH", "ADVANCED_PLANNING_ROOT",
])


def _strip_quoted_heredocs(text):
    """Drop the bodies of <<'EOF' style heredocs.

    A quoted heredoc delimiter suppresses expansion entirely, so `$name` inside
    one is literal text, not a variable read -- `setup/codex/install.sh` writes
    a PLANNING.md containing the literal string "$advanced-planning" that way.
    Unquoted heredocs (<<EOF) DO expand and are left in scope, which is the
    whole point: those are where an unassigned variable really does bite.

    Bodies are dropped from the text used for BOTH halves of the comparison, so
    this removes false positives without hiding a real one: a variable that is
    only ever assigned inside a quoted heredoc was never really assigned.
    """
    out, delim = [], None
    for line in text.split("\n"):
        if delim is None:
            match = re.search(r"<<-?\s*(['\"])([A-Za-z_][A-Za-z0-9_]*)\1", line)
            if match:
                delim = match.group(2)
                out.append(line[:match.start()])
                continue
            out.append(line)
        elif line.strip() == delim:
            delim = None
    return "\n".join(out)


@pytest.mark.parametrize("script", [
    "setup/claude-code/install.sh",
    "platforms/claude-code/install.sh",
    # codex and opencode carry the same rewrite helpers and were never checked
    # by this analyser at all until F10 touched them.
    "setup/codex/install.sh",
    "setup/opencode/install.sh",
])
def test_no_installer_reads_a_variable_it_never_assigns(script):
    """Found by running the third installer, not by reading it.

    `platforms/claude-code/install.sh` calls its root `SCRIPT_DIR`, but the
    global block added here was written against the other installer's name for
    the same thing, `REPO_ROOT`. Nothing defines it, so `set -e` aborted on
    `cp "$REPO_ROOT/platforms/..."` -- AFTER the commands had been copied and
    BEFORE their launcher paths were rewritten. That is precisely the state
    this whole change exists to prevent: commands installed to a home directory
    naming a project-relative launcher that will not be there.

    It exits 1, so it is not silent. It is worse than silent: it half-installs.
    """
    path = _REPO_ROOT / script
    text = io.open(str(path), encoding="utf-8", newline="").read()
    text = _strip_quoted_heredocs(text)
    # `(?:^|[;&|]) ` and not just `^`: these installers write more than one
    # assignment per line (`_f="$1"; _launcher="$2"`), and an anchored pattern
    # sees only the first -- which would have reported the second as unassigned.
    # `then`/`else`/`do` join the list for the same reason `;` is on it: an
    # assignment can legally follow a keyword, and an anchored pattern would
    # report `if ...; then _ends_nl=0; fi` as never assigning `_ends_nl`.
    assigned = set(re.findall(
        r"(?:^|[;&|]|\bthen\b|\belse\b|\bdo\b)"
        r"\s*(?:local\s+|export\s+)?([A-Za-z_][A-Za-z0-9_]*)=",
        text, re.M))
    assigned |= set(re.findall(r"for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in", text))
    # `read VAR` assigns VAR. This is the same class of omission the `for` line
    # above already covers, not a loosening: a variable that is genuinely never
    # assigned still appears in no `read` anywhere, and is still reported.
    assigned |= set(re.findall(
        r"\bread\s+(?:-[A-Za-z]+\s+)*([A-Za-z_][A-Za-z0-9_]*)", text))
    # A backslash-escaped `\$` is a literal dollar sign, not an expansion --
    # these installers write `\\$advanced-planning` into generated docs. Without
    # the lookbehind those literals read as uses of a variable named `advanced`.
    used = set(re.findall(r'(?<!\\)\$\{?([A-Za-z_][A-Za-z0-9_]*)', text))
    unknown = sorted(used - assigned - _INSTALLER_ENV)
    assert not unknown, (
        "%s reads %s but never assigns them, and never declares them as "
        "environment. Under set -e that half-installs." % (script, unknown))


@pytest.mark.parametrize("script,project_marker", [
    ("setup/claude-code/install.sh", "--project"),
    ("setup/claude-code/install.ps1", "-Project"),
    ("platforms/claude-code/install.sh", "--project"),
])
def test_every_installer_project_path_records_the_runtime(script, project_marker):
    """There are THREE installers, and the third one's project path shipped
    commands without their launcher for its whole life -- the original defect,
    fully intact, in the one code path nobody had re-read.

    Found by an independent reviewer reading the file after the controller had
    fixed its --global branch and moved on. The parameterisation is the point:
    the earlier test covered the two installers under setup/ and said nothing
    about this one.
    """
    text = io.open(str(_REPO_ROOT / script), encoding="utf-8",
                   newline="").read().replace("\r\n", "\n")
    assert project_marker in text, (
        "%s does not appear to have a project install path" % script)
    # Two writes now: one in the global branch, one in the project branch.
    # Counting is what distinguishes "records it somewhere" from "records it
    # on the path a project install actually takes".
    assert text.count("runtime.json") >= 2, (
        "%s writes runtime.json %d time(s); a global-only write leaves every "
        "project install shipping commands whose launcher is not there"
        % (script, text.count("runtime.json")))
    assert text.count("ap_launcher.py") >= 2, (
        "%s copies the launcher %d time(s), so one of its install paths does "
        "not" % (script, text.count("ap_launcher.py")))


# ---------------------------------------------------------------------------
# (i) the installers record the path on upgrade, not only on fresh install
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("installer", ["install.ps1", "install.sh"])
def test_installer_records_the_runtime_outside_the_scaffold_guard(installer):
    """Both installers skip the .advanced-plans/ scaffold when it already
    exists. If the manifest were written inside that branch, upgrading a
    project that already had planning data would silently leave the old
    recorded path in place -- which is the one case the guard cannot repair
    because it would not know anything was wrong.
    """
    src = _REPO_ROOT / "setup" / "claude-code" / installer
    text = io.open(str(src), encoding="utf-8", newline="").read().replace("\r\n", "\n")
    assert "runtime.json" in text, "%s never writes runtime.json" % installer
    assert "ap_launcher.py" in text, "%s never installs the launcher" % installer

    lines = text.split("\n")
    # LAST occurrence of each, not first. Both installers now write a SECOND
    # runtime.json in their --global branch, which sits above the project
    # install and exits before reaching it; taking the first match would
    # compare the GLOBAL write against the PROJECT guard and prove nothing
    # about either.
    guard = max(i for i, l in enumerate(lines)
                if "skipping scaffold" in l.lower())
    manifest = max(i for i, l in enumerate(lines) if "runtime.json" in l)
    # The scaffold branch is well inside the file; the manifest write must come
    # after the whole if/else has closed, not within it.
    assert manifest > guard, (
        "%s writes runtime.json at line %d, before the scaffold guard at line "
        "%d" % (installer, manifest + 1, guard + 1))
    assert "Shared Python runtime" in text, (
        "%s should mark the section so a later reader does not move it back "
        "inside the guard" % installer)


def test_the_guard_only_names_repairs_that_exist():
    """The guard's value is that its suggested repair works.

    The first draft told the reader to run `/sync-install`, which refreshes
    `.claude/` surfaces from install_audit's file lists and is blind to
    `.advanced-plans/runtime.json` -- it would have reported CLEAN and changed
    nothing. A guard that names a no-op repair is worse than a raw traceback,
    because it costs the reader a round of trust before they find out.
    """
    launcher = io.open(str(LAUNCHER_SRC), encoding="utf-8").read()
    sync = io.open(str(COMMANDS_DIR / "sync-install.md"),
                   encoding="utf-8", newline="").read()
    if "/sync-install" in launcher:
        assert "runtime.json" in sync, (
            "the launcher tells the reader to run /sync-install, but "
            "sync-install.md never touches runtime.json, so that repair is a "
            "no-op. Either make it one, or stop naming it.")
        assert "ap.py --check" in sync or "ap_launcher.py" in sync, (
            "sync-install.md mentions runtime.json but never checks or "
            "rewrites it through the launcher")
        # Ordering is the whole repair. Step 2 runs install_audit *through*
        # the launcher, so a repair written after it can never be reached in
        # either case it exists for: a stale manifest exits 3 and a missing
        # launcher exits 2, and both stop the command before it arrives.
        # Found in review, after the first draft placed it at step 4b.
        repair = sync.index("Ensure the shared runtime is reachable")
        audit = sync.index('python ".advanced-plans/bin/ap.py" install_audit')
        assert repair < audit, (
            "sync-install.md repairs the runtime record at offset %d but "
            "first invokes the launcher at offset %d, so the repair is "
            "unreachable in exactly the cases it is for." % (repair, audit))


def test_install_sh_records_a_path_the_interpreter_can_open():
    """Found by running it: under Git Bash on Windows $REPO_ROOT is a POSIX
    path (/c/Users/...) and the native Python cannot open it, so the guard
    fired on a fresh, correct install. The diagnostic was right and its
    suggested repair was useless -- re-running the installer reproduced the
    same bad path. The manifest has to hold a path the interpreter that reads
    it can resolve.
    """
    src = _REPO_ROOT / "setup" / "claude-code" / "install.sh"
    text = io.open(str(src), encoding="utf-8", newline="").read().replace("\r\n", "\n")
    body = text.split("Shared Python runtime", 1)[1]
    assert "cygpath" in body, (
        "install.sh writes source_root without normalising it. On Windows that "
        "records /c/Users/... , which the native interpreter cannot open.")
    assert '"source_root": "$REPO_ROOT"' not in body, (
        "install.sh records the raw $REPO_ROOT again; use the normalised value.")


# ---------------------------------------------------------------------------
# unit-level checks on the resolver itself
# ---------------------------------------------------------------------------

def test_find_manifest_walks_up_and_stops(tmp_path):
    proj = make_project(tmp_path, _REPO_ROOT)
    deep = proj / "a" / "b" / "c"
    deep.mkdir(parents=True)
    found = ap_launcher.find_manifest(str(deep))
    assert found is not None
    assert pathlib.Path(found) == proj / ".advanced-plans" / "runtime.json"

    # The orphan case used to assert `is None`, on the assumption that a
    # directory outside any project finds no manifest above it. That
    # assumption is machine-dependent and was false on the machine this was
    # written on, where ~/.advanced-plans/ exists (holding specs/) with no
    # manifest - so the walk reached the HOME directory and treated it as a
    # project. That is not a test artefact, it is the finding: without the
    # boundary stop, any uninstalled project on such a machine would adopt
    # whatever manifest the home directory came to hold.
    orphan = tmp_path / "unrelated"
    orphan.mkdir()
    try:
        found = ap_launcher.find_manifest(str(orphan))
    except ap_launcher.Boundary as exc:
        # A boundary above it, with no manifest: refused, not borrowed.
        assert exc.kind in ("project", "repo")
        assert not os.path.isfile(
            os.path.join(exc.directory, ".advanced-plans", "runtime.json"))
    else:
        # Or genuinely nothing above it, on a machine with no such directory.
        assert found is None


def test_unreachable_carries_a_fix():
    exc = ap_launcher.Unreachable("something is wrong", "do this")
    assert exc.problem == "something is wrong"
    assert exc.fix == "do this"


def _launcher_imports():
    import ast
    tree = ast.parse(io.open(str(LAUNCHER_SRC), encoding="utf-8").read())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def test_launcher_imports_nothing_from_the_package_it_resolves():
    """It has to run before the runtime is reachable, so it cannot depend on
    it. Importing `platforms` here would be circular by construction."""
    assert "platforms" not in _launcher_imports()


def test_launcher_stays_inside_the_canonical_allow_set():
    """CI runs ast_check over platforms/python/, so a dependency added here
    fails the build. Checked against core/constraints.json rather than a list
    copied into this file, which would drift the moment the policy changed.
    """
    constraints = json.loads(
        io.open(str(_REPO_ROOT / "core" / "constraints.json"),
                encoding="utf-8").read())
    allowed = set(constraints["allowed_imports"])
    excluded = set(constraints.get("explicitly_excluded", []))
    imported = _launcher_imports()
    assert not (imported & excluded), (
        "the launcher imports %s, which core/constraints.json explicitly "
        "excludes" % sorted(imported & excluded))
    assert imported <= allowed, (
        "the launcher imports %s, which is outside the canonical allow-set. "
        "Either use something in it, or widen core/constraints.json "
        "deliberately and say why in its notes."
        % sorted(imported - allowed))



def test_no_command_invokes_python3_by_name():
    """One interpreter name across all call sites, and it is `python`.

    Sixteen call sites said `python` and two said `python3`. On Windows that is
    not a spelling difference: `python3` is the Microsoft Store alias, which on
    a machine that has never installed from the Store opens the Store page
    instead of running anything, and on a machine that has, resolves to a
    *different interpreter* than `python` does -- verified here, where
    `python3` is a 3.13 WindowsApps shim while `python` is the 3.12 install the
    rest of this suite runs against.

    Neither of the two sites routed through ap.py, so this is not the
    unreachable-runtime defect. It is the same mistake one layer out: the
    command decides which interpreter runs, and two of them decided
    differently for no reason anyone recorded.
    """
    offenders = []
    for md in sorted(COMMANDS_DIR.glob("*.md")):
        text = io.open(str(md), encoding="utf-8", newline="").read()
        for match in re.finditer(r"\bpython3\b", text):
            line = text.count("\n", 0, match.start()) + 1
            offenders.append("%s:%d" % (md.name, line))
    assert not offenders, (
        "these call sites invoke python3 rather than python: %s. Use `python`, "
        "which is what every other call site and every installer uses."
        % ", ".join(offenders))


# ---------------------------------------------------------------------------
# The guard the F15 allow-set decision removed
# ---------------------------------------------------------------------------

SETUP_DIR = _REPO_ROOT / "setup"

# The two installer forms that copy a module out of platforms/python/ into a
# directory where the platforms package does not exist. Anchored on the copy
# verb, not on the path alone: install.sh also NAMES ap_launcher.py in a
# comment, and a check that counted comments would keep passing on a repo that
# had stopped shipping anything at all.
_SH_COPY = re.compile(
    r'do_cp\s+"\$REPO_ROOT/platforms/python/([A-Za-z0-9_]+\.py)"')
_PS1_COPY = re.compile(
    r'Do-Copy\s+\(Join-Path\s+\$RepoRoot\s+'
    r'"platforms\\python\\([A-Za-z0-9_]+\.py)"\)')


def _shipped_modules():
    """Every platforms/python module an installer copies, read off the installers.

    Returns
    -------
    dict
        {module filename: sorted list of "<host>/<installer>:<line>" sites}.
    """
    found = {}
    installers = (sorted(SETUP_DIR.glob("*/install.sh"))
                  + sorted(SETUP_DIR.glob("*/install.ps1")))
    for installer in installers:
        text = io.open(str(installer), encoding="utf-8", newline="").read()
        pattern = _SH_COPY if installer.suffix == ".sh" else _PS1_COPY
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            site = "%s/%s:%d" % (installer.parent.name, installer.name, line)
            found.setdefault(match.group(1), []).append(site)
    return dict((name, sorted(sites)) for name, sites in found.items())


class TestShippedModulesImportStdlibOnly:
    """A shipped module may not import the package that is not shipped with it.

    core/constraints.json now admits ``platforms`` to the allow-set, so
    ast_check no longer catches this. That was a deliberate decision -- see the
    note in that file -- and it is correct for the sixteen modules no install
    ships, whose imports resolve because they only ever run from the checkout.

    It is not correct for the ones that ARE shipped. An installer copies
    ap_launcher.py to ``<project>/.advanced-plans/bin/ap.py``, where no
    platforms package exists; a ``platforms`` import there is the exact
    unreachable-runtime failure this module's other tests were written for.
    Nothing checked that any more. This does.

    The subject is read off the installers rather than typed here, so a module
    that starts being shipped is covered the day it starts, and the first test
    below fails if that reading ever stops finding anything.
    """

    def test_the_discovery_finds_the_installers(self):
        """The guard's subject must be a real reading, not an empty set.

        A regex that silently stops matching turns the guard below into a loop
        over nothing, which passes. That is the failure this suite exists to
        catch, so it is checked before the thing it enables.
        """
        shipped = _shipped_modules()
        assert shipped, (
            "no installer was found to copy anything out of platforms/python/. "
            "Either the copy verb changed and _SH_COPY/_PS1_COPY need "
            "updating, or nothing is shipped any more -- in which case this "
            "whole class should go rather than pass over an empty set.")
        assert "ap_launcher.py" in shipped, (
            "ap_launcher.py is the module this guard was written for and the "
            "installers no longer appear to ship it. Found instead: %s"
            % ", ".join(sorted(shipped)))

        sites = shipped["ap_launcher.py"]
        kinds = set(site.split("/")[1].split(":")[0] for site in sites)
        assert kinds == set(["install.sh", "install.ps1"]), (
            "only %s matched, so one of the two installer patterns has gone "
            "stale and half the shipping sites are invisible to this guard. "
            "Sites: %s" % (", ".join(sorted(kinds)), ", ".join(sites)))

        hosts = set(site.split("/")[0] for site in sites)
        assert len(hosts) >= 2, (
            "ap_launcher.py was found shipped by only one host (%s). Every "
            "adapter ships it, so this reading is incomplete."
            % ", ".join(sorted(hosts)))

    def test_shipped_modules_import_stdlib_only(self, monkeypatch):
        """The guard proper: no shipped module may import platforms."""
        from platforms.python import ast_check

        full = ast_check.load_allowed_imports()
        assert "platforms" in full, (
            "this class exists only because 'platforms' is in the allow-set. "
            "If the exemption has since been scoped to unshipped modules, "
            "ast_check covers the shipped ones again and this class should be "
            "deleted rather than adjusted until it passes.")

        stdlib_only = full - set(["platforms"])
        monkeypatch.setattr(
            ast_check, "load_allowed_imports", lambda: stdlib_only)

        offenders = []
        for name, sites in sorted(_shipped_modules().items()):
            source = _REPO_ROOT / "platforms" / "python" / name
            assert source.is_file(), (
                "%s is copied by %s but does not exist in platforms/python/"
                % (name, ", ".join(sites)))
            for violation in ast_check.check_file(source):
                offenders.append(
                    "%s:%d imports %r -- shipped by %s"
                    % (name, violation.line, violation.imported_name,
                       ", ".join(sites)))

        assert not offenders, (
            "these modules are copied into a directory that has no platforms "
            "package, so these imports fail at runtime in every installed "
            "project:\n  %s\nEither drop the import or stop shipping the "
            "module." % "\n  ".join(offenders))
