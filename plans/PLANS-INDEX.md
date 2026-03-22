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
| 5 | Gate Review Sub-Phase | [`phase-5-ralph-loops.md`](phase-5-ralph-loops.md) | **in_progress** | 013–018 | Gate agents, /run-gate, /next-phase, versioning utilities |

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
| 018 | 5 | Integration Verification | `phase-5-ralph-loops.md` | **in_progress** | `phase-5-ralph-loops.md` | 1 |

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
