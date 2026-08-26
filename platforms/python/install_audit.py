"""
Install-layer drift auditor for the advanced-planning framework.

Compares three surfaces for the command, agent, and schema files:

  Source layer     -- the canonical source tree (this repository)
  Project layer    -- a target project's .claude/ install dir
  Global layer     -- the developer's machine-global ~/.claude/ install dir

Source directories compared (source_rel -> installed_name):
  platforms/claude-code/commands/  ->  commands/
  platforms/claude-code/agents/    ->  agents/
  core/agents/                     ->  agents/
  core/schemas/                    ->  schemas/

Two source dirs install into agents/. They are audited separately so a report
names the source a file came from, but 'extra' is computed against the union of
everything installing into a directory -- otherwise each surface denounces the
other's files as extras, and core/agents/ drift is never seen at all.

Per-file verdicts:
  current  -- file present in both layers, content hash matches (EOL-insensitive)
  stale    -- file present in both layers, content hash differs
  missing  -- file present in source but absent in the installed layer
  extra    -- file present in the installed layer but absent in source
              (informational only; NOT a failure — projects may have custom files)

Exit codes:
  0  -- all compared files are current
  1  -- at least one stale or missing file found
  2  -- usage / argument error

Global dir resolution (USERPROFILE-first):
  On Windows, HOME may resolve to a network drive while the harness uses
  USERPROFILE. To avoid the trap that bit the Codex auth preflight in
  Phase 14, global home is resolved in this order:
    1. os.environ['USERPROFILE']   (Windows primary)
    2. os.environ['HOME']          (POSIX / fallback)
    3. pathlib.Path.home()         (stdlib last resort)

CLI:
  python -m platforms.python.install_audit [--root ROOT]
                                           [--layers LAYER_PAIR]

  --layers accepts a comma-separated pair from:
    source,project    compare source against the project layer only
    source,global     compare source against the global layer only
    all               compare both pairs (default)

  Missing global dir is skipped with a note (not a failure).

FALSE-POSITIVE TRAP -- READ BEFORE MODIFYING:
  This module READS the global ~/.claude/ directory; it must NEVER WRITE
  outside the repository.  All drift-correction writes happen in the
  /sync-install command, not here.
"""

import argparse
import hashlib
import os
import pathlib
import sys
from typing import Dict, List, NamedTuple, Optional


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class FileVerdict(NamedTuple):
    """Verdict for a single file comparison between two layers."""

    surface: str           # e.g. "commands", "agents", "schemas"
    filename: str          # relative filename within the surface dir
    verdict: str           # "current", "stale", "diverged", "missing", "extra"
    source_hash: Optional[str]    # None when source file is absent (extra)
    installed_hash: Optional[str] # None when installed file is absent (missing)


class LayerPairResult(NamedTuple):
    """Audit result for one source->installed layer pair."""

    pair_label: str           # e.g. "source -> project"
    installed_dir: pathlib.Path
    verdicts: List[FileVerdict]


# ---------------------------------------------------------------------------
# Home resolution (USERPROFILE-first)
# ---------------------------------------------------------------------------

def resolve_global_home(env: Optional[Dict[str, str]] = None) -> pathlib.Path:
    """Resolve the global home directory, preferring USERPROFILE over HOME.

    On Windows, USERPROFILE points to the local user profile
    (C:\\Users\\<name>), while HOME may point to a network drive.  Prefer
    USERPROFILE to avoid network-drive latency or unavailability (the same
    trap that caused the Codex auth preflight failure in Phase 14).

    Parameters
    ----------
    env : dict, optional
        Environment mapping to consult. Defaults to ``os.environ``.  Pass
        a custom dict in tests to monkeypatch without touching the real env.

    Returns
    -------
    pathlib.Path
        Resolved home directory.
    """
    if env is None:
        env = os.environ  # type: ignore[assignment]

    for key in ("USERPROFILE", "HOME"):
        val = env.get(key)
        if val:
            return pathlib.Path(val)
    return pathlib.Path.home()


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def _file_hash(path: pathlib.Path) -> str:
    """Return a SHA-256 hex digest of *path* with EOL-normalised content.

    Line endings ``\\r\\n`` and bare ``\\r`` are normalised to ``\\n`` before
    hashing so that autocrlf-converted copies hash identically to LF copies.

    Parameters
    ----------
    path : pathlib.Path
        File to hash.  Read as UTF-8 with ``errors='replace'``.

    Returns
    -------
    str
        40-character hex digest (SHA-256, first 40 chars for readability).
    """
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        # Unreadable -- treat as empty for hashing purposes
        raw = ""
    normalised = raw.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:40]


# ---------------------------------------------------------------------------
# Surface definitions
# ---------------------------------------------------------------------------

