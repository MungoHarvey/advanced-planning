---
programme: "Advanced Planning Framework"
status: in_progress
last_updated: 2026-06-11

current_phase: 17
current_loop: null
gate_status: pending
released: v0.16.0
next_action: "Phase 16 CLOSED (gate passed attempt 1, operator override on the codex bootstrap-checkpoint finding -- see gate_pass event). Closed + auto-compacted via the new run-gate Step 10.4 pipeline (live proof). v0.16.0 tagged on e8843c7. Phase 17 not yet planned. Follow-ups logged: extend gate-override-policy.md with the criterion-bootstrap category; fix worker agent numbered steps that still say 'git commit' (contradicts Hard Contract); structural junk-file guard (PreToolUse hook). Operator push pending: git push origin main --follow-tags."

active_branches:
  - branch: main
    phase: 17
    session: primary

phases:
  complete: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
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

Phase 16 is **closed and compacted** — gate passed attempt 1 (code-review 95,
phase-goals 90; codex 92 FAIL on the bootstrap-checkpoint criterion, operator
override recorded on the `gate_pass` event). First codex-included gate via the
synced command surface; closeout + compaction ran automatically via the new
run-gate Step 10.4 pipeline. `v0.16.0` tagged. Phase 17 is **not yet planned**.
Operator push still pending: `git push origin main --follow-tags` (tags
v0.11/0.13/0.14/0.15/0.16 + ~85 commits). Follow-ups for Phase 17 scoping:
extend `docs/gate-override-policy.md` with the criterion-bootstrap category;
fix worker agent numbered steps that still instruct `git commit` (contradicts
the Hard Contract — code-review finding); structural junk-file guard
(PreToolUse hook).

---

## Phase 16 Progress

Phase 16 — Trust the Machinery, 5 loops:

| Loop | Task | Status |
|---|---|---|
| ralph-loop-064 | Install-sync + drift guard (live 3-layer sync) | completed |
| ralph-loop-065 | Trustworthy record (history events + Hard Contract) | completed |
| ralph-loop-066 | Loop-flow economy (fast-path + checkpoint tags) | completed |
| ralph-loop-067 | Compaction backfill — all 15 phases covered | completed |
| ralph-loop-068 | Auto-compact at close + v0.16.0 | completed |

Loop file: `.advanced-plans/phases/phase-16/loops.md`
Gate verdicts: `.advanced-plans/gate-verdicts/phase-16-attempt-1-*.json`
Compaction: `.advanced-plans/phases/phase-16/complete.md` + `handoff.md`
