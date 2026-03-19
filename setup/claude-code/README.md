# Claude Code Setup

Sets up the Advanced Planning System in [Claude Code](https://claude.ai/claude-code) — the
terminal-based agentic coding tool.

Installation copies slash commands, skills, and agent definitions into your project's `.claude/`
directory (or your global Claude Code config for commands you want everywhere).

---

## Prerequisites

- [Claude Code](https://claude.ai/claude-code) installed
- This repository cloned to your computer
- `bash` or `sh` available in your terminal

---

## Installation

### Project install (recommended)

Installs everything into a single project's `.claude/` directory:

```sh
cd /path/to/advanced-planning
sh setup/claude-code/install.sh --project /path/to/your/project
```

This creates `.claude/` in your project with:

```
.claude/
├── commands/          ← Slash commands (/new-phase, /new-loop, /next-loop, /loop-status)
├── skills/            ← Core planning skills (symlinked from core/skills/)
├── agents/            ← Agent definitions (orchestrator, worker)
└── settings.json      ← Claude Code configuration
```

After installation, open Claude Code in your project directory and run `/next-loop` to begin.

### Global commands (optional)

Installs slash commands globally so they are available in every Claude Code session:

```sh
sh setup/claude-code/install.sh --global
```

Note: skills are project-scoped, not global. Run the `--project` install per project so
each project has its own `core/skills/` local copy for skill injection.

### Reference mode (dry run)

Prints the paths that would be installed without copying anything:

```sh
sh setup/claude-code/install.sh --dry-run --project /path/to/your/project
```

---

## Slash Commands

After installation, these commands are available in Claude Code:

| Command | What it does |
|---------|-------------|
| `/new-phase` | Creates a phase plan document using the `phase-plan-creator` skill |
| `/new-loop` | Decomposes a phase into ralph loops using the `ralph-loop-planner` skill |
| `/next-loop` | Runs the next pending loop: spawns orchestrator → worker → reports back |
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
/new-phase
```

Claude will guide you through creating your first phase plan. Then:

```
/new-loop
/next-loop
```

And you're running.

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

Skills are copied (not symlinked by default) so each project has an independent copy.
Use `--symlink` if you prefer to share a single skills directory:

```sh
sh setup/claude-code/install.sh --project /path/to/your/project --symlink
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
