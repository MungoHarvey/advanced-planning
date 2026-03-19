# Planning System: Master Guide

Hierarchical planning architecture for sustained, accurate multi-step execution in Claude Code.

```
Phase Plan → Ralph Loops → TODOs → Execution → Handoff → Next Loop
```

---

## The Problem This Solves

Long Claude Code sessions fail not from lack of capability, but from:
- **Context drift** — earlier instructions deprioritised as context grows
- **Unverifiable progress** — tasks marked done on effort, not outcome
- **No resumption path** — session restart means losing state entirely
- **Scope creep** — boundaries blur without explicit in/out scope

This system addresses all four.

---

## Installation

This package can be used in two ways.

### Option A — Install into a project

Copies commands, skills, and agents into a project's `.claude/` directory,
making slash commands available in that project only.

```bash
cd /path/to/your/project
/path/to/advanced-planning/install.sh
```

### Option B — Install commands globally

Makes `/next-loop`, `/new-phase`, `/new-loop`, and `/loop-status` available
across **all** Claude Code projects. Skills and agents still install per-project.

```bash
/path/to/advanced-planning/install.sh --global
# Then, inside each project that uses planning:
/path/to/advanced-planning/install.sh --project /path/to/project
```

### Option C — Skill mode (no install)

Reference the whole package as a single skill via `@advanced-planning`. Claude reads
the routing SKILL.md and dispatches to sub-skills and commands on demand. No files
are copied to the project — useful for one-off planning sessions.

---

## Architecture Overview

### Package structure

```
advanced-planning/          ← this package
├── install.sh              ← installer (see above)
├── SKILL.md                ← routing skill for skill-mode use
├── README.md               ← this file
├── skills/
│   ├── phase-plan-creator/ ← phase plan generation
│   │   ├── SKILL.md
│   │   └── references/phase-plan-template.md
│   └── ralph-loop-planner/ ← loop decomposition
│       ├── SKILL.md
│       └── references/
│           ├── ralph-loop-template.md
│           └── todo-schema.md
├── commands/
│   ├── new-phase.md        ← /new-phase [description]
│   ├── new-loop.md         ← /new-loop
│   ├── next-loop.md        ← /next-loop
│   └── loop-status.md      ← /loop-status
├── agents/
│   ├── README.md
│   ├── loop-orchestrator.md ← Sonnet: coordinates loop execution
│   └── analysis-worker.md   ← Haiku: runs bounded computational tasks
└── references/
    └── claude-md-convention.md ← CLAUDE.md Planning State spec
```

### What gets installed into a project

```
.claude/
├── CLAUDE.md                          ← add Planning State section (see references/)
├── plans/                             ← created empty, ready for phase plans
├── skills/
│   ├── phase-plan-creator/
│   │   ├── SKILL.md
│   │   └── references/phase-plan-template.md
│   └── ralph-loop-planner/
│       ├── SKILL.md
│       └── references/
│           ├── ralph-loop-template.md
│           └── todo-schema.md
├── commands/
│   ├── new-phase.md                   ← /new-phase [description]
│   ├── new-loop.md                    ← /new-loop
│   ├── next-loop.md                   ← /next-loop
│   └── loop-status.md                 ← /loop-status
└── agents/
    ├── loop-orchestrator.md
    └── analysis-worker.md
```

---

## Workflow

### Step 1 — Create Phase Plan
```
/new-phase Phase 2: DESeq2 differential expression pipeline for DRUGseq compounds
```
Triggers `@phase-plan-creator`. Saves to `.claude/plans/phase-2.md`. Updates CLAUDE.md.

### Step 2 — Decompose into Loops
```
/new-loop
```
Triggers `@ralph-loop-planner` with the active phase plan. Saves loops to `.claude/plans/phase-2-ralph-loops.md`. Updates CLAUDE.md with first loop as current.

### Step 3 — Check Status
```
/loop-status
```
Shows current loop, todo progress, last handoff, and what's next.

### Step 4 — Execute
```
/next-loop
```
Reads CLAUDE.md, loads current loop, injects last handoff, syncs todos to TodoWrite sidebar,
takes a git checkpoint, and begins execution.

### Step 5 — Repeat
At loop completion, handoff is written to frontmatter and CLAUDE.md is updated.
Next session: `/loop-status` to orient, `/next-loop` to continue.

---

## Key Concepts

### Handoff (Continuity Across Sessions)
Three-field block written at **loop completion**:
```yaml
handoff:
  done: "what was completed"
  failed: "what failed and why, or NA"
  next: "exact action to resume from"
```
Injected into the next loop's prompt. Keeps context clean — no need to drag the full
prior session forward.

### Outcome-Driven TODOs
Every todo has an `outcome` field answering: *what must be true for this to be done?*
```yaml
outcome: "data/normalised.rds exists; dim() matches input; no NA values"
```
Agents verify the outcome before marking completed. Not done on effort.

### Two-Layer Todo Tracking
- **Frontmatter YAML** — authoritative, extended schema (`skill`, `agent`, `outcome`)
- **Native TodoWrite** — session sidebar visibility, subset schema (`id`, `content+outcome`, `status`, `priority`)

### Git Checkpoints
Every loop: `git commit` before starting, `git commit` on completion.
Rollback points if a loop corrupts state; audit trail of what each loop produced.

### CLAUDE.md as Persistent Anchor
`## Planning State` section survives session restarts. Tells Claude exactly where the
project is — current phase, loop, status, and last handoff — without scanning plan files.

---

## Schema Quick Reference

### Frontmatter Todo Fields (canonical order)
```yaml
- id: loop-NNN-N
  content: ""
  skill: ""       # skill-name or NA
  agent: ""       # agent-id or NA
  outcome: ""     # concrete done criteria
  status: pending # pending | in_progress | completed | cancelled
```

### Native TodoWrite Fields
```json
{ "id": "", "content": "[task] → [outcome]", "status": "pending", "priority": "high" }
```

### Ralph Loop Frontmatter Fields
```yaml
name: "ralph-loop-NNN"
task_name: ""
max_iterations: 3
on_max_iterations: escalate    # escalate | checkpoint | rollback
handoff: { done: "", failed: "", next: "" }
todos: [...]
prompt: |
  ...
```

---

## Recovery Reference

| `on_max_iterations` | When to use | Behaviour |
|---|---|---|
| `escalate` | Code, infra | Stop, write partial handoff, surface to human |
| `checkpoint` | Research, data | Commit state, write handoff, pause for human |
| `rollback` | Infrastructure | `git reset` to pre-loop checkpoint |

---

## Tips

**One todo in_progress at a time.** Claude Code's system prompt enforces this. Your schema should too.

**Outcomes, not intentions.** If you can't write a verifiable outcome, the todo is too vague.

**Handoffs are written, not improvised.** At loop end, always write the handoff block before committing. The next session depends on it.

**Skill discovery is normal.** If you find you need a skill not in the phase plan, add it to `Discovered` and note why. Don't force tasks into skills they don't fit.

**CLAUDE.md is cheap to write, expensive to ignore.** Updating it takes 30 seconds. Reconstructing state after a context reset takes much longer.
