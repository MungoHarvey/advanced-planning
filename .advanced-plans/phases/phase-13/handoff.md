---
phase: 13
title: "Self-Correcting Gate (Gate-Remediation Loop)"
status: passed
created: 2026-06-09T09:40:32Z
complete_ref: .advanced-plans/phases/phase-13/complete.md
plan_ref: .advanced-plans/phases/phase-13/plan.md
loops_ref: .advanced-plans/phases/phase-13/loops.md
gate_verdict_refs:
  - .advanced-plans/gate-verdicts/phase-13-attempt-1-code-review-agent.json
  - .advanced-plans/gate-verdicts/phase-13-attempt-1-phase-goals-agent.json
token_ceiling: 1500
---

## What was done & why
- `triage_findings` (remediate.py) routes loops_to_revert->structural, critical+file/line->localized, else->unfixable; AST NONE -- 21306ff
- `test_remediate.py` covers structural/localized/unfixable/warning-ignored/empty/multi-agent/conflict (19 tests) -- 21306ff
- `inject_failure_context` writes phase-N/retry-context.json sidecar and no longer injects loops.md frontmatter; regression asserted -- 21306ff
- `gate-reviewer.md` Re-Gate Isolation Rule: no retry-context/gate-verdicts/prior-verdict reads, evaluate frozen criteria, emit all criteria_outcomes -- 489f2dc
- `/next-phase --auto` cycle count from history.jsonl gate_fail events; bound 2 -> versioned-retry+STOP from pre-remediation snapshot -- ce7199f
- Remediation Safety: diff-allowlist breach->escalate, criteria-frozen.md SHA-256 hash-checked before each re-gate, missing criterion->escalate -- ce7199f
- Git-State Policy: staged allowlist (no git add -A), transient-file exclusion, pre-remediation SHA recorded, dirty-tree preflight escalates -- ce7199f
- Composition Rules: --force/--skip-gate skip remediation; failing re-run loop hits loop-fail STOP; contradictory findings->escalate; passed_after_remediation...
- Without --auto, gate-fail behaviour is byte-for-byte today's behaviour (regression trace) -- d73ae37
- VERSION 0.13.0, CHANGELOG [0.13.0] section, CLAUDE.md Phase 13 decision-log entry -- 8ddd4a9
- 300 tests pass, AST zero-dep NONE (11 files), LOCKED files byte-unchanged -- e9d34d0

## Outcomes
- `triage_findings` (remediate.py) routes loops_to_revert->structural, critical+file/line->localized, else->unfixable; AST NONE -- 21306ff
- `test_remediate.py` covers structural/localized/unfixable/warning-ignored/empty/multi-agent/conflict (19 tests) -- 21306ff
- `inject_failure_context` writes phase-N/retry-context.json sidecar and no longer injects loops.md frontmatter; regression asserted -- 21306ff
- `gate-reviewer.md` Re-Gate Isolation Rule: no retry-context/gate-verdicts/prior-verdict reads, evaluate frozen criteria, emit all criteria_outcomes -- 489f2dc
- `/next-phase --auto` cycle count from history.jsonl gate_fail events; bound 2 -> versioned-retry+STOP from pre-remediation snapshot -- ce7199f
- Remediation Safety: diff-allowlist breach->escalate, criteria-frozen.md SHA-256 hash-checked before each re-gate, missing criterion->escalate -- ce7199f
- Git-State Policy: staged allowlist (no git add -A), transient-file exclusion, pre-remediation SHA recorded, dirty-tree preflight escalates -- ce7199f
- Composition Rules: --force/--skip-gate skip remediation; failing re-run loop hits loop-fail STOP; contradictory findings->escalate; passed_after_remediation...
- Without --auto, gate-fail behaviour is byte-for-byte today's behaviour (regression trace) -- d73ae37
- VERSION 0.13.0, CHANGELOG [0.13.0] section, CLAUDE.md Phase 13 decision-log entry -- 8ddd4a9
- 300 tests pass, AST zero-dep NONE (11 files), LOCKED files byte-unchanged -- e9d34d0

## Errors & issues encountered
- `validate_regateverdict_criteria_outcomes` parsed criteria_outcomes as a dict, not the schema array (gate finding) -- fixed e9d34d0, +4 array-form tests

## Files touched (pointers, not contents)
- edited: ``platforms/python/remediate.py`` -- Triage helper (zero-dep, tested)
- edited: ``platforms/python/tests/test_remediate.py`` -- Triage tests
- edited: ``platforms/python/versioning.py`` -- Failure-context channel retarget
- edited: ``platforms/python/tests/test_versioning.py`` -- Versioning tests (retarget regression)
- edited: ``core/state/gate-failure-context.schema.json`` -- Failure-context schema wording
- edited: ``core/agents/gate-reviewer.md`` -- Gate isolation rule
- edited: ``platforms/claude-code/commands/next-phase.md`` -- Remediation controller
- edited: ``VERSION`, `CHANGELOG.md`` -- Version + changelog
- edited: ``CLAUDE.md`` -- Phase 13 decision-log entry

## Gate review
Attempt 1 pass at confidence 95 . -> full verdict: .advanced-plans/gate-verdicts/phase-13-attempt-1-phase-goals-agent.json

## Skills & methods used
- `python` -- `remediate.py` + tests, `versioning.py` retarget preserving zero-dep.
- `schema-design` -- the `gate-failure-context.schema.json` wording + the isolation-rule contract.
- `command-rewriting` -- the `/next-phase` controller (the bounded loop + safety/git/composition).
- `verification-before-completion` -- the controller trace/predicate tests + release gate.

## Resume pointers
- Plans: .advanced-plans/phases/phase-13/plan.md / .advanced-plans/phases/phase-13/loops.md - Spec: .advanced-plans/specs/2026-06-08-self-correcting-gate-design.md - Next: Start phase-14
