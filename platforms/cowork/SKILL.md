---
name: advanced-planning
model: opus
description: "Hierarchical planning system for sustained, accurate multi-step execution in Cowork. Use for ALL planning tasks: creating phase plans, decomposing work into ralph loop iterations, executing the next loop with the two-agent pattern, checking progress, and managing handoffs across sessions. Triggers: plan this project, new phase, create a phase plan, break this into loops, next loop, loop status, run the next loop, what are we working on, resume the project, what's the plan, how should we approach this, decompose this work, planning, iterations, ralph loop, handoff, session continuity."
---

# Advanced Planning — Cowork Routing Skill

A **routing skill** for hierarchical project planning in Cowork mode.

```
Phase Plan → Ralph Loops → TODOs → Execution → Handoff → Next Loop
```

This skill provides the complete toolchain for sustained multi-session execution:
structured phase planning, loop decomposition with verifiable todos, and cross-session
continuity via concise handoff summaries.

---

## How This Works in Cowork

Unlike Claude Code, Cowork does not have slash commands. This routing skill is your single
entry point — describe what you want to do and the skill dispatches to the right tool.

The two-agent execution cycle uses **Cowork's Agent tool** directly:
- Orchestrator (Sonnet) → spawned via Agent tool to prepare the next loop
- Worker (Haiku) → spawned via Agent tool to execute todos with skill injection

All plan files and state live in your **workspace folder** — they persist between sessions.

---

## Dispatch Table

Read the description of what the user wants and route to the matching action below.

| User Intent | Action |
|-------------|--------|
| **Create a new phase plan** — "plan this", "new phase", "scope this work" | Load `phase-plan-creator` skill → Generate phase plan → Save to `plans/phase-N.md` |
| **Decompose phase into loops** — "break into loops", "new loop", "plan iterations" | Load `ralph-loop-planner` skill → Generate loop stubs → Save to `plans/phase-N-ralph-loops.md` |
| **Execute the next loop** — "next loop", "run it", "continue", "execute" | Run the **Next Loop Cycle** (see below) |
| **Progress report** — "show progress", "what happened", "status report", "what was done" | Load `progress-report` skill → Synthesise plan files, handoffs, git history → Print report |
| **Check loop status** — "loop status", "where are we", "what's left" | Run the **Loop Status Check** (see below) |
| **Diagnose issues** — "something went wrong", "check execution", "why isn't it working" | Run the **Execution Diagnostic** (see below) |
| **Verify model tiers** — "model check", "which model is running" | Run the **Model Check** (see below) |

---

## Action: Load phase-plan-creator

```
Read skills/phase-plan-creator/SKILL.md
Read skills/phase-plan-creator/references/phase-plan-template.md
```

Follow the skill instructions. Save output to `plans/phase-[N].md`.
Update `planning-state.md` with the new phase details.

Then ask: "Shall I decompose this into ralph loops now?"
If yes: load `ralph-loop-planner` next.

---

## Action: Load ralph-loop-planner

```
Read skills/ralph-loop-planner/SKILL.md
Read skills/ralph-loop-planner/references/ralph-loop-template.md
Read skills/ralph-loop-planner/references/todo-schema.md
```

Follow the skill instructions. Save output to `plans/phase-[N]-ralph-loops.md`.

Optionally run the full population pipeline immediately:
```
Read skills/plan-todos/SKILL.md              → populate todos[]
Read skills/plan-skill-identification/SKILL.md → assign skills
Read skills/plan-subagent-identification/SKILL.md → assign agents
```

---

## Action: Load progress-report

```
Read skills/progress-report/SKILL.md
Read skills/progress-report/references/progress-report-template.md
```

Follow the skill instructions. Read plan files, loop handoff summaries, todo statuses,
and the snapshot trail to compile a structured progress report.

Print the report to the conversation. Do not modify any plan files.

---

## Action: Next Loop Cycle

The two-agent handoff pattern. Run these steps in order:

### Step 1 — Snapshot checkpoint (before)

```bash
sh state/checkpoint.sh save before-loop-cycle
```

(Creates a recoverable snapshot in case the loop corrupts state.)

### Step 2 — Spawn the Orchestrator

Use the **Agent tool** with:
- `model: sonnet`
- Prompt: the full contents of `agents/orchestrator-prompt.md`
- Include the path to the current workspace as context

The orchestrator will:
- Identify the next pending loop
- Populate todos/skills/agents if needed
- Write `state/loop-ready.json`
- Return

Wait for the orchestrator to complete.

### Step 3 — Read loop-ready.json

```
Read state/loop-ready.json
```

If `"status": "all_complete"`: print "✓ All loops complete. Phase finished." and stop.

Print:
```
→ Preparing: [loop_name] — [task_name]
  Todos:         [todos_count]
  Prior context: [handoff_injected.done or "first loop"]
```

### Step 4 — Spawn the Worker

Use the **Agent tool** with:
- `model: haiku`
- Prompt: the full contents of `agents/worker-prompt.md`
- Include the workspace path and `state/loop-ready.json` contents as context

