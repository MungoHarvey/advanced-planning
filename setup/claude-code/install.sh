#!/bin/sh
# install.sh
#
# Installs the Advanced Planning System into a Claude Code project or globally.
#
# Usage:
#   sh setup/claude-code/install.sh --project /path/to/your/project
#   sh setup/claude-code/install.sh --global
#   sh setup/claude-code/install.sh --dry-run --project /path/to/your/project
#   sh setup/claude-code/install.sh --project /path/to/your/project --symlink
#
# What is installed:
#   --project: copies commands, skills, agents, settings into PROJECT/.claude/
#   --global:  copies commands, skills, agents, and schemas into ~/.claude/
#   --symlink: creates symlinks to core/skills/ instead of copying

set -e

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROJECT_DIR=""
GLOBAL=false
DRY_RUN=false
SYMLINK=false
SELF_INSTALL=false

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
    case "$1" in
        --project)
            PROJECT_DIR="$2"
            shift 2
            ;;
        --project=*)
            PROJECT_DIR="${1#--project=}"
            shift
            ;;
        --global)
            GLOBAL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --symlink)
            SYMLINK=true
            shift
            ;;
        --help|-h)
            echo "Usage:"
            echo "  sh setup/claude-code/install.sh --project /path/to/project"
            echo "  sh setup/claude-code/install.sh --global"
            echo "  sh setup/claude-code/install.sh --dry-run --project /path/to/project"
            echo "  sh setup/claude-code/install.sh --project /path/to/project --symlink"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
say() { echo "[install] $*"; }

do_cp() {
    # do_cp SRC DEST
    if [ "$DRY_RUN" = true ]; then
        echo "  [dry-run] cp -r $1 $2"
    else
        cp -r "$1" "$2"
    fi
}

do_ln() {
    # do_ln SRC DEST (symlink)
    if [ "$DRY_RUN" = true ]; then
        echo "  [dry-run] ln -sf $1 $2"
    else
        ln -sf "$1" "$2"
    fi
}

do_mkdir() {
    if [ "$DRY_RUN" = true ]; then
        echo "  [dry-run] mkdir -p $1"
    else
        mkdir -p "$1"
    fi
}

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------
if [ "$GLOBAL" = false ] && [ -z "$PROJECT_DIR" ]; then
    echo "ERROR: provide --project /path/to/project or --global" >&2
    exit 1
fi

if [ ! -d "$REPO_ROOT/core" ]; then
    echo "ERROR: cannot find core/ in $REPO_ROOT" >&2
    echo "Run this script from the advanced-planning root or check your path." >&2
    exit 1
fi


# ---------------------------------------------------------------------------
# Global runtime record (mechanism B')
# ---------------------------------------------------------------------------
# USERPROFILE before HOME: under Git Bash on Windows $HOME is routinely a
# mapped network drive while the launcher, install_audit and the Codex auth
# preflight all use the local profile. Writing the record to one and reading
# it from the other is the original defect wearing a different hat.
#
# Two forms are needed and they are not interchangeable:
#   ap_home_fs      POSIX, for mkdir/cp in this script
#   ap_home_native  C:/Users/..., for embedding in files Python will read
# Forward slashes in the native form deliberately: they survive sed, JSON and
# Python string literals without a single backslash escape, and Windows Python
# accepts them everywhere.
ap_home_fs() {
    if [ -n "${USERPROFILE:-}" ] && command -v cygpath >/dev/null 2>&1; then
        cygpath -u "$USERPROFILE"
    elif [ -n "${USERPROFILE:-}" ]; then
        printf '%s' "$USERPROFILE"
    else
        printf '%s' "$HOME"
    fi
}

ap_home_native() {
    if [ -n "${USERPROFILE:-}" ] && command -v cygpath >/dev/null 2>&1; then
        cygpath -m "$USERPROFILE"
    elif [ -n "${USERPROFILE:-}" ]; then
        printf '%s' "$USERPROFILE" | tr '\\' '/'
    else
        printf '%s' "$HOME"
    fi
}

