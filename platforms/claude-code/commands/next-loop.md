---
description: Execute the next pending ralph loop using the two-agent handoff pattern. Spawns ralph-orchestrator (Sonnet) to prepare the loop, then spawns ralph-loop-worker (Sonnet) to execute it. Run repeatedly to advance through all loops in the phase plan. Use --auto to chain loops until the phase completes.
allowed-tools: Read, Write, Glob, Bash, Edit, TodoWrite, Agent
argument-hint: "[--auto] [--full]"
---

# /next-loop

Coordinate one full loop cycle using the filesystem state bus:
orchestrator prepares → worker executes → main thread advances state.

## Steps

### 1. Check for an active plan

```bash
ls .advanced-plans/phases/phase-*/loops.md 2>/dev/null | head -5 || echo "NONE"
```

If no loop files found: print `No phase loops found. Run /decompose-phase first.` and stop.

### 2. Parse --auto and --full flags

If `$ARGUMENTS` contains `--auto`:
- Set `AUTO_MODE = true`
- Print: `Autonomous mode: will chain loops until phase complete or failure.`

Otherwise: `AUTO_MODE = false` (default single-loop behaviour).

If `$ARGUMENTS` contains `--full`:
- Set `FULL_MODE = true`
- Print: `Full-population mode: will populate stub loops (todos → skills → agents) before execution.`

Otherwise: `FULL_MODE = false` (default; assumes todos are already populated).

### 2b. Check if all loops are complete

Read the loop files in `.advanced-plans/phases/`. If all todos across all loops are `completed` or `cancelled`:
print `All loops complete. Phase finished.` and stop.

### 3. Git checkpoint

```bash
git add -A && git commit -m "checkpoint: before next-loop cycle" 2>/dev/null || true
```

### 3a. Archive cross-phase stale state

Before the resume check, archive any state files that belong to a previous phase.
This prevents a stale `loop-ready.json` from a completed phase being silently consumed
as if it referred to the current phase.

```bash
python -c "
import pathlib, re
planning = pathlib.Path('.advanced-plans/PLANNING.md').read_text(encoding='utf-8')
m = re.search(r'^current_phase:\s*(\S+)', planning, re.MULTILINE)
phase_num = m.group(1).strip('\"') if m else None
if phase_num:
    current_phase = phase_num if str(phase_num).startswith('phase-') else f'phase-{phase_num}'
    from platforms.python.state_manager import archive_cross_phase_state
    archived = archive_cross_phase_state('.advanced-plans/state', current_phase)
    if archived:
        print(f'Archived stale state from prior phase to: {archived}')
    else:
        print('No stale cross-phase state to archive.')
else:
    print('Could not determine current_phase from PLANNING.md; skipping archive.')
"
```

### 3b. Resume-detection check (mid-loop death guard)

Before spawning the orchestrator, check for signs that a previous worker died mid-loop:

```bash
# Get mtime of state bus files (seconds since epoch)
READY_MTIME=$(python -c "import os,pathlib; p=pathlib.Path('.advanced-plans/state/loop-ready.json'); print(int(p.stat().st_mtime)) if p.exists() else print(0)")
COMPLETE_MTIME=$(python -c "import os,pathlib; p=pathlib.Path('.advanced-plans/state/loop-complete.json'); print(int(p.stat().st_mtime)) if p.exists() else print(0)")
DIRTY=$(git status --porcelain | wc -l | tr -d ' ')
```

**Decision logic:**

- If `loop-ready.json` does NOT exist: state bus is clean. Log `state-bus clean (no loop-ready.json); proceeding` and continue to Step 4.
- If `loop-ready.json` mtime > `loop-complete.json` mtime AND `DIRTY > 0`:
  - This matches the Loop-035 failure mode: worker died after orchestrator wrote the ready file but
    before (or during) execution, leaving a dirty working tree.
  - Load and invoke the `resume-review` skill if available (`.claude/skills/resume-review/SKILL.md`
    or `~/.claude/skills/resume-review/SKILL.md`).
  - Print the following and **PAUSE for operator acknowledgment** before continuing:
    ```
    WARN: mid-loop death detected.
      loop-ready.json is newer than loop-complete.json AND the working tree is dirty.
      This may mean a previous worker died before completing its loop.

      Options:
        1. Continue — spawn a fresh orchestrator (prior loop state will be overwritten)
        2. Investigate — run /check-execution to diagnose the interrupted loop
        3. Abort — stop here; fix manually then re-run /next-loop

    Type 1, 2, or 3 and press Enter:
    ```
  - Only proceed to Step 4 if operator selects option 1.
  - If option 2 or 3: stop.
