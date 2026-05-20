"""
AST import checker for platforms/python/ source modules.

Loads the canonical allow-set from core/constraints.json and reports any
import that is not in the allow-set. Supports CLI mode:

    python -m platforms.python.ast_check <path> [<path> ...]

Exit codes:
    0  -- no violations found
    1  -- one or more violations found
    2  -- usage / file-not-found error
"""

import ast
import argparse
import json
import pathlib
import sys
from typing import List, NamedTuple


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class Violation(NamedTuple):
    """A single import-constraint violation."""

    file: pathlib.Path
    line: int
    imported_name: str
    reason: str


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def _find_constraints_json() -> pathlib.Path:
    """Locate core/constraints.json relative to this file or cwd.

    Parameters
    ----------
    (none)

    Returns
    -------
    pathlib.Path
        Absolute path to the constraints file.

    Raises
    ------
    FileNotFoundError
        If core/constraints.json cannot be located.
    """
    # Try relative to this file: platforms/python/ -> ../../core/constraints.json
    candidate = pathlib.Path(__file__).resolve().parent.parent.parent / "core" / "constraints.json"
    if candidate.exists():
        return candidate

    # Try relative to cwd
    candidate_cwd = pathlib.Path.cwd() / "core" / "constraints.json"
    if candidate_cwd.exists():
        return candidate_cwd

    raise FileNotFoundError(
        "core/constraints.json not found. Expected at repo-root/core/constraints.json."
    )


def load_allowed_imports() -> set:
    """Load the canonical allow-set from core/constraints.json.

    Parameters
    ----------
    (none)

    Returns
    -------
    set
        Frozenset-like set of allowed top-level module names (strings).

    Raises
    ------
    FileNotFoundError
        If core/constraints.json cannot be located.
    KeyError
        If the JSON does not contain an 'allowed_imports' key.
    """
    constraints_path = _find_constraints_json()
    data = json.loads(constraints_path.read_text(encoding="utf-8"))
    return set(data["allowed_imports"])


def check_file(path: pathlib.Path) -> List[Violation]:
    """Check a single Python source file for import-constraint violations.

    Parameters
    ----------
    path : pathlib.Path
        Path to the .py file to inspect.

    Returns
    -------
    list of Violation
        Empty list means the file is clean. Each Violation names the file,
        the line number, the imported name, and the reason.
    """
    allowed = load_allowed_imports()
    violations: List[Violation] = []

    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        violations.append(
            Violation(
                file=path,
                line=exc.lineno or 0,
                imported_name="<syntax-error>",
                reason=str(exc),
            )
        )
        return violations

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in allowed:
                    violations.append(
                        Violation(
                            file=path,
                            line=node.lineno,
                            imported_name=top,
                            reason=f"'{top}' is not in the allow-set",
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                if top not in allowed:
                    violations.append(
                        Violation(
                            file=path,
                            line=node.lineno,
                            imported_name=top,
                            reason=f"'{top}' is not in the allow-set",
                        )
                    )

    return violations


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _collect_py_files(paths: List[str]) -> List[pathlib.Path]:
    """Expand a list of path strings into individual .py files.

    Parameters
    ----------
    paths : list of str
        Each entry may be a .py file or a directory. Directories are
        searched recursively for *.py files.

    Returns
    -------
    list of pathlib.Path
        Deduplicated, sorted list of absolute paths.
    """
    result = set()
    for raw in paths:
        p = pathlib.Path(raw).resolve()
        if p.is_dir():
            for f in p.rglob("*.py"):
                result.add(f)
        elif p.suffix == ".py":
            result.add(p)
        else:
            print(f"WARN: {raw} is not a .py file or directory; skipped", file=sys.stderr)
    return sorted(result)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m platforms.python.ast_check",
        description=(
            "Check Python source files for imports not in core/constraints.json. "
            "Exit 0 = clean, exit 1 = violations found."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="+",
        metavar="PATH",
        help="One or more .py files or directories to check (directories are searched recursively).",
    )
    parser.add_argument(
        "--exclude",
        metavar="PATTERN",
        action="append",
        default=[],
        help="Glob pattern to exclude (e.g. 'tests/'). May be repeated.",
    )
    return parser


def main(argv: List[str] = None) -> int:
    """Entry point for CLI mode.

    Parameters
    ----------
    argv : list of str, optional
        Argument list (defaults to sys.argv[1:]).

    Returns
    -------
    int
        Exit code: 0 = clean, 1 = violations, 2 = error.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        all_files = _collect_py_files(args.paths)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # Apply exclusion patterns
    exclude_patterns = args.exclude
    if exclude_patterns:
        filtered = []
        for f in all_files:
            excluded = False
            for pattern in exclude_patterns:
                if pathlib.PurePosixPath(f.as_posix()).match(pattern):
                    excluded = True
                    break
                # Also check if 'pattern' appears as a path segment
                if pattern.rstrip("/") in [part for part in f.parts]:
                    excluded = True
                    break
            if not excluded:
                filtered.append(f)
        all_files = filtered

    if not all_files:
        print("No .py files found to check.")
        return 0

    all_violations: List[Violation] = []
    for f in all_files:
        violations = check_file(f)
        all_violations.extend(violations)

    if not all_violations:
        print(f"NONE -- {len(all_files)} file(s) checked, 0 violations")
        return 0

    print(f"VIOLATIONS -- {len(all_violations)} violation(s) in {len(all_files)} file(s) checked:")
    for v in all_violations:
        print(f"  {v.file}:{v.line}: {v.reason}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
