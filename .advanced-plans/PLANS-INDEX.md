# Plans Index

Tracking document for the **Advanced Planning System — Open-Source Restructure** programme.

---

## Master Plan

| File | Description |
|------|-------------|
| [`master-plan.md`](master-plan.md) | Programme overview: context, all phases, cross-phase principles |

---

## Phases

| Phase | Name | File | Status | Loops | Outcome |
|-------|------|------|--------|-------|---------|
| 1 | Core Architecture Design | [`phase-1/plan.md`](phases/phase-1/plan.md) | **complete** | 001–004 | Schemas, skills, agent roles, state bus |
| 2 | Claude Code Adapter | [`phase-2/plan.md`](phases/phase-2/plan.md) | **complete** | 005–007 | Commands, agents, settings, end-to-end test |
| 3 | Cowork Adapter | [`phase-3/plan.md`](phases/phase-3/plan.md) | **complete** | 008–009 | Routing skill, agent prompts, snapshot checkpoints |
| 4 | Generic + Release | [`phase-4/plan.md`](phases/phase-4/plan.md) | **complete** | 010–012 | Python API, docs, examples, GitHub release |
| 5 | Gate Review Sub-Phase | [`phase-5/plan.md`](phases/phase-5/plan.md) | **complete** | 013–018 | Gate agents, /run-gate, /next-phase, versioning utilities, plugin scaffold |
| 6 | Compaction Schema Audit & Lock | [`phase-6/complete.md`](phases/phase-6/complete.md) | **complete** | 019–022 | Cold/hot compaction schemas locked; verdict format audit; phase-5 worked example |
| 7 | `/phase-compact` Slash Command | [`phase-7/`](phases/phase-7/) | **complete** | 023–026 | Verdict schema extended; /phase-compact implemented; phase-6 compacted end-to-end; agent template documented |
| 8 | Framework Consistency Remediation | [`phase-8/plan.md`](phases/phase-8/plan.md) | **complete** | 027 | Loop 027 complete (hook + permissions hygiene). Loops 028–031 absorbed into Phase 9. |
| 9 | `.advanced-plans/` Restructure | [`phase-9/complete.md`](phases/phase-9/complete.md) | **complete** | 032–036 | Migrate data home to `.advanced-plans/` for cross-platform portability; introduce `PLANNING.md` dashboard with YAML frontmatter; absorbs Phase 8 Loops 028–031. Design: [`2026-05-14-advanced-plans-restructure-design.md`](specs/2026-05-14-advanced-plans-restructure-design.md). Gate PASSED attempt 2. |
| 10 | /phase-compact Context-Compaction Reframe | [`phase-10/plan.md`](phases/phase-10/plan.md) | **draft** | 037–041 | Reframe /phase-compact from terse-artefact writer to conversation-context compaction (Approach A): per-phase handoff.md resume digest + unchanged LOCKED complete.md; context_meter transparency report; CLAUDE.md ## Compaction Instructions; PreCompact freshness hook; AskUserQuestion consent/handoff. Design: [`2026-05-19-phase-compact-context-compaction-design.md`](specs/2026-05-19-phase-compact-context-compaction-design.md). |

---

## Phase Compaction Manifest

Hot manifest entries written by `/phase-compact` at gate pass (locked schema:
`docs/phase-manifest-entry.schema.md`). Phases 6/7 were compacted before this
section existed — their cold artefacts exist but manifest entries are not yet backfilled.

- phase: 9
  title: ".advanced-plans/ Restructure"
  status: passed
  commits: ecdfca4..19199d3
  detail: .advanced-plans/phases/phase-9/complete.md
  highlights:
    - Data home migrated to .advanced-plans/; all 12 success criteria met (verdict attempt-2 PASS)
    - PLANNING.md YAML dashboard introduced for cold-start orientation

---

## Ralph Loops

