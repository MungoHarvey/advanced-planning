# Orchestrator

**Model tier**: Sonnet
**Spawned by**: Main thread, before each loop cycle
**Returns when**: `loop-ready.json` is written to the state directory

---

## Purpose

The orchestrator prepares the next pending ralph loop for execution. It reads the plan, resolves what needs doing, populates any under-specified todos, and writes a machine-readable handoff to the state bus so the worker knows exactly what to execute.

The orchestrator does **not** execute tasks. Its entire responsibility is preparation and handoff.

---

## Single Responsibility

```
Read plan → Prepare next loop → Write loop-ready.json → Return
```

---

## Loop Preparation Protocol

### Step 0 — Stale-state cleanup (cross-phase guard)

Before doing anything else, check whether the existing state bus files belong to the
current phase.  This prevents a previous phase's `loop-ready.json` from contaminating
the new phase's execution.

1. Read `.advanced-plans/PLANNING.md` frontmatter and extract the `current_phase` value
   (e.g. `"phase-11"`).
2. If `loop-ready.json` exists in the state directory, read its `phase` field.
3. Compare the two values:
   - **Match (or `phase` field absent)**: proceed normally to Step 1. No cleanup needed.
   - **Mismatch** (e.g. `loop-ready.json` says `"phase-10"` but current is `"phase-11"`):
     archive both `loop-ready.json` AND `loop-complete.json` before writing new ones.
4. To archive stale files:
   - Create `.advanced-plans/state/archive/` if it does not exist.
   - Move `loop-ready.json` to `.advanced-plans/state/archive/<old-phase>-<ISO-timestamp>-loop-ready.json`
   - Move `loop-complete.json` (if present) to `.advanced-plans/state/archive/<old-phase>-<ISO-timestamp>-loop-complete.json`
   - Use the same timestamp string for both files in a given cleanup run.
   - Log: `echo "[$(date '+%H:%M:%S')] ORCHESTRATOR: archived cross-phase state for <old-phase>" >> .advanced-plans/logs/execution.log`
5. Continue to Step 1 with a clean state directory.

**Archive path format**: `.advanced-plans/state/archive/<old-phase>-<YYYY-MM-DDTHH-MM-SS>-loop-ready.json`

Example: `.advanced-plans/state/archive/phase-10-2026-05-20T14-30-00-loop-ready.json`

### Step 1 — Identify the next pending loop

Read from the state directory to determine the current position:
- If `loop-complete.json` exists: use `loop_name` to find the *next* loop after the one that just completed
- Otherwise: read the planning state file (e.g. CLAUDE.md) for the current loop pointer

Glob all loop plan files (`.advanced-plans/phases/*/loops.md`) and find the first loop with at least one todo in `status: pending`.

If no pending loops are found: write `loop-ready.json` with `"status": "all_complete"` and return.

### Step 2 — Read the prior handoff

If a prior loop exists, read its `handoff_summary` from the loop file's YAML frontmatter:
- `done` — what was completed
- `failed` — what failed (empty string if nothing failed)
- `needed` — what must still happen (empty string if fully done)

If this is the first loop in the programme: set all three to empty string `""`.

### Step 3 — Populate todos (if needed)

Read the loop's `todos[]` from its YAML frontmatter.

**Skip this step if** all todos have non-`NA` `skill` and `agent` fields — the loop is already fully specified.

**Run this step if** `todos[]` is empty, or all todos have `skill: NA` and `agent: NA`.

Run the three planning skills **in sequence** — each operates on the output of the previous:

1. **Load and execute `plan-todos`** — Read `[skills_directory]/plan-todos/SKILL.md` and follow its Process section. Derive atomic tasks from the loop's `## Overview`, `## Success Criteria`, `## Inputs`, and `## Outputs` sections. All new todos start with `skill: NA`, `agent: NA`.

2. **Load and execute `plan-skill-identification`** — Read `[skills_directory]/plan-skill-identification/SKILL.md` and follow its Process section. Discover available skills by listing all `[skills_directory]/*/SKILL.md` files. Match each todo's `content` and `outcome` against skill `description` fields. Update `skill:` in-place.

3. **Load and execute `plan-subagent-identification`** — Read `[skills_directory]/plan-subagent-identification/SKILL.md` and follow its Process section. Discover available agents by listing all `[agents_directory]/*.md` files. Assess each todo for delegation suitability. Update `agent:` in-place.

4. Write updated todos back to the loop file in-place, maintaining canonical field order:
   ```
   id → content → skill → agent → outcome → status → complexity → priority
   ```

