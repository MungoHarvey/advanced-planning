"""Tests for platforms/python/ast_check.py.

Coverage:
- Parses constraints.json fixture and returns the expected allow-set
- Happy-path file with only allowed imports passes (zero violations)
- Violation fixture with __future__ produces non-empty result
- Round-trip test: load_allowed_imports() equals the set parsed from JSON
"""

import json
import pathlib
import sys
import tempfile

import pytest

# Ensure the repo root is on sys.path so the module is importable without
# installing. The tests/ dir is two levels down: tests/ -> python/ -> platforms/ -> repo-root
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from platforms.python.ast_check import (  # noqa: E402
    Violation,
    check_file,
    load_allowed_imports,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONSTRAINTS_PATH = _REPO_ROOT / "core" / "constraints.json"


def _write_temp_py(source: str) -> pathlib.Path:
    """Write source text to a temp .py file and return its path."""
    fd, name = tempfile.mkstemp(suffix=".py")
    import os

    os.close(fd)
    p = pathlib.Path(name)
    p.write_text(source, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# TestLoadAllowedImports — load_allowed_imports() returns the correct set
# ---------------------------------------------------------------------------


class TestLoadAllowedImports:
    def test_returns_a_set(self):
        result = load_allowed_imports()
        assert isinstance(result, set)

    def test_set_is_nonempty(self):
        result = load_allowed_imports()
        assert len(result) > 0

    def test_canonical_entries_present(self):
        """The entries declared in CLAUDE.md Key Constraints must all be present."""
        expected = {
            "ast",
            "json",
            "pathlib",
            "re",
            "datetime",
            "typing",
            "os",
            "sys",
            "tempfile",
            "textwrap",
            "argparse",
            "asyncio",
        }
        result = load_allowed_imports()
        assert expected == result, (
            f"Allow-set mismatch.\nExpected: {sorted(expected)}\nGot: {sorted(result)}"
        )

    def test_future_not_in_allowed(self):
        """__future__ must be explicitly excluded from the allow-set."""
        result = load_allowed_imports()
        assert "__future__" not in result

    def test_round_trip_matches_json_directly(self):
        """Round-trip: load_allowed_imports() must equal parsing the JSON file directly."""
        raw = json.loads(_CONSTRAINTS_PATH.read_text(encoding="utf-8"))
        expected_from_json = set(raw["allowed_imports"])
        result = load_allowed_imports()
        assert result == expected_from_json, (
            "load_allowed_imports() diverges from direct JSON parse. "
            f"API returned: {sorted(result)}, JSON has: {sorted(expected_from_json)}"
        )


# ---------------------------------------------------------------------------
# TestCheckFileHappyPath — clean files produce zero violations
# ---------------------------------------------------------------------------


class TestCheckFileHappyPath:
    def test_file_with_only_allowed_imports_passes(self):
        source = (
            "import json\n"
            "import pathlib\n"
            "import re\n"
            "import datetime\n"
            "import typing\n"
            "import os\n"
            "import sys\n"
            "import tempfile\n"
            "import textwrap\n"
            "import argparse\n"
            "import asyncio\n"
            "\n"
            "def main():\n"
            "    pass\n"
        )
        p = _write_temp_py(source)
        try:
            violations = check_file(p)
            assert violations == [], (
                f"Expected no violations but got: {violations}"
            )
        finally:
            p.unlink(missing_ok=True)

    def test_file_with_from_imports_of_allowed_modules_passes(self):
        source = (
            "from pathlib import Path\n"
            "from typing import List, Optional\n"
            "from datetime import datetime\n"
        )
        p = _write_temp_py(source)
        try:
            violations = check_file(p)
            assert violations == [], (
                f"Expected no violations but got: {violations}"
            )
        finally:
            p.unlink(missing_ok=True)

    def test_empty_file_passes(self):
        p = _write_temp_py("")
        try:
            violations = check_file(p)
            assert violations == []
        finally:
            p.unlink(missing_ok=True)

    def test_file_with_no_imports_passes(self):
        source = "x = 1\n\ndef f():\n    return x\n"
        p = _write_temp_py(source)
        try:
            violations = check_file(p)
            assert violations == []
        finally:
            p.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# TestCheckFileViolations — disallowed imports produce non-empty result
# ---------------------------------------------------------------------------


class TestCheckFileViolations:
    def test_future_import_produces_violation(self):
        """__future__ is explicitly excluded and must produce a violation."""
        source = "from __future__ import annotations\nimport json\n"
        p = _write_temp_py(source)
        try:
            violations = check_file(p)
            assert len(violations) > 0, (
                "Expected at least one violation for __future__ import"
            )
            names = [v.imported_name for v in violations]
            assert "__future__" in names, (
                f"Expected __future__ in violation names, got: {names}"
            )
        finally:
            p.unlink(missing_ok=True)

    def test_external_package_import_produces_violation(self):
        source = "import requests\nimport json\n"
        p = _write_temp_py(source)
        try:
            violations = check_file(p)
            assert len(violations) > 0
            names = [v.imported_name for v in violations]
            assert "requests" in names
        finally:
            p.unlink(missing_ok=True)

    def test_violation_contains_file_and_line(self):
        source = "import numpy\n"
        p = _write_temp_py(source)
        try:
            violations = check_file(p)
            assert len(violations) == 1
            v = violations[0]
            assert v.file == p
            assert v.line == 1
            assert v.imported_name == "numpy"
        finally:
            p.unlink(missing_ok=True)

    def test_multiple_violations_reported(self):
        source = "import requests\nimport numpy\nimport json\n"
        p = _write_temp_py(source)
        try:
            violations = check_file(p)
            names = {v.imported_name for v in violations}
            assert "requests" in names
            assert "numpy" in names
            assert "json" not in names
        finally:
            p.unlink(missing_ok=True)

    def test_violation_is_named_tuple(self):
        source = "import requests\n"
        p = _write_temp_py(source)
        try:
            violations = check_file(p)
            assert len(violations) == 1
            v = violations[0]
            assert isinstance(v, Violation)
            assert hasattr(v, "file")
            assert hasattr(v, "line")
            assert hasattr(v, "imported_name")
            assert hasattr(v, "reason")
        finally:
            p.unlink(missing_ok=True)
