---
description: "Advance to the next incomplete phase and execute all its loops autonomously. Without --auto, executes only the next phase's loops to completion (equivalent to /next-loop --auto scoped to one phase). With --auto, chains phases end-to-end until the entire programme completes, a loop fails, or max iterations are hit. Reads phase order from PLANS-INDEX.md and loop completion from loop-complete.json."
allowed-tools: Read, Glob, Bash, Edit, TodoWrite, Agent
argument-hint: "[--auto] [--phase N]"
---

# /next-phase

Advance through one or all remaining phases autonomously.

---

## Step 1 — Parse arguments

```
If $ARGUMENTS contains "--auto":
  AUTO_MODE = true
  Print: "⚡ Autonomous mode: will chain phases until programme complete or failure."
Otherwise:
  AUTO_MODE = false

If $ARGUMENTS contains "--phase N":
  TARGET_PHASE = N   (run only this specific phase)
Otherwise:
  TARGET_PHASE = null (use current phase from Planning State)
```

---

## Step 2 — Establish current position

Read `CLAUDE.md ## Planning State`:
- `phase` — current phase number
- `status` — `not_started | in_progress | complete`

If `status: complete` for all phases:
  Print: "✓ Programme complete. All phases finished."
  Stop.

Determine the **target phase**:
- If `TARGET_PHASE` set: use that phase number
- If current phase `status: in_progress`: use current phase (resume it)
- Otherwise: find the first phase where not all loops are `completed/cancelled`

```bash
# Find the phase plan file for target phase
ls .claude/plans/phase-${PHASE_N}.md 2>/dev/null \
  || ls .claude/plans/phase-${PHASE_N}-*.md 2>/dev/null \
  || echo "ERROR: No plan file for phase ${PHASE_N}"
```

If no phase plan file found: print error and stop.

---

## Step 3 — Verify phase is ready to run

Read the target phase plan file. Check its `## Dependencies` section.

For each listed dependency (prior phases):
  - Read those phase loop files
  - Confirm all todos have `status: completed` or `cancelled`
  - If any dependency incomplete: print which phase must finish first and stop

---

## Step 4 — Execute the phase

Print:
```
▶ Beginning Phase [N]: [phase name]
  Loops: [N total] | Pending: [N pending]
  Mode: [single-phase | autonomous chain]
```

Write audit entry:
```bash
echo "[$(date '+%H:%M:%S')] PHASE START: phase-${N} mode:${AUTO_MODE}" \
  >> .claude/logs/audit.log
```

**Invoke `/next-loop --auto` to execute all loops in this phase.**

This runs the existing loop-chaining behaviour — it will:
- Execute each pending loop via orchestrator + worker
- Chain to the next loop on success
- Stop on failure or when no loops remain in the phase

Monitor the result by reading `.claude/state/loop-complete.json` after
`/next-loop --auto` returns, and by checking todo statuses across all loops
in this phase's plan file.

---

## Step 5 — Evaluate phase outcome

After `/next-loop --auto` returns, determine phase status:

**Check A — Read final `loop-complete.json`:**
```bash
cat .claude/state/loop-complete.json 2>/dev/null
```

**Check B — Scan all loops in this phase:**
```bash
# Count todos by status across all loops in this phase
grep -E "^\s+status:" .claude/plans/phase-${N}-ralph-loops.md \
  | sort | uniq -c
```

**Phase outcome rules:**

| Condition | Outcome |
|---|---|
| All todos `completed` or `cancelled` | ✅ PHASE_COMPLETE |
| Any loop has `status: failed` in loop-complete.json | ❌ PHASE_FAILED |
| Remaining `pending` todos (loop stopped early) | ⚠ PHASE_PARTIAL |

---

## Step 6 — Write phase audit entry

```bash
echo "[$(date '+%H:%M:%S')] PHASE END: phase-${N} outcome:${OUTCOME}" \
  >> .claude/logs/audit.log
```

Append to `history.jsonl`:
```bash
echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"event\":\"phase_complete\",\"phase\":${N},\"outcome\":\"${OUTCOME}\"}" \
  >> .claude/state/history.jsonl
```

---

## Step 7 — On PHASE_FAILED or PHASE_PARTIAL

Print:
```
⚠ Phase [N] did not complete.
  Last loop: [loop name from loop-complete.json]
  Status:    [failed/partial]
  Done:      [handoff.done from loop-complete.json]
  Failed:    [handoff.failed]
  Needed:    [handoff.needed]

Review .claude/plans/phase-[N]-ralph-loops.md and re-run when ready.
Run /next-phase to retry this phase, or /next-loop to step through manually.
```

Stop regardless of AUTO_MODE. Never auto-advance past a failed phase.

---

## Step 8 — On PHASE_COMPLETE

Update `CLAUDE.md ## Planning State`:
- Set current phase `status: complete`
- Set next phase as current phase with `status: in_progress`
- Update `todos_done` count

Print:
```
✓ Phase [N] complete: [phase name]
  Loops finished: [N]
  Todos completed: [N]
```

**If AUTO_MODE = false:** stop here.
```
Next: run /next-phase to begin Phase [N+1],
      or /next-phase --auto to chain remaining phases.
```

**If AUTO_MODE = true:** check whether any phases remain.

---

## Step 9 — AUTO_MODE phase chaining

Check for remaining incomplete phases:

```bash
# Find next phase with pending loops
# (read PLANS-INDEX.md if present, otherwise glob phase-*.md files)
ls .claude/plans/phase-*.md | sort | while read f; do
  phase_n=$(echo "$f" | grep -o 'phase-[0-9]*' | grep -o '[0-9]*')
  pending=$(grep "status: pending" ".claude/plans/phase-${phase_n}-ralph-loops.md" \
    2>/dev/null | wc -l)
  [ "$pending" -gt 0 ] && echo "$phase_n" && break
done
```

**If next phase found:**
```
▶ Chaining to Phase [N+1]: [phase name]
```
Return to **Step 3** with the new target phase.

**If no pending phases remain:**
```
✓ Programme complete.
  All [N] phases finished.
  Total loops: [N] | Total todos: [N]

Full history: .claude/state/history.jsonl
Audit log:   .claude/logs/audit.log
```
Stop.

---

## Safety rules

- **Never skip a failed phase.** AUTO_MODE stops on any `PHASE_FAILED` or `PHASE_PARTIAL`. The human must inspect and re-run.
- **Honour dependencies.** Each phase's `## Dependencies` are checked before starting, even mid-chain.
- **Always write audit entries.** Every phase start and end is logged to `audit.log` and `history.jsonl` before proceeding.
- **Pause signal respected.** Before starting each new phase, check:
  ```bash
  test -f .claude/logs/pause.signal && echo "PAUSED" && exit 0
  ```
