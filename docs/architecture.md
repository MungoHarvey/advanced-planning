# Architecture

The v8 Advanced Planning System is a hierarchical, multi-agent planning framework designed around three principles: bounded execution, targeted skill injection, and platform-agnostic coordination via a filesystem state bus.

---

## Three-Tier Hierarchy

Every programme is structured as a three-level hierarchy:

```
Phase Plan (strategic)
│   Authored once per phase by an Opus-tier agent.
│   Defines scope, loop sequence, success criteria.
│
├── Ralph Loop 001 (tactical)
│   │   Planned by a Sonnet-tier orchestrator.
│   │   Decomposed into verifiable todos.
│   │
│   ├── Todo 1 ─ execute with skill A (Haiku)
│   ├── Todo 2 ─ execute with skill B (Haiku)
│   └── Todo 3 ─ execute (no skill) (Haiku)
│
├── Ralph Loop 002
│   └── ...
│
└── Ralph Loop N
```

**Why three tiers?** Each tier operates at the right level of abstraction. Opus reasons strategically and is called infrequently (once per phase). Sonnet reasons tactically about the current loop. Haiku executes repeatedly with laser focus on individual tasks, guided by injected skills.

---

## Two-Agent Pattern

Each loop cycle involves two agents — an orchestrator and a worker — coordinated by the main thread via the filesystem state bus.

```
Main Thread
    │
    ├─ spawn Orchestrator (Sonnet)
    │       reads plan files
    │       populates todos (if needed)
    │       writes loop-ready.json
    │       returns ◄──────────────────────────────┐
    │                                               │
    ├─ reads loop-ready.json                        │
    │                                               │
    ├─ spawn Worker (Haiku)                         │
    │       reads loop-ready.json                   │
    │       executes todos (targeted skill inject)  │
    │       writes handoff_summary to loop file     │
    │       writes loop-complete.json               │
    │       returns ◄──────────────────────────────┘
    │
    ├─ reads loop-complete.json
    ├─ updates planning state
    └─ advance to next loop (or stop)
```

**Key constraint**: The orchestrator and worker never spawn each other. All spawning decisions are made by the main thread. This is necessary in environments (like Claude Code) where subagents cannot spawn further subagents.

---

## Filesystem State Bus

The state bus is the coordination layer between agents. It uses three files:

```
state/
├── loop-ready.json      ← orchestrator writes; worker reads
├── loop-complete.json   ← worker writes; main thread reads
└── history.jsonl        ← main thread appends; one record per loop
```

### loop-ready.json

Written by the orchestrator to hand off to the worker:

```json
{
  "loop_name": "ralph-loop-003",
  "loop_file": "plans/phase-1-ralph-loops.md",
  "task_name": "Agent Role Definitions",
  "todos_count": 4,
  "prepared_at": "2024-03-15T14:22:00+00:00",
  "status": "ready",
  "handoff_injected": {
    "done": "5 core skills created in core/skills/.",
    "failed": "",
    "needed": "Create core/agents/ with orchestrator.md, worker.md, and analysis-worker.md."
  }
}
```

### loop-complete.json

Written by the worker when the loop finishes:

```json
{
  "loop_name": "ralph-loop-003",
  "loop_file": "plans/phase-1-ralph-loops.md",
  "status": "completed",
  "todos_done": 4,
  "todos_failed": 0,
  "completed_at": "2024-03-15T15:05:00+00:00",
  "handoff": {
    "done": "3 agent files created: core/agents/orchestrator.md, worker.md, README.md.",
    "failed": "",
    "needed": ""
  }
}
```

---

## Targeted Skill Injection

The worker loads a skill's `SKILL.md` immediately before each todo that has one assigned, then discards it before the next todo begins. No skill is loaded at startup; no skill persists across todo boundaries.

```
Worker startup: read loop-ready.json, register todos, open checkpoint

  Todo 1 (skill: plan-todos):
    load  → skills/plan-todos/SKILL.md
    exec  → work according to skill instructions
    verify → outcome condition confirmed
    unload → skill context cleared

  Todo 2 (skill: skill-creator):
    load  → skills/skill-creator/SKILL.md
    exec  → ...
    unload

  Todo 3 (skill: NA):
    exec  → no skill loaded
    verify

Worker completion: write handoff_summary, write loop-complete.json, close checkpoint
```

This pattern prevents two failure modes: generic output from skill-less execution, and contradictory instructions from loading all skills simultaneously.

---

## Platform Adapter Model

The core (schemas, skills, agent protocols, state bus) is platform-agnostic. Each adapter wraps it in the conventions of its execution environment without changing the core protocol.

```
┌─────────────────────────────────────────┐
│               CORE                      │
│  schemas/   skills/   agents/   state/  │
│  Platform-independent. No adapter refs. │
└──────────────┬──────────────────────────┘
               │
       ┌───────┼───────┐
       ▼       ▼       ▼
  Claude    Cowork  Generic
   Code     Adapter  (Python)
  Adapter
```

### What each adapter provides

| Contract | Claude Code | Cowork | Generic |
|----------|------------|--------|---------|
| Entry point | Slash commands | Routing SKILL.md | Python function calls |
| Agent spawning | `claude --model` | Agent tool | Framework-specific |
| State directory | `.claude/state/` | `state/` | Configurable |
| Checkpoints | `git commit` | `checkpoint.sh` | User-defined |
| Session tracking | TodoWrite hook | TodoWrite tool | Optional |

---

## Five Architectural Decisions

### 1. Filesystem state bus (not a database or queue)

Files are the lowest-common-denominator coordination mechanism. They work in every environment — local dev, cloud VMs, sandboxed agents, CI — with no dependencies. The sequential read/write pattern maps naturally to the two-agent cycle.

### 2. Handoff summary over full context

Carrying the full loop output as context between loops grows unboundedly. Three sentences (done/failed/needed) are sufficient for an agent to orient itself; anything more is noise that dilutes attention.

### 3. Model tiers by frequency, not capability

Opus is expensive; Haiku is cheap. The planning operations that justify Opus (phase decomposition, loop sequencing) happen once. The execution operations that use Haiku happen many times. Assigning model tier by frequency of invocation is economically optimal.

### 4. Targeted skill injection over preloading

See the dedicated section above. The per-todo load/unload cycle is the mechanism; "load all at startup" and "load none" are both anti-patterns that produce worse outputs.

### 5. Platform adapters, not platform-specific core

Keeping the core platform-agnostic means all adapters benefit from improvements to core skills and schemas without any porting work. A new adapter is 3–5 files that wire up the entry point and spawning mechanism; the protocol is inherited.

---

## Repository Structure

```
advanced-planning/
├── core/
│   ├── schemas/      ← JSON/Markdown schemas for all plan file types
│   ├── skills/       ← Platform-agnostic planning skills (Opus-tier)
│   ├── agents/       ← Orchestrator and worker role definitions
│   └── state/        ← State bus JSON schemas
├── platforms/
│   ├── claude-code/  ← Slash commands, hooks, settings, install script
│   ├── cowork/       ← Routing skill, agent prompts, checkpoint utility
│   └── python/       ← Python API, unit tests, framework examples
├── docs/             ← Documentation suite (this file, and others)
├── examples/         ← Worked examples (planning-system-restructure)
└── plans/            ← The plan files used to build this very repository
```
