# Advanced Planning System

A hierarchical, multi-agent planning framework for structuring complex, multi-week programmes
as sequences of bounded, verifiable loops. Built for Anthropic's Claude models; adaptable to
any agent framework.

```
Phase Plan (Opus)
├── Ralph Loop 001 (Sonnet: orchestrate) → (Haiku: execute with skill injection)
├── Ralph Loop 002 ...
└── Ralph Loop N
```

---

## Why This Exists

Long-running agent programmes fail predictably: context fills, focus drifts, and outputs become
increasingly generic. The planning system solves this with three mechanisms:

**Bounded loops** — each loop has a fixed maximum iterations and a defined completion condition.
Agents cannot drift indefinitely.

**Targeted skill injection** — the worker loads one specialist `SKILL.md` per todo, immediately
before execution, then discards it. Each task gets exactly the expertise it needs; none bleeds
into adjacent tasks.

**Handoff summaries** — three sentences (done/failed/needed) carry context between loops. Enough
for orientation; not enough to bloat.

---

## Quick Start

### Claude Code (terminal)

```bash
git clone https://github.com/MungoHarvey/advanced-planning
cd advanced-planning
sh setup/claude-code/install.sh --project /path/to/your/project
cd /path/to/your/project && claude
/plan-and-phase   # explore first, then plan
# or: /new-phase  # jump straight to phase planning
```

### Cowork (desktop app)

1. Clone or download this repository
2. Open Claude Cowork and select the `advanced-planning/` folder
3. Say: **"Start a new planning session for [your project]"**

See `setup/cowork/README.md` for full Cowork setup instructions.

---

## Platforms

| Platform | Environment | Entry Point | Setup |
|----------|-------------|-------------|-------|
| Claude Code | Terminal / IDE | Slash commands (`/plan-and-phase`, `/next-loop`, `/progress-report`) | `setup/claude-code/` |
| Cowork | Desktop app | Natural language triggers | `setup/cowork/` |
| Python API | Any agent framework | Python import | `platforms/python/` |

---

## Skills Ecosystem

The planning system is designed to work with a wider ecosystem of specialist skills:

