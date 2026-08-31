#!/bin/sh
# install.sh
#
# Installs the Advanced Planning System for Codex into a project or globally.
#
# Usage:
#   sh setup/codex/install.sh --project /path/to/your/project
#   sh setup/codex/install.sh --global
#   sh setup/codex/install.sh --dry-run --project /path/to/your/project
#
# What is installed:
#   --project: shared routing skill + approved core skills to PROJECT/.agents/skills/
#   --global:  skills to ~/.agents/skills/, runtime to ~/.advanced-plans/
#   AGENTS.md merge in project root (idempotent fence)
#   No .codex/ content - Codex discovers skills automatically

set -e

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROJECT_DIR=""
GLOBAL=false
DRY_RUN=false
SELF_INSTALL=false

# Approved core skills to install (excludes companion-detection, permission-config)
# The shared routing skill "advanced-planning" is installed alongside these.
APPROVED_SKILLS="phase-plan-creator ralph-loop-planner plan-todos plan-skill-identification plan-subagent-identification progress-report schema-design"
ALL_INSTALLED_SKILLS="advanced-planning $APPROVED_SKILLS"

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
        --help|-h)
            echo "Usage:"
            echo "  sh setup/codex/install.sh --project /path/to/project"
            echo "  sh setup/codex/install.sh --global"
            echo "  sh setup/codex/install.sh --dry-run --project /path/to/project"
            echo ""
            echo "Installs the shared routing skill and approved core skills to .agents/skills/"
            echo "Writes .advanced-plans/runtime.json and .advanced-plans/bin/ap.py (Contract 6)"
            echo "Merges AGENTS.md with an idempotent fenced block"
            echo "No .codex/ content is created"
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
    if [ "$DRY_RUN" = true ]; then
        echo "  [dry-run] cp -r $1 $2"
    else
        cp -r "$1" "$2"
    fi
}

do_mkdir() {
    if [ "$DRY_RUN" = true ]; then
        echo "  [dry-run] mkdir -p $1"
    else
        mkdir -p "$1"
    fi
}

sha256_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | cut -d' ' -f1
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | cut -d' ' -f1
    else
        echo "NO_SHA256"
    fi
}

files_identical() {
    if command -v diff >/dev/null 2>&1; then
        diff -q "$1" "$2" >/dev/null 2>&1
        return $?
    else
        # Fallback: compare SHA-256
        _h1="$(sha256_file "$1")"
        _h2="$(sha256_file "$2")"
        [ "$_h1" = "$_h2" ]
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
    exit 1
fi

if [ ! -d "$REPO_ROOT/platforms/shared/agent-skills/advanced-planning" ]; then
    echo "ERROR: cannot find platforms/shared/agent-skills/advanced-planning" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Global runtime record (Contract 6)
# ---------------------------------------------------------------------------
ap_home_fs() {
    if [ -n "${USERPROFILE:-}" ] && command -v cygpath >/dev/null 2>&1; then
        cygpath -u "$USERPROFILE"
    elif [ -n "${USERPROFILE:-}" ]; then
        printf '%s' "$USERPROFILE"
    elif [ -n "${HOME:-}" ]; then
        printf '%s' "$HOME"
    else
        echo "install.sh: neither USERPROFILE nor HOME is set; refusing to resolve the global home to the filesystem root." >&2
        exit 1
    fi
}

ap_home_native() {
    if [ -n "${USERPROFILE:-}" ] && command -v cygpath >/dev/null 2>&1; then
        cygpath -m "$USERPROFILE"
    elif [ -n "${USERPROFILE:-}" ]; then
        printf '%s' "$USERPROFILE" | tr '\\' '/'
    elif [ -n "${HOME:-}" ]; then
        printf '%s' "$HOME"
    else
        echo "install.sh: neither USERPROFILE nor HOME is set; refusing to resolve the global home to the filesystem root." >&2
        exit 1
    fi
}

# Replace every LITERAL occurrence of $2 with $3 in $1; answer in AP_SUBST_RESULT.
# A function rather than a command substitution, because $( ) forks once per call
# and this runs per line -- on Windows that is seconds of wall clock. Both
# operands are quoted inside the expansions, so a glob metacharacter in either is
# taken literally.
ap_subst() {
    _sub_s="$1"; _sub_n="$2"; _sub_r="$3"; _sub_out=""
    while :; do
        case "$_sub_s" in
            *"$_sub_n"*)
                _sub_out="$_sub_out${_sub_s%%"$_sub_n"*}$_sub_r"
                _sub_s="${_sub_s#*"$_sub_n"}"
                ;;
            *)
                break
                ;;
        esac
    done
    AP_SUBST_RESULT="$_sub_out$_sub_s"
}

