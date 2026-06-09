---
phase: 14
title: "Install & Exercise Codex Gate + Self-Heal in Runtime"
status: passed
gate_verdict_ref: .advanced-plans/gate-verdicts/phase-14-attempt-1-phase-goals-agent.json
anchor_sha: 9465e55
end_sha: d4aefc4
commit_count: 12
loop_count: 4
created: 2026-06-09T14:30:00Z
---

## Goals met
- Runtime commands installed byte-identical: run-gate (codex refs) + next-phase (46 remediation refs) — `6826550`, `.claude/commands/`
- codex-reviewer parity copy present; `core/agents/codex-reviewer.md` path resolves — `6826550`, `.claude/agents/codex-reviewer.md`
- `test_codex_gate_live.py` proves real-fixture `backend:codex` parse + degrade path — `9d127e1`, `platforms/python/tests/test_codex_gate_live.py`
- Sandboxed self-heal integration test: synthetic fail → triage → allowlist-breach escalation, no real edits — `7b49f82`, `platforms/python/tests/test_self_heal_integration.py`
- `remediate` + `remediation_controller` import/run cleanly from repo root — `7b49f82` (loop-057 reachability smoke)
- Witnessed worktree self-heal emitted `gate_remediation` + `passed_after_remediation`, main pristine (20→20) — `452c396`, `.advanced-plans/phases/phase-14/exercise-058-transcript.md`
- Phase-level codex live run: `backend:codex` verdict written for phase-14-attempt-1 — `d4aefc4`, `.advanced-plans/gate-verdicts/phase-14-attempt-1-codex.json`
- `CONTRIBUTING.md` runtime-drift note + explicit `cp` re-sync commands — `6826550`, `CONTRIBUTING.md`
- v0.14.0 cut: VERSION + CHANGELOG `[0.14.0]` + CLAUDE.md Phase 14 decision log — `452c396`
- Full suite 343 pass, AST zero-dep NONE, 4 LOCKED files byte-unchanged — `d4aefc4`

## Deferred
- (none)

## Opened
- Documented-override path exercised: a gate may pass with a recorded codex-dissent override when codex's fail is a read-only-sandbox/isolation false-negative — precedent for a future formal gate-override policy — `d4aefc4`, `history.jsonl`
- codex-cli output shape is version-coupled (multi-block `exec` transcript vs `-o` last-message); future codex upgrades should re-validate the run-gate capture path — `docs/tool-friction-log.md` (2026-06-09)