#: (source_rel_dir, installed_subdir_name) pairs defining what to compare.
SURFACES = [
    ("platforms/claude-code/commands", "commands"),
    ("platforms/claude-code/agents",   "agents"),
    ("core/agents",                     "agents"),
    ("core/schemas",                    "schemas"),
]

#: Slack allowed between mtimes before source counts as strictly newer. A copy
#: preserves neither mtime exactly across filesystems, so an exact comparison
#: would flip verdicts on rounding alone.
MTIME_TOLERANCE_SECONDS = 2.0


def _direction(source: pathlib.Path, installed: pathlib.Path) -> str:
    """Return "stale" or "diverged" for two files already known to differ.

    Source strictly newer than the installed copy (beyond the tolerance) means
    the copy is behind and refreshing it is safe: "stale". Anything else --
    installed newer, or a tie, or an unreadable mtime -- means the installed
    copy may hold work source has never seen, and the answer is "diverged".
    """
    try:
        src_mtime = source.stat().st_mtime
        inst_mtime = installed.stat().st_mtime
    except OSError:
        return "diverged"
    if src_mtime > inst_mtime + MTIME_TOLERANCE_SECONDS:
        return "stale"
    return "diverged"


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def find_repo_root(start: pathlib.Path = None) -> pathlib.Path:
    """Locate the repository root by walking up to find core/constraints.json.

    Parameters
    ----------
    start : pathlib.Path, optional
        Starting directory. Defaults to this file's directory.

    Returns
    -------
    pathlib.Path
        Absolute path to the repository root.

    Raises
    ------
    FileNotFoundError
        If the repository root cannot be found.
    """
    candidate = (start or pathlib.Path(__file__)).resolve()
    for parent in [candidate, *candidate.parents]:
        if (parent / "core" / "constraints.json").exists():
            return parent
    raise FileNotFoundError(
        "Repository root not found (looked for core/constraints.json). "
        "Run from within the advanced-planning repository."
    )