- Otherwise (loop-complete.json is newer than or equal to loop-ready.json, OR working tree is clean):
  - Log `state-bus clean; proceeding` and continue to Step 4.

**This check MUST NOT block when state is genuinely clean** (e.g. after a successful loop
completion the loop-complete.json is newer than loop-ready.json).

Note: cross-phase stale files were already archived in Step 3a before this check runs,
so `loop-ready.json` here (if present) belongs to the current phase.

### 3c. One-pass population (--full mode only)

This step runs **only when `FULL_MODE = true`**.

Before spawning the orchestrator, identify the next pending loop in the current phase
(the first loop whose `todos[]` array is empty or contains only stub entries with
`status: pending` and no meaningful `content`). If the loop is fully populated, skip
this step and proceed to Step 4.

If the next pending loop is an **unpopulated stub** (i.e. `todos[]` is empty or all
todos have no `skill:` / `agent:` values assigned beyond `NA` placeholders from a
bare stub), run the three planning skills in sequence to fully populate it before
the orchestrator reads it:

1. **`plan-todos`** — derive atomic, verifiable todos from the loop's description and
   success criteria. Write the `todos[]` array into the loop's YAML frontmatter.
   Resolve skill path: `.claude/skills/plan-todos/SKILL.md` (project-local) or
   `~/.claude/skills/plan-todos/SKILL.md` (global fallback).

2. **`plan-skill-identification`** — read the populated `todos[]`, assign the most
   appropriate installed skill (or `NA`) to each todo's `skill:` field in-place.
   Resolve skill path: `.claude/skills/plan-skill-identification/SKILL.md` (project-local)
   or `~/.claude/skills/plan-skill-identification/SKILL.md` (global fallback).

3. **`plan-subagent-identification`** — read the todos with skills assigned, assign the
   appropriate agent (or `NA`) to each todo's `agent:` field in-place.
   Resolve skill path: `.claude/skills/plan-subagent-identification/SKILL.md`
   (project-local) or `~/.claude/skills/plan-subagent-identification/SKILL.md`
   (global fallback).

**Each skill is loaded (SKILL.md read), applied, then discarded before the next skill
is loaded.** Do not carry skill context across steps.

After all three skills have run, the loop's `todos[]` must be fully populated (content,
skill, agent, outcome, status, priority all set). Print:

```
--full: stub loop populated via plan-todos → plan-skill-identification → plan-subagent-identification
  Todos populated: [count]
```

Then continue to Step 4 (the orchestrator will see the now-populated loop).

If `FULL_MODE = false`: skip this step entirely. Behaviour is **unchanged**.

### 4. Spawn ralph-orchestrator

Spawn the `ralph-orchestrator` subagent (Sonnet model).

The orchestrator will:
- Identify the next pending loop
- Populate todos/skills/agents if the loop stubs are not yet fully specified
- Write `.advanced-plans/state/loop-ready.json`

Wait for the orchestrator to complete before proceeding.

### 5. Read and validate loop-ready.json

```bash
cat .advanced-plans/state/loop-ready.json
```

If the file contains `"status": "all_complete"`: print `All loops complete.` and stop.

**Validate structure** before proceeding:
- `loop_name` must be non-empty
- `loop_file` must exist as a file
- `todos_count` must be > 0
- `status` must be `"ready"`
- `handoff_injected` must contain all three fields: `done`, `failed`, `needed`

If any validation fails: print the specific error (e.g. `Validation failed: loop_file does not exist at [path]`) and stop.

Print:
```
-> Preparing: [loop_name] — [task_name]
  Todos:         [todos_count]
  Prior context: [handoff_injected.done, or "first loop" if empty]
```

### 5c. Prepare worker context

Before spawning the worker, the main thread reads the loop file and extracts the information
the worker needs. This ensures the worker receives explicit context rather than discovering
it independently:

