---
phase: 11
title: "Friction Remediation & v0.x Pre-Release"
status: passed
gate_verdict_ref: .advanced-plans/gate-verdicts/phase-11-attempt-1-phase-goals-agent.json
anchor_sha: 1bb073c
end_sha: dc94b1b
commit_count: 18
loop_count: 5
created: 2026-06-10T22:50:00Z
---

## Goals met

- core/constraints.json + platforms/python/ast_check.py + CI job added; round-trip test; 189 tests pass — commit 418c88b, .advanced-plans/gate-verdicts/phase-11-attempt-1-phase-goals-agent.json
- complexity field removed from todos under .advanced-plans/phases/**; no Haiku row in CLAUDE.md; CHANGELOG.md BREAKING change documented — commit 418c88b
- core/skills/schema-design/SKILL.md and core/skills/permission-config/SKILL.md created; install script auto-includes via wildcard — commit 92d8221
- Worker preflight warns and proceeds on missing skill (WARN format in ralph-loop-worker.md); tests cover — commit 92d8221
- FALLBACK path active: run-gate.md CONTINGENCY block documents main-thread persist-on-behalf contract for phase-goals-agent Write tool upstream-block — commit f05049e
- Zero agent: ralph-loop-worker on todos; plan-subagent-identification documents NA default and Reserved Values — commit 92d8221
- docs/path-conventions.md created with canonical path map, deprecated tokens, where-to-find-what table; stale directives rewritten — commit f42c6fe
- /next-loop resume-detection: detect_mid_loop_death() in state_manager.py; IRON-RULE regression test in test_next_loop_resume.py (7 tests) — commit f42c6fe
- archive_cross_phase_state() in state_manager.py; ralph-orchestrator.md Step 0 cleanup; 9 tests cover — commit f42c6fe
- Dogfood self-install: SELF_INSTALL detection in install.sh; idempotent skip-data-scaffold; install.ps1 mirror; 5 idempotency tests; E2E Loop 046 confirmed — commit 4749964
- VERSION 0.11.0; CHANGELOG covers v0.6-v0.11; tag cut + pushed; GitHub Release published pre-release — commit dc94b1b
- 189 tests pass; AST NONE; LOCKED files byte-unchanged vs anchor — commit f05049e

## Deferred

- README.md Model Tiers table Haiku row (missed in criterion 2 strict scope) → Phase 12 sweep

## Opened

- Confirmed live during Phase 11 gate: editing phase-goals-agent.md tools field does NOT propagate to runtime tool availability — FALLBACK contract is the supported path; friction-log entry partially-resolved (upstream-blocked)
