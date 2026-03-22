# Advanced Planning System — Gate Review Sub-Phase & Plugin Development

## Document Purpose

This document formalises the gate review sub-phase extension to the Advanced Planning System v8 architecture. It captures the design rationale, the complete specification of new components, and the pathway to packaging the system as a Claude Code plugin. It serves three purposes: as an architectural record, as an implementation guide, and as a reference for plugin development.

---

## Part 1: Previous Work — Summary and Context

### 1.1 The Advanced Planning System

The Advanced Planning System is a hierarchical, multi-agent planning framework proven across 9 phases and 56+ ralph loops in production use. It structures complex programmes as bounded, verifiable loops organised in a three-tier hierarchy:

```
Phase Plan (strategic — Opus)
├── Ralph Loop 001 (tactical — Sonnet orchestrates, Haiku executes)
│   ├── Todo 1 (with targeted skill injection)
│   ├── Todo 2
│   └── Todo 3
├── Ralph Loop 002
└── Ralph Loop N
```

The system solves four failure modes in long-running AI agent sessions: context drift, unverifiable progress, no resumption path, and scope creep.

### 1.2 Core Architecture (Phase 1 — Complete)

Phase 1 delivered the platform-independent foundation:

**Schemas** (`core/schemas/`): Four schema documents defining every planning artefact — phase-plan, ralph-loop, todo, and handoff — with field specifications, worked examples, and validation checklists.

**Planning Skills** (`core/skills/`): Five skills migrated from prototypes and stripped of platform coupling — phase-plan-creator, ralph-loop-planner, plan-todos, plan-skill-identification, plan-subagent-identification. Each follows the targeted skill injection protocol: load immediately before use, discard after.

**Agent Role Definitions** (`core/agents/`): Two abstract roles — the loop orchestrator (Sonnet) and the loop worker (Haiku). The worker definition contains the targeted skill injection protocol as a numbered step sequence with pseudocode. Neither agent spawns the other; the main thread controls all sequencing.

**Filesystem State Bus** (`core/state/`): The coordination layer using three files:

| File | Writer | Reader | Purpose |
|------|--------|--------|---------|
| `loop-ready.json` | Orchestrator | Worker | Loop preparation handoff |
| `loop-complete.json` | Worker | Main thread | Loop completion signal |
| `history.jsonl` | Main thread | Any | Append-only event log |

### 1.3 Platform Adapters (Phases 2–4 — Complete)

| Adapter | Entry Point | Status |
|---------|-------------|--------|
| Claude Code | Slash commands (`/plan-and-phase`, `/next-loop`, etc.) | Complete |
| Cowork | Routing `SKILL.md` + natural language | Complete |
| Python API | `state_manager.py`, `plan_io.py`, `handoff.py` | Complete |

### 1.4 The Two-Agent Pattern

Every loop cycle follows the same sequence:

```
Main Thread
├── spawn Orchestrator (Sonnet) → writes loop-ready.json → returns
├── reads loop-ready.json
├── spawn Worker (Haiku) → executes todos → writes loop-complete.json → returns
├── reads loop-complete.json
├── updates planning state
└── advance to next loop (or stop)
```

The orchestrator and worker never spawn each other. This constraint is necessary in Claude Code, where subagents cannot spawn further subagents.

### 1.5 Handoff Summaries

Three fields only — `done`, `failed`, `needed` — one sentence each. This is the only context carried between loops, enforcing bounded context and preventing drift.

### 1.6 The Gap Identified

The existing system has no formal mechanism for verifying that a phase's outputs actually meet its stated objectives before advancing. The `on_max_iterations` field handles per-loop failures, but there is no inter-phase quality gate. A worker can mark all todos complete whilst producing outputs that don't satisfy the phase plan's success criteria. This gap is what the gate review sub-phase addresses.

---

## Part 2: The Gate Review Sub-Phase — Design Specification

### 2.1 Immutability Principle

The gate review design rests on a fundamental distinction between two kinds of information:

**Operational state** changes as the pipeline advances. Status fields (`pending`, `in_progress`, `completed`) are operational state and update in-place — that is their purpose.

**Documentary record** captures what happened, what was decided, what failed, what was learned. Handoff summaries, gate verdicts, failure notes, and loop prompts are evidence. They must never be overwritten. Overwriting destroys the audit trail and the learned context that makes retries smarter than the original attempt.

```
MUTABLE (status only)              IMMUTABLE (append or version)
─────────────────────              ─────────────────────────────
todo.status                        todo.content
todo.status                        todo.outcome
loop handoff_summary.done/         loop prompt (never edited)
  failed/needed                    handoff_summary (written once on completion)
PLANS-INDEX.md active pointer      gate-verdict.json (new file per attempt)
CLAUDE.md Planning State           history.jsonl (append-only)
                                   loop files on retry → new versioned file
                                   failure notes → injected into new file
```

### 2.2 Gate Review Agents

The gate sub-phase introduces specialised review agents that run between loop completion and phase advancement. These agents are spawned by the main thread (consistent with the two-agent pattern) and produce structured verdicts.

#### 2.2.1 Gate Reviewer (Abstract Role)

**Location**: `core/agents/gate-reviewer.md`

The abstract gate role runs once per phase boundary (no ralph loop — it is a single-pass evaluation). It receives the phase plan, all loop files, and all outputs produced. It writes a structured verdict to `gate-verdicts/`.

#### 2.2.2 Concrete Gate Agents

| Agent | Location | Purpose |
|-------|----------|---------|
| Code Review Agent | `platforms/claude-code/agents/code-review-agent.md` | Reviews produced code against quality standards, patterns, and phase success criteria |
| Phase Goals Agent | `platforms/claude-code/agents/phase-goals-agent.md` | Verifies outputs satisfy the phase plan's stated success criteria |
| Security Agent | `platforms/claude-code/agents/security-agent.md` | Scans for security issues, secret exposure, injection patterns (optional, per phase config) |
| Test Agent | `platforms/claude-code/agents/test-agent.md` | Runs and verifies test suites, coverage thresholds (optional, per phase config) |
| Programme Reporter | `platforms/claude-code/agents/programme-reporter.md` | Closeout synthesis — produces the final programme narrative |

### 2.3 Gate Verdict Schema

**Location**: `core/state/gate-verdict.schema.json`

Each gate agent writes a verdict file. Verdicts are immutable — one file per attempt, never overwritten:

```json
{
  "phase": "phase-2",
  "attempt": 1,
  "timestamp": "2026-03-22T10:00:00Z",
  "agent": "code-review-agent",
  "verdict": "fail",
  "confidence": 85,
  "findings": [
    {
      "severity": "critical",
      "location": "src/normalisation.R",
      "description": "Unhandled NA values in batch 3 normalisation",
      "evidence": "data/normalised.rds contains 47 NA entries"
    }
  ],
  "loops_to_revert": ["ralph-loop-002", "ralph-loop-003"],
  "failure_notes": [
    "Do not use na.rm=TRUE as a workaround — address the upstream cause",
    "Do not skip batch 3 — all samples must be included"
  ]
}
```

### 2.4 Versioned Retry Mechanism

When a gate fails and triggers a retry, the system creates new plan files for the affected loops rather than editing existing ones:

**First attempt:**
```
plans/
  phase-2.md
  phase-2-ralph-loops.md              ← v1, attempted, gate failed
  gate-verdicts/
    phase-2-attempt-1.json            ← permanent record
```

**After gate failure, retry:**
```
plans/
  phase-2.md                          ← unchanged
  phase-2-ralph-loops.md              ← v1, untouched, status frozen
  phase-2-ralph-loops-v2.md           ← new file, failure context injected
  gate-verdicts/
    phase-2-attempt-1.json            ← original verdict, unchanged
    phase-2-attempt-2.json            ← new verdict when v2 completes
```

`PLANS-INDEX.md` tracks the active version:

```markdown
| Phase 2 | phase-2-ralph-loops-v2.md | attempt-2 | in_progress |
```

### 2.5 Gate Failure Context Injection

When a gate fails, it writes a structured failure note that becomes the opening context of every new loop file. This is what makes retries smarter — the agent begins its second attempt already knowing what went wrong:

```yaml
# Injected at top of phase-2-ralph-loops-v2.md frontmatter
gate_failure_context:
  attempt: 1
  verdict_file: gate-verdicts/phase-2-attempt-1.json
  summary: "Code review found unhandled NA values in batch 3 normalisation."
  loops_reverted:
    - loop: ralph-loop-002
      reason: "Normalisation function incomplete — batch 3 edge case"
    - loop: ralph-loop-003
      reason: "Integration depends on normalised.rds which is invalid"
  do_not_repeat:
    - "Do not use na.rm=TRUE as a workaround — address the upstream cause"
    - "Do not skip batch 3 — all samples must be included"
```

### 2.6 New Commands

| Command | Purpose |
|---------|---------|
| `/run-gate` | Spawns configured gate agents, reads verdicts, triggers revert or advance |
| `/run-closeout` | Final programme synthesis using the complete documentary record |
| Updated `/next-phase` | Calls `/run-gate` before advancing; on fail, creates versioned files |

### 2.7 Programme Closeout

Because nothing is ever overwritten, the programme closeout phase has access to the complete history:

- Which phases required retries and why
- Which gate agents triggered rollbacks most frequently (signal about plan quality)
- Common failure patterns across loops
- Whether final outputs meet original phase objectives

This is only possible with the documentary record intact.

### 2.8 Alignment with Anthropic's Code Review Plugin

Anthropic's official `code-review` plugin for Claude Code provides a directly relevant reference implementation. Key architectural parallels and differences:

**Anthropic's code-review plugin:**
- Launches 5 parallel Sonnet agents for independent auditing perspectives: CLAUDE.md compliance, bug detection, historical context, PR history, and code comments
- Uses confidence-based scoring (threshold ≥80) to filter false positives
- Produces structured output with issue severity, file locations, and line references
- Operates at the PR/commit level via `gh` CLI integration

**Our gate review sub-phase:**
- Launches configurable gate agents (code-review, phase-goals, security, test) at phase boundaries
- Uses structured verdicts with findings, severity, and actionable failure notes
- Operates at the phase/loop level within the planning system's state bus
- Produces versioned retry files with injected failure context

**Leverage opportunities:**
- The confidence scoring pattern from Anthropic's plugin can be adopted for our gate agents, filtering low-confidence findings before triggering rollbacks
- The parallel agent spawning pattern validates our approach of multiple independent reviewers
- The CLAUDE.md compliance checking pattern maps directly to our phase-goals-agent checking phase success criteria
- Agent prompt structures from the official plugin (severity classification, evidence linking) can inform our agent definitions

**Anthropic's feature-dev plugin** also provides relevant patterns:
- 7-phase guided workflow (Discovery → Questions → Architecture → Implementation → Review → Refinement → Summary)
- Three specialised agents: code-explorer, code-architect, code-reviewer
- The phased workflow with review gates mirrors our phase → gate → advance pattern

### 2.9 Updated State Bus Events

The `history.jsonl` append-only log gains four new event types:

| Event Type | Trigger |
|------------|---------|
| `gate_pass` | All gate agents return `pass` verdicts |
| `gate_fail` | Any gate agent returns `fail` verdict |
| `phase_retry` | New versioned loop files created after gate failure |
| `closeout` | Programme closeout synthesis completed |

---

## Part 3: Implementation Plan

### 3.1 Task Overview

The implementation is structured as ralph loops within a new phase, following the system's own methodology (dogfooding).

### Task 1: State Schemas

