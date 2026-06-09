---
programme: "Advanced Planning Framework"
status: in_progress
last_updated: 2026-06-09

current_phase: 14
current_loop: null
gate_status: ready_for_gate
released: v0.13.0
next_action: "Phase 14 loops 055-058 ALL COMPLETE. Codex gate + self-heal installed to runtime; proven via 343 tests + a witnessed worktree-isolated self-heal exercise (main untouched); codex double-block parser fix applied (real codex output now yields backend:codex). v0.14.0 staged (VERSION/CHANGELOG/CLAUDE.md). Run /next-phase (or /run-gate) for the Phase 14 gate — codex should write a backend:codex verdict for phase-14-attempt-1. Then /phase-compact + tag v0.14.0."

active_branches:
  - branch: main
    phase: 14
    session: primary

phases:
  complete: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
  pending: [14]
  failed: []

state_files:
  ready: .advanced-plans/state/loop-ready.json
  complete: .advanced-plans/state/loop-complete.json
  history: .advanced-plans/state/history.jsonl

notes: |
  Phase 13 — Self-Correcting Gate (loops 051-054): complete, gate PASSED attempt 1
  (code-review-agent + phase-goals-agent both pass), released as v0.13.0. Bounded
  triage->safety->fix->re-gate remediation loop in /next-phase --auto, with the
  anti-gate-gaming safety spine (diff allowlist, frozen criteria, full
  criteria_outcomes). Post-gate fix folded in: validate_regateverdict_criteria_outcomes
  now parses the schema-compliant criteria_outcomes array (300 tests, AST NONE).
  Phase 14 not yet planned.
---

# PLANNING.md — Live Programme Dashboard

This file is the machine-readable dashboard for the Advanced Planning Framework programme.
An agent starting cold can read the frontmatter above (roughly 15 lines) to know the
current phase, loop, gate state, and recommended next action.

**For directory layout and slash command reference, see [README.md](./README.md).**

---

## What to do next

All 5 Phase 9 loops are complete. Gate review attempt 1 **FAILED** (both
agents) on a self-inflicted double-prefix path corruption in 4 command
files, introduced by Loop 036's substitution pass. The corruption and the
secondary findings have been remediated in-place. Re-run `/run-gate` for
attempt 2.

---

## Phase 9 Progress

Phase 9 — `.advanced-plans/` Restructure decomposes into 5 loops:

| Loop | Task | Status |
|---|---|---|
| ralph-loop-032 | Skeleton + Preconditions | completed |
| ralph-loop-033 | File Migration | completed |
| ralph-loop-034 | Command Rewrites + Phase 8 Absorption | completed |
| ralph-loop-035 | Hooks + Permissions + Python + Install | completed |
| ralph-loop-036 | Docs + Tests + Backfill + Audit | completed (gate-1 remediated) |

Loop file: `.advanced-plans/phases/phase-9/loops.md`
Gate verdicts: `.advanced-plans/gate-verdicts/phase-9-attempt-1-*.json`
