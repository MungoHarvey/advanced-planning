---
description: Advance to the next phase. Runs gate review first; on pass advances. Use --auto to chain across phase boundaries — gate review → plan next phase → execute loops → repeat until programme complete or failure.
allowed-tools: Read, Write, Glob, Bash, Edit, TodoWrite, Agent
argument-hint: "[--auto] [--skip-gate] [--force]"
---

# /next-phase

Advance from the current phase to the next. By default this command runs the full gate
review first. On gate pass, the current phase is marked complete and you are prompted to
plan the next phase. On gate fail, versioned retry files are created with injected failure
context so the retry loop has full information.

Use `--auto` to chain across phase boundaries autonomously: gate review → plan next phase →
execute all loops → gate review → repeat until the programme completes or a gate/loop fails.

## Steps

### 1. Read current phase

Read `.advanced-plans/PLANNING.md` and extract `current_phase`. Also read `CLAUDE.md` for
any `## Planning State` section if PLANNING.md is absent. Identify:
- Current phase number `N`
- Current loop file path
- Current phase status

If the current phase already has `status: complete`:
print `Phase [N] is already complete. Run /decompose-phase to plan Phase [N+1].` and stop.

Print: `-> Current phase: Phase [N]`

### 1a. Detect a phase already closed by /run-gate

`/run-gate` now closes a phase out on gate pass (marks it complete and advances the
`current_phase` pointer — see run-gate.md Step 10.4). So by the time you reach `/next-phase`,
the gate and closeout for the just-finished phase may already be done. Detect this to avoid
re-gating or double-advancing.

Check whether the current phase `[N]` has a plan at
`.advanced-plans/phases/phase-[N]/plan.md`:

- **Plan present with pending/in-progress loops** → normal case. Proceed to Step 2 (this phase
  still needs its gate).
- **Plan absent** → the `current_phase` pointer was advanced by a prior `/run-gate` closeout and
  phase `[N]` is not yet planned. There is nothing to gate or advance for the prior phase. Then:
  - If `--auto` is set (`AUTO_PHASE_MODE`): skip the gate (Steps 3–6) and go directly to Step 8b
    to plan and execute phase `[N]`.
  - Otherwise: print `Phase [N-1] was already closed out by /run-gate (gate passed). Phase [N]
    is not yet planned — run /phase-compact [N-1] if you have not, then /plan-and-phase to scope
    Phase [N] (or /next-phase --auto to plan + run it).` and stop.

This guard makes `/run-gate` (gate + close) and `/next-phase` (plan/advance + `--auto` chaining)
compose cleanly: running `/next-phase` after a `/run-gate` pass never re-spawns gate agents for
the already-passed phase.

### 2. Parse flags

Check `$ARGUMENTS` for:
- `--auto`: autonomous phase chaining — after gate pass, plan and execute the next phase automatically
- `--skip-gate`: bypass gate review entirely, treat as pass
- `--force`: if gate fails, advance anyway (with a warning)

If `--auto` is set:
- Set `AUTO_PHASE_MODE = true`
- Print: `Autonomous phase mode: will chain phases until programme complete or failure.`

If `--skip-gate` is set, skip Steps 3–5 and proceed directly to Step 6 (gate pass path).

If `--force` is set, note it for use in Step 7.

### 3. Run gate review

Run the full gate review inline (same logic as `/run-gate`):

**3a. Verify all loops complete**

```bash
grep -rn "status: pending\|status: in_progress" .advanced-plans/phases/phase-[N]/loops.md 2>/dev/null || echo "0"
```

If any incomplete todos found:
print `Gate review blocked: [N] todos are not yet completed. Finish all loops first.`
and stop.

**3b. Determine agents and attempt number**

Default gate agents: `code-review-agent`, `phase-goals-agent`

Count existing verdict files to find attempt number:

```bash
ls .advanced-plans/gate-verdicts/phase-[N]-attempt-*.json 2>/dev/null | wc -l
```

Set `attempt = (existing_count / agent_count) + 1`, minimum 1.

**3c. Create gate-verdicts directory and sentinel**

```bash
mkdir -p .advanced-plans/gate-verdicts
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > .advanced-plans/state/gate-review-mode
```

