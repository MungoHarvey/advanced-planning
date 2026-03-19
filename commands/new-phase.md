---
description: "Create a new phase plan. Invokes the phase-plan-creator skill with your description. Provide: project/task description, phase number or name, and any constraints. Output is saved to .claude/plans/phase-N.md and CLAUDE.md is updated."
allowed-tools: Read, Write, Edit
---

# New Phase

Invoke the `phase-plan-creator` skill with the following input:

$ARGUMENTS

After generating the phase plan:
1. Save to `.claude/plans/phase-[N].md`
2. Update `## Planning State` in `CLAUDE.md`:
   - Set `Current phase` to the new phase number
   - Set `Active plan` to the new file path
   - Set `Loop status` to `pending`
3. Confirm the file was written and show the path
