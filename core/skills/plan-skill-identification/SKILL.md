---
name: plan-skill-identification
model: opus
description: "Read the todos[] array in a ralph loop's YAML frontmatter and update the skill: field for each todo in-place. Matches each task's content and outcome against available skills to find the best fit; sets skill: NA for tasks that require no specialist skill. Run after plan-todos and before plan-subagent-identification. Maintains canonical field order when editing. Triggers: assign skills, identify skills for todos, skill mapping, fill skill fields, match skills to tasks."
---

# Plan Skill Identification

Reads a ralph loop's populated `todos[]` and assigns the most appropriate skill to each task.
Edits the `skill:` field in-place, maintaining canonical schema order.

## When to Use

- `todos[]` has been populated by `plan-todos` (all skills currently `NA`)
- Part of the full pipeline: `ralph-loop-planner` → `plan-todos` → **`plan-skill-identification`** → `plan-subagent-identification`
- You want to explicitly map skills before execution rather than leaving them for auto-detection

## Your Input

Provide:
- **Loop file path** (e.g. `plans/ralph-loop-002.md`)
- **Skills directory path** — the location of available SKILL.md files for this project

## Process

1. **Read the loop file** — extract all todos with `skill: NA`

2. **Discover available skills:**
   - List all `SKILL.md` files in the skills directory (e.g. `core/skills/*/SKILL.md`)
   - Read each SKILL.md's frontmatter `name` and `description` fields
   - Also check for globally available skills in any additional skill locations

3. **For each todo:**
   - Read `content` and `outcome`
   - Match against skill descriptions using the three-level cascade (see below)
   - Assign the best-fit skill name, or `NA` if no specialist skill is needed

4. **Update `skill:` field in-place** for each todo, maintaining canonical order:
   ```
   id → content → skill → agent → outcome → status → complexity → priority
   ```

5. **Report** any todos where no good skill match was found — flag as `MISSING: [description]`
   rather than leaving `NA`, so skill gaps are surfaced explicitly

## Three-Level Skill Cascade

Skills are assigned at three levels, each more specific than the last:

```
Phase-level (broad):
  `statistical-analysis` — assigned to the whole phase
  ↓
Loop-level (specific):
  `data-processing` — transforming raw inputs to analysis-ready format
  `output-formatting` — structuring results for downstream consumers
  ↓
Todo-level (precise):
  `schema-design` — needed specifically for the canonical field order in state files
```

When running plan-skill-identification, you are operating at the **todo level** — the most
precise tier. The phase and loop level skills inform which specialist sub-skills to look for.

## Skill Assignment Rules

- Use the skill's exact `name` from its SKILL.md frontmatter
- Assign `NA` for tasks that are straightforward file I/O, git operations, simple scripting, or general reference writing
- If two skills both fit, choose the **more specific** one
- If a task clearly needs a skill that does not exist yet, flag it as `MISSING: [description]` rather than leaving `NA` — this surfaces skill gaps for the project owner to address
- Do not assign skills to the handoff update task or git checkpoint tasks — these are `NA`

## Output Format

Updates `skill:` in each todo in-place:

```yaml
todos:
  - id: "loop-002-1"
    content: "Migrate phase-plan-creator skill into core/skills/phase-plan-creator/"
    skill: "skill-creator"        # ← was NA, now assigned
    agent: "NA"
    outcome: "SKILL.md exists at target path; zero platform-specific references present"
    status: pending
    priority: high

  - id: "loop-002-2"
    content: "Write git checkpoint commit before starting work"
    skill: "NA"                   # ← simple git operation; no specialist skill needed
    agent: "NA"
    outcome: "git log shows checkpoint commit before loop work begins"
    status: pending
    priority: high

  - id: "loop-002-3"
    content: "Verify all five skills are platform-agnostic with a scan"
    skill: "NA"                   # ← general verification; no specialist skill needed
    agent: "NA"
    outcome: "Zero occurrences of platform-specific terms across all core/skills/ SKILL.md files"
    status: pending
    priority: high
```

## Missing Skill Flagging

If no existing skill covers a todo, flag it explicitly:

```yaml
  - id: "loop-005-3"
    content: "Validate loop-ready.json against the JSON Schema"
    skill: "MISSING: json-schema-validator — tool to programmatically validate JSON against draft-07 schema"
    agent: "NA"
    outcome: "Validation command exits 0; 0 validation errors reported"
    status: pending
    priority: high
```

This surfaces skill gaps for the project owner rather than silently falling back to general capability.

## After Completion

Run `plan-subagent-identification` to assign `agent:` fields for tasks that benefit
from subagent delegation.

## See Also

- `ralph-loop-planner/references/todo-schema.md` — Canonical field order reference
- `plan-todos` — Derives todos before this skill runs
- `plan-subagent-identification` — Assigns agents after this skill runs
- `core/schemas/todo.schema.md` — Formal schema for validation