# Point a copied command file at an absolute launcher. Only the two executable
# forms are rewritten; prose mentions of .advanced-plans/bin/ap.py describe the
# project install and stay true.
ap_rewrite_call_sites() {
    _f="$1"; _launcher="$2"
    # Only the PATH changes. The quoting and the r'' prefix are already in the
    # source form, so this is a pure substitution of one string for another --
    # which is what lets install_audit normalise it back and report no drift.
    sed -i \
        -e "s#python \"\.advanced-plans/bin/ap\.py\"#python \"$_launcher\"#g" \
        -e "s#runpy\.run_path(r'\.advanced-plans/bin/ap\.py')#runpy.run_path(r'$_launcher')#g" \
        "$_f"
}

ap_write_global_runtime() {
    _home_fs="$(ap_home_fs)"
    _home_native="$(ap_home_native)"
    _ap_dir="$_home_fs/.advanced-plans"
    do_mkdir "$_ap_dir/bin"
    do_cp "$REPO_ROOT/platforms/python/ap_launcher.py" "$_ap_dir/bin/ap.py"
    if [ "$DRY_RUN" != true ]; then
        _src="$REPO_ROOT"
        if command -v cygpath >/dev/null 2>&1; then _src="$(cygpath -m "$REPO_ROOT")"; fi
        _ver="unknown"
        [ -f "$REPO_ROOT/VERSION" ] && _ver="$(tr -d '[:space:]' < "$REPO_ROOT/VERSION")"
        printf '{"schema_version": 1, "source_root": "%s", "version": "%s", "written_by": "setup/claude-code/install.sh --global"}\n' \
            "$_src" "$_ver" > "$_ap_dir/runtime.json"
    fi
    say "  + $_ap_dir/bin/ap.py"
    say "  + $_ap_dir/runtime.json"
}

# ---------------------------------------------------------------------------
# Global install
# ---------------------------------------------------------------------------
if [ "$GLOBAL" = true ]; then
    GLOBAL_DIR="$(ap_home_fs)/.claude"
    AP_LAUNCHER="$(ap_home_native)/.advanced-plans/bin/ap.py"
    say "Installing globally to $GLOBAL_DIR"
    do_mkdir "$GLOBAL_DIR/commands"
    do_mkdir "$GLOBAL_DIR/agents"
    do_mkdir "$GLOBAL_DIR/schemas"

    say "Installing slash commands..."
    for cmd in "$REPO_ROOT/platforms/claude-code/commands/"*.md; do
        [ -f "$cmd" ] || continue
        do_cp "$cmd" "$GLOBAL_DIR/commands/"
        # Globally-installed commands run in projects that were never
        # project-installed, where .advanced-plans/bin/ap.py does not exist and
        # the interpreter dies before the launcher's diagnostic can fire.
        [ "$DRY_RUN" = true ] || ap_rewrite_call_sites \
            "$GLOBAL_DIR/commands/$(basename "$cmd")" "$AP_LAUNCHER"
        say "  + commands/$(basename "$cmd")"
    done

    say "Installing agent definitions..."
    for agent in "$REPO_ROOT/core/agents/"*.md; do
        [ -f "$agent" ] || continue
        do_cp "$agent" "$GLOBAL_DIR/agents/"
        say "  + agents/$(basename "$agent")"
    done

    # Copy platform-specific agent definitions
    for agent in "$REPO_ROOT/platforms/claude-code/agents/"*.md; do
        [ -f "$agent" ] || continue
        do_cp "$agent" "$GLOBAL_DIR/agents/"
        say "  + agents/$(basename "$agent")"
    done

    say "Installing core skills..."
    if [ "$SYMLINK" = true ]; then
        do_ln "$REPO_ROOT/core/skills" "$GLOBAL_DIR/skills"
        say "  + skills/ → $REPO_ROOT/core/skills (symlinked)"
    else
        do_mkdir "$GLOBAL_DIR/skills"
        for skill_dir in "$REPO_ROOT/core/skills/"*/; do
            [ -d "$skill_dir" ] || continue
            skill_name="$(basename "$skill_dir")"
            do_cp "$skill_dir" "$GLOBAL_DIR/skills/"
            say "  + skills/$skill_name/"
        done
    fi

    say "Installing schemas..."
    for schema in "$REPO_ROOT/core/schemas/"*.md "$REPO_ROOT/core/schemas/"*.json; do
        [ -f "$schema" ] || continue
        do_cp "$schema" "$GLOBAL_DIR/schemas/"
        say "  + schemas/$(basename "$schema")"
    done

    say ""
    say "Recording the shared Python runtime globally..."
    ap_write_global_runtime

    say ""
    say "Global install complete."
    exit 0
