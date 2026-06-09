# Phase 15 — Ralph Loops

Decomposition of `.advanced-plans/phases/phase-15/plan.md` (Automation-Surface Audit) into 5
executable loops. Scope source: `.advanced-plans/exploration-notes.md` and
`docs/tool-friction-log.md` open entries.

---

```yaml
---
name: "ralph-loop-059"
task_name: "Doc-Hygiene + Wire State-Archiving"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "PLANS-INDEX stale-pending rows corrected (042-046, 055-058, phase-14 draft→complete); master-plan.md marked historical; archive_cross_phase_state wired into next-loop.md Step 3a (source + byte-identical .claude/ copy); phase-boundary regression test added (344 tests green, AST NONE); friction-log entries struck through."
  failed: ""
  needed: "Begin loop-060: CI path-convention audit (path_audit.py + tests + ci.yml job)."

todos:
  - id: "loop-059-1"
    content: "Correct stale **pending** loop-status rows in .advanced-plans/PLANS-INDEX.md for completed loops 042-046 and 055-058 (set to completed)"
    skill: "NA"
    agent: "NA"
    outcome: "PLANS-INDEX.md shows no gate-passed loop with a **pending** status row; a grep for '**pending**' returns only genuinely-pending loops (if any)"
    status: completed
    complexity: low
    priority: high
  - id: "loop-059-2"
    content: "Resolve master-plan.md staleness: add an explicit 'Historical / superseded' header noting the programme ran 14+ phases beyond the original 4-phase scope, OR refresh the phase overview to reflect reality"
    skill: "NA"
    agent: "NA"
    outcome: "master-plan.md no longer asserts a 4-phase programme as current; it either reflects the true phase count or carries a clear historical marker"
    status: completed
    complexity: low
    priority: medium
  - id: "loop-059-3"
    content: "Wire state_manager.archive_cross_phase_state() into next-loop.md (Step 3-area) so prior-phase stale loop-ready.json/loop-complete.json are archived at the phase boundary instead of consumed; mirror the edit to the .claude/ runtime copy"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/claude-code/commands/next-loop.md invokes archive_cross_phase_state at the loop-start/boundary; .claude/commands/next-loop.md is byte-identical to source"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-059-4"
    content: "Add/confirm a test proving cross-phase stale state files are archived to .advanced-plans/state/archive/ rather than read as current"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "A pytest test (extending test_orchestrator_state_cleanup.py if apt) asserts a prior-phase loop-ready.json is moved to archive/ at boundary; full suite green"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-059-5"
    content: "Strike through the resolved entries in docs/tool-friction-log.md (stale-state archiving; PLANS-INDEX missing/incorrect entries) with a Loop 059 resolution note"
    skill: "NA"
    agent: "NA"
    outcome: "The relevant friction-log entries carry a struck-through header + one-line resolution note per the log's convention"
    status: completed
    complexity: low
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Fix the live documentation-hygiene defects and wire the already-built state-archiving function
  into the loop flow so stale cross-phase state is archived, not consumed.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-059"

  ## Success criteria
  - [ ] No completed loop reads **pending** in PLANS-INDEX.md
  - [ ] master-plan.md reflects reality or is marked historical
  - [ ] next-loop.md (source + .claude/ copy) archives cross-phase stale state
  - [ ] Archiving covered by a passing test; full suite green
  - [ ] Friction-log entries struck through with resolution notes

  ## Required skills
  - verification-before-completion (for the archiving test)

  ## Inputs
  - .advanced-plans/PLANS-INDEX.md, .advanced-plans/master-plan.md
  - platforms/python/state_manager.py (archive_cross_phase_state, line ~241)
  - platforms/claude-code/commands/next-loop.md
  - docs/tool-friction-log.md

  ## Constraints
  - Do NOT re-implement archive_cross_phase_state — wire the existing function
  - Keep .claude/ runtime copy byte-identical to source after the edit
  - Zero-dependency Python (stdlib only)

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-059 — doc-hygiene + state-archiving wired"
  2. Update handoff_summary
  3. Mark all todos completed
```

