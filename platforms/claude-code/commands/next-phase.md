---
description: Advance to the next phase. Runs the gate review first; on pass advances, on fail creates versioned retry files with injected failure context.
allowed-tools: Read, Write, Glob, Bash, Edit, Agent
argument-hint: "[--skip-gate] [--force]"
---

# /next-phase

Advance from the current phase to the next. By default this command runs the full gate
review first. On gate pass, the current phase is marked complete and you are prompted to
plan the next phase. On gate fail, versioned retry files are created with injected failure
context so the retry loop has full information.

## Steps

### 1. Read current phase

Read `CLAUDE.md` and extract the `## Planning State` section. Identify:
- Current phase number `N`
- Current loop file path
- Current phase status

If the current phase already has `status: complete`:
print `✓ Phase [N] is already complete. Run /new-phase to plan Phase [N+1].` and stop.

Print: `→ Current phase: Phase [N]`

### 2. Parse flags

Check `$ARGUMENTS` for:
- `--skip-gate`: bypass gate review entirely, treat as pass
- `--force`: if gate fails, advance anyway (with a warning)

If `--skip-gate` is set, skip Steps 3–5 and proceed directly to Step 6 (gate pass path).

If `--force` is set, note it for use in Step 7.

### 3. Run gate review

Run the full gate review inline (same logic as `/run-gate`):

**3a. Verify all loops complete**

```bash
grep -c "status: pending\|status: in_progress" .claude/plans/*.md 2>/dev/null || echo "0"
```

If any incomplete todos found:
print `✗ Gate review blocked: [N] todos are not yet completed. Finish all loops first.`
and stop.

**3b. Determine agents and attempt number**

Default gate agents: `code-review-agent`, `phase-goals-agent`

Count existing verdict files to find attempt number:

```bash
ls plans/gate-verdicts/phase-[N]-attempt-*.json 2>/dev/null | wc -l
```

Set `attempt = (existing_count / agent_count) + 1`, minimum 1.

**3c. Create gate-verdicts directory and sentinel**

```bash
mkdir -p plans/gate-verdicts
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > .claude/state/gate-review-mode
```

**3d. Spawn each gate agent sequentially**

For each agent, spawn via Agent tool with the prompt:

```
You are [agent-name] performing a gate review.

Phase: [N]
Attempt: [attempt]
Phase plan: plans/phase-[N]-*.md
Loop files: .claude/plans/ (all loop files for this phase)

Your verdict output path: plans/gate-verdicts/phase-[N]-attempt-[attempt]-[agent-name].json

Evaluate whether the phase success criteria have been met. Write your verdict to the
output path following gate-verdict.schema.json. Then return.
```

Wait for each agent before spawning the next.

**3e. Remove sentinel**

```bash
rm .claude/state/gate-review-mode
```

**3f. Aggregate verdicts**

Read all verdict files for this phase+attempt. Check each `verdict` field:
- ALL `"pass"` → gate passes; set `GATE_RESULT = pass`
- ANY `"fail"` → gate fails; set `GATE_RESULT = fail`, note the failing agent and verdict file

### 4. Append gate event to history.jsonl

If `GATE_RESULT = pass`:

```bash
echo '{"event":"gate_pass","phase":"phase-[N]","attempt":[attempt],"timestamp":"[ISO timestamp]","agents":["code-review-agent","phase-goals-agent"],"verdict_files":["plans/gate-verdicts/phase-[N]-attempt-[attempt]-code-review-agent.json","plans/gate-verdicts/phase-[N]-attempt-[attempt]-phase-goals-agent.json"]}' >> .claude/state/history.jsonl
```

If `GATE_RESULT = fail`:

```bash
echo '{"event":"gate_fail","phase":"phase-[N]","attempt":[attempt],"timestamp":"[ISO timestamp]","agent":"[failing-agent]","verdict_file":"[failing-verdict-path]","loops_to_revert":[loops JSON array]}' >> .claude/state/history.jsonl
```

### 5. Handle --force flag on gate failure

If `GATE_RESULT = fail` and `--force` was provided:

Print:
```
⚠ WARNING: Gate review FAILED but --force was used. Advancing anyway.
  Failing agent: [agent-name]
  Verdict file:  [path]
  The failure context has NOT been preserved in versioned retry files.
  This is irreversible — the gate failure will be recorded in history.jsonl.
```

Set `GATE_RESULT = pass` and continue to Step 6.

### 6. Gate PASS — advance to next phase

Update `CLAUDE.md` `## Planning State`:
- Set current phase `status: complete`
- Set `phase: [N+1]` as the next active phase (with `status: not_started`)

```bash
git add -A && git commit -m "complete: phase-[N] gate passed — advancing to phase-[N+1]"
```

Print:
```
✓ Phase [N] gate PASSED.
  Status updated in CLAUDE.md.
  Phase [N+1] is ready to plan.

Run /new-phase to plan Phase [N+1].
```

Stop.

### 7. Gate FAIL — create versioned retry files

**7a. Determine next attempt number**

`next_attempt = attempt + 1`

**7b. Read failure context from verdict**

Read the failing agent's verdict file. Extract:
- `findings`: list of issues with severity, location, description, evidence
- `loops_to_revert`: list of loop names that must be revisited
- `failure_notes`: prose summary of what went wrong

**7c. Create versioned loop file**

Copy the current active loop file to a versioned path:

```bash
cp plans/phase-[N]-ralph-loops.md plans/phase-[N]-ralph-loops-v[next_attempt].md
```

**7d. Inject gate_failure_context block**

Edit the new versioned file (`plans/phase-[N]-ralph-loops-v[next_attempt].md`). In the
YAML frontmatter of each loop listed in `loops_to_revert`, add a `gate_failure_context`
block:

```yaml
gate_failure_context:
  attempt: [attempt]
  verdict_file: "plans/gate-verdicts/phase-[N]-attempt-[attempt]-[agent-name].json"
  summary: "[failure_notes from verdict]"
  loops_reverted:
    - loop: "[loop-name]"
      reason: "[relevant finding description for this loop]"
  do_not_repeat:
    - "[finding description 1]"
    - "[finding description 2]"
```

**7e. Reset todo statuses in versioned file**

In the versioned file, for each loop listed in `loops_to_revert`, change all
`status: completed` todos to `status: pending` so they are re-executed on retry.

**7f. Freeze the original loop file**

In the original loop file (`plans/phase-[N]-ralph-loops.md`), change any
`status: pending` or `status: in_progress` todos to `status: frozen` to prevent
the original from being modified during retry.

**7g. Update PLANS-INDEX.md**

Read `plans/PLANS-INDEX.md`. Update the Phase [N] entry:
- Add versioned file as the new active file
- Set attempt number to `next_attempt`
- Note: original file is now frozen

If `PLANS-INDEX.md` does not exist, create it with a Phase [N] entry.

**7h. Append phase_retry event to history.jsonl**

```bash
echo '{"event":"phase_retry","phase":"phase-[N]","attempt":[next_attempt],"timestamp":"[ISO timestamp]","new_loop_file":"plans/phase-[N]-ralph-loops-v[next_attempt].md","original_loop_file":"plans/phase-[N]-ralph-loops.md"}' >> .claude/state/history.jsonl
```

**7i. Git commit**

```bash
git add -A && git commit -m "retry: phase-[N] attempt [next_attempt] — gate failed on [failing-agent]"
```

**7j. Print failure summary**

```
✗ Phase [N] gate FAILED (attempt [attempt]).
  Failed agent:  [agent-name]
  Verdict file:  [path]
  Issues found:  [count]

Versioned retry files created:
  New loop file: plans/phase-[N]-ralph-loops-v[next_attempt].md
  Failure context injected into: [list of affected loops]
  Original file frozen: plans/phase-[N]-ralph-loops.md

Run /next-loop to begin Phase [N] retry (attempt [next_attempt]).
```

## Notes

- Gate review is mandatory by default — use `--skip-gate` only when the review has already
  been run separately via `/run-gate`
- `--force` overrides gate failure but does not suppress the `gate_fail` history event
- Versioned retry files preserve all completed work; only `loops_to_revert` are reset
- The `do_not_repeat` field in `gate_failure_context` is carried forward through all retries
- After all phases complete, run `/run-closeout` to produce the programme narrative
