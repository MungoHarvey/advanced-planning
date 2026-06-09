---
phase: 14
title: "Install & Exercise Codex Gate + Self-Heal in Runtime"
status: passed
created: 2026-06-09T14:24:18Z
complete_ref: .advanced-plans/phases/phase-14/complete.md
plan_ref: .advanced-plans/phases/phase-14/plan.md
loops_ref: .advanced-plans/phases/phase-14/loops.md
gate_verdict_refs:
  - .advanced-plans/gate-verdicts/phase-14-attempt-1-code-review-agent.json
  - .advanced-plans/gate-verdicts/phase-14-attempt-1-phase-goals-agent.json
token_ceiling: 1500
---

## What was done & why
- Runtime commands installed byte-identical: run-gate (codex refs) + next-phase (46 remediation refs) -- `6826550`, `.claude/commands/`
- codex-reviewer parity copy present; `core/agents/codex-reviewer.md` path resolves -- `6826550`, `.claude/agents/codex-reviewer.md`
- `test_codex_gate_live.py` proves real-fixture `backend:codex` parse + degrade path -- `9d127e1`, `platforms/python/tests/test_codex_gate_live.py`
- Sandboxed self-heal integration test: synthetic fail -> triage -> allowlist-breach escalation, no real edits -- `7b49f82`, `platforms/python/tests/test_self_h...
- `remediate` + `remediation_controller` import/run cleanly from repo root -- `7b49f82` (loop-057 reachability smoke)
- Witnessed worktree self-heal emitted `gate_remediation` + `passed_after_remediation`, main pristine (20->20) -- `452c396`, `.advanced-plans/phases/phase-14/e...
- Phase-level codex live run: `backend:codex` verdict written for phase-14-attempt-1 -- `d4aefc4`, `.advanced-plans/gate-verdicts/phase-14-attempt-1-codex.json`
- `CONTRIBUTING.md` runtime-drift note + explicit `cp` re-sync commands -- `6826550`, `CONTRIBUTING.md`
- v0.14.0 cut: VERSION + CHANGELOG `[0.14.0]` + CLAUDE.md Phase 14 decision log -- `452c396`
- Full suite 343 pass, AST zero-dep NONE, 4 LOCKED files byte-unchanged -- `d4aefc4`

## Outcomes
- Runtime commands installed byte-identical: run-gate (codex refs) + next-phase (46 remediation refs) -- `6826550`, `.claude/commands/`
- codex-reviewer parity copy present; `core/agents/codex-reviewer.md` path resolves -- `6826550`, `.claude/agents/codex-reviewer.md`
- `test_codex_gate_live.py` proves real-fixture `backend:codex` parse + degrade path -- `9d127e1`, `platforms/python/tests/test_codex_gate_live.py`
- Sandboxed self-heal integration test: synthetic fail -> triage -> allowlist-breach escalation, no real edits -- `7b49f82`, `platforms/python/tests/test_self_h...
- `remediate` + `remediation_controller` import/run cleanly from repo root -- `7b49f82` (loop-057 reachability smoke)
- Witnessed worktree self-heal emitted `gate_remediation` + `passed_after_remediation`, main pristine (20->20) -- `452c396`, `.advanced-plans/phases/phase-14/e...
- Phase-level codex live run: `backend:codex` verdict written for phase-14-attempt-1 -- `d4aefc4`, `.advanced-plans/gate-verdicts/phase-14-attempt-1-codex.json`
- `CONTRIBUTING.md` runtime-drift note + explicit `cp` re-sync commands -- `6826550`, `CONTRIBUTING.md`
- v0.14.0 cut: VERSION + CHANGELOG `[0.14.0]` + CLAUDE.md Phase 14 decision log -- `452c396`
- Full suite 343 pass, AST zero-dep NONE, 4 LOCKED files byte-unchanged -- `d4aefc4`

## Errors & issues encountered
- Documented-override path exercised: a gate may pass with a recorded codex-dissent override when codex's fail is a read-only-sandbox/isolation false-negative --
- (+1 more observations -- see complete.md ## Opened)

## Files touched (pointers, not contents)
- edited: ``.claude/commands/run-gate.md`` -- Refreshed run-gate command
- edited: ``.claude/commands/next-phase.md`` -- Refreshed next-phase command
- edited: ``.claude/agents/codex-reviewer.md`` -- Installed codex-reviewer (parity copy)
- edited: ``platforms/python/tests/test_codex_gate_live.py`` -- Codex gate live test + fixture
- edited: ``platforms/python/tests/`` -- Self-heal sandbox integration test
- edited: `loop handoff + `.advanced-plans/state/history.jsonl`` -- Witnessed exercise evidence
- edited: ``CONTRIBUTING.md`` -- Runtime drift note
- edited: ``VERSION`, `CHANGELOG.md`, `CLAUDE.md`` -- Version + changelog + decision log

## Gate review
Attempt 1 pass at confidence 93 . -> full verdict: .advanced-plans/gate-verdicts/phase-14-attempt-1-phase-goals-agent.json

## Skills & methods used
- `command-rewriting` -- / file-sync: faithful refresh of the runtime command bodies.
- `verification-before-completion` -- the tests + preflight + witnessed exercise are the heart of
- `schema-design` -- confirming codex verdicts validate against `gate-verdict.schema.json`.

## Resume pointers
- Plans: .advanced-plans/phases/phase-14/plan.md / .advanced-plans/phases/phase-14/loops.md - Spec: .advanced-plans/specs/2026-06-09-phase-14-install-exercise-codex-self-heal-design.md - Next: Start phase-15
