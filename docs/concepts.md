# Concepts Reference

An authoritative glossary for the v8 Advanced Planning System. Every term used across the documentation is defined here. Where a concept has a concrete counterpart in the codebase, the relevant file is noted.

---

## Ralph Loop

A **ralph loop** is a self-contained, bounded unit of execution. Each loop targets a specific outcome, has a fixed maximum number of iterations, and produces a handoff summary when it completes.

**Example**: `ralph-loop-003` might be "Create agent role definitions for the planning system." It contains 4 todos, a success criterion ("3 agent markdown files exist in core/agents/"), and a `max_iterations: 3` guard.

Ralph loops are specified in plan files as YAML frontmatter blocks. See `core/schemas/ralph-loop.schema.md` for the full schema.

---

## Phase Plan

A **phase plan** is a strategic document that breaks a large programme into a sequence of ralph loops. Phase plans are authored by an Opus-tier agent and are intentionally high-level — they define scope, success criteria, and the loop sequence, but not the individual tasks within each loop.

**Example**: Phase 2 ("Claude Code Adapter") defines three loops: Commands & Install, Agents & Settings, End-to-End Test. Each loop then gets decomposed into todos at the start of its execution.

Phase plans live in `plans/phase-N.md`. Their schema is at `core/schemas/phase-plan.schema.md`.

---

## Handoff Summary

The **handoff summary** is the only context carried between consecutive ralph loops. It has exactly three fields:

- `done` — What was completed (artefact-focused, one sentence)
- `failed` — What failed and why, with specific reference (empty string if nothing failed)
- `needed` — The precise first action the next loop should begin with (empty string if fully done)

**Why only three fields?** Forcing a summary into one sentence per field prevents context bloat. An agent that must summarise its work in one sentence is forced to prioritise the essential.

**Example**:
```yaml
handoff_summary:
  done: "3 schema files created in core/schemas/ — phase-plan, ralph-loop, and handoff schemas."
  failed: ""
  needed: "Create todo.schema.md to complete the schema set before moving to loop-002."
```

The handoff summary is written by the worker at the end of each loop and injected into the orchestrator's prompt at the start of the next.

Schema: `core/schemas/handoff.schema.md`

---

## Targeted Skill Injection

**Targeted skill injection** is the practice of loading a skill's `SKILL.md` immediately before executing the todo it's assigned to, then discarding it before the next todo begins.

This is the core execution optimisation in the v8 system. It solves two problems:

1. **No skills loaded** → the worker executes with general capability; specialist tasks get generic output
2. **All skills loaded at startup** → the worker's context is flooded with contradictory instructions from every applicable skill

With targeted injection, each task gets exactly one skill's instructions, at the moment of execution, cleared before the next.

**Example**: A loop with three todos — one assigned `plan-todos`, one assigned `skill-creator`, one unassigned — loads and unloads skills as follows:

```
Todo 1: load plan-todos/SKILL.md → execute → verify → unload
Todo 2: load skill-creator/SKILL.md → execute → verify → unload
Todo 3: (no skill) → execute → verify
```

This is mandatory behaviour for any compliant worker implementation. See `core/agents/worker.md`.

---

## State Bus

The **state bus** is the three-file coordination mechanism between the orchestrator and worker. Files are written and read sequentially — there is no message queue, database, or network call.

| File | Writer | Reader | Purpose |
|------|--------|--------|---------|
| `loop-ready.json` | Orchestrator | Worker | Assignment: loop file, todos count, handoff context |
| `loop-complete.json` | Worker | Main thread | Completion: status, todos done/failed, handoff summary |
| `history.jsonl` | Main thread | Human/tooling | Append-only log of all loop completions |

**Why files?** File-based coordination works in every environment — local machines, cloud VMs, sandboxed sessions, CI runners. There is no dependency to install, no service to start, no authentication to configure.

Schemas: `core/state/loop-ready.schema.json`, `core/state/loop-complete.schema.json`

