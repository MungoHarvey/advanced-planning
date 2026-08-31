"""
Tests for platforms/python/install_audit.py.

Covers:
  1. current detection -- identical content (LF) hashes the same
  2. stale detection   -- modified installed file triggers stale verdict
  3. missing detection -- source file absent in installed layer
  4. EOL-insensitivity -- CRLF vs LF same content -> current, not stale
  5. USERPROFILE-before-HOME resolution -- monkeypatched env
  6. --layers pair selection -- source,project vs source,global vs all
"""

import pathlib
import re

import pytest

from platforms.python.install_audit import (
    _VALID_LAYER_PAIRS,
    FileVerdict,
    _file_hash,
    LayerPairResult,
    audit_pair,
    has_drift,
    main,
    resolve_global_home,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_surface(base: pathlib.Path, subdir: str, files: dict) -> None:
    """Create a surface directory with the given filename -> content mapping."""
    d = base / subdir
    d.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (d / name).write_text(content, encoding="utf-8")


def _make_repo(tmp_path: pathlib.Path, commands_src: dict, agents_src: dict, schemas_src: dict):
    """Create a minimal fake repo tree under tmp_path/repo/."""
    repo = tmp_path / "repo"
    _make_surface(repo / "platforms" / "claude-code", "commands", commands_src)
    _make_surface(repo / "platforms" / "claude-code", "agents", agents_src)
    _make_surface(repo / "core", "schemas", schemas_src)
    # Install core/constraints.json so find_repo_root works
    (repo / "core" / "constraints.json").write_text("{}", encoding="utf-8")
    return repo


# ---------------------------------------------------------------------------
# 1. current detection
# ---------------------------------------------------------------------------

class TestCurrentDetection:
    def test_identical_lf_content_is_current(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            commands_src={"cmd.md": "# command\n"},
            agents_src={},
            schemas_src={},
        )
        installed = tmp_path / "project" / ".claude"
        _make_surface(installed, "commands", {"cmd.md": "# command\n"})

        result = audit_pair(repo, installed, "source -> project")
        v = result.verdicts[0]
        assert v.filename == "cmd.md"
        assert v.verdict == "current"

    def test_no_drift_means_has_drift_false(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            commands_src={"a.md": "hello\n"},
            agents_src={},
            schemas_src={},
        )
        installed = tmp_path / "project" / ".claude"
        _make_surface(installed, "commands", {"a.md": "hello\n"})

        result = audit_pair(repo, installed, "source -> project")
        assert not has_drift(result)


# ---------------------------------------------------------------------------
# 2. stale detection
# ---------------------------------------------------------------------------

class TestStaleDetection:
    def test_modified_installed_file_is_stale(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            commands_src={"cmd.md": "# original\n"},
            agents_src={},
            schemas_src={},
        )
        installed = tmp_path / "project" / ".claude"
        _make_surface(installed, "commands", {"cmd.md": "# MODIFIED\n"})

        result = audit_pair(repo, installed, "source -> project")
        v = result.verdicts[0]
        assert v.verdict == "stale"
        assert v.source_hash != v.installed_hash

    def test_stale_triggers_has_drift(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            commands_src={"cmd.md": "# v1\n"},
            agents_src={},
            schemas_src={},
        )
        installed = tmp_path / "project" / ".claude"
        _make_surface(installed, "commands", {"cmd.md": "# v2\n"})

        result = audit_pair(repo, installed, "source -> project")
        assert has_drift(result)


# ---------------------------------------------------------------------------
# 3. missing detection
# ---------------------------------------------------------------------------

class TestMissingDetection:
    def test_source_file_absent_in_installed_is_missing(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            commands_src={"new.md": "# new command\n"},
            agents_src={},
            schemas_src={},
        )
        installed = tmp_path / "project" / ".claude"
        # installed/commands/ exists but does NOT contain new.md
        _make_surface(installed, "commands", {})

        result = audit_pair(repo, installed, "source -> project")
        v = next(vd for vd in result.verdicts if vd.filename == "new.md")
        assert v.verdict == "missing"
        assert v.installed_hash is None

    def test_missing_triggers_has_drift(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            commands_src={"absent.md": "content\n"},
            agents_src={},
            schemas_src={},
        )
        installed = tmp_path / "project" / ".claude"
        _make_surface(installed, "commands", {})

        result = audit_pair(repo, installed, "source -> project")
        assert has_drift(result)

    def test_extra_file_in_installed_only_is_extra_not_failure(self, tmp_path):
        """Files only in the installed layer are 'extra' -- not a failure."""
        repo = _make_repo(
            tmp_path,
            commands_src={},
            agents_src={},
            schemas_src={},
        )
        installed = tmp_path / "project" / ".claude"
        _make_surface(installed, "commands", {"custom.md": "project-specific\n"})

        result = audit_pair(repo, installed, "source -> project")
        v = next(vd for vd in result.verdicts if vd.filename == "custom.md")
        assert v.verdict == "extra"
        assert not has_drift(result)


# ---------------------------------------------------------------------------
# 4. EOL-insensitivity
# ---------------------------------------------------------------------------

class TestEOLInsensitivity:
    def test_crlf_installed_vs_lf_source_is_current(self, tmp_path):
        """CRLF-converted installed copy must hash identically to LF source."""
        lf_content = "line one\nline two\nline three\n"
        crlf_content = lf_content.replace("\n", "\r\n")

        repo = _make_repo(
            tmp_path,
            commands_src={"cmd.md": lf_content},
            agents_src={},
            schemas_src={},
        )
        installed = tmp_path / "project" / ".claude"
        # Write CRLF bytes directly to simulate autocrlf checkout
        crlf_bytes = crlf_content.encode("utf-8")
        (installed / "commands").mkdir(parents=True, exist_ok=True)
        (installed / "commands" / "cmd.md").write_bytes(crlf_bytes)

        result = audit_pair(repo, installed, "source -> project")
        v = result.verdicts[0]
        assert v.verdict == "current", (
            f"Expected current (EOL diff only), got {v.verdict}; "
            f"source_hash={v.source_hash}, installed_hash={v.installed_hash}"
        )

    def test_bare_cr_installed_vs_lf_source_is_current(self, tmp_path):
        """Bare \\r line endings are also normalised."""
        lf_content = "alpha\nbeta\n"
        cr_content = lf_content.replace("\n", "\r")

        repo = _make_repo(
            tmp_path,
            commands_src={"cmd.md": lf_content},
            agents_src={},
            schemas_src={},
        )
        installed = tmp_path / "project" / ".claude"
        (installed / "commands").mkdir(parents=True, exist_ok=True)
        (installed / "commands" / "cmd.md").write_bytes(cr_content.encode("utf-8"))

        result = audit_pair(repo, installed, "source -> project")
        v = result.verdicts[0]
        assert v.verdict == "current"

    def test_different_content_with_same_eol_is_stale(self, tmp_path):
        """Sanity: genuinely different content is still stale after normalisation."""
        repo = _make_repo(
            tmp_path,
            commands_src={"cmd.md": "version A\n"},
            agents_src={},
            schemas_src={},
        )
        installed = tmp_path / "project" / ".claude"
        crlf = "version B\r\n"
        (installed / "commands").mkdir(parents=True, exist_ok=True)
        (installed / "commands" / "cmd.md").write_bytes(crlf.encode("utf-8"))

        result = audit_pair(repo, installed, "source -> project")
        v = result.verdicts[0]
        assert v.verdict == "stale"


# ---------------------------------------------------------------------------
# 5. USERPROFILE-before-HOME resolution
# ---------------------------------------------------------------------------

class TestUserprofileResolution:
    def test_userprofile_wins_over_home(self, tmp_path):
        """resolve_global_home returns USERPROFILE when both are set."""
        userprofile_dir = tmp_path / "userprofile_home"
        home_dir = tmp_path / "unix_home"
        userprofile_dir.mkdir()
        home_dir.mkdir()

        env = {
            "USERPROFILE": str(userprofile_dir),
            "HOME": str(home_dir),
        }
        result = resolve_global_home(env)
        assert result == userprofile_dir

    def test_home_used_when_userprofile_absent(self, tmp_path):
        """resolve_global_home falls back to HOME when USERPROFILE is absent."""
        home_dir = tmp_path / "unix_home"
        home_dir.mkdir()

        env = {"HOME": str(home_dir)}
        result = resolve_global_home(env)
        assert result == home_dir

    def test_empty_userprofile_falls_through_to_home(self, tmp_path):
        """Empty string USERPROFILE is treated as absent."""
        home_dir = tmp_path / "unix_home"
        home_dir.mkdir()

        env = {"USERPROFILE": "", "HOME": str(home_dir)}
        result = resolve_global_home(env)
        assert result == home_dir

    def test_main_uses_monkeypatched_env_for_global_layer(self, tmp_path, monkeypatch):
        """--layers source,global uses the env-resolved home, not os.environ."""
        repo = _make_repo(
            tmp_path,
            commands_src={"cmd.md": "# cmd\n"},
            agents_src={},
            schemas_src={},
        )
        fake_global_home = tmp_path / "fake_global"
        fake_global_home.mkdir()
        # No .claude/ under fake_global_home -> "NOTE: global ... not found" + exit 0

        # Patch resolve_global_home via main(env=...) parameter
        captured = []

        original_main = main

        def run():
            return original_main(
                argv=["--root", str(repo), "--layers", "source,global"],
                env={"USERPROFILE": str(fake_global_home), "HOME": "/nope"},
            )

        rc = run()
        # Missing global dir is not a failure
        assert rc == 0


# ---------------------------------------------------------------------------
# 6. --layers pair selection
# ---------------------------------------------------------------------------

class TestLayersSelection:
    def _repo_and_project(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            commands_src={"cmd.md": "# cmd\n"},
            agents_src={"agent.md": "# agent\n"},
            schemas_src={"s.md": "# schema\n"},
        )
        project = tmp_path / "project" / ".claude"
        _make_surface(project, "commands", {"cmd.md": "# cmd\n"})
        _make_surface(project, "agents", {"agent.md": "# STALE\n"})
        _make_surface(project, "schemas", {"s.md": "# schema\n"})
        return repo, project

    def test_source_project_pair_only(self, tmp_path):
        repo, project_dot_claude = self._repo_and_project(tmp_path)
        # Place project at repo/.claude so the default project path is found
        # Instead, pass --root and use a custom project path
        result = audit_pair(repo, project_dot_claude, "source -> project")
        assert any(v.verdict == "stale" for v in result.verdicts)

    def test_layers_invalid_value_exits_2(self, tmp_path):
        repo = _make_repo(tmp_path, {}, {}, {})
        rc = main(
            argv=["--root", str(repo), "--layers", "invalid,option"],
            env={},
        )
        assert rc == 2

    def test_layers_source_project_skips_global(self, tmp_path, capsys):
        """--layers source,project must not emit global-layer output."""
        repo = _make_repo(
            tmp_path,
            commands_src={"cmd.md": "# x\n"},
            agents_src={},
            schemas_src={},
        )
        # No .claude under repo -- project layer is missing -> NOTE printed, exit 0
        rc = main(
            argv=["--root", str(repo), "--layers", "source,project"],
            env={"USERPROFILE": str(tmp_path), "HOME": str(tmp_path)},
        )
        captured = capsys.readouterr()
        # Should NOT mention "global" in the output
        assert "global" not in captured.out
        assert rc == 0

    def test_layers_source_global_skips_project(self, tmp_path, capsys):
        """--layers source,global must not emit project-layer output."""
        repo = _make_repo(
            tmp_path,
            commands_src={"cmd.md": "# x\n"},
            agents_src={},
            schemas_src={},
        )
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        # No .claude/ under fake_home -> NOTE + exit 0
        rc = main(
            argv=["--root", str(repo), "--layers", "source,global"],
            env={"USERPROFILE": str(fake_home), "HOME": str(fake_home)},
        )
        captured = capsys.readouterr()
        assert "project" not in captured.out
        assert rc == 0


# ---------------------------------------------------------------------------
# 7. the install-time launcher rewrite is canonical, not drift
# ---------------------------------------------------------------------------


class TestLauncherPathNormalisation:
    """A --global install rewrites the launcher path in every command it
    copies, because a project-relative path is meaningless from a project the
    installer never touched. Without normalising that one path back out, every
    globally installed command reports stale forever and no /sync-install can
    settle it -- observed as "6 stale" on a clean install before this landed.
    """

    def test_the_installers_absolute_path_hashes_as_the_source_form(self, tmp_path):
        src = tmp_path / "src.md"
        src.write_text(
            'python ".advanced-plans/bin/ap.py" history_log\n'
            "import runpy; runpy.run_path(r'.advanced-plans/bin/ap.py')\n",
            encoding="utf-8",
        )
        installed = tmp_path / "installed.md"
        installed.write_text(
            'python "C:/Users/bob/.advanced-plans/bin/ap.py" history_log\n'
            "import runpy; "
            "runpy.run_path(r'C:/Users/bob/.advanced-plans/bin/ap.py')\n",
            encoding="utf-8",
        )
        assert _file_hash(src) == _file_hash(installed)

    def test_a_backslash_path_normalises_too(self, tmp_path):
        """install.ps1 writes forward slashes today, but the launcher accepts
        either and a future installer changing its mind must not read as drift.
        """
        src = tmp_path / "src.md"
        src.write_text('python ".advanced-plans/bin/ap.py" run_gate\n',
                       encoding="utf-8")
        installed = tmp_path / "installed.md"
        installed.write_text(
            'python "C:\\Users\\bob\\.advanced-plans\\bin\\ap.py" run_gate\n',
            encoding="utf-8")
        assert _file_hash(src) == _file_hash(installed)

    def test_normalisation_does_not_mask_a_real_edit(self, tmp_path):
        """The narrow point. Normalisation that swallowed the rest of the line
        would turn install_audit into a no-op for exactly the files it most
        needs to police.
        """
        src = tmp_path / "src.md"
        src.write_text('python ".advanced-plans/bin/ap.py" history_log\n',
                       encoding="utf-8")
        tampered = tmp_path / "tampered.md"
        tampered.write_text(
            'python "C:/Users/bob/.advanced-plans/bin/ap.py" rm_rf\n',
            encoding="utf-8")
        assert _file_hash(src) != _file_hash(tampered)


# ---------------------------------------------------------------------------
# 7. CI asks for a layer it can actually have
# ---------------------------------------------------------------------------

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
_GITIGNORE = _REPO_ROOT / ".gitignore"

# The surfaces install_audit compares. Named here as the INSTALLED basenames,
# which is what a layer directory has to contain to be auditable at all.
_AUDITED_SURFACES = ("commands", "agents", "schemas")

_JOB_RE = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$")
_AUDIT_RE = re.compile(r"python\s+-m\s+platforms\.python\.install_audit(.*)$")
_LAYERS_RE = re.compile(r"--layers[=\s]+(\S+)")
_GLOBAL_INSTALL_RE = re.compile(r"install\.sh\b.*--global")


def _workflow_events(text):
    """Every install/audit call in a workflow, tagged with its job and line.

    Plain-text parsing rather than a YAML load: what CI runs is the literal
    command string, and this check exists precisely to compare that string
    against reality. It also keeps the test suite free of a YAML dependency.
    """
    events = []
    job = None
    for i, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        m = _JOB_RE.match(line)
        if m:
            job = m.group(1)
            continue
        if _GLOBAL_INSTALL_RE.search(line):
            events.append({"kind": "install", "job": job, "line": i})
        a = _AUDIT_RE.search(line)
        if a:
            lm = _LAYERS_RE.search(a.group(1))
            # install_audit's own default when --layers is omitted.
            events.append({"kind": "audit", "job": job, "line": i,
                           "layers": lm.group(1) if lm else "all"})
    return events


def _project_layer_is_reachable(gitignore_text):
    """Can a fresh `actions/checkout` contain .claude/commands|agents|schemas?

    A bare `.claude/*` with a single negation for settings.json is exactly the
    trap: the directory EXISTS on the runner, so install_audit's
    "not found -- skipped" guard never fires, and every source file is then
    reported missing.
    """
    lines = [l.strip() for l in gitignore_text.replace("\r\n", "\n").split("\n")]
    if not any(l in (".claude/*", ".claude/", ".claude") for l in lines):
        return True
    negated = {l[1:].rstrip("/") for l in lines if l.startswith("!")}
    return all(
        any(n == ".claude/%s" % s or n.startswith(".claude/%s/" % s) for n in negated)
        for s in _AUDITED_SURFACES
    )


def _ci_audit_problems(workflow_text, gitignore_text, valid_pairs):
    """Every reason a workflow's install_audit call cannot mean anything."""
    events = _workflow_events(workflow_text)
    problems = []
    for ev in [e for e in events if e["kind"] == "audit"]:
        pair = ev["layers"]
        where = "%s (job %s, line %d)" % (pair, ev["job"], ev["line"])

        if pair not in valid_pairs:
            problems.append(
                "invalid: --layers %s is not one of %s, so the step exits 2 "
                "before auditing anything" % (where, sorted(valid_pairs)))
            continue

        if pair in ("source,project", "all") and not _project_layer_is_reachable(
                gitignore_text):
            problems.append(
                "gitignored: --layers %s asks for the project layer, but "
                ".gitignore keeps .claude/%s out of a fresh checkout, so the "
                "job can only ever fail"
                % (where, "|".join(_AUDITED_SURFACES)))

        if pair in ("source,global", "all"):
            installed_before = [
                e for e in events
                if e["kind"] == "install" and e["job"] == ev["job"]
                and e["line"] < ev["line"]
            ]
            if not installed_before:
                problems.append(
                    "vacuous: --layers %s audits the global layer, but nothing "
                    "earlier in that job installs one. install_audit skips a "
                    "missing layer with a note and returns 0, so this step "
                    "would pass without comparing a single file" % where)
    return problems


class TestCIAuditsALayerItCanActuallyHave:
    """7: the workflow must ask install_audit for a layer that can exist.

    `--layers source,project` was in ci.yml from the start and failed on every
    run: .claude/settings.json is tracked, so .claude/ exists on the runner,
    the skip guard never fires, and all 27 source files read as missing. A
    permanently-red job teaches people to ignore the red.
    """

    def test_the_parser_actually_parses(self):
        """Without this, every assertion below passes for a broken regex.

        A parser that finds no invocations reports no problems, and that is
        indistinguishable from a workflow that is correct.
        """
        good = (
            "jobs:\n"
            "  path-convention-audit:\n"
            "    steps:\n"
            "      - run: |\n"
            "          sh setup/claude-code/install.sh --global\n"
            "      - run: |\n"
            "          python -m platforms.python.install_audit "
            "--layers source,global\n"
        )
        events = _workflow_events(good)
        kinds = [e["kind"] for e in events]
        assert kinds == ["install", "audit"], (
            "parser did not see one install then one audit: %r" % events)
        assert events[1]["layers"] == "source,global"
        assert events[1]["job"] == "path-convention-audit", (
            "the audit was not attributed to its job: %r" % events[1])
        assert not _ci_audit_problems(good, ".gitignore\n", _VALID_LAYER_PAIRS), (
            "a correct workflow was reported as a problem")

        assert _workflow_events("jobs:\n  build:\n    steps: []\n") == [], (
            "the parser invents invocations in a workflow that has none")

        # Each rule must fire on the shape it exists to catch.
        ignore = ".claude/*\n!.claude/settings.json\n"
        cases = [
            ("--layers source,project", ignore, "gitignored"),
            ("--layers source", ignore, "invalid"),
            ("--layers source,global", ignore, "vacuous"),
        ]
        for flag, gi, expected in cases:
            wf = ("jobs:\n  audit:\n    steps:\n      - run: |\n"
                  "          python -m platforms.python.install_audit %s\n" % flag)
            found = _ci_audit_problems(wf, gi, _VALID_LAYER_PAIRS)
            assert any(p.startswith(expected) for p in found), (
                "%r should have been reported as %s, got: %r"
                % (flag, expected, found))

        assert _project_layer_is_reachable(".claude/*\n!.claude/commands\n"
                                          "!.claude/agents\n!.claude/schemas\n"), (
            "a gitignore that re-includes every audited surface should be "
            "treated as reachable")

    def test_ci_audits_a_layer_that_can_exist_and_is_actually_created(self):
        assert _WORKFLOW.is_file(), "no workflow at %s" % _WORKFLOW
        text = _WORKFLOW.read_text(encoding="utf-8")
        events = _workflow_events(text)
        audits = [e for e in events if e["kind"] == "audit"]
        assert audits, (
            "no install_audit invocation found in %s. Either CI stopped "
            "auditing installs, or this parser stopped matching it -- and "
            "both make this check meaningless." % _WORKFLOW.name)

        problems = _ci_audit_problems(
            text, _GITIGNORE.read_text(encoding="utf-8"), _VALID_LAYER_PAIRS)
        assert not problems, (
            "%d CI install-audit invocation(s) cannot mean what they claim:\n"
            "  %s" % (len(problems), "\n  ".join(problems)))
