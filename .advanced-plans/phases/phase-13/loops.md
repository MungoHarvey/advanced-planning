# Phase 13 — Ralph Loops

Decomposition of `.advanced-plans/phases/phase-13/plan.md` (Self-Correcting Gate) into 4
loops. Design (brainstorming + eng-review + codex):
`.advanced-plans/specs/2026-06-08-self-correcting-gate-design.md`.

---

```yaml
---
name: "ralph-loop-051"
task_name: "Triage Core + Channel Move"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "remediate.py triage_findings (19 tests, AST NONE); inject_failure_context retargeted to retry-context.json sidecar (7 tests including CRITICAL regressions); gate-failure-context.schema.json updated; all 234 tests pass."
  failed: ""
  needed: "ralph-loop-052 (gate-reviewer.md isolation rule) and ralph-loop-053 (remediation controller) can now proceed."

todos:
  - id: "loop-051-1"
    content: "Create platforms/python/remediate.py with triage_findings (stdlib only)"
    skill: "test-driven-development"
    agent: "NA"
    outcome: "remediate.py defines triage_findings(verdict) -> {structural, localized, unfixable}; routes loops_to_revert->structural, severity=='critical' finding with actionable file/line->localized, else->unfixable; ignores warning/info; AST check NONE"
    status: completed
    priority: high
  - id: "loop-051-2"
    content: "Write platforms/python/tests/test_remediate.py covering all triage routes"
    skill: "test-driven-development"
    agent: "NA"
    outcome: "test_remediate.py covers structural, localized, unfixable, warning/info-ignored, empty verdict, multi-agent union, contradictory-location conflict; pytest passes"
    status: completed
    priority: high
  - id: "loop-051-3"
    content: "Retarget inject_failure_context in versioning.py to write phase-N/retry-context.json (not loops.md frontmatter)"
    skill: "NA"
    agent: "NA"
    outcome: "inject_failure_context writes .advanced-plans/phases/phase-N/retry-context.json and does NOT inject gate_failure_context into loops.md frontmatter; conforms to gate-failure-context fields"
    status: completed
    priority: high
  - id: "loop-051-4"
    content: "Update test_versioning.py for the retarget (CRITICAL regression)"
    skill: "test-driven-development"
    agent: "NA"
    outcome: "test_versioning.py asserts retry-context.json is written AND loops.md frontmatter no longer receives gate_failure_context; all versioning tests pass"
    status: completed
    priority: high
  - id: "loop-051-5"
    content: "Update gate-failure-context.schema.json description to reference the sidecar"
    skill: "schema-design"
    agent: "NA"
    outcome: "core/state/gate-failure-context.schema.json description says the context is written to the worker-only retry-context.json sidecar, not loop frontmatter; file still parses"
    status: completed
    priority: high
  - id: "loop-051-6"
    content: "Run full pytest + AST zero-dep check"
    skill: "NA"
    agent: "NA"
    outcome: "All tests pass; python -m platforms.python.ast_check platforms/python/ --exclude tests/ --exclude examples/ reports NONE"
    status: completed
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Build the tested zero-dep triage helper and move failure context to the worker-only sidecar.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-051"

  ## Success criteria
  - [ ] remediate.py triage_findings -> {structural, localized, unfixable}, keys on severity
  - [ ] test_remediate.py covers all 7 routes; pytest passes
  - [ ] inject_failure_context writes retry-context.json sidecar, NOT loops.md frontmatter
  - [ ] test_versioning.py regression: sidecar written + no frontmatter injection
  - [ ] gate-failure-context.schema.json references the sidecar
  - [ ] AST NONE

  ## Required skills
  - `test-driven-development`: remediate.py + tests
  - `schema-design`: schema wording

  ## Inputs
  - Design spec: .advanced-plans/specs/2026-06-08-self-correcting-gate-design.md (Decisions, Remediation Safety)
  - Existing: platforms/python/versioning.py (inject_failure_context), core/state/gate-verdict.schema.json

  ## Expected outputs
  - platforms/python/remediate.py (new); platforms/python/tests/test_remediate.py (new)
  - platforms/python/versioning.py (edit); platforms/python/tests/test_versioning.py (edit)
  - core/state/gate-failure-context.schema.json (edit)

  ## Constraints
  - Zero external deps (json, re, pathlib, hashlib if needed — confirm against core/constraints.json). No jsonschema.
  - triage keys on severity=="critical" (no per-finding confidence exists); location is a freeform string.
  - Do NOT edit next-phase.md or gate-reviewer.md in this loop.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-051 — triage core + retry-context sidecar"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Build the tested, zero-dependency `triage_findings` and retarget failure context to the worker-only `retry-context.json` sidecar (out of `loops.md`, so re-gate agents can stay blind). Foundation for the controller.

## Success Criteria
- ✓ triage_findings routes verified by tests; AST NONE
- ✓ Sidecar written; frontmatter injection removed (regression test)

## Skills Required
### Broad (from phase plan): `python`, `schema-design`
### Specific: `test-driven-development` (helper + tests)
### Discovered: none

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Triage helper | platforms/python/remediate.py | Python |
| Triage tests | platforms/python/tests/test_remediate.py | Python |
| Channel retarget | platforms/python/versioning.py | Python |
| Schema wording | core/state/gate-failure-context.schema.json | JSON |

## Dependencies
### Must Complete Before: none (first loop)
### Parallelisable: ralph-loop-052 (touches only core/agents/, no overlap)

## Complexity
**Scope**: Medium · **Effort**: 2-3h
**Key challenges**: 1) lenient triage boundary (severity + freeform location); 2) the regression that proves frontmatter injection is gone.

---

```yaml
---
name: "ralph-loop-052"
task_name: "Gate Isolation Contract"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "core/agents/gate-reviewer.md gains a Re-Gate Isolation Rule section: gate agents must not read retry-context.*, gate-verdicts/, or prior verdicts; must use criteria-frozen.md (or phase plan fallback) as the criterion set; must emit criteria_outcomes for ALL criteria on every re-gate; core-pure (no .claude/ paths); CC agents inherit via their existing protocol reference."
  failed: ""
  needed: "ralph-loop-053 (remediation controller) can proceed."

