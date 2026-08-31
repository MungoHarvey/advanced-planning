# -*- coding: utf-8 -*-
"""Reach the shared Python runtime from a project that only has the adapter.

The problem this exists to solve
--------------------------------
Advanced Planning's slash commands shell out to ``python -m
platforms.python.<module>`` with the *project* as the working directory. No
installer ships ``platforms/python/`` into a project, so every one of those
invocations dies with ``ModuleNotFoundError: No module named 'platforms'`` in
any project that is not the source checkout. The modules are fine; they are
not *reachable*.

The fix is mechanism (c) of four costed at the phase-6 loop-001 decision gate:
**resolve a recorded source path**, rather than copying the runtime into every
project (an Nth copy of executable code that can drift) or putting a console
script on PATH (a packaging system and a PATH mutation, for what is really a
search-path problem).

Every adapter installer writes ``.advanced-plans/runtime.json``::

    {"schema_version": 1, "source_root": "/abs/path/to/advanced-planning", ...}

and every call site invokes modules through this launcher instead of ``-m``::

    python .advanced-plans/bin/ap.py history_log .advanced-plans/state/history.jsonl ...

``.advanced-plans/`` is the host-neutral location, not ``.claude/``: the Codex,
OpenCode and Cursor adapters resolve the runtime by exactly this route, which
is why the manifest is not adapter-scoped.

Mechanism (d), the guard, is not separable from (c) and is implemented here.
The recorded path is absolute, so a moved or renamed source checkout breaks it.
Before the guard, that failed as a bare ``ModuleNotFoundError`` in the middle
of a slash command, naming neither the manifest nor the repair. Now every
failure names the file, the key and the command that fixes it, and exits ``3``
so a caller can tell "the runtime is unreachable" from "the module ran and
returned non-zero".

Resolution order
----------------
1. ``$ADVANCED_PLANNING_ROOT`` -- an operator escape hatch that needs no
   manifest, and what the tests use.
2. ``source_root`` in the nearest ``.advanced-plans/runtime.json``, searched
   from the working directory upward, so a command still works when it is run
   from a subdirectory. The walk stops at a *boundary* -- a directory that is
   itself a project (it has ``.advanced-plans/``) or a repository root (it has
   ``.git``) -- so a nested project or a vendored repository can never inherit
   the checkout of whatever happens to enclose it.
3. The **global** record at ``<home>/.advanced-plans/runtime.json``, written
   only by ``--global`` installs. This is what makes a globally-installed
   command work in a project that was never project-installed, which is the
   whole point of a global install. Reaching a boundary in step 2 does not
   skip this step: a project that has scaffolded ``.advanced-plans/`` but was
   never project-installed is precisely the global case.
4. This file's own checkout, when it is running from inside one. That is what
   makes the source repository work with no manifest at all.

``<home>`` is ``%USERPROFILE%`` before ``$HOME``. Under Git Bash on Windows
``$HOME`` is routinely a mapped network drive while the installers and
``install_audit`` use the local profile, so resolving the global record with
``os.path.expanduser('~')`` would look in a different place from the one the
installer wrote to - the original defect, moved rather than fixed.

Whatever is resolved must actually contain ``platforms/python/__init__.py``. A
path that no longer points at a checkout is a stale manifest, and that is the
failure the guard exists for.

Usage
-----
    python .advanced-plans/bin/ap.py <module> [args...]   # run a module
    python .advanced-plans/bin/ap.py --path               # print source_root
    python .advanced-plans/bin/ap.py --check              # diagnose, do not run

``--path`` is for the call sites that are inline ``python -c`` scripts rather
than module invocations: they set ``PYTHONPATH`` from it and leave their own
body unchanged. It carries the same guard, so those sites are covered too.

Standard library only, and it must not import the package it is resolving --
this file has to run *before* the runtime is reachable.
"""
import json
import os
import pathlib
import sys

EXIT_UNREACHABLE = 3

MANIFEST_RELPATH = os.path.join(".advanced-plans", "runtime.json")
PROJECT_MARKER = ".advanced-plans"
MANIFEST_KEY = "source_root"
ENV_VAR = "ADVANCED_PLANNING_ROOT"
PACKAGE_MARKER = os.path.join("platforms", "python", "__init__.py")
REPO_MARKER = ".git"


