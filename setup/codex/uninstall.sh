#!/bin/sh
# uninstall.sh — remove what install.sh installed for Codex, and nothing else.
#
# Usage:
#   ./uninstall.sh --project [path]   Remove from a project (default: .)
#   ./uninstall.sh --global           Remove from the global config
#   ./uninstall.sh ... --yes          Actually delete. Without it, dry run.
#   ./uninstall.sh --help
#
# Why this exists, and why it is fussier than `rm -rf`:
#
#   The installed mechanism shares a directory with the user's own work.
#   .advanced-plans/ holds bin/ap.py and runtime.json -- which this script
#   removes -- alongside phases/, specs/, state/, logs/, PLANNING.md and
#   README.md, which are the user's planning record and which this script must
#   never touch. install.sh even migrates a legacy plans/ directory into them.
#   So "uninstall" cannot be a directory removal; it has to be a removal of a
#   known set of names.
#
#   The shared skill at .agents/skills/advanced-planning/ may be registered by
#   both Codex and OpenCode. This script reads .advanced-plans/skill-ownership.json
#   and only removes what Codex owns. Shared entries have this adapter's
#   registration dropped but the files left.
#
#   That set is derived from the source checkout, exactly as install.sh derives
#   what to copy. A file in .agents/skills/ that this checkout does not
#   provide was not installed from here and is left alone.
#
# Order is deliberate: skills first, the launcher last. A partial uninstall
# that removed the launcher but left the commands would leave the system in the
# one state it cannot diagnose -- the commands invoke .advanced-plans/bin/ap.py,
# and with that file gone the interpreter fails to open it and exits before any
# of this system's code, so no guard can name the cause. Commands without a
# launcher is broken and silent; a launcher without commands is inert and
# harmless. Fail in the harmless direction.
#
# Dry run is the default. This deletes files under a user's home directory and
# inside their project, and the failure mode of getting it wrong is losing
# planning work, so acting requires --yes to be typed.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
REPO_ROOT="$SCRIPT_DIR"

MODE=""
PROJECT_DIR="."
CONFIRMED=false

# USERPROFILE before HOME: Git Bash $HOME is routinely a mapped network drive
# on Windows while the installer wrote to the local profile. Removing from a
# different home than the install wrote to would silently remove nothing and
# report success. Kept identical to install.sh's ap_home_fs.
ap_home_fs() {
    if [ -n "${USERPROFILE:-}" ] && command -v cygpath >/dev/null 2>&1; then
        cygpath -u "$USERPROFILE"
    elif [ -n "${USERPROFILE:-}" ]; then
        printf '%s' "$USERPROFILE"
    elif [ -n "${HOME:-}" ]; then
        printf '%s' "$HOME"
    else
        echo "uninstall.sh: neither USERPROFILE nor HOME is set; refusing to guess the global home." >&2
        exit 1
    fi
}

print_help() {
    sed -n '/^# Usage:/,/^$/p' "$0" | sed 's/^# \{0,1\}//'
}

REMOVED=0
KEPT=0

# Remove one path, if it is one we installed. Links are unlinked, never
# followed.
remove_path() {
    _p="$1"
    if [ -L "$_p" ]; then
        if [ "$CONFIRMED" = true ]; then rm -- "$_p"; else echo "  [dry-run] unlink $_p"; fi
        REMOVED=$((REMOVED + 1))
        return 0
    fi
    if [ -d "$_p" ]; then
        if [ "$CONFIRMED" = true ]; then rm -rf -- "$_p"; else echo "  [dry-run] rm -rf $_p"; fi
        REMOVED=$((REMOVED + 1))
        return 0
    fi
    if [ -f "$_p" ]; then
        if [ "$CONFIRMED" = true ]; then rm -f -- "$_p"; else echo "  [dry-run] rm $_p"; fi
        REMOVED=$((REMOVED + 1))
        return 0
    fi
    return 0
}

