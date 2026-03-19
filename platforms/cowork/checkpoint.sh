#!/bin/sh
# checkpoint.sh — Snapshot-based checkpoint utility for the Cowork planning adapter
#
# Replaces git checkpoints in environments without git (e.g. Cowork sandboxed VMs).
# Snapshots the plans/ and state/ directories to state/snapshots/{label}-{timestamp}/
#
# Usage:
#   sh checkpoint.sh save [label]     — save a named snapshot
#   sh checkpoint.sh restore <stamp>  — restore a snapshot by timestamp prefix
#   sh checkpoint.sh list             — list all available snapshots
#
# POSIX sh compatible — no bash-specific syntax used.

set -e

# ── Locate workspace root (directory containing this script) ──────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$SCRIPT_DIR"

STATE_DIR="$WORKSPACE/state"
SNAPSHOTS_DIR="$STATE_DIR/snapshots"
PLANS_DIR="$WORKSPACE/plans"

# ── Helpers ───────────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
checkpoint.sh — Planning snapshot utility

Usage:
  sh checkpoint.sh save [label]     Save current plans/ and state/ to a snapshot
  sh checkpoint.sh restore <stamp>  Restore from snapshot matching timestamp stamp
  sh checkpoint.sh list             List all available snapshots

Examples:
  sh checkpoint.sh save before-loop-009
  sh checkpoint.sh save complete-ralph-loop-009
  sh checkpoint.sh restore 20240315-143022
  sh checkpoint.sh list
EOF
}

timestamp() {
    date +%Y%m%d-%H%M%S
}

# ── Commands ──────────────────────────────────────────────────────────────────

cmd_save() {
    LABEL="${1:-snapshot}"
    STAMP="$(timestamp)"
    SNAP_NAME="${LABEL}-${STAMP}"
    SNAP_PATH="$SNAPSHOTS_DIR/$SNAP_NAME"

    # Ensure snapshot directory exists
    mkdir -p "$SNAP_PATH"

    # Snapshot plans/ if it exists
    PLANS_COUNT=0
    if [ -d "$PLANS_DIR" ]; then
        cp -r "$PLANS_DIR" "$SNAP_PATH/plans"
        PLANS_COUNT="$(find "$SNAP_PATH/plans" -type f | wc -l | tr -d ' ')"
    fi

    # Snapshot state/ files (excluding the snapshots subdirectory to avoid recursion)
    STATE_COUNT=0
    if [ -d "$STATE_DIR" ]; then
        mkdir -p "$SNAP_PATH/state"
        # Copy individual files from state/ (not the snapshots/ subdirectory)
        for f in "$STATE_DIR"/*; do
            [ -f "$f" ] && cp "$f" "$SNAP_PATH/state/"
        done
        STATE_COUNT="$(find "$SNAP_PATH/state" -type f | wc -l | tr -d ' ')"
    fi

    # Write a manifest
    cat > "$SNAP_PATH/manifest.txt" <<MANIFEST
snapshot: $SNAP_NAME
label:    $LABEL
saved_at: $STAMP
plans:    $PLANS_COUNT files
state:    $STATE_COUNT files
MANIFEST

    echo "Saved: $SNAP_NAME"
    echo "  plans/ : $PLANS_COUNT files"
    echo "  state/ : $STATE_COUNT files"
    echo "  path   : $SNAP_PATH"
}

cmd_restore() {
    STAMP="${1:-}"
    if [ -z "$STAMP" ]; then
        echo "Error: restore requires a timestamp argument." >&2
        echo "Run 'sh checkpoint.sh list' to see available snapshots." >&2
        exit 1
    fi

    # Find snapshot directory matching the stamp prefix
    MATCH=""
    for d in "$SNAPSHOTS_DIR"/*/; do
        [ -d "$d" ] || continue
        NAME="$(basename "$d")"
        case "$NAME" in
            *"$STAMP"*) MATCH="$d" ;;
        esac
    done

    if [ -z "$MATCH" ]; then
        echo "Error: no snapshot found matching '$STAMP'." >&2
        echo "Run 'sh checkpoint.sh list' to see available snapshots." >&2
        exit 1
    fi

    echo "Restoring from: $(basename "$MATCH")"

    # Restore plans/
    if [ -d "$MATCH/plans" ]; then
        rm -rf "$PLANS_DIR"
        cp -r "$MATCH/plans" "$PLANS_DIR"
        PLANS_COUNT="$(find "$PLANS_DIR" -type f | wc -l | tr -d ' ')"
        echo "  Restored plans/ : $PLANS_COUNT files"
    fi

    # Restore state/ files (preserve the snapshots/ subdirectory)
    if [ -d "$MATCH/state" ]; then
        for f in "$MATCH/state"/*; do
            [ -f "$f" ] && cp "$f" "$STATE_DIR/"
        done
        STATE_COUNT="$(find "$MATCH/state" -type f | wc -l | tr -d ' ')"
        echo "  Restored state/ : $STATE_COUNT files"
    fi

    echo "Done. Restored to snapshot: $(basename "$MATCH")"
}

cmd_list() {
    if [ ! -d "$SNAPSHOTS_DIR" ]; then
        echo "No snapshots found. (state/snapshots/ does not exist)"
        return
    fi

    COUNT=0
    for d in "$SNAPSHOTS_DIR"/*/; do
        [ -d "$d" ] || continue
        NAME="$(basename "$d")"
        MANIFEST_FILE="$d/manifest.txt"
        if [ -f "$MANIFEST_FILE" ]; then
            # Print label and timestamp from manifest
            SAVED="$(grep '^saved_at:' "$MANIFEST_FILE" | sed 's/saved_at: *//')"
            PLANS="$(grep '^plans:' "$MANIFEST_FILE" | sed 's/plans: *//')"
            STATE="$(grep '^state:' "$MANIFEST_FILE" | sed 's/state: *//')"
            printf "  %-50s  saved=%s  plans=%s  state=%s\n" "$NAME" "$SAVED" "$PLANS" "$STATE"
        else
            printf "  %s\n" "$NAME"
        fi
        COUNT=$((COUNT + 1))
    done

    if [ "$COUNT" -eq 0 ]; then
        echo "No snapshots found."
    else
        echo ""
        echo "$COUNT snapshot(s) total."
    fi
}

# ── Dispatch ──────────────────────────────────────────────────────────────────

COMMAND="${1:-}"

case "$COMMAND" in
    save)
        shift
        cmd_save "$@"
        ;;
    restore)
        shift
        cmd_restore "$@"
        ;;
    list)
        cmd_list
        ;;
    help|--help|-h|"")
        usage
        ;;
    *)
        echo "Error: unknown command '$COMMAND'" >&2
        echo "" >&2
        usage >&2
        exit 1
        ;;
esac
