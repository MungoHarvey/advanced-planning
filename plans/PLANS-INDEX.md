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

---

## Ralph Loops

| Loop | Phase | Name | File | Status |
|------|-------|------|------|--------|
| 001 | 1 | Schema Definitions | `phase-1-ralph-loops.md` | **complete** |
| 002 | 1 | Planning Skills (5) | `phase-1-ralph-loops.md` | **complete** |
| 003 | 1 | Agent Role Definitions | `phase-1-ralph-loops.md` | **complete** |
| 004 | 1 | State Bus Protocol | `phase-1-ralph-loops.md` | **complete** |
| 005 | 2 | Commands & Install | `phase-2-ralph-loops.md` | **complete** |
| 006 | 2 | Agents & Settings | `phase-2-ralph-loops.md` | **complete** |
| 007 | 2 | End-to-End Test | `phase-2-ralph-loops.md` | **complete** |
| 008 | 3 | Routing SKILL & Agent Integration | `phase-3-ralph-loops.md` | **complete** |
| 009 | 3 | Snapshot Checkpoints & Testing | `phase-3-ralph-loops.md` | **complete** |
| 010 | 4 | Python API | `phase-4-ralph-loops.md` | **complete** |
| 011 | 4 | Documentation & Examples | `phase-4-ralph-loops.md` | **complete** |
| 012 | 4 | Package & Release | `phase-4-ralph-loops.md` | **complete** |

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
/new-phase  → generates plans/phase-{N}.md
/new-loop   → decomposes into plans/phase-{N}-ralph-loops.md
/next-loop  → executes next pending loop
/loop-status → shows progress (this document is the human-readable equivalent)
```

**Programme complete.** All 12 loops delivered across 4 phases. Repository ready for open-source release — see `docs/release-checklist.md` for pre-publication steps.

**Notes**:
- Loops 001 and 004 were completed during the initial architecture session.
- Loops 002 and 003 were completed in the subsequent execution session.
- Loops 005–007 (Phase 2) completed in one session.
- Loops 008–009 (Phase 3) completed in one session.
