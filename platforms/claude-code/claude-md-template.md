# [Project Name] — CLAUDE.md

## Project Overview

[Brief description of what this project does and its primary goal]

## Key Commands

```bash
# Build
[build command]

# Test
[test command]

# Lint / format
[lint command]
```

Always run lint and tests before committing.

## Tech Stack & Conventions

- [Language/framework]: [Relevant conventions]
- [Naming conventions]: [e.g. snake_case for files, PascalCase for classes]
- [File structure]: [Where things live and why]

## Patterns Discovered

<!-- Updated after each completed phase -->
- [Pattern]: [When to apply it]

---

## Planning State

<!--
  This section is the persistent anchor for the advanced planning system.
  Updated automatically by /new-phase, /next-loop, and /loop-status.
  Do not delete — used for session continuity and cross-session handoffs.
-->

### Current Phase

```yaml
phase: 1
name: "[Phase Name]"
plan_file: ".claude/plans/phase-1.md"
status: not_started   # not_started | in_progress | complete
```

### Current Loop

```yaml
loop: "ralph-loop-001"
task: "[Task Name]"
loop_file: ".claude/plans/phase-1-ralph-loops.md"
todos_done: 0
todos_total: 0
```

### Last Handoff

```yaml
done: ""
failed: ""
needed: ""
```

### Completed Phases

| Phase | Name | Outcome | Loops |
|-------|------|---------|-------|
| — | — | — | — |

### Learnings & Decisions

<!-- Add after each completed phase. These inform future phases. -->
- [Decision]: [Why; what we would do differently]
- [Pattern discovered]: [When to apply it]
- [Gotcha]: [What to watch for]

---

## Skills Available

<!-- List active skills so the session knows what's available -->
- `phase-plan-creator`: Generate structured phase plans with verifiable success criteria
- `ralph-loop-planner`: Decompose phase plans into executable ralph loop iterations
- `plan-todos`: Derive atomic todo tasks from a loop description
- `plan-skill-identification`: Assign skills to todos by matching against available SKILL.md files
- `plan-subagent-identification`: Assign agents to todos based on delegation rules

## Subagents Available

<!-- List configured subagents and their purposes -->
- `ralph-orchestrator` (Sonnet): Prepares the next loop — finds pending work, populates todos, writes loop-ready.json
- `ralph-loop-worker` (Haiku): Executes todos with targeted skill injection, writes loop-complete.json
- `analysis-worker` (Haiku): General bounded execution agent for delegated analysis or implementation tasks
