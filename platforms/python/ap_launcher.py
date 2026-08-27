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
   from a subdirectory.
3. This file's own checkout, when it is running from inside one. That is what
   makes the source repository work with no manifest at all.

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


class ProjectWithoutManifest(Exception):
    """A project directory was reached that has no manifest of its own."""

    def __init__(self, project):
        Exception.__init__(self, project)
        self.project = project


def find_manifest(start=None):
    """The nearest .advanced-plans/runtime.json at or above `start`.

    Walking up matters: a slash command is as likely to be run from a package
    subdirectory as from the project root, and a launcher that looked only in
    the working directory would fail there for no reason a user could see.

    But the walk stops at a project boundary. A directory holding
    ``.advanced-plans/`` IS a project; if it has no manifest of its own, the
    answer is "this project is not installed", not "borrow the manifest of
    whatever project happens to contain it". Without this stop, a project
    vendored inside another silently resolved to the OUTER project's checkout
    and ran it, exit 0, with no diagnostic - which is the one failure this
    design was always most exposed to. Found by a cross-vendor review panel
    and reproduced before being fixed.
    """
    here = os.path.abspath(start or os.getcwd())
    while True:
        candidate = os.path.join(here, MANIFEST_RELPATH)
        if os.path.isfile(candidate):
            return candidate
        if os.path.isdir(os.path.join(here, PROJECT_MARKER)):
            raise ProjectWithoutManifest(here)
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
    return root if os.path.isfile(os.path.join(root, PACKAGE_MARKER)) else None


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

    try:
        manifest = find_manifest(start)
    except ProjectWithoutManifest as exc:
        raise Unreachable(
            "%s is an Advanced Planning project (it has %s/) but has no %s"
            % (exc.project, PROJECT_MARKER, MANIFEST_RELPATH),
            "run this project's own installer from your advanced-planning "
            "checkout (setup/claude-code/install.ps1 or install.sh). The walk "
            "for a manifest deliberately stops here rather than borrowing an "
            "enclosing project's, which would run the wrong checkout without "
            "saying so.")
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

    raise Unreachable(
        "no %s found in %s or any parent directory, and this launcher is not "
        "running from a source checkout" % (MANIFEST_RELPATH, os.getcwd()),
        "run this project's installer (setup/claude-code/install.ps1 or "
        "install.sh), which writes that file; or set %s to your "
        "advanced-planning checkout." % ENV_VAR)


def bootstrap(start=None):
    """Put the resolved runtime on sys.path and return its root."""
    root, _how = resolve(start)
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