**Sub-tasks:**
- 1.1: Create `core/state/gate-verdict.schema.json` — verdict, findings array, loops_to_revert, failure_notes
- 1.2: Create `core/state/gate-failure-context.schema.json` — what gets injected into retry loop files
- 1.3: Update `core/schemas/ralph-loop.schema.md` — add optional `gate_failure_context` block to frontmatter specification
- 1.4: Update `core/state/README.md` — document new event types and gate verdict protocol
- 1.5: Validate all schemas are JSON Schema draft-07 compliant

**Success criteria:** All schemas exist, are machine-validatable, and cross-reference correctly with existing schemas.

### Task 2: Gate Agent Definitions

**Sub-tasks:**
- 2.1: Create `core/agents/gate-reviewer.md` — abstract gate role (single-pass, no ralph loop)
- 2.2: Create `platforms/claude-code/agents/code-review-agent.md` — reviews code quality, patterns, CLAUDE.md compliance; incorporates confidence scoring pattern from Anthropic's official plugin
- 2.3: Create `platforms/claude-code/agents/phase-goals-agent.md` — verifies outputs against phase success criteria
- 2.4: Create `platforms/claude-code/agents/security-agent.md` — optional security scanning agent
- 2.5: Create `platforms/claude-code/agents/test-agent.md` — optional test verification agent
- 2.6: Create `platforms/claude-code/agents/programme-reporter.md` — closeout synthesis
- 2.7: Cross-reference all agent definitions against gate-verdict schema and state bus protocol

**Success criteria:** All agent files exist with clear role definitions, input/output contracts, and verdict writing protocols. Code review agent incorporates confidence scoring.

### Task 3: Gate Commands

**Sub-tasks:**
- 3.1: Create `platforms/claude-code/commands/run-gate.md` — spawns configured gate agents, reads verdicts, triggers revert or advance
- 3.2: Create `platforms/claude-code/commands/run-closeout.md` — final programme synthesis
- 3.3: Update `platforms/claude-code/commands/next-phase.md` — integrate `/run-gate` call; on fail, create versioned loop files with failure context and update PLANS-INDEX.md
- 3.4: Verify command files reference correct paths and follow existing command conventions

**Success criteria:** Commands execute the gate workflow end-to-end. `/next-phase` cannot advance past a failed gate without retry.

### Task 4: Python Versioning Utilities

**Sub-tasks:**
- 4.1: Create `platforms/python/versioning.py` with functions:
  - `create_retry_version(loop_file, attempt_number)` → creates new versioned file
  - `inject_failure_context(new_file, verdict)` → writes failure context block
  - `get_active_version(plans_index, phase)` → returns currently active loop file
  - `freeze_loop_file(loop_file)` → marks file as historical (no further status updates)
- 4.2: Create `platforms/python/tests/test_versioning.py` — comprehensive test suite
- 4.3: Validate standard library only — no external dependencies in source modules

**Success criteria:** All functions pass tests. `create_retry_version` preserves original, creates clean new file with failure context injected.

### Task 5: Integration Verification

**Sub-tasks:**
- 5.1: Trace a complete gate-pass scenario: loops complete → `/run-gate` → all pass → `/next-phase` advances
- 5.2: Trace a complete gate-fail scenario: loops complete → `/run-gate` → fail → versioned retry files created → worker reads failure context → retry succeeds → gate passes
- 5.3: Verify `history.jsonl` contains correct event sequence for both scenarios
- 5.4: Verify PLANS-INDEX.md correctly tracks active versions
- 5.5: Update CLAUDE.md with gate review documentation

**Success criteria:** Both scenarios produce correct state transitions. Documentary record is intact and complete.

---

## Part 4: Plugin Development Pathway

### 4.1 Plugin Architecture Mapping

The Advanced Planning System maps naturally to the Claude Code plugin structure:

