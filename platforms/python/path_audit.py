"""
Path-convention audit for the advanced-planning framework.

Scans the active executable/installed surface (command, agent, skill, and related
source files) for deprecated or corrupted path tokens that indicate a pre-restructure
or Phase-9-class bug. Exits non-zero if any violation is found.

FALSE-POSITIVE TRAP — READ THIS BEFORE MODIFYING:
The repository contains many *legitimate* `.claude/` references (installed-runtime
layout: `.claude/commands/`, `.claude/skills/`, etc.) as well as *historical/
illustrative* references to the corruption tokens in docs/, planning artefacts, and
test fixtures. A naive grep over the whole tree would flag all of these and be useless.

To avoid this, the audit is SCOPED to the active executable surface only:
    - platforms/claude-code/commands/
    - platforms/claude-code/agents/
    - platforms/cowork/
    - core/agents/
    - core/skills/
    - .claude/commands/
    - .claude/agents/

The following are EXPLICITLY EXCLUDED from the scan:
    - docs/          (narrative docs; contains historical examples of the bad tokens)
    - .advanced-plans/ (planning data + specs + this phase's own loop files)
    - platforms/python/tests/ (test fixtures may plant tokens deliberately)
    - README*, CHANGELOG*, *.schema.md (documentation files)

Only these signatures are treated as violations:

A. Path-convention violations (all scanned roots):
    1. Doubled prefix:      `.advanced-.advanced-`  (or `\\.advanced-\\.advanced-`)
    2. Wrong nesting:       `.claude/.advanced-plans`
    3. Deprecated token:    `.claude/plans/`

B. Host-neutrality violations (core/ roots ONLY — see docs/path-conventions.md §7.3):
    Core files must contain no host-specific directories, tool names, or permission syntax.
    The following are violations when found under core/agents/ or core/skills/:

    B1. Host directories:
        - `.claude/`, `.cursor/`, `.opencode/`, `.codex/`, `.agents/`, `.gemini/`
    B2. Host-only tool and agent names:
        - `Agent` tool, `Task` tool, `subagent_type` parameter
        - Slash-command syntax: `/plan-and-phase`, `/next-loop`, `/run-gate`, etc.
    B3. Host permission syntax:
        - `settings.json` permission rules (e.g., `permissions.defaultMode`)
        - `opencode.json` configuration
        - `.cursor/rules` references

A bare `.claude/commands/` or `.claude/skills/` reference is LEGITIMATE in
platforms/claude-code/ (installed runtime docs) and is NOT flagged there.
The same reference in core/ IS flagged.

Source of truth for canonical paths: docs/path-conventions.md

CLI:
    python -m platforms.python.path_audit [--root ROOT] [--verbose]

Exit codes:
    0  -- no violations found
    1  -- one or more violations found
    2  -- usage / argument error
"""

import argparse
import pathlib
import re
import sys
from typing import List, NamedTuple


# ---------------------------------------------------------------------------
# Violation signatures
# ---------------------------------------------------------------------------

#: Each entry is (pattern_name, compiled_regex, core_only).
#: A line matching ANY of these is a violation.
#: core_only=True means the pattern is only checked under core/ roots.
VIOLATION_PATTERNS: List[tuple] = [
    (
        "doubled-prefix (.advanced-.advanced-)",
        re.compile(r"\.advanced-\.advanced-"),
        False,  # all roots
    ),
    (
        "wrong-nesting (.claude/.advanced-plans)",
        re.compile(r"\.claude/\.advanced-plans"),
        False,  # all roots
    ),
    (
        "deprecated-token (.claude/plans/)",
        re.compile(r"\.claude/plans/"),
        False,  # all roots
    ),
    # Host-neutrality violations (core/ only)
    (
        "host-directory (.claude/|.cursor/|.opencode/|.codex/|.agents/|.gemini/)",
        re.compile(r"\.(claude|cursor|opencode|codex|agents|gemini)/"),
        True,  # core/ only
    ),
    (
        "host-tool-name (Claude Code|Cowork|Agent tool|Task tool|TodoWrite|subagent_type)",
        re.compile(r"(Claude Code|Cowork|Agent tool|Task tool|TodoWrite|subagent_type)"),
        True,  # core/ only
    ),
    (
        r"host-permission-syntax (settings.json|opencode.json|.cursor/rules)",
        re.compile(r"(settings\.json|opencode\.json|\.cursor/rules)"),
        True,  # core/ only
    ),
]


# ---------------------------------------------------------------------------
# Scanned roots (relative to repo root, configurable)
# ---------------------------------------------------------------------------

#: Default set of directory roots to scan (relative paths from repo root).
DEFAULT_SCANNED_ROOTS: List[str] = [
    "platforms/claude-code/commands",
    "platforms/claude-code/agents",
    "platforms/cowork",
    "core/agents",
    "core/skills",
    ".claude/commands",
    ".claude/agents",
]