**3d. Spawn each gate agent sequentially**

For each agent, spawn via Agent tool with the prompt:

```
You are [agent-name] performing a gate review.

Phase: [N]
Attempt: [attempt]
Phase plan: .advanced-plans/phases/phase-[N]/plan.md
Loop files: .advanced-plans/phases/phase-[N]/loops.md

Your verdict output path: .advanced-plans/gate-verdicts/phase-[N]-attempt-[attempt]-[agent-name].json

Evaluate whether the phase success criteria have been met. Write your verdict to the
output path following gate-verdict.schema.json. Then return.
```

Wait for each agent before spawning the next.

**3e. Remove sentinel**

```bash
rm .advanced-plans/state/gate-review-mode
```

**3f. Aggregate verdicts**

Read all verdict files for this phase+attempt. Check each `verdict` field:
- ALL `"pass"` → gate passes; set `GATE_RESULT = pass`
- ANY `"fail"` → gate fails; set `GATE_RESULT = fail`, note the failing agent and verdict file

### 4. Append gate event to history.jsonl

If `GATE_RESULT = pass`:

```bash
echo '{"event":"gate_pass","phase":"phase-[N]","attempt":[attempt],"timestamp":"[ISO timestamp]","agents":["code-review-agent","phase-goals-agent"],"verdict_files":[".advanced-plans/gate-verdicts/phase-[N]-attempt-[attempt]-code-review-agent.json",".advanced-plans/gate-verdicts/phase-[N]-attempt-[attempt]-phase-goals-agent.json"]}' >> .advanced-plans/state/history.jsonl
```

If `GATE_RESULT = fail`:

```bash
echo '{"event":"gate_fail","phase":"phase-[N]","attempt":[attempt],"timestamp":"[ISO timestamp]","agent":"[failing-agent]","verdict_file":"[failing-verdict-path]","loops_to_revert":[loops JSON array]}' >> .advanced-plans/state/history.jsonl
```

### 5. Handle --force flag on gate failure

If `GATE_RESULT = fail` and `--force` was provided:

Print:
```
WARNING: Gate review FAILED but --force was used. Advancing anyway.
  Failing agent: [agent-name]
  Verdict file:  [path]
  The failure context has NOT been preserved in versioned retry files.
  This is irreversible — the gate failure will be recorded in history.jsonl.
```

Set `GATE_RESULT = pass` and continue to Step 6.

### 6. Gate PASS — advance to next phase

Update `.advanced-plans/PLANNING.md`:
- Set current phase `status: complete`
- Set `current_phase: [N+1]` as the next active phase

```bash
git add -A && git commit -m "complete: phase-[N] gate passed — advancing to phase-[N+1]"
```

Print:
```
Phase [N] gate PASSED.
  Status updated in .advanced-plans/PLANNING.md.
```

If `AUTO_PHASE_MODE = false`: print `Run /decompose-phase to plan Phase [N+1].` and stop.

If `AUTO_PHASE_MODE = true`: proceed to Step 8 (auto-continuation).

---

### 8. Auto-continuation (--auto only)

This step runs only when `AUTO_PHASE_MODE = true`. It chains phase planning, loop execution,
and gate review into a continuous autonomous pipeline.

#### 8a. Check for next phase

Read `.advanced-plans/PLANS-INDEX.md` and `.advanced-plans/master-plan.md` (if they exist) to determine if more
phases are planned:

- If a master plan exists with a defined Phase [N+1] description: use that description as input
- If PLANS-INDEX.md lists a Phase [N+1] with status `not_started`: use its name as input
- If no more phases are defined anywhere:
  print `Programme complete. All planned phases passed gate review.` and stop
- If uncertain (no master plan, no pre-defined phases):
  print `Phase [N] complete. No next phase defined in master plan. Run /decompose-phase to plan manually.` and stop

#### 8b. Plan the next phase (inline planning pipeline)

Run the full planning pipeline for Phase [N+1] (same steps as `/new-phase`):

1. Auto-increment phase number: `N+1`
2. Load `.claude/skills/phase-plan-creator/SKILL.md` and follow its Process section
   - Use the description from Step 8a as input
   - Save to `.advanced-plans/phases/phase-[N+1]/plan.md`
