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
├── commands/     ← Slash commands (/plan-and-phase, /new-phase, /next-loop, /progress-report, etc.)
├── skills/       ← Core planning skills (including progress-report)
├── agents/       ← Agent definitions (orchestrator, worker)
├── schemas/      ← JSON and Markdown schemas
├── state/        ← Runtime state directory (loop-ready.json etc.)
└── settings.json ← Claude Code configuration (includes planning-mode hooks)
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

> **Skill path resolution** — When a command or agent references `.claude/skills/<name>/`,
> Claude resolves it in this order:
> 1. **Project-local** — `.claude/skills/<name>/` (preferred)
> 2. **Global fallback** — `~/.claude/skills/<name>/` (used when no local copy is present)
>
> Plans and runtime state (`.claude/plans/`, `.claude/state/`, `.claude/logs/`) are always
> project-local — there is no global fallback for these.

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

| Command | What it does |
|---------|-------------|
| `/plan-and-phase [desc]` | Read-only codebase exploration → human review → full planning pipeline |
| `/new-phase [desc]` | Creates a phase plan document using the `phase-plan-creator` skill |
| `/new-loop [phase]` | Decomposes a phase into ralph loops using the `ralph-loop-planner` skill |
| `/next-loop` | Runs the next pending loop: spawns orchestrator → worker → reports back |
| `/next-loop --auto` | Chains loops automatically until phase complete or failure |
| `/progress-report` | Structured report from plan files, handoffs, and git history |
| `/loop-status` | Shows current loop, todo states, and handoff summary |

---

## How `/next-loop` Works

```
1. Main thread reads plans/ to find the next pending loop
2. Spawns orchestrator (Sonnet): reads loop, populates todos if needed, writes loop-ready.json
3. Spawns worker (Haiku): reads loop-ready.json, executes todos with targeted skill injection
4. Worker writes loop-complete.json and handoff_summary
5. Main thread reports: what was done, what failed, what comes next
```

Each agent is a subprocess spawned with `claude --model` and a self-contained prompt. Neither
spawns the other — the main thread (the `/next-loop` command) handles all sequencing.

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
