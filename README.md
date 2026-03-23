# Advanced Planning System

A hierarchical, multi-agent planning framework that structures complex AI-driven programmes as bounded, verifiable execution loops. Built for Anthropic's Claude models; adaptable to any agent framework.

---

## Introduction

Long-running AI agent sessions fail in predictable ways. Context windows fill and attention degrades. Scope drifts without anyone noticing. There is no way to verify that outputs actually meet objectives. And when a session ends, there is no clean way to resume.

The Advanced Planning System addresses each of these failure modes:

| Problem | Solution |
|---------|----------|
| **Context fills, focus drifts** | Bounded execution loops with fixed iteration limits and explicit completion conditions |
| **Outputs miss objectives** | Inter-phase quality gates — review agents evaluate success criteria before advancement |
| **No resumption path** | Three-field handoff summaries (done/failed/needed) carry just enough context between loops |
| **Generic output quality** | Targeted skill injection — the right specialist instructions loaded per task, discarded after |
| **Unverifiable progress** | Observable outcome conditions on every todo; gate verdicts with confidence scoring |

The system decomposes work into a three-tier hierarchy: **Phase Plans** (strategic scope) are broken into **Ralph Loops** (bounded iterations), which contain **Todos** (atomic tasks). An orchestrator agent prepares each loop; a worker agent executes it with skill injection; the main thread sequences everything via a filesystem state bus.

```
Phase Plan (Opus — strategic)
├── Ralph Loop 001 (Sonnet: orchestrate → Sonnet: execute with skill injection)
├── Ralph Loop 002 ...
├── Ralph Loop N
└── Gate Review (Sonnet: code-review, phase-goals) → advance or versioned retry
```

---

## Key Features

- **Hierarchical task planning** — three-tier decomposition (Phases → Loops → Todos) turns complex programmes into manageable, verifiable units
- **Multi-agent orchestration** — two-agent pattern coordinates planning and execution via a filesystem state bus, with no shared memory required
- **Targeted skill injection** — worker loads one specialist `SKILL.md` per todo then discards it; each task gets exactly the expertise it needs without cross-contamination
- **Quality gates** — gate review agents evaluate phase outputs before advancement; versioned retry files carry failure context so retries start smarter
- **Autonomous chaining** — `/next-loop --auto` chains loops within a phase; `/next-phase --auto` chains across phase boundaries including gate reviews
- **Handoff summaries** — three sentences (done/failed/needed) bridge loops; enough for orientation, not enough to bloat context
- **Platform-agnostic core** — schemas, skills, and protocols work across Claude Code, Cowork, and any Python-based agent framework

---

## How To Use

### 1. Install

Clone the repository and install into your project:

**macOS / Linux:**
```bash
git clone https://github.com/MungoHarvey/advanced-planning
cd advanced-planning
sh setup/claude-code/install.sh --project /path/to/your/project
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/MungoHarvey/advanced-planning
cd advanced-planning
.\setup\claude-code\install.ps1 -Project C:\path\to\your\project
```

This copies commands, skills, agents, schemas, and hooks into your project's `.claude/` directory. For global installation (commands available in all projects), use `--global` instead of `--project`.

See `setup/claude-code/README.md` for all options (`--global`, `--symlink`, `--dry-run`).

### 2. Plan a phase

Open Claude Code in your project and create a phase plan:

```bash
cd /path/to/your/project && claude
```

**Option A — Explore first, then plan** (recommended for unfamiliar codebases):
```
/plan-and-phase [description of what you want to accomplish]
```
This activates read-only planning mode, explores the codebase, presents findings for review, then runs the full planning pipeline.

**Option B — Plan directly** (when you already know the codebase):
```
/new-phase [description of what you want to accomplish]
```
This runs the full pipeline immediately: phase plan → loop decomposition → todo population → skill assignment → agent assignment.

Both produce execution-ready loop files in `plans/` with fully specified todos.

### 3. Execute loops

Run loops one at a time or chain them automatically:

```
/next-loop          # execute one loop (orchestrator prepares → worker executes)
/next-loop --auto   # chain all loops until the phase completes or a loop fails
```

Each loop cycle:
1. Spawns an **orchestrator** (Sonnet) to prepare the loop and write `loop-ready.json`
2. Spawns a **worker** (Sonnet) that executes todos with targeted skill injection and writes `loop-complete.json`
3. Updates planning state and creates a git checkpoint

