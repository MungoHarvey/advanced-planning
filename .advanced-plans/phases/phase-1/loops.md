# Phase 1 — Ralph Loops: Core Architecture Design

Loops 001–004 deliver the platform-independent foundation of the planning system v8 release: schemas, planning skills, agent role definitions, and the filesystem state bus.

---

## ralph-loop-001: Schema Definitions

```yaml
name: "ralph-loop-001"
task_name: "Schema Definitions"
max_iterations: 3
on_max_iterations: checkpoint

handoff_summary:
  done: "All 4 schema documents created in core/schemas/ with field specs, worked examples, validation checklists, and anti-patterns."
  failed: ""
  needed: ""

todos:
  - id: "loop-001-1"
    content: "Write phase-plan.schema.md covering required sections, field specifications, deliverables table format, and success criteria standards"
    skill: "NA"
    agent: "NA"
    outcome: "core/schemas/phase-plan.schema.md exists with all required sections, a field spec table, one worked example, and a validation checklist"
    status: completed
    priority: high

  - id: "loop-001-2"
    content: "Write ralph-loop.schema.md covering YAML frontmatter fields, on_max_iterations behaviour table, markdown body sections, and prompt design rules"
    skill: "NA"
    agent: "NA"
    outcome: "core/schemas/ralph-loop.schema.md exists with frontmatter field table, all three on_max_iterations values documented, markdown body section list, and prompt design rules with a validation checklist"
    status: completed
    priority: high

  - id: "loop-001-3"
    content: "Write todo.schema.md covering the two-layer architecture, canonical field order, status transitions, native TodoWrite sync schema, and outcome writing standards"
    skill: "NA"
    agent: "NA"
    outcome: "core/schemas/todo.schema.md exists with two-layer table, all 7 frontmatter fields in canonical order, status transition diagram, and outcome writing standards with anti-pattern examples"
    status: completed
    priority: high

  - id: "loop-001-4"
    content: "Write handoff.schema.md covering the three-field protocol, writing rules, injection protocol, and anti-patterns table with real worked examples"
    skill: "NA"
    agent: "NA"
    outcome: "core/schemas/handoff.schema.md exists with all three field specs, three worked examples (successful/partial/max_iterations), the injection protocol block, and an anti-patterns table"
    status: completed
    priority: high

prompt: |
  ## Context from prior loop
  Done: Phase plan approved; repository skeleton created with STRUCTURE.md and PLANS-INDEX.md in place.
  Failed:
  Needed:

  ## Objective
  Create four schema reference documents in core/schemas/ that define every planning artefact in the system with sufficient precision that any contributor can implement them from the document alone.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-001 schema definitions"

  ## Success criteria
  - [ ] core/schemas/phase-plan.schema.md exists with required sections table, field specs, and validation checklist
  - [ ] core/schemas/ralph-loop.schema.md exists with frontmatter field table, on_max_iterations behaviour, markdown body sections, prompt design rules
  - [ ] core/schemas/todo.schema.md exists with two-layer architecture, canonical field order, status transitions, outcome writing standards
  - [ ] core/schemas/handoff.schema.md exists with three-field specs, three worked examples, injection protocol, anti-patterns

  ## Required skills
  - None (schema design is general documentation work)

  ## Inputs
  - Source schemas from v8 prototype: advanced-planning/advanced-planning/platforms/claude-code/
  - Practical evidence: advanced-planning/plans-in-practice-reporting/ (56+ loops)
  - Analysis document: advanced-planning/ANALYSIS-AND-OPTIMISATION.md

  ## Expected outputs
  - core/schemas/phase-plan.schema.md
  - core/schemas/ralph-loop.schema.md
  - core/schemas/todo.schema.md
  - core/schemas/handoff.schema.md

  ## Constraints
  - All schemas must be platform-agnostic (no Claude Code or Cowork-specific language)
  - Every field must have: type, required/optional, valid values, and description
  - Worked examples must use the generic planning domain, not forex-specific content
  - Anti-patterns sections must reflect actual failure modes observed in the 56+ loop evidence base

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-001 — 4 schema documents created in core/schemas/"
  2. Update handoff_summary with what was completed
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
```