The worker will:
- Execute all todos using targeted skill injection (one SKILL.md per todo)
- Update todo statuses in the plan file
- Write `state/loop-complete.json`
- Return

Wait for the worker to complete.

### Step 5 — Read loop-complete.json and update state

```
Read state/loop-complete.json
```

Update `planning-state.md`:
- Advance `current_loop` to the next pending loop
- Increment `todos_done`
- Copy handoff values to the `last_handoff` section

### Step 6 — Snapshot checkpoint (after)

```bash
sh state/checkpoint.sh save after-[loop_name]
```

### Step 7 — Print cycle summary

```
✓ [loop_name] complete
  Done:   [loop_complete.handoff.done]
  Failed: [loop_complete.handoff.failed or "none"]
  Todos:  [todos_done]/[todos_count] completed
```

If `todos_failed > 0`:
```
⚠ [N] todos did not complete. Review plans/[loop_file] before continuing.
```

---

## Action: Loop Status Check

```
Glob("plans/*.md") → read all loop files
```

For each loop extract: name, task_name, todo counts (pending/in_progress/completed/cancelled), handoff_summary fields.

Print:
```
Phase Plan Status
──────────────────────────────────────────────────────────
Loop                      │ Todos            │ State
──────────────────────────────────────────────────────────
ralph-loop-001            │ 4/4 complete     │ ✅ Done
  Task: Schema Definitions│                  │
  Done: All 4 schema docs in core/schemas/

ralph-loop-002            │ 0/5 complete     │ ⏳ Pending
  Task: Planning Skills   │                  │
──────────────────────────────────────────────────────────
Next action: spawn orchestrator to run ralph-loop-002
```

---

## Action: Execution Diagnostic

Check five areas and report:

1. **Todo progression**: `grep "status:" plans/*.md` — are todos advancing?
2. **Handoff population**: `grep -A3 "handoff_summary:" plans/*.md` — are done/failed/needed fields populated?
3. **State files**: Do `state/loop-ready.json` and `state/loop-complete.json` exist and contain valid JSON?
4. **Snapshot trail**: `ls state/snapshots/` — are checkpoints being created?
5. **Skill injection**: Did the worker log skill loads in its completion note?

Report:
```
EXECUTION HEALTH REPORT
────────────────────────────────────────
Todo progression:   [N/N complete | stuck at X]
Handoff summaries:  [populated | empty]
State files:        [present and valid | missing]
Snapshot trail:     [N snapshots | none]
Skill injection:    [confirmed | unknown]
────────────────────────────────────────
Overall:  HEALTHY / PARTIAL / NOT EXECUTING
```

---

## Action: Model Check

Read `model:` frontmatter from each skill and agent prompt:

```
Read skills/phase-plan-creator/SKILL.md        → model field
Read skills/ralph-loop-planner/SKILL.md        → model field
Read skills/plan-todos/SKILL.md                → model field
Read skills/plan-skill-identification/SKILL.md → model field
Read skills/plan-subagent-identification/SKILL.md → model field
Read skills/progress-report/SKILL.md           → model field
```

Print the expected model tier table:
```
Component                         Expected
──────────────────────────────────────────
Planning skills (new-phase pipeline)  opus
Progress report skill                 sonnet
Orchestrator (Agent tool spawn)       sonnet
Worker (Agent tool spawn)             haiku
──────────────────────────────────────────
```

---

## Workspace Structure

After setup, your workspace folder will contain:

```
[workspace]/
├── planning-state.md           ← Persistent planning state (replaces CLAUDE.md)
├── plans/                      ← Phase plans and ralph loop files
│   ├── phase-1.md
│   └── phase-1-ralph-loops.md
├── skills/                     ← Core planning skills (copied from core/)
│   ├── phase-plan-creator/
│   ├── ralph-loop-planner/
│   ├── plan-todos/
│   ├── plan-skill-identification/
│   ├── plan-subagent-identification/
│   └── progress-report/
├── agents/                     ← Agent prompts for the Agent tool
│   ├── orchestrator-prompt.md
│   └── worker-prompt.md
└── state/                      ← Runtime state (loop-ready.json, snapshots)
    ├── loop-ready.json
    ├── loop-complete.json
    ├── checkpoint.sh
    └── snapshots/
```

---

## Planning State File

Cowork uses `planning-state.md` (in the workspace root) instead of a CLAUDE.md section.
This file is the persistent anchor — read it at the start of every session.

```markdown
# Planning State

## Current Phase
phase: 1
name: "[Phase Name]"
plan_file: "plans/phase-1.md"
status: in_progress

## Current Loop
loop: "ralph-loop-001"
task: "[Task Name]"
loop_file: "plans/phase-1-ralph-loops.md"
todos_done: 0
todos_total: 0

## Last Handoff
done: ""
failed: ""
needed: ""

## Completed Phases
| Phase | Name | Outcome | Loops |
|-------|------|---------|-------|
| — | — | — | — |
```
