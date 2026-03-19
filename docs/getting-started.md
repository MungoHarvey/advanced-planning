# Getting Started

Choose your platform:

- **[Claude Code](#claude-code)** — terminal / IDE, slash commands, developers
- **[Cowork](#cowork)** — desktop app, natural language, no terminal needed

Both run the same core planning protocol. The difference is how you invoke it.

---

## Claude Code

Takes you from zero to a completed first ralph loop using slash commands. Approximately 30 minutes.

**Prerequisites**: Claude Code installed (`claude --version`), a project directory.

### Step 1 — Install

Clone the repository and run the installer:

```bash
git clone https://github.com/MungoHarvey/advanced-planning
cd advanced-planning
sh setup/claude-code/install.sh --project /path/to/your/project
```

Verify the install:

```bash
ls /path/to/your/project/.claude/
# commands/  skills/  agents/  schemas/  state/  settings.json
```

See `setup/claude-code/README.md` for install options (`--global`, `--symlink`, `--dry-run`).

### Step 2 — Create a Phase Plan

```bash
cd /path/to/your/project
claude
```

```
/new-phase
```

Claude asks about your project — what you're building, what success looks like, how many loops
you expect. After answering you'll have `plans/phase-1.md` with scope, loop specifications, and
success criteria. Edit it directly if anything looks wrong; the system reads plan files as
source of truth.

**Expected output:**
```
plans/
└── phase-1.md
```

### Step 3 — Decompose Into Loops

```
/new-loop 1
```

Reads `phase-1.md` and creates `phase-1-ralph-loops.md` with YAML frontmatter stubs for each
loop: `name`, `task_name`, `max_iterations`, `on_max_iterations`, empty `todos[]`, and a blank
`handoff_summary`. Todos are populated when each loop starts.

**Expected output:**
```
plans/
├── phase-1.md
└── phase-1-ralph-loops.md
```

### Step 4 — Run the First Loop

```
/next-loop
```

Full two-agent cycle:

1. Git checkpoint — saves state before the loop begins
2. Orchestrator (Sonnet) — reads plan, populates todos if needed, writes `loop-ready.json`
3. Worker (Haiku) — reads `loop-ready.json`, executes todos with targeted skill injection, writes `loop-complete.json`
4. Updates planning state and commits all outputs

**Expected output:**
```
.claude/state/
├── loop-ready.json
└── loop-complete.json

plans/phase-1-ralph-loops.md  ← todos marked completed, handoff_summary populated
```

### Step 5 — Check Progress

```
/loop-status
```

```
Phase 1: My Project
Loop                     Status        Todos
─────────────────────────────────────────────
ralph-loop-001           ✅ complete   4/4
ralph-loop-002           ⏳ pending    0/3
```

Run `/next-loop` again for the next pending loop.

### Command Reference

| Command | What it does |
|---------|-------------|
| `/new-phase` | Create a phase plan using `phase-plan-creator` skill |
| `/new-loop [N]` | Decompose phase N into loop files using `ralph-loop-planner` skill |
| `/next-loop` | Execute the next pending loop (full two-agent cycle) |
| `/loop-status` | Show progress table |
| `/check-execution` | Diagnose if the worker isn't progressing |
| `/model-check` | Verify agent model tiers |

### Troubleshooting

**The worker isn't completing todos.** Run `/check-execution` — it diagnoses six failure areas:
hook environment, worker spawning, todo progression, handoff population, git checkpoints, file
write activity.

**A todo failed and I need to retry.** Find the todo in the loop file and change `status` from
`cancelled` back to `pending`. Run `/next-loop` — the orchestrator will see pending todos and
prepare accordingly.

**I want to edit a loop's scope.** Edit the loop file directly. The orchestrator reads plan
files fresh each time, so edits take effect immediately on the next `/next-loop`.

---

## Cowork

Sets up the planning system in Claude Cowork — no terminal required.
Approximately 15 minutes.

**Prerequisites**: Claude Cowork desktop app.

### Step 1 — Mount the folder

Clone or download this repository. Open Claude Cowork, click **Select folder**, and choose
the `advanced-planning/` root directory (the folder containing `core/`, `platforms/`, etc.).

### Step 2 — Create a planning state file

In the mounted folder, create `planning-state.md`:

```markdown
# Planning State

## Current Loop
None — starting fresh.

## Session Notes
[Add context about your project here]
```

### Step 3 — Start a session

Begin a new Cowork session and say:

> "Start a new planning session for [brief description of your project]"

Claude loads the routing skill, orients to your project, and guides you through creating
your first phase plan.

### Natural Language Triggers

| Say something like… | What Claude does |
|---------------------|------------------|
| "Start a new planning session" | Orients to current state |
| "Create a phase plan for Phase 1" | Loads `phase-plan-creator` skill |
| "Plan the loops for Phase 2" | Loads `ralph-loop-planner` skill |
| "Fill in the todos for loop 003" | Loads `plan-todos` skill |
| "Assign skills to loop 003 todos" | Loads `plan-skill-identification` skill |
| "Run loop 003" | Spawns orchestrator, then worker |
| "Save a checkpoint" | Runs `sh platforms/cowork/checkpoint.sh save` |
| "What's the status of my loops?" | Reads all loop files and reports |

### Optional: portable zip

To share the system with a colleague:

```sh
sh setup/cowork/create-zip.sh
```

Produces `advanced-planning-cowork-{timestamp}.zip`. Unzip anywhere, mount in Cowork.

See `setup/cowork/README.md` for the full Cowork guide including checkpoint commands,
workspace layout, and troubleshooting.

---

## Next Steps

- `docs/concepts.md` — Glossary: ralph loops, handoff summaries, targeted skill injection
- `docs/architecture.md` — Two-agent pattern, state bus, three-tier hierarchy
- `docs/model-tier-strategy.md` — Model costs and how to optimise them
- `examples/planning-system-restructure/` — This repository built using itself (dogfood)
- `docs/adapting-to-new-platforms.md` — How to build an adapter for your own platform