1. Read the loop file at `loop_ready.loop_file`
2. Extract the `todos[]` array — note all unique `skill:` values (excluding `NA`)
3. For each unique skill, resolve the path: `.claude/skills/[skill]/SKILL.md` (project-local)
   or `~/.claude/skills/[skill]/SKILL.md` (global fallback)
4. Build the worker prompt addendum:

```
Loop: [loop_name]
Loop file: [loop_file path]
Todos: [count]
Skills needed: [comma-separated list of skill names]
Skill paths:
  - [skill-name]: [resolved path]
  - [skill-name]: [resolved path]
Prior context (handoff):
  done: [handoff_injected.done]
  failed: [handoff_injected.failed]
  needed: [handoff_injected.needed]

Execute all todos inline using targeted skill injection. Read each skill's SKILL.md
before executing the corresponding todo. You cannot spawn subagents — execute everything directly.
```

### 6. Spawn ralph-loop-worker

Spawn the `ralph-loop-worker` subagent (Sonnet model) with the worker prompt addendum
from Step 5c included in the spawn prompt.

The worker will:
- Read `.advanced-plans/state/loop-ready.json` for its assignment
- Read each skill file at the paths provided before executing the corresponding todo
- Execute all todos inline using the targeted skill injection protocol
- Write `.advanced-plans/state/loop-complete.json`

Wait for the worker to complete before proceeding.

### 7. Read loop-complete.json

```bash
cat .advanced-plans/state/loop-complete.json
```

### 8. Update PLANNING.md

Read `.advanced-plans/PLANNING.md` and update:
- `current_loop:` — advance to next pending loop
- `last_updated:` — today's date

If all loops are now complete:
- Set `status: complete` on the current phase in PLANNING.md

### 9. Git commit and history event

```bash
git add -A && git commit -m "complete: [loop_name] - [loop_complete.handoff.done]" 2>/dev/null || true
```

After the commit, append a `loop_complete` event to the audit log:

```bash
python -m platforms.python.history_log .advanced-plans/state/history.jsonl \
  "{\"event\":\"loop_complete\",\"phase\":\"[phase]\",\"loop\":\"[loop_name]\",\"todos_done\":[todos_done],\"todos_count\":[todos_count],\"todos_failed\":[todos_failed],\"commit\":\"$(git rev-parse --short HEAD)\"}"
```

**Convention — release-staging loops**: when a loop cuts a release (bumps VERSION, writes
CHANGELOG), append a `release_staged` event with fields `event`, `phase`, `version`.
This is a convention note; no new machinery is required — use the same `history_log` CLI.

### 10. Print cycle summary

```
[loop_name] complete
  Done:   [loop_complete.handoff.done]
  Failed: [loop_complete.handoff.failed or "none"]
  Todos:  [todos_done]/[todos_count] completed

Run /next-loop to continue with the next loop.
```

If `todos_failed > 0`:
```
[N] todos did not complete. Review .advanced-plans/phases/[phase]/loops.md before continuing.
```

### 11. Auto-chain decision

If `AUTO_MODE` is false: stop. Print `Run /next-loop to continue.`

If `AUTO_MODE` is true:

- **status is "failed"** → stop. Print:
  ```
  Auto-chain stopped: [loop_name] failed.
    Review .advanced-plans/phases/[phase]/loops.md and .advanced-plans/state/loop-complete.json.
    Fix the issue, then run /next-loop to resume.
  ```

- **All loops complete** → stop. Print:
  ```
  Phase complete. All loops finished.
    Run /progress-report to see a summary of what was accomplished.
  ```

- **status is "completed" or "partial" with more loops pending** → print `Auto-chaining to next loop...`
  and return to Step 3 (git checkpoint), beginning the next loop cycle (which will re-run Step 3a archive check).

## Notes

- The orchestrator and worker are spawned sequentially — never concurrently
- The main thread (this command) is the only decision-maker for loop sequencing
- If the orchestrator writes `status: all_complete`, the phase is done
- Run `/check-execution` if a loop completes without visible output or with unexpected results
- Auto mode respects `on_max_iterations` — a loop that escalates will stop the chain
- Each loop in auto mode gets its own git checkpoint (Step 3), so any failure is recoverable
- Run `/progress-report` after an auto run to see a structured summary of what happened
