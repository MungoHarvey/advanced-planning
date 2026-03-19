---
name: ralph-loop-planner
description: "Decompose phase plans into executable ralph loop iterations with verifiable outcomes, concise handoffs, and native TodoWrite sync. Use after @phase-plan-creator to generate task-based iterations ready for Claude Code execution. Each iteration includes YAML frontmatter with todos (id/content/skill/agent/outcome/status), a handoff block (done/failed/next), max_iterations with on_max_iterations recovery, and a complete execution prompt. Reference ralph-loop-template.md for full schema and examples."
---

# Ralph Loop Planner

Decomposes a phase plan into executable ralph loop iterations. Each iteration is self-contained,
has verifiable success criteria, and includes everything needed for execution and resumption.

## When to Use

- You have a phase plan (from `@phase-plan-creator`) and need executable iterations
- Need to assign specific skills to each iteration (refined from phase-level)
- Want verifiable success criteria and explicit done criteria per todo
- Preparing work for Claude Code execution with reliable context handoffs
- Need to identify sequencing and recovery behaviour between iterations

## Your Input

Provide:
- **Phase plan** (from `@phase-plan-creator` output or pasted directly)
- **Iteration count** (approximate; 3–6 is typical)
- **Execution context** (Claude Code primary? Local models? Hybrid?)
- **Output preference** (single file or individual files per loop)
- **Skill mapping** (optional: which skills exist in `.claude/skills/`?)

## Claude's Process

1. **Analyse phase plan** to identify:
   - Deliverables → iteration outcomes
   - Sequencing constraints → dependencies
   - Broad skills → refine to specific skills per loop
   - Complexity drivers → scope estimate per loop

2. **Generate N ralph loops** following the schema in `ralph-loop-template.md`

3. **For each loop, produce:**
   - YAML frontmatter with todos array (all fields canonical)
   - Handoff block (empty fields — filled at execution time)
   - `max_iterations` and `on_max_iterations` set appropriately
   - Complete execution prompt with context injection block
   - Markdown description (overview, skills, dependencies, complexity)

4. **Output locations:**
   - Single file: `.claude/plans/phase-N-ralph-loops.md`
   - Individual files: `.claude/plans/ralph-loop-NNN.md` + index

## Output Structure per Iteration

Each loop follows the full template in `ralph-loop-template.md`. Key fields:

```yaml
---
name: "ralph-loop-NNN"
task_name: "Descriptive Task Name"
max_iterations: 3
on_max_iterations: escalate       # escalate | checkpoint | rollback

handoff:
  done: ""
  failed: ""
  next: ""

todos:
  - id: loop-NNN-1
    content: "[atomic task]"
    skill: "[skill-name or NA]"
    agent: "[subagent-id or NA]"
    outcome: "[concrete done criteria]"
    status: pending

prompt: |
  # Context from previous loop
  <!-- Inject handoff from loop NNN-1 here -->
  
  # Objective
  [What this loop accomplishes]
  ...
---
```

## Handoff Convention

The `handoff` block is written at **completion**, not upfront. Three fields only:

```yaml
handoff:
  done: "[What was completed — files written, tests passing, decisions made]"
  failed: "[What did not complete and why; exact file/path if relevant; NA if none]"
  next: "[Precise action next loop starts with — not a restatement of phase goals]"
```

The next loop's prompt has a `## Context from previous loop` block. At execution time,
paste the handoff fields there. This keeps context clean across sessions.

## Skill Refinement Pattern

```
Phase-level skill: `bioinformatics-analysis`
↓ Refined for loop:
  - `deseq2-normalisation`: multiBatchNorm across batches
  - `visualization-generation`: PCA plots
  - (discovered) `batch-effect-detection`: needed before normalisation
```

Always distinguish: **Broad** (from phase plan) / **Specific** (refined for loop) / **Discovered** (new).

## Recovery Strategy by Loop Type

| Loop Type | Recommended `on_max_iterations` |
|---|---|
| Implementation/code | `escalate` — partial code is worse than none |
| Research/exploration | `checkpoint` — partial findings have value |
| Data processing | `checkpoint` — preserve processed outputs |
| Infrastructure | `rollback` — partial infra state is dangerous |

## Output Options

### Option A: Single Comprehensive File
All loops in `.claude/plans/phase-N-ralph-loops.md`:
- Quick overview of sequencing
- Easy to navigate and version-control
- Recommended for <10 loops

### Option B: Individual Files
Separate `.claude/plans/ralph-loop-NNN.md` + index:
- Better for large projects (10+ loops)
- Easier to modify specific loops
- Individual files map cleanly to git history

## After Planning

1. Use `/new-loop` command to save and update `CLAUDE.md` planning state
2. Use `/loop-status` to confirm the plan structure looks right
3. Use `/next-loop` to begin execution of the first loop

## See Also

- `ralph-loop-template.md` — Full schema with examples and best practices
- `todo-schema.md` — Canonical todo format and native TodoWrite sync rules
- `@phase-plan-creator` — Generate phase plans before loop decomposition
- `claude-md-convention.md` — CLAUDE.md Planning State section spec
