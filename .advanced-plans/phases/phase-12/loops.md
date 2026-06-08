# Phase 12 — Ralph Loops

Decomposition of `.advanced-plans/phases/phase-12/plan.md` (Codex Cross-Model
Second-Opinion Gate Reviewer) into 4 executable loops. Design:
`.advanced-plans/specs/2026-06-08-phase-12-codex-gate-reviewer-design.md`.

---

```yaml
---
name: "ralph-loop-047"
task_name: "Schema + Tested Gate Core"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "gate-verdict.schema.json extended with optional backend enum field; legacy phase-7/gate-verdicts/ deleted; codex_gate.py created (4 functions, stdlib only, AST NONE); test_codex_gate.py written with all 20 paths including 2 CRITICAL regressions; 209/209 tests pass."
  failed: ""
  needed: "loop-048: write core/agents/codex-reviewer.md contract; loop-049: wire Codex into run-gate.md."

todos:
  - id: "loop-047-1"
    content: "Add optional `backend` field (enum codex|subagent) to gate-verdict.schema.json"
    skill: "schema-design"
    agent: "NA"
    outcome: "core/state/gate-verdict.schema.json has an optional `backend` property with enum [\"codex\",\"subagent\"]; file still parses (json.loads succeeds); additionalProperties stays false"
    status: completed
    priority: high
  - id: "loop-047-2"
    content: "Delete the legacy nested .advanced-plans/phases/phase-7/gate-verdicts/ directory"
    skill: "NA"
    agent: "NA"
    outcome: "No .advanced-plans/phases/phase-7/gate-verdicts/ directory exists; the only verdict directory is the flat .advanced-plans/gate-verdicts/"
    status: completed
    priority: high
  - id: "loop-047-3"
    content: "Create platforms/python/codex_gate.py with extract_verdict_json, validate_verdict, extract_and_validate, aggregate_verdicts (stdlib only)"
    skill: "test-driven-development"
    agent: "NA"
    outcome: "platforms/python/codex_gate.py defines all four functions; `python -m platforms.python.ast_check` reports NONE (imports within the allow-set: json, re, pathlib)"
    status: completed
    priority: high
  - id: "loop-047-4"
    content: "Write platforms/python/tests/test_codex_gate.py covering all 20 eng-review paths including the 2 CRITICAL aggregation regressions"
    skill: "test-driven-development"
    agent: "NA"
    outcome: "test_codex_gate.py covers: 5 extraction cases, 6 validation cases (incl. extra-field tolerance), 3 extract_and_validate cases (incl. identity-overfit reject), 6 aggregate_verdicts cases (incl. all-pass and any-fail CRITICAL regressions); pytest passes"
    status: completed
    priority: high
  - id: "loop-047-5"
    content: "Run full pytest suite and the AST zero-dep check"
    skill: "NA"
    agent: "NA"
    outcome: "All tests pass (pre-existing + new); `python -m platforms.python.ast_check` reports NONE"
    status: completed
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Land the schema change and the tested, zero-dependency gate core that owns the failure-prone Codex stdout handling.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-047"

  ## Success criteria
  - [ ] gate-verdict.schema.json has optional `backend` enum [codex,subagent]; still parses
  - [ ] legacy .advanced-plans/phases/phase-7/gate-verdicts/ removed
  - [ ] codex_gate.py defines extract_verdict_json / validate_verdict / extract_and_validate / aggregate_verdicts
  - [ ] validate_verdict checks required+types+verdict-enum+agent=="codex" and TOLERATES unknown extra fields
  - [ ] test_codex_gate.py covers all 20 paths incl. 2 CRITICAL regressions; pytest passes
  - [ ] AST zero-dep check reports NONE

  ## Required skills
  - `schema-design`: the backend field + enum
  - `test-driven-development`: codex_gate.py and its tests

  ## Inputs
  - Design: .advanced-plans/specs/2026-06-08-phase-12-codex-gate-reviewer-design.md
  - Test plan: the eng-review coverage diagram (20 paths) in the design doc / project test-plan artifact
  - Constraint source: core/constraints.json (zero-dep allow-set)

  ## Expected outputs
  - core/state/gate-verdict.schema.json (edited)
  - platforms/python/codex_gate.py (new)
  - platforms/python/tests/test_codex_gate.py (new)

  ## Constraints
  - Zero external dependencies — stdlib only (json, re, pathlib). No jsonschema.
  - Validator is lenient: reject only real problems (missing required, wrong type, bad verdict enum, wrong agent, identity overfit); tolerate unknown extra fields (backend, evaluated_by).
  - extract_and_validate must reject identity-overfit (codex copying the sample phase/attempt) and return a skip reason rather than raising.
  - Do not touch run-gate.md in this loop.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-047 — schema backend field + tested codex_gate core"
  2. Update handoff_summary (done / failed / needed)
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Land the `backend` schema field, remove the stray verdict directory, and build the tested, zero-dependency `codex_gate.py` that owns extraction, validation, and aggregation. This loop de-risks the crux (Codex stdout parsing) before any wiring depends on it.

## Success Criteria
- ✓ Schema `backend` enum present; parses: `python -c "import json; json.load(open('core/state/gate-verdict.schema.json'))"`
- ✓ Stray dir gone: `ls .advanced-plans/phases/phase-7/gate-verdicts/` fails
- ✓ Four functions present in codex_gate.py
- ✓ AST NONE: `python -m platforms.python.ast_check`
- ✓ pytest green incl. 2 CRITICAL regressions

## Skills Required
### Broad (from phase plan):
- `python`: build the gate core preserving zero-dep
- `schema-design`: the backend field
### Specific (refined for this loop):
- `test-driven-development`: write tests alongside the four functions
### Discovered:
- None

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| backend field | core/state/gate-verdict.schema.json | JSON |
| Gate core | platforms/python/codex_gate.py | Python |
| Tests | platforms/python/tests/test_codex_gate.py | Python (pytest) |

## Dependencies
### Must Complete Before
- None — first loop in phase
### Blocked By
- Nothing
### Parallelisable
- ralph-loop-048 (contract doc touches only core/agents/, no overlap)

## Complexity
**Scope**: Medium
**Estimated effort**: 2–3 hours
**Key challenges**:
1. Robust fenced-block extraction across malformed inputs without over-engineering
2. Lenient-but-correct validator boundary (reject real problems, tolerate extras)

---

```yaml
---
name: "ralph-loop-048"
task_name: "Codex Reviewer Contract"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-048-1"
    content: "Write core/agents/codex-reviewer.md: the platform-agnostic Codex reviewer contract"
    skill: "schema-design"
    agent: "NA"
    outcome: "core/agents/codex-reviewer.md exists with mandatory role sections and states: untrusted-artefact rule, per-criterion file/line evidence requirement, fenced-json-only output, isolation rule (must not read gate-verdicts/), agent==\"codex\""
    status: pending
    priority: high
  - id: "loop-048-2"
    content: "Verify core purity of the new contract doc"
    skill: "NA"
    agent: "NA"
    outcome: "grep finds no .claude/ or other platform-specific paths in core/agents/codex-reviewer.md"
    status: pending
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Write the portable Codex reviewer contract that run-gate's invocation will reference, modeled on core/agents/gate-reviewer.md.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-048"

  ## Success criteria
  - [ ] core/agents/codex-reviewer.md exists, beside gate-reviewer.md
  - [ ] States untrusted-artefact rule + file/line evidence requirement + fenced-json-only + isolation rule + agent:"codex"
  - [ ] Mirrors phase-goals-agent's success-criteria check (read plan + loop outputs, verify each criterion)
  - [ ] No .claude/ or platform-specific paths (core purity)

  ## Required skills
  - `schema-design`: structure the contract doc

  ## Inputs
  - Model: core/agents/gate-reviewer.md, platforms/claude-code/agents/phase-goals-agent.md
  - Design: the "Relationship to /codex" + premises sections of the design spec

  ## Expected outputs
  - core/agents/codex-reviewer.md (new)

  ## Constraints
  - This file is the CONTRACT only. No `codex exec` invocation here (that lives in run-gate.md, loop 049).
  - Core purity: no platform paths, no gstack references.
  - Emit-one-fenced-json-block must be stated explicitly.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-048 — codex-reviewer contract"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Write the platform-agnostic Codex reviewer contract in `core/agents/` (where role definitions live, beside `gate-reviewer.md`). Codex is a Bash subprocess, not an Agent-tool agent, so it gets a contract here, not a file under `platforms/claude-code/agents/`.