3. Load `.claude/skills/ralph-loop-planner/SKILL.md` and follow its Process section
   - Read the phase plan just created
   - Save to `.advanced-plans/phases/phase-[N+1]/loops.md`
4. Load `.claude/skills/plan-todos/SKILL.md` and follow its Process section
   - Populate `todos[]` for every loop
5. Load `.claude/skills/plan-skill-identification/SKILL.md` and follow its Process section
   - Glob `.claude/skills/*/SKILL.md` to discover available skills
   - Assign `skill:` fields in-place
6. Load `.claude/skills/plan-subagent-identification/SKILL.md` and follow its Process section
   - Glob `.claude/agents/*.md` to discover available agents
   - Assign `agent:` fields in-place
7. Update `.advanced-plans/PLANNING.md` with the new phase and first loop

```bash
git add -A && git commit -m "plan: phase-[N+1] — [phase name], [loop count] loops, [todo count] todos"
```

Print:
```
Phase [N+1] planned: [phase name]
  Loops: [count]
  Todos: [count]
  Beginning execution...
```

#### 8c. Execute all loops (inline loop chaining)

Run the loop execution cycle for Phase [N+1] (same logic as `/next-loop --auto`):

**For each pending loop:**

1. Git checkpoint:
   ```bash
   git add -A && git commit -m "checkpoint: before next-loop cycle" 2>/dev/null || true
   ```

2. Spawn `ralph-orchestrator` (Sonnet):
   - Identifies next pending loop
   - Populates todos if needed
   - Writes `.advanced-plans/state/loop-ready.json`
   - Returns

3. Read `.advanced-plans/state/loop-ready.json`
   - If `status: all_complete`: all loops done, proceed to Step 8d
   - Otherwise: print loop summary

4. Spawn `ralph-loop-worker` (Sonnet):
   - Reads `loop-ready.json` for assignment
   - Executes all todos with targeted skill injection
   - Writes `.advanced-plans/state/loop-complete.json`
   - Returns

5. Read `.advanced-plans/state/loop-complete.json`

6. Update `.advanced-plans/PLANNING.md`:
   - Advance loop pointer
   - Update `last_updated`

7. Git commit:
   ```bash
   git add -A && git commit -m "complete: [loop_name] — [handoff.done]"
   ```

8. Check continuation:
   - If loop `status: failed`: **STOP**. Print failure details and exit auto mode.
   - If more loops pending: return to sub-step 1 (next loop)
   - If all loops complete: proceed to Step 8d

#### 8d. Return to gate review

All loops in Phase [N+1] are complete. Increment `N` and return to **Step 3** (gate review)
to evaluate this phase before advancing further.

Print:
```
Phase [N+1] loops complete. Running gate review...
```

### 7. Gate FAIL — remediation controller (--auto) or versioned retry (default)

#### 7.0. Precedence of flags (evaluated before anything else)

- `--force` was already handled in Step 5 (gate forced to pass). If execution reaches
  Step 7, `--force` is NOT set.
- `--skip-gate` bypasses the gate entirely and never reaches Step 7.
- Therefore: **`--auto --force`** = gate fail is impossible to reach here (Step 5 exits
  early); **`--auto --skip-gate`** = gate never runs, Step 7 is never reached.
- Without `--auto`, Step 7 runs the versioned-retry + STOP path (Steps 7a–7j below)
  unconditionally. This is byte-for-byte the same behavior as before this command was
  updated.

---

#### 7-AUTO. Bounded remediation controller (--auto only)

This section runs ONLY when `AUTO_PHASE_MODE = true`. If `AUTO_PHASE_MODE = false`,
skip directly to **Step 7a** (versioned-retry + STOP path).

**7-AUTO-a. Count remediation cycles from history.jsonl**

Count the number of `gate_fail` events for `phase-[N]` already appended to
`.advanced-plans/state/history.jsonl` (the current failing event was appended in Step 4,
so this count includes it):

```bash
grep -c '"event":"gate_fail".*"phase":"phase-[N]"' .advanced-plans/state/history.jsonl 2>/dev/null || echo 0
```

Set `cycles = <that count>`.

