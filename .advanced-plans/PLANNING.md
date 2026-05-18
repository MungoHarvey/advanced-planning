---
programme: "Advanced Planning Framework"
status: in_progress
last_updated: 2026-05-18

current_phase: 9
current_loop: ralph-loop-036
gate_status: due
next_action: "/run-gate"

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
  Phase 9 — .advanced-plans/ Restructure: all 5 loops (032-036) complete.
  035 narrowed hook allowlists + permissions to .advanced-plans/** and updated
  Python path constants + install scripts. 036 rewrote CLAUDE.md, re-pointed all
  core/ + platforms/ docs, updated pytest fixtures (72 passing), backfilled
  PLANS-INDEX Phases 6-7. Grep audit clean; smoke test + git-history checks pass.
  Phase 9 awaiting gate review (/run-gate).
---

# PLANNING.md — Live Programme Dashboard

This file is the machine-readable dashboard for the Advanced Planning Framework programme.
An agent starting cold can read the frontmatter above (roughly 15 lines) to know the
current phase, loop, gate state, and recommended next action.

**For directory layout and slash command reference, see [README.md](./README.md).**

---

## What to do next

Run `/next-loop` to execute the next pending loop in Phase 9.

Current loop just completed: `ralph-loop-034` (Command Rewrites + Phase 8 Absorption)
Next loop: `ralph-loop-035` (Hooks + Permissions + Python + Install)

---

## Phase 9 Progress

Phase 9 — `.advanced-plans/` Restructure decomposes into 5 loops:

| Loop | Task | Status |
|---|---|---|
| ralph-loop-032 | Skeleton + Preconditions | completed |
| ralph-loop-033 | File Migration | completed |
| ralph-loop-034 | Command Rewrites + Phase 8 Absorption | completed |
| ralph-loop-035 | Hooks + Permissions + Python + Install | pending |
| ralph-loop-036 | Docs + Tests + Backfill + Audit | pending |

Loop file: `.advanced-plans/phases/phase-9/loops.md`
