---
description: Generate a retrospective synthesis of programme progress from handoff summaries and git history. Covers what was accomplished across completed loops and phases. For the current live state (what is pending right now), use /loop-status instead.
allowed-tools: Read, Glob, Grep, Bash
argument-hint: "[--phase N]"
---

# /progress-report

Retrospective synthesis of programme progress. Reads existing artefacts — phase plans,
loop handoff summaries, phase completion artefacts, and git history — and produces a
structured markdown report. Does not modify any files.

**Scope:** historical synthesis of completed work. For a live snapshot of what is currently
pending or in-progress, use `/loop-status`.

## Steps

### 1. Resolve skill path

Check for the progress-report skill in order:
1. `.claude/skills/progress-report/SKILL.md`
2. `~/.claude/skills/progress-report/SKILL.md`

Load the skill if found. If not found, proceed using the steps below directly.

### 2. Parse arguments

If `$ARGUMENTS` contains `--phase N`, scope all data gathering to phase N only.
Otherwise report on the full programme.

### 3. Gather historical data

1. Glob `.advanced-plans/phases/*/plan.md` for phase plans
2. Glob `.advanced-plans/phases/*/loops.md` for loop files (read handoff summaries)
3. Glob `.advanced-plans/phases/*/complete.md` for phase completion artefacts
4. Read `.advanced-plans/PLANS-INDEX.md` if it exists
5. Read `.advanced-plans/PLANNING.md` for current programme state
6. Run `git log --oneline --grep="complete:" --grep="checkpoint:" -30` for the commit trail
7. Read `.advanced-plans/state/loop-complete.json` for the most recent loop result
8. Read `.advanced-plans/logs/execution.log` (last 50 lines) if the file exists

### 4. Compile and print report

Produce a structured report with:
- Programme overview (current phase, overall status)
- Per-phase summary: phase title, loop count, key accomplishments from handoff summaries
- Recent git commit trail (last 10 relevant commits)
- Most recent loop result
- Any deferred items or open questions from phase completion artefacts

Print to the conversation — do not save to file unless the user asks.

### 5. Optional: save report

If the user asks to save the report:

Write to `.advanced-plans/progress-report-$(date +%Y-%m-%d).md`

## Notes

- This command is read-only — it never modifies plan files or state
- The git trail provides timestamps that plan files themselves do not carry
- Run after `/next-loop --auto` to see a summary of what the autonomous run accomplished
- Use `--phase N` to scope the report when working across a multi-phase programme
- For live loop/todo state, use `/loop-status` — it reads current pending/in-progress statuses