**[awesome-agent-skills](https://github.com/MungoHarvey/awesome-agent-skills)** — A curated
catalogue of agent skills for Claude Code and Cowork, including a VoltAgent skill-finder that
lets you pull skills from the VoltAgent marketplace on demand. If a planning loop calls for a
specialist skill that does not yet exist locally, the skill-finder can locate and install it.

**[claude-scientific-skills](https://github.com/anthropics/claude-scientific-skills)** *(community)* — A
collection of domain-specific skills for scientific and research workflows. Pair these with the
planning system to run multi-phase research programmes with the same bounded, verifiable loop
structure used for software projects.

To use external skills with this planning system: download the skill, place the `SKILL.md` in
your project's `.claude/skills/[skill-name]/` directory, and reference it by name in your
`plan-skill-identification` step. The worker will load it automatically via targeted injection.

---

## Architecture

```
┌──────────────────────────────────────────────┐
│                    CORE                      │
│  schemas/    skills/    agents/    state/    │
│  Platform-agnostic specifications            │
└─────────────────┬────────────────────────────┘
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
   Claude      Cowork    Python
    Code                   API
   Adapter    Adapter   (generic)
```

**State bus**: `loop-ready.json` → `loop-complete.json` → `history.jsonl`

**Two-agent pattern**: Orchestrator (Sonnet) prepares → Worker (Haiku) executes → Main thread advances

See `docs/architecture.md` for the full explanation.

---

## Repository Structure

```
advanced-planning/
├── core/
│   ├── schemas/          ← Plan file schemas (phase-plan, ralph-loop, todo, handoff)
│   ├── skills/           ← Planning skills (phase-plan-creator, ralph-loop-planner, etc.)
│   ├── agents/           ← Orchestrator and worker role definitions
│   └── state/            ← State bus JSON schemas
├── platforms/
│   ├── claude-code/      ← Slash commands, hooks, settings.json
│   ├── cowork/           ← Routing SKILL.md, agent prompts, checkpoint.sh
│   └── python/           ← Python API (state_manager, plan_io, handoff) + tests
├── setup/
│   ├── claude-code/      ← install.sh and Claude Code setup guide
│   └── cowork/           ← create-zip.sh and Cowork setup guide
├── docs/                 ← Architecture, getting started, concepts, decisions
├── examples/             ← This repository's own plan files (dogfood example)
└── plans/                ← The plan files used to build this repository
```

---

## Documentation

| Document | What it covers |
|----------|---------------|
| `docs/getting-started.md` | First loop in 30 minutes |
| `docs/concepts.md` | Glossary: ralph loop, handoff summary, targeted skill injection, state bus |
| `docs/architecture.md` | Two-agent pattern, state bus, three-tier hierarchy, design decisions |
| `docs/model-tier-strategy.md` | Model costs, tier assignments, override guidance |
| `docs/adapting-to-new-platforms.md` | Five-contract adapter checklist with worked examples |
| `docs/decisions.md` | Eight architectural decisions with context and rationale |

---

## Python API

```python
from platforms.python.state_manager import write_loop_ready, read_loop_complete
from platforms.python.plan_io import find_next_loop, get_pending_todos
from platforms.python.handoff import inject_handoff, make_empty_handoff

loop = find_next_loop("plans")
write_loop_ready("state", loop_name=loop["loop_name"], ...)
# ... spawn orchestrator and worker ...
result = read_loop_complete("state")
```

No external dependencies. Standard library only. 40 unit tests across state management,
plan I/O, and handoff injection. See `platforms/python/README.md`.

---

## Model Tiers

| Role | Model | When |
|------|-------|------|
| Phase planning | Opus | Once per phase |
| Loop orchestration | Sonnet | Once per loop |
| Progress reporting | Sonnet | On demand (read-only synthesis) |
| Todo execution | Haiku | Per todo, with skill injection |

---

## Installation via Plugin (Cowork)

The easiest way to use this system in Cowork is via the **Advanced Planning plugin**, which
packages the core skills, agent prompts, and checkpoint utilities into a single installable
bundle. Install it from the Cowork plugin manager, then select your project folder and start
a session.

For manual setup without the plugin, follow `setup/cowork/README.md`.

---

## Future Development

The current system establishes a solid foundation. These are the directions we expect to
develop next.

### Headless Mode

`/next-loop --auto` provides autonomous loop chaining within a session: the command chains
loops end-to-end, stopping only on phase completion or failure. For true headless operation
across sessions — a daemon that resumes automatically after a session boundary — only a thin
orchestrating script is needed; the state bus already supports it.

### Nested Subagent Orchestration

The current two-agent pattern has a hard constraint: **the main thread is the only sequencer**.
Neither the orchestrator nor the worker spawns further agents. This is by design in the current
release — Claude Code does not permit agents to spawn further subagents, so the main thread
must retain control.

As this capability becomes available (either in Claude Code, or via the API directly), the
architecture could evolve to a nested model:

```
Main thread
└── Subagent Orchestrator (Sonnet)
    ├── Prepares loop-ready.json
    └── Spawns Worker (Haiku)
        └── Executes todos with skill injection
```

In this model the main thread becomes a true programme-level sequencer, delegating each
complete loop cycle — orchestration and execution — to a single subagent invocation.
This would reduce main-thread context consumption significantly on long programmes and
enable fully autonomous multi-loop execution within a single top-level call.

We are tracking this as a first-class future capability. Contributions exploring this pattern
via the Python API (where subagent spawning is already possible with `subprocess` or async
calls) are welcome.

---

## Licence

MIT — see `LICENCE`.

## Contributing

See `CONTRIBUTING.md`. GitHub: [MungoHarvey/advanced-planning](https://github.com/MungoHarvey/advanced-planning)
