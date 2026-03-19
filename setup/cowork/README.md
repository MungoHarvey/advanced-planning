# Cowork Setup

Sets up the Advanced Planning System in [Claude Cowork](https://claude.ai) — the desktop tool
for non-developers to automate file and task management.

---

## Option A — Install via Plugin (Recommended)

The simplest way to get started is the **Advanced Planning plugin** for Cowork, which bundles
all the skills, agent prompts, and checkpoint utilities into a single installable package.

1. Open Claude Cowork
2. Go to **Settings → Plugins → Browse**
3. Search for **Advanced Planning**
4. Click **Install**
5. Start a new session and say: "Start a new planning session for [your project]"

The plugin handles all path configuration automatically. No folder mounting or manual file
setup required.

---

## Option B — Manual Setup (Folder Mount)

If you prefer to work directly from the repository — for example to customise skills or
contribute changes — follow the steps below. No terminal required; you mount a folder and
Claude finds the skills automatically.

### What You Need

- Claude Cowork (desktop app)
- This repository cloned or downloaded to your computer

---

## Setup

### Step 1 — Point Cowork at this folder

Open Claude Cowork. Click **Select folder** and choose the root of this repository
(the folder that contains `core/`, `platforms/`, `docs/`, etc.).

Claude will now have access to all the skill files, agent prompts, and checkpoint utilities.

### Step 2 — Create your project's planning state file

In the folder Cowork is watching, create a file called `planning-state.md`:

```markdown
# Planning State

## Current Loop
None — starting fresh.

## Session Notes
[Add notes here as you work]
```

This is the orientation file Claude reads at the start of each session to understand where you are.

### Step 3 — Start a session

Begin a new Cowork session and say:

> "Start a new planning session for [brief description of your project]"

Claude will load the routing skill, orient itself, and guide you through creating your first
phase plan.

---

## Optional: Build a portable zip

If you want to share the system with a colleague or keep a self-contained copy:

```sh
sh setup/cowork/create-zip.sh
```

This produces `advanced-planning-cowork-{timestamp}.zip`. Your colleague can unzip it anywhere
and point Cowork at the resulting folder.

---

## Natural Language Triggers

Once set up, you control the system by describing what you want. Claude reads the routing skill
and loads the appropriate specialist skill automatically.

| Say something like… | What happens |
|---------------------|--------------|
| "Start a new planning session" | Claude orients to your project state |
| "Create a phase plan for Phase 1" | `phase-plan-creator` skill loads |
| "Plan the loops for Phase 2" | `ralph-loop-planner` skill loads |
| "Fill in the todos for loop 003" | `plan-todos` skill loads |
| "Assign skills to loop 003 todos" | `plan-skill-identification` skill loads |
| "Assign agents to loop 003 todos" | `plan-subagent-identification` skill loads |
| "Run loop 003" | Orchestrator agent spawned, then worker agent |
| "Save a checkpoint" | `sh platforms/cowork/checkpoint.sh save` runs |
| "Show me all checkpoints" | `sh platforms/cowork/checkpoint.sh list` runs |
| "Restore checkpoint from yesterday" | `sh platforms/cowork/checkpoint.sh restore {stamp}` runs |

---

## Loop Execution Flow

When you say "run loop 003":

```
1. Claude (orchestrator role) reads the loop file
2. Populates any empty todos using plan-todos, plan-skill-identification, plan-subagent-identification
3. Writes loop-ready.json to the state directory
4. Claude (worker role) reads loop-ready.json
5. Executes each todo with targeted skill injection (one skill loaded per todo)
6. Writes loop-complete.json and handoff_summary when done
7. Reports back to you with what was completed and what comes next
```

The orchestrator and worker are both Claude, spawned with different prompts from
`platforms/cowork/agents/`. You don't need to manage this — just say "run the next loop".

---

## Checkpoint Commands

State snapshots preserve your `plans/` and `state/` directories so you can roll back if needed:

```sh
# Save a checkpoint before risky work
sh platforms/cowork/checkpoint.sh save before-loop-003

# List all saved checkpoints
sh platforms/cowork/checkpoint.sh list

# Restore a checkpoint by timestamp prefix
sh platforms/cowork/checkpoint.sh restore 20250312-143022
```

Snapshots are stored in `state/snapshots/` and excluded from zip packages.

---

## Workspace Layout

After a few loops, your project folder will look like this:

```
your-project/
├── advanced-planning/     ← this repo (mounted in Cowork)
│   ├── core/
│   ├── platforms/cowork/
│   └── ...
├── plans/                 ← your phase plans and loop files
│   ├── PLANS-INDEX.md
│   ├── phase-1.md
│   ├── phase-1-ralph-loops.md
│   └── ralph-loop-001.md
├── state/                 ← state bus files (loop-ready.json etc.)
│   └── snapshots/
└── planning-state.md      ← session orientation file
```

---

## Troubleshooting

**Claude isn't loading skills automatically.**
Make sure the Cowork folder includes `platforms/cowork/SKILL.md` — this is the routing file
that maps your requests to the right specialist skill. If it is missing, re-clone the repository
and select the correct root folder.

**loop-ready.json was written but execution didn't start.**
Start a fresh session and say "run the next loop". The orchestrator and worker are separate
agent invocations — Claude needs explicit instruction to proceed to the worker step.

**I want to reset and start a loop over.**
Restore the pre-loop checkpoint: `sh platforms/cowork/checkpoint.sh restore {stamp}`.
Then delete `state/loop-complete.json` if it exists, and run the loop again.

---

## Comparison: Cowork vs Claude Code

| | Cowork | Claude Code |
|---|--------|-------------|
| Setup | Mount folder, start session | Run `install.sh` in terminal |
| Triggers | Natural language | Slash commands (`/next-loop`) |
| Checkpoints | POSIX sh snapshots | `git commit` |
| Agent spawning | Agent tool with model param | `claude --model` subprocess |
| Skills | Loaded via routing SKILL.md | Loaded per-todo by worker |
| Best for | Non-developers, planning work | Developers, code-heavy projects |

Both platforms run the same core protocol. The difference is how you invoke it.
