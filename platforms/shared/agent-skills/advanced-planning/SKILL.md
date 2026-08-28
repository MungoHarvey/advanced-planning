# advanced-planning

**Advanced Planning Router** — routes the five planning verbs to the shared Python runtime.

## When to Use

Use this skill when the user invokes any of these five actions:

| Verb | Example |
|------|---------|
| `phase` | `phase <goal>` — create a new phase plan |
| `loop` | `loop next` — execute one orchestrator → worker cycle |
| `gate` | `gate current` — run gate review on completed phase |
| `resume` | `resume` — recover from mid-session interruption |
| `compact` | `compact current` — generate phase compaction artefacts |

This skill is host-neutral. It works identically under Codex, OpenCode, and any other host that discovers `.agents/skills/advanced-planning/SKILL.md`.

## Process

### 1. Parse the action

Extract the verb (first word) and arguments (remainder). Valid verbs are: `phase`, `loop`, `gate`, `resume`, `compact`.

If the verb is unknown, print:
```
Unknown action: <verb>
Valid actions: phase, loop, gate, resume, compact
```
and stop.

### 2. Validate state directory

All state operations use `.advanced-plans/state/`. If the directory does not exist and the action requires it, create it.

### 3. Route to the shared runtime

Every Python call goes through the launcher, in exactly this form:

```
python ".advanced-plans/bin/ap.py" <module> [args]
```

Never `python -m platforms.python.<module>`, never `python platforms/python/<module>.py`, never `sys.path.insert(0, '.')`.

### 4. Action implementations

#### `phase <goal>`

1. Call the phase planning pipeline via the shared runtime.
2. When the phase plan is written to `.advanced-plans/phases/phase-N/plan.md`, print the plan and the human gate instruction:

   ```
   REVIEW .advanced-plans/phases/phase-N/plan.md

   Reply with exactly one:
   APPROVE phase-N
   REVISE phase-N: <instructions>
   STOP phase-N
   ```

3. **Stop and wait.** Do not proceed to loop decomposition. Do not record an approval event. Do not run auto mode.

4. On `APPROVE phase-N`: run loop decomposition, todo population, skill assignment, and agent assignment. Update `.advanced-plans/PLANNING.md`.

5. On `REVISE phase-N`: rerun phase planning with the supplied instructions and present the revised plan.

6. On `STOP phase-N`: preserve the plan and exit.

#### `loop next`

1. Check for outstanding human review. If a phase plan exists without an approval record, print the gate instruction and stop.

2. Validate `loop-ready.json` if present:
   - If it exists and matches the next pending loop, proceed to worker assignment.
   - If it exists but is stale (different phase), archive it and start fresh.

3. Spawn the orchestrator (via native subagent or external Herdr task) to prepare `loop-ready.json`.

4. Once `loop-ready.json` is written and validated (use `state_validate loop-ready`), spawn the worker to execute the loop.

5. On worker completion, validate `loop-complete.json` and update planning state.

**Auto-chaining is not the default.** `loop next` performs exactly one cycle. Auto-chaining requires an explicit `--auto` flag.

#### `gate current`

1. Identify the current completed phase from `.advanced-plans/PLANNING.md`.

2. Spawn independent gate reviewers (one per review type) to evaluate the phase outputs.

3. Validate every verdict against `core/state/gate-verdict.schema.json`.

4. If all verdicts pass: close the phase, advance the pointer, and direct to `/phase-compact`.

5. If any verdict fails: create validated retry context with `gate_failure_context` injected, and stop for operator direction.

#### `resume`

1. Validate existing state:
   - If an outstanding human review exists: reprint the plan and gate instruction.
   - If `loop-complete.json` exists and matches `loop-ready.json`: finalize without rerunning.
   - If `loop-ready.json` exists without matching completion: resume that assignment.
   - If state is dirty or contradictory: stop for explicit direction.
   - If JSON is invalid: do not overwrite; report the defect.

2. Proceed based on the validated state.

#### `compact current`

1. Generate and validate phase handoff and compaction artefacts:
   - `.advanced-plans/phases/phase-N/complete.md` (cold artefact)
   - `.advanced-plans/PLANS-INDEX.md` manifest entry (hot artefact)
   - `.advanced-plans/phases/phase-N/handoff.md` (resume digest)

2. **Do not claim to compact host conversation context.** This action compacts AAW artefacts only.

3. If the host exposes a native context-compaction command, print it for the user. Otherwise print:
   ```
   Start a new session and run the resume trigger.
   ```

## Output Format

### Success

Print a brief summary of what happened:
- Phase created: `Created phase-N: <title>`
- Loop executed: `Completed ralph-loop-NNN: <task_name>`
- Gate passed: `Phase-N passed gate review`
- Gate failed: `Phase-N failed gate review: <reason>`
- Resumed: `Resumed ralph-loop-NNN`
- Compacted: `Compacted phase-N artefacts`

### Failure

Print a clear error message:
- Unknown action: `Unknown action: <verb>`
- Missing state: `No state found: <path>`
- Validation failed: `Validation failed: <details>`
- Human gate blocking: `Awaiting human review: <instruction>`

## References

- `orchestrator-prompt.md` — full orchestrator role prompt
- `worker-prompt.md` — full worker role prompt
- `gate-reviewer-prompt.md` — full gate reviewer role prompt
- `manual-review.md` — human gate text

## Constraints

- **State directory:** `.advanced-plans/state/` — never a host-private directory.
- **Schema validation:** use `state_validate` before publishing any state document and after reading one.
- **Human gate blocks:** after phase planning, print the gate instruction and stop.
- **No Plannotator:** do not mention, detect, or recommend the deprecated review companion.
- **Checkpoint ownership:** the worker never commits. Codex runs in linked worktrees where `git commit` is forbidden by sandbox; the external controller commits.
