---
description: "Load and execute the next pending ralph loop from the active plan. Reads Planning State from CLAUDE.md, loads the loop frontmatter and todos, syncs to TodoWrite, and begins execution. No arguments needed."
allowed-tools: Read, Edit, Bash(git *)
---

# Next Loop

Read `CLAUDE.md` and locate the `## Planning State` section.

1. **Identify the current loop** from `Current loop:` field
2. **Read the active plan file** from `Active plan:` field
3. **Load the loop's frontmatter**: todos, prompt, max_iterations, on_max_iterations
4. **Inject the last handoff** from CLAUDE.md into the prompt context block
5. **Sync todos to TodoWrite**: map each todo to `{id, content → outcome, status: pending, priority: high}`
6. **Git checkpoint**: `git add -A && git commit -m "checkpoint: before [loop-name]"`
7. **Begin execution** of the loop prompt, working through todos in order

On completion:
- Write the handoff block to the loop's frontmatter (done / failed / next)
- Update `## Planning State` in CLAUDE.md: advance loop, copy handoff
- Git checkpoint: `git add -A && git commit -m "complete: [loop-name] — [one-line summary]"`
- Report results against the loop's success criteria

$ARGUMENTS
