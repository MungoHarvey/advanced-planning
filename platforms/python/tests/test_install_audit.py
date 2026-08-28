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

import pytest

from platforms.python.install_audit import (
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