fi

# ---------------------------------------------------------------------------
# Project install
# ---------------------------------------------------------------------------
CLAUDE_DIR="$PROJECT_DIR/.claude"

# Self-install detection: if --project resolves to the same git toplevel as
# the repo root, use symlinks (junctions on Windows) for runtime dirs so that
# edits to source files are immediately visible without re-running the installer.
PROJECT_REAL="$(cd "$PROJECT_DIR" 2>/dev/null && pwd || echo "$PROJECT_DIR")"
PROJECT_GIT_TOP="$(cd "$PROJECT_DIR" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null || echo "")"
REPO_GIT_TOP="$(cd "$REPO_ROOT" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null || echo "")"
if [ -n "$PROJECT_GIT_TOP" ] && [ -n "$REPO_GIT_TOP" ] && [ "$PROJECT_GIT_TOP" = "$REPO_GIT_TOP" ]; then
    SELF_INSTALL=true
    say "Self-install detected: project is the source repo root"
    say "Runtime dirs will be symlinked so source edits surface immediately"
fi

say "Installing Advanced Planning System"
say "  repo:    $REPO_ROOT"
say "  project: $PROJECT_DIR"
say "  target:  $CLAUDE_DIR"
if [ "$DRY_RUN" = true ]; then
    say "  mode:    DRY RUN (no files written)"
fi
if [ "$SELF_INSTALL" = true ]; then
    say "  mode:    SELF-INSTALL (symlinks for runtime dirs)"
elif [ "$SYMLINK" = true ]; then
    say "  skills:  symlinked"
fi
say ""

# Create target directories
do_mkdir "$CLAUDE_DIR/commands"
do_mkdir "$CLAUDE_DIR/agents"

# ---------------------------------------------------------------------------
# .advanced-plans/ scaffold — idempotent skip if data already exists
# ---------------------------------------------------------------------------
AP_DIR="$PROJECT_DIR/.advanced-plans"
if [ -d "$AP_DIR" ]; then
    say "Preserving existing planning data at $AP_DIR — skipping scaffold"
else
    say "Creating .advanced-plans/ scaffold..."
    do_mkdir "$AP_DIR/phases"
    do_mkdir "$AP_DIR/specs"
    do_mkdir "$AP_DIR/state"
    do_mkdir "$AP_DIR/logs"

    # Idempotent migration: move legacy layouts into .advanced-plans/ if present
    if [ "$DRY_RUN" = false ]; then
        if [ -d "$PROJECT_DIR/plans" ] && [ ! -f "$AP_DIR/PLANS-INDEX.md" ]; then
            say "Migrating legacy plans/ to .advanced-plans/ ..."
            cp -R "$PROJECT_DIR/plans/." "$AP_DIR/" 2>/dev/null || true
        fi
        if [ -d "$CLAUDE_DIR/state" ]; then
            say "Migrating legacy .claude/state/ to .advanced-plans/state/ ..."
            cp -R "$CLAUDE_DIR/state/." "$AP_DIR/state/" 2>/dev/null || true
        fi
        if [ -d "$CLAUDE_DIR/logs" ]; then
            say "Migrating legacy .claude/logs/ to .advanced-plans/logs/ ..."
            cp -R "$CLAUDE_DIR/logs/." "$AP_DIR/logs/" 2>/dev/null || true
        fi
    else
        echo "  [dry-run] migrate plans/ and .claude/state|logs/ to .advanced-plans/ if present"
    fi

    if [ ! -f "$AP_DIR/PLANNING.md" ] && [ "$DRY_RUN" = false ]; then
        cat > "$AP_DIR/PLANNING.md" <<'PLANEOF'
---
programme: ""
status: not_started
last_updated: ""
current_phase: ""
current_loop: ""
gate_status: ""
next_action: "Run /new-phase to create the first phase plan"
active_branches: []
phases:
  complete: []
  pending: []
  failed: []
state_files:
  ready: .advanced-plans/state/loop-ready.json
  complete: .advanced-plans/state/loop-complete.json
  history: .advanced-plans/state/history.jsonl
notes: ""
---