## Overview

Produce four markdown reference documents that define the planning artefacts — phase plan, ralph loop, todo, and handoff — as formal schemas that any contributor or platform adapter can implement from the document alone. These schemas are the definitional foundation everything else builds upon.

## Success Criteria

- ✓ All four schema documents exist in `core/schemas/`
- ✓ Every schema defines every field with type, requirement level, valid values, and description
- ✓ Each schema contains at least one worked example in the generic domain
- ✓ All schemas are platform-agnostic (no tool-specific or platform-specific language)
- ✓ Validation checklists present in each document
- ✓ Anti-patterns sections present where relevant (ralph-loop, handoff, todo)

## Skills Required

### Broad (from phase plan):
- `schema-design`: Defining clear, validatable schemas from practical evidence
- `documentation`: Writing reference documents usable without additional context

### Specific (refined for this loop):
- None — schema documents are plain markdown with YAML examples; no specialised tool skill required

### Discovered (new, identified during planning):
- None

## Inputs

| Input | Source | Format |
|-------|--------|--------|
| v8 prototype skills | `advanced-planning/advanced-planning/platforms/claude-code/skills/` | Markdown |
| Practical loop evidence | `advanced-planning/plans-in-practice-reporting/` | Markdown |
| Analysis document | `advanced-planning/ANALYSIS-AND-OPTIMISATION.md` | Markdown |
| Existing todo schema (v7) | `advanced-planning/skills/ralph-loop-planner/references/todo-schema.md` | Markdown |

## Outputs

| Output | Location | Format |
|--------|----------|--------|
| Phase plan schema | `core/schemas/phase-plan.schema.md` | Markdown |
| Ralph loop schema | `core/schemas/ralph-loop.schema.md` | Markdown |
| Todo schema | `core/schemas/todo.schema.md` | Markdown |
| Handoff schema | `core/schemas/handoff.schema.md` | Markdown |

## Dependencies

### Must Complete Before
- Repository skeleton with `core/schemas/` directory: COMPLETE (created with STRUCTURE.md)

### Blocked By
- Nothing — first loop in programme

### Parallelisable
- All four schemas are independent and could be authored concurrently, but sequential execution is fine given a single worker

## Complexity

**Scope**: Low — four documentation files, no code
**Estimated effort**: 1–2 hours
**Key challenges**: Distilling 56+ loops of practical evidence into minimal, complete schemas without over-specifying; resisting the urge to add aspirational fields not validated by practice

---

## ralph-loop-002: Planning Skills (5)

