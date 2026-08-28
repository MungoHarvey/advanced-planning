#!/bin/sh
# install.sh — Advanced Planning System v8 Claude Code Adapter
# Installs the planning system into a Claude Code project or globally.
#
# Usage:
#   ./install.sh --project [path]   Install into a specific project directory
#   ./install.sh --project .        Install into the current directory
#   ./install.sh --global           Install commands globally (~/.claude/commands/)
#   ./install.sh --reference        Print paths for @-reference usage (no file copy)
#   ./install.sh --help             Show this help text
#
# Modes:
#   --project   Copies core skills and adapter files into [path]/.claude/
#               Recommended for teams using the system on a specific project.
#
#   --global    Copies slash commands to ~/.claude/commands/ for system-wide availability.
#               Skills are not copied — they are referenced via SKILL_PATH below.
#               Run from the advanced-planning root directory.
#
#   --reference Prints the paths you need to reference skills and agents via @ syntax.
#               No files are copied. Use when you want to load skills manually.

set -e

# Determine script location (the advanced-planning root)
SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
ADAPTER_DIR="$SCRIPT_DIR/platforms/claude-code"
CORE_DIR="$SCRIPT_DIR/core"

print_help() {
    sed -n '/^# Usage:/,/^[^#]/p' "$0" | grep "^#" | sed 's/^# //'
}

print_reference() {
    echo ""
    echo "Advanced Planning System v8 — Reference Paths"
    echo "──────────────────────────────────────────────"
    echo ""
    echo "Skills directory:"
    echo "  $CORE_DIR/skills/"
    echo ""
    echo "To load a skill manually:"
    echo "  Read $CORE_DIR/skills/phase-plan-creator/SKILL.md"
    echo "  Read $CORE_DIR/skills/ralph-loop-planner/SKILL.md"
    echo "  Read $CORE_DIR/skills/plan-todos/SKILL.md"
    echo "  Read $CORE_DIR/skills/plan-skill-identification/SKILL.md"
    echo "  Read $CORE_DIR/skills/plan-subagent-identification/SKILL.md"
    echo "  Read $CORE_DIR/skills/progress-report/SKILL.md"
    echo ""
    echo "Agent definitions:"
    echo "  $ADAPTER_DIR/agents/ralph-orchestrator.md"
    echo "  $ADAPTER_DIR/agents/ralph-loop-worker.md"
    echo "  $ADAPTER_DIR/agents/analysis-worker.md"
    echo ""
    echo "CLAUDE.md template:"
    echo "  $ADAPTER_DIR/claude-md-template.md"
    echo ""
}