ap_rewrite_call_sites() {
    _f="$1"; _launcher="$2"
    # Only the PATH changes. The quoting and the r'' prefix are already in the
    # source form, so this is a pure substitution of one string for another --
    # which is what lets install_audit normalise it back and report no drift.
    #
    # Done in shell rather than with `sed -i`, which CANNOT be used here: under
    # MSYS (Git Bash) sed opens files in text mode and rewrites every CRLF as
    # LF, measured even for a substitution that matches nothing. That made a
    # shell global install produce byte-different skill files from a PowerShell
    # one, whose Set-ApCallSites preserves endings. The same GNU sed 4.9 on
    # Linux preserves CR, so it is the platform rather than the tool and no sed
    # invocation is safe. Default awk strips too; perl and gawk preserve but
    # would each be a new install-time dependency. This uses neither.
    if [ ! -f "$_f" ]; then
        printf 'ERROR: cannot rewrite call sites, no such file: %s\n' "$_f" >&2
        return 1
    fi

    _pat_py='python ".advanced-plans/bin/ap.py"'
    _pat_rp="runpy.run_path(r'.advanced-plans/bin/ap.py')"

    # A file with no call site is never opened for writing, so it stays
    # byte-identical rather than merely ending up with equal text.
    if ! grep -qF -e "$_pat_py" -e "$_pat_rp" "$_f"; then
        return 0
    fi

    # Command substitution strips trailing newlines, so an empty answer here
    # means the last byte was one. That is how a file with no final newline
    # survives the rewrite without gaining one.
    if [ -n "$(tail -c 1 "$_f")" ]; then _ends_nl=0; else _ends_nl=1; fi

    _tmp="$_f.ap-rewrite"
    _first=1
    while IFS= read -r _line || [ -n "$_line" ]; do
        if [ "$_first" = 0 ]; then printf '\n'; fi
        _first=0
        ap_subst "$_line" "$_pat_py" "python \"$_launcher\""
        ap_subst "$AP_SUBST_RESULT" "$_pat_rp" "runpy.run_path(r'$_launcher')"
        printf '%s' "$AP_SUBST_RESULT"
    done < "$_f" > "$_tmp"
    if [ "$_ends_nl" = 1 ] && [ "$_first" = 0 ]; then printf '\n' >> "$_tmp"; fi
    mv "$_tmp" "$_f"
}

ap_write_global_runtime() {
    _home_fs="$(ap_home_fs)"
    _home_native="$(ap_home_native)"
    _ap_dir="$_home_fs/.advanced-plans"
    do_mkdir "$_ap_dir/bin"
    do_cp "$REPO_ROOT/platforms/python/ap_launcher.py" "$_ap_dir/bin/ap.py"
    if [ "$DRY_RUN" != true ]; then
        # Convert to a path Windows Python can open
        if command -v cygpath >/dev/null 2>&1; then
            _src="$(cygpath -m "$REPO_ROOT")"
        elif echo "$REPO_ROOT" | grep -q "^/mnt/[a-zA-Z]/"; then
            _drive="$(echo "$REPO_ROOT" | sed 's|^/mnt/\([a-zA-Z]\)/.*|\1|')"
            _rest="$(echo "$REPO_ROOT" | sed 's|^/mnt/[a-zA-Z]/||')"
            _src="${_drive}:/${_rest}"
        else
            _src="$REPO_ROOT"
        fi
        _ver="unknown"
        [ -f "$REPO_ROOT/VERSION" ] && _ver="$(tr -d '[:space:]' < "$REPO_ROOT/VERSION")"
        printf '{"schema_version": 1, "source_root": "%s", "version": "%s", "written_by": "setup/codex/install.sh --global"}\n' \
            "$_src" "$_ver" > "$_ap_dir/runtime.json"
    fi
    say "  + $_ap_dir/bin/ap.py"
    say "  + $_ap_dir/runtime.json"
}