```yaml
name: "ralph-loop-002"
task_name: "Planning Skills (5)"
max_iterations: 3
on_max_iterations: checkpoint

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-002-1"
    content: "Migrate and refine phase-plan-creator skill from v8 prototype into core/skills/phase-plan-creator/ stripping all platform-specific references"
    skill: "skill-creator"
    agent: "NA"
    outcome: "core/skills/phase-plan-creator/SKILL.md exists, references no Claude Code or Cowork-specific tools, and includes a references/ subdirectory with the phase plan template"
    status: pending
    priority: high

  - id: "loop-002-2"
    content: "Migrate and refine ralph-loop-planner skill from v7/v8 sources into core/skills/ralph-loop-planner/ with updated references matching the v8 schemas"
    skill: "skill-creator"
    agent: "NA"
    outcome: "core/skills/ralph-loop-planner/SKILL.md exists with references/ containing ralph-loop-template.md and todo-schema.md that match the schemas produced in loop-001"
    status: pending
    priority: high

  - id: "loop-002-3"
    content: "Migrate and refine plan-todos skill from v8 prototype into core/skills/plan-todos/ with Opus model assignment and platform-agnostic decomposition patterns"
    skill: "skill-creator"
    agent: "NA"
    outcome: "core/skills/plan-todos/SKILL.md exists, specifies model: opus in frontmatter, and contains at least three atomic decomposition patterns with examples"
    status: pending
    priority: high

  - id: "loop-002-4"
    content: "Migrate and refine plan-skill-identification skill from v8 prototype into core/skills/plan-skill-identification/ with the three-level skill cascade documented"
    skill: "skill-creator"
    agent: "NA"
    outcome: "core/skills/plan-skill-identification/SKILL.md exists and documents the phase→loop→todo skill cascade with a concrete example showing skill refinement at each level"
    status: pending
    priority: medium

  - id: "loop-002-5"
    content: "Migrate and refine plan-subagent-identification skill from v8 prototype into core/skills/plan-subagent-identification/ with delegation rules and model tier assignments"
    skill: "skill-creator"
    agent: "NA"
    outcome: "core/skills/plan-subagent-identification/SKILL.md exists with delegation rules table and model tier assignments (Opus=planning, Sonnet=orchestration, Haiku=execution) documented"
    status: pending
    priority: medium

  - id: "loop-002-6"
    content: "Verify all five skills are platform-agnostic by scanning each SKILL.md for tool-specific or platform-specific references"
    skill: "NA"
    agent: "NA"
    outcome: "No occurrences of 'Claude Code', 'Cowork', '/next-loop', 'slash command', 'Agent tool', or 'TodoWrite' appear in any core/skills/ SKILL.md file"
    status: pending
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Migrate all five planning skills from the v7/v8 prototypes into core/skills/, refining each to be platform-agnostic and consistent with the schemas defined in loop-001.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-002 planning skills migration"

  ## Success criteria
  - [ ] core/skills/phase-plan-creator/SKILL.md exists and is platform-agnostic
  - [ ] core/skills/ralph-loop-planner/SKILL.md exists with references/ matching loop-001 schemas
  - [ ] core/skills/plan-todos/SKILL.md exists with model: opus and decomposition patterns
  - [ ] core/skills/plan-skill-identification/SKILL.md exists with three-level cascade documented
  - [ ] core/skills/plan-subagent-identification/SKILL.md exists with delegation rules and model tier table
  - [ ] Verification scan finds zero platform-specific references in any core/skills/ SKILL.md

  ## Required skills
  - `skill-creator`: Crafting well-structured SKILL.md files with proper frontmatter and reference documents

  ## Inputs
  - v8 prototype skills: advanced-planning/advanced-planning/platforms/claude-code/skills/
  - v7 skills: advanced-planning/skills/ (phase-plan-creator, ralph-loop-planner)
  - Schemas from loop-001: core/schemas/
  - Analysis document sections on skill optimisation: advanced-planning/ANALYSIS-AND-OPTIMISATION.md

  ## Expected outputs
  - core/skills/phase-plan-creator/SKILL.md (+ references/)
  - core/skills/ralph-loop-planner/SKILL.md (+ references/)
  - core/skills/plan-todos/SKILL.md
  - core/skills/plan-skill-identification/SKILL.md
  - core/skills/plan-subagent-identification/SKILL.md

  ## Constraints
  - Skills must contain ZERO platform-specific references (no Claude Code, Cowork, slash commands, Agent tool, TodoWrite)
  - Each skill must be self-contained — usable without reading any other skill document
  - model: frontmatter field is mandatory for skills that require a specific model tier (planning skills → opus)
  - Reference files in references/ subdirectories must match the schemas produced in loop-001 (no drift)

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-002 — 5 planning skills migrated to core/skills/"
  2. Update handoff_summary with what was completed
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
```

## Overview

Migrate the five planning skills from the v7/v8 prototypes into `core/skills/`, stripping platform-specific language and aligning each skill's reference documents with the schemas formalised in loop-001. The result is a portable skill library that any platform adapter can reference directly.

