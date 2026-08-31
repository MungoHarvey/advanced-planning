---
description: Bridge from exploratory analysis to execution-ready planning. Explores the codebase (read-only), then runs the full planning pipeline to produce execution-ready ralph loops.
allowed-tools: Read, Write, Glob, Grep, Bash, Edit, Agent
argument-hint: "[description of what you want to accomplish] [--auto]"
---

# /plan-and-phase

Bridge exploratory thinking into execution-ready loop plans. Explores the codebase read-only,
presents findings for review, then runs the full planning pipeline.

## Steps

### Step 0: Parse --auto flag

If `$ARGUMENTS` contains `--auto`:

- Set `AUTO_EXECUTE = true`
- Strip `--auto` from `$ARGUMENTS` before passing to skills

Otherwise: `AUTO_EXECUTE = false` (default).

### Step 1: Enter Planning Mode

The planning-mode sentinel lives at `.advanced-plans/state/planning-mode`. Creating it
activates the PreToolUse hooks in `settings.json` that restrict writes during exploration.

```bash
mkdir -p .advanced-plans/state && echo "$(date -Iseconds)" > .advanced-plans/state/planning-mode
```

Print: `Planning mode active — writes restricted to .advanced-plans/ only`

### Step 2: EXPLORE — Codebase Exploration

Use `$ARGUMENTS` as the exploration focus. If no arguments provided, ask the user what they
want to accomplish before continuing.

Read-only exploration — do NOT write any files except to `.advanced-plans/`:

1. Read architecture files: `CLAUDE.md`, `README.md`, top-level directory structure
2. Glob for source files relevant to the stated goal
3. Grep for patterns, interfaces, and existing implementations related to the goal
4. Read files that are directly relevant to understanding the work ahead

Save findings to `.advanced-plans/exploration-notes.md` with these sections:

```markdown
## Exploration Focus
[What we are trying to accomplish]

## Codebase Structure
[Relevant areas of the codebase — directories, key files, patterns]

## Key Findings
[Patterns discovered, existing code to build on, constraints, interfaces]

## Risks & Concerns
[Potential issues, unknown areas, things that need more investigation]

## Recommendations
[Suggested approach for phase planning — what to tackle first, how to scope]
```

### Step 3: HUMAN REVIEW GATE

Present a concise summary of the exploration findings. Ask the user to choose:

- **continue** — Proceed to phase planning using these findings
- **edit** — User refines the exploration notes directly, then says "continue"
- **stop** — Remove sentinel, exit (exploration notes preserved for later use)

Wait for the user's response before proceeding.

### Step 4: Exit Planning Mode

```bash
rm -f .advanced-plans/state/planning-mode
```

Print: `Planning mode exited — writes re-enabled`

### Step 5: PHASE DECOMPOSITION

Resolve the `phase-plan-creator` skill:

1. Check `.claude/skills/phase-plan-creator/SKILL.md`
2. Fall back to `~/.claude/skills/phase-plan-creator/SKILL.md`
3. Fall back to the core skills path referenced in CLAUDE.md

Load the skill. Use the exploration notes from `.advanced-plans/exploration-notes.md`
plus `$ARGUMENTS` as input. Follow the skill's process to produce a phase plan.

Save to `.advanced-plans/phases/phase-[N]/plan.md` (increment N based on existing phase dirs).

### Step 6: FULL PIPELINE

Run each remaining planning skill in sequence, exactly as `/new-phase` does:

1. Load `ralph-loop-planner` — decompose phase into loops, save to `.advanced-plans/phases/phase-[N]/loops.md`
2. Load `plan-todos` — populate todos for every loop
3. Load `plan-skill-identification` — assign skills to todos
4. Load `plan-subagent-identification` — assign agents to todos

Resolve each skill from `.claude/skills/` first, then `~/.claude/skills/`.

### Step 7: Update PLANNING.md

Read `.advanced-plans/PLANNING.md` and update:

- `current_phase:` — set to the new phase number
- `current_loop:` — set to the first loop
- `status:` — set to `in_progress`
- `last_updated:` — today's date

### Step 8: Emit phase_planned event and print completion summary

Append a `phase_planned` event to the audit log:

```bash
python ".advanced-plans/bin/ap.py" history_log .advanced-plans/state/history.jsonl \
  "{\"event\":\"phase_planned\",\"phase\":\"phase-[N]\",\"loops\":[loop count],\"todos\":[total todos]}"
```

If `AUTO_EXECUTE` is false:

```
Phase [N] — [phase name] ready for execution
  Loops:      [loop count] loops planned
  Todos:      [total todos] todos across all loops
  Plan file:  .advanced-plans/phases/phase-[N]/plan.md
  Loop file:  .advanced-plans/phases/phase-[N]/loops.md

Run /next-loop to begin execution.
Run /next-loop --auto to chain all loops until the phase completes.
```

If `AUTO_EXECUTE` is true:

```
Phase [N] — [phase name] — planning complete. Beginning autonomous execution...
  Loops:      [loop count] loops planned
  Todos:      [total todos] todos across all loops
```

Then immediately chain into `/next-loop --auto` (no confirmation gate — user chose `--auto`).

## Notes

- The sentinel file `.advanced-plans/state/planning-mode` is the canonical owner of planning-mode
  state. The PreToolUse hooks in `settings.json` check for its existence to restrict writes.
- The sentinel file `.advanced-plans/state/gate-review-mode` is the canonical owner of
  gate-review-mode state. Hooks check for its existence to restrict writes during gate review.
- If the user chooses **stop** at Step 3, the exploration notes are preserved in `.advanced-plans/`
  and can be fed to `/new-phase` manually
- The pipeline in Steps 5–6 is identical to `/new-phase` — the only difference is that
  exploration notes inform the phase plan rather than the user describing the goal cold