def audit_pair(
    repo_root: pathlib.Path,
    installed_base: pathlib.Path,
    pair_label: str,
) -> LayerPairResult:
    """Audit all surfaces between the source layer and one installed layer.

    Parameters
    ----------
    repo_root : pathlib.Path
        Absolute path to the repository root (source layer anchor).
    installed_base : pathlib.Path
        Absolute path to the installed ``.claude/`` base dir
        (e.g. ``/home/user/.claude`` or ``project/.claude``).
    pair_label : str
        Human-readable label for the pair (used in report output).

    Returns
    -------
    LayerPairResult
        Verdicts for every file in every surface.
    """
    verdicts: List[FileVerdict] = []

    # Every name any surface contributes to a given installed dir. More than one
    # source dir may install into the same place, so an "extra" is what is
    # installed there and claimed by none of them -- not merely by this surface.
    claimed: Dict[str, set] = {}

    for source_rel, installed_name in SURFACES:
        source_dir = repo_root / source_rel
        installed_dir = installed_base / installed_name

        if not source_dir.exists():
            # Source surface missing — skip (unusual, but defensive)
            continue

        source_files: Dict[str, pathlib.Path] = {}
        for f in sorted(source_dir.rglob("*")):
            if f.is_file():
                rel = f.relative_to(source_dir).as_posix()
                source_files[rel] = f

        claimed.setdefault(installed_name, set()).update(source_files)

        for name in sorted(source_files):
            installed_file = installed_dir / name
            sh = _file_hash(source_files[name])
            if installed_file.is_file():
                ih = _file_hash(installed_file)
                if sh == ih:
                    v = "current"
                else:
                    v = _direction(source_files[name], installed_file)
            else:
                ih = None
                v = "missing"

            verdicts.append(
                FileVerdict(
                    surface=installed_name,
                    filename=name,
                    verdict=v,
                    source_hash=sh,
                    installed_hash=ih,
                )
            )

    # Second pass: extras, against the union of names claimed per installed dir.
    for installed_name, source_names in sorted(claimed.items()):
        installed_dir = installed_base / installed_name
        if not installed_dir.exists():
            continue
        for f in sorted(installed_dir.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(installed_dir).as_posix()
            if rel in source_names:
                continue
            verdicts.append(
                FileVerdict(
                    surface=installed_name,
                    filename=rel,
                    verdict="extra",
                    source_hash=None,
                    installed_hash=_file_hash(f),
                )
            )

    return LayerPairResult(
        pair_label=pair_label,
        installed_dir=installed_base,
        verdicts=verdicts,
    )


def has_drift(result: LayerPairResult) -> bool:
    """Return True if *result* contains any stale, diverged, or missing files.

    Parameters
    ----------
    result : LayerPairResult

    Returns
    -------
    bool
    """
    return any(
        v.verdict in ("stale", "diverged", "missing") for v in result.verdicts
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _print_result(result: LayerPairResult, verbose: bool = False) -> None:
    """Print a human-readable report for a single layer-pair result.

    Parameters
    ----------
    result : LayerPairResult
    verbose : bool
        When True, also print ``current`` and ``extra`` verdicts.
    """
    drift = has_drift(result)
    status_label = "DRIFT DETECTED" if drift else "current"
    print(f"\n=== {result.pair_label} ({result.installed_dir}) [{status_label}] ===")

    # Group by verdict for readability
    by_verdict: Dict[str, List[FileVerdict]] = {}
    for v in result.verdicts:
        by_verdict.setdefault(v.verdict, []).append(v)

    # Always print stale, diverged and missing. DIVERGED is printed under its
    # own name and never under STALE: /sync-install parses STALE and MISSING
    # lines into a copy list, and copying source over a diverged file destroys
    # changes the one-way sync cannot bring back.
    for verdict_name in ("stale", "diverged", "missing"):
        for v in by_verdict.get(verdict_name, []):
            print(f"  {verdict_name.upper():8s}  {v.surface}/{v.filename}")
            if v.source_hash:
                print(f"            source   sha256:{v.source_hash}")
            if v.installed_hash:
                print(f"            installed sha256:{v.installed_hash}")

    if by_verdict.get("diverged"):
        print(
            "  NOTE: DIVERGED files hold changes the source tree has never\n"
            "        seen. /sync-install copies source -> installed only and\n"
            "        cannot recover them. Reconcile by hand before syncing."
        )

    if verbose:
        for verdict_name in ("current", "extra"):
            for v in by_verdict.get(verdict_name, []):
                print(f"  {verdict_name.upper():8s}  {v.surface}/{v.filename}")

    # Summary counts
    counts = {k: len(vs) for k, vs in by_verdict.items()}
    total = sum(counts.values())
    print(
        f"  Summary: {counts.get('current', 0)} current, "
        f"{counts.get('stale', 0)} stale, "
        f"{counts.get('diverged', 0)} diverged, "
        f"{counts.get('missing', 0)} missing, "
        f"{counts.get('extra', 0)} extra  (total: {total})"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_VALID_LAYER_PAIRS = {"source,project", "source,global", "all"}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m platforms.python.install_audit",
        description=(
            "Audit install-layer drift for the advanced-planning framework. "
            "Compares source against project (./.claude/) and/or global "
            "(~/.claude/) installed copies. "
            "Exit 0 = all current; exit 1 = stale or missing files found."
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
        "--layers",
        metavar="PAIR",
        default="all",
        help=(
            "Layer pairs to compare. One of: source,project | source,global | all. "
            "Default: all (both pairs that exist)."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Also print current and extra verdicts (not just stale/missing).",
    )
    return parser


def main(argv: List[str] = None, env: Optional[Dict[str, str]] = None) -> int:
    """Entry point for CLI mode.

    Parameters
    ----------
    argv : list of str, optional
        Argument list (defaults to sys.argv[1:]).
    env : dict, optional
        Environment mapping for home resolution. Defaults to os.environ.
        Exposed as a parameter so tests can monkeypatch without side effects.

    Returns
    -------
    int
        Exit code: 0 = clean, 1 = drift, 2 = error.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.layers not in _VALID_LAYER_PAIRS:
        print(
            f"ERROR: --layers must be one of: {', '.join(sorted(_VALID_LAYER_PAIRS))}",
            file=sys.stderr,
        )
        return 2

    try:
        if args.root:
            repo_root = pathlib.Path(args.root).resolve()
        else:
            repo_root = find_repo_root(pathlib.Path(__file__))
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    results: List[LayerPairResult] = []

    # --- Project layer ---
    if args.layers in ("source,project", "all"):
        project_claude = repo_root / ".claude"
        if project_claude.exists():
            results.append(
                audit_pair(repo_root, project_claude, "source -> project")
            )
        else:
            print(f"NOTE: project .claude/ dir not found at {project_claude} — skipped")

    # --- Global layer ---
    if args.layers in ("source,global", "all"):
        global_home = resolve_global_home(env)
        global_claude = global_home / ".claude"
        if global_claude.exists():
            results.append(
                audit_pair(repo_root, global_claude, "source -> global")
            )
        else:
            print(
                f"NOTE: global .claude/ dir not found at {global_claude} — skipped "
                f"(not a failure)"
            )

    if not results:
        print("NOTE: no layer pairs found to compare — nothing to audit")
        return 0

    any_drift = False
    for result in results:
        _print_result(result, verbose=args.verbose)
        if has_drift(result):
            any_drift = True

    print()
    if any_drift:
        print("RESULT: drift detected — run /sync-install to refresh stale/missing files")
        return 1

    print("RESULT: all layers current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
