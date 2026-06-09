# Phase 14 — Ralph Loops

Decomposition of `.advanced-plans/phases/phase-14/plan.md` (Install & Exercise Codex Gate +
Self-Heal in Runtime) into 4 executable loops. Design spec:
`.advanced-plans/specs/2026-06-09-phase-14-install-exercise-codex-self-heal-design.md`.

---

```yaml
---
name: "ralph-loop-055"
task_name: "Runtime Install"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-055-1"
    content: "Refresh .claude/commands/run-gate.md from platforms/claude-code/commands/run-gate.md (plain copy)"
    skill: "NA"
    agent: "NA"
    outcome: ".claude/commands/run-gate.md is byte-identical to platforms/claude-code/commands/run-gate.md (diff empty); grep -c -i codex returns >0"
    status: pending
    complexity: low
    priority: high
  - id: "loop-055-2"
    content: "Refresh .claude/commands/next-phase.md from platforms/claude-code/commands/next-phase.md (plain copy)"
    skill: "NA"
    agent: "NA"
    outcome: ".claude/commands/next-phase.md is byte-identical to platforms/claude-code/commands/next-phase.md (diff empty); grep -c -i remediat returns >0"
    status: pending
    complexity: low
    priority: high
  - id: "loop-055-3"
    content: "Copy core/agents/codex-reviewer.md to .claude/agents/codex-reviewer.md for parity and confirm the path run-gate references resolves"
    skill: "NA"
    agent: "NA"
    outcome: ".claude/agents/codex-reviewer.md exists; the core/agents/codex-reviewer.md path referenced by run-gate.md resolves from repo root (file readable)"
    status: pending
    complexity: low
    priority: high
  - id: "loop-055-4"
    content: "Add a runtime-drift note to CONTRIBUTING.md: commands are copied (not symlinked) and the re-sync command"
    skill: "NA"
    agent: "NA"
    outcome: "CONTRIBUTING.md contains a section stating .claude/commands/ are copied not symlinked, with the explicit cp re-sync command from platforms/claude-code/commands/"
    status: pending
    complexity: low
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Install the codex-wired run-gate + self-heal next-phase into this repo's project .claude/ runtime and document the drift mechanism.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-055"

  ## Success criteria
  - [ ] .claude/commands/run-gate.md byte-identical to source; codex refs > 0
  - [ ] .claude/commands/next-phase.md byte-identical to source; remediation refs > 0
  - [ ] .claude/agents/codex-reviewer.md present; core/agents/ path resolves
  - [ ] CONTRIBUTING.md drift note + re-sync command present

  ## Required skills
  - None — faithful file copy + a documentation note

  ## Inputs
  - platforms/claude-code/commands/run-gate.md, next-phase.md (sources of truth)
  - core/agents/codex-reviewer.md

  ## Expected outputs
  - Refreshed .claude/commands/{run-gate,next-phase}.md; .claude/agents/codex-reviewer.md; CONTRIBUTING.md note

  ## Constraints
  - Plain copy only — no token substitution, no hand-edits to the command bodies
  - Do NOT touch user-level ~/.claude/commands/

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-055 — codex gate + self-heal installed to .claude/ runtime"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Refresh the two stale runtime command bodies from source and install the codex-reviewer parity
copy, so the gate this repo executes is finally codex- and self-heal-aware. Document the
copy-not-symlink drift mechanism so it does not recur.

## Success Criteria
- ✓ `.claude/commands/run-gate.md` byte-identical to source (`diff` empty), codex refs > 0
- ✓ `.claude/commands/next-phase.md` byte-identical to source, remediation refs > 0
- ✓ `.claude/agents/codex-reviewer.md` exists; `core/agents/codex-reviewer.md` resolves
- ✓ `CONTRIBUTING.md` drift note + re-sync command present

## Skills Required
### Broad (from phase plan): `command-rewriting`/file-sync
### Specific: none — plain copy
### Discovered: none

## Dependencies
### Must Complete Before: none (first loop)
### Blocked By: nothing

## Complexity
**Scope**: Low — file copies + one doc note
**Estimated effort**: <1 hour
**Key challenges**: 1. Faithful byte-identical copy; 2. clear drift note that survives future installs

## Rationale
F1/F2 already resolved, so this loop is mechanical. Byte-identity is checkable because install is
plain `cp -r` (no substitution). Drift note prevents silent regression.

---

```yaml
---
name: "ralph-loop-056"
task_name: "Codex Gate Proof"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-056-1"
    content: "Capture a real codex CLI stdout sample as a pytest fixture for gate-verdict extraction"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "A fixture file under platforms/python/tests/ contains real codex stdout; documented how it was produced (codex invocation recorded)"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-056-2"
    content: "Write test_codex_gate_live.py asserting extract_and_validate parses the fixture into a schema-valid verdict"
    skill: "test-driven-development"
    agent: "NA"
    outcome: "platforms/python/tests/test_codex_gate_live.py passes; asserts the verdict validates against gate-verdict.schema.json with backend=='codex'"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-056-3"
    content: "Add a degrade-path test: codex unavailable -> in-house agents proceed, gate_codex_skipped appended, no codex.json"
    skill: "test-driven-development"
    agent: "NA"
    outcome: "Test asserts the degrade branch: no codex.json written and a gate_codex_skipped event shape produced when codex preflight fails"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-056-4"
    content: "Document the codex preflight smoke (codex --version / auth) and record the local result"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Loop handoff records codex --version output (codex-cli 0.124.0) and preflight pass; smoke steps noted for reproducibility"
    status: pending
    complexity: low
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Prove the codex gate works in isolation: real codex stdout extracts/validates into a schema-valid verdict, and the degrade path is safe.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-056"

  ## Success criteria
  - [ ] Real codex stdout fixture captured + provenance documented
  - [ ] test_codex_gate_live.py passes (schema-valid verdict, backend==codex)
  - [ ] Degrade-path test passes (no codex.json; gate_codex_skipped)
  - [ ] codex preflight smoke recorded

  ## Required skills
  - `test-driven-development`: write the failing test first, then confirm extract/validate satisfies it
  - `verification-before-completion`: evidence (real codex run) over assertion

  ## Inputs
  - platforms/python/codex_gate.py (extract_and_validate, aggregate_verdicts)
  - core/state/gate-verdict.schema.json
  - codex CLI (codex-cli 0.124.0 on PATH)

  ## Expected outputs
  - platforms/python/tests/test_codex_gate_live.py + fixture

  ## Constraints
  - Zero-dependency Python (stdlib only); AST checker must stay NONE
  - Do NOT modify codex_gate.py logic — this loop tests it

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-056 — codex gate proven (live fixture + degrade test)"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Encode the codex-gate exercise as repeatable pytest: a real codex stdout fixture proves
`extract_and_validate`, and a degrade test proves graceful fallback. This is the gate-verifiable
half of the codex proof (the other half is the guaranteed live run at Phase 14's own gate).

## Success Criteria
- ✓ `test_codex_gate_live.py` passes against a real codex stdout fixture (backend==codex, schema-valid)
- ✓ Degrade-path test passes: no `codex.json`, `gate_codex_skipped` produced
- ✓ Codex preflight smoke recorded (`codex --version`)
- ✓ AST zero-dep NONE preserved

## Skills Required
### Broad (from phase plan): `verification-before-completion`, `schema-design`
### Specific: `test-driven-development` (write the assertion first)
### Discovered: none

## Dependencies
### Must Complete Before: loop-055 (run-gate installed, codex path resolvable)
### Blocked By: codex CLI availability (present: 0.124.0)

## Complexity
**Scope**: Medium — capturing a real fixture + two tests
**Estimated effort**: 1–2 hours
**Key challenges**: 1. A representative real codex stdout sample; 2. faithfully simulating the degrade branch without mocking away the real contract

## Rationale
A captured real fixture is more honest than a hand-authored one and stays regression-safe. The
degrade test guards the most important safety property: codex absence never blocks the gate.

---

```yaml
---
name: "ralph-loop-057"
task_name: "Self-Heal Proof"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-057-1"
    content: "Write a sandboxed synthetic-fail integration test driving remediation_controller triage to an allowlist-breach escalation"
    skill: "test-driven-development"
    agent: "NA"
    outcome: "A pytest in platforms/python/tests/ stages a synthetic gate fail and asserts triage routes correctly AND a diff-allowlist breach escalates rather than commits"
    status: pending
    complexity: high
    priority: high
  - id: "loop-057-2"
    content: "Runtime reachability smoke: import/run remediate + remediation_controller as the installed commands invoke them"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "python -m platforms.python.remediate runs cleanly from repo root; remediation_controller imports without error; result recorded in handoff"
    status: pending
    complexity: low
    priority: high
  - id: "loop-057-3"
    content: "Confirm the full existing suite still passes against the installed runtime (no regression)"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "python -m pytest platforms/python/tests/ passes with count >= prior (300) + the new tests from loops 056-057"
    status: pending
    complexity: low
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Prove the self-heal remediation loop works in isolation: synthetic fail triages correctly and the anti-gaming safety spine escalates on an allowlist breach.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-057"

  ## Success criteria
  - [ ] Sandboxed synthetic-fail integration test passes (triage + allowlist-breach escalation)
  - [ ] remediate / remediation_controller reachable + runnable from repo root
  - [ ] Full suite passes, no regression

  ## Required skills
  - `test-driven-development`: assert the triage + escalation behaviour
  - `verification-before-completion`: runtime reachability is evidence the installed commands can call the modules

  ## Inputs
  - platforms/python/remediate.py (triage_findings)
  - platforms/python/remediation_controller.py
  - Phase 13 existing tests (test_remediate.py, test_remediation_controller.py) for reference

  ## Expected outputs
  - New sandboxed integration test in platforms/python/tests/

  ## Constraints
  - Zero-dependency Python; AST NONE
  - Do NOT modify remediate.py / remediation_controller.py logic — test only
  - The test must NOT perform real source edits or commits — it stages synthetic inputs only

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-057 — self-heal proven (sandboxed triage + escalation test)"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Encode the self-heal exercise as a repeatable, fully-sandboxed pytest (no real edits/commits),
complementing Phase 13's unit tests with an integration-level triage→escalation assertion, and
confirm the modules are reachable from the runtime invocation path.

## Success Criteria
- ✓ Sandboxed synthetic-fail integration test passes (triage routes; allowlist breach escalates)
- ✓ `python -m platforms.python.remediate` runs from repo root; controller imports cleanly
- ✓ Full suite passes (≥300 + new tests); AST NONE

## Skills Required
### Broad (from phase plan): `verification-before-completion`
### Specific: `test-driven-development`
### Discovered: none

## Dependencies
### Must Complete Before: loop-055 (next-phase installed)
### Blocked By: nothing
### Parallelisable: loop-056 (independent test file; both depend only on 055)

## Complexity
**Scope**: High — integration test must stage synthetic gate state realistically without side effects
**Estimated effort**: 2–3 hours
**Key challenges**: 1. Staging a synthetic fail + frozen-criteria + allowlist inputs purely in-memory/tmp; 2. asserting escalation without triggering a real remediation

## Rationale
The sandboxed test is the durable, safe proof; the witnessed live run (loop 058) is the realism
proof. Keeping this test side-effect-free is non-negotiable — it must never edit source.

---

```yaml
---
name: "ralph-loop-058"
task_name: "Witnessed Exercise + v0.14.0 Release"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-058-1"
    content: "In a throwaway git worktree, stage a deliberately-induced gate fail and run the refreshed /next-phase --auto remediation path; capture the transcript + events"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "A worktree run produces gate_remediation and/or passed_after_remediation events + a captured transcript showing the bounded triage->fix->re-gate loop executing live"
    status: pending
    complexity: high
    priority: high
  - id: "loop-058-2"
    content: "Discard the worktree and verify main is untouched"
    skill: "NA"
    agent: "NA"
    outcome: "git worktree list shows the throwaway worktree removed; git status on main is clean; no contrived-fail artefacts remain on main"
    status: pending
    complexity: low
    priority: high
  - id: "loop-058-3"
    content: "Bump VERSION to 0.14.0; add CHANGELOG [0.14.0] section; add CLAUDE.md Phase 14 decision-log entry"
    skill: "NA"
    agent: "NA"
    outcome: "VERSION reads 0.14.0; CHANGELOG.md has a [0.14.0] section listing the install + two-track proof; CLAUDE.md decision log has a Phase 14 entry"
    status: pending
    complexity: low
    priority: high
  - id: "loop-058-4"
    content: "Release gate: full pytest + AST zero-dep NONE + LOCKED files byte-unchanged"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "pytest all pass; ast_check reports NONE; the 4 LOCKED files (phase-complete/manifest/handoff schemas + phase-9/complete.md) are byte-unchanged vs HEAD"
    status: pending
    complexity: medium
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Witness the self-heal loop correcting a real (contrived, isolated) gate fail, then cut v0.14.0 — leaving main pristine.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-058"

  ## Success criteria
  - [ ] Worktree-isolated induced fail runs the bounded remediation loop live; events + transcript captured
  - [ ] Worktree discarded; main clean (git status + git worktree list verified)
  - [ ] VERSION 0.14.0 + CHANGELOG [0.14.0] + CLAUDE.md Phase 14 decision-log entry
  - [ ] Full pytest pass; AST NONE; LOCKED files byte-unchanged

  ## Required skills
  - `verification-before-completion`: the witnessed run + release gate are evidence-first

  ## Inputs
  - Refreshed .claude/commands/next-phase.md (from loop-055)
  - platforms/python/remediation_controller.py, remediate.py, versioning.py
  - VERSION, CHANGELOG.md, CLAUDE.md

  ## Expected outputs
  - Captured exercise evidence (transcript + history events); v0.14.0 release artefacts

  ## Constraints
  - The contrived fail and its remediation MUST run in a discarded git worktree — never commit to main
  - Tag deferred to gate pass (do not cut the git tag in this loop)
  - Zero-dependency Python preserved; LOCKED files must not change

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-058 — self-heal witnessed live; v0.14.0 prepared"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
The realism proof + release. Deliberately induce a gate fail inside a throwaway worktree, watch
the installed self-heal remediate and re-gate live, capture the evidence, discard the worktree,
then prepare the v0.14.0 release. Phase 14's own gate (run after this loop) supplies the codex
live-run criterion.

## Success Criteria
- ✓ Worktree-isolated induced fail runs the bounded loop live; `gate_remediation`/`passed_after_remediation` events + transcript captured
- ✓ Worktree discarded; `git status` clean on main; `git worktree list` shows it gone
- ✓ `VERSION` 0.14.0; CHANGELOG `[0.14.0]`; CLAUDE.md Phase 14 decision-log entry
- ✓ Full pytest pass; AST NONE; 4 LOCKED files byte-unchanged

## Skills Required
### Broad (from phase plan): `verification-before-completion`
### Specific: none
### Discovered: none

## Dependencies
### Must Complete Before: loop-055 (next-phase installed), loop-057 (self-heal proven in sandbox first)
### Blocked By: nothing

## Complexity
**Scope**: High — orchestrating a live remediation in an isolated worktree, then a clean release
**Estimated effort**: 2–4 hours
**Key challenges**: 1. Inducing a fail that exercises the loop without corrupting main; 2. clean worktree teardown; 3. release-gate completeness

## Rationale
Running the contrived fail in a worktree is the key safety decision: a contrived failure and its
remediation never touch the live tree, and "revert" is just deleting the worktree. This is the
recursion the Phase 13 plan anticipated, made real and observed.
