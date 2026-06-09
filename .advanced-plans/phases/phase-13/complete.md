---
phase: 13
title: "Self-Correcting Gate (Gate-Remediation Loop)"
status: passed
gate_verdict_ref: .advanced-plans/gate-verdicts/phase-13-attempt-1-phase-goals-agent.json
anchor_sha: 7936b34
end_sha: f988a71
commit_count: 18
loop_count: 4
created: 2026-06-09T09:40:00Z
---

## Goals met
- `triage_findings` (remediate.py) routes loops_to_revert→structural, critical+file/line→localized, else→unfixable; AST NONE — 21306ff
- `test_remediate.py` covers structural/localized/unfixable/warning-ignored/empty/multi-agent/conflict (19 tests) — 21306ff
- `inject_failure_context` writes phase-N/retry-context.json sidecar and no longer injects loops.md frontmatter; regression asserted — 21306ff
- `gate-reviewer.md` Re-Gate Isolation Rule: no retry-context/gate-verdicts/prior-verdict reads, evaluate frozen criteria, emit all criteria_outcomes — 489f2dc
- `/next-phase --auto` cycle count from history.jsonl gate_fail events; bound 2 → versioned-retry+STOP from pre-remediation snapshot — ce7199f
- Remediation Safety: diff-allowlist breach→escalate, criteria-frozen.md SHA-256 hash-checked before each re-gate, missing criterion→escalate — ce7199f
- Git-State Policy: staged allowlist (no git add -A), transient-file exclusion, pre-remediation SHA recorded, dirty-tree preflight escalates — ce7199f
- Composition Rules: --force/--skip-gate skip remediation; failing re-run loop hits loop-fail STOP; contradictory findings→escalate; passed_after_remediation flag — ce7199f
- Without --auto, gate-fail behaviour is byte-for-byte today's behaviour (regression trace) — d73ae37
- VERSION 0.13.0, CHANGELOG [0.13.0] section, CLAUDE.md Phase 13 decision-log entry — 8ddd4a9
- 300 tests pass, AST zero-dep NONE (11 files), LOCKED files byte-unchanged — e9d34d0

## Deferred
- Gating --auto advance on passed_after_remediation (human sign-off before building on a repaired phase) — deferred to follow-on
- Structured findings[].location (file/line/loop) + per-finding confidence in the verdict schema — deferred to a schema evolution
- Cross-phase remediation (a fail in phase N reaching into phase N-1) — out of scope

## Opened
- `validate_regateverdict_criteria_outcomes` parsed criteria_outcomes as a dict, not the schema array (gate finding) — fixed e9d34d0, +4 array-form tests