---

```yaml
---
name: "ralph-loop-060"
task_name: "CI Path-Convention Audit"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-060-1"
    content: "Write platforms/python/path_audit.py (stdlib only): scan tracked command/agent/doc files for non-canonical path tokens (.claude/plans/, doubled-prefix .advanced-.advanced-, .claude/.advanced-plans, non-canonical gate-verdicts location), distinguishing legitimate installed-runtime .claude/ refs from source-repo refs"
    skill: "NA"
    agent: "NA"
    outcome: "path_audit.py exists, exits non-zero with a clear report when a non-canonical token is present, exits zero on a clean tree; uses only pathlib/re/sys"
    status: pending
    complexity: high
    priority: high
  - id: "loop-060-2"
    content: "Write platforms/python/tests/test_path_audit.py with a positive case (clean tree passes) and negative cases (planted doubled-prefix and .claude/plans/ tokens fail), plus a case proving a legitimate installed-runtime .claude/ reference does NOT trip the audit"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Tests cover pass + both fail signatures + the false-positive guard; all green under pytest"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-060-3"
    content: "Add a path-convention-audit job (or step) to .github/workflows/ci.yml that runs path_audit.py and blocks on failure"
    skill: "NA"
    agent: "NA"
    outcome: "ci.yml runs the path audit on push/PR; the job is present and wired to fail the build on a non-canonical path"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-060-4"
    content: "Demonstrate the guard would have caught the Phase 9 double-prefix corruption: a transient planted token makes the audit fail, then is removed and the audit passes (capture evidence in the handoff)"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Evidence recorded that the audit fails on the planted Phase-9-class corruption and passes once removed; working tree left clean"
    status: pending
    complexity: low
    priority: medium
  - id: "loop-060-5"
    content: "Strike through the resolved friction-log entries (non-canonical path enforcement; command rot path tokens) with a Loop 060 resolution note"
    skill: "NA"
    agent: "NA"
    outcome: "Relevant friction-log entries struck through with resolution notes"
    status: pending
    complexity: low
    priority: low

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Install the CI path-convention audit that prevents the path-corruption bug class (the Phase 9
  double-prefix defect), with positive and negative test coverage.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-060"

  ## Success criteria
  - [ ] path_audit.py (stdlib only) flags non-canonical paths, passes clean trees
  - [ ] Tests cover pass + fail signatures + false-positive guard
  - [ ] ci.yml runs the audit and blocks on failure
  - [ ] Demonstrated to catch the Phase-9-class corruption; tree left clean

  ## Required skills
  - verification-before-completion

  ## Inputs
  - docs/path-conventions.md (canonical path map)
  - .github/workflows/ci.yml
  - Phase 9 friction-log entries (corruption signatures)

  ## Constraints
  - Zero-dependency Python (pathlib/re/sys only) — AST check must stay NONE
  - Audit must not flag legitimate installed-runtime .claude/ references

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-060 — CI path-convention audit"
  2. Update handoff_summary
  3. Mark all todos completed
```

---

