# CLAUDE.md Planning State Convention

## Purpose

The `## Planning State` section in `CLAUDE.md` is the persistent anchor for the planning system.
It survives session restarts, `--resume` flags, and context resets. It is the single source of
truth for *where the project is* in the phase → loop hierarchy.

---

## Required Section in CLAUDE.md

Add this section to every project's `CLAUDE.md`. Update it at the end of each loop.

```markdown
## Planning State

Current phase: [N]
Current loop: ralph-loop-[NNN]
Loop status: pending | in_progress | completed | blocked

Last completed: ralph-loop-[NNN-1]
Last handoff:
  done: "[What was completed]"
  failed: "[What failed, or NA]"
  next: "[Exact action to resume from]"

Plans location: .claude/plans/
Active plan: .claude/plans/phase-[N]-ralph-loops.md
```

---

## Update Protocol

### After each loop completes:
1. Copy the handoff block from the loop's frontmatter into `CLAUDE.md`
2. Advance `current loop` to the next `pending` loop
3. Set `loop status` to `pending` (ready for next session)

### At loop start:
1. Read `## Planning State` to orient — no need to scan full plan file
2. Read the active plan file to load the current loop's todos and prompt
3. Inject the `last handoff` block into the loop's context (per the prompt template)

---

## Example: Mid-Project State

```markdown
## Planning State

Current phase: 2
Current loop: ralph-loop-003
Loop status: pending

Last completed: ralph-loop-002
Last handoff:
  done: "DESeq2 DE complete; results/deseq2_tdp43_wt.rds written; volcano plot generated"
  failed: "NA"
  next: "Run pathway enrichment on sig_hits.csv using fgsea; reference gene sets in data/msigdb_h.rds"

Plans location: .claude/plans/
Active plan: .claude/plans/phase-2-ralph-loops.md
```

---

## Why Not Just Read the Plan File?

Plan files are long. Reading the full YAML to find current state wastes context tokens.
`CLAUDE.md` is loaded at session start — the planning state is immediately available
without any file reads. The plan file is the *detail*; CLAUDE.md is the *pointer*.

---

## Global vs Project CLAUDE.md

| File | Scope | Use for |
|---|---|---|
| `~/.claude/CLAUDE.md` | All projects | Persistent preferences, global skills, tool permissions |
| `[project]/CLAUDE.md` | This project | Planning state, project conventions, tech decisions |

The `## Planning State` section belongs in **project** CLAUDE.md only.
Global CLAUDE.md should never contain project-specific state.

---

## Suggested Full CLAUDE.md Structure

```markdown
# [Project Name]

## Project Overview
[One paragraph: what this project is, tech stack, key goals]

## Key Commands
- Build: `[command]`
- Test: `[command]`
- Lint: `[command]`

## Conventions
- [Tech choice]: [How applied here]
- [Naming pattern]: [Specific format]

## Planning State

Current phase: [N]
Current loop: ralph-loop-[NNN]
Loop status: [status]

Last completed: ralph-loop-[NNN-1]
Last handoff:
  done: "[summary]"
  failed: "[summary or NA]"
  next: "[exact resume action]"

Plans location: .claude/plans/
Active plan: .claude/plans/phase-[N]-ralph-loops.md

## Learnings
[Patterns discovered, gotchas, decisions made during execution]
- [Loop NNN]: [Learning]
- [Loop NNN]: [Learning]
```
