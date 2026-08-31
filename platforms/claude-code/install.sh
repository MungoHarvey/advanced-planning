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

install_skill() {
    # install_skill SRC DEST NAME - put one core skill at DEST.
    #
    # `ln -sf SRC DEST` where DEST already exists as a real directory does not
    # replace it: it creates DEST/basename(SRC) *inside* it and exits 0. So did
    # the `cp -r` fallback. Installing twice therefore produced
    # .claude/skills/<name>/<name> for every skill while reporting a clean
    # "Symlinked" both times. Worse, on a host where ln really does symlink,
    # the second install resolves through the first link and writes that nested
    # copy into core/skills/ in the source repository. -n makes ln treat an
    # existing symlink as a file rather than following it.
    #
    # The message is verified rather than assumed. MSYS ln on Windows silently
    # copies and exits 0, so "Symlinked" was printed for a plain copy - a claim
    # about the machine that nothing had read back off it. The line now names
    # what is actually on disk.
    _src="$1"
    _dst="$2"
    _name="$3"

    if [ -L "$_dst" ]; then
        # A link someone put there before: safe to repoint.
        rm -f "$_dst"
    elif [ -d "$_dst" ]; then
        # A real directory - a previous copy-mode install, or the user's own.
        # Refusing outright would break re-installing on every host where
        # symlinks degrade to copies, which is most Windows machines. So
        # compare, and refuse only a genuine divergence.
        # Captured through `if`, not as a bare statement: `set -e` is in force
        # at the top of this script and would abort on diff's non-zero exit
        # before $? was ever read, making the installer exit 1 having printed
        # no reason at all. Measured - that is exactly what the first version
        # of this guard did.
        # --strip-trailing-cr because this repo's .gitattributes checks the
        # source out CRLF on Windows, and any LF-writing tool touching an
        # installed copy would otherwise make every line of it "differ" and
        # refuse a re-install for a reason the user cannot act on. Measured:
        # rewriting one installed SKILL.md with sed reported 1,151c1,151.
        # install_audit already normalises EOL before judging drift; this
        # agrees with it rather than inventing a second answer.
        if diff -r -q --strip-trailing-cr "$_src" "$_dst" >/dev/null 2>&1; then
            _rc=0
        else
            _rc=$?
        fi
        if [ $_rc -eq 0 ]; then
            echo "    - unchanged $_name"
            return 0
        elif [ $_rc -eq 1 ]; then
            echo "ERROR: $_dst exists as a real directory whose contents differ from" >&2
            echo "  $_src" >&2
            echo "  Refusing to overwrite it or to nest a copy inside it. Remove or rename it." >&2
            exit 1
        else
            # diff exits >=2 for "trouble" - it could not compare them at all.
            # That is not evidence of either answer, so do not claim one.
            echo "ERROR: could not compare $_src with $_dst (diff exited $_rc)." >&2
            echo "  Refusing to install over a directory whose state is unknown." >&2
            exit 1
        fi
    elif [ -e "$_dst" ]; then
        echo "ERROR: $_dst exists as a regular file. Remove or rename it before installing." >&2
        exit 1
    fi

    if ln -sfn "$_src" "$_dst" 2>/dev/null && [ -L "$_dst" ]; then
        echo "    ✓ Symlinked $_name"
        return 0
    fi

    # ln either failed or "succeeded" without producing a link. Either way the
    # destination may now hold a partial copy, so clear it before copying.
    if [ ! -L "$_dst" ] && [ -d "$_dst" ]; then
        rm -rf "$_dst"
    fi
    cp -r "$_src" "$_dst"
    echo "    ✓ Copied $_name"
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
        # ${skill_dir%/} strips the trailing slash the glob leaves on, so the
        # link target reads back cleanly and cp does not copy into a directory.
        install_skill "${skill_dir%/}" "$CLAUDE_DIR/skills/$skill_name" "$skill_name"
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
    elif [ -n "${HOME:-}" ]; then
        printf '%s' "$HOME"
    else
        # Neither is set. Returning the empty string here is not harmless: the
        # callers append "/.claude" and "/.advanced-plans" and mkdir -p the
        # result, so an empty home installs at the filesystem root -- the only
        # path in this mechanism that writes outside the profile it was asked
        # to install into. Under `set -e` this non-zero status propagates out
        # of the command substitution and stops the installer, which is the
        # intended outcome. Masked on Windows, where Git Bash repopulates HOME
        # during startup; reachable on any POSIX shell, which is what CI runs.
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
        # Neither is set. Returning the empty string here is not harmless: the
        # callers append "/.claude" and "/.advanced-plans" and mkdir -p the
        # result, so an empty home installs at the filesystem root -- the only
        # path in this mechanism that writes outside the profile it was asked
        # to install into. Under `set -e` this non-zero status propagates out
        # of the command substitution and stops the installer, which is the
        # intended outcome. Masked on Windows, where Git Bash repopulates HOME
        # during startup; reachable on any POSIX shell, which is what CI runs.
        echo "install.sh: neither USERPROFILE nor HOME is set; refusing to resolve the global home to the filesystem root." >&2
        exit 1
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
