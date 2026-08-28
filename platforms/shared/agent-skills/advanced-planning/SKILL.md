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

This skill is host-neutral. It works identically across all hosts that discover `.agents/skills/advanced-planning/SKILL.md`.

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

Two forms are valid (Contract 6):

**Form A — Modules with CLI** (have `if __name__ == "__main__"` block):
```bash
python ".advanced-plans/bin/ap.py" <module> [args]
```

**Form B — Library modules** (no CLI — use inline bootstrap):
```python
import runpy; runpy.run_path(r'.advanced-plans/bin/ap.py')['bootstrap']()
# Then call the library function directly
```

Modules **with** CLI: `state_validate`, `history_log`, `handoff_digest`

Modules **without** CLI (library only): `plan_io`, `state_manager`, `handoff` — use Form B.

Never `python -m platforms.python.<module>`, never `python platforms/python/<module>.py`, never `sys.path.insert(0, '.')`.

**Exit code contract**: The launcher exits `3` when the runtime is unreachable (moved checkout, missing manifest). On exit `3`, print the repair diagnostic and stop — do not carry on as though the step succeeded.

### 4. Action implementations

#### `phase <goal>`

1. **GAP:** `plan_io` has no `create_phase_plan` function. The runtime has `find_next_loop`, `_parse_simple_yaml_block`, etc. but no phase creation function. This is a **gap** — the runtime needs a new function for phase plan creation.

   For now, the host must perform phase planning directly (not through the runtime) and write `.advanced-plans/phases/phase-N/plan.md`.

2. When the phase plan is written, print the plan and the human gate instruction:

   ```
   REVIEW .advanced-plans/phases/phase-N/plan.md

   Reply with exactly one:
   APPROVE phase-N
   REVISE phase-N: <instructions>
   STOP phase-N
   ```

3. **Stop and wait.** Do not proceed to loop decomposition. Do not record an approval event. Do not run auto mode.

4. On `APPROVE phase-N`: run loop decomposition, todo population, skill assignment, and agent assignment.

   **GAP:** `plan_io` has no `decompose` function. Loop decomposition is done by the `ralph-loop-planner` skill, not a runtime module. The host should load and execute the `ralph-loop-planner` skill directly.

   Log the event (this module HAS CLI):
   ```bash
   python ".advanced-plans/bin/ap.py" history_log .advanced-plans/state/history.jsonl '{"event": "phase_approved", "phase": "phase-N"}'
   ```

5. On `REVISE phase-N`: rerun phase planning with the supplied instructions and present the revised plan.

6. On `STOP phase-N`: preserve the plan and exit.

#### `loop next`

1. Check for outstanding human review. If a phase plan exists without an approval record, print the gate instruction and stop.

2. Check state status. **Note:** `state_manager` is a library module (no CLI). Use the bootstrap form:

   ```python
   import runpy
   runpy.run_path(r'.advanced-plans/bin/ap.py')['bootstrap']()
   from platforms.python.state_manager import get_status
   status = get_status(".advanced-plans/state")
   # status has keys: has_loop_ready, has_loop_complete, loop_ready, loop_complete, history_count
   ```

3. Validate `loop-ready.json` if present (this module HAS CLI):
   ```bash
   python ".advanced-plans/bin/ap.py" state_validate loop-ready .advanced-plans/state/loop-ready.json
   ```
   - Exit code `0`: valid, proceed to worker assignment.
   - Exit code `1`: invalid document — print validation errors and stop.
   - Exit code `2` or `3`: environment error (missing schema, unreachable runtime) — print the repair diagnostic and stop.
   - If stale (different phase), archive via bootstrap form:
     ```python
     from platforms.python.state_manager import archive_cross_phase_state
     archive_cross_phase_state(".advanced-plans/state", "phase-N")
     ```

4. Spawn the orchestrator (via native subagent or external Herdr task) to prepare `loop-ready.json`.

5. Once `loop-ready.json` is written, validate before spawning the worker:
   ```bash
   python ".advanced-plans/bin/ap.py" state_validate loop-ready .advanced-plans/state/loop-ready.json
   ```

6. Spawn the worker to execute the loop.