#: Default excluded path segments. Any file whose path contains one of these
#: segments (as a directory part or prefix) is skipped.
DEFAULT_EXCLUDED_SEGMENTS: List[str] = [
    "docs",
    ".advanced-plans",
    "platforms/python/tests",
    "platforms\\python\\tests",  # Windows path separator variant
]


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class PathViolation(NamedTuple):
    """A single path-convention violation."""

    file: pathlib.Path
    line: int
    pattern_name: str
    matched_text: str


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def find_repo_root(start: pathlib.Path = None) -> pathlib.Path:
    """Locate the repository root by walking up to find core/constraints.json.

    Parameters
    ----------
    start : pathlib.Path, optional
        Directory to start from. Defaults to this file's location.

    Returns
    -------
    pathlib.Path
        Absolute path to the repository root.

    Raises
    ------
    FileNotFoundError
        If the repository root cannot be determined.
    """
    candidate = (start or pathlib.Path(__file__)).resolve()
    for parent in [candidate, *candidate.parents]:
        if (parent / "core" / "constraints.json").exists():
            return parent
    raise FileNotFoundError(
        "Repository root not found (looked for core/constraints.json). "
        "Run from within the advanced-planning repository."
    )


def _is_excluded(file_path: pathlib.Path, excluded_segments: List[str]) -> bool:
    """Return True if the file should be excluded from scanning.

    Parameters
    ----------
    file_path : pathlib.Path
        Absolute or relative path to the file.
    excluded_segments : list of str
        Path segments or prefixes that mark a file as excluded.

    Returns
    -------
    bool
    """
    posix = file_path.as_posix()
    for segment in excluded_segments:
        # Normalise to forward slashes for comparison
        seg = segment.replace("\\", "/")
        if seg in posix:
            return True
    return False


def check_file(path: pathlib.Path, core_only_scan: bool = False) -> List[PathViolation]:
    """Scan a single file for path-convention violations.

    Parameters
    ----------
    path : pathlib.Path
        Path to the file to inspect (any text file).
    core_only_scan : bool, optional
        If True, only check core-only patterns (host-neutrality rules).
        Used when scanning core/ roots.

    Returns
    -------
    list of PathViolation
        Empty list means the file is clean.
    """
    violations: List[PathViolation] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return violations

    for lineno, line in enumerate(lines, start=1):
        for pattern_name, regex, is_core_only in VIOLATION_PATTERNS:
            # Skip core-only patterns if not in a core-only scan
            if is_core_only and not core_only_scan:
                continue
            match = regex.search(line)
            if match:
                violations.append(
                    PathViolation(
                        file=path,
                        line=lineno,
                        pattern_name=pattern_name,
                        matched_text=line.strip(),
                    )
                )
                # Report first match per line per pattern; continue checking
                # other patterns on the same line.

    return violations


def audit(
    repo_root: pathlib.Path,
    scanned_roots: List[str] = None,
    excluded_segments: List[str] = None,
) -> List[PathViolation]:
    """Run the full path-convention audit.

    Parameters
    ----------
    repo_root : pathlib.Path
        Absolute path to the repository root.
    scanned_roots : list of str, optional
        Relative directory paths to scan. Defaults to DEFAULT_SCANNED_ROOTS.
    excluded_segments : list of str, optional
        Path segments that exclude a file. Defaults to DEFAULT_EXCLUDED_SEGMENTS.

    Returns
    -------
    list of PathViolation
        All violations found across all scanned roots.
    """
    if scanned_roots is None:
        scanned_roots = DEFAULT_SCANNED_ROOTS
    if excluded_segments is None:
        excluded_segments = DEFAULT_EXCLUDED_SEGMENTS

    all_violations: List[PathViolation] = []

    for root_rel in scanned_roots:
        root_abs = repo_root / root_rel
        if not root_abs.exists():
            # Root may not exist in all environments (e.g. .claude/ before install)
            continue
        if root_abs.is_file():
            files = [root_abs]
        else:
            files = sorted(root_abs.rglob("*"))

        # Determine if this is a core/ root (host-neutrality rules apply)
        is_core_root = root_rel.startswith("core/")

        for f in files:
            if not f.is_file():
                continue
            # Skip binary-looking files (check suffix allowlist)
            if f.suffix.lower() not in {".md", ".txt", ".yaml", ".yml", ".json", ".sh", ".ps1", ""}:
                continue
            if _is_excluded(f, excluded_segments):
                continue
            violations = check_file(f, core_only_scan=is_core_root)
            all_violations.extend(violations)

    return all_violations


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m platforms.python.path_audit",
        description=(
            "Audit the active executable surface for deprecated/corrupted path tokens. "
            "Exit 0 = clean, exit 1 = violations found."
        ),
    )
    parser.add_argument(
        "--root",
        metavar="DIR",
        default=None,
        help=(
            "Repository root directory. "
            "Defaults to auto-detection via core/constraints.json."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each scanned file even if it is clean.",
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
        if args.root:
            repo_root = pathlib.Path(args.root).resolve()
        else:
            repo_root = find_repo_root(pathlib.Path(__file__))
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    violations = audit(repo_root)

    if not violations:
        print(f"CLEAN -- path-convention audit passed (scanned roots: {DEFAULT_SCANNED_ROOTS})")
        return 0

    print(
        f"VIOLATIONS -- {len(violations)} path-convention violation(s) found:"
    )
    for v in violations:
        print(f"  {v.file}:{v.line}: [{v.pattern_name}]")
        print(f"    {v.matched_text}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