### 4. Review and advance

After all loops in a phase complete, run the quality gate:

```
/run-gate           # spawn gate agents to evaluate phase outputs
```

Gate agents (code-review, phase-goals, and optionally security and test) evaluate whether success criteria are met. Each writes a structured verdict with confidence scoring.

Then advance to the next phase:

```
/next-phase         # run gate review → advance on pass, versioned retry on fail
```

- **Gate pass**: phase marked complete, ready for `/new-phase` to plan the next one
- **Gate fail**: versioned retry file created (`phase-N-ralph-loops-v2.md`) with failure context injected, so the retry knows what went wrong

### 5. Go fully autonomous

For multi-phase programmes with a master plan, chain everything end-to-end:

```
/next-phase --auto  # gate → plan next phase → execute loops → gate → repeat
```

This chains across phase boundaries autonomously: gate review → plan next phase → execute all loops → gate review → repeat until the programme completes or a gate/loop fails. Gate failures always stop auto mode (manual review required for versioned retry).

### 6. Monitor progress

At any point during execution:

```
/loop-status        # show all loops with todo counts and handoff summaries
/progress-report    # structured report from plan files, handoffs, and git history
/check-execution    # six-area diagnostic if something seems wrong
/model-check        # verify model tier assignments across skills and agents
```

After all phases complete:

```
/run-closeout       # programme closeout — final narrative from the documentary record
```

---

## Command Reference

### Planning
| Command | Purpose | When to use |
|---------|---------|-------------|
| `/plan-and-phase [desc]` | Explore codebase, then plan | Starting a new project or unfamiliar codebase |
| `/new-phase [desc]` | Plan without exploration | You know the codebase and want to plan directly |
| `/new-loop [N]` | Decompose phase into loops | Regenerating loops for an existing phase plan |

### Execution
| Command | Purpose | When to use |
|---------|---------|-------------|
| `/next-loop` | Execute one loop | Step-by-step execution with manual review between loops |
| `/next-loop --auto` | Chain all loops in phase | Autonomous execution within a single phase |

### Quality Gates
| Command | Purpose | When to use |
|---------|---------|-------------|
| `/run-gate` | Evaluate phase outputs | Standalone review before deciding to advance |
| `/next-phase` | Gate review then advance | Ready to move to the next phase |
| `/next-phase --auto` | Chain across phases | Fully autonomous multi-phase programme execution |
| `/run-closeout` | Programme narrative | All phases complete, want a final summary |

### Diagnostics
| Command | Purpose | When to use |
|---------|---------|-------------|
| `/progress-report` | Structured status report | Reviewing what was accomplished, resuming after a break |
| `/loop-status` | Loop progress table | Quick check on current phase progress |
| `/check-execution` | Execution diagnostic | Worker isn't progressing or something seems wrong |
| `/model-check` | Model tier verification | Confirming agents are running at the expected model tier |

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│                      CORE                        │
│  schemas/    skills/    agents/    state/        │
│  Platform-agnostic specifications                │
└──────────────────┬───────────────────────────────┘
                   │
         ┌─────────┼─────────┐
         ▼         ▼         ▼
    Claude      Cowork    Python
     Code                   API
    Adapter    Adapter   (generic)