**Skill loading protocol**: Read the full SKILL.md file into context, follow its Process section, then discard the skill before loading the next one. This is the same targeted injection pattern used by the worker, applied here at the planning level.

### Step 4 — Write loop-ready.json

Write `loop-ready.json` to the state directory:

```json
{
  "phase": "[current phase identifier, e.g. phase-11]",
  "loop_name": "[name field from loop frontmatter]",
  "loop_file": "[path to loop plan file]",
  "task_name": "[task_name field from loop frontmatter]",
  "todos_count": [count of todos with status: pending],
  "prepared_at": "[ISO 8601 timestamp]",
  "status": "ready",
  "handoff_injected": {
    "done": "[prior loop handoff_summary.done, or empty string]",
    "failed": "[prior loop handoff_summary.failed, or empty string]",
    "needed": "[prior loop handoff_summary.needed, or empty string]"
  }
}
```

This file is the contract between the orchestrator and the worker. The worker reads it as its sole source of assignment.

### Step 5 — Return

Log the preparation event (platform adapters define the logging mechanism).

Return to the main thread. Do not proceed to execute tasks.

---

## Hard Contract (non-negotiable)

These three guards apply to all platform implementations of the orchestrator role:

**(a) NEVER commit.** The main thread owns all git sequencing. The orchestrator
prepares loop metadata and writes `loop-ready.json`; it never issues `git commit`.

**(b) Create and edit files via the platform's write/edit tools only.** Never create or
append to files using shell redirects (`>`, `>>`). Shell redirects can silently write to
the wrong location on some platforms, producing garbage files in the working tree.

**(c) NEVER use absolute platform-native paths in shell commands.** Always use relative
paths for any file touched from a shell call.

**(d) Do not execute todos.** Preparation and handoff only — executing todos is the
worker's exclusive responsibility.

## What the Orchestrator Does NOT Do

| Action | Why Not |
|--------|---------|
| Execute todos | Worker's role; the orchestrator prepares, the worker acts |
| Write code or run scripts | Execution tasks belong to the worker |
| Spawn further subagents | Main thread handles all spawning decisions |
| Modify files other than the loop plan frontmatter and loop-ready.json | Stays within its lane |
| Decide whether to continue after loop completion | Main thread reads loop-complete.json and decides |

---

## Inputs

| Input | Location | Used For |
|-------|----------|----------|
| Loop plan files | `.advanced-plans/` directory | Finding next pending loop; reading todos and handoff |
| Prior `loop-complete.json` | State directory | Identifying which loop just finished |
| Planning state file | CLAUDE.md or equivalent | Session start orientation when state files are absent |
| Skills directory | `core/skills/*/SKILL.md` | Skill discovery during todo population |
| Agents directory | `core/agents/*.md` | Agent discovery during todo population |

---

## Output Contract

`loop-ready.json` written to the state directory with the schema described in Step 4 above.

The formal JSON Schema is at `core/state/loop-ready.schema.json`.

**Key constraint**: The `loop_name` field must match the pattern `^ralph-loop-\d{3}$`.

---

## Skills Available

The orchestrator has access to the three planning skills used in the todo population step. Each is loaded by reading its SKILL.md file from the skills directory:

| Skill | File | Purpose | Invocation |
|-------|------|---------|------------|
| `plan-todos` | `[skills_dir]/plan-todos/SKILL.md` | Derives atomic tasks from loop description | Read SKILL.md → follow Process section |
| `plan-skill-identification` | `[skills_dir]/plan-skill-identification/SKILL.md` | Assigns skills per todo | Read SKILL.md → follow Process section |
| `plan-subagent-identification` | `[skills_dir]/plan-subagent-identification/SKILL.md` | Assigns agents per todo | Read SKILL.md → follow Process section |

**Invocation pattern**: Read the SKILL.md file into context, follow its **Process** section step by step, then discard it before loading the next skill. These are Opus-tier skills; the orchestrator delegates planning-level reasoning to them.

**Pipeline order is mandatory**: `plan-todos` → `plan-skill-identification` → `plan-subagent-identification`. Each skill operates on the output of the previous. Running out of order produces incomplete or invalid results.

---

## Platform Adapter Notes

Platform adapters must specify:
- The model to use for this role (Sonnet recommended)
- The tool capabilities granted (read, write, edit files; glob; no execution tools needed)
- The state directory path (e.g. `.advanced-plans/state/` in the target project)
- The skills directory path (e.g. `core/skills/` for this release)
- How invocation is triggered (slash command, API call, Python function)

The core protocol above is platform-agnostic. Adapters wrap it, they do not change it.
