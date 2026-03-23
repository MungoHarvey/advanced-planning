# Advanced Planning System

A hierarchical, multi-agent planning framework for AI-powered project management. Structures
complex, multi-week programmes as sequences of bounded, verifiable execution loops with
automated code review, quality gates, and targeted skill injection. Built for Anthropic's
Claude models; adaptable to any agent framework.

```
Phase Plan (Opus — strategic planning)
├── Ralph Loop 001 (Sonnet: orchestrate) → (Sonnet: execute with skill injection)
├── Ralph Loop 002 ...
├── Ralph Loop N
└── Gate Review (Sonnet: code-review, phase-goals) → advance or retry
```

---

## Key Features

- **Hierarchical task planning** — three-tier hierarchy (Phase Plans → Ralph Loops → Todos) decomposes complex programmes into manageable, verifiable units
- **Multi-agent orchestration** — two-agent pattern with filesystem state bus coordinates planning and execution without shared memory
- **Targeted skill injection** — worker loads one specialist `SKILL.md` per todo, then discards it; each task gets exactly the expertise it needs
- **Quality gates** — gate review agents evaluate phase outputs before advancement; on failure, versioned retry files carry failure context so retries start smarter
- **Bounded execution loops** — fixed iteration limits and explicit completion conditions prevent context drift and scope creep
- **Handoff summaries** — three sentences (done/failed/needed) carry context between loops; enough for orientation, not enough to bloat
- **Platform-agnostic core** — core schemas, skills, and protocols work across Claude Code, Cowork, and any Python-based agent framework

---

## Why This Exists

Long-running AI agent sessions fail predictably: context fills, focus drifts, and outputs become
increasingly generic. The Advanced Planning System solves this with bounded execution, targeted
skill injection, and inter-phase quality gates — keeping agents focused, verifiable, and
resumable across sessions.

---

## Quick Start

### Claude Code (terminal / IDE)

```bash
git clone https://github.com/MungoHarvey/advanced-planning
cd advanced-planning
sh setup/claude-code/install.sh --project /path/to/your/project
cd /path/to/your/project && claude
/plan-and-phase   # explore codebase first, then plan
# or: /new-phase  # jump straight to phase planning
/next-loop --auto # execute all loops until phase complete
```

### Windows (PowerShell)

```powershell
git clone https://github.com/MungoHarvey/advanced-planning
cd advanced-planning
.\setup\claude-code\install.ps1 -Project C:\path\to\your\project
cd C:\path\to\your\project; claude
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
| Claude Code | Terminal / IDE | Slash commands (`/plan-and-phase`, `/next-loop`, `/run-gate`, `/next-phase`, `/progress-report`) | `setup/claude-code/` |
| Cowork | Desktop app | Natural language triggers | `setup/cowork/` |
| Python API | Any agent framework | Python import | `platforms/python/` |

---

## Commands

### Planning
| Command | What it does |
|---------|-------------|
| `/plan-and-phase [desc]` | Explore codebase read-only, then run full planning pipeline |
| `/new-phase [desc]` | Full pipeline: phase plan → loops → todos → skills → agents |
| `/new-loop [N]` | Decompose phase N into ralph loop stubs |

### Execution
| Command | What it does |
|---------|-------------|
| `/next-loop` | Execute the next pending loop (two-agent pattern) |
| `/next-loop --auto` | Chain loops until phase complete or failure |

### Quality Gates
| Command | What it does |
|---------|-------------|
| `/run-gate` | Spawn gate agents to evaluate phase outputs against success criteria |
| `/next-phase` | Run gate review → advance or retry. Use `--auto` to chain across phases |
| `/run-closeout` | Programme closeout — final narrative from documentary record |

### Diagnostics
| Command | What it does |
|---------|-------------|
| `/progress-report` | Structured report from plan files, handoffs, and git history |
| `/loop-status` | Show all loops with todo counts and handoff summaries |
| `/check-execution` | Six-area diagnostic for execution issues |
| `/model-check` | Verify model tier assignments |

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

**Two-agent pattern**: Orchestrator (Sonnet) prepares → Worker (Sonnet) executes → Main thread advances

**State bus**: `loop-ready.json` → `loop-complete.json` → `history.jsonl`

**Gate review**: `/run-gate` spawns review agents at phase boundaries → structured verdicts → `/next-phase` advances or creates versioned retry files

See `docs/architecture.md` for the full explanation.

---

## Skills Ecosystem

The planning system is designed to work with a wider ecosystem of specialist skills:

**[awesome-agent-skills](https://github.com/MungoHarvey/awesome-agent-skills)** — A curated
catalogue of agent skills for Claude Code and Cowork, including a VoltAgent skill-finder that
lets you pull skills from the VoltAgent marketplace on demand.

**[claude-scientific-skills](https://github.com/anthropics/claude-scientific-skills)** *(community)* — Domain-specific skills for scientific and research workflows.

To use external skills: place the `SKILL.md` in your project's `.claude/skills/[skill-name]/`
directory. The worker loads it automatically via targeted injection when a todo references it.

---

## Repository Structure

```
advanced-planning/
├── core/
│   ├── schemas/          ← Plan file schemas (phase-plan, ralph-loop, todo, handoff)
│   ├── skills/           ← 6 planning skills (model-agnostic instruction sets)
│   ├── agents/           ← Abstract roles (orchestrator, worker, gate-reviewer)
│   └── state/            ← State bus JSON schemas (loop-ready, loop-complete, gate-verdict)
├── platforms/
│   ├── claude-code/      ← 11 slash commands, 8 agents, hooks, settings, plugin scaffold
│   ├── cowork/           ← Routing SKILL.md, agent prompts, checkpoint.sh
│   └── python/           ← Python API (state_manager, plan_io, handoff, versioning) + 70 tests
├── setup/
│   ├── claude-code/      ← install.sh / install.ps1 and setup guide
│   └── cowork/           ← create-zip.sh and Cowork setup guide
├── docs/                 ← Architecture, getting started, concepts, decisions, model tiers
├── examples/             ← Worked programme examples
└── plans/                ← This repository's own plan files (5 phases, 18 loops)
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

