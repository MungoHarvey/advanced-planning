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
#   --global:  copies commands only into ~/.claude/commands/
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
# Global install (commands only)
# ---------------------------------------------------------------------------
if [ "$GLOBAL" = true ]; then
    GLOBAL_DIR="$HOME/.claude"
    say "Installing slash commands globally to $GLOBAL_DIR/commands/"
    do_mkdir "$GLOBAL_DIR/commands"
    for cmd in "$REPO_ROOT/platforms/claude-code/commands/"*.md; do
        [ -f "$cmd" ] || continue
        do_cp "$cmd" "$GLOBAL_DIR/commands/"
        say "  + commands/$(basename "$cmd")"
    done
    say ""
    say "Global install complete."
    say "Skills are NOT installed globally — run --project per project for skill injection."
    exit 0
fi

# ---------------------------------------------------------------------------
# Project install
# ---------------------------------------------------------------------------
CLAUDE_DIR="$PROJECT_DIR/.claude"

say "Installing Advanced Planning System"
say "  repo:    $REPO_ROOT"
say "  project: $PROJECT_DIR"
say "  target:  $CLAUDE_DIR"
if [ "$DRY_RUN" = true ]; then
    say "  mode:    DRY RUN (no files written)"
fi
if [ "$SYMLINK" = true ]; then
    say "  skills:  symlinked"
fi
say ""

# Create target directories
do_mkdir "$CLAUDE_DIR/commands"
do_mkdir "$CLAUDE_DIR/agents"
do_mkdir "$CLAUDE_DIR/state"

# Copy slash commands
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

# Install skills (copy or symlink)
say "Installing core skills..."
if [ "$SYMLINK" = true ]; then
    do_ln "$REPO_ROOT/core/skills" "$CLAUDE_DIR/skills"
    say "  + skills/ → $REPO_ROOT/core/skills (symlinked)"
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

# Write settings.json
SETTINGS="$CLAUDE_DIR/settings.json"
say "Writing settings.json..."
if [ "$DRY_RUN" = false ]; then
    cat > "$SETTINGS" <<EOF
{
  "planning": {
    "state_dir": ".claude/state",
    "skills_dir": ".claude/skills",
    "agents_dir": ".claude/agents",
    "plans_dir": "plans"
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
say "  3. /new-phase   ← create your first phase plan"
say "  4. /new-loop    ← decompose phase into loops"
say "  5. /next-loop   ← run the first loop"
say ""
say "See setup/claude-code/README.md for full documentation."