7. On worker completion, validate `loop-complete.json`:
   ```bash
   python ".advanced-plans/bin/ap.py" state_validate loop-complete .advanced-plans/state/loop-complete.json
   ```
   Then log the event (HAS CLI):
   ```bash
   python ".advanced-plans/bin/ap.py" history_log .advanced-plans/state/history.jsonl '{"event": "loop_completed", "loop": "ralph-loop-NNN"}'
   ```

**Auto-chaining is not the default.** `loop next` performs exactly one cycle. Auto-chaining requires an explicit `--auto` flag.

#### `gate current`

1. Identify the current completed phase from `.advanced-plans/PLANNING.md`.

2. Spawn independent gate reviewers (one per review type) to evaluate the phase outputs.

3. Validate every verdict against the schema:
   ```bash
   python ".advanced-plans/bin/ap.py" state_validate gate-verdict gate-verdicts/phase-N-attempt-1.json
   ```
   - Exit code `0`: verdict is valid.
   - Exit code `1`: verdict is invalid — print validation errors and stop.
   - Exit code `2` or `3`: environment error — print the repair diagnostic and stop.

4. If all verdicts pass: close the phase, advance the pointer, and direct to `/phase-compact`. Log the event:
   ```bash
   python ".advanced-plans/bin/ap.py" history_log .advanced-plans/state/history.jsonl '{"event": "gate_pass", "phase": "phase-N"}'
   ```

5. If any verdict fails: create validated retry context with `gate_failure_context` injected, and stop for operator direction. Log:
   ```bash
   python ".advanced-plans/bin/ap.py" history_log .advanced-plans/state/history.jsonl '{"event": "gate_fail", "phase": "phase-N"}'
   ```

**External task dispatch** (if using Herdr/AAW fallback):
- Before dispatch, validate the envelope:
  ```bash
  python ".advanced-plans/bin/ap.py" state_validate external-task-envelope <envelope-path>
  ```
- After completion, validate collected evidence before state advances:
  ```bash
  python ".advanced-plans/bin/ap.py" state_validate collected-evidence <evidence-path>
  ```

#### `resume`

1. Validate existing state by reading status. **Note:** `state_manager` is a library module (no CLI). Use the bootstrap form:

   ```python
   import runpy
   runpy.run_path(r'.advanced-plans/bin/ap.py')['bootstrap']()
   from platforms.python.state_manager import get_status
   status = get_status(".advanced-plans/state")
   # status has keys: has_loop_ready, has_loop_complete, loop_ready, loop_complete, history_count
   ```

2. Based on the state:
   - **Outstanding human review**: Reprint the plan and gate instruction.
   - **`loop-complete.json` matches `loop-ready.json`**: Finalize without rerunning. Validate both (HAS CLI):
     ```bash
     python ".advanced-plans/bin/ap.py" state_validate loop-ready .advanced-plans/state/loop-ready.json
     python ".advanced-plans/bin/ap.py" state_validate loop-complete .advanced-plans/state/loop-complete.json
     ```
   - **`loop-ready.json` without matching completion**: Resume that assignment. Validate:
     ```bash
     python ".advanced-plans/bin/ap.py" state_validate loop-ready .advanced-plans/state/loop-ready.json
     ```
   - **Dirty or contradictory state**: Stop for explicit direction.
   - **Invalid JSON**: Do not overwrite; report the defect. Validate to get specific errors:
     ```bash
     python ".advanced-plans/bin/ap.py" state_validate loop-ready .advanced-plans/state/loop-ready.json
     ```

#### `compact current`

1. Generate and validate phase handoff and compaction artefacts:

   **Note:** `handoff` is a library module (no CLI). `handoff_digest` HAS CLI.

   For `handoff_digest` (HAS CLI):
   ```bash
   python ".advanced-plans/bin/ap.py" handoff_digest phase-N
   ```

   For the `handoff` module operations, use the bootstrap form:
   ```python
   import runpy
   runpy.run_path(r'.advanced-plans/bin/ap.py')['bootstrap']()
   from platforms.python.handoff import read_handoff, inject_handoff
   # Use these functions as needed
   ```

   These produce:
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
- **Deprecated review companions:** do not mention, detect, or recommend external review tools that are not part of the core planning framework.
- **Checkpoint ownership:** the worker never commits. Codex runs in linked worktrees where `git commit` is forbidden by sandbox; the external controller commits.
