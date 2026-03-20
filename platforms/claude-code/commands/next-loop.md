---
description: Execute the next pending ralph loop using the two-agent handoff pattern. Spawns ralph-orchestrator (Sonnet) to prepare the loop, then spawns ralph-loop-worker (Haiku) to execute it. Run repeatedly to advance through all loops in the phase plan. Use --auto to chain loops until the phase completes.
allowed-tools: Read, Write, Glob, Bash, Edit, TodoWrite, Agent
argument-hint: "[--auto]"
---

# /next-loop

Coordinate one full loop cycle using the filesystem state bus:
orchestrator prepares → worker executes → main thread advances state.

## Steps

### 1. Check for an active plan

```bash
ls .claude/plans/*.md 2>/dev/null | head -5 || echo "NONE"
```

If no plan files found: print `No phase plan found. Run /new-phase first.` and stop.

### 2. Parse --auto flag

If `$ARGUMENTS` contains `--auto`:
- Set `AUTO_MODE = true`
- Print: `⚡ Autonomous mode: will chain loops until phase complete or failure.`

Otherwise: `AUTO_MODE = false` (default single-loop behaviour).

### 2b. Check if all loops are complete

Read the loop files in `.claude/plans/`. If all todos across all loops are `completed` or `cancelled`:
print `✓ All loops complete. Phase finished.` and stop.

### 3. Git checkpoint and directory setup

```bash
mkdir -p .claude/logs .claude/state
git add -A && git commit -m "checkpoint: before next-loop cycle" 2>/dev/null || true
```

### 4. Spawn ralph-orchestrator

Spawn the `ralph-orchestrator` subagent (Sonnet model).

The orchestrator will:
- Identify the next pending loop
- Populate todos/skills/agents if the loop stubs are not yet fully specified
- Write `.claude/state/loop-ready.json`

Wait for the orchestrator to complete before proceeding.

### 5. Read loop-ready.json

```bash
cat .claude/state/loop-ready.json
```

If the file contains `"status": "all_complete"`: print `✓ All loops complete.` and stop.

Print:
```
→ Preparing: [loop_name] — [task_name]
  Todos:         [todos_count]
  Prior context: [handoff_injected.done, or "first loop" if empty]
```

### 6. Spawn ralph-loop-worker

Spawn the `ralph-loop-worker` subagent (Haiku model).

The worker will:
- Read `.claude/state/loop-ready.json` for its assignment
- Execute all todos in order using the targeted skill injection protocol
- Write `.claude/state/loop-complete.json`

Wait for the worker to complete before proceeding.

### 7. Read loop-complete.json

```bash
cat .claude/state/loop-complete.json
```

### 8. Update CLAUDE.md Planning State

Read the `## Planning State` section and update:
- `loop:` — advance to next pending loop
- `todos_done:` — increment by `todos_done` from loop-complete.json

If all loops are now complete:
- Set `status: complete` on the current phase

### 9. Git commit

```bash
git add -A && git commit -m "complete: [loop_name] - [loop_complete.handoff.done]" 2>/dev/null || true
```

### 10. Print cycle summary

```
✓ [loop_name] complete
  Done:   [loop_complete.handoff.done]
  Failed: [loop_complete.handoff.failed or "none"]
  Todos:  [todos_done]/[todos_count] completed

Run /next-loop to continue with the next loop.
```

If `todos_failed > 0`:
```
⚠ [N] todos did not complete. Review .claude/plans/[loop_file] before continuing.
```

### 11. Auto-chain decision

If `AUTO_MODE` is false: stop. Print `Run /next-loop to continue.`

If `AUTO_MODE` is true:

- **status is "failed"** → stop. Print:
  ```
  ✗ Auto-chain stopped: [loop_name] failed.
    Review .claude/plans/[loop_file] and .claude/state/loop-complete.json.
    Fix the issue, then run /next-loop to resume.
  ```

- **All loops complete** → stop. Print:
  ```
  ✓ Phase complete. All loops finished.
    Run /progress-report to see a summary of what was accomplished.
  ```

- **status is "completed" or "partial" with more loops pending** → print `Auto-chaining to next loop...`
  and return to Step 3 (git checkpoint), beginning the next loop cycle.

## Notes

- The orchestrator and worker are spawned sequentially — never concurrently
- The main thread (this command) is the only decision-maker for loop sequencing
- If the orchestrator writes `status: all_complete`, the phase is done
- Run `/check-execution` if a loop completes without visible output or with unexpected results
- Auto mode respects `on_max_iterations` — a loop that escalates will stop the chain
- Each loop in auto mode gets its own git checkpoint (Step 3), so any failure is recoverable
- Run `/progress-report` after an auto run to see a structured summary of what happened