# Planning

This directory holds all planning artefacts. See README.md for the layout.
PLANEOF
    fi
    if [ ! -f "$AP_DIR/README.md" ] && [ "$DRY_RUN" = false ]; then
        cat > "$AP_DIR/README.md" <<'READEOF'
# .advanced-plans/

Platform-agnostic planning data home.

- `PLANNING.md` -- live programme dashboard (YAML frontmatter)
- `PLANS-INDEX.md` -- index of all phases and loops
- `phases/phase-N/` -- `plan.md` + `loops.md` per phase
- `specs/` -- design specs
- `state/` -- filesystem state bus (loop-ready/complete, history.jsonl)
- `logs/` -- execution log
READEOF
    fi
fi

# ---------------------------------------------------------------------------
# Shared Python runtime: launcher + recorded source path
#
# The commands shell out to platforms/python/<module>, which no install ships.
# Rather than copy that tree into every project, record where the checkout is
# and hand the project a launcher that reads the record. See
# platforms/python/ap_launcher.py for why this shape and not the other three.
#
# Deliberately OUTSIDE the scaffold guard above: that guard skips everything
# when .advanced-plans/ already exists, and an upgrade-in-place is exactly the
# case where the recorded path most needs refreshing.
# ---------------------------------------------------------------------------
say "Recording the shared Python runtime..."
do_mkdir "$AP_DIR/bin"
do_cp "$REPO_ROOT/platforms/python/ap_launcher.py" "$AP_DIR/bin/ap.py"
if [ "$DRY_RUN" = false ]; then
    # Under Git Bash / MSYS on Windows, $REPO_ROOT is a POSIX path
    # (/c/Users/...) that the native Python interpreter cannot open. Record
    # a path the interpreter that will read it can actually resolve.
    # cygpath -m gives C:/Users/... - native, and forward slashes so it
    # needs no JSON escaping. Absent off Windows, where $REPO_ROOT is right.
    AP_SOURCE_ROOT="$(cygpath -m "$REPO_ROOT" 2>/dev/null || echo "$REPO_ROOT")"
    AP_VERSION="$(cat "$REPO_ROOT/VERSION" 2>/dev/null || echo unknown)"
    AP_STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo unknown)"
    cat > "$AP_DIR/runtime.json" <<RUNTIMEEOF
{
  "schema_version": 1,
  "source_root": "$AP_SOURCE_ROOT",
  "version": "$AP_VERSION",
  "written_by": "setup/claude-code/install.sh",
  "written_at": "$AP_STAMP"
}
RUNTIMEEOF
    say "  + .advanced-plans/runtime.json -> $AP_SOURCE_ROOT"
    say "  + .advanced-plans/bin/ap.py"
else
    echo "  [dry-run] write $AP_DIR/runtime.json recording $REPO_ROOT"
fi

# ---------------------------------------------------------------------------
# Runtime dirs: self-install uses symlinks; normal install copies
# ---------------------------------------------------------------------------
if [ "$SELF_INSTALL" = true ]; then
    # In the source repo: symlink runtime dirs to their canonical source locations
    say "Installing runtime dirs as symlinks (self-install mode)..."
    if [ "$DRY_RUN" = true ]; then
        echo "  [dry-run] ln -sf $REPO_ROOT/platforms/claude-code/commands $CLAUDE_DIR/commands"
        echo "  [dry-run] ln -sf $REPO_ROOT/core/skills $CLAUDE_DIR/skills"
        echo "  [dry-run] ln -sf $REPO_ROOT/core/agents $CLAUDE_DIR/core-agents (note: agents merged below)"
        echo "  [dry-run] ln -sf $REPO_ROOT/core/schemas $CLAUDE_DIR/schemas"
    else
        # Remove existing dirs/links before creating symlinks
        rm -rf "$CLAUDE_DIR/commands" "$CLAUDE_DIR/skills" "$CLAUDE_DIR/schemas"
        ln -sf "$REPO_ROOT/platforms/claude-code/commands" "$CLAUDE_DIR/commands"
        say "  + commands -> platforms/claude-code/commands"
        ln -sf "$REPO_ROOT/core/skills" "$CLAUDE_DIR/skills"
        say "  + skills -> core/skills"
        ln -sf "$REPO_ROOT/core/schemas" "$CLAUDE_DIR/schemas"
        say "  + schemas -> core/schemas"
        # Agents: symlink core/agents; copy platform-specific ones alongside
        rm -rf "$CLAUDE_DIR/agents"
        mkdir -p "$CLAUDE_DIR/agents"
        for agent in "$REPO_ROOT/core/agents/"*.md; do
            [ -f "$agent" ] || continue
            ln -sf "$agent" "$CLAUDE_DIR/agents/$(basename "$agent")"
            say "  + agents/$(basename "$agent") -> core/agents"
        done
        for agent in "$REPO_ROOT/platforms/claude-code/agents/"*.md; do
            [ -f "$agent" ] || continue
            ln -sf "$agent" "$CLAUDE_DIR/agents/$(basename "$agent")"
            say "  + agents/$(basename "$agent") -> platforms/claude-code/agents"
        done
    fi