## Success Criteria
- ✓ File exists with mandatory role sections
- ✓ Untrusted-artefact rule, evidence requirement, fenced-json-only, isolation rule all stated
- ✓ Core purity: `grep -r "\.claude/" core/agents/codex-reviewer.md` empty

## Skills Required
### Broad (from phase plan):
- `schema-design`: the contract doc
### Specific (refined for this loop):
- None beyond schema-design
### Discovered:
- None

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Codex reviewer contract | core/agents/codex-reviewer.md | Markdown |

## Dependencies
### Must Complete Before
- None (pure docs)
### Blocked By
- Nothing
### Parallelisable
- ralph-loop-047 (no file overlap)

## Complexity
**Scope**: Low
**Estimated effort**: 1 hour
**Key challenges**:
1. Stating the prompt-injection / untrusted-artefact rule crisply enough to be actionable

---

```yaml
---
name: "ralph-loop-049"
task_name: "run-gate Wiring (Parallel + Conflict UX)"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-049-1"
    content: "Add Codex preflight to run-gate.md (which codex + local auth check; no gstack helpers)"
    skill: "NA"
    agent: "NA"
    outcome: "run-gate.md has a preflight step using `which codex` + a local auth check (auth.json / $CODEX_API_KEY / $OPENAI_API_KEY); no reference to gstack-codex-probe or ~/.claude/skills/gstack"
    status: pending
    priority: high
  - id: "loop-049-2"
    content: "Wire the execution ordering: code-review-agent first, then codex(background) parallel with phase-goals(foreground), joined on subagent return; amend the sequential-only note"
    skill: "NA"
    agent: "NA"
    outcome: "run-gate.md Step 7 documents the ordering and the join; the 'never concurrently' note is amended to: same-backend subagents stay sequential, the Codex backend writes a distinct file and runs parallel to one subagent"
    status: pending
    priority: high
  - id: "loop-049-3"
    content: "Wire the verdict write + aggregation: main thread parses Codex stdout via codex_gate, writes codex.json on success or codex.raw.txt on skip, then calls aggregate_verdicts"
    skill: "NA"
    agent: "NA"
    outcome: "run-gate.md captures Codex stdout, calls codex_gate.extract_and_validate, writes .advanced-plans/gate-verdicts/phase-N-attempt-M-codex.json (agent:codex, backend:codex) on success or ...codex.raw.txt on skip, and replaces the Step-9 prose with a call to aggregate_verdicts"
    status: pending
    priority: high
  - id: "loop-049-4"
    content: "Add conflict UX to Steps 9-11 and the degrade event to history.jsonl"
    skill: "NA"
    agent: "NA"
    outcome: "run-gate.md: on any fail OR a codex-vs-subagent disagreement, surfaces findings and asks the user via AskUserQuestion unless an auto-remediation policy is configured; appends a gate_codex_skipped (or equivalent degrade) event to history.jsonl whenever Codex contributes no verdict"
    status: pending
    priority: high
  - id: "loop-049-5"
    content: "Validate background-process join feasibility; if unreliable, document the codex-first sequential-blind fallback"
    skill: "NA"
    agent: "NA"
    outcome: "run-gate.md states the join mechanism; if background-join proves unreliable, the sequential-blind fallback (codex first to completion, subagent forbidden from reading gate-verdicts/) is documented as the alternative"
    status: pending
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Wire Codex into /run-gate: preflight, the parallel-independent execution pair, the verdict write, and the conflict UX, all calling the tested codex_gate helper.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-049"

  ## Success criteria
  - [ ] Preflight (which codex + local auth, no gstack) present
  - [ ] Ordering: code-review first, then codex(bg) || phase-goals(fg), join; sequential-only note amended
  - [ ] codex.json written on success (agent:codex, backend:codex); codex.raw.txt on skip
  - [ ] Step 9 calls aggregate_verdicts (no hand-derived prose aggregation)
  - [ ] Conflict UX (Steps 9-11) + history.jsonl degrade event
  - [ ] Join mechanism stated; sequential-blind fallback documented if needed

  ## Required skills
  - None (command-doc editing)

  ## Inputs
  - platforms/claude-code/commands/run-gate.md (current)
  - platforms/python/codex_gate.py (from loop 047)
  - core/agents/codex-reviewer.md (from loop 048)
  - design spec: the "B+" recommended approach + build order

  ## Expected outputs
  - platforms/claude-code/commands/run-gate.md (edited)

  ## Constraints
  - Reuse the existing Step-7 CONTINGENCY (main-thread-writes-on-behalf) mechanism.
  - Degrade gracefully: if preflight fails or extraction fails, drop Codex and proceed on the two in-house agents — never block the gate on Codex absence.
  - Do NOT auto-revert on conflict — surface and ask (unless auto-remediation configured).
  - The Codex prompt must hand it the schema path + a real example verdict and the untrusted-artefact rule from core/agents/codex-reviewer.md.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-049 — run-gate codex wiring + conflict UX"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Edit `run-gate.md` to add Codex as a parallel, independent reviewer of the phase-goals check: preflight, ordering, verdict write via `codex_gate`, and the fail/conflict user-decision UX. Depends on loops 047 (helper) and 048 (contract).

## Success Criteria
- ✓ Preflight present; no gstack coupling (`grep -i gstack run-gate.md` empty)
- ✓ Ordering + join documented; sequential-only note amended
- ✓ Verdict write + aggregate_verdicts call present
- ✓ Conflict UX + degrade event present

## Skills Required
### Broad (from phase plan):
- `command-rewriting`: the run-gate edits
### Specific (refined for this loop):
- None (no matching specific skill; editing is direct)
### Discovered:
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Current command | platforms/claude-code/commands/run-gate.md | Markdown |
| Gate helper | platforms/python/codex_gate.py | Python |
| Contract | core/agents/codex-reviewer.md | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Wired command | platforms/claude-code/commands/run-gate.md | Markdown |

## Dependencies
### Must Complete Before
- ralph-loop-047: needs aggregate_verdicts + extract_and_validate
- ralph-loop-048: references the contract
### Blocked By
- Nothing external
### Parallelisable
- None (depends on 047 + 048)

## Complexity
**Scope**: Medium
**Estimated effort**: 2 hours
**Key challenges**:
1. Background-process join semantics in the main thread (fallback to sequential-blind if flaky)
2. Conflict UX that surfaces without auto-acting, with a clean auto-remediation hook

---

```yaml
---
name: "ralph-loop-050"
task_name: "Verification + v0.12.0 Release"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-050-1"
    content: "Degrade E2E: shadow `codex` off PATH and confirm the gate behaves as today's two-agent gate"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "With codex unavailable, a gate run produces exactly the two in-house verdict files, appends a degrade event to history.jsonl, writes no codex.json; result documented"
    status: pending
    priority: high
  - id: "loop-050-2"
    content: "Codex-present E2E: confirm a real codex run yields a valid third verdict"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "With codex available, a gate run produces a schema-valid phase-N-attempt-M-codex.json (agent:codex, backend:codex) and aggregate_verdicts ANDs all three; result documented (or explicitly noted skipped if codex unauthed in this environment)"
    status: pending
    priority: medium
  - id: "loop-050-3"
    content: "Verify zero gstack coupling across all new and edited files"
    skill: "NA"
    agent: "NA"
    outcome: "grep for 'gstack' and '~/.claude/skills/gstack' across codex_gate.py, codex-reviewer.md, run-gate.md, schema returns no matches"
    status: pending
    priority: high
  - id: "loop-050-4"
    content: "Bump VERSION to 0.12.0, add CHANGELOG [0.12.0] entry, add CLAUDE.md decision-log entry"
    skill: "NA"
    agent: "NA"
    outcome: "VERSION reads 0.12.0; CHANGELOG.md has a [0.12.0] section describing the Codex gate reviewer; CLAUDE.md decision log records the Phase 12 cross-model gate decision"
    status: pending
    priority: high
  - id: "loop-050-5"
    content: "Run full test suite + AST check; confirm LOCKED files byte-unchanged"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "All pytest passes; AST zero-dep NONE; git diff on docs/phase-complete.schema.md, docs/phase-manifest-entry.schema.md, docs/phase-handoff.schema.md, .advanced-plans/phases/phase-9/complete.md is empty"
    status: pending
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Verify the Codex gate end-to-end (degrade and present paths), confirm zero coupling, and prepare the v0.12.0 release artefacts.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-050"

  ## Success criteria
  - [ ] Degrade E2E: codex off PATH -> two-agent gate + degrade event, no codex.json
  - [ ] Codex-present E2E: valid codex.json (or documented skip if unauthed here)
  - [ ] gstack-coupling grep clean
  - [ ] VERSION 0.12.0 + CHANGELOG [0.12.0] + CLAUDE.md decision-log entry
  - [ ] Full pytest + AST NONE; LOCKED files byte-unchanged

  ## Required skills
  - `verification-before-completion`: the E2E checks and release gate

  ## Inputs
  - All Phase 12 outputs (loops 047-049)
  - LOCKED file list from the phase plan success criteria

  ## Expected outputs
  - VERSION (edited), CHANGELOG.md (edited), CLAUDE.md (decision-log entry)
  - Verification notes (in the loop handoff / commit message)

  ## Constraints
  - Tag cut is DEFERRED to gate pass (framework convention) — do not cut the tag in this loop.
  - If codex is unauthed in this environment, mark 050-2 as a documented skip, not a failure (the degrade path is the load-bearing guarantee).
  - LOCKED files must not change.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-050 — verification + v0.12.0 prepared (pre-gate)"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Prove the gate works both with and without Codex, confirm zero gstack coupling, and stage the v0.12.0 release (tag deferred to gate pass). This is the verification + release loop.

## Success Criteria
- ✓ Degrade E2E documented; ✓ present E2E documented or skipped-with-reason
- ✓ gstack grep clean; ✓ VERSION/CHANGELOG/CLAUDE.md updated
- ✓ pytest + AST NONE; LOCKED files unchanged (git diff empty)

## Skills Required
### Broad (from phase plan):
- `verification-before-completion`: E2E + release gate
### Specific (refined for this loop):
- None
### Discovered:
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Phase 12 outputs | loops 047-049 | Python + Markdown |
| Release convention | Phase 11 v0.11.0 pattern | — |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Version bump | VERSION | Text |
| Changelog entry | CHANGELOG.md | Markdown |
| Decision log | CLAUDE.md | Markdown |

## Dependencies
### Must Complete Before
- ralph-loop-047, 048, 049 (verifies their combined output)
### Blocked By
- Nothing
### Parallelisable
- None (final loop)

## Complexity
**Scope**: Medium
**Estimated effort**: 1–2 hours
**Key challenges**:
1. Exercising the degrade path cleanly (shadowing codex off PATH without breaking other tooling)
2. Keeping LOCKED files byte-unchanged through the release edits
