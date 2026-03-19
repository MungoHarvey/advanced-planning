# Adapting to New Platforms

This guide explains how to build a new platform adapter for the v8 planning system. The core (schemas, skills, agent protocols, state bus) is platform-agnostic — an adapter provides the execution environment-specific wiring without touching the core.

The Cowork adapter is used as a worked example throughout.

---

## The Five Adapter Contracts

Every compliant adapter must fulfil five contracts:

### Contract 1 — Entry Point

How does a user or programme initiate planning actions?

| Adapter | Entry Point |
|---------|------------|
| Claude Code | Slash commands: `/new-phase`, `/new-loop`, `/next-loop` |
| Cowork | Routing `SKILL.md` — natural language intent dispatch |
| Generic | Python function calls: `find_next_loop()`, `write_loop_ready()` |

**Your adapter must define**: how a user triggers planning operations, and how the adapter maps those triggers to the core planning cycle.

### Contract 2 — Agent Spawning

How are the orchestrator and worker spawned?

| Adapter | Spawning Mechanism |
|---------|-------------------|
| Claude Code | `claude --model sonnet agents/ralph-orchestrator.md` subcommand |
| Cowork | `Agent tool` with `model: sonnet` / `model: haiku` parameters |
| Generic | Framework-specific (e.g. `langgraph.invoke`, `crew.kickoff`) |

**Your adapter must define**: how to spawn an orchestrator (Sonnet-tier), how to spawn a worker (Haiku-tier), and how to pass the agent prompt to each.

**Key constraint**: The orchestrator and worker must not spawn each other. All spawning is coordinated by the main thread.

### Contract 3 — State Directory

Where do `loop-ready.json`, `loop-complete.json`, and `history.jsonl` live?

| Adapter | State Directory |
|---------|----------------|
| Claude Code | `.claude/state/` |
| Cowork | `state/` (workspace-relative) |
| Generic | Configurable via `STATE_DIR` parameter |

**Your adapter must define**: the absolute or workspace-relative path to the state directory, and ensure both the orchestrator and worker use the same path.

### Contract 4 — Skills Directory

Where do `SKILL.md` files live for targeted skill injection?

| Adapter | Skills Directory |
|---------|----------------|
| Claude Code | `.claude/skills/[skill]/SKILL.md` |
| Cowork | `skills/[skill]/SKILL.md` |
| Generic | Configurable; usually `core/skills/[skill]/SKILL.md` or symlinked |

**Your adapter must define**: the path prefix used by the worker when loading skills per-todo. This must match where the core skills are actually installed.

### Contract 5 — Checkpoints

How is state preserved before and after each loop?

| Adapter | Checkpoint Mechanism |
|---------|---------------------|
| Claude Code | `git add -A && git commit -m "checkpoint: before [loop]"` |
| Cowork | `sh state/checkpoint.sh save before-[loop]` |
| Generic | User-defined; can be git, snapshots, or a no-op |

**Your adapter must define**: how to save a checkpoint before the loop starts, and how to save a closing checkpoint after the loop completes. The worker prompt must include these checkpoint steps in platform-appropriate syntax.

---

## Minimum Adapter Checklist

A new adapter is ready when all of the following are true:

- [ ] Entry point defined and tested (slash command, routing skill, API call, etc.)
- [ ] Orchestrator prompt exists as a self-contained document with Cowork/platform path conventions
- [ ] Worker prompt exists with the targeted skill injection protocol and platform-correct skill paths
- [ ] State directory path is consistent between orchestrator prompt, worker prompt, and entry point
- [ ] Skills directory path in the worker prompt matches the actual installed skills location
- [ ] Opening and closing checkpoint steps are in the worker prompt
- [ ] No `.claude/` paths in a non-Claude Code adapter (or equivalent platform-internal paths)
- [ ] An adapter README exists covering setup, quick-start, and the top 3 failure modes

---

## Worked Example: Cowork Adapter

The Cowork adapter (`platforms/cowork/`) demonstrates all five contracts for an environment with no git and no CLI.

### Contract 1 — Entry Point

A single `SKILL.md` file with a broad trigger description handles all planning intents. The dispatch table maps user phrases to actions:

```markdown
| Intent | Action |
|--------|--------|
| "run the next loop" | Execute Next Loop Cycle (7-step Agent tool sequence) |
| "show me the status" | Read planning-state.md and plans/ |
| "create a phase plan" | Load core skills and author plans/phase-N.md |
```

No slash commands exist in Cowork. The routing skill replaces them.

### Contract 2 — Agent Spawning

The `SKILL.md` instructs the main session to use Cowork's Agent tool:

```
Agent tool:
  model: sonnet
  prompt: [full contents of agents/orchestrator-prompt.md]
         + "Workspace path: [path to workspace folder]"
```

The agent prompts (`orchestrator-prompt.md` and `worker-prompt.md`) are self-contained — they include the full protocol, path conventions, and all instructions needed without referencing any external file at runtime.

### Contract 3 — State Directory

All state paths are workspace-relative:
- `state/loop-ready.json`
- `state/loop-complete.json`
- `state/snapshots/`

The workspace path is passed as context to each agent at spawn time.

### Contract 4 — Skills Directory

The worker prompt specifies:
```
skills/[skill-name]/SKILL.md
```

When the Cowork workspace is set up with the planning system's core skills in a `skills/` subdirectory, this resolves correctly.

### Contract 5 — Checkpoints

The worker prompt includes:

```bash
# Opening checkpoint
sh state/checkpoint.sh save before-[loop_name]

# Closing checkpoint
sh state/checkpoint.sh save complete-[loop_name]
```

The `checkpoint.sh` script handles `save`, `restore`, and `list` subcommands. See `platforms/cowork/checkpoint.sh`.

---

## Template: Minimal Adapter README

Use this structure for your adapter's README:

```markdown
# Advanced Planning — [Platform] Adapter

One-line description of what this adapter provides.

## What This Does

Brief explanation of the execution model specific to this platform.

## Setup (N Steps)

Step 1 — [How to install/configure]
Step 2 — [How to initialise the workspace]
Step 3 — [How to run the first loop]

## Triggering Planning Actions

[How users invoke planning in this platform]

## How Loop Execution Works

[Diagram or description of the orchestrator → worker cycle]

## Checkpoints

[How checkpoints work in this environment]

## Troubleshooting

### [Failure mode 1]
Symptom / Cause / Fix

### [Failure mode 2]
...

### [Failure mode 3]
...
```

---

## What Not to Change

When building a new adapter, do **not** modify:

- `core/schemas/` — the canonical schema for all plan file types
- `core/skills/` — the platform-agnostic planning skills
- `core/agents/orchestrator.md` and `core/agents/worker.md` — the core protocol
- `core/state/` — the state bus JSON schemas

The adapter wraps these; it does not replace them. If you need different behaviour in a core component, contribute to the core and all adapters benefit.
