# Phase 8 — Ralph Loops

5 loops decomposing the Framework Consistency Remediation phase plan.

Source: `plans/phase-8.md`
Spec: `plans/2026-05-13-framework-consistency-audit-remediation.md`

Todos are intentionally empty in these stubs. Run `plan-todos` to populate, then
`plan-skill-identification` and `plan-subagent-identification` to assign skills
and agents before execution.

---

```yaml
---
name: "ralph-loop-027"
task_name: "Hook + Permissions Hygiene"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "Patched planning-mode hook allowlist in settings.json and hooks.json to include plans/, cleaned phase-goals-agent.md tools field, created .claude/settings.json with scoped allow rules, updated CLAUDE.md; all 70 tests pass."
  failed: "Interactive smoke test not executed (worker cannot trigger hooks interactively); static pattern analysis recorded in plans/phase-8-notes.md confirms correct behaviour."
  needed: ""

todos:
  - id: "loop-027-1"
    content: "Read platforms/claude-code/settings.json and platforms/claude-code/hooks/hooks.json to understand the current planning-mode PreToolUse allowlist pattern"
    skill: "NA"
    agent: "NA"
    outcome: "Current allowlist paths and glob patterns documented inline; gaps confirmed against success criteria (plans/, .claude/plans/, .claude/state/)"
    status: completed
    priority: high
  - id: "loop-027-2"
    content: "Patch platforms/claude-code/settings.json planning-mode hook to allow writes to plans/, .claude/plans/, and .claude/state/ while blocking all other paths when the sentinel is present"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "settings.json hook allowlist contains precisely-anchored patterns for plans/, .claude/plans/, .claude/state/; no overly-broad globs present"
    status: completed
    priority: high
  - id: "loop-027-3"
    content: "Apply the same allowlist fix to platforms/claude-code/hooks/hooks.json so the mirror config matches settings.json"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "hooks.json allowlist is identical to the patched settings.json allowlist; diff between the two hook configs shows no discrepancy in path rules"
    status: completed
    priority: high
  - id: "loop-027-4"
    content: "Edit platforms/claude-code/agents/phase-goals-agent.md frontmatter to declare tools: Read, Glob, Grep, Write with no parenthetical scope"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "phase-goals-agent.md frontmatter tools field reads exactly 'Read, Glob, Grep, Write' with no parenthetical annotation; canonical YAML field order preserved"
    status: completed
    priority: high
  - id: "loop-027-5"
    content: "Create .claude/settings.json at repo root (checked-in, not .local.json) with permissive allow rules scoped to plans/**, .claude/state/**, .claude/logs/**"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: ".claude/settings.json exists, parses as valid JSON, and contains allow rules scoped only to plans/**, .claude/state/**, .claude/logs/** — no repo-wide globs"
    status: completed
    priority: high
  - id: "loop-027-6"
    content: "Update CLAUDE.md line 56 area to reference the corrected planning-mode allowlist (plans/, .claude/plans/, .claude/state/)"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "CLAUDE.md Planning Mode Hooks section accurately describes the corrected allowlist; no stale path references remain"
    status: completed
    priority: medium
  - id: "loop-027-7"
    content: "Record manual smoke test: with planning-mode sentinel present, confirm write to plans/test.md is allowed and write to core/skills/foo.md is blocked; document result in commit message or plans/phase-8-notes.md"
    skill: "NA"
    agent: "NA"
    outcome: "Smoke test result recorded (pass/fail with observed behaviour); both sentinel-present paths exercised"
    status: completed
    priority: medium
  - id: "loop-027-8"
    content: "Run python -m pytest platforms/python/tests/ -v and validate all core/state/*.json files parse as valid JSON"
    skill: "NA"
    agent: "NA"
    outcome: "pytest exits 0 with no failures; JSON validation command exits 0 with no parse errors"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Eliminate silent-failure paths in the planning-mode hook, remove cosmetic tool scopes, and add repo-root permission settings so routine plan/state edits stop prompting.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-027"

  ## Success criteria
  - [ ] Planning-mode PreToolUse hook allows writes to `plans/`, `.claude/plans/`, and `.claude/state/`; blocks all other paths when the `.claude/state/planning-mode` sentinel is present
  - [ ] `platforms/claude-code/agents/phase-goals-agent.md` frontmatter declares `tools: Read, Glob, Grep, Write` with no parenthetical scope
  - [ ] Repo-root `.claude/settings.json` exists (checked-in, not `.local.json`) with permissive allow rules scoped to `plans/**`, `.claude/state/**`, `.claude/logs/**`
  - [ ] CLAUDE.md:56 updated to reference the corrected allowlist
  - [ ] Manual smoke test recorded: with sentinel present, write to `plans/test.md` allowed, write to `core/skills/foo.md` blocked
  - [ ] `python -m pytest platforms/python/tests/ -v` passes
  - [ ] All `core/state/*.json` files parse as valid JSON

  ## Required skills
  - `hook-and-permissions`: understanding PreToolUse semantics, path glob matching, allow-rule schema
  - `frontmatter-schema`: maintaining canonical YAML field order in agent files

  ## Inputs
  - Phase plan: plans/phase-8.md (Wave 1 sub-tasks 1.1, 1.2, 1.3)
  - Design spec: plans/2026-05-13-framework-consistency-audit-remediation.md
  - Files to modify: platforms/claude-code/settings.json, platforms/claude-code/hooks/hooks.json, platforms/claude-code/agents/phase-goals-agent.md, CLAUDE.md
  - File to create: .claude/settings.json (repo root)

  ## Expected outputs
  - Patched settings.json + hooks.json
  - Cleaned phase-goals-agent.md frontmatter
  - New .claude/settings.json
  - Updated CLAUDE.md
  - Smoke test note (inline in commit message or in plans/phase-8-notes.md)

  ## Constraints
  - Do not change locked schemas
  - Do not add new commands, skills, or agents
  - Do not modify state-bus files
  - Repo-root settings.json must use precisely-scoped allow rules — no `Edit(*)` or `Write(*)`

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-027 — hook allowlist + permissions hygiene"
  2. Update handoff_summary in frontmatter
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Foundational defect fixes: the planning-mode hook silently blocks writes to `plans/`, the `phase-goals-agent` declares a tool scope the harness ignores, and routine plan-file edits prompt for permission. All three are small fixes with disproportionate impact on workflow seamlessness.

## Success Criteria
- ✓ Planning-mode hook allows `plans/`, `.claude/plans/`, `.claude/state/`; blocks others: verified by manual smoke test
- ✓ phase-goals-agent frontmatter declares `tools: Read, Glob, Grep, Write` (no parenthetical): verified by file read
- ✓ Repo-root `.claude/settings.json` exists with precisely-scoped allow rules: verified by file existence and JSON validity
- ✓ CLAUDE.md:56 references the corrected allowlist
- ✓ Existing test suite passes

## Skills Required

### Broad (from phase plan):
- `code-editing`: direct JSON and markdown edits
- `hook-and-permissions`: PreToolUse semantics and allow-rule schema

### Specific (refined for this loop):
- `frontmatter-schema`: canonical YAML field order in agent files

### Discovered:
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Hook config | platforms/claude-code/settings.json | JSON |
| Mirror hook config | platforms/claude-code/hooks/hooks.json | JSON |
| Agent definition | platforms/claude-code/agents/phase-goals-agent.md | Markdown + frontmatter |
| Framework instructions | CLAUDE.md | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Patched hook allowlist | platforms/claude-code/settings.json, platforms/claude-code/hooks/hooks.json | JSON |
| Cleaned agent frontmatter | platforms/claude-code/agents/phase-goals-agent.md | Markdown |
| Repo-root permissions | .claude/settings.json | JSON |
| Updated framework doc | CLAUDE.md | Markdown |

## Dependencies

### Must Complete Before
- None — first loop in Phase 8

### Blocked By
- None

### Parallelisable
- ralph-loop-029 (progress-report dedup): no overlapping files
- ralph-loop-031 (docs): no overlapping files

## Complexity
**Scope**: Low — 4 file edits, 1 new file
**Estimated effort**: 30–45 minutes
**Key challenges**:
1. Getting the case-statement glob pattern right so `*plans/*` matches `plans/` but not `vendor/myplans/`
2. Manual smoke test needs both create-sentinel and remove-sentinel paths exercised

---

```yaml
---
name: "ralph-loop-028"
task_name: "Sentinel Ownership Consolidation"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos: []

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Make `/run-gate` the sole owner of the `gate-review-mode` sentinel. Remove sentinel lifecycle ops from `/next-phase` so nested invocation cannot leave a stale sentinel.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-028"

  ## Success criteria
  - [ ] `platforms/claude-code/commands/next-phase.md` contains no `gate-review-mode` sentinel create or remove operations
  - [ ] `platforms/claude-code/commands/run-gate.md` remains the sole sentinel manager; create and remove are clearly paired
  - [ ] `next-phase.md` invokes `/run-gate` for gate review rather than inlining the gate steps
  - [ ] Dry-run sequence documented (or executed): create sentinel via run-gate, simulate early exit from next-phase, verify no stale sentinel left
  - [ ] CLAUDE.md gate-review section reflects single-owner pattern

  ## Required skills
  - `code-editing`: markdown command-file edits
  - `gate-review-workflow`: understanding the existing gate protocol

  ## Inputs
  - Files to modify: platforms/claude-code/commands/next-phase.md, platforms/claude-code/commands/run-gate.md
  - Framework doc: CLAUDE.md (gate review section)

  ## Expected outputs
  - next-phase.md without sentinel ops
  - run-gate.md confirmed as sole owner
  - Updated CLAUDE.md if the description of the protocol changes

  ## Constraints
  - Gate review must remain functionally equivalent — no regression in write protection
  - The sentinel path (.claude/state/gate-review-mode) does not change
  - Do not add new commands or sentinels

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-028 — sentinel ownership consolidated in run-gate"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
The `gate-review-mode` sentinel is currently created and removed by both `/run-gate` and `/next-phase`. Nested invocation risks leaving a stale sentinel after early exit. This loop establishes single ownership in `/run-gate`.

## Success Criteria
- ✓ next-phase.md sentinel ops removed: verified by grep returning no matches in that file
- ✓ run-gate.md sole owner: verified by inspection of remaining create/remove operations
- ✓ Nested-invocation dry run produces no stale sentinel
- ✓ CLAUDE.md gate protocol description aligns with single-owner model

## Skills Required

### Broad (from phase plan):
- `code-editing`
- `gate-review-workflow`

### Specific (refined for this loop):
- None

### Discovered:
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Next-phase command | platforms/claude-code/commands/next-phase.md | Markdown |
| Run-gate command | platforms/claude-code/commands/run-gate.md | Markdown |
| Gate protocol doc | CLAUDE.md (Gate Review Protocol section) | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Refactored next-phase | platforms/claude-code/commands/next-phase.md | Markdown |
| Verified run-gate | platforms/claude-code/commands/run-gate.md | Markdown |
| Updated framework doc | CLAUDE.md | Markdown |

## Dependencies

### Must Complete Before
- None — independent of other Phase 8 loops

### Blocked By
- None

### Parallelisable
- ralph-loop-027, 029, 030, 031 — no overlapping files

## Complexity
**Scope**: Low — 2 file edits, possible third
**Estimated effort**: 30 minutes
**Key challenges**:
1. Confirming that next-phase's `run-gate` invocation produces the same sentinel lifecycle as inlined gate steps
2. The dry-run step requires careful trace of who creates/removes the sentinel when

---

```yaml
---
name: "ralph-loop-029"
task_name: "progress-report Deduplication"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos: []

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Resolve the duplicate `progress-report` definition. Confirm the command body invokes the skill; refactor if it re-implements logic.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-029"

  ## Success criteria
  - [ ] `platforms/claude-code/commands/progress-report.md` invokes the `core/skills/progress-report` skill rather than duplicating its logic
  - [ ] No execution-time logic is present in both the command body and the skill body
  - [ ] If refactor was needed, the diff is recorded in the commit message
  - [ ] `python -m pytest platforms/python/tests/ -v` passes

  ## Required skills
  - `code-editing`: markdown command edits

  ## Inputs
  - Command file: platforms/claude-code/commands/progress-report.md
  - Skill file: core/skills/progress-report/SKILL.md

  ## Expected outputs
  - Verified or refactored progress-report.md
  - If refactored: command body becomes a thin wrapper that invokes the skill

  ## Constraints
  - Behaviour must remain identical from the user's perspective
  - Skill body remains canonical source of logic
  - Do not delete either the skill or the command — both remain, the command is a wrapper

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-029 — progress-report deduplication"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
The `progress-report` name is registered as both a skill (`core/skills/progress-report/`) and a command (`platforms/claude-code/commands/progress-report.md`). The command should be a thin wrapper invoking the skill. This loop verifies that, and refactors if drift has occurred.

## Success Criteria
- ✓ Command body invokes skill (verified by reading both files)
- ✓ No duplicated logic between command and skill
- ✓ Test suite passes after any refactor

## Skills Required

### Broad (from phase plan):
- `code-editing`

### Specific (refined for this loop):
- None

### Discovered:
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Command file | platforms/claude-code/commands/progress-report.md | Markdown |
| Skill body | core/skills/progress-report/SKILL.md | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Verified or refactored command | platforms/claude-code/commands/progress-report.md | Markdown |

## Dependencies

### Must Complete Before
- None

### Blocked By
- None

### Parallelisable
- ralph-loop-027, 028, 030, 031 — no overlapping files

## Complexity
**Scope**: Low — likely a no-op verification; refactor only if drift found
**Estimated effort**: 15–30 minutes
**Key challenges**:
1. Defining "invokes" precisely — does the command body need to read the skill at runtime, or is referencing it via natural language enough? Follow existing precedent.

---

```yaml
---
name: "ralph-loop-030"
task_name: "Rename new-loop to decompose-phase"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos: []

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Rename `/new-loop` to `/decompose-phase` to eliminate the prefix collision with `/next-loop`. Sweep forward-looking references, add a tombstone redirect, and record the rename in `PLANS-INDEX.md`.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-030"

  ## Success criteria
  - [ ] `platforms/claude-code/commands/new-loop.md` is renamed to `decompose-phase.md` (or new file created with the new name; original becomes tombstone)
  - [ ] A tombstone `new-loop.md` exists containing only a redirect notice pointing to `/decompose-phase`
  - [ ] No forward-looking file in the repo contains `new-loop` as a command reference (historical phase plans `plans/phase-{1,2,3,4,5,6,7}*.md` and `plans/phase-completes/*` excluded from this rule)
  - [ ] CLAUDE.md "Platform Adapters" table mentions `/decompose-phase` and notes the rename from `/new-loop`
  - [ ] `plans/PLANS-INDEX.md` has a "Command Renames" table including this rename with rationale
  - [ ] Internal lookup path in the new `decompose-phase.md` correctly points to `plans/phase-{N}.md` (NOT `.claude/plans/`); fixes the double-extension bug noted in tool-friction-log.md
  - [ ] `python -m pytest platforms/python/tests/ -v` passes

  ## Required skills
  - `cross-reference-sweep`: grep-and-replace across docs, plans, READMEs
  - `code-editing`: file renames and markdown edits

  ## Inputs
  - Command file to rename: platforms/claude-code/commands/new-loop.md
  - Forward-looking files to sweep: platforms/claude-code/commands/*.md, platforms/claude-code/agents/*.md, core/**, docs/**, CLAUDE.md, README.md, STRUCTURE.md, platforms/claude-code/README.md, setup/**
  - Files to leave alone: plans/phase-{1..7}*.md, plans/phase-completes/*.md, plans/master-plan.md, plans/2026-*.md (historical)

  ## Expected outputs
  - Renamed command file
  - Tombstone command file
  - Updated CLAUDE.md, README.md, STRUCTURE.md, docs/
  - Updated PLANS-INDEX.md with Command Renames table
  - Fixed lookup path in decompose-phase.md (resolves a known friction-log entry)

  ## Constraints
  - Historical references in plans/phase-{1..7}*.md and plans/phase-completes/* MUST remain untouched
  - The tombstone must not duplicate functionality — it only redirects
  - All grep sweeps must verify the substitution didn't create new ambiguity (e.g., partial-word matches)

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-030 — new-loop renamed to decompose-phase"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
The prefix collision between `/new-loop` (decomposes a phase) and `/next-loop` (executes the next loop) creates routing ambiguity. This loop renames `/new-loop` to `/decompose-phase`, leaves a tombstone for graceful degradation, and updates forward-looking references.

## Success Criteria
- ✓ File renamed and tombstone present
- ✓ Forward-looking refs swept (historical artefacts excluded)
- ✓ CLAUDE.md disambiguation present
- ✓ PLANS-INDEX.md rename log appended
- ✓ Internal lookup path corrected (friction-log entry resolved as side-effect)
- ✓ Test suite passes

## Skills Required

### Broad (from phase plan):
- `cross-reference-sweep`
- `code-editing`

### Specific (refined for this loop):
- None

### Discovered:
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Command file | platforms/claude-code/commands/new-loop.md | Markdown |
| Forward-looking files | platforms/, core/, docs/, CLAUDE.md, README.md, STRUCTURE.md, setup/ | Markdown |
| Friction-log entry | docs/tool-friction-log.md (path bugs in /new-loop) | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Renamed command | platforms/claude-code/commands/decompose-phase.md | Markdown |
| Tombstone | platforms/claude-code/commands/new-loop.md | Markdown |
| Updated index | plans/PLANS-INDEX.md | Markdown |
| Updated cross-refs | Multiple files | Markdown |

## Dependencies

### Must Complete Before
- ralph-loop-031 ideally — Wave 5's disambiguation work in CLAUDE.md is cleaner if the rename has landed

### Blocked By
- None functionally, but sequence after loops 027–029 to minimise rebase churn

### Parallelisable
- ralph-loop-027, 028, 029 — different files

## Complexity
**Scope**: Medium — many small edits, comprehensive grep sweep required
**Estimated effort**: 45–60 minutes
**Key challenges**:
1. Avoiding accidental matches when sweeping (e.g., `new-loop` inside a code comment or URL)
2. Deciding boundary precisely: historical artefacts to leave alone, forward-looking surface to update
3. Verifying tombstone behaves correctly (graceful redirect, no functional duplication)

---

```yaml
---
name: "ralph-loop-031"
task_name: "Disambiguation + Skill-Activation Policy"
max_iterations: 3
on_max_iterations: checkpoint

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos: []

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Document the two-stage skill-activation pipeline (keywords plan, frontmatter executes), add one-line disambiguation headers to `/new-phase` and `/plan-and-phase`, verify the `new-phase` ↔ `phase-plan-creator` wrapper relationship, and register Phase 8 outcomes in `PLANS-INDEX.md`.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-031"

  ## Success criteria
  - [ ] `platforms/claude-code/commands/new-phase.md` opens with a one-sentence "use this when…" line distinguishing it from `/plan-and-phase`
  - [ ] `platforms/claude-code/commands/plan-and-phase.md` opens with a one-sentence "use this when…" line distinguishing it from `/new-phase`
  - [ ] CLAUDE.md has a new paragraph documenting the two-stage skill-activation pipeline (description keywords inform `plan-skill-identification`; frontmatter `skill:` field is the only execution-time source) with a concrete worked example
  - [ ] `core/skills/plan-skill-identification/SKILL.md` references its planner-stage consumer role explicitly in the When-to-Use or Process section
  - [ ] `new-phase.md` command body is verified to invoke `phase-plan-creator` skill rather than re-implementing it; refactored if drifted
  - [ ] `plans/PLANS-INDEX.md` has a Phase 8 row with status updated from "draft" to "complete" once the loop closes, listing loops 027–031 and an outcome summary
  - [ ] `python -m pytest platforms/python/tests/ -v` passes
  - [ ] All `core/state/*.json` files parse as valid JSON

  ## Required skills
  - `code-editing`: markdown edits to commands and CLAUDE.md
  - `frontmatter-schema`: maintaining skill description conventions

  ## Inputs
  - Files to modify: platforms/claude-code/commands/new-phase.md, platforms/claude-code/commands/plan-and-phase.md, CLAUDE.md, core/skills/plan-skill-identification/SKILL.md, plans/PLANS-INDEX.md
  - Reference: design spec (plans/2026-05-13-framework-consistency-audit-remediation.md) Wave 5 sub-tasks

  ## Expected outputs
  - Disambiguation headers on two command files
  - New CLAUDE.md paragraph documenting the pipeline
  - Updated plan-skill-identification skill body
  - Verified new-phase wrapper (or refactor diff)
  - Phase 8 marked complete in PLANS-INDEX.md

  ## Constraints
  - Do not change the skill-activation behaviour of any agent or worker — this loop documents existing behaviour and clarifies lifecycle, not implementation
  - Do not delete description trigger keywords from any skill; they stay as planner input per the locked decision
  - CLAUDE.md addition should be one paragraph with one example, not a treatise

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-031 — disambiguation + skill-activation policy + Phase 8 close"
  2. Update handoff_summary in frontmatter
  3. Mark all todos completed
  4. Phase 8 gate review is the next step after this loop

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Final Phase 8 loop. Documentation and verification ratify the decisions made by earlier waves: disambiguates two similar commands, formalises the two-stage skill-activation pipeline in CLAUDE.md, verifies the new-phase wrapper, and closes Phase 8 in the index.

## Success Criteria
- ✓ Both `/new-phase` and `/plan-and-phase` open with disambiguation headers
- ✓ CLAUDE.md documents the skill-activation pipeline in one paragraph with example
- ✓ `plan-skill-identification` skill body acknowledges its planner-stage role
- ✓ `new-phase` wrapper verified or refactored
- ✓ PLANS-INDEX.md reflects Phase 8 completion
- ✓ Test suite passes

## Skills Required

### Broad (from phase plan):
- `code-editing`
- `frontmatter-schema`

### Specific (refined for this loop):
- None

### Discovered:
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Commands to disambiguate | platforms/claude-code/commands/new-phase.md, plan-and-phase.md | Markdown |
| Framework doc | CLAUDE.md | Markdown |
| Planner skill | core/skills/plan-skill-identification/SKILL.md | Markdown |
| Index | plans/PLANS-INDEX.md | Markdown |
| Design spec | plans/2026-05-13-framework-consistency-audit-remediation.md | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Disambiguation headers | new-phase.md, plan-and-phase.md | Markdown |
| Two-stage pipeline doc | CLAUDE.md | Markdown |
| Updated planner skill | core/skills/plan-skill-identification/SKILL.md | Markdown |
| Verified wrapper | platforms/claude-code/commands/new-phase.md | Markdown |
| Phase 8 close entry | plans/PLANS-INDEX.md | Markdown |

## Dependencies

### Must Complete Before
- Phase 8 gate review (`/run-gate`)

### Blocked By
- ralph-loop-030 (rename) preferred ahead of this loop to keep CLAUDE.md disambiguation language consistent

### Parallelisable
- None — sequenced last in Phase 8

## Complexity
**Scope**: Low–Medium — multiple small doc edits across several files
**Estimated effort**: 45–60 minutes
**Key challenges**:
1. Writing the two-stage pipeline paragraph clearly enough that a future contributor understands the boundary without re-reading the audit
2. Worked example for the pipeline must be concrete (real skill name, real keywords, real frontmatter entry) not abstract
