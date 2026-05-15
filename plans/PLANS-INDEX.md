# Plans Index

Tracking document for the **Advanced Planning System — Open-Source Restructure** programme.

---

## Master Plan

| File | Description |
|------|-------------|
| [`master-plan.md`](master-plan.md) | Programme overview: context, all 4 phases, cross-phase principles |

---

## Phases

| Phase | Name | File | Status | Loops | Outcome |
|-------|------|------|--------|-------|---------|
| 1 | Core Architecture Design | [`phase-1.md`](phase-1.md) | **complete** | 001–004 | Schemas, skills, agent roles, state bus |
| 2 | Claude Code Adapter | [`phase-2.md`](phase-2.md) | **complete** | 005–007 | Commands, agents, settings, end-to-end test |
| 3 | Cowork Adapter | [`phase-3.md`](phase-3.md) | **complete** | 008–009 | Routing skill, agent prompts, snapshot checkpoints |
| 4 | Generic + Release | [`phase-4.md`](phase-4.md) | **complete** | 010–012 | Python API, docs, examples, GitHub release |
| 5 | Gate Review Sub-Phase | [`phase-5.md`](phase-5.md) | **complete** | 013–018 | Gate agents, /run-gate, /next-phase, versioning utilities, plugin scaffold |
| 8 | Framework Consistency Remediation | [`phase-8.md`](phase-8.md) | **closing** | 027 | Loop 027 complete (hook + permissions hygiene). Loops 028–031 absorbed into Phase 9. |
| 9 | `.advanced-plans/` Restructure | [`phase-9.md`](phase-9.md) | **draft** | 032–036 | Migrate data home to `.advanced-plans/` for cross-platform portability; introduce `PLANNING.md` dashboard with YAML frontmatter; absorbs Phase 8 Loops 028–031. Design: [`2026-05-14-advanced-plans-restructure-design.md`](2026-05-14-advanced-plans-restructure-design.md) |

> **Index gap**: Phases 6 and 7 are complete (compacted artefacts in `plans/phase-completes/`) but missing from this table. Scheduled to be backfilled by Phase 9 Wave 5.

---

## Ralph Loops

| Loop | Phase | Name | File | Status | Active File | Attempt |
|------|-------|------|------|--------|-------------|---------|
| 001 | 1 | Schema Definitions | `phase-1-ralph-loops.md` | **complete** | — | 1 |
| 002 | 1 | Planning Skills (5) | `phase-1-ralph-loops.md` | **complete** | — | 1 |
| 003 | 1 | Agent Role Definitions | `phase-1-ralph-loops.md` | **complete** | — | 1 |
| 004 | 1 | State Bus Protocol | `phase-1-ralph-loops.md` | **complete** | — | 1 |
| 005 | 2 | Commands & Install | `phase-2-ralph-loops.md` | **complete** | — | 1 |
| 006 | 2 | Agents & Settings | `phase-2-ralph-loops.md` | **complete** | — | 1 |
| 007 | 2 | End-to-End Test | `phase-2-ralph-loops.md` | **complete** | — | 1 |
| 008 | 3 | Routing SKILL & Agent Integration | `phase-3-ralph-loops.md` | **complete** | — | 1 |
| 009 | 3 | Snapshot Checkpoints & Testing | `phase-3-ralph-loops.md` | **complete** | — | 1 |
| 010 | 4 | Python API | `phase-4-ralph-loops.md` | **complete** | — | 1 |
| 011 | 4 | Documentation & Examples | `phase-4-ralph-loops.md` | **complete** | — | 1 |
| 012 | 4 | Package & Release | `phase-4-ralph-loops.md` | **complete** | — | 1 |
| 013 | 5 | Gate State Schemas | `phase-5-ralph-loops.md` | **complete** | — | 1 |
| 014 | 5 | Gate Agent Definitions | `phase-5-ralph-loops.md` | **complete** | — | 1 |
| 015 | 5 | Invocation & Catalogue Updates | `phase-5-ralph-loops.md` | **complete** | — | 1 |
| 016 | 5 | Gate Commands | `phase-5-ralph-loops.md` | **complete** | — | 1 |
| 017 | 5 | Python Versioning Utilities | `phase-5-ralph-loops.md` | **complete** | — | 1 |
| 018 | 5 | Integration Verification | `phase-5-ralph-loops.md` | **complete** | — | 1 |
| 027 | 8 | Hook + Permissions Hygiene | `phase-8-ralph-loops.md` | **complete** | — | 1 |
| 028 | 8 | Sentinel Ownership Consolidation | `phase-8-ralph-loops.md` | absorbed → Phase 9 | — | — |
| 029 | 8 | progress-report Deduplication | `phase-8-ralph-loops.md` | absorbed → Phase 9 | — | — |
| 030 | 8 | Rename new-loop to decompose-phase | `phase-8-ralph-loops.md` | absorbed → Phase 9 | — | — |
| 031 | 8 | Disambiguation + Skill-Activation Policy | `phase-8-ralph-loops.md` | absorbed → Phase 9 | — | — |
| 032 | 9 | Skeleton + Preconditions | `phase-9-ralph-loops.md` | pending | — | 1 |
| 033 | 9 | File Migration | `phase-9-ralph-loops.md` | pending | — | 1 |
| 034 | 9 | Command Rewrites + Phase 8 Absorption | `phase-9-ralph-loops.md` | pending | — | 1 |
| 035 | 9 | Hooks + Permissions + Python + Install | `phase-9-ralph-loops.md` | pending | — | 1 |
| 036 | 9 | Docs + Tests + Backfill + Audit | `phase-9-ralph-loops.md` | pending | — | 1 |

> Loops 019–026 belong to Phases 6 and 7 (compacted) and are not yet enumerated here — see the index gap note above.

---

## Results / Decision Logs

| Phase | Results File | Status |
|-------|-------------|--------|
| 1 | `docs/decisions.md` (accumulated) | Not yet created |
| 2 | — | — |
| 3 | — | — |
| 4 | — | — |

---

## Workflow

```
/new-phase    → generates plans/phase-{N}.md
/new-loop     → decomposes into plans/phase-{N}-ralph-loops.md
/next-loop    → executes next pending loop
/loop-status  → shows progress (this document is the human-readable equivalent)
/run-gate     → spawns gate agents to review phase outputs; writes verdicts to plans/gate-verdicts/
/next-phase   → runs gate review then advances (pass) or creates versioned retry files (fail)
/run-closeout → spawns programme-reporter to synthesise the full programme narrative
```

**Version tracking**: On gate failure, `/next-phase` creates `phase-{N}-ralph-loops-v{attempt}.md`.
The `Active File` column above tracks which version is the current retry target. `Attempt` is 1 for
the original (no retry) and increments on each gate failure.

**Notes**:
- Loops 001 and 004 were completed during the initial architecture session.
- Loops 002 and 003 were completed in the subsequent execution session.
- Loops 005–007 (Phase 2) completed in one session.
- Loops 008–009 (Phase 3) completed in one session.
- Loops 013–018 (Phase 5) implement the Gate Review Sub-Phase.