todos:
  - id: "loop-052-1"
    content: "Add the isolation rule to core/agents/gate-reviewer.md"
    skill: "schema-design"
    agent: "NA"
    outcome: "gate-reviewer.md states: gate agents never read retry-context.*, gate-verdicts/, or prior verdicts; on a re-gate they evaluate the frozen criteria and MUST emit criteria_outcomes for ALL criteria (blind to failure context, not to the contract)"
    status: completed
    priority: high
  - id: "loop-052-2"
    content: "Verify core purity and CC-agent inheritance"
    skill: "NA"
    agent: "NA"
    outcome: "grep finds no .claude/ paths in core/agents/gate-reviewer.md; both platforms/claude-code/agents/{code-review,phase-goals}-agent.md still reference the core protocol so they inherit the rule (no per-agent duplication)"
    status: completed
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Add the platform-agnostic isolation rule that keeps re-gate agents blind to failure context yet bound to the original contract.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-052"

  ## Success criteria
  - [ ] gate-reviewer.md isolation rule present (no retry-context/verdicts; frozen criteria; full criteria_outcomes)
  - [ ] core purity (no .claude/ paths); CC agents inherit via their protocol reference

  ## Required skills
  - `schema-design`: structure the rule into the existing protocol doc

  ## Inputs
  - core/agents/gate-reviewer.md; platforms/claude-code/agents/{code-review,phase-goals}-agent.md
  - Design spec: Remediation Safety + Blindness decision

  ## Expected outputs
  - core/agents/gate-reviewer.md (edit)

  ## Constraints
  - Core purity: no platform paths, no gstack references.
  - Do NOT duplicate the rule into the CC agent docs — they inherit by reference.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-052 — gate-reviewer isolation rule"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Add the isolation rule to the core gate-reviewer protocol (inherited by the CC gate agents): blind to failure context and prior verdicts, but must evaluate the frozen criteria and report every one.

## Success Criteria
- ✓ Isolation rule + full-criteria_outcomes requirement stated; core-pure; inherited

## Skills Required
### Broad: `schema-design`
### Specific/Discovered: none

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Isolation rule | core/agents/gate-reviewer.md | Markdown |

## Dependencies
### Must Complete Before: none
### Parallelisable: ralph-loop-051

## Complexity
**Scope**: Low · **Effort**: ~1h
**Key challenges**: stating "blind to failure context, not to the contract" crisply enough to be enforceable.

---