```
advanced-planning-plugin/
├── .claude-plugin/
│   └── plugin.json                    # Plugin manifest
├── commands/
│   ├── plan-and-phase.md              # /plan-and-phase command
│   ├── new-phase.md                   # /new-phase command
│   ├── next-loop.md                   # /next-loop command
│   ├── next-phase.md                  # /next-phase (with gate integration)
│   ├── loop-status.md                 # /loop-status command
│   ├── progress-report.md             # /progress-report command
│   ├── run-gate.md                    # /run-gate command
│   └── run-closeout.md               # /run-closeout command
├── agents/
│   ├── ralph-orchestrator.md          # Loop orchestrator (Sonnet)
│   ├── ralph-loop-worker.md           # Loop worker (Haiku)
│   ├── code-review-agent.md           # Gate: code review
│   ├── phase-goals-agent.md           # Gate: phase goals verification
│   ├── security-agent.md              # Gate: security scanning (optional)
│   ├── test-agent.md                  # Gate: test verification (optional)
│   └── programme-reporter.md          # Closeout synthesis
├── skills/
│   ├── phase-plan-creator/
│   │   └── SKILL.md
│   ├── ralph-loop-planner/
│   │   └── SKILL.md
│   ├── plan-todos/
│   │   └── SKILL.md
│   ├── plan-skill-identification/
│   │   └── SKILL.md
│   └── plan-subagent-identification/
│       └── SKILL.md
├── hooks/
│   └── hooks.json                     # PreToolUse hooks for planning mode
├── setup/
│   └── install.sh                     # Installation script
├── schemas/
│   ├── phase-plan.schema.md
│   ├── ralph-loop.schema.md
│   ├── todo.schema.md
│   ├── handoff.schema.md
│   ├── gate-verdict.schema.json
│   └── gate-failure-context.schema.json
└── README.md
```

### 4.2 Plugin Manifest

```json
{
  "name": "advanced-planning",
  "description": "Hierarchical multi-agent planning framework with bounded execution, targeted skill injection, and gate review verification. Structures complex programmes as Phase Plans (Opus) → Ralph Loops (Sonnet orchestrates) → Todos (Haiku executes).",
  "version": "1.0.0",
  "author": "Advanced Planning Contributors",
  "commands": "./commands",
  "agents": "./agents",
  "skills": "./skills",
  "hooks": "./hooks/hooks.json"
}
```

### 4.3 Development Using plugin-dev

Anthropic's `plugin-dev` toolkit provides an 8-phase guided workflow for building plugins. The process aligns with our own methodology:

| plugin-dev Phase | Our Mapping |
|-----------------|-------------|
| 1. Discovery | Architecture review (this document) |
| 2. Component Planning | Commands, agents, skills, hooks inventory |
| 3. Detailed Design | Agent prompts, command frontmatter, hook logic |
| 4. Structure Creation | Directory layout, plugin.json manifest |
| 5. Implementation | File creation with content from existing adapters |
| 6. Validation | `plugin-validator` agent checks structure |
| 7. Testing | `--plugin-dir` flag for local testing |
| 8. Documentation | README, usage examples, configuration guide |

**Recommended approach:**

```bash
# Step 1: Install the plugin-dev toolkit
/plugin install plugin-dev

# Step 2: Start the guided workflow
/plugin-dev:create-plugin "Hierarchical multi-agent planning with gate review"

# Step 3: Follow the 8-phase process, using existing adapter files as source material
```

### 4.4 Key Plugin Development Considerations

**Namespacing**: All commands will be namespaced under the plugin name. Users invoke `/advanced-planning:next-loop` rather than `/next-loop`. This prevents conflicts with other plugins.

**Skill triggering**: Skills should include clear trigger descriptions in their frontmatter so Claude Code activates them appropriately. The `phase-plan-creator` skill, for example, should trigger when users express intent to plan a new body of work.

**Agent model tiers**: Agent frontmatter should specify the model tier where the system benefits from it. The orchestrator benefits from Sonnet's reasoning; the worker can often use Haiku for cost efficiency.

**Hook integration**: The `PreToolUse` hook for planning mode (blocking writes outside `.claude/plans/` during exploration) translates directly to the plugin hooks system. The hook logic is identical; only the configuration location changes.

**Progressive disclosure**: Following Anthropic's pattern, skills should have lean core documentation with detailed references available on demand. The ralph-loop-planner skill, for instance, has a core SKILL.md of ~200 words with a `references/` directory containing the full template and worked examples.

