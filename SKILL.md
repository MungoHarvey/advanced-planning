---
name: advanced-planning
description: "Hierarchical planning system for sustained, accurate multi-step execution in Claude Code. Use for ALL planning tasks: creating phase plans, decomposing work into ralph loop iterations, managing todos with verifiable outcomes, structuring handoffs across sessions, and running /next-loop or /loop-status commands. Triggers: plan this project, new phase, create a phase plan, break this into loops, next loop, loop status, planning, iterations, ralph loop, handoff, I want to plan, how should we approach this, what are the steps, decompose this work, session continuity, resuming a project."
---

# Advanced Planning

A **routing skill** for hierarchical project planning in Claude Code.

```
Phase Plan → Ralph Loops → TODOs → Execution → Handoff → Next Loop
```

This skill provides the complete toolchain for sustained multi-session execution:
structured phase planning, loop decomposition with verifiable todos, and session
continuity via handoff blocks.

## When to Use

- Planning a new project or phase from scratch
- Decomposing a phase plan into executable iterations
- Checking status of the current loop or plan
- Executing the next pending loop
- Structuring todos with verifiable outcomes
- Any task requiring continuity across multiple Claude Code sessions

## Routing Table

| Task | Sub-skill or Command |
|---|---|
| **Create a new phase plan** (objectives, scope, risks, deliverables) | Read `skills/phase-plan-creator/SKILL.md` |
| **Decompose a phase plan into ralph loops** | Read `skills/ralph-loop-planner/SKILL.md` |
| **Execute the next pending loop** | Read `commands/next-loop.md` |
| **Create a new phase and save it** | Read `commands/new-phase.md` |
| **Generate loops from the active phase plan** | Read `commands/new-loop.md` |
| **Check current loop and todo progress** | Read `commands/loop-status.md` |
| **Understand the todo schema and outcome format** | Read `skills/ralph-loop-planner/references/todo-schema.md` |
| **Understand the CLAUDE.md Planning State convention** | Read `references/claude-md-convention.md` |
| **Understand available subagents (orchestrator, workers)** | Read `agents/README.md` |
| **Run a loop using the orchestrator subagent** | Read `agents/loop-orchestrator.md` |
| **Delegate a computational task to a worker subagent** | Read `agents/analysis-worker.md` |

## Typical Workflow

```
1. /new-phase "Phase 2: DESeq2 differential expression pipeline"
      → runs phase-plan-creator → saves .claude/plans/phase-2.md

2. /new-loop
      → runs ralph-loop-planner with active phase plan
      → saves .claude/plans/phase-2-ralph-loops.md

3. /loop-status
      → reads CLAUDE.md → shows current loop, todos, last handoff

4. /next-loop
      → loads current loop → syncs TodoWrite → git checkpoint → executes

5. [loop completes] → handoff written → CLAUDE.md updated → repeat from 3
```

## Architecture

```
advanced-planning/
├── SKILL.md                          ← this file (router)
├── README.md                         ← full system guide
├── skills/
│   ├── phase-plan-creator/           ← phase plan generation
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── phase-plan-template.md
│   └── ralph-loop-planner/           ← loop decomposition
│       ├── SKILL.md
│       └── references/
│           ├── ralph-loop-template.md
│           └── todo-schema.md
├── commands/
│   ├── new-phase.md                  ← /new-phase
│   ├── new-loop.md                   ← /new-loop
│   ├── next-loop.md                  ← /next-loop
│   └── loop-status.md                ← /loop-status
├── agents/
│   ├── README.md                     ← agent system overview
│   ├── loop-orchestrator.md          ← Sonnet: coordinates loop execution
│   └── analysis-worker.md            ← Haiku: runs bounded computational tasks
└── references/
    └── claude-md-convention.md       ← CLAUDE.md Planning State spec
```

## Key Concepts (Quick Reference)

**Handoff** — three-field block written at loop completion, injected into next loop's prompt:
```yaml
handoff:
  done: "what completed"
  failed: "what failed and why, or NA"
  next: "exact action to resume from"
```

**Outcome-driven TODOs** — every todo has a concrete `outcome` field:
```yaml
outcome: "data/normalised.rds exists; dim() matches input; no NA values"
```

**CLAUDE.md as persistent anchor** — `## Planning State` survives session restarts.
See `references/claude-md-convention.md` for the spec.

**Recovery** — each loop has `on_max_iterations: escalate | checkpoint | rollback`
matched to the loop type. See `skills/ralph-loop-planner/SKILL.md` for guidance.

**Orchestrator/worker pattern** — for loops with heavy computation, the `loop-orchestrator`
(Sonnet) coordinates execution and delegates individual todos to `analysis-worker` (Haiku)
via the `agent:` field in todo frontmatter. Workers receive explicit input/output paths and
report structured completion notes. See `agents/README.md` for the full pattern.
