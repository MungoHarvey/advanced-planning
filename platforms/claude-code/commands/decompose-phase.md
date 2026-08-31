---
description: Decompose a phase plan into executable ralph loop iterations. Pass the phase number or plan file path as the argument, or run without arguments to use the most recent phase plan.
allowed-tools: Read, Glob, Write, Edit
argument-hint: "[phase number or plan file path]"
---

# /decompose-phase

Decompose a phase plan into ralph loop iterations using the ralph-loop-planner skill.

## Skill & Agent Path Resolution

Resolve all `.claude/skills/` and `.claude/agents/` references in this order:

1. **Project-local** — `.claude/skills/<name>/` (preferred)
2. **Global fallback** — `~/.claude/skills/<name>/` (used when local copy absent)

For Glob operations, search both locations and merge results; local takes precedence
for any duplicate skill/agent names.

## Steps

### 1. Find the phase plan

- If `$ARGUMENTS` is provided:
  - Try `.advanced-plans/phases/phase-$ARGUMENTS/plan.md` (e.g. `phase-2/plan.md` for `/decompose-phase 2`)
  - Try as a direct file path
- If no arguments: `Glob(".advanced-plans/phases/*/plan.md")` and use the most recently modified

### 2. Read the phase plan file

### 3. Load the ralph-loop-planner skill

```
Read .claude/skills/ralph-loop-planner/SKILL.md
Read .claude/skills/ralph-loop-planner/references/ralph-loop-template.md
Read .claude/skills/ralph-loop-planner/references/todo-schema.md
```

### 4. Confirm preferences

Ask the user:

- How many loops (approximate)? Default: 3–5
- Any specific skills to map against? (optional)

### 5. Follow the ralph-loop-planner process

Generate loops following the skill instructions. Each loop stub has:

- Complete YAML frontmatter with empty `todos[]` and empty `handoff_summary`
- Full markdown body (Overview, Success Criteria, Skills, Dependencies, Complexity)

### 6. Save output

Save to `.advanced-plans/phases/phase-[N]/loops.md` (co-located with the phase plan).

Update `.advanced-plans/PLANS-INDEX.md` to record the new loops file.

### 7. Prompt next step

```
[N] ralph loops saved to .advanced-plans/phases/phase-[N]/loops.md

Run /loop-status to review the plan structure.
Run /next-loop to begin execution (todos will be auto-populated on first run).
```

## Usage

```
/decompose-phase 2
```

Decompose phase 2 plan into loops.

```
/decompose-phase .advanced-plans/phases/phase-refactoring/plan.md
```

Decompose a named plan file.

```
/decompose-phase
```

Uses the most recently modified phase plan.
