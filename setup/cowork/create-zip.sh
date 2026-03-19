#!/bin/sh
# create-zip.sh
#
# Packages the Advanced Planning System into a self-contained zip file
# ready to drop into Claude Cowork.
#
# Usage:
#   sh setup/cowork/create-zip.sh
#   sh setup/cowork/create-zip.sh --output /path/to/output.zip
#
# What the zip contains:
#   advanced-planning/
#     core/            ← platform-agnostic schemas, skills, agents
#     platforms/cowork/ ← Cowork routing skill, agent prompts, checkpoint.sh
#
# Drop the resulting zip into Claude Cowork and it will appear as a
# mounted folder. Claude can then use the skills and agent prompts directly.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
OUTPUT="${1:-}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
DEFAULT_OUTPUT="${SCRIPT_DIR}/advanced-planning-cowork-${TIMESTAMP}.zip"

# Parse --output flag
while [ $# -gt 0 ]; do
    case "$1" in
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        --output=*)
            OUTPUT="${1#--output=}"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

OUTPUT="${OUTPUT:-$DEFAULT_OUTPUT}"

echo "=== Advanced Planning — Cowork Package Builder ==="
echo "Source: $SCRIPT_DIR"
echo "Output: $OUTPUT"
echo ""

# Verify source structure
for dir in core/skills core/schemas core/agents platforms/cowork; do
    if [ ! -d "$SCRIPT_DIR/$dir" ]; then
        echo "ERROR: expected directory not found: $SCRIPT_DIR/$dir"
        echo "Run this script from the advanced-planning repo root, or check your installation."
        exit 1
    fi
done

# Build the zip
cd "$SCRIPT_DIR"

zip -r "$OUTPUT" \
    core/ \
    platforms/cowork/ \
    -x "**/__pycache__/*" \
    -x "**/*.pyc" \
    -x "**/state/snapshots/*" \
    -x "**/.DS_Store" \
    -x "**/Thumbs.db"

echo ""
echo "Package created: $OUTPUT"
echo ""
echo "File size: $(du -sh "$OUTPUT" | cut -f1)"
echo ""
echo "=== Next steps ==="
echo "1. Open Claude Cowork"
echo "2. Click 'Select folder' and choose the extracted advanced-planning/ folder"
echo "   (or unzip to a convenient location first)"
echo "3. Start a new session — Claude will find the SKILL.md routing file automatically"
echo "4. Say: 'start a new planning session' to begin"
echo ""
echo "See setup/cowork/README.md for full setup instructions."
