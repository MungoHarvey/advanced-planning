---
description: Show the current state of all ralph loops in the active phase — which todos are pending, in-progress, or done, and what comes next. For a historical synthesis of what was accomplished, use /progress-report instead.
allowed-tools: Read, Glob
---

# /loop-status

Print a concise current-state snapshot for all ralph loops in the active plan.

**Scope:** live status of pending and completed work. For historical synthesis of what was
accomplished across loops and phases, use `/progress-report`.

## Steps

### 1. Find plan files

```
Glob(".advanced-plans/phases/*/loops.md")
```

Read `.advanced-plans/PLANNING.md` to identify the current phase, then focus on that phase's
loops file. If PLANNING.md is absent, read all loops files found.

### 2. For each loop, extract

- `name` and `task_name` from frontmatter
- Todo counts: pending / in_progress / completed / cancelled
- `handoff_summary.done`, `.failed`, `.needed`
- Dependencies section from markdown body (if present)

### 3. Print status table

```
Phase [N] Loop Status
─────────────────────────────────────────────────────────────
Loop                      | Todos            | State
─────────────────────────────────────────────────────────────
ralph-loop-001            | 4/4 complete     | Done
  Task: Schema Definitions|                  |
  Done: All 4 schema docs created in core/schemas/.

ralph-loop-002            | 2/6 complete     | In progress
  Task: Planning Skills   |                  |
  Done: phase-plan-creator and ralph-loop-planner migrated.
  Failed: —
  Needed: Migrate plan-todos, plan-skill-identification, plan-subagent-identification.

ralph-loop-003            | 0/5 complete     | Pending
  Task: Agent Roles       |                  |
  Depends on: loop-001, loop-004
─────────────────────────────────────────────────────────────
Next action: run /next-loop to continue ralph-loop-002
```

### 4. Final line

- If all loops complete: `All loops complete. Phase plan finished.`
- If a loop is blocked: `Loop NNN blocked — [dependency] must complete first.`
- Otherwise: `Run /next-loop to continue [loop-name].`

## Usage

```
/loop-status
```

No arguments required. Reads from `.advanced-plans/phases/` automatically.