```yaml
---
name: "ralph-loop-053"
task_name: "Remediation Controller"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "next-phase.md --auto gate-fail branch replaced with bounded triage->safety->fix->re-gate controller (Steps 7-AUTO-a through 7-AUTO-j); remediation_controller.py with 8 zero-dep predicate helpers added; 58 tests covering all 7 required escalation paths pass; AST NONE; 292 tests total pass; hashlib added to allow-set."
  failed: ""
  needed: "ralph-loop-054: E2E verification traces + zero gstack coupling + VERSION 0.13.0 + CHANGELOG + final gate."

todos:
  - id: "loop-053-1"
    content: "Add the bounded gate-fail remediation branch to next-phase.md --auto"
    skill: "NA"
    agent: "NA"
    outcome: "next-phase.md gate-fail branch (under --auto) computes cycles from history.jsonl gate_fail events, escalates at cycles>=2 to versioned-retry+STOP from the pre-remediation snapshot, else runs triage_findings and dispatches structural (re-run loops_to_revert) / localized (analysis-worker focused fix); sentinel is bracketed (up for gate, removed before fix) with an explicit assert-sentinel-absent before any fix"
    status: completed
    priority: high
  - id: "loop-053-2"
    content: "Add the Remediation Safety spine (diff allowlist + frozen criteria + full criteria_outcomes)"
    skill: "NA"
    agent: "NA"
    outcome: "next-phase.md: before cycle 1 writes phase-N/criteria-frozen.md (+hash); validates remediation `git diff --name-only` is a subset of the source allowlist (never plan.md/loops.md/criteria/tests/schemas/reviewer docs/verdicts) and escalates on any out-of-bounds path; asserts the live criteria hash matches before each re-gate; rejects a re-gate verdict missing any frozen criterion -> escalate"
    status: completed
    priority: high
  - id: "loop-053-3"
    content: "Add the Git-State Policy"
    skill: "NA"
    agent: "NA"
    outcome: "next-phase.md: remediation commit stages only allowlisted source paths (no git add -A); no-change detection compares allowlisted source only (excludes retry-context/history/verdicts); records pre-remediation SHA; dirty-tree preflight escalates rather than committing unrelated changes"
    status: completed
    priority: high
  - id: "loop-053-4"
    content: "Add Composition Rules + new history events"
    skill: "NA"
    agent: "NA"
    outcome: "next-phase.md: --force/--skip-gate skip remediation (documented precedence); a failing re-run loop hits the existing loop-fail STOP; contradictory findings escalate with a remediation_conflict note; gate_remediation event appended per cycle; passed_after_remediation flag set on a gate_pass that followed >=1 cycle"
    status: completed
    priority: high
  - id: "loop-053-5"
    content: "Add controller predicate/trace tests"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Tests/traces cover: cycle bound from history events; sentinel-absent assertion; diff-allowlist rejection->escalate; transient-excluded no-change->escalate; criteria-hash mismatch->escalate; re-gate verdict missing a criterion->escalate; --auto OFF -> byte-for-byte today's behavior"
    status: completed
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Wire the bounded, guard-railed remediation loop into /next-phase --auto, with the full safety spine.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-053"

  ## Success criteria
  - [ ] Bounded triage->fix->re-gate loop; cycles from history events; escalate at 2 from pre-rem snapshot
  - [ ] Diff allowlist + frozen criteria + full criteria_outcomes enforcement
  - [ ] Git-state policy (staged allowlist, transient exclusion, snapshot, dirty preflight)
  - [ ] Composition rules + gate_remediation / passed_after_remediation events
  - [ ] Controller predicate/trace tests incl. --auto-off regression

  ## Required skills
  - `command-rewriting` (direct editing); `verification-before-completion` (the controller tests)

  ## Inputs
  - platforms/claude-code/commands/next-phase.md (current Step 7 gate-fail branch)
  - platforms/python/remediate.py (triage_findings, from 051); core/agents/gate-reviewer.md (isolation, from 052)
  - versioning.py create_retry_version; hooks.json gate-review-mode behavior
  - Design spec: Control Flow + Remediation Safety + Git-State Policy + Composition Rules

  ## Expected outputs
  - platforms/claude-code/commands/next-phase.md (edit)
  - controller test/trace artifacts under platforms/python/tests/ where logic is extractable

  ## Constraints
  - Reuse create_retry_version + the existing escalation STOP; do not duplicate them.
  - The ASSERT-sentinel-absent step is mandatory (the hook blocks source writes with exit 2 otherwise).
  - Never git add -A in the remediation commit.
  - Without --auto, the branch must behave exactly as today (regression).

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-053 — remediation controller + safety + composition"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
The heart of the phase: the bounded triage→safety→fix→re-gate controller in `/next-phase --auto`, with the anti-gate-gaming spine, git-state policy, and composition rules. Depends on 051 (triage) and 052 (isolation rule).

## Success Criteria
- ✓ Loop + bound + safety + git-state + composition all present and trace/predicate-tested

## Skills Required
### Broad: `command-rewriting`
### Specific: `verification-before-completion` (controller tests)
### Discovered: none

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Remediation controller | platforms/claude-code/commands/next-phase.md | Markdown |

## Dependencies
### Must Complete Before: ralph-loop-051, ralph-loop-052
### Parallelisable: none

## Complexity
**Scope**: High · **Effort**: 3-4h
**Key challenges**: 1) the diff-allowlist + frozen-criteria enforcement (the safety spine); 2) sentinel sequencing so fixes aren't hook-blocked; 3) composing with existing --force / loop-fail / auto-chain without regressions.

---

```yaml
---
name: "ralph-loop-054"
task_name: "Verification + v0.13.0 Release"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-054-1"
    content: "E2E trace: fix->re-gate->pass happy path and bound->escalate path"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Documented trace (or harness test) showing one remediation cycle reaching a re-gate pass, and a 2-cycle-exhausted run escalating to versioned-retry+STOP from the pre-remediation snapshot"
    status: pending
    priority: high
  - id: "loop-054-2"
    content: "Verify the gate-gaming guard: an out-of-bounds remediation edit is blocked"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "A test/trace demonstrates that a remediation diff touching a forbidden path (e.g. loops.md success criteria or a test asserting the failed criterion) is rejected by the allowlist check and escalates instead of re-gating"
    status: pending
    priority: high
  - id: "loop-054-3"
    content: "Verify zero gstack coupling across new/edited files"
    skill: "NA"
    agent: "NA"
    outcome: "grep for gstack / ~/.claude/skills/gstack across remediate.py, test_remediate.py, versioning.py, gate-reviewer.md, next-phase.md, gate-failure-context.schema.json returns no matches"
    status: pending
    priority: high
  - id: "loop-054-4"
    content: "Release artefacts: VERSION 0.13.0, CHANGELOG [0.13.0], CLAUDE.md decision log"
    skill: "NA"
    agent: "NA"
    outcome: "VERSION reads 0.13.0; CHANGELOG.md has a [0.13.0] section describing the self-correcting gate (safety spine + bounded self-heal); CLAUDE.md decision log records the Phase 13 decision"
    status: pending
    priority: high
  - id: "loop-054-5"
    content: "Final gate: full pytest + AST NONE + LOCKED files unchanged"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "pytest all pass; AST zero-dep NONE; git diff empty on docs/phase-complete.schema.md, docs/phase-manifest-entry.schema.md, docs/phase-handoff.schema.md, .advanced-plans/phases/phase-9/complete.md"
    status: pending
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Prove the self-heal works (including the gate-gaming guard), confirm zero coupling, and stage v0.13.0.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-054"

  ## Success criteria
  - [ ] Fix->re-gate->pass and bound->escalate traces documented
  - [ ] Out-of-bounds remediation edit blocked by allowlist (test/trace)
  - [ ] gstack-coupling grep clean
  - [ ] VERSION 0.13.0 + CHANGELOG [0.13.0] + CLAUDE.md decision log
  - [ ] Full pytest + AST NONE; LOCKED files byte-unchanged

  ## Required skills
  - `verification-before-completion`: the E2E traces + release gate

  ## Inputs
  - All Phase 13 outputs (051-053); release convention from Phase 11/12 (tag deferred to gate pass)

  ## Expected outputs
  - VERSION, CHANGELOG.md, CLAUDE.md (edits); verification notes in handoff/commit

  ## Constraints
  - Tag cut DEFERRED to gate pass — do not cut/push a tag in this loop.
  - Do not modify LOCKED files.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-054 — verification + v0.13.0 prepared (pre-gate)"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Verify the loop end-to-end — especially that the gate-gaming guard actually blocks an out-of-bounds fix — confirm zero coupling, and stage the v0.13.0 release.

## Success Criteria
- ✓ Happy + escalate + gate-gaming-blocked traces; grep clean; release staged; suite green; LOCKED unchanged

## Skills Required
### Broad: `verification-before-completion`
### Specific/Discovered: none

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Version bump | VERSION | Text |
| Changelog | CHANGELOG.md | Markdown |
| Decision log | CLAUDE.md | Markdown |

## Dependencies
### Must Complete Before: ralph-loop-051, 052, 053
### Parallelisable: none (final loop)

## Complexity
**Scope**: Medium · **Effort**: 1-2h
**Key challenges**: 1) demonstrating the allowlist guard blocks a gaming attempt without a live full gate run; 2) keeping LOCKED files unchanged through release edits.