## Success Criteria

- ✓ All five `SKILL.md` files exist under `core/skills/`
- ✓ `phase-plan-creator` and `ralph-loop-planner` include `references/` subdirectories with template files
- ✓ `plan-todos` specifies `model: opus` and contains decomposition patterns
- ✓ `plan-skill-identification` documents the three-level skill cascade
- ✓ `plan-subagent-identification` documents model tier assignments and delegation rules
- ✓ Verification scan confirms zero platform-specific references

## Skills Required

### Broad (from phase plan):
- `skill-creator`: Crafting well-structured SKILL.md files

### Specific (refined for this loop):
- Source skills to read: `advanced-planning/advanced-planning/platforms/claude-code/skills/` and `advanced-planning/skills/`

### Discovered (new, identified during planning):
- None anticipated

## Inputs

| Input | Source | Format |
|-------|--------|--------|
| v8 prototype skills | `advanced-planning/advanced-planning/platforms/claude-code/skills/` | Markdown |
| v7 skills | `advanced-planning/skills/` | Markdown |
| Loop-001 schemas | `core/schemas/` | Markdown |
| v8 DECISIONS.md | `advanced-planning/DECISIONS.md` | Markdown |

## Outputs

| Output | Location | Format |
|--------|----------|--------|
| Phase plan creator skill | `core/skills/phase-plan-creator/` | SKILL.md + references/ |
| Ralph loop planner skill | `core/skills/ralph-loop-planner/` | SKILL.md + references/ |
| Plan todos skill | `core/skills/plan-todos/` | SKILL.md |
| Plan skill identification skill | `core/skills/plan-skill-identification/` | SKILL.md |
| Plan subagent identification skill | `core/skills/plan-subagent-identification/` | SKILL.md |

## Dependencies

### Must Complete Before
- Loop-001 (Schema Definitions): provides the canonical schemas that skill reference documents must match

### Blocked By
- Loop-001 — cannot finalise ralph-loop-planner/references/ until todo.schema.md and ralph-loop.schema.md are complete

### Parallelisable
- The five skills are independent of each other once schemas exist; a multi-agent execution could run them concurrently

## Complexity

**Scope**: Medium — five skills, some with reference subdirectories; primarily migration work with targeted refinement
**Estimated effort**: 2–4 hours
**Key challenges**: Removing platform-specific language without losing the specificity that makes skills useful; ensuring ralph-loop-planner/references/ stays in sync with the schemas from loop-001

---

## ralph-loop-003: Agent Role Definitions

