---
programme: "Advanced Planning Framework"
status: in_progress
last_updated: 2026-06-09

current_phase: 16
current_loop: null
gate_status: pending
released: v0.14.0
next_action: "Phase 15 CLOSED (gate passed attempt 1; code-review 95, phase-goals 93). Closed out via the new /run-gate-pass progression (gate→close). Delivered: state-archiving wired into next-loop.md; CI path-convention audit; /sync-plans; /next-loop --full; gate-override-policy.md + codex guard; AND the /run-gate closeout-on-pass improvement folded in. v0.15.0 staged. Next: /phase-compact 15 to compact; tag v0.15.0; then /plan-and-phase (or /next-phase --auto) for Phase 16. Operator still to push: `git push origin main --follow-tags` (no SSH key in env)."

active_branches:
  - branch: main
    phase: 16
    session: primary

phases:
  complete: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
  pending: []
  failed: []

state_files:
  ready: .advanced-plans/state/loop-ready.json
  complete: .advanced-plans/state/loop-complete.json
  history: .advanced-plans/state/history.jsonl

notes: |
  Phase 15 — Automation-Surface Audit (loops 059-063): complete, gate PASSED attempt 1
  (code-review 95, phase-goals 93; two-agent gate, no codex this run). Delivered:
  state-archiving wired into next-loop.md Step 3a; CI path-convention audit (path_audit.py
  + ci.yml job 4); /sync-plans; /next-loop --full one-pass population; gate-override-policy.md
  + codex version-coupling guard. Follow-on (same session): /run-gate now closes the phase
  out on a current-phase pass (Step 10.4), and /next-phase detects an already-closed phase
  (Step 1a) — removes the "gated but not closed" seam. 366 tests, AST NONE, path_audit CLEAN,
  LOCKED docs + gate-verdict.schema.json byte-unchanged. v0.15.0 staged (not yet tagged).
  Phase 15 closed out via the new gate->close progression. Phase 16 not yet planned.
  Pending: /phase-compact 15; tag v0.15.0; push (operator — no SSH key in env).
---

# PLANNING.md — Live Programme Dashboard

This file is the machine-readable dashboard for the Advanced Planning Framework programme.
An agent starting cold can read the frontmatter above (roughly 15 lines) to know the
current phase, loop, gate state, and recommended next action.

**For directory layout and slash command reference, see [README.md](./README.md).**

---

## What to do next

Phase 15 is **closed** — gate passed (attempt 1; code-review 95, phase-goals 93),
and closed out via the new `/run-gate`-pass progression (gate → close). **Not yet
compacted or released externally.** Next: `/phase-compact 15` to write the cold
artefact + handoff digest, then tag `v0.15.0`. `main` (+ tags `v0.11/0.13/0.14` and
the forthcoming `v0.15.0`) still needs `git push origin main --follow-tags` by the
operator (this environment has no SSH key). Phase 16 is **not yet planned** — run
`/plan-and-phase` (or `/next-phase --auto`) to scope it.

---

## Phase 15 Progress

Phase 15 — Automation-Surface Audit, 5 loops:

| Loop | Task | Status |
|---|---|---|
| ralph-loop-059 | Doc-hygiene + wire state-archiving | completed |
| ralph-loop-060 | CI path-convention audit | completed |
| ralph-loop-061 | /sync-plans command | completed |
| ralph-loop-062 | /next-loop --full one-pass population | completed |
| ralph-loop-063 | Gate-override policy + codex guard + v0.15.0 | completed |

Follow-on (same session): `/run-gate` closeout-on-pass (Step 10.4) + `/next-phase`
already-closed detection (Step 1a) — the "gated but not closed" seam fix.

Loop file: `.advanced-plans/phases/phase-15/loops.md`
Gate verdicts: `.advanced-plans/gate-verdicts/phase-15-attempt-1-*.json`