def global_home(env=None):
    """The user profile directory, preferring USERPROFILE over HOME.

    Deliberately duplicates ``install_audit.resolve_global_home``. This file
    is copied out of the checkout and run before the runtime is reachable, so
    it cannot import the module it agrees with. The duplication is pinned by
    test_global_home_agrees_with_install_audit, which fails if either side is
    changed alone - the drift this launcher's own design notes warn about,
    made loud rather than assumed away.
    """
    env = os.environ if env is None else env
    for key in ("USERPROFILE", "HOME"):
        value = env.get(key)
        if value:
            return value
    return os.path.expanduser("~")


def _is_ancestor(parent, child):
    """True when `parent` is `child` or contains it."""
    parent = os.path.normcase(os.path.abspath(parent))
    child = os.path.normcase(os.path.abspath(child))
    return child == parent or child.startswith(parent + os.sep)


def sibling_manifest(start=None):
    """The manifest beside this launcher, if this launcher is an installed one.

    ``<anywhere>/.advanced-plans/bin/ap.py`` has its manifest two directories
    up at ``<anywhere>/.advanced-plans/runtime.json``. For the global copy that
    IS the global record, and reading it this way rather than re-deriving the
    profile directory is what makes install-time and run-time agree: a record
    written under one home and read under another - CI, a container, a service
    account, or just Git Bash's mapped $HOME against a PowerShell install - is
    otherwise invisible. Found by installing globally into one profile and
    calling the result from a shell holding a different one.

    For a project copy this resolves to that project's own manifest, which the
    upward walk has already found. Harmless there, and it means one rule
    covers both.

    With one refusal, which is the whole reason this is not two lines: if the
    launcher's own project ENCLOSES the directory being resolved, using its
    record is the borrowing the boundary stop exists to refuse - just arrived
    at by a different route. Running `outer/.advanced-plans/bin/ap.py` from
    `outer/vendor/inner` must still say "inner is not installed", not quietly
    run outer's checkout. The upward walk stays authoritative over this.

    Residual, stated rather than hidden: a global install whose profile
    encloses the project AND whose install-time home differs from the
    run-time home falls back to the profile-derived lookup, which will not
    find it. That combination fails loudly with the usual exit 3, and the
    repair - reinstall - is the right one.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(here) != "bin":
        return None
    ap_dir = os.path.dirname(here)
    if os.path.basename(ap_dir) != PROJECT_MARKER:
        return None
    if _is_ancestor(os.path.dirname(ap_dir),
                    os.path.abspath(start or os.getcwd())):
        return None
    candidate = os.path.join(ap_dir, "runtime.json")
    return candidate if os.path.isfile(candidate) else None


def global_manifest(env=None):
    """Path of the profile-level record. Existence is not implied."""
    return os.path.join(global_home(env), MANIFEST_RELPATH)


class Unreachable(Exception):
    """The shared runtime could not be resolved. Carries the operator fix."""

    def __init__(self, problem, fix):
        Exception.__init__(self, problem)
        self.problem = problem
        self.fix = fix

    def report(self, stream=None):
        stream = stream or sys.stderr
        stream.write("advanced-planning: %s\n" % self.problem)
        stream.write("advanced-planning: fix: %s\n" % self.fix)


class Boundary(Exception):
    """The upward walk reached a directory it must not search past.

    Two kinds, and the distinction is only for the diagnostic:

    ``project``
        the directory has ``.advanced-plans/`` but no manifest -- it is a
        project that was never installed;
    ``repo``
        the directory is a repository root with no manifest -- a separate
        piece of software that merely lives inside another.

    Neither is an error on its own. Both mean "stop looking upward for a
    *project* manifest"; the global record is consulted next. What they
    prevent is the one failure this design is most exposed to: succeeding
    against the wrong checkout without saying so.
    """

    def __init__(self, directory, kind):
        Exception.__init__(self, directory)
        self.directory = directory
        self.kind = kind


def find_manifest(start=None):
    """The nearest .advanced-plans/runtime.json at or above `start`.

    Walking up matters: a slash command is as likely to be run from a package
    subdirectory as from the project root, and a launcher that looked only in
    the working directory would fail there for no reason a user could see.

    But the walk stops at a boundary, raising `Boundary` rather than
    climbing past it. A directory holding ``.advanced-plans/`` IS a project,
    and a directory holding ``.git`` is a separate piece of software; if
    either has no manifest of its own, the answer is "not installed", not
    "borrow the manifest of whatever happens to contain it".

    Both stops were found by a cross-vendor review panel and reproduced
    before being fixed. Without the project stop, a project vendored inside
    another silently resolved to the OUTER project's checkout and ran it,
    exit 0, no diagnostic. The repository stop closes the same hole for the
    commoner case the first one misses: a nested independent repository -- a
    monorepo service, a submodule -- that has no ``.advanced-plans/`` marker
    to stop on at all.

    The caller decides what a boundary means. It is not a failure: the global
    record is consulted next, and only if that is absent too does it become
    an error.
    """
    here = os.path.abspath(start or os.getcwd())
    while True:
        candidate = os.path.join(here, MANIFEST_RELPATH)
        if os.path.isfile(candidate):
            return candidate
        if os.path.isdir(os.path.join(here, PROJECT_MARKER)):
            raise Boundary(here, "project")
        if os.path.exists(os.path.join(here, REPO_MARKER)):
            # A file, not just a directory: linked worktrees and submodules
            # record their git dir in a `.git` FILE, and those are exactly
            # the nested checkouts this stop exists for.
            raise Boundary(here, "repo")
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


def _launcher_checkout():
    """The source checkout this file is running from, or None.

    True in the source repository (``platforms/python/ap_launcher.py``) and
    false for the installed copy at ``.advanced-plans/bin/ap.py``, which is
    the whole reason the manifest exists.
    """
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    if not os.path.isfile(os.path.join(root, PACKAGE_MARKER)):
        return None
    if (os.path.normcase(root)
            == os.path.normcase(os.path.abspath(global_home()))):
        # Three dirnames up from <home>/.advanced-plans/bin/ap.py is <home>.
        # A user who happens to keep platforms/python/ under their profile
        # would otherwise have the profile silently adopted as the runtime.
        return None
    return root


def resolve(start=None):
    """Return (source_root, how_it_was_found). Raise Unreachable with a fix."""
    env = os.environ.get(ENV_VAR, "").strip()
    if env:
        if not os.path.isfile(os.path.join(env, PACKAGE_MARKER)):
            raise Unreachable(
                "%s is set to %r, which is not an Advanced Planning checkout "
                "(no %s under it)" % (ENV_VAR, env, PACKAGE_MARKER),
                "unset %s, or point it at the directory that contains core/ "
                "and platforms/." % ENV_VAR)
        return os.path.abspath(env), "$" + ENV_VAR

    boundary = None
    try:
        manifest = find_manifest(start)
    except Boundary as exc:
        boundary, manifest = exc, None

    if manifest is None:
        # The global record, written only by a --global install. This is what
        # a globally-installed command falls back to, including in a project
        # that has scaffolded .advanced-plans/ without ever being installed.
        #
        # Beside-the-launcher first: it cannot disagree with the install that
        # wrote it. The profile-derived path is the fallback for a launcher
        # invoked from a source checkout while a global install exists.
        manifest = sibling_manifest(start)
    if manifest is None:
        candidate = global_manifest()
        if os.path.isfile(candidate):
            manifest = candidate

    if manifest is not None:
        try:
            data = json.loads(pathlib.Path(manifest).read_text(encoding="utf-8"))
        except ValueError as exc:
            raise Unreachable(
                "%s is not valid JSON (%s)" % (manifest, exc),
                "re-run this project's installer, or repair the file by hand: "
                "it needs a %r key holding the absolute path to your "
                "advanced-planning checkout." % MANIFEST_KEY)
        if not isinstance(data, dict):
            # Valid JSON is not the same as a manifest. `[]` parses fine and
            # then raises AttributeError on .get, which is the raw traceback
            # this guard exists to replace.
            raise Unreachable(
                "%s parses as JSON but is a %s, not an object"
                % (manifest, type(data).__name__),
                "re-run this project's installer, or replace the file with an "
                "object holding a %r key." % MANIFEST_KEY)
        root = data.get(MANIFEST_KEY)
        if root is not None and not isinstance(root, str):
            raise Unreachable(
                "%s records %s as a %s; it must be a string path"
                % (manifest, MANIFEST_KEY, type(root).__name__),
                "re-run this project's installer, or set %r to the absolute "
                "path of your advanced-planning checkout." % MANIFEST_KEY)
        root = (root or "").strip()
        if not root:
            raise Unreachable(
                "%s has no %r" % (manifest, MANIFEST_KEY),
                "re-run this project's installer, which writes that key.")
        if not os.path.isfile(os.path.join(root, PACKAGE_MARKER)):
            raise Unreachable(
                "%s records %s = %r, but there is no %s under it - the "
                "checkout has most likely been moved, renamed or deleted"
                % (manifest, MANIFEST_KEY, root, PACKAGE_MARKER),
                "re-run the installer from the checkout's new location "
                "(setup/claude-code/install.ps1 or install.sh), or run "
                "/sync-install, or edit %s so %r points at it."
                % (manifest, MANIFEST_KEY))
        return os.path.abspath(root), manifest

    own = _launcher_checkout()
    if own:
        return own, "the checkout this launcher is running from"

    if boundary is not None:
        what = ("an Advanced Planning project (it has %s/)" % PROJECT_MARKER
                if boundary.kind == "project"
                else "a repository root (it has %s)" % REPO_MARKER)
        raise Unreachable(
            "%s is %s but has no %s, and there is no global record at %s "
            "either" % (boundary.directory, what, MANIFEST_RELPATH,
                        global_manifest()),
            "run this project's installer from your advanced-planning "
            "checkout (setup/claude-code/install.ps1 or install.sh), or "
            "install globally with --global. The walk stops here rather than "
            "borrowing the manifest of whatever encloses this directory, "
            "which would run the wrong checkout without saying so.")

    raise Unreachable(
        "no %s found in %s or any parent directory, no global record at %s, "
        "and this launcher is not running from a source checkout"
        % (MANIFEST_RELPATH, os.getcwd(), global_manifest()),
        "run this project's installer (setup/claude-code/install.ps1 or "
        "install.sh), which writes that file; or install globally with "
        "--global; or set %s to your advanced-planning checkout." % ENV_VAR)


def bootstrap(start=None):
    """Put the resolved runtime on sys.path and return its root.

    This is the entry point for the inline ``python -c`` call sites::

        import runpy; runpy.run_path('...ap.py')['bootstrap']()

    which is half of them. It reports and exits rather than letting
    `Unreachable` propagate: an exception escaping here reaches the operator
    as a traceback naming a line number inside this file, which is precisely
    the failure the guard exists to replace - and it would replace it at only
    the other half of the call sites. Exiting keeps one contract for every
    site: exit 3, the manifest named, the repair named.
    """
    try:
        root, _how = resolve(start)
    except Unreachable as exc:
        exc.report()
        raise SystemExit(EXIT_UNREACHABLE)
    if root not in sys.path:
        sys.path.insert(0, root)
    return root


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        sys.stderr.write("advanced-planning: no module named. "
                         "Usage: ap.py <module> [args...] | --path | --check\n")
        return EXIT_UNREACHABLE
    if argv[0] in ("-h", "--help"):
        sys.stdout.write(__doc__.split("Usage\n-----\n", 1)[-1].strip() + "\n")
        return 0

    try:
        root, how = resolve()
    except Unreachable as exc:
        exc.report()
        return EXIT_UNREACHABLE

    if argv[0] == "--path":
        sys.stdout.write(root + "\n")
        return 0
    if argv[0] == "--check":
        sys.stdout.write("advanced-planning: runtime at %s (via %s)\n"
                         % (root, how))
        return 0

    module = argv[0]
    if module.startswith("-"):
        sys.stderr.write("advanced-planning: unknown option %r\n" % module)
        return EXIT_UNREACHABLE
    if not module.startswith("platforms.python."):
        module = "platforms.python." + module

    if root not in sys.path:
        sys.path.insert(0, root)
    sys.argv = [module.rsplit(".", 1)[-1]] + argv[1:]

    import runpy
    try:
        runpy.run_module(module, run_name="__main__", alter_sys=True)
    except ImportError as exc:
        # Resolution succeeded, so the checkout is real; this is a module that
        # is not in it. Reporting that as a path problem would send the reader
        # to entirely the wrong file.
        sys.stderr.write("advanced-planning: %s is not in the runtime at %s "
                         "(%s)\n" % (module, root, exc))
        sys.stderr.write("advanced-planning: fix: check the module name, or "
                         "update the checkout - it may predate this command.\n")
        return EXIT_UNREACHABLE
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        return 0 if not exc.code else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