If `cycles >= 2`:
- Print:
  ```
  Phase [N] gate FAILED (attempt [attempt]) — cycle bound reached (cycles=[cycles]).
  Escalating to versioned retry from pre-remediation snapshot.
  ```
- Use the pre-remediation SHA recorded in Step 7-AUTO-c (if set) as the baseline for
  `create_retry_version`; if no pre-remediation SHA is recorded (first failure reached the
  bound without a prior cycle), use the current HEAD.
- Proceed to **Step 7a** (versioned-retry + STOP).

**7-AUTO-b. First-cycle setup (if cycles == 1)**

On the first remediation cycle (`cycles == 1`):

1. Record the pre-remediation commit SHA:
   ```bash
   git rev-parse HEAD
   ```
   Store as `PRE_REMEDIATION_SHA`. This is the baseline for escalation versioning.

2. Preserve the ref for inspection:
   ```bash
   git tag phase-[N]-remediation-attempts 2>/dev/null || true
   ```
   (Non-fatal if tag already exists.)

3. **Dirty-tree preflight.** Check for uncommitted changes unrelated to this loop:
   ```bash
   git diff --name-only HEAD
   ```
   If any untracked/modified files exist that are NOT part of the expected loop outputs,
   print:
   ```
   ESCALATE: dirty working tree before remediation — unrelated changes detected.
   Commit or stash them before /next-phase --auto.
   ```
   Then proceed to **Step 7a** (versioned-retry + STOP from `PRE_REMEDIATION_SHA`).

4. **Freeze the phase success criteria.** Extract the `## Success Criteria` block from
   `.advanced-plans/phases/phase-[N]/plan.md` and write it to
   `.advanced-plans/phases/phase-[N]/criteria-frozen.md`. Record its SHA-256 hash as
   `CRITERIA_HASH`:
   ```bash
   python -c "import hashlib, pathlib; f=pathlib.Path('.advanced-plans/phases/phase-[N]/criteria-frozen.md'); print(hashlib.sha256(f.read_bytes()).hexdigest())"
   ```
   Store as `CRITERIA_HASH`.

**7-AUTO-c. Triage findings**

Import and call `triage_findings` from `platforms/python/remediate.py`:

```python
import runpy; runpy.run_path(r'.advanced-plans/bin/ap.py')['bootstrap']()
from platforms.python.remediate import triage_findings
result = triage_findings(verdict)
# result keys: structural, localized, unfixable, conflict
```

Where `verdict` is the failing agent's verdict dict read in Step 7b.

If `result["unfixable"]` is non-empty:
- Print:
  ```
  ESCALATE: unfixable finding(s) detected — no actionable location and no structural revert covers them.
  ```
- Proceed to **Step 7a** (versioned-retry + STOP).

If `result["conflict"]` is non-empty:
- Print:
  ```
  ESCALATE: contradictory findings (remediation_conflict) — same location targeted by multiple
  incompatible findings. Human review required.
  ```
- Proceed to **Step 7a** (versioned-retry + STOP).

**7-AUTO-d. Assert sentinel is absent**

Before dispatching any fix, the `gate-review-mode` sentinel MUST be removed
(Step 3e already removes it after the gate; this is a defense-in-depth ASSERT):

```bash
if [ -f .advanced-plans/state/gate-review-mode ]; then
  echo "ESCALATE: gate-review-mode sentinel still present — cannot dispatch fix (PreToolUse hook would block source edits with exit 2). Remove .advanced-plans/state/gate-review-mode first."
  exit 1
fi
```

If the sentinel exists: escalate (proceed to **Step 7a**, do NOT continue).

**7-AUTO-e. Write failure context sidecar**

Write the failure context to the worker-only sidecar
(`.advanced-plans/phases/phase-[N]/retry-context.json`). Call
`inject_failure_context` from `platforms/python/versioning.py`:

```python
import runpy; runpy.run_path(r'.advanced-plans/bin/ap.py')['bootstrap']()
from platforms.python.versioning import inject_failure_context
import pathlib
inject_failure_context(
    pathlib.Path(".advanced-plans/phases/phase-[N]/loops.md"),
    verdict=verdict_dict,  # the failing verdict
)
```

This writes `.advanced-plans/phases/phase-[N]/retry-context.json`. It does NOT modify
`loops.md` frontmatter.