# ---------------------------------------------------------------------------
# Collision check for shared skills
# ---------------------------------------------------------------------------
check_collision() {
    _src="$1"
    _dst="$2"
    _skill_name="$3"
    # Optional 4th argument.  When set, the destination was rewritten to point
    # at this absolute launcher when it was installed, so the raw source can
    # never match it and every second global install would report a fork of a
    # file it actually agrees with.  Compare what THIS installer would write.
    # The project branch passes nothing and keeps a raw-vs-raw comparison.
    _launcher="${4:-}"

    if [ ! -e "$_dst" ]; then
        return 0  # No collision - destination absent
    fi

    # Check each file in the skill directory recursively
    _collision=false
    while IFS= read -r _rel; do
        [ -n "$_rel" ] || continue
        _src_file="$_src/$_rel"
        _dst_file="$_dst/$_rel"
        if [ -f "$_src_file" ] && [ -f "$_dst_file" ]; then
            _cmp_file="$_src_file"
            _tmp_file=""
            if [ -n "$_launcher" ]; then
                _tmp_file="$(mktemp)"
                cp "$_src_file" "$_tmp_file"
                ap_rewrite_call_sites "$_tmp_file" "$_launcher"
                _cmp_file="$_tmp_file"
            fi
            if ! files_identical "$_cmp_file" "$_dst_file"; then
                _collision=true
                _src_hash="$(sha256_file "$_cmp_file")"
                _dst_hash="$(sha256_file "$_dst_file")"
                if [ -n "$_tmp_file" ]; then
                    rm -f "$_tmp_file"
                fi
                echo "ERROR: collision detected for skill '$_skill_name'" >&2
                echo "  Source:      $_src_file (SHA-256: $_src_hash)" >&2
                if [ -n "$_launcher" ]; then
                    echo "  (source hashed as it would be installed, call sites rewritten)" >&2
                fi
                echo "  Installed:   $_dst_file (SHA-256: $_dst_hash)" >&2
                echo "  Refusing to overwrite - silent divergence is the defect this check exists to catch." >&2
                return 1
            fi
            if [ -n "$_tmp_file" ]; then
                rm -f "$_tmp_file"
            fi
        fi
    done <<EOF
$(cd "$_src" && find . -type f | sed 's|^\./||')
EOF

    # Identical - report shared; unchanged
    say "  shared; unchanged: $_skill_name"
    return 2  # Signal: identical, skip copy
}

