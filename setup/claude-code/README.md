# Claude Code Setup

Sets up the Advanced Planning System in [Claude Code](https://claude.ai/claude-code) — the
terminal-based agentic coding tool.

Installation copies slash commands, skills, and agent definitions into your project's `.claude/`
directory (or your global Claude Code config for commands you want everywhere).

---

## Prerequisites

- [Claude Code](https://claude.ai/claude-code) installed
- This repository cloned to your computer

---

## Installation

Two installer scripts are provided — use whichever matches your OS.

| Script | Platform |
|--------|----------|
| `setup/claude-code/install.ps1` | Windows (PowerShell) |
| `setup/claude-code/install.sh` | macOS / Linux |

---

### Project install (recommended)

Installs commands, skills, agents, and schemas into a single project's `.claude/` directory.

**Windows:**
```powershell
cd C:\path\to\advanced-planning
.\setup\claude-code\install.ps1 -Project C:\path\to\your\project
```

**macOS / Linux:**
```bash
cd /path/to/advanced-planning
sh setup/claude-code/install.sh --project /path/to/your/project
```

This creates `.claude/` in your project:

```
.claude/
├── commands/     ← Slash commands (11 files)
│   ├── plan-and-phase.md, new-phase.md, new-loop.md, next-loop.md
│   ├── run-gate.md, run-closeout.md, next-phase.md     ← gate review commands
│   ├── progress-report.md, loop-status.md
│   └── check-execution.md, model-check.md
├── skills/       ← Core planning skills (6 skills)
│   ├── phase-plan-creator/, ralph-loop-planner/, plan-todos/
│   ├── plan-skill-identification/, plan-subagent-identification/
│   └── progress-report/
├── agents/       ← Agent definitions (9 files)
│   ├── orchestrator.md, worker.md                       ← abstract core roles
│   ├── ralph-orchestrator.md, ralph-loop-worker.md      ← loop execution agents
│   ├── analysis-worker.md                               ← standalone task agent
│   ├── gate-reviewer.md                                 ← abstract gate role
│   ├── code-review-agent.md, phase-goals-agent.md       ← default gate agents
│   ├── security-agent.md, test-agent.md                 ← optional gate agents
│   └── programme-reporter.md                            ← closeout agent
├── schemas/      ← JSON and Markdown schemas
├── state/        ← Runtime state (loop-ready.json, loop-complete.json, sentinels)
├── logs/         ← execution.log (written by session hooks)
└── settings.json ← Permissions, planning-mode hooks, gate-review-mode hooks
```

Plans and gate verdicts are stored in the project root:
```
plans/
├── phase-N.md, phase-N-ralph-loops.md    ← plan files
├── PLANS-INDEX.md                        ← master tracker with version columns
└── gate-verdicts/                        ← verdict JSON files from gate agents
```

Open Claude Code in your project and run `/plan-and-phase` to explore and plan, or `/next-loop` to begin execution directly.

---

### Global install (optional)

Installs commands, skills, agents, and schemas globally into `~/.claude/` so they are
available in every Claude Code session.

**Windows:**
```powershell
.\setup\claude-code\install.ps1 -Global
```

**macOS / Linux:**
```bash
sh setup/claude-code/install.sh --global
```

This installs into `~/.claude/`:

```
~/.claude/
├── commands/     ← Slash commands available in every project
├── skills/       ← Core planning skills (global fallback)
├── agents/       ← Agent definitions (global fallback)
└── schemas/      ← JSON and Markdown schemas
```

> **When to use global vs project install:**
>
> | Scenario | Recommendation |
> |----------|---------------|
> | Single project with planning needs | `--project` only |
> | Multiple projects, same planning setup | `--global` for commands/skills/agents, then `--project` for settings.json and state dir |
> | Trying it out before committing | `--global` — commands available everywhere, no project changes |
> | Team sharing via git | `--project` — `.claude/` directory checked into the repo |
>
> **Path resolution order** — When a command or agent references `.claude/skills/<name>/`,
> Claude resolves it in this order:
> 1. **Project-local** — `.claude/skills/<name>/` (preferred)
> 2. **Global fallback** — `~/.claude/skills/<name>/` (used when no local copy is present)
>
> Plans and runtime state (`plans/`, `.claude/state/`, `.claude/logs/`) are always
> project-local — there is no global fallback for these. The `settings.json` with hooks
> is only written by `--project` install (global installs do not include hooks).

---

### Dry run (preview only)

Prints what would be installed without writing any files.

**Windows:**
```powershell
.\setup\claude-code\install.ps1 -Project C:\path\to\your\project -DryRun
```

**macOS / Linux:**
```bash
sh setup/claude-code/install.sh --dry-run --project /path/to/your/project
```

---

### Symlink / Junction mode

Links to `core/skills/` instead of copying, so skill updates are reflected immediately.
`--symlink` also works with `--global` to symlink skills into `~/.claude/skills/`.

**Windows** (creates a directory junction — no elevated permissions required):
```powershell
.\setup\claude-code\install.ps1 -Project C:\path\to\your\project -Symlink
.\setup\claude-code\install.ps1 -Global -Symlink
```

**macOS / Linux:**
```bash
sh setup/claude-code/install.sh --project /path/to/your/project --symlink
sh setup/claude-code/install.sh --global --symlink
```

---

## Slash Commands

After installation, these commands are available in Claude Code:

### Planning commands
| Command | What it does |
|---------|-------------|
| `/plan-and-phase [desc]` | Read-only codebase exploration → human review → full planning pipeline |
| `/new-phase [desc]` | Full pipeline: phase plan → loops → todos → skills → agents |
| `/new-loop [phase]` | Decomposes a phase into ralph loops using the `ralph-loop-planner` skill |

### Execution commands
| Command | What it does |
|---------|-------------|
| `/next-loop` | Runs the next pending loop: spawns orchestrator → worker → reports back |
| `/next-loop --auto` | Chains loops automatically until phase complete or failure |

### Gate review commands
| Command | What it does |
|---------|-------------|
| `/run-gate` | Spawns gate agents (code-review, phase-goals) to evaluate phase outputs |
| `/next-phase` | Runs gate review → on pass advances; on fail creates versioned retry files. Use `--auto` to chain across phases. |
| `/run-closeout` | Spawns programme-reporter for final narrative synthesis |

### Diagnostic commands
| Command | What it does |
|---------|-------------|
| `/progress-report` | Structured report from plan files, handoffs, and git history |
| `/loop-status` | Shows current loop, todo states, and handoff summary |
| `/check-execution` | Six-area diagnostic for worker/loop execution issues |
| `/model-check` | Verify model tier assignments across skills and agents |

---

## How `/next-loop` Works

```
1. Main thread reads plans/ to find the next pending loop
2. Spawns orchestrator (Sonnet): reads loop, populates todos if needed, writes loop-ready.json
3. Spawns worker (Sonnet): reads loop-ready.json, executes todos with targeted skill injection
4. Worker writes loop-complete.json and handoff_summary
5. Main thread reports: what was done, what failed, what comes next
```

Each agent is a subprocess spawned via the Agent tool. Neither spawns the other — the main
thread (the `/next-loop` command) handles all sequencing.

## How `/run-gate` Works

```
1. Main thread verifies all loops in the phase are complete
2. Creates gate-review-mode sentinel (restricts agents to read-only + verdict writes)
3. Spawns gate agents sequentially (default: code-review-agent, phase-goals-agent)
4. Each agent writes a verdict JSON to plans/gate-verdicts/
5. Removes sentinel, aggregates verdicts (all pass → gate_pass; any fail → gate_fail)
6. Appends event to history.jsonl
```

## How `/next-phase` Works

```
1. Runs gate review (same as /run-gate)
2. On pass: marks phase complete, updates CLAUDE.md, prompts for /new-phase
3. On fail: creates versioned retry file (phase-N-ralph-loops-v2.md),
   injects gate_failure_context, freezes original, updates PLANS-INDEX.md
```

---

## First Use

After installing into your project:

```sh
cd /path/to/your/project
claude  # opens Claude Code in this project
```

In the Claude Code session:

```
/plan-and-phase
```

Claude explores the codebase read-only, presents findings for review, then runs the full
planning pipeline. Alternatively, if you already know what you want to build:

```
/new-phase
```

Then run:

```
/next-loop          ← execute one loop at a time
/next-loop --auto   ← chain all loops until the phase is done
```

Check progress at any time:

```
/progress-report
```

---

## Project Layout After First Loop

```
your-project/
├── .claude/               ← installed by setup/claude-code/install.sh
│   ├── commands/
│   ├── skills/
│   ├── agents/
│   ├── state/             ← created at runtime (loop-ready.json, loop-complete.json)
│   └── settings.json
└── plans/                 ← created by /new-phase and /new-loop
    ├── PLANS-INDEX.md
    ├── phase-1.md
    ├── phase-1-ralph-loops.md
    └── ralph-loop-001.md
```

---

## Updating Skills

When you pull a new version of this repository, re-run the install to update your project:

```sh
sh setup/claude-code/install.sh --project /path/to/your/project
```

To update a global install:

```sh
sh setup/claude-code/install.sh --global
```

Skills are copied (not symlinked by default) so each project has an independent copy.
Use `--symlink` if you prefer to share a single skills directory across all projects:

```sh
sh setup/claude-code/install.sh --project /path/to/your/project --symlink
sh setup/claude-code/install.sh --global --symlink
```

---

## Troubleshooting

**Commands not showing up after install.**
Run `claude --version` to confirm Claude Code is installed and the project path is correct.
Check that `.claude/commands/` contains the `.md` files.

**Worker not loading skills per todo.**
The `targeted skill injection` protocol is mandatory. If you have customised the worker prompt,
ensure the per-todo skill load/unload cycle is present. See `core/agents/worker.md`.

**`loop-ready.json` written but worker didn't start.**
Run `/next-loop` again — the main thread reads `loop-ready.json` and spawns the worker
as a separate step. If it still doesn't start, check the state directory path in settings.json.