**7-AUTO-f. Dispatch remediation**

Dispatch based on triage result. Both paths may be active if both `structural` and
`localized` are non-empty (overlap is harmless — the re-run will also fix the localized
issue incidentally).

**Structural path** (if `result["structural"]` is non-empty):

For each loop id in `result["structural"]`:

1. Set `current_loop = <loop_id>`
2. Git checkpoint:
   ```bash
   git add -A && git commit -m "checkpoint: before remediation re-run [loop_id]"
   ```
3. Spawn `ralph-orchestrator` to prepare the loop:
   - It reads `retry-context.json` for context.
   - It writes `.advanced-plans/state/loop-ready.json`.
4. Spawn `ralph-loop-worker` to execute the loop.
   - Worker reads `retry-context.json` directly.
5. Read `.advanced-plans/state/loop-complete.json`.
6. If loop `status: failed`: this is a **loop-fail STOP** (not a remediation cycle).
   Print:
   ```
   Loop [loop_id] FAILED during structural remediation — not a remediation cycle.
   STOP: manual review required.
   ```
   Exit auto mode immediately (do NOT increment cycle count or re-gate).

**Localized path** (if `result["localized"]` is non-empty):

Spawn `analysis-worker` with a focused-fix prompt:

```
You are analysis-worker performing a focused remediation fix.

Phase: [N]
Retry context: .advanced-plans/phases/phase-[N]/retry-context.json
Frozen criteria: .advanced-plans/phases/phase-[N]/criteria-frozen.md

Critical findings requiring a fix:
[list each localized finding: location, description, evidence]

Instructions:
- Read the retry context and the frozen criteria.
- Fix ONLY the specific file/line identified in each finding's location field.
- Do NOT modify: .advanced-plans/phases/**/plan.md, **/loops.md,
  core/schemas/**, core/state/**, platforms/python/tests/** (unless the test
  itself is the source of the bug and is NOT an assertion of a failed criterion),
  gate-agent docs, gate-verdict* files, or criteria-frozen.md.
- After editing, return a summary of changed files.
```

Wait for the agent to return.

**7-AUTO-g. Validate the diff allowlist**

After all fix dispatches complete, validate that only allowlisted source files were touched.

Define the allowlist (files the remediation cycle may modify):
- Any file under `platforms/` (excluding `platforms/python/tests/**` that assert
  the failed criteria)
- Any file under `core/skills/` or `core/agents/`
- Any file under `.claude/` (skills, commands, agents)
- `.advanced-plans/phases/phase-[N]/retry-context.json` (written by Step 7-AUTO-e)

Define the NEVER-TOUCH list (any match → escalate immediately, do not re-gate):
- `.advanced-plans/phases/**/plan.md`
- `.advanced-plans/phases/**/loops*.md` (including versioned files)
- `.advanced-plans/phases/**/criteria-frozen.md`
- `core/schemas/**`
- `core/state/**`
- `platforms/python/tests/**` test files that contain assertions for the failed criteria
- `core/agents/gate-reviewer.md`
- `platforms/claude-code/agents/**` gate agent docs
- `.advanced-plans/gate-verdicts/**`
- `.advanced-plans/state/history.jsonl`
- `.advanced-plans/state/loop-ready.json`
- `.advanced-plans/state/loop-complete.json`
- `.advanced-plans/state/gate-review-mode`

Get the diff of files changed since `PRE_REMEDIATION_SHA`:

```bash
git diff --name-only [PRE_REMEDIATION_SHA]..HEAD
```

For each changed file:
- If it matches the NEVER-TOUCH list: print:
  ```
  ESCALATE: remediation touched a forbidden path: [path]
  This is a gate-gaming attempt or a configuration error.
  ```
  Then proceed to **Step 7a** (versioned-retry + STOP from `PRE_REMEDIATION_SHA`).

**No-change detection (allowlisted source only):**

If the diff of allowlisted source paths (excluding transient files:
`retry-context.json`, `history.jsonl`, `gate-verdicts/`, `loop-ready.json`,
`loop-complete.json`, `gate-review-mode`) is empty:
- Print:
  ```
  ESCALATE: remediation produced no change to allowlisted source files.
  The fix had no effect — cannot re-gate.
  ```