---

## Model Tier

The **model tier** describes which class of AI model is used at each level of the hierarchy:

| Tier | Default Model | Role | Frequency |
|------|--------------|------|-----------|
| Strategic | Opus | Phase plan authoring | Once per phase |
| Tactical | Sonnet | Orchestrator (loop preparation) | Once per loop |
| Execution | Sonnet (default); Haiku for low-complexity | Worker (todo execution) | Many times per loop |

The model choice at each tier is driven by economics: Opus is expensive and powerful, used only where strategic reasoning is required. Sonnet is the default execution tier, chosen for its compositional reasoning on multi-file tasks. Haiku is available for todos marked `complexity: low`, where the task is simple enough that a lighter model suffices.

See `docs/model-tier-strategy.md` for cost estimates and guidance on overriding defaults.

---

## on_max_iterations

The **`on_max_iterations`** field specifies what the worker should do if a loop exhausts its maximum iteration budget without completing all todos. Three strategies:

| Value | Behaviour |
|-------|-----------|
| `escalate` | Stop; write `loop-complete.json` with `status: failed`; surface to human |
| `checkpoint` | Write `loop-complete.json` with `status: partial`; snapshot current state; let main thread decide |
| `rollback` | Revert to pre-loop state (git reset or snapshot restore); write `status: failed` |

Use `escalate` for loops whose partial completion leaves the system in an inconsistent state. Use `checkpoint` for loops where partial progress is useful and the human can triage. Use `rollback` only when partial state is worse than no state.

---

## Planning Mode

**Planning mode** is a temporary read-only enforcement state activated during `/plan-and-phase`
exploration. When active, a sentinel file `.claude/state/planning-mode` is present. The
`PreToolUse` hooks in `settings.json` check for this sentinel and block `Write`, `Edit`,
and `MultiEdit` tool calls to any path outside `.claude/plans/` and `.claude/state/`.

This prevents accidental changes to source code during the exploration phase, when the
goal is to read and understand — not to modify.

**Lifecycle**:
1. `/plan-and-phase` creates the sentinel: `echo "$(date -Iseconds)" > .claude/state/planning-mode`
2. Exploration proceeds read-only (exploration notes saved to `.claude/plans/`)
3. Human review gate — user confirms, edits, or stops
4. Sentinel removed: `rm -f .claude/state/planning-mode`
5. Full planning pipeline runs with writes re-enabled

The sentinel is always removed before the planning pipeline runs, so no hooks interfere
with phase plan or loop file creation.

---

## Progress Report

The **progress report** is a retrospective synthesis produced by the `progress-report`
skill and the `/progress-report` command. It reads existing artefacts — plan files, loop
handoff summaries, todo statuses, and git commit history — and compiles them into a
structured markdown report.

No new logging infrastructure is needed. The report is entirely derived from data that
the planning system already produces during normal execution.

**Data sources** (in order of priority):
1. Phase plan files (`phase-N.md`) — objectives and success criteria
2. Loop files (`phase-N-ralph-loops.md`) — todo statuses and handoff summaries
3. `CLAUDE.md` Planning State — current position in the plan
4. Git log (`complete:` and `checkpoint:` commits) — timestamps for loop completions
5. `.claude/state/loop-complete.json` — most recent loop result
6. `.claude/logs/execution.log` — agent activity log

The report is read-only. It never modifies plan files. Use `/progress-report --phase N`
to scope the report to a single phase, or omit the flag for the full programme.

---

## Platform Adapter

A **platform adapter** wraps the platform-agnostic core (schemas, skills, agent protocols, state bus) in the conventions of a specific execution environment.

This release ships three adapters:

| Adapter | Entry Point | Agent Spawning | Checkpoints |
|---------|------------|----------------|-------------|
| Claude Code | Slash commands (`/next-loop`) | `claude --model` subprocess | `git commit` |
| Cowork | Routing `SKILL.md` | Agent tool with `model:` param | `checkpoint.sh` snapshots |
| Generic | Python API import | Framework-specific (see examples) | User-defined |

