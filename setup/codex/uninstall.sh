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
#   registration dropped but the files left. The registry is updated, not deleted.
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
# Set only by the ownership KEEP decision below.  KEPT alone will not do: it is
# also incremented by remove_if_empty for a directory that merely has files in
# it, which says nothing about who owns the runtime.
SHARED_OWNERS=0

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

# Process ownership: remove "codex" from each skill, determine what to delete.
# Uses Python for proper JSON handling. Outputs decisions to stdout.
# Format: KEEP|REMOVE skill_name
process_ownership() {
    _skills_dir="$1"
    _ownership_file="$2"
    _confirmed="$3"

    # List of skills this adapter installed
    _approved_skills="advanced-planning phase-plan-creator ralph-loop-planner plan-todos plan-skill-identification plan-subagent-identification progress-report schema-design"

    python - "$_ownership_file" "$_skills_dir" "$_approved_skills" "$_confirmed" <<'PYEOF'
import json
import sys
import os

owner_file = sys.argv[1]
skills_dir = sys.argv[2]
approved_skills = sys.argv[3].split() if len(sys.argv) > 3 else []
confirmed = sys.argv[4] == "true"

# Read ownership file
data = {"schema_version": 1, "skills": {}}
if os.path.exists(owner_file):
    try:
        with open(owner_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError):
        # Malformed - treat as empty, will be cleaned up
        pass

if "skills" not in data:
    data["skills"] = {}

# Process each skill this adapter installed - mutate data in place
any_remaining = False
for skill in approved_skills:
    owners = data["skills"].get(skill, [])
    if not isinstance(owners, list):
        owners = []
    
    # Remove "codex" from owners - mutate data directly
    if "codex" in owners:
        owners = [o for o in owners if o != "codex"]
        data["skills"][skill] = owners  # Write back to data
    
    # Determine action
    skill_path = os.path.join(skills_dir, skill)
    skill_exists = os.path.isdir(skill_path)
    
    if owners:
        # Shared - keep files, update registration
        print(f"KEEP|{skill}|{','.join(owners)}")
        any_remaining = True
    elif skill_exists:
        # Sole owner - remove files, drop entry
        print(f"REMOVE|{skill}|")
    # else: skill doesn't exist and no owners - nothing to do

# Write updated ownership file only if there are remaining entries
if any_remaining and confirmed:
    # Build remaining skills: approved skills with owners + non-approved entries
    remaining_skills = {}
    for skill in approved_skills:
        owners = data["skills"].get(skill, [])
        if owners:
            remaining_skills[skill] = owners
    # Also keep any non-approved-skill entries (from other adapters)
    for k, v in data["skills"].items():
        if k not in approved_skills and v:
            remaining_skills[k] = v
    
    if remaining_skills:
        data["skills"] = remaining_skills
        data["schema_version"] = 1
        with open(owner_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.write('\n')
    elif os.path.exists(owner_file):
        os.remove(owner_file)
elif not any_remaining and confirmed and os.path.exists(owner_file):
    # No remaining owners - delete the file
    os.remove(owner_file)
PYEOF
}

uninstall_from() {
    AGENTS_DIR="$1"
    AP_DIR="$2"
    SKILLS_DIR="$AGENTS_DIR/skills"
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
    # Process ownership and get decisions
    if [ "$CONFIRMED" = true ]; then
        _decisions="$(process_ownership "$SKILLS_DIR" "$OWNERSHIP_FILE" "$CONFIRMED")"
    else
        # Dry run - simulate what would happen
        _decisions="$(process_ownership "$SKILLS_DIR" "$OWNERSHIP_FILE" "false")"
    fi
    
    # Parse decisions - use here-string to avoid subshell (while in pipe loses REMOVED/KEPT)
    while IFS='|' read -r _action _skill _owners; do
        [ -z "$_action" ] && continue
        _skill_path="$SKILLS_DIR/$_skill"
        if [ "$_action" = "KEEP" ]; then
            echo "  - $_skill (shared with another adapter - leaving files, updating registration)"
            KEPT=$((KEPT + 1))
            SHARED_OWNERS=1
        elif [ "$_action" = "REMOVE" ]; then
            echo "  - skills/$_skill"
            remove_path "$_skill_path"
        fi
    done <<EOF
$_decisions
EOF
    
    remove_if_empty "$SKILLS_DIR"
    remove_if_empty "$AGENTS_DIR"

    # Remove AGENTS.md fence
    echo "AGENTS.md:"
    _agents_file="$AGENTS_DIR/../AGENTS.md"
    remove_agents_fence "$_agents_file"

    # Shared Python runtime
    echo "Shared Python runtime:"
    if [ "$SHARED_OWNERS" -eq 1 ]; then
        # Another adapter still owns a skill here, and every one of those
        # skills invokes .advanced-plans/bin/ap.py.  Removing the launcher
        # would leave that adapter installed but inert -- exactly the failure
        # the ownership check above exists to prevent.
        echo "  keeping bin/ap.py and runtime.json (still owned by another adapter)"
    else
        if [ -f "$AP_DIR/bin/ap.py" ]; then
            echo "  - bin/ap.py"
            remove_path "$AP_DIR/bin/ap.py"
        fi
        remove_if_empty "$AP_DIR/bin"
        if [ -f "$AP_DIR/runtime.json" ]; then
            echo "  - runtime.json"
            remove_path "$AP_DIR/runtime.json"
        fi
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