- Proceed to **Step 7a** (versioned-retry + STOP from `PRE_REMEDIATION_SHA`).

**7-AUTO-h. Commit the remediation**

Stage ONLY the allowlisted source paths that were actually changed. NEVER use `git add -A`.

```bash
git add [space-separated list of allowlisted changed source files only]
git commit -m "remediate: phase-[N] cycle [cycles] — [brief summary of changes]"
```

Append the `gate_remediation` event to `history.jsonl`:

```bash
echo '{"event":"gate_remediation","phase":"phase-[N]","cycle":[cycles],"timestamp":"[ISO timestamp]","structural_count":[len(result.structural)],"localized_count":[len(result.localized)]}' >> .advanced-plans/state/history.jsonl
```

**7-AUTO-i. Assert frozen criteria still match**

Before spawning the re-gate, verify the frozen criteria have not changed:

```bash
python -c "
import hashlib, pathlib
f = pathlib.Path('.advanced-plans/phases/phase-[N]/criteria-frozen.md')
h = hashlib.sha256(f.read_bytes()).hexdigest()
expected = '[CRITERIA_HASH]'
if h != expected:
    raise SystemExit('ESCALATE: criteria-frozen.md hash mismatch — criteria have been altered. Aborting re-gate.')
print('criteria hash OK:', h)
"
```

If the hash does not match: proceed to **Step 7a** (versioned-retry + STOP from
`PRE_REMEDIATION_SHA`).

**7-AUTO-j. Re-gate (fresh agents, frozen criteria)**

Run a new gate review — this is the same as Step 3, with the following differences:
- The sentinel is raised NOW (just for this gate spawn) and removed immediately after.
- The gate agent prompt includes a reference to `criteria-frozen.md` as the authoritative
  criteria source (per the Re-Gate Isolation Rule in `core/agents/gate-reviewer.md`).
- Increment `attempt` by 1 for this re-gate.

After each gate agent returns its verdict, before aggregating:
- Validate that the verdict contains a `criteria_outcomes` field with an entry for EVERY
  criterion listed in `criteria-frozen.md`.
- If any criterion is missing from `criteria_outcomes`: print:
  ```
  ESCALATE: re-gate verdict from [agent-name] is missing criteria_outcomes for criterion: [criterion].
  A fresh agent must evaluate ALL frozen criteria.
  ```
  Then proceed to **Step 7a** (versioned-retry + STOP from `PRE_REMEDIATION_SHA`).

Aggregate verdicts as in Step 3f.

If `GATE_RESULT = pass`:
- Append `gate_pass` event with `passed_after_remediation: true` to `history.jsonl`:
  ```bash
  echo '{"event":"gate_pass","phase":"phase-[N]","attempt":[attempt],"timestamp":"[ISO timestamp]","agents":["code-review-agent","phase-goals-agent"],"passed_after_remediation":true,"cycles":[cycles],"verdict_files":[...]}' >> .advanced-plans/state/history.jsonl
  ```
- Print:
  ```
  Phase [N] gate PASSED after [cycles] remediation cycle(s).
  Note: passed_after_remediation=true recorded in history.
  ```
- Proceed to **Step 6** (gate pass path).

If `GATE_RESULT = fail`:
- Append `gate_fail` event to `history.jsonl` (Step 4 logic applies — cycles increments on
  the next pass through Step 7-AUTO-a).
- Return to **Step 7-AUTO-a** (loop — check cycle bound again).

---

#### Versioned-retry + STOP (non-auto default, and escalation path)

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
cp .advanced-plans/phases/phase-[N]/loops.md .advanced-plans/phases/phase-[N]/loops-v[next_attempt].md
```

**7d. Inject gate_failure_context block**

Edit the new versioned file (`.advanced-plans/phases/phase-[N]/loops-v[next_attempt].md`). In the
YAML frontmatter of each loop listed in `loops_to_revert`, add a `gate_failure_context`
block:

```yaml
gate_failure_context:
  attempt: [attempt]
  verdict_file: ".advanced-plans/gate-verdicts/phase-[N]-attempt-[attempt]-[agent-name].json"
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