An adapter must specify: entry point, agent spawning mechanism, state directory path, skills directory path, and checkpoint strategy. The core protocol is unchanged across adapters.

See `docs/adapting-to-new-platforms.md` for the full adapter checklist.

---

## Orchestrator

The **orchestrator** is a Sonnet-tier agent responsible for loop preparation. It reads the plan, resolves the next pending loop, populates any under-specified todos (using planning skills), and writes `loop-ready.json`. It does not execute tasks.

The orchestrator is spawned once per loop cycle by the main thread, and returns as soon as `loop-ready.json` is written.

Core protocol: `core/agents/orchestrator.md`

---

## Worker

The **worker** is a Sonnet-tier agent (by default) responsible for loop execution. It reads its assignment from `loop-ready.json`, applies the targeted skill injection protocol for each todo, verifies outcomes, writes the handoff summary, and writes `loop-complete.json`. It does not plan, restructure, or decide whether to continue to the next loop. Haiku may be substituted for individual todos marked `complexity: low`.

The worker is spawned once per loop cycle by the main thread, after the orchestrator returns.

Core protocol: `core/agents/worker.md`

---

## Snapshot Checkpoint

A **snapshot checkpoint** is a file-based backup of `plans/` and `state/` at a point in time, used in environments without git (primarily the Cowork adapter). Snapshots are stored in `state/snapshots/{label}-{timestamp}/` and can be restored if a loop leaves the workspace in a bad state.

The `platforms/cowork/checkpoint.sh` script provides `save`, `restore`, and `list` subcommands.

See `docs/adapting-to-new-platforms.md` for the git checkpoint equivalent used in the Claude Code adapter.

---

## Gate Review

### Gate Reviewer

A **gate reviewer** is an agent that evaluates the outputs of a completed phase before the programme advances. Gate reviewers are single-pass — they read artefacts, apply their evaluation criteria, and write a verdict file. They do not execute tasks or modify plan files. Each gate reviewer is spawned by the main thread, consistent with the two-agent pattern.

### Gate Verdict

A **gate verdict** is a structured assessment written by a gate reviewer to `plans/gate-verdicts/`. Each verdict includes:

- A pass/fail decision
- Confidence scoring per finding (0–100); only findings with confidence ≥80 trigger failure
- Severity-tagged findings (critical, warning, info)
- A summary suitable for injection into retry context

Verdict files are immutable — one file per agent per attempt, never overwritten. A `gate_pass` event is appended to `history.jsonl` when all required agents pass.

### Versioned Retry

**Versioned retry** is the mechanism for recovering from a failed gate. Rather than editing the original loop file, a new versioned file is created:

- The original (`phase-N-ralph-loops.md`) is frozen; all todos are set to `status: frozen`
- A retry file (`phase-N-ralph-loops-v2.md`) is created with affected todos reset to pending
- `PLANS-INDEX.md` is updated to track the active version and attempt number

This preserves a complete audit trail of what was tried and why it failed.

### Gate-Review-Mode

**Gate-review-mode** is a sentinel-based enforcement state, analogous to Planning Mode, that restricts agents to read-only operations during gate evaluation. When the sentinel is present, `Write`, `Edit`, and `MultiEdit` calls to paths outside `plans/gate-verdicts/` are blocked. This prevents gate agents from accidentally modifying the artefacts they are evaluating.

### Failure Context Injection

**Failure context injection** is the mechanism that makes retries smarter than the original attempt. When a gate fails, a `gate_failure_context` YAML block is injected into the retry loop file. This block contains a summary of what failed, which findings triggered the failure, and targeted guidance for the retry. The orchestrator reads this context when preparing the retry loop, so the worker begins with precise knowledge of what went wrong.