# ---------------------------------------------------------------------------
# AGENTS.md merge
# ---------------------------------------------------------------------------
merge_agents_md() {
    _project="$1"
    _agents_file="$_project/AGENTS.md"
    _fence_start="<!-- advanced-planning:codex:start -->"
    _fence_end="<!-- advanced-planning:codex:end -->"

    _fence_content="$_fence_start
## Advanced Planning for Codex

This project uses the Advanced Planning framework for structured, multi-loop execution.

**Triggers:**
- \`\$advanced-planning phase <goal>\` - Create a new phase plan
- \`\$advanced-planning loop next\` - Execute the next loop
- \`\$advanced-planning gate current\` - Run gate review on completed phase
- \`\$advanced-planning resume\` - Recover from interruption
- \`\$advanced-planning compact current\` - Compact phase artefacts

**Runtime:** Commands use the shared Python launcher at \`.advanced-plans/bin/ap.py\`. Exit code 3 means the runtime is unreachable - run the installer again.

**Skills:** Installed to \`.agents/skills/\` - Codex discovers them automatically.

$_fence_end"

    if [ ! -f "$_agents_file" ]; then
        # Create new file with fence
        if [ "$DRY_RUN" = true ]; then
            echo "  [dry-run] create $_agents_file with fence block"
        else
            printf '%s\n' "$_fence_content" > "$_agents_file"
            say "  + AGENTS.md (created with fence)"
        fi
        return 0
    fi

    # Check if fence already exists
    if grep -q "$_fence_start" "$_agents_file" 2>/dev/null; then
        # Fence exists - check for malformed/duplicated fence
        _count="$(grep -c "$_fence_start" "$_agents_file" 2>/dev/null || echo 0)"
        if [ "$_count" -gt 1 ]; then
            echo "ERROR: malformed AGENTS.md - multiple advanced-planning:codex:start fences" >&2
            exit 1
        fi
        if ! grep -q "$_fence_end" "$_agents_file" 2>/dev/null; then
            echo "ERROR: malformed AGENTS.md - fence started but not closed" >&2
            exit 1
        fi
        # Idempotent - fence exists and is well-formed, skip
        say "  AGENTS.md fence already present - unchanged"
        return 0
    fi

    # Append fence to existing file
    if [ "$DRY_RUN" = true ]; then
        echo "  [dry-run] append fence block to $_agents_file"
    else
        printf '\n%s\n' "$_fence_content" >> "$_agents_file"
        say "  + AGENTS.md (appended fence)"
    fi
}

# ---------------------------------------------------------------------------
# Ownership metadata for shared skills
# ---------------------------------------------------------------------------
# Uses Python for JSON read/modify/write to avoid fragile shell parsing.
# Python is a hard dependency (the launcher) and this is the approach
# that guarantees correct merging without grep-based hacks.
write_ownership() {
    _project="$1"
    _owner_file="$_project/.advanced-plans/skill-ownership.json"

    if [ "$DRY_RUN" = true ]; then
        echo "  [dry-run] merge/write $_owner_file"
        return
    fi

    # Python does the JSON merge: reads existing (if any), adds "codex" to
    # each installed skill's owner list (creating entries as needed), leaves
    # other entries untouched, deduplicates, and writes back.
    python - "$_owner_file" "$ALL_INSTALLED_SKILLS" <<'PYEOF'
import json
import sys
import os

owner_file = sys.argv[1]
approved_skills = sys.argv[2].split() if len(sys.argv) > 2 else []

# Read existing or start fresh
if os.path.exists(owner_file):
    try:
        with open(owner_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f"install.sh: {owner_file} is malformed JSON ({exc})\n")
        sys.stderr.write("install.sh: fix: repair the file or delete it and re-install.\n")
        sys.exit(1)
else:
    data = {"schema_version": 1, "skills": {}}

# Ensure skills dict exists
if "skills" not in data:
    data["skills"] = {}

# Merge: for each skill this adapter installs, add "codex" to owners
for skill in approved_skills:
    existing = data["skills"].get(skill, [])
    if not isinstance(existing, list):
        existing = []
    if "codex" not in existing:
        existing.append("codex")
    data["skills"][skill] = existing

# Write back
data["schema_version"] = 1
with open(owner_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
PYEOF
}

# ---------------------------------------------------------------------------
# Global install
# ---------------------------------------------------------------------------
if [ "$GLOBAL" = true ]; then
    GLOBAL_DIR="$(ap_home_fs)/.agents"
    AP_LAUNCHER="$(ap_home_native)/.advanced-plans/bin/ap.py"
    say "Installing globally to $GLOBAL_DIR"
    do_mkdir "$GLOBAL_DIR/skills"

    # Install shared routing skill
    say "Installing shared routing skill..."
    _src="$REPO_ROOT/platforms/shared/agent-skills/advanced-planning"
    _dst_parent="$GLOBAL_DIR/skills"
    _collision_result=0
    check_collision "$_src" "$_dst_parent/advanced-planning" "advanced-planning" "$AP_LAUNCHER" || _collision_result=$?
    if [ $_collision_result -eq 0 ]; then
        do_cp "$_src" "$_dst_parent/"
        say "  + skills/advanced-planning/"
    elif [ $_collision_result -eq 1 ]; then
        exit 1  # Collision error
    fi
    # _collision_result == 2 means identical, already reported

    # Rewrite call sites in global install
    if [ "$DRY_RUN" != true ]; then
        find "$_dst_parent/advanced-planning" -name '*.md' -type f | while IFS= read -r _f; do
            ap_rewrite_call_sites "$_f" "$AP_LAUNCHER"
        done
        say "  (rewrote launcher call sites to $AP_LAUNCHER)"
    fi

    # Install approved core skills
    say "Installing approved core skills..."
    for _skill in $APPROVED_SKILLS; do
        _src="$REPO_ROOT/core/skills/$_skill"
        if [ ! -d "$_src" ]; then
            echo "WARNING: core/skills/$_skill not found - skipping" >&2
            continue
        fi
        _collision_result=0
        check_collision "$_src" "$_dst_parent/$_skill" "$_skill" "$AP_LAUNCHER" || _collision_result=$?
        if [ $_collision_result -eq 0 ]; then
            do_cp "$_src" "$_dst_parent/"
            say "  + skills/$_skill/"
        elif [ $_collision_result -eq 1 ]; then
            exit 1
        fi
        # Rewrite call sites if skill has any
        if [ "$DRY_RUN" != true ]; then
            find "$_dst_parent/$_skill" -name '*.md' -type f | while IFS= read -r _f; do
                ap_rewrite_call_sites "$_f" "$AP_LAUNCHER"
            done
        fi
    done

    say ""
    say "Recording the shared Python runtime globally..."
    ap_write_global_runtime

    # The global skills are shared with the other adapter, so the ownership
    # registry has to exist here too.  Without it a global uninstall reads an
    # empty owner list and removes the shared skill the other adapter needs.
    say ""
    say "Recording skill ownership globally..."
    write_ownership "$(ap_home_fs)"

    say ""
    say "Global install complete."
    say ""
    say "Next steps:"
    say "  Codex will discover skills in $GLOBAL_DIR/skills/"
    say "  Use: \$advanced-planning phase <goal>"
    exit 0
fi

# ---------------------------------------------------------------------------
# Project install
# ---------------------------------------------------------------------------
AGENTS_DIR="$PROJECT_DIR/.agents"
AP_DIR="$PROJECT_DIR/.advanced-plans"

# Self-install detection
PROJECT_REAL="$(cd "$PROJECT_DIR" 2>/dev/null && pwd || echo "$PROJECT_DIR")"
PROJECT_GIT_TOP="$(cd "$PROJECT_DIR" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null || echo "")"
REPO_GIT_TOP="$(cd "$REPO_ROOT" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null || echo "")"
if [ -n "$PROJECT_GIT_TOP" ] && [ -n "$REPO_GIT_TOP" ] && [ "$PROJECT_GIT_TOP" = "$REPO_GIT_TOP" ]; then
    SELF_INSTALL=true
    say "Self-install detected: project is the source repo root"
fi

say "Installing Advanced Planning System for Codex"
say "  repo:    $REPO_ROOT"
say "  project: $PROJECT_DIR"
say "  target:  $AGENTS_DIR/skills/"
if [ "$DRY_RUN" = true ]; then
    say "  mode:    DRY RUN (no files written)"
fi
say ""

# Create target directories
do_mkdir "$AGENTS_DIR/skills"

# ---------------------------------------------------------------------------
# Shared Python runtime - OUTSIDE any scaffold guard
# ---------------------------------------------------------------------------
say "Recording the shared Python runtime..."
do_mkdir "$AP_DIR/bin"
do_cp "$REPO_ROOT/platforms/python/ap_launcher.py" "$AP_DIR/bin/ap.py"
if [ "$DRY_RUN" = false ]; then
    # Convert to a path Windows Python can open
    # cygpath -m: Git Bash/cygwin -> C:/Users/...
    # WSL: /mnt/c/... -> C:/... via sed
    if command -v cygpath >/dev/null 2>&1; then
        AP_SOURCE_ROOT="$(cygpath -m "$REPO_ROOT")"
    elif echo "$REPO_ROOT" | grep -q "^/mnt/[a-zA-Z]/"; then
        # WSL path: /mnt/c/... -> C:/...
        _drive="$(echo "$REPO_ROOT" | sed 's|^/mnt/\([a-zA-Z]\)/.*|\1|')"
        _rest="$(echo "$REPO_ROOT" | sed 's|^/mnt/[a-zA-Z]/||')"
        AP_SOURCE_ROOT="${_drive}:/${_rest}"
    else
        AP_SOURCE_ROOT="$REPO_ROOT"
    fi
    AP_VERSION="$(tr -d '[:space:]' < "$REPO_ROOT/VERSION" 2>/dev/null || echo unknown)"
    AP_STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo unknown)"
    cat > "$AP_DIR/runtime.json" <<RUNTIMEEOF
{
  "schema_version": 1,
  "source_root": "$AP_SOURCE_ROOT",
  "version": "$AP_VERSION",
  "written_by": "setup/codex/install.sh",
  "written_at": "$AP_STAMP"
}
RUNTIMEEOF
    say "  + .advanced-plans/runtime.json -> $AP_SOURCE_ROOT"
    say "  + .advanced-plans/bin/ap.py"
else
    echo "  [dry-run] write $AP_DIR/runtime.json recording $REPO_ROOT"
    echo "  [dry-run] copy $AP_DIR/bin/ap.py"
fi

# ---------------------------------------------------------------------------
# .advanced-plans/ scaffold - idempotent skip if data already exists
# ---------------------------------------------------------------------------
if [ -d "$AP_DIR" ] && [ -f "$AP_DIR/PLANNING.md" ]; then
    say "Preserving existing planning data at $AP_DIR - skipping scaffold"
else
    say "Creating .advanced-plans/ scaffold..."
    do_mkdir "$AP_DIR/phases"
    do_mkdir "$AP_DIR/specs"
    do_mkdir "$AP_DIR/state"
    do_mkdir "$AP_DIR/logs"

    if [ "$DRY_RUN" = false ]; then
        if [ ! -f "$AP_DIR/PLANNING.md" ]; then
            cat > "$AP_DIR/PLANNING.md" <<'PLANEOF'
---
programme: ""
status: not_started
last_updated: ""
current_phase: ""
current_loop: ""
gate_status: ""
next_action: "Run $advanced-planning phase <goal> to create the first phase plan"
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
        if [ ! -f "$AP_DIR/README.md" ]; then
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
    else
        echo "  [dry-run] create .advanced-plans/ scaffold"
    fi
fi

# ---------------------------------------------------------------------------
# Install shared routing skill
# ---------------------------------------------------------------------------
say "Installing shared routing skill..."
_src="$REPO_ROOT/platforms/shared/agent-skills/advanced-planning"
_dst_parent="$AGENTS_DIR/skills"
_collision_result=0
check_collision "$_src" "$_dst_parent/advanced-planning" "advanced-planning" || _collision_result=$?
if [ $_collision_result -eq 0 ]; then
    do_cp "$_src" "$_dst_parent/"
    say "  + skills/advanced-planning/"
elif [ $_collision_result -eq 1 ]; then
    exit 1
fi
# _collision_result == 2 means identical, already reported

# ---------------------------------------------------------------------------
# Install approved core skills
# ---------------------------------------------------------------------------
say "Installing approved core skills..."
for _skill in $APPROVED_SKILLS; do
    _src="$REPO_ROOT/core/skills/$_skill"
    if [ ! -d "$_src" ]; then
        echo "WARNING: core/skills/$_skill not found - skipping" >&2
        continue
    fi
    _collision_result=0
    check_collision "$_src" "$_dst_parent/$_skill" "$_skill" || _collision_result=$?
    if [ $_collision_result -eq 0 ]; then
        do_cp "$_src" "$_dst_parent/"
        say "  + skills/$_skill/"
    elif [ $_collision_result -eq 1 ]; then
        exit 1
    fi
done

# ---------------------------------------------------------------------------
# Merge AGENTS.md
# ---------------------------------------------------------------------------
say "Merging AGENTS.md..."
merge_agents_md "$PROJECT_DIR"

# ---------------------------------------------------------------------------
# Write ownership metadata
# ---------------------------------------------------------------------------
say "Recording skill ownership..."
write_ownership "$PROJECT_DIR"

say ""
say "Installation complete."
say ""
say "Next steps:"
say "  1. cd $PROJECT_DIR"
say "  2. Start a new Codex session (skills are discovered on session start)"
say "  3. Use: \$advanced-planning phase <goal>"
say ""
say "See platforms/codex/README.md for full documentation."