```yaml
name: "ralph-loop-003"
task_name: "Agent Role Definitions"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-003-1"
    content: "Write core/agents/orchestrator.md defining the Sonnet orchestrator's responsibilities, inputs, outputs, and the loop preparation protocol"
    skill: "NA"
    agent: "NA"
    outcome: "core/agents/orchestrator.md exists with: role summary, model tier (sonnet), responsibilities list, inputs/outputs table, step-by-step loop preparation protocol, and the loop-ready.json write contract"
    status: pending
    priority: high

  - id: "loop-003-2"
    content: "Write core/agents/worker.md defining the Haiku worker's responsibilities, the per-todo skill injection protocol, and the loop-complete.json write contract"
    skill: "NA"
    agent: "NA"
    outcome: "core/agents/worker.md exists with: role summary, model tier (haiku), responsibilities list, the targeted skill injection protocol as a numbered step sequence, on_max_iterations behaviour, and the loop-complete.json write contract"
    status: pending
    priority: high

  - id: "loop-003-3"
    content: "Document the targeted skill injection protocol in worker.md as a step-by-step procedure covering: read skill field from todo, locate SKILL.md, load into context, execute todo, unload between todos"
    skill: "NA"
    agent: "NA"
    outcome: "worker.md contains a 'Targeted Skill Injection Protocol' section with numbered steps, a pseudocode example, and explicit entry/exit points for skill loading per todo"
    status: pending
    priority: high

  - id: "loop-003-4"
    content: "Write core/agents/README.md explaining the two-agent architecture, model tier economics, and the subagent spawning constraint with its workaround"
    skill: "NA"
    agent: "NA"
    outcome: "core/agents/README.md exists with: two-agent diagram (ASCII), model tier economics table (Opus/Sonnet/Haiku with cost rationale), and the subagent spawning constraint documented with the main-thread workaround pattern"
    status: pending
    priority: medium

  - id: "loop-003-5"
    content: "Verify the orchestrator and worker role documents are internally consistent: handoff fields match the handoff schema, state bus references match core/state/README.md"
    skill: "NA"
    agent: "NA"
    outcome: "Cross-reference check passes: all field names in orchestrator.md and worker.md match core/schemas/handoff.schema.md; all state file names match core/state/README.md"
    status: pending
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Define the two abstract agent roles — orchestrator and worker — with precise responsibility boundaries, the targeted skill injection protocol, and internal consistency with the schemas and state bus produced in prior loops.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-003 agent role definitions"

  ## Success criteria
  - [ ] core/agents/orchestrator.md exists with loop preparation protocol and loop-ready.json write contract
  - [ ] core/agents/worker.md exists with targeted skill injection protocol and loop-complete.json write contract
  - [ ] Targeted skill injection protocol is a numbered step sequence with pseudocode and explicit entry/exit points
  - [ ] core/agents/README.md exists with two-agent ASCII diagram and model tier economics table
  - [ ] Cross-reference check: all field names in agent docs match handoff.schema.md and state/README.md

  ## Required skills
  - None (agent role documentation is general reference writing)

  ## Inputs
  - v8 prototype agents: advanced-planning/advanced-planning/platforms/claude-code/agents/
  - State bus protocol: core/state/README.md
  - Handoff schema: core/schemas/handoff.schema.md
  - Analysis document (skill injection section): advanced-planning/ANALYSIS-AND-OPTIMISATION.md

  ## Expected outputs
  - core/agents/orchestrator.md
  - core/agents/worker.md
  - core/agents/README.md

  ## Constraints
  - Agent roles must be platform-agnostic — no slash commands, Agent tool calls, or Cowork-specific mechanics
  - Targeted skill injection protocol must be specific enough that a platform adapter can implement it without clarification
  - on_max_iterations: escalate — these are design documents; if stuck, surface to human rather than producing incomplete role definitions
  - Do not add a third agent role without strong justification; the two-agent pattern is validated

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-003 — orchestrator.md, worker.md, README.md created in core/agents/"
  2. Update handoff_summary with what was completed
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
```

## Overview

Define the two abstract agent roles that implement the planning system — the loop orchestrator (Sonnet) and the loop worker (Haiku) — as platform-agnostic role documents. The worker definition is the critical deliverable: it contains the targeted skill injection protocol, the highest-value optimisation identified in the analysis, formalised as a precise step sequence that all platform adapters must implement.

## Success Criteria

- ✓ `core/agents/orchestrator.md` defines responsibilities, loop preparation protocol, and loop-ready.json write contract
- ✓ `core/agents/worker.md` defines responsibilities, targeted skill injection protocol (numbered steps + pseudocode), and loop-complete.json write contract
- ✓ `core/agents/README.md` provides the two-agent overview with ASCII diagram and model tier economics
- ✓ Cross-reference check confirms internal consistency with handoff and state bus schemas

## Skills Required

### Broad (from phase plan):
- `documentation`: Writing precise reference documents for agent implementers

### Specific (refined for this loop):
- Read `core/state/README.md` for state bus contract details before writing agent docs
- Read `core/schemas/handoff.schema.md` for field names before writing handoff references in agent docs

### Discovered (new, identified during planning):
- None

## Inputs

