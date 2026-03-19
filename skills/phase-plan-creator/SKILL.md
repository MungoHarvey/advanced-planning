---
name: phase-plan-creator
description: "Generate structured, verifiable overarching plans for project phases. Use when starting a new project phase, need to establish clear scope and dependencies, or want success criteria documented before iteration planning. Creates comprehensive phase plans that feed into @ralph-loop-planner. Always use this as the first step before detailed iteration planning. Triggers: new phase, project plan, phase plan, plan a project, what's the plan, how do we approach, scope this out, plan this work, start a project."
---

# Phase Plan Creator

Creates structured phase plans with clear objectives, dependencies, risk assessment, and skill
requirements. Output feeds directly into `@ralph-loop-planner` for iteration decomposition.

## When to Use

- Starting a new project phase or major task
- Need to establish scope and verifiable success criteria before iteration planning
- Breaking down complex problems into sequential phases
- Documenting assumptions, dependencies, and risks upfront
- Defining broad skill domains required for the phase

## Your Input

Provide:
- **Project/task description** — What you're trying to accomplish
- **Phase context** — Which phase (1, 2, 3) or phase name
- **Success definition** — What "done" looks like (optional; Claude can prompt)
- **Constraints** — Technical, resource, or scope constraints (optional)

## Claude's Process

1. **Ask clarifying questions** (if needed) about:
   - What must exist before this phase starts?
   - Highest risks or uncertainties?
   - Which skill domains apply?
   - Alternative approaches worth considering?

2. **Generate structured phase plan** following the template in `references/phase-plan-template.md`

3. **Output as markdown** suitable for:
   - Committing to `.claude/plans/`
   - Reviewing and editing inline
   - Feeding to `@ralph-loop-planner`
   - Logging to Obsidian vault

## Output Structure

```markdown
# Phase [N]: [Descriptive Name]

## Objective
[One clear sentence. Pattern: "[Action] [thing] [into/for] [goal]"]

## Scope
### Included:
- [Concrete deliverable]

### Explicitly NOT included:
- [Out of scope]

## Key Deliverables
- [Deliverable type]: [Specific description], format [X]

## Success Criteria
- ✓ [Measurable outcome]: [How verified]

## Dependencies
### Must Complete Before:
- [Task/phase]: [Why required]

### Blocked By:
- [External dependency]: [Status, ETA]

## Skills Required (Broad Categories)
- `[skill-domain]`: [Purpose in this phase]

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| [Risk] | Low/Med/High | Low/Med/High | [Action] |

## Assumptions
- `[Assumption]`: [Why we believe it; how we'll validate]

## Notes
[Design decisions, alternatives considered]
```

## Next Steps

1. **Review and edit** the generated phase plan inline
2. **Save** using `/new-phase` command (updates CLAUDE.md Planning State automatically)
3. **Pass to `@ralph-loop-planner`** to decompose into executable iterations

## See Also

- `references/phase-plan-template.md` — Detailed template with examples and best practices
- `@ralph-loop-planner` — Decompose phase plans into executable iterations
- `../../commands/new-phase.md` — `/new-phase` slash command wrapping this skill
- `../../references/claude-md-convention.md` — How CLAUDE.md Planning State is updated
