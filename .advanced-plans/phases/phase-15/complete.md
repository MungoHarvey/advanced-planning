---
phase: 15
title: "Automation-Surface Audit"
status: passed
gate_verdict_ref: .advanced-plans/gate-verdicts/phase-15-attempt-1-phase-goals-agent.json
anchor_sha: bd9de6a
end_sha: 36efe6e
commit_count: 16
loop_count: 5
created: 2026-06-09T18:40:00Z
---

## Goals met
- PLANS-INDEX.md shows no completed loop with a `**pending**` status row (042-046, 055-058 corrected) — `664c786`, `.advanced-plans/PLANS-INDEX.md`
- master-plan.md carries an explicit HISTORICAL/SUPERSEDED marker (no longer asserts a 4-phase programme) — `664c786`, `.advanced-plans/master-plan.md`
- Cross-phase stale state archived at the boundary via next-loop.md Step 3a + regression test — `664c786`, `platforms/claude-code/commands/next-loop.md`
- CI path-audit passes clean and fails on a planted token; legitimate `.claude/` refs do not trip it — `4873cf2`, `platforms/python/path_audit.py` + `ci.yml` job 4
- /sync-plans re-renders the PLANS-INDEX entry from the spec with no manual edit (drift-kill demo) — `4be9657`, `platforms/claude-code/commands/sync-plans.md`
- /next-loop --full populates a stub loop's todos/skills/agents in one invocation (Step 3c) — `56fc571`, `platforms/claude-code/commands/next-loop.md`
- docs/gate-override-policy.md defines permitted conditions, required history.jsonl record, and authoriser; no schema change needed — `ca77089`, `docs/gate-override-policy.md`
- codex version-coupling guard test added (capture-contract, not version-pinned) — `ca77089`, `platforms/python/tests/test_codex_gate_live.py` (`TestCaptureContractVersionGuard`)
- Full suite green (366), AST NONE, LOCKED schema docs + gate-verdict.schema.json byte-unchanged, v0.15.0 cut — `ca77089`, `VERSION` + `CHANGELOG.md`
- Every friction-log entry closed by this phase struck through with a resolution note — `664c786`..`ca77089`, `docs/tool-friction-log.md`

## Deferred
- Path-constants-not-inlined refactor — deferred; the CI path-audit captures most of its safety value without the repo-wide churn — `.advanced-plans/phases/phase-15/plan.md` (## Scope)
- Worker-layer missing-skill preflight (execution.log warning) — deferred; the plan layer already emits `MISSING:` — `.advanced-plans/phases/phase-15/plan.md` (## Scope)

## Opened
- Same-session follow-on: /run-gate now closes the phase out on a current-phase pass (Step 10.4) and /next-phase detects an already-closed phase (Step 1a) — removes the "gated but not closed" seam — `b9838ab`, `CLAUDE.md` decision log
- Two worker-tooling friction signals logged: Windows-absolute-path bash redirects create mangled junk files; workers self-commit despite "do not commit" — `ca77089`, `docs/tool-friction-log.md`
- Machine-global `~/.claude/commands/` copies are stale vs source (the run-gate/next-phase closeout improvements are not reflected there) — operator-refresh decision, intentionally out of scope