### 4.5 Distribution Strategy

**Phase A — Local testing:**
```bash
claude --plugin-dir ./advanced-planning-plugin
```

**Phase B — Team distribution via local marketplace:**
Create a marketplace repository with the plugin, share internally for colleague review.

**Phase C — Public distribution:**
Submit to the official Anthropic marketplace via the submission form at `claude.ai/settings/plugins/submit`. The plugin must meet quality and security standards.

### 4.6 Patterns Borrowed from Anthropic's Official Plugins

| Pattern | Source Plugin | Our Adoption |
|---------|-------------|--------------|
| Parallel agent spawning for independent review | code-review | Gate agents run independently, verdicts aggregated |
| Confidence-based filtering (≥80 threshold) | code-review | Gate verdicts include confidence scores; low-confidence findings don't trigger rollbacks |
| Phased workflow with review gates | feature-dev | Phase → loops → gate → advance/retry |
| Specialised agents for distinct concerns | feature-dev (explorer, architect, reviewer) | Gate agents for code quality, phase goals, security, tests |
| Dynamic skill loading | plugin-dev | Targeted skill injection — load per-todo, discard after |
| `$ARGUMENTS` templating | plugin-dev | Commands accept arguments for phase names, loop targets |
| Proactive agent triggering | plugin-dev patterns | Gate agents trigger automatically at phase boundaries |

---

## Appendices

### A. Glossary

| Term | Definition |
|------|-----------|
| Ralph Loop | A bounded execution cycle with a defined task, todos, and handoff summary |
| Gate | A verification checkpoint between phase completion and advancement |
| Verdict | A structured assessment produced by a gate agent |
| Targeted Skill Injection | Loading a SKILL.md immediately before a todo, discarding after |
| Handoff Summary | Three-field context bridge between loops: done/failed/needed |
| Documentary Record | Immutable artefacts capturing what happened (never overwritten) |
| Operational State | Mutable status fields tracking current pipeline position |

### B. File Inventory — New Components

| File | Type | Purpose |
|------|------|---------|
| `core/state/gate-verdict.schema.json` | Schema | Verdict structure for gate agents |
| `core/state/gate-failure-context.schema.json` | Schema | Failure context injected into retry files |
| `core/agents/gate-reviewer.md` | Agent definition | Abstract gate role |
| `platforms/claude-code/agents/code-review-agent.md` | Agent definition | Code quality review |
| `platforms/claude-code/agents/phase-goals-agent.md` | Agent definition | Phase success criteria verification |
| `platforms/claude-code/agents/security-agent.md` | Agent definition | Security scanning (optional) |
| `platforms/claude-code/agents/test-agent.md` | Agent definition | Test verification (optional) |
| `platforms/claude-code/agents/programme-reporter.md` | Agent definition | Closeout synthesis |
| `platforms/claude-code/commands/run-gate.md` | Command | Gate execution workflow |
| `platforms/claude-code/commands/run-closeout.md` | Command | Programme closeout |
| `platforms/python/versioning.py` | Python module | Retry versioning utilities |
| `platforms/python/tests/test_versioning.py` | Tests | Versioning test suite |

### C. References

- Anthropic Code Review Plugin: `github.com/anthropics/claude-plugins-official/tree/main/plugins/code-review`
- Anthropic Feature Dev Plugin: `github.com/anthropics/claude-plugins-official/tree/main/plugins/feature-dev`
- Anthropic Plugin Dev Toolkit: `github.com/anthropics/claude-code/tree/main/plugins/plugin-dev`
- Claude Code Plugin Documentation: `code.claude.com/docs/en/plugins`
- Plugin Marketplace Documentation: `code.claude.com/docs/en/plugin-marketplaces`
- Plugin Reference: `code.claude.com/docs/en/plugins-reference`

---

*Document version: 1.0 — 22 March 2026*
*Status: Design specification — ready for implementation*