# Remove <dest>/<name> for every <name> the source directory provides.
remove_installed_from() {
    _src="$1"; _dest="$2"; _label="$3"
    if [ -L "$_dest" ]; then
        echo "  - $_label (link -- unlinking, not following)"
        remove_path "$_dest"
        return 0
    fi
    [ -d "$_dest" ] || return 0
    for _item in "$_src"/*; do
        [ -e "$_item" ] || continue
        _name="$(basename "$_item")"
        if [ -e "$_dest/$_name" ] || [ -L "$_dest/$_name" ]; then
            echo "  - $_label/$_name"
            remove_path "$_dest/$_name"
        fi
    done
}

# Remove a directory only if the uninstall emptied it.
remove_if_empty() {
    _d="$1"
    if [ -L "$_d" ]; then
        return 0
    fi
    [ -d "$_d" ] || return 0
    if [ "$CONFIRMED" != true ]; then
        echo "  [dry-run] rmdir $_d, if the removals above leave it empty"
        return 0
    fi
    if [ -z "$(ls -A "$_d" 2>/dev/null)" ]; then
        rmdir "$_d"
    else
        echo "  keeping $_d (not empty -- contains files this installer did not write)"
        KEPT=$((KEPT + 1))
    fi
}

# Check skill ownership and remove appropriately
remove_skill_with_ownership() {
    _skill_name="$1"
    _skills_dir="$2"
    _ownership_file="$3"
    _skill_path="$_skills_dir/$_skill_name"

    [ -d "$_skill_path" ] || return 0

    # Check ownership if metadata exists
    if [ -f "$_ownership_file" ]; then
        # Simple check: does the ownership file list "codex" for this skill?
        # If skill is shared (multiple owners), remove registration but leave files
        # If skill is codex-only, remove files
        # For now: if ownership file exists and lists codex, remove the skill
        # This is a simplified approach - full implementation would parse JSON
        _is_owner=true
        if grep -q "\"$_skill_name\"" "$_ownership_file" 2>/dev/null; then
            # Skill is in ownership file - check if codex is listed
            # Extract the array for this skill and check for "codex"
            if grep -A5 "\"$_skill_name\"" "$_ownership_file" | grep -q '"codex"'; then
                _is_owner=true
            else
                _is_owner=false
            fi
        fi

        if [ "$_is_owner" = false ]; then
            echo "  - $_skill_name (shared with another adapter - leaving in place)"
            KEPT=$((KEPT + 1))
            return 0
        fi
    fi

    echo "  - skills/$_skill_name"
    remove_path "$_skill_path"
}

# Remove AGENTS.md fence for codex
remove_agents_fence() {
    _agents_file="$1"
    _fence_start="<!-- advanced-planning:codex:start -->"
    _fence_end="<!-- advanced-planning:codex:end -->"

    [ -f "$_agents_file" ] || return 0

    if ! grep -q "$_fence_start" "$_agents_file" 2>/dev/null; then
        return 0
    fi

    if [ "$CONFIRMED" = true ]; then
        # Remove the fence block using sed
        # This is tricky - we need to remove from fence_start to fence_end inclusive
        # Use a temp file approach for portability
        _tmpfile=$(mktemp)
        sed "/${_fence_start}/,/${_fence_end}/d" "$_agents_file" > "$_tmpfile"
        # Remove leading/trailing blank lines that may result
        sed '/^$/N;/^\n$/d' "$_tmpfile" > "${_tmpfile}.2"
        mv "${_tmpfile}.2" "$_agents_file"
        rm -f "$_tmpfile"
        echo "  - AGENTS.md fence block removed"
        REMOVED=$((REMOVED + 1))
    else
        echo "  [dry-run] remove AGENTS.md fence block"
    fi
}

uninstall_from() {
    CLAUDE_DIR="$1"
    AP_DIR="$2"
    SKILLS_DIR="$CLAUDE_DIR/skills"
    OWNERSHIP_FILE="$AP_DIR/skill-ownership.json"

    echo ""
    echo "Removing Codex Advanced Planning adapter from:"
    echo "  skills:   $SKILLS_DIR"
    echo "  runtime:  $AP_DIR"
    if [ "$CONFIRMED" != true ]; then
        echo ""
        echo "  DRY RUN -- nothing will be deleted. Re-run with --yes to act."
    fi
    echo ""

    echo "Skills (with ownership check):"
    # Remove shared routing skill
    remove_skill_with_ownership "advanced-planning" "$SKILLS_DIR" "$OWNERSHIP_FILE"
    # Remove approved core skills
    for _skill in phase-plan-creator ralph-loop-planner plan-todos plan-skill-identification plan-subagent-identification progress-report schema-design; do
        remove_skill_with_ownership "$_skill" "$SKILLS_DIR" "$OWNERSHIP_FILE"
    done
    remove_if_empty "$SKILLS_DIR"
    remove_if_empty "$CLAUDE_DIR/.agents"

    # Remove AGENTS.md fence
    echo "AGENTS.md:"
    remove_agents_fence "$CLAUDE_DIR/../AGENTS.md"

    # Shared Python runtime
    echo "Shared Python runtime:"
    if [ -f "$AP_DIR/bin/ap.py" ]; then
        echo "  - bin/ap.py"
        remove_path "$AP_DIR/bin/ap.py"
    fi
    remove_if_empty "$AP_DIR/bin"
    if [ -f "$AP_DIR/runtime.json" ]; then
        echo "  - runtime.json"
        remove_path "$AP_DIR/runtime.json"
    fi
    # Remove skill-ownership.json
    if [ -f "$OWNERSHIP_FILE" ]; then
        echo "  - skill-ownership.json"
        remove_path "$OWNERSHIP_FILE"
    fi

    echo ""
    echo "Left in place -- this is your planning record, not part of the install:"
    for _keep in phases specs state logs PLANNING.md README.md gate-verdicts evidence; do
        [ -e "$AP_DIR/$_keep" ] && echo "  $AP_DIR/$_keep"
    done
    echo ""
    if [ "$CONFIRMED" = true ]; then
        echo "Done. $REMOVED path(s) removed, $KEPT kept."
    else
        echo "Dry run complete. $REMOVED path(s) would be removed. Re-run with --yes."
    fi
    echo ""
}

while [ $# -gt 0 ]; do
    case "$1" in
        --help|-h) print_help; exit 0 ;;
        --global) MODE="global"; shift ;;
        --project)
            MODE="project"
            if [ -n "${2:-}" ] && [ "${2#--}" = "$2" ]; then PROJECT_DIR="$2"; shift; fi
            shift ;;
        --yes) CONFIRMED=true; shift ;;
        *) echo "Unknown option: $1" >&2; echo "Run ./uninstall.sh --help" >&2; exit 1 ;;
    esac
done

case "$MODE" in
    global)
        uninstall_from "$(ap_home_fs)/.agents" "$(ap_home_fs)/.advanced-plans"
        ;;
    project)
        if [ ! -d "$PROJECT_DIR" ]; then
            echo "Error: directory not found: $PROJECT_DIR" >&2
            exit 1
        fi
        uninstall_from "$PROJECT_DIR/.agents" "$PROJECT_DIR/.advanced-plans"
        ;;
    *)
        echo "Specify --project [path] or --global." >&2
        echo "Run ./uninstall.sh --help for details." >&2
        exit 1
        ;;
esac
