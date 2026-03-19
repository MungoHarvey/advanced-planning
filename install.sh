#!/usr/bin/env bash
# advanced-planning installer
# Copies planning system files into a Claude Code project or user environment.
#
# Usage:
#   ./install.sh              — install into current directory's .claude/
#   ./install.sh --global     — install commands globally into ~/.claude/commands/
#   ./install.sh --project /path/to/project  — install into a specific project

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="project"
PROJECT_DIR="$(pwd)"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --global)
      MODE="global"
      shift
      ;;
    --project)
      PROJECT_DIR="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: ./install.sh [--global] [--project /path/to/project]"
      echo ""
      echo "  (no args)           Install into .claude/ in the current directory"
      echo "  --global            Install commands globally into ~/.claude/commands/"
      echo "  --project <path>    Install into .claude/ in the specified project"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

echo "Advanced Planning Installer"
echo "==========================="

if [[ "$MODE" == "global" ]]; then
  # Global install — commands only (skills and agents stay in project scope)
  TARGET_COMMANDS="$HOME/.claude/commands"
  mkdir -p "$TARGET_COMMANDS"
  echo "Installing commands globally → $TARGET_COMMANDS"
  cp -v "$SCRIPT_DIR/commands/"*.md "$TARGET_COMMANDS/"
  echo ""
  echo "✓ Commands installed globally. Available as /next-loop, /new-phase, /new-loop, /loop-status in all projects."
  echo ""
  echo "Note: Skills and agents must still be installed per-project."
  echo "Run without --global inside a project directory to complete setup."

else
  # Project install
  CLAUDE_DIR="$PROJECT_DIR/.claude"

  echo "Installing into project: $PROJECT_DIR"
  echo ""

  # Commands
  TARGET_COMMANDS="$CLAUDE_DIR/commands"
  mkdir -p "$TARGET_COMMANDS"
  echo "→ commands/ to $TARGET_COMMANDS"
  cp -v "$SCRIPT_DIR/commands/"*.md "$TARGET_COMMANDS/"
  echo ""

  # Skills
  TARGET_SKILLS="$CLAUDE_DIR/skills"
  mkdir -p "$TARGET_SKILLS"
  echo "→ skills/ to $TARGET_SKILLS"
  cp -rv "$SCRIPT_DIR/skills/phase-plan-creator" "$TARGET_SKILLS/"
  cp -rv "$SCRIPT_DIR/skills/ralph-loop-planner" "$TARGET_SKILLS/"
  echo ""

  # Agents
  TARGET_AGENTS="$CLAUDE_DIR/agents"
  mkdir -p "$TARGET_AGENTS"
  echo "→ agents/ to $TARGET_AGENTS"
  cp -v "$SCRIPT_DIR/agents/"*.md "$TARGET_AGENTS/"
  echo ""

  # Plans directory (empty, ready to use)
  mkdir -p "$CLAUDE_DIR/plans"
  echo "→ Created $CLAUDE_DIR/plans/ (empty, ready for phase plans)"
  echo ""

  echo "✓ Installation complete."
  echo ""
  echo "Next steps:"
  echo "  1. Add the Planning State section to your project's CLAUDE.md"
  echo "     (see references/claude-md-convention.md for the template)"
  echo "  2. Run /new-phase in Claude Code to create your first phase plan"
  echo "  3. Run /new-loop to decompose it into executable iterations"
fi
