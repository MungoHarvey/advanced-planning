---
description: Run programme closeout synthesis. Spawns the programme-reporter agent to produce a final narrative from the complete documentary record.
allowed-tools: Read, Write, Glob, Agent
argument-hint: ""
---

# /run-closeout

Produce the final programme closeout narrative. The `programme-reporter` agent reads
the complete documentary record — all phase plans, loop files, handoff summaries, and
history.jsonl — and synthesises a structured closeout report.

Run this command after all phases have passed their gate reviews.

## Steps

### 1. Verify programme is complete

Read `.advanced-plans/PLANNING.md` and check that all phases have `status: complete`.

If any phase does not have `status: complete`:
print `Cannot run closeout: not all phases are complete. Check .advanced-plans/PLANNING.md.`
and stop.

Print: `-> All phases complete — proceeding to closeout synthesis.`

### 2. Gather documentary record

Collect the paths to all programme artefacts for the agent:

```bash
ls .advanced-plans/phases/*/plan.md
ls .advanced-plans/phases/*/loops.md
ls .advanced-plans/phases/*/complete.md 2>/dev/null || echo "No phase completes found"
ls .advanced-plans/state/history.jsonl 2>/dev/null || echo "No history log found"
ls .advanced-plans/phases/*/gate-verdicts/*.json 2>/dev/null || echo "No gate verdicts found"
```

### 3. Spawn programme-reporter

Spawn the `programme-reporter` subagent with the following prompt:

```
You are programme-reporter performing the final closeout synthesis.

Documentary record:
  Phase plans:    .advanced-plans/phases/*/plan.md
  Loop files:     .advanced-plans/phases/*/loops.md
  Phase completes: .advanced-plans/phases/*/complete.md
  History log:    .advanced-plans/state/history.jsonl
  Gate verdicts:  .advanced-plans/phases/*/gate-verdicts/*.json

Your output: .advanced-plans/programme-closeout.md

Read all artefacts listed above. Synthesise a structured programme closeout report
covering: objectives achieved, phases completed, key decisions made, lessons learned,
and any outstanding items. Write the report to .advanced-plans/programme-closeout.md. Then return.
```

Wait for the agent to complete.

### 4. Verify closeout report was produced

```bash
ls .advanced-plans/programme-closeout.md
```

If the file does not exist:
print `programme-reporter did not write .advanced-plans/programme-closeout.md — check agent output.`
and stop.

### 5. Append closeout event to history.jsonl

Count completed phases and total loops from history.jsonl:

```bash
grep -c '"event":"loop_complete"' .advanced-plans/state/history.jsonl 2>/dev/null || echo "0"
grep -c '"event":"phase_retry"' .advanced-plans/state/history.jsonl 2>/dev/null || echo "0"
```

Append the closeout event:

```bash
echo '{"event":"closeout","timestamp":"[ISO timestamp]","phases_completed":[N],"total_loops":[M],"total_retries":[R],"report_file":".advanced-plans/programme-closeout.md"}' >> .advanced-plans/state/history.jsonl
```

### 6. Print summary

```
Programme closeout complete.
  Report: .advanced-plans/programme-closeout.md

Review the report and share it with stakeholders.
```

## Notes

- Run this command only after all phases are complete and all gate reviews have passed
- The report is written to `.advanced-plans/programme-closeout.md` — never overwrite an existing report
  (rename the existing file first if re-running)
- The `programme-reporter` agent has read access to all plan and state files
- Gate verdicts are included in the documentary record so the report can reference them