| Loop | Phase | Name | File | Status | Active File | Attempt |
|------|-------|------|------|--------|-------------|---------|
| 001 | 1 | Schema Definitions | `phases/phase-1/loops.md` | **complete** | — | 1 |
| 002 | 1 | Planning Skills (5) | `phases/phase-1/loops.md` | **complete** | — | 1 |
| 003 | 1 | Agent Role Definitions | `phases/phase-1/loops.md` | **complete** | — | 1 |
| 004 | 1 | State Bus Protocol | `phases/phase-1/loops.md` | **complete** | — | 1 |
| 005 | 2 | Commands & Install | `phases/phase-2/loops.md` | **complete** | — | 1 |
| 006 | 2 | Agents & Settings | `phases/phase-2/loops.md` | **complete** | — | 1 |
| 007 | 2 | End-to-End Test | `phases/phase-2/loops.md` | **complete** | — | 1 |
| 008 | 3 | Routing SKILL & Agent Integration | `phases/phase-3/loops.md` | **complete** | — | 1 |
| 009 | 3 | Snapshot Checkpoints & Testing | `phases/phase-3/loops.md` | **complete** | — | 1 |
| 010 | 4 | Python API | `phases/phase-4/loops.md` | **complete** | — | 1 |
| 011 | 4 | Documentation & Examples | `phases/phase-4/loops.md` | **complete** | — | 1 |
| 012 | 4 | Package & Release | `phases/phase-4/loops.md` | **complete** | — | 1 |
| 013 | 5 | Gate State Schemas | `phases/phase-5/loops.md` | **complete** | — | 1 |
| 014 | 5 | Gate Agent Definitions | `phases/phase-5/loops.md` | **complete** | — | 1 |
| 015 | 5 | Invocation & Catalogue Updates | `phases/phase-5/loops.md` | **complete** | — | 1 |
| 016 | 5 | Gate Commands | `phases/phase-5/loops.md` | **complete** | — | 1 |
| 017 | 5 | Python Versioning Utilities | `phases/phase-5/loops.md` | **complete** | — | 1 |
| 018 | 5 | Integration Verification | `phases/phase-5/loops.md` | **complete** | — | 1 |
| 019 | 6 | Verdict Format Audit & Gap Analysis | `phases/phase-6/loops.md` | **complete** | — | 1 |
| 020 | 6 | Cold & Hot Schemas Drafted | `phases/phase-6/loops.md` | **complete** | — | 1 |
| 021 | 6 | Phase-5 Retrospective Worked Example | `phases/phase-6/loops.md` | **complete** | — | 1 |
| 022 | 6 | Schemas Locked | `phases/phase-6/loops.md` | **complete** | — | 1 |
| 023 | 7 | Verdict Schema Extended + Agent Permission Fix | `phases/phase-7/loops.md` | **complete** | — | 1 |
| 024 | 7 | /phase-compact Slash Command | `phases/phase-7/loops.md` | **complete** | — | 1 |
| 025 | 7 | Phase-6 Compacted End-to-End | `phases/phase-7/loops.md` | **complete** | — | 1 |
| 026 | 7 | Agent Template Documented | `phases/phase-7/loops.md` | **complete** | — | 1 |
| 027 | 8 | Hook + Permissions Hygiene | `phases/phase-8/loops.md` | **complete** | — | 1 |
| 028 | 8 | Sentinel Ownership Consolidation | `phases/phase-8/loops.md` | absorbed → Phase 9 | — | — |
| 029 | 8 | progress-report Deduplication | `phases/phase-8/loops.md` | absorbed → Phase 9 | — | — |
| 030 | 8 | Rename new-loop to decompose-phase | `phases/phase-8/loops.md` | absorbed → Phase 9 | — | — |
| 031 | 8 | Disambiguation + Skill-Activation Policy | `phases/phase-8/loops.md` | absorbed → Phase 9 | — | — |
| 032 | 9 | Skeleton + Preconditions | `phases/phase-9/loops.md` | **complete** | — | 1 |
| 033 | 9 | File Migration | `phases/phase-9/loops.md` | **complete** | — | 1 |
| 034 | 9 | Command Rewrites + Phase 8 Absorption | `phases/phase-9/loops.md` | **complete** | — | 1 |
| 035 | 9 | Hooks + Permissions + Python + Install | `phases/phase-9/loops.md` | **complete** | — | 1 |
| 036 | 9 | Docs + Tests + Backfill + Audit | `phases/phase-9/loops.md` | **complete** | — | 1 |

---

## Results / Decision Logs

| Phase | Results File | Status |
|-------|-------------|--------|
| 1 | `docs/decisions.md` (accumulated) | Not yet created |

---

## Workflow

```
/new-phase        → generates .advanced-plans/phases/phase-{N}/plan.md
/decompose-phase  → decomposes into .advanced-plans/phases/phase-{N}/loops.md
/next-loop        → executes next pending loop
/loop-status      → live snapshot of pending/in-progress todos
/progress-report  → historical synthesis across loops/phases
/run-gate         → spawns gate agents; writes verdicts to .advanced-plans/gate-verdicts/
/next-phase       → runs gate review then advances (pass) or creates versioned retry files (fail)
/run-closeout     → spawns programme-reporter to synthesise the full programme narrative
```

**Version tracking**: On gate failure, `/next-phase` creates
`.advanced-plans/phases/phase-{N}/loops-v{attempt}.md`. The `Active File`
column above tracks which version is the current retry target. `Attempt` is 1
for the original (no retry) and increments on each gate failure.

**Notes**:
- Loops 001 and 004 were completed during the initial architecture session.
- Loops 002 and 003 were completed in the subsequent execution session.
- Loops 005–007 (Phase 2) completed in one session.
- Loops 008–009 (Phase 3) completed in one session.
- Loops 013–018 (Phase 5) implement the Gate Review Sub-Phase.
- Loops 019–022 (Phase 6) and 023–026 (Phase 7) were compacted; see
  `phases/phase-6/complete.md` and the Phase 7 gate verdicts.
- Phase 9 (Loops 032–036) migrated all planning data to `.advanced-plans/`.
