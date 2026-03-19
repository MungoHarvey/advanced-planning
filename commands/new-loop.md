---
description: "Decompose a phase plan into ralph loop iterations. Reads the active phase plan from .claude/plans/ and invokes ralph-loop-planner. Optionally pass a phase plan path as argument. Output saved to .claude/plans/phase-N-ralph-loops.md."
allowed-tools: Read, Write, Edit
---

# New Loop Plan

Read the active phase plan. If an argument is provided, use that path instead:

$ARGUMENTS

Invoke the `ralph-loop-planner` skill with the phase plan content.

After generating the ralph loops:
1. Save to `.claude/plans/phase-[N]-ralph-loops.md`
2. Update `## Planning State` in `CLAUDE.md`:
   - Set `Active plan` to the new ralph loops file
   - Set `Current loop` to the first loop name (e.g., `ralph-loop-001`)
   - Set `Loop status` to `pending`
3. Confirm the file was written, show path, and list the loops generated with their task names