| Input | Source | Format |
|-------|--------|--------|
| v8 orchestrator prototype | `advanced-planning/advanced-planning/platforms/claude-code/agents/ralph-orchestrator.md` | Markdown |
| v8 worker prototype | `advanced-planning/advanced-planning/platforms/claude-code/agents/ralph-loop-worker.md` | Markdown |
| State bus protocol | `core/state/README.md` | Markdown |
| Handoff schema | `core/schemas/handoff.schema.md` | Markdown |
| Analysis (skill injection section) | `advanced-planning/ANALYSIS-AND-OPTIMISATION.md` | Markdown |

## Outputs

| Output | Location | Format |
|--------|----------|--------|
| Orchestrator role definition | `core/agents/orchestrator.md` | Markdown |
| Worker role definition | `core/agents/worker.md` | Markdown |
| Agent architecture overview | `core/agents/README.md` | Markdown |

## Dependencies

### Must Complete Before
- Loop-001 (Schema Definitions): handoff schema must exist before worker.md can reference it accurately
- Loop-004 (State Bus Protocol): state bus README must exist before agent docs can reference loop-ready.json / loop-complete.json

### Blocked By
- Loop-001 — in practice, both loops should be complete before this loop starts

### Parallelisable
- orchestrator.md and worker.md could be drafted concurrently; README.md requires both to exist

## Complexity

**Scope**: Medium — three documents, but worker.md requires the targeted skill injection protocol to be precisely specified
**Estimated effort**: 2–3 hours
**Key challenges**: Making the skill injection protocol specific enough to be implementable by a platform adapter while remaining platform-agnostic; the cross-reference verification requires careful attention to field names

---

## ralph-loop-004: State Bus Protocol

```yaml
name: "ralph-loop-004"
task_name: "State Bus Protocol"
max_iterations: 3
on_max_iterations: checkpoint

handoff_summary:
  done: "State bus protocol formalised in core/state/: README.md with sequence diagram and adapter responsibilities, loop-ready.schema.json and loop-complete.schema.json with full JSON Schema validation."
  failed: ""
  needed: ""

todos:
  - id: "loop-004-1"
    content: "Write core/state/README.md with the sequential coordination protocol, file schema summaries, protocol sequence diagram, and adapter responsibilities table"
    skill: "NA"
    agent: "NA"
    outcome: "core/state/README.md exists with: design principles, files table (written-by/read-by/lifecycle), ASCII sequence diagram for main-thread/orchestrator/worker, file schema summaries, and adapter responsibilities table"
    status: completed
    priority: high

  - id: "loop-004-2"
    content: "Write core/state/loop-ready.schema.json as a JSON Schema (draft-07) covering all required fields with pattern validation for loop_name"
    skill: "NA"
    agent: "NA"
    outcome: "core/state/loop-ready.schema.json is valid JSON Schema draft-07, requires loop_name/loop_file/task_name/todos_count/prepared_at/status/handoff_injected, and loop_name has pattern ^ralph-loop-\\d{3}$"
    status: completed
    priority: high

  - id: "loop-004-3"
    content: "Write core/state/loop-complete.schema.json as a JSON Schema (draft-07) covering all required fields with status enum and duration_seconds as optional metric"
    skill: "NA"
    agent: "NA"
    outcome: "core/state/loop-complete.schema.json is valid JSON Schema draft-07, status enum is [completed, partial, failed], duration_seconds is optional, and handoff object requires done/failed/needed string fields"
    status: completed
    priority: high

  - id: "loop-004-4"
    content: "Add history.jsonl specification to core/state/README.md as an optional append-only audit log with example entries and an explanation of when it is useful"
    skill: "NA"
    agent: "NA"
    outcome: "core/state/README.md contains a history.jsonl section with: schema (event, loop_name, timestamp, status fields), two example JSONL lines, and a note that this file is optional but recommended for diagnostics"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Produce a formal, machine-verifiable specification for the filesystem state bus so that any platform adapter can implement sequential loop coordination from the documents alone.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-004 state bus protocol"

  ## Success criteria
  - [ ] core/state/README.md exists with sequence diagram, file table, and adapter responsibilities
  - [ ] core/state/loop-ready.schema.json validates against JSON Schema draft-07; loop_name has pattern constraint
  - [ ] core/state/loop-complete.schema.json validates against JSON Schema draft-07; status enum is [completed, partial, failed]
  - [ ] history.jsonl is documented as optional with example entries

  ## Required skills
  - None (JSON Schema and protocol documentation are general specification work)

  ## Inputs
  - v8 state bus design notes: advanced-planning/DECISIONS.md
  - v8 commands for state bus usage: advanced-planning/advanced-planning/platforms/claude-code/commands/next-loop.md
  - Analysis document: advanced-planning/ANALYSIS-AND-OPTIMISATION.md

  ## Expected outputs
  - core/state/README.md
  - core/state/loop-ready.schema.json
  - core/state/loop-complete.schema.json

  ## Constraints
  - State bus must be sequential, never concurrent — this constraint must be stated explicitly in the protocol
  - JSON Schemas must be draft-07 for maximum compatibility
  - history.jsonl is optional — the minimal implementation requires only loop-ready.json and loop-complete.json
  - Adapter responsibilities table must distinguish between Claude Code, Cowork, and Generic implementations

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-004 — state bus protocol formalised in core/state/"
  2. Update handoff_summary with what was completed
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
```