```yaml
---
name: "ralph-loop-061"
task_name: "/sync-plans Command"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-061-1"
    content: "Write platforms/claude-code/commands/sync-plans.md: a command that re-renders downstream artefacts (phase-plan frontmatter metadata + PLANS-INDEX entry) from a design spec, reporting any drift it corrects"
    skill: "NA"
    agent: "NA"
    outcome: "sync-plans.md exists with numbered steps, a usage section, and error modes; references only canonical .advanced-plans/ paths"
    status: pending
    complexity: high
    priority: high
  - id: "loop-061-2"
    content: "Copy sync-plans.md to the .claude/commands/ runtime byte-identical and add it to the Command Surface table in CLAUDE.md"
    skill: "NA"
    agent: "NA"
    outcome: ".claude/commands/sync-plans.md byte-identical to source; CLAUDE.md Command Surface table lists /sync-plans with its one-line purpose"
    status: pending
    complexity: low
    priority: medium
  - id: "loop-061-3"
    content: "Demonstrate /sync-plans on a real phase: show it re-renders the PLANS-INDEX entry (and/or phase-plan metadata) from the spec with no manual edit, killing a seeded drift"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Evidence captured that a seeded spec→index drift is reconciled by /sync-plans without hand-editing the index"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-061-4"
    content: "Strike through the resolved friction-log entry (three/four artefacts encode the same design; sync drift) with a Loop 061 resolution note"
    skill: "NA"
    agent: "NA"
    outcome: "The drift friction-log entry struck through with a resolution note"
    status: pending
    complexity: low
    priority: low

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Add a /sync-plans command that re-renders downstream planning artefacts from the spec to
  eliminate manual spec→plan→index drift.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-061"

  ## Success criteria
  - [ ] sync-plans.md command exists (source + byte-identical .claude/ copy)
  - [ ] Listed in CLAUDE.md Command Surface
  - [ ] Demonstrated to reconcile a seeded drift with no manual edit

  ## Required skills
  - verification-before-completion

  ## Inputs
  - Existing command files as format reference (e.g. phase-compact.md)
  - .advanced-plans/PLANS-INDEX.md, a phase plan + its spec

  ## Constraints
  - Canonical .advanced-plans/ paths only (the new path audit will check this)
  - Keep .claude/ runtime copy byte-identical

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-061 — /sync-plans command"
  2. Update handoff_summary
  3. Mark all todos completed
```

---

```yaml
---
name: "ralph-loop-062"
task_name: "/next-loop --full One-Pass Population"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-062-1"
    content: "Add a --full flag to platforms/claude-code/commands/next-loop.md that, on a stub loop, chains stubs→todos→skills→agents population in one pass (invoking plan-todos, plan-skill-identification, plan-subagent-identification in sequence) before execution"
    skill: "NA"
    agent: "NA"
    outcome: "next-loop.md documents --full and its one-pass population behaviour; the flag is parsed alongside --auto"
    status: pending
    complexity: high
    priority: high
  - id: "loop-062-2"
    content: "Mirror the edit to the .claude/commands/next-loop.md runtime copy byte-identical and note --full in the CLAUDE.md --auto/flag documentation"
    skill: "NA"
    agent: "NA"
    outcome: ".claude/commands/next-loop.md byte-identical to source; CLAUDE.md mentions --full"
    status: pending
    complexity: low
    priority: medium
  - id: "loop-062-3"
    content: "Demonstrate --full produces output equivalent to the four-step manual chain on a stub loop (todos populated, skills assigned, agents assigned in one invocation)"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Evidence captured that a stub loop is fully populated by a single --full invocation, equivalent to the manual chain"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-062-4"
    content: "Strike through the resolved friction-log entry (stub generation and todo population are separate steps with no automation) with a Loop 062 resolution note"
    skill: "NA"
    agent: "NA"
    outcome: "The workflow-chaining friction-log entry struck through with a resolution note"
    status: pending
    complexity: low
    priority: low

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Add /next-loop --full one-pass loop population so a stub loop becomes execution-ready in a
  single invocation instead of four sequential skill calls.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-062"

  ## Success criteria
  - [ ] --full flag documented + parsed in next-loop.md (source + .claude/ copy)
  - [ ] CLAUDE.md notes --full
  - [ ] Demonstrated equivalent to the four-step manual chain

  ## Required skills
  - verification-before-completion

  ## Inputs
  - platforms/claude-code/commands/next-loop.md
  - core/skills/{plan-todos,plan-skill-identification,plan-subagent-identification}

  ## Constraints
  - Single-loop and --auto behaviour must remain unchanged when --full is absent
  - Keep .claude/ runtime copy byte-identical

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-062 — /next-loop --full one-pass population"
  2. Update handoff_summary
  3. Mark all todos completed
```