| Role | Model | When |
|------|-------|------|
| Phase planning | Opus | Once per phase |
| Loop orchestration | Sonnet | Once per loop |
| Todo execution (default) | Sonnet | Per todo, with skill injection |
| Todo execution (low complexity) | Haiku | Per todo, when `complexity: low` |
| Gate review | Sonnet | Once per phase boundary |
| Closeout synthesis | Sonnet | Once per programme |
| Progress reporting | Sonnet | On demand (read-only synthesis) |

---

## Gate Review & Quality Gates

At each phase boundary, `/run-gate` spawns review agents to evaluate whether success criteria
are met before advancing:

1. **Code review agent** — checks code quality, patterns, CLAUDE.md compliance
2. **Phase goals agent** — verifies each success criterion against actual artifacts
3. **Security agent** *(optional)* — scans for exposed secrets and injection patterns
4. **Test agent** *(optional)* — runs test suites and checks coverage thresholds

On **pass**: phase advances. On **fail**: versioned retry files (`phase-N-ralph-loops-v2.md`)
are created with failure context injected, so the retry starts knowing what went wrong.

Verdicts use confidence scoring (threshold: 80) to filter false positives. All verdicts are
immutable — one file per agent per attempt, preserving the complete documentary record.

---

## Installation via Plugin (Cowork)

The easiest way to use this system in Cowork is via the **Advanced Planning plugin**, which
packages the core skills, agent prompts, and checkpoint utilities into a single installable
bundle. Install it from the Cowork plugin manager, then select your project folder and start
a session.

For manual setup without the plugin, follow `setup/cowork/README.md`.

---

## Future Development

### Plugin Marketplace Packaging

The system is structured as plugin-ready with `.claude-plugin/plugin.json` and `hooks/hooks.json`
already in place at `platforms/claude-code/`. Packaging for the Claude Code plugin marketplace
requires only directory restructuring and submission — no core changes needed.

### Headless Mode

`/next-loop --auto` provides autonomous loop chaining within a session. For true headless
operation across sessions — a daemon that resumes automatically after session boundaries —
only a thin orchestrating script is needed; the state bus already supports it.

---

## Licence

MIT — see `LICENCE`.

## Contributing

See `CONTRIBUTING.md`. GitHub: [MungoHarvey/advanced-planning](https://github.com/MungoHarvey/advanced-planning)
