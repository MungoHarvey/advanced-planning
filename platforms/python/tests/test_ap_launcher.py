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
import subprocess
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
    pattern = re.compile(r"bin/ap\.py\s+([a-z_][a-z0-9_]*)")
    seen, missing = set(), []
    for md in sorted(COMMANDS_DIR.glob("*.md")):
        text = io.open(str(md), encoding="utf-8", newline="").read()
        for m in pattern.finditer(text):
            seen.add(m.group(1))
            if m.group(1) not in available:
                missing.append("%s: %s" % (md.name, m.group(1)))
    assert seen, "no launcher call sites found at all - did the rewrite land?"
    assert not missing, "call sites name modules that do not exist: %s" % missing


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
    guard = next(i for i, l in enumerate(lines)
                 if "skipping scaffold" in l.lower())
    manifest = next(i for i, l in enumerate(lines) if "runtime.json" in l)
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
        audit = sync.index("python .advanced-plans/bin/ap.py install_audit")
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

    orphan = tmp_path / "unrelated"
    orphan.mkdir()
    assert ap_launcher.find_manifest(str(orphan)) is None


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
