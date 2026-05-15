---
programme: "Advanced Planning Framework"
status: in_progress
last_updated: 2026-05-15

current_phase: 9
current_loop: ralph-loop-034
gate_status: not_due
next_action: "/next-loop"

active_branches:
  - branch: main
    phase: 9
    session: primary

phases:
  complete: [1, 2, 3, 4, 5, 6, 7, 8]
  pending: [9]
  failed: []

state_files:
  ready: .advanced-plans/state/loop-ready.json
  complete: .advanced-plans/state/loop-complete.json
  history: .advanced-plans/state/history.jsonl

notes: |
  Phase 9 — .advanced-plans/ Restructure (Loop 033 just completed).
  Loop 033 performed the full git mv migration: all phase plans, ralph-loop files,
  gate verdicts, completion artefacts, design specs, nav files, state bus files, and
  logs moved to .advanced-plans/. Old plans/, .claude/state/, .claude/logs/ directories
  removed. History verified via git log --follow. Loop 034 rewrites slash commands.
---

# PLANNING.md — Live Programme Dashboard

This file is the machine-readable dashboard for the Advanced Planning Framework programme.
An agent starting cold can read the frontmatter above (roughly 15 lines) to know the
current phase, loop, gate state, and recommended next action.

**For directory layout and slash command reference, see [README.md](./README.md).**

---

## What to do next

Run `/next-loop` to execute the next pending loop in Phase 9.

Current loop just completed: `ralph-loop-033` (File Migration)
Next loop: `ralph-loop-034` (Command Rewrites + Phase 8 Absorption)

---

## Phase 9 Progress

Phase 9 — `.advanced-plans/` Restructure decomposes into 5 loops:

| Loop | Task | Status |
|---|---|---|
| ralph-loop-032 | Skeleton + Preconditions | completed |
| ralph-loop-033 | File Migration | completed |
| ralph-loop-034 | Command Rewrites + Phase 8 Absorption | pending |
| ralph-loop-035 | Hooks + Permissions + Python + Install | pending |
| ralph-loop-036 | Docs + Tests + Backfill + Audit | pending |

Loop file: `.advanced-plans/phases/phase-9/loops.md`