In the original loop file (`.advanced-plans/phases/phase-[N]/loops.md`), change any
`status: pending` or `status: in_progress` todos to `status: frozen` to prevent
the original from being modified during retry.

**7g. Update PLANS-INDEX.md**

Read `.advanced-plans/PLANS-INDEX.md`. Update the Phase [N] entry:
- Add versioned file as the new active file
- Set attempt number to `next_attempt`
- Note: original file is now frozen

If `PLANS-INDEX.md` does not exist, create it with a Phase [N] entry.

**7h. Append phase_retry event to history.jsonl**

```bash
echo '{"event":"phase_retry","phase":"phase-[N]","attempt":[next_attempt],"timestamp":"[ISO timestamp]","new_loop_file":".advanced-plans/phases/phase-[N]/loops-v[next_attempt].md","original_loop_file":".advanced-plans/phases/phase-[N]/loops.md"}' >> .advanced-plans/state/history.jsonl
```

**7i. Git commit**

```bash
git add -A && git commit -m "retry: phase-[N] attempt [next_attempt] — gate failed on [failing-agent]"
```

**7j. Print failure summary**

```
Phase [N] gate FAILED (attempt [attempt]).
  Failed agent:  [agent-name]
  Verdict file:  [path]
  Issues found:  [count]

Versioned retry files created:
  New loop file: .advanced-plans/phases/phase-[N]/loops-v[next_attempt].md
  Failure context injected into: [list of affected loops]
  Original file frozen: .advanced-plans/phases/phase-[N]/loops.md

Run /next-loop to begin Phase [N] retry (attempt [next_attempt]).
```

## Notes

- Gate review is mandatory by default — use `--skip-gate` only when the review has already
  been run separately via `/run-gate`
- `--force` overrides gate failure but does not suppress the `gate_fail` history event
- Versioned retry files preserve all completed work; only `loops_to_revert` are reset
- The `do_not_repeat` field in `gate_failure_context` is carried forward through all retries
- After all phases complete, run `/run-closeout` to produce the programme narrative
- **Remediation safety:** a remediation cycle may only touch allowlisted source files.
  Any path matching the NEVER-TOUCH list causes immediate escalation to versioned-retry+STOP.
  The phase success criteria are frozen before the first cycle and hash-verified before
  each re-gate; any drift → escalate. Re-gate agents must emit `criteria_outcomes` for ALL
  frozen criteria; a missing criterion → escalate.
- **Git state:** the remediation commit stages only the allowlisted source paths that changed.
  `git add -A` is NEVER used in a remediation commit. Transient files (retry-context.json,
  history.jsonl, verdicts, sentinels) are excluded from no-change detection.
- **passed_after_remediation:** a `gate_pass` event following ≥1 remediation cycle carries
  `passed_after_remediation: true`. Under v1 the phase still advances; enforcement (requiring
  human sign-off before building further) is a follow-on.

### Auto mode stop conditions

| Condition | Behaviour |
|-----------|-----------|
| Gate FAIL, cycles < 2, `--auto` | Triage → fix → re-gate (bounded remediation loop) |
| Gate FAIL, cycles >= 2, `--auto` | Versioned retry from pre-remediation snapshot, STOP |
| Gate FAIL, no `--auto` | Versioned retry + STOP (byte-for-byte today's behavior) |
| Unfixable or contradictory findings | ESCALATE → versioned retry + STOP immediately |
| Sentinel present before fix dispatch | ESCALATE → versioned retry + STOP |
| Diff touches forbidden path | ESCALATE → versioned retry + STOP |
| No change to allowlisted source after fix | ESCALATE → versioned retry + STOP |
| Criteria hash mismatch before re-gate | ESCALATE → versioned retry + STOP |
| Re-gate verdict missing a criterion | ESCALATE → versioned retry + STOP |
| Loop FAIL during structural remediation | Loop-fail STOP (not a remediation cycle) |
| Loop FAIL during normal execution | STOP with loop failure details |
| All planned phases complete | STOP with "Programme complete" message |
| No master plan / no next phase description | STOP, prompt user to run `/decompose-phase` manually |
| `--skip-gate` combined with `--auto` | Gates skipped, no remediation, phases advance without review |
| `--force` combined with `--auto` | Gate fail forced to pass in Step 5; Step 7 never reached |