else
    # Normal install: copy slash commands
    say "Installing slash commands..."
    for cmd in "$REPO_ROOT/platforms/claude-code/commands/"*.md; do
        [ -f "$cmd" ] || continue
        do_cp "$cmd" "$CLAUDE_DIR/commands/"
        say "  + commands/$(basename "$cmd")"
    done

    # Copy agent definitions
    say "Installing agent definitions..."
    for agent in "$REPO_ROOT/core/agents/"*.md; do
        [ -f "$agent" ] || continue
        do_cp "$agent" "$CLAUDE_DIR/agents/"
        say "  + agents/$(basename "$agent")"
    done

    # Copy platform-specific agent definitions
    for agent in "$REPO_ROOT/platforms/claude-code/agents/"*.md; do
        [ -f "$agent" ] || continue
        do_cp "$agent" "$CLAUDE_DIR/agents/"
        say "  + agents/$(basename "$agent")"
    done

    # Install skills (copy or symlink)
    # All subdirectories of core/skills/ are included automatically.
    # Current skills: companion-detection, phase-plan-creator, plan-skill-identification,
    #   plan-subagent-identification, plan-todos, ralph-loop-planner, progress-report,
    #   schema-design, permission-config
    say "Installing core skills..."
    if [ "$SYMLINK" = true ]; then
        do_ln "$REPO_ROOT/core/skills" "$CLAUDE_DIR/skills"
        say "  + skills/ -> $REPO_ROOT/core/skills (symlinked)"
    else
        do_mkdir "$CLAUDE_DIR/skills"
        for skill_dir in "$REPO_ROOT/core/skills/"*/; do
            [ -d "$skill_dir" ] || continue
            skill_name="$(basename "$skill_dir")"
            do_cp "$skill_dir" "$CLAUDE_DIR/skills/"
            say "  + skills/$skill_name/"
        done
    fi

    # Copy schemas
    say "Installing schemas..."
    do_mkdir "$CLAUDE_DIR/schemas"
    for schema in "$REPO_ROOT/core/schemas/"*.md "$REPO_ROOT/core/schemas/"*.json; do
        [ -f "$schema" ] || continue
        do_cp "$schema" "$CLAUDE_DIR/schemas/"
        say "  + schemas/$(basename "$schema")"
    done
fi

# Write settings.json
SETTINGS="$CLAUDE_DIR/settings.json"
say "Writing settings.json..."
if [ "$DRY_RUN" = false ]; then
    cat > "$SETTINGS" <<EOF
{
  "permissions": {
    "allow": [
      "Read(.advanced-plans/**)",
      "Write(.advanced-plans/**)",
      "Edit(.advanced-plans/**)",
      "MultiEdit(.advanced-plans/**)"
    ]
  },
  "planning": {
    "state_dir": ".advanced-plans/state",
    "skills_dir": ".claude/skills",
    "agents_dir": ".claude/agents",
    "plans_dir": ".advanced-plans"
  }
}
EOF
else
    echo "  [dry-run] write $SETTINGS"
fi

say ""
say "Installation complete."
say ""
say "Next steps:"
say "  1. cd $PROJECT_DIR"
say "  2. claude"
say "  3. /new-phase        ← create your first phase plan"
say "  4. /decompose-phase  ← decompose phase into loops"
say "  5. /next-loop        ← run the first loop"
say ""
say "See setup/claude-code/README.md for full documentation."
