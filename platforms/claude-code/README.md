# Advanced Planning System v8 — Claude Code Adapter

A hierarchical multi-agent planning framework for long-running AI coding projects. Structures complex work into bounded, verifiable loops with explicit handoffs between planning and execution agents.

## What It Does

The system structures complex work into three tiers:

- **Phase plans** (Opus) — strategic scope, deliverables, and success criteria per phase
- **Ralph loops** (Sonnet) — bounded, verifiable iterations with explicit todo lists
- **Todo execution** (Haiku) — atomic task execution with targeted skill loading per task

Each loop produces a concise handoff summary (done/failed/needed) that carries context across sessions without dragging forward full conversation history.

---

## Installation

### Option 1: Project install (recommended)

Installs commands, skills, agents, and settings into a single project:

```bash
cd advanced-planning
./platforms/claude-code/install.sh --project /path/to/your/project
```

This creates `.claude/` in your project with everything configured and ready.

### Option 2: Global commands

Installs slash commands globally so they are available in all Claude Code sessions:

```bash
cd advanced-planning
./platforms/claude-code/install.sh --global
```

Note: skills are not copied globally — run `--project` install per project to have skills locally.

### Option 3: Reference mode (no install)

Prints the paths to reference skills manually, without copying any files:

```bash
./platforms/claude-code/install.sh --reference
```

---

## Quick Start (5 minutes)

After `--project` install, open a Claude Code session in your project and:

**1. Add Planning State to your CLAUDE.md**

Copy the `## Planning State` section from the installed template:
```bash
cat .claude/claude-md-template.md
```
Paste the `## Planning State` block into your project's `CLAUDE.md`.

**2. Create your first phase plan**

```
/new-phase Implement a REST API for user authentication with JWT tokens
```

Claude will generate a structured phase plan with objectives, scope, deliverables, success criteria, and risk assessment — then automatically decompose it into 3–5 executable ralph loops.

**3. Check what was planned**

```
/loop-status
```

Review the loops, todos, and skill assignments before execution begins.

**4. Execute the first loop**

```
/next-loop
```

Claude spawns `ralph-orchestrator` (Sonnet) to prepare the loop, then `ralph-loop-worker` (Haiku) to execute it. Each todo is worked with its assigned skill loaded just-in-time.

**5. Continue**

Repeat `/next-loop` until the phase is complete. Each run produces a handoff summary and a git checkpoint commit.

---

## Command Reference

| Command | Description | Key Arguments |
|---------|-------------|---------------|
| `/new-phase [description]` | Full planning pipeline: phase plan → loops → todos → skills → agents | Description of what to accomplish |
| `/new-loop [phase]` | Decompose a phase plan into ralph loops only | Phase number or file path |
| `/next-loop` | Execute the next pending loop (two-agent pattern) | None |
| `/loop-status` | Show all loops with todo counts and handoff summaries | None |
| `/check-execution` | Six-area diagnostic: hooks, workers, todos, handoffs, git, output files | None |
| `/model-check` | Verify model tier assignments across skills and agents | None |

---

## Directory Structure After Install

```
your-project/
└── .claude/
    ├── commands/           ← Slash commands (6 files)
    │   ├── new-phase.md
    │   ├── new-loop.md
    │   ├── next-loop.md
    │   ├── loop-status.md
    │   ├── check-execution.md
    │   └── model-check.md
    ├── skills/             ← Core planning skills (symlinked from core/)
    │   ├── phase-plan-creator/
    │   ├── ralph-loop-planner/
    │   ├── plan-todos/
    │   ├── plan-skill-identification/
    │   └── plan-subagent-identification/
    ├── agents/             ← Agent definitions (3 files)
    │   ├── ralph-orchestrator.md   (Sonnet)
    │   ├── ralph-loop-worker.md    (Haiku)
    │   └── analysis-worker.md      (Haiku)
    ├── settings.json       ← Permissions + execution logging hooks
    ├── plans/              ← Phase plans and ralph loop files (created at runtime)
    ├── state/              ← loop-ready.json, loop-complete.json (runtime)
    └── logs/               ← execution.log (runtime)
```

---

## How the Two-Agent Pattern Works

Each `/next-loop` cycle runs two agents sequentially:

```
/next-loop (main thread)
    │
    ├─ Spawn ralph-orchestrator (Sonnet)
    │    Reads plan → populates todos if needed → writes loop-ready.json
    │    Returns
    │
    ├─ Read loop-ready.json → print summary
    │
    ├─ Spawn ralph-loop-worker (Haiku)
    │    Reads loop-ready.json → executes todos → writes loop-complete.json
    │    Returns
    │
    └─ Read loop-complete.json → update CLAUDE.md → git commit → print summary
```

The main thread (the `/next-loop` command) handles all sequencing decisions. Neither agent spawns the other — this is required because Claude Code agents cannot spawn further subagents.

---

## Targeted Skill Injection

The `ralph-loop-worker` does **not** load all skills at startup. For each todo, it:

1. Reads the `skill:` field from the todo
2. If non-NA: loads `SKILL.md` for that skill immediately before executing the task
3. Executes the task with that skill's instructions active
4. Clears the skill before moving to the next todo

This prevents skill instructions from one task bleeding into another, and keeps context focused on the current task's precise requirements.

---

## Troubleshooting

### `/next-loop` runs but produces no output files

Run `/check-execution` — Check 3 (Todo Progression) and Check 6 (File Write Activity) will identify whether todos are being marked complete without real work.

Most common cause: todos have vague `outcome:` fields that were marked complete on effort rather than verification. Fix: rewrite the `outcome:` field to be an observable condition (`file exists at path X` rather than `task done`).

### Hook environment variables show `unknown`

Check 1 in `/check-execution` identifies this. The `$CLAUDE_MODEL` and `$CLAUDE_AGENT_NAME` variables may not be set in the hook shell context. This is a known Claude Code limitation — model tier routing still works correctly, but cannot be confirmed from `execution.log` alone. Use `/model-check` to verify frontmatter model assignments.

### `settings.json` conflicts with existing project settings

The installer saves the planning system settings as `settings.planning.json` when a `settings.json` already exists. Merge the `hooks:` section manually — the `permissions.allow` section can be merged or replaced with whichever is more permissive.

### Loops complete but handoff_summary fields are empty

The worker skipped the completion protocol. Run `/check-execution` Check 4. To fix: edit the loop file and manually add the handoff summary based on what was produced, then run `/next-loop` to continue.

---

## Model Tier Summary

| Role | Model | Why |
|------|-------|-----|
| Planning skills (`/new-phase` pipeline) | Opus | Highest reasoning demand; runs once per phase |
| `ralph-orchestrator` | Sonnet | Loop preparation: moderate complexity, reads plan, assembles context |
| `ralph-loop-worker` | Haiku | Execution: high frequency, bounded tasks, cost matters at scale |
| `analysis-worker` | Haiku | Delegated execution: same rationale as worker |