---

```yaml
---
name: "ralph-loop-063"
task_name: "Gate-Override Policy + codex Guard + Release"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-063-1"
    content: "Write docs/gate-override-policy.md: when a gate-pass-with-dissent override is permitted (e.g. a reviewer's fail is a verifiable environment/isolation false-negative with no deliverable defect), what must be recorded (override:true + override_reason in history.jsonl), and who may authorise it — codifying the Phase 14 codex-dissent precedent"
    skill: "NA"
    agent: "NA"
    outcome: "docs/gate-override-policy.md exists and defines the permitted conditions, the required history.jsonl record, and the authorisation rule; cross-referenced from CLAUDE.md"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-063-2"
    content: "If (and only if) the policy needs a schema field, add an optional backward-compatible override block to core/state/gate-verdict.schema.json and log the decision in CLAUDE.md; otherwise record that no schema change was needed"
    skill: "schema-design"
    agent: "NA"
    outcome: "Either gate-verdict.schema.json gains an additive optional field (existing verdicts still validate) with a CLAUDE.md decision-log entry, or a note records that history.jsonl recording suffices and no schema change was made"
    status: pending
    complexity: medium
    priority: medium
  - id: "loop-063-3"
    content: "Extend platforms/python/tests/test_codex_gate_live.py with a version-coupling guard that asserts the run-gate codex capture contract (last-message file shape) still parses to a schema-valid verdict, failing loudly if codex output shape changes"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "A codex version-coupling guard test exists and passes against the captured fixture; documents the coupling it protects"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-063-4"
    content: "Cut v0.15.0: bump VERSION, add CHANGELOG [0.15.0] section, add a Phase 15 CLAUDE.md decision-log entry; run full suite + AST check + confirm LOCKED schema docs byte-unchanged"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "VERSION=0.15.0; CHANGELOG [0.15.0] present; CLAUDE.md Phase 15 decision logged; full pytest green across 3.10-3.12; AST NONE; LOCKED docs byte-unchanged"
    status: pending
    complexity: low
    priority: high
  - id: "loop-063-5"
    content: "Strike through any remaining friction-log entries closed this phase and the Phase 14 'Opened' threads (gate-override policy; codex version-coupling) with Loop 063 resolution notes"
    skill: "NA"
    agent: "NA"
    outcome: "All friction-log entries + Phase 14 Opened threads addressed this phase carry struck-through resolution notes"
    status: pending
    complexity: low
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Close the loose Phase 14 threads (formal gate-override policy + codex version-coupling guard)
  and cut the v0.15.0 release.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-063"

  ## Success criteria
  - [ ] docs/gate-override-policy.md defines permitted conditions + required record + authoriser
  - [ ] Any gate-verdict.schema.json change is additive/optional + logged (or no change, noted)
  - [ ] codex version-coupling guard test passes
  - [ ] v0.15.0 cut; suite green; AST NONE; LOCKED docs byte-unchanged
  - [ ] Friction-log + Phase 14 Opened threads struck through with resolution notes

  ## Required skills
  - schema-design (only if touching gate-verdict.schema.json)
  - verification-before-completion

  ## Inputs
  - .advanced-plans/state/history.jsonl (phase-14 override event — the precedent)
  - core/state/gate-verdict.schema.json
  - platforms/python/tests/test_codex_gate_live.py
  - VERSION, CHANGELOG.md, CLAUDE.md

  ## Constraints
  - Any schema change must be backward-compatible (existing verdicts still validate)
  - LOCKED schema docs (phase-complete, phase-manifest-entry, phase-handoff) byte-unchanged
  - Zero-dependency Python

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-063 — gate-override policy + codex guard + v0.15.0"
  2. Update handoff_summary
  3. Mark all todos completed
```
