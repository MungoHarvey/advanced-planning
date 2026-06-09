---
programme: "Advanced Planning Framework"
status: in_progress
last_updated: 2026-06-09

current_phase: 15
current_loop: ralph-loop-061
gate_status: pending
released: v0.14.0
next_action: "Phase 15 (Automation-Surface Audit) PLANNED — 5 loops (059-063), anchor bd9de6a, target v0.15.0. Scope: doc-hygiene + wire state-archiving (059); CI path-convention audit (060); /sync-plans (061); /next-loop --full (062); gate-override policy + codex version-coupling guard + release (063). Deferred: path-constants refactor, worker-layer missing-skill preflight. Next: /next-loop to begin loop-059, or /next-loop --auto to chain. NOTE: still-unpushed — operator to run `git push origin main --follow-tags` (env has no SSH key)."

active_branches:
  - branch: main
    phase: 15
    session: primary

phases:
  complete: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
  pending: []
  failed: []

state_files:
  ready: .advanced-plans/state/loop-ready.json
  complete: .advanced-plans/state/loop-complete.json
  history: .advanced-plans/state/history.jsonl

notes: |
  Phase 14 — Install & Exercise Codex Gate + Self-Heal in Runtime (loops 055-058):
  complete, gate PASSED attempt 1. code-review-agent + phase-goals-agent both PASS
  (conf 95/93); codex produced a backend:codex verdict (self-evidencing criterion met),
  recorded fail as a documented override (read-only-sandbox/isolation false-negative,
  no deliverable defect). First real codex run surfaced + fixed 4 run-gate
  codex-invocation bugs. Witnessed self-heal ran in a discarded worktree (main pristine).
  343 tests, AST NONE, 4 LOCKED files byte-unchanged. Released v0.14.0; tags v0.13.0 +
  v0.14.0 cut locally on gate-pass commits (push pending — no SSH key in env).
  Phase 15 not yet planned.
---

# PLANNING.md — Live Programme Dashboard

This file is the machine-readable dashboard for the Advanced Planning Framework programme.
An agent starting cold can read the frontmatter above (roughly 15 lines) to know the
current phase, loop, gate state, and recommended next action.

**For directory layout and slash command reference, see [README.md](./README.md).**

---

## What to do next

Phase 14 is **closed** — gate passed (attempt 1, documented codex override),
compaction artefacts written, v0.14.0 released. Tags `v0.13.0` and `v0.14.0`
are cut locally on their gate-pass commits; `main` (+ tags) still needs
`git push origin main --follow-tags` by the operator (this environment has no
SSH key). Phase 15 is **not yet planned** — run `/new-phase` or
`/plan-and-phase` to scope it, then `/decompose-phase` + `/next-loop`.

---

## Phase 14 Progress

Phase 14 — Install & Exercise Codex Gate + Self-Heal in Runtime, 4 loops:

| Loop | Task | Status |
|---|---|---|
| ralph-loop-055 | Runtime install (byte-identical commands + codex-reviewer) | completed |
| ralph-loop-056 | Codex gate proof (live fixture + degrade test) | completed |
| ralph-loop-057 | Self-heal proof (sandboxed integration test) | completed |
| ralph-loop-058 | Witnessed worktree self-heal + v0.14.0 release | completed |

Loop file: `.advanced-plans/phases/phase-14/loops.md`
Gate verdicts: `.advanced-plans/gate-verdicts/phase-14-attempt-1-*.json`
Compaction: `.advanced-plans/phases/phase-14/complete.md` + `handoff.md`