install_project() {
    TARGET="$1"

    if [ -z "$TARGET" ]; then
        echo "Error: --project requires a directory path" >&2
        echo "Usage: ./install.sh --project /path/to/project" >&2
        exit 1
    fi

    if [ ! -d "$TARGET" ]; then
        echo "Error: directory not found: $TARGET" >&2
        exit 1
    fi

    CLAUDE_DIR="$TARGET/.claude"

    echo ""
    echo "Installing Advanced Planning System v8 into $CLAUDE_DIR"
    echo "──────────────────────────────────────────────────────"

    # Create .claude directory structure
    mkdir -p "$CLAUDE_DIR/commands"
    mkdir -p "$CLAUDE_DIR/agents"
    mkdir -p "$CLAUDE_DIR/skills"
    mkdir -p "$CLAUDE_DIR/state"
    mkdir -p "$CLAUDE_DIR/plans"
    mkdir -p "$CLAUDE_DIR/logs"

    # Copy slash commands
    echo "  → Copying slash commands..."
    cp "$ADAPTER_DIR/commands/"*.md "$CLAUDE_DIR/commands/"

    # Copy or symlink core skills
    echo "  → Installing core skills..."
    for skill_dir in "$CORE_DIR/skills"/*/; do
        skill_name="$(basename "$skill_dir")"
        # Try symlink first; fall back to copy if symlinks not supported
        if ln -sf "$skill_dir" "$CLAUDE_DIR/skills/$skill_name" 2>/dev/null; then
            echo "    ✓ Symlinked $skill_name"
        else
            cp -r "$skill_dir" "$CLAUDE_DIR/skills/$skill_name"
            echo "    ✓ Copied $skill_name"
        fi
    done

    # Copy agent files
    echo "  → Copying agent definitions..."
    cp "$ADAPTER_DIR/agents/"*.md "$CLAUDE_DIR/agents/"

    # Copy settings.json (warn if one already exists)
    if [ -f "$CLAUDE_DIR/settings.json" ]; then
        echo "  ⚠ settings.json already exists — saving adapter version as settings.planning.json"
        cp "$ADAPTER_DIR/settings.json" "$CLAUDE_DIR/settings.planning.json"
        echo "    Merge the hooks from settings.planning.json into your existing settings.json"
    else
        cp "$ADAPTER_DIR/settings.json" "$CLAUDE_DIR/settings.json"
        echo "  → settings.json installed"
    fi

    # The shared Python runtime. Without this the commands copied just above
    # invoke .advanced-plans/bin/ap.py in a project that has no such file, and
    # die with the interpreter's own "can't open file" - which is the whole
    # defect this mechanism exists to close, still fully intact in this branch
    # of this installer until now. The setup/ installers have carried it since
    # 54a0a73; this one only ever got it on the --global path.
    #
    # Written unconditionally, and after everything above: an upgrade in place
    # is exactly when a stale source_root most needs refreshing, and nothing
    # here may skip it.
    echo "  → Recording the shared Python runtime..."
    _ap_dir="$TARGET/.advanced-plans"
    mkdir -p "$_ap_dir/bin"
    cp "$SCRIPT_DIR/platforms/python/ap_launcher.py" "$_ap_dir/bin/ap.py"
    _src="$SCRIPT_DIR"
    if command -v cygpath >/dev/null 2>&1; then _src="$(cygpath -m "$SCRIPT_DIR")"; fi
    _ver="unknown"
    [ -f "$SCRIPT_DIR/VERSION" ] && _ver="$(tr -d '[:space:]' < "$SCRIPT_DIR/VERSION")"
    printf '{"schema_version": 1, "source_root": "%s", "version": "%s", "written_by": "platforms/claude-code/install.sh --project"}\n' \
        "$_src" "$_ver" > "$_ap_dir/runtime.json"

    echo ""
    echo "✓ Installation complete"
    echo ""
    echo "Next steps:"
    echo "  1. Add the Planning State section to your CLAUDE.md:"
    echo "     cat $ADAPTER_DIR/claude-md-template.md"
    echo "  2. Open a Claude Code session in $TARGET"
    echo "  3. Run /plan-and-phase [description] to explore and plan, or /new-phase to jump straight to phase planning"
    echo "  4. Run /next-loop to begin execution (or /next-loop --auto to chain all loops)"
    echo ""
}

# USERPROFILE before HOME: Git Bash $HOME is routinely a mapped network drive
# on Windows while the launcher and install_audit use the local profile.
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

install_global() {
    GLOBAL_DIR="$(ap_home_fs)/.claude"
    COMMANDS_DIR="$GLOBAL_DIR/commands"
    AP_GLOBAL_DIR="$(ap_home_fs)/.advanced-plans"
    AP_LAUNCHER="$(ap_home_native)/.advanced-plans/bin/ap.py"

    echo ""
    echo "Installing Advanced Planning System v8 commands globally to $COMMANDS_DIR"
    echo "────────────────────────────────────────────────────────────────────────"

    mkdir -p "$COMMANDS_DIR"

    # Copy slash commands
    echo "  → Copying slash commands..."
    cp "$ADAPTER_DIR/commands/"*.md "$COMMANDS_DIR/"

    # The shared Python runtime. Without this, every copied command shells out
    # to .advanced-plans/bin/ap.py in projects this installer never touches,
    # and dies with the interpreter's own "can't open file" - naming neither
    # the product nor the repair. This installer shipped commands without their
    # launcher for its whole life; found by a cross-vendor review panel.
    echo "  → Recording the shared Python runtime globally..."
    mkdir -p "$AP_GLOBAL_DIR/bin"
    cp "$SCRIPT_DIR/platforms/python/ap_launcher.py" "$AP_GLOBAL_DIR/bin/ap.py"
    _src="$SCRIPT_DIR"
    if command -v cygpath >/dev/null 2>&1; then _src="$(cygpath -m "$SCRIPT_DIR")"; fi
    _ver="unknown"
    [ -f "$SCRIPT_DIR/VERSION" ] && _ver="$(tr -d '[:space:]' < "$SCRIPT_DIR/VERSION")"
    printf '{"schema_version": 1, "source_root": "%s", "version": "%s", "written_by": "platforms/claude-code/install.sh --global"}\n' \
        "$_src" "$_ver" > "$AP_GLOBAL_DIR/runtime.json"

    for _f in "$COMMANDS_DIR"/*.md; do
        [ -f "$_f" ] || continue
        # Only the PATH changes; the quoting and the r'' prefix are already in
        # the source form, which is what lets install_audit see no drift.
        sed -i \
            -e "s#python \"\.advanced-plans/bin/ap\.py\"#python \"$AP_LAUNCHER\"#g" \
            -e "s#runpy\.run_path(r'\.advanced-plans/bin/ap\.py')#runpy.run_path(r'$AP_LAUNCHER')#g" \
            "$_f"
    done

    # Note: skills are NOT copied globally — they must be referenced by path
    echo ""
    echo "  Note: Core skills are NOT installed globally."
    echo "  Commands will load skills from:"
    echo "    $CORE_DIR/skills/"
    echo ""
    echo "  To use globally installed commands with skills, either:"
    echo "    a) Run --project install in each project to copy skills locally"
    echo "    b) Set PLANNING_SKILLS_PATH=$CORE_DIR/skills in your shell profile"
    echo ""
    echo "✓ Global commands installed"
    echo ""
    echo "Commands available in any Claude Code session:"
    ls "$COMMANDS_DIR"/*.md | xargs -I{} basename {} .md | sed 's/^/  \//'
    echo ""
}

# Parse arguments
case "$1" in
    --help|-h)
        print_help
        ;;
    --reference)
        print_reference
        ;;
    --project)
        install_project "$2"
        ;;
    --global)
        install_global
        ;;
    "")
        echo "Advanced Planning System v8 — Installer"
        echo ""
        echo "Run with --help for usage information."
        echo ""
        print_help
        ;;
    *)
        echo "Unknown option: $1" >&2
        echo "Run ./install.sh --help for usage." >&2
        exit 1
        ;;
esac