## Overview

Formalise the filesystem-based state bus — the coordination mechanism between the orchestrator and worker agents — as a protocol specification with machine-verifiable JSON Schemas. The state bus is the architectural linchpin that enables the two-agent pattern; any platform adapter must implement this protocol to integrate with the planning system.

## Success Criteria

- ✓ `core/state/README.md` exists with the full protocol specification, sequence diagram, and adapter responsibilities
- ✓ `loop-ready.schema.json` is valid JSON Schema draft-07 with pattern validation
- ✓ `loop-complete.schema.json` is valid JSON Schema draft-07 with status enum
- ✓ `history.jsonl` documented as optional with example entries

## Skills Required

### Broad (from phase plan):
- `schema-design`: Defining machine-verifiable schemas

### Specific (refined for this loop):
- JSON Schema draft-07 syntax for `pattern`, `enum`, `format: date-time` fields
- ASCII sequence diagram for the three-party protocol

### Discovered (new, identified during planning):
- None

## Inputs

| Input | Source | Format |
|-------|--------|--------|
| State bus design decisions | `advanced-planning/DECISIONS.md` | Markdown |
| v8 next-loop command | `advanced-planning/advanced-planning/platforms/claude-code/commands/next-loop.md` | Markdown |
| v8 loop-ready agent | `advanced-planning/advanced-planning/platforms/claude-code/agents/ralph-orchestrator.md` | Markdown |

## Outputs

| Output | Location | Format |
|--------|----------|--------|
| Protocol specification | `core/state/README.md` | Markdown |
| loop-ready JSON Schema | `core/state/loop-ready.schema.json` | JSON Schema draft-07 |
| loop-complete JSON Schema | `core/state/loop-complete.schema.json` | JSON Schema draft-07 |

## Dependencies

### Must Complete Before
- Loop-001 (Schema Definitions): handoff field names in the state bus schemas must match `handoff.schema.md`

### Blocked By
- Loop-001 — state bus schemas embed the handoff sub-schema; must use the same field names

### Parallelisable
- Can run in parallel with Loop-002 and Loop-003 once Loop-001 is complete

## Complexity

**Scope**: Low — three documents; JSON Schema is straightforward for this domain
**Estimated effort**: 1–2 hours
**Key challenges**: Ensuring the adapter responsibilities table accurately differentiates what changes between Claude Code, Cowork, and Generic platforms; the sequence diagram must be unambiguous about which party writes vs reads each file
