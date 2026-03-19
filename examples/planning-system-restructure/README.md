# Worked Example: Planning System Restructure

This directory is a worked example of the Advanced Planning System applied to itself. The planning system was designed and built using the planning system — a deliberate self-dogfooding exercise to validate the architecture before open-source release.

---

## What This Example Shows

A focused, 4-phase technical project with clear deliverables and bounded scope. The programme ran for approximately 12 ralph loops across 4 phases.

**The programme**: Restructure an existing planning system prototype into a clean, open-source release with a platform-agnostic core, three platform adapters (Claude Code, Cowork, Python), and a full documentation suite.

**What makes this a good example to study**:
- Real deliverables (not toy examples)
- Multiple phases with genuine dependencies between them
- Mix of implementation loops (write code) and writing loops (write documentation)
- Evidence of mid-programme adaptation (schema iteration as the handoff format matured)
- Self-referential: the plan files in `plans/` were the active working documents throughout

---

## How to Navigate the Plan Files

The plan files for this programme live in `plans/` at the repository root (not in this `examples/` directory — the plans were the live working documents, not copies).

```
plans/
├── PLANS-INDEX.md              ← start here — master tracker
├── master-plan.md              ← programme overview and cross-phase principles
├── phase-1.md                  ← Phase 1 strategic plan (Core Architecture)
├── phase-1-ralph-loops.md      ← Loop specs 001–004 with YAML frontmatter
├── phase-2.md                  ← Phase 2 strategic plan (Claude Code Adapter)
├── phase-2-ralph-loops.md      ← Loop specs 005–007
├── phase-3.md                  ← Phase 3 strategic plan (Cowork Adapter)
├── phase-3-ralph-loops.md      ← Loop specs 008–009
├── phase-4.md                  ← Phase 4 strategic plan (Generic + Release)
└── phase-4-ralph-loops.md      ← Loop specs 010–012
```

**Start with `PLANS-INDEX.md`** — it shows the full loop sequence, phase statuses, and progress at a glance.

**Then read a ralph loop file**, such as `phase-1-ralph-loops.md`. Each loop is a YAML frontmatter block with:
- `name`, `task_name`, `max_iterations`, `on_max_iterations`
- `handoff_summary` — the three-sentence summary written after completion
- `todos[]` — the tasks executed within the loop, each with `id`, `content`, `skill`, `agent`, `outcome`, and `status`

---

## Patterns to Look For

### 1. Handoff summaries as a programme narrative

Read the `handoff_summary.done` fields in sequence across all loops. Together they form a readable narrative of the programme's progress — what was built, in what order, and what was passed forward.

Example from loop 009:
```yaml
handoff_summary:
  done: "Phase 3 complete: checkpoint.sh, README.md, and full verification passed."
  failed: ""
  needed: "Begin Phase 4 — Generic + Release (loops 010-012)."
```

### 2. Skill assignment per todo

In each loop's `todos[]`, notice the `skill:` field. Where `skill: NA`, the worker executed with general capability. Where a specific skill is named (e.g. `skill: skill-creator`), the worker loaded that skill's `SKILL.md` immediately before execution and unloaded it after.

### 3. Loop scoping decisions

Compare the `## Overview` section (narrative scope) with the `todos[]` count. Well-scoped loops have 3–6 todos. Loops with more than 8 todos often indicate scope creep — the orchestrator's population step should have flagged this and proposed splitting.

### 4. The portability constraint

In Phase 3 (Cowork adapter) and Phase 4 (generic adapter), notice the repeated verification step: scanning for `.claude/` paths in adapter files. This reflects a real constraint discovered in the architecture — platform adapters must not embed platform-internal paths in what should be portable files. The constraint was codified as a loop outcome and verified before marking each loop complete.

### 5. Schema migration mid-programme

Between Phase 1 and Phase 2, the `handoff` field schema changed from v7 (three fields: `done`/`failed`/`next`) to v8 (three fields: `done`/`failed`/`needed`). The `needed` field replaced `next` to be more clearly action-oriented. This migration is documented in `docs/decisions.md` and visible in the template files created in loop 002.

---

## Key Files to Read

| File | Why It's Interesting |
|------|---------------------|
| `plans/PLANS-INDEX.md` | The master tracker — shows loop sequence and phase status |
| `plans/phase-1-ralph-loops.md` | The most technically diverse loops (schemas, skills, agents, state) |
| `plans/phase-3-ralph-loops.md` | Shows the Cowork adapter design decisions in todo form |
| `core/agents/worker.md` | The targeted skill injection protocol in its canonical form |
| `platforms/cowork/agents/worker-prompt.md` | The same protocol rewritten as a self-contained Agent tool prompt |
| `docs/decisions.md` | Eight architectural decisions with rationale |

---

## What Wasn't Captured

The plan files show the *what* and *when*, not the full *why* of every micro-decision. The reasoning behind specific wording choices, edge cases considered, and alternatives rejected during execution are in `docs/decisions.md` for the architectural decisions, but the operational decisions (why a particular todo was phrased this way, why a skill was assigned here but not there) are not systematically recorded.

This is intentional: the planning system is not a full audit log. It is a coordination mechanism. The decisions worth preserving are the architectural ones; the execution micro-decisions belong in code comments and commit messages.
