# Advanced Planning — Cowork Adapter

Run the v8 hierarchical planning system inside Cowork using the Agent tool. No git required — snapshot checkpoints keep your work safe.

---

## What This Does

The Cowork adapter gives you a three-tier planning workflow directly in your Cowork session:

- **Phases** (strategic, Opus) → break a project into bounded phases
- **Ralph loops** (tactical, Sonnet) → plan each loop as a sequence of verifiable todos
- **Todos** (execution, Sonnet default; Haiku for `complexity: low`) → actually do the work, one task at a time, with the right skill loaded for each

---

## Setup (3 Steps)

### Step 1 — Add the skill to Cowork

Copy (or symlink) this adapter folder into your Cowork skills directory:

```
platforms/cowork/SKILL.md  →  your Cowork skills folder
platforms/cowork/agents/   →  alongside SKILL.md
platforms/cowork/checkpoint.sh → alongside SKILL.md
```

The folder structure Cowork needs:

```
skills/
└── advanced-planning/
    ├── SKILL.md               ← routing entry point
    ├── checkpoint.sh          ← snapshot utility
    └── agents/
        ├── orchestrator-prompt.md
        └── worker-prompt.md
```

### Step 2 — Set up your workspace

Create a `planning-state.md` file in your workspace folder. This replaces CLAUDE.md from the Claude Code adapter:

```markdown
# Planning State

## Current Phase
Phase: 1
Status: active

## Current Loop
Loop: ralph-loop-001
Status: pending

## Last Handoff
done: ""
failed: ""
needed: ""
```

Also create `plans/` and `state/` directories in your workspace.

### Step 3 — Start a planning session

Open a new Cowork session with your workspace folder selected. Say something like:

> "I want to plan a new project phase" or "What's the status of my current loops?"

The routing skill will pick up your intent and guide you from there.

---

## What You Can Say

The planning skill activates on natural language. All of these work:

| What you want to do | Example phrase |
|---------------------|----------------|
| Start a new project phase | "Create a phase plan for building the API layer" |
| Plan the next loop | "Plan the next loop for Phase 2" |
| Run the next loop | "Run the next loop", "Let's execute the next step" |
| Check progress | "What loops are done?", "Show me the status" |
| Diagnose a problem | "Why isn't the worker completing todos?" |
| Check model assignments | "Are agents using the right models?" |

---

## How Loop Execution Works

When you ask to run a loop, the skill orchestrates two agents in sequence:

```
You → SKILL.md (routing)
         ↓
    Agent tool (model: sonnet)
    ← reads loop plan → writes state/loop-ready.json
         ↓
    Agent tool (model: sonnet)
    ← reads loop-ready.json → executes todos → writes state/loop-complete.json
         ↓
    Main session reads loop-complete.json → updates planning-state.md
```

Each agent prompt is self-contained — the full protocol is passed directly to the Agent tool.

### Spawning the orchestrator (Sonnet)

```
Agent tool:
  model: sonnet
  prompt: [contents of agents/orchestrator-prompt.md]
         + "Workspace path: [path to your workspace folder]"
```

### Spawning the worker (Sonnet)

```
Agent tool:
  model: sonnet
  prompt: [contents of agents/worker-prompt.md]
         + "Workspace path: [path to your workspace folder]"
```

The SKILL.md handles this — you don't need to construct the prompts manually.

---

## Snapshot Checkpoints

Because Cowork sessions don't use git, the adapter uses file snapshots instead. `checkpoint.sh` saves the current state of `plans/` and `state/` to `state/snapshots/`.

### Common commands

```bash
# Save a named snapshot before starting a loop
sh checkpoint.sh save before-loop-003

# Save after a loop completes
sh checkpoint.sh save complete-ralph-loop-003

# See all snapshots
sh checkpoint.sh list

# Restore if something went wrong
sh checkpoint.sh restore before-loop-003
```

The worker runs opening and closing snapshots automatically. You can also run them manually at any point.

---

## Workspace Layout

```
your-workspace/
├── planning-state.md          ← current phase/loop/handoff state
├── plans/
│   ├── phase-1.md             ← phase plan
│   └── phase-1-ralph-loops.md ← loop specs for Phase 1
└── state/
    ├── loop-ready.json        ← orchestrator → worker handoff
    ├── loop-complete.json     ← worker → main thread handoff
    └── snapshots/             ← checkpoint archives
        ├── before-loop-001-20240315-143022/
        └── complete-loop-001-20240315-144511/
```

---

## Troubleshooting

### The worker seems to be executing without loading skills

**Symptom**: Todos complete quickly but outputs are generic — missing domain-specific detail.

**Cause**: Targeted skill injection wasn't applied. The worker must read `skills/[skill]/SKILL.md` immediately before each todo, then discard it before the next.

**Fix**: Check the worker-prompt.md is being passed in full to the Agent tool. The targeted skill injection section is clearly marked as mandatory. If needed, explicitly instruct the agent: "Before each todo, read the assigned skill's SKILL.md and follow its instructions."

---

### loop-ready.json was written but the worker didn't start

**Symptom**: `state/loop-ready.json` exists with `"status": "ready"` but no worker activity.

**Cause**: The main session needs to explicitly spawn the worker after the orchestrator returns. The two agents don't chain themselves — the main thread connects them.

**Fix**: After the orchestrator agent returns, read `state/loop-ready.json` to confirm it's ready, then spawn the worker agent using the `agents/worker-prompt.md` prompt.

---

### Snapshot restore brought back old loop-complete.json

**Symptom**: After restoring, the system thinks a loop already completed.

**Cause**: `state/loop-complete.json` was included in the snapshot being restored.

**Fix**: After restoring, delete `state/loop-complete.json` before spawning the orchestrator. The orchestrator uses `planning-state.md` as its fallback when `loop-complete.json` is absent.

---

## Relationship to Other Adapters

| Feature | Claude Code adapter | Cowork adapter |
|---------|--------------------|--------------------|
| Entry point | `/new-phase`, `/next-loop` slash commands | Routing SKILL.md (natural language) |
| Agent spawning | `claude --model` subprocess | Agent tool with `model:` parameter |
| State tracking | CLAUDE.md Planning State section | `planning-state.md` |
| Checkpoints | `git add -A && git commit` | `sh checkpoint.sh save [label]` |
| Session tracking | TodoWrite tool | TodoWrite tool (same) |

The core planning logic (schemas, skills, orchestrator/worker protocols) is identical between adapters — only the platform interface differs.
