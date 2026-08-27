# Adapting to New Platforms

This guide explains how to build a new platform adapter for the v8 planning system. The core (schemas, skills, agent protocols, state bus) is platform-agnostic — an adapter provides the execution environment-specific wiring without touching the core.

The Cowork adapter is used as a worked example throughout.

---

## The Six Adapter Contracts

Every compliant adapter must fulfil six contracts:

### Contract 1 — Entry Point

How does a user or programme initiate planning actions?

| Adapter | Entry Point |
|---------|------------|
| Claude Code | Slash commands: `/new-phase`, `/decompose-phase`, `/next-loop` |
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
| Claude Code | `.advanced-plans/state/` |
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

### Contract 6 — Shared Python Runtime

Where does the adapter's tooling find `platforms/python/`?

Nowhere, unless the adapter arranges it. No installer ships that tree into a
project, so `python -m platforms.python.<module>` resolves only when the working
directory happens to be the source checkout. Until 2026-08-27 the Claude Code
adapter did exactly that at thirteen call sites, and every one of them failed in
every installed project.

The framework's answer is to record where the checkout is and read the record:

| | |
|---|---|
| Manifest | `.advanced-plans/runtime.json`, written by the adapter's installer |
| Key | `source_root` — an absolute path the *interpreter that will read it* can open |
| Launcher | `.advanced-plans/bin/ap.py`, copied from `platforms/python/ap_launcher.py` |
| Module call | `python .advanced-plans/bin/ap.py <module> [args]` |
| In-line call | `runpy.run_path('.advanced-plans/bin/ap.py')['bootstrap']()` before the import |
| Escape hatch | `$ADVANCED_PLANNING_ROOT`, which overrides the manifest |

The manifest sits in `.advanced-plans/`, not in any adapter's own directory,
because every adapter resolves the runtime by this same route. An adapter that
put it under `.claude/` or `.codex/` would make the next adapter write a second
one.

**Your adapter must define**: that its installer writes `runtime.json` and
copies the launcher, and that it does both **outside** any "planning data
already exists, skip the scaffold" guard. Upgrading a project in place is
precisely when a stale `source_root` most needs refreshing, and it is the one
failure the guard below cannot diagnose, because nothing looks wrong.

****The call sites run from the project root.** `.advanced-plans/bin/ap.py` is
a project-root-relative path, exactly like every other path an Advanced
Planning command names. Invoked from a subdirectory the interpreter fails to
open it and exits 2, before the launcher's guard can say anything useful — so
an adapter must not `cd` between resolving the project and calling a command.
The launcher's upward walk for `runtime.json` is what covers an adapter that
names the launcher by an *absolute* path instead.

Two traps, both found by running it:**

*A path the shell can open is not always a path the interpreter can open.* Under
Git Bash on Windows, `$REPO_ROOT` is `/c/Users/...`; native Python cannot open
it. `install.sh` normalises with `cygpath -m`. Any adapter installer that runs
under MSYS needs the same.

*The recorded path is absolute, so it breaks when the checkout moves.* That is
the accepted cost of this mechanism, and it is why the launcher's guard is not
optional: every failure names the manifest, the key, and the repair, and exits
`3` so a caller can tell an unreachable runtime from a module that ran and
returned non-zero. An adapter that swallows exit 3 has removed the only thing
that makes the mechanism supportable.

The alternatives, and why not: copying `platforms/python/` into each project
puts an N-th copy of executable code where it can drift, policed by an
`install_audit` that compares by mtime; a console-script shim adds a packaging
system and mutates PATH for what is a search-path problem. Both were costed at
the phase-6 loop-001 gate.

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
- [ ] Installer writes `.advanced-plans/runtime.json` and copies the launcher, both outside the scaffold guard
- [ ] Every call site reaches the runtime through the launcher; none uses bare `-m` or `sys.path.insert(0, '.')`
- [ ] An adapter README exists covering setup, quick-start, and the top 3 failure modes

---

## Worked Example: Cowork Adapter

The Cowork adapter (`platforms/cowork/`) demonstrates contracts 1-5 for an environment with no git and no CLI. It is also the one adapter that satisfies contract 6 by not needing it: `platforms/cowork/checkpoint.sh` is POSIX shell and invokes no Python at all.

### Contract 1 — Entry Point

A single `SKILL.md` file with a broad trigger description handles all planning intents. The dispatch table maps user phrases to actions:

```markdown
| Intent | Action |
|--------|--------|
| "run the next loop" | Execute Next Loop Cycle (7-step Agent tool sequence) |
| "show me the status" | Read planning-state.md and .advanced-plans/ |
| "create a phase plan" | Load core skills and author .advanced-plans/phases/phase-N/plan.md |
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
