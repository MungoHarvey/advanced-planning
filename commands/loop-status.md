---
description: "Show current planning state: active phase, loop, todo progress, and last handoff. Reads CLAUDE.md and the active plan file. Use at session start to orient, or any time you need a quick status check."
allowed-tools: Read
---

# Loop Status

Read `CLAUDE.md` and the active plan file. Report the following concisely:

## Current State
- Phase and loop name
- Loop status (pending / in_progress / completed / blocked)
- Todos: list each with current status and outcome

## Last Handoff
Show the done / failed / next fields from the last completed loop.

## Remaining Work
List all loops in the active plan with their status (pending / in_progress / completed).
Show how many remain.

## Next Action
State exactly what should happen next to advance the plan.

Keep the output brief — this is a status check, not a report.

$ARGUMENTS
