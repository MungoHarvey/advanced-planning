#!/bin/sh
# uninstall.sh — remove what install.sh installed, and nothing else.
#
# Usage:
#   ./uninstall.sh --project [path]   Remove from a project (default: .)
#   ./uninstall.sh --global           Remove from the global Claude Code config
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
#   That set is derived from the source checkout, exactly as install.sh derives
#   what to copy. A file in .claude/commands/ that this checkout does not
#   provide was not installed from here and is left alone.
#
# Order is deliberate: commands first, the launcher last. A partial uninstall
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
# report success. Kept identical to install.sh's ap_home_fs and pinned by
# platforms/python/tests/test_home_resolution_agreement.py.
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
# followed: install.sh can symlink skills/ into the source checkout, and the
# target there is the user's checkout, which was never part of the install.
# Unlinking is what is actually meant, so the -L branch comes first and the
# recursive branch can never see a link.
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
    # The destination may itself be a link INTO the source checkout, and this
    # check has to come before anything that walks it. install.sh replaces
    # .claude/commands, skills and schemas wholesale with symlinks in
    # self-install mode, and install.ps1 uses junctions for the same thing;
    # --symlink does it for skills alone. `[ -d ]` follows a link, so without
    # this the loop below would iterate the source names and rm each one
    # THROUGH the link -- deleting the user's checkout, not their install.
    # Git Bash reports a junction as both -L and -d, so this catches the
    # Windows shape too.
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

# Remove a directory only if the uninstall emptied it. A leftover file in there
# is the user's, and it is the reason this is not `rm -rf`.
remove_if_empty() {
    _d="$1"
    # A link is never "an empty directory to tidy up" -- it is either already
    # unlinked above or it is not ours. Checked before -d, which follows it.
    # Written as an if rather than `[ -L ... ] && return 0`, whose failing
    # AND-list exit status is a set -e hazard that differs between shells.
    if [ -L "$_d" ]; then
        return 0
    fi
    [ -d "$_d" ] || return 0
    # During a dry run the deletions above have not happened, so the directory
    # is still full and "not empty" would be a lie about the end state. Only
    # the confirmed run can report this truthfully.
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

uninstall_from() {
    CLAUDE_DIR="$1"
    AP_DIR="$2"

    echo ""
    echo "Removing Advanced Planning from:"
    echo "  adapter:  $CLAUDE_DIR"
    echo "  runtime:  $AP_DIR"
    if [ "$CONFIRMED" != true ]; then
        echo ""
        echo "  DRY RUN -- nothing will be deleted. Re-run with --yes to act."
    fi
    echo ""

    echo "Slash commands:"
    remove_installed_from "$REPO_ROOT/platforms/claude-code/commands" \
        "$CLAUDE_DIR/commands" "commands"
    remove_if_empty "$CLAUDE_DIR/commands"

    echo "Agent definitions:"
    remove_installed_from "$REPO_ROOT/core/agents" "$CLAUDE_DIR/agents" "agents"
    remove_installed_from "$REPO_ROOT/platforms/claude-code/agents" \
        "$CLAUDE_DIR/agents" "agents"
    remove_if_empty "$CLAUDE_DIR/agents"

    echo "Skills:"
    remove_installed_from "$REPO_ROOT/core/skills" "$CLAUDE_DIR/skills" "skills"
    remove_if_empty "$CLAUDE_DIR/skills"

    echo "Schemas:"
    remove_installed_from "$REPO_ROOT/core/schemas" "$CLAUDE_DIR/schemas" "schemas"
    remove_if_empty "$CLAUDE_DIR/schemas"

    # settings.json is reported, never removed. The installer writes it only
    # when absent and saves settings.planning.json when one already exists, so
    # the file here may be entirely the user's, may be ours, or may be theirs
    # with our hooks merged in by hand. Nothing in it records which, so this
    # script cannot know, and deleting a Claude Code settings file on a guess
    # is not a recoverable mistake.
    if [ -f "$CLAUDE_DIR/settings.json" ]; then
        echo "Settings:"
        echo "  keeping $CLAUDE_DIR/settings.json -- remove the planning hooks by hand if you want them gone."
        KEPT=$((KEPT + 1))
    fi
    if [ -f "$CLAUDE_DIR/settings.planning.json" ]; then
        echo "  - settings.planning.json"
        remove_path "$CLAUDE_DIR/settings.planning.json"
    fi

    # Last, for the reason at the top of this file.
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

    echo ""
    echo "Left in place -- this is your planning record, not part of the install:"
    for _keep in phases specs state logs PLANNING.md README.md gate-verdicts evidence; do
        [ -e "$AP_DIR/$_keep" ] && echo "  $AP_DIR/$_keep"
    done
    echo ""
    if [ "$CONFIRMED" = true ]; then
        echo "Done. $REMOVED path(s) removed."
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
        uninstall_from "$(ap_home_fs)/.claude" "$(ap_home_fs)/.advanced-plans"
        ;;
    project)
        if [ ! -d "$PROJECT_DIR" ]; then
            echo "Error: directory not found: $PROJECT_DIR" >&2
            exit 1
        fi
        uninstall_from "$PROJECT_DIR/.claude" "$PROJECT_DIR/.advanced-plans"
        ;;
    *)
        echo "Specify --project [path] or --global." >&2
        echo "Run ./uninstall.sh --help for details." >&2
        exit 1
        ;;
esac