```

**Two-agent pattern**: Orchestrator (Sonnet) prepares → Worker (Sonnet) executes → Main thread advances. Neither agent spawns the other; the main thread controls all sequencing.

**State bus**: Three files coordinate the cycle — `loop-ready.json` (orchestrator → worker), `loop-complete.json` (worker → main thread), `history.jsonl` (append-only audit log).

**Gate review**: After all loops complete, `/run-gate` spawns review agents at phase boundaries. Structured verdicts drive pass/advance or fail/retry decisions. Verdicts are immutable; versioned retry files preserve the complete documentary record.

See `docs/architecture.md` for the full explanation.

---

## Platforms

| Platform | Environment | Entry Point | Setup Guide |
|----------|-------------|-------------|-------------|
| Claude Code | Terminal / IDE | Slash commands | `setup/claude-code/` |
| Cowork | Desktop app | Natural language triggers | `setup/cowork/` |
| Python API | Any agent framework | Python import | `platforms/python/` |

### Cowork Plugin

The easiest way to use the system in Cowork is via the **Advanced Planning plugin**. Install from the Cowork plugin manager, select your project folder, and start a session. For manual setup, follow `setup/cowork/README.md`.

---

## Skills Ecosystem

The planning system works with a wider ecosystem of specialist skills:

- **[awesome-agent-skills](https://github.com/MungoHarvey/awesome-agent-skills)** — curated catalogue for Claude Code and Cowork, including VoltAgent skill-finder for on-demand marketplace installs
- **[claude-scientific-skills](https://github.com/anthropics/claude-scientific-skills)** *(community)* — domain-specific skills for scientific and research workflows

To use external skills: place the `SKILL.md` in `.claude/skills/[skill-name]/`. The worker loads it automatically via targeted injection when a todo references it.

---

## Repository Structure

```
advanced-planning/
├── core/                ← Platform-agnostic specifications
│   ├── schemas/         ← Plan file schemas (phase-plan, ralph-loop, todo, handoff)
│   ├── skills/          ← 6 planning skills (model-agnostic instruction sets)
│   ├── agents/          ← Abstract roles (orchestrator, worker, gate-reviewer)
│   └── state/           ← State bus JSON schemas (loop-ready, loop-complete, gate-verdict)
├── platforms/
│   ├── claude-code/     ← 11 slash commands, 8 agents, hooks, settings, plugin scaffold
│   ├── cowork/          ← Routing SKILL.md, agent prompts, checkpoint.sh
│   └── python/          ← Python API (state_manager, plan_io, handoff, versioning) + 70 tests
├── setup/
│   ├── claude-code/     ← install.sh / install.ps1 and setup guide
│   └── cowork/          ← create-zip.sh and Cowork setup guide
├── docs/                ← Architecture, getting started, concepts, decisions, model tiers
├── examples/            ← Worked programme examples
└── plans/               ← This repository's own plan files (5 phases, 18 loops)
```

---

## Documentation

| Document | What it covers |
|----------|---------------|
| `docs/getting-started.md` | First loop in 30 minutes — Claude Code and Cowork |
| `docs/concepts.md` | Glossary: ralph loops, handoff summaries, skill injection, gate review |
| `docs/architecture.md` | Two-agent pattern, state bus, gate review, three-tier hierarchy |
| `docs/model-tier-strategy.md` | Model costs, tier assignments, override guidance |
| `docs/adapting-to-new-platforms.md` | Five-contract adapter checklist with worked examples |
| `docs/decisions.md` | Ten architectural decisions with context and rationale |
| `docs/gate-review-architecture.md` | Gate review design spec: verdicts, retry, plugin pathway |

---

## Python API

```python
from platforms.python.state_manager import write_loop_ready, read_loop_complete
from platforms.python.plan_io import find_next_loop, get_pending_todos
from platforms.python.handoff import inject_handoff, make_empty_handoff
from platforms.python.versioning import create_retry_version, freeze_loop_file

loop = find_next_loop("plans")
write_loop_ready("state", loop_name=loop["loop_name"], ...)
# ... spawn orchestrator and worker ...
result = read_loop_complete("state")
```

No external dependencies. Standard library only. 70 unit tests across state management,
plan I/O, handoff injection, and versioning utilities. See `platforms/python/README.md`.

---

## Model Tiers

| Role | Model | Frequency |
|------|-------|-----------|
| Phase planning | Opus | Once per phase |
| Loop orchestration | Sonnet | Once per loop |
| Todo execution (default) | Sonnet | Per todo, with skill injection |
| Todo execution (low complexity) | Haiku | Per todo, when `complexity: low` |
| Gate review | Sonnet | Once per phase boundary |
| Closeout synthesis | Sonnet | Once per programme |
| Progress reporting | Sonnet | On demand |

---

## Future Development

### Plugin Marketplace Packaging

The system is plugin-ready with `.claude-plugin/plugin.json` and `hooks/hooks.json` already in place at `platforms/claude-code/`. Packaging for the Claude Code plugin marketplace requires only directory restructuring and submission.

### Headless Mode

`/next-loop --auto` and `/next-phase --auto` provide autonomous chaining within a session. For true headless operation across sessions, only a thin orchestrating script is needed — the state bus already supports it.

---

## Licence

MIT — see `LICENCE`.

## Contributing

See `CONTRIBUTING.md`. GitHub: [MungoHarvey/advanced-planning](https://github.com/MungoHarvey/advanced-planning)
