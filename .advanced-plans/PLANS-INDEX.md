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
| 10 | /phase-compact Context-Compaction Reframe | [`phase-10/plan.md`](phases/phase-10/plan.md) | **complete** | 037–041 | Reframe /phase-compact from terse-artefact writer to conversation-context compaction (Approach A): per-phase handoff.md resume digest + unchanged LOCKED complete.md; context_meter transparency report; CLAUDE.md ## Compaction Instructions; PreCompact freshness hook; AskUserQuestion consent/handoff. Gate PASSED attempt 1 (both agents). Design: [`2026-05-19-phase-compact-context-compaction-design.md`](specs/2026-05-19-phase-compact-context-compaction-design.md). |
| 11 | Friction Remediation & v0.x Pre-Release | [`phase-11/plan.md`](phases/phase-11/plan.md) | **complete** | 042–046 | Resolve 9 highest-impact tool-friction-log entries + bootstrap version scheme. Gate PASSED attempt 1 (code-review 95, phase-goals 93). Tag `v0.11.0` cut + pushed; GitHub Release published as pre-release. Key finding: S5 phase-goals-agent Write tool propagation confirmed upstream-blocked at runtime; FALLBACK contingency in run-gate.md is the supported workaround. Design: [`2026-05-20-phase-11-friction-remediation-design.md`](specs/2026-05-20-phase-11-friction-remediation-design.md). |
| 12 | Codex Cross-Model Second-Opinion Gate Reviewer | [`phase-12/plan.md`](phases/phase-12/plan.md) | **complete** | 047–050 | Add OpenAI Codex as an independent cross-model second opinion on the phase-goals gate check (augment mode: gate = AND of all; degrades to today's two-agent gate when Codex absent). "B+" approach: tested zero-dep `codex_gate.py` (extract/validate/aggregate) + portable `core/agents/codex-reviewer.md` contract + run-gate parallel-independent wiring. Office-hours design + /plan-eng-review CLEARED. Gate PASSED attempt 1 (code-review 95, phase-goals 95); v0.12.0 staged. Design: [`2026-06-08-phase-12-codex-gate-reviewer-design.md`](specs/2026-06-08-phase-12-codex-gate-reviewer-design.md). |
| 13 | Self-Correcting Gate (Gate-Remediation Loop) | [`phase-13/complete.md`](phases/phase-13/complete.md) | **complete** | 051–054 | Turn the gate-fail dead-end into a bounded, guard-railed self-heal under `/next-phase --auto`: triage findings (structural→re-run loop, localized→focused fix), remediate, re-gate with fresh blind agents, bounded 2 cycles then escalate. Safety spine (anti gate-gaming): diff allowlist + frozen criteria + full criteria_outcomes; git-state policy; composition rules. Brainstorming + /plan-eng-review CLEARED + /codex guardrails folded in. Gate PASSED attempt 1 (both agents); v0.13.0. Post-gate fix: criteria_outcomes array parsing (300 tests). Design: [`2026-06-08-self-correcting-gate-design.md`](specs/2026-06-08-self-correcting-gate-design.md). |
| 14 | Install & Exercise Codex Gate + Self-Heal in Runtime | [`phase-14/plan.md`](phases/phase-14/plan.md) | **complete** | 055–058 | Wire the Phase 12 codex gate + Phase 13 self-heal (both built in source, never installed) into this repo's project `.claude/` runtime, then prove both via a two-track strategy: automated tests (codex extract/validate + degrade; sandboxed self-heal triage→escalation) AND a witnessed live exercise (codex fires on Phase 14's own gate; self-heal via a deliberately-induced, worktree-isolated, reverted gate fail). Refresh stale command bodies (run-gate 0→codex, next-phase 0→remediation); copy codex-reviewer to `.claude/agents/` for parity (no `platforms/` duplicate — run-gate resolves the `core/agents/` path in-repo); CONTRIBUTING drift note. Adversarial review resolved F1 (project `.claude/` is the live target) + F2 (no codex-reviewer packaging) empirically. Brainstorming + design spec approved. Target v0.14.0. Design: [`2026-06-09-phase-14-install-exercise-codex-self-heal-design.md`](specs/2026-06-09-phase-14-install-exercise-codex-self-heal-design.md). |
| 15 | Automation-Surface Audit | [`phase-15/plan.md`](phases/phase-15/plan.md) | **complete** | 059–063 | Friction paydown from the tool-friction-log backlog: state-archiving wired into `/next-loop` Step 3a; CI path-convention audit (`path_audit.py` + job 4, catches the Phase-9 corruption class); `/sync-plans` command; `/next-loop --full` one-pass stub population; formal gate-override policy + codex version-coupling guard. Gate PASSED attempt 1 (code-review 95, phase-goals 93); 366 tests. Follow-on: `/run-gate` closes the phase out on a current-phase pass (gate→close seam removed). Released v0.15.0. Scope source: [`exploration-notes.md`](exploration-notes.md) + friction log. |
| 16 | Trust the Machinery | [`phase-16/plan.md`](phases/phase-16/plan.md) | **draft** | 064–068 | Make the framework's execution surfaces trustworthy and cheap, from the 2026-06-09 retro's six gaps: install-layer sync + drift guard (`install_audit.py` + `/sync-install` — the upgrade pathway for all consuming projects); history.jsonl event coverage (`history_log.py` + wiring); worker-contract guards moved into agent definitions; conditional orchestrator fast-path for populated loops; checkpoint tags + execution.log untracked; compaction backfill ×9 + auto-compact at gate-close. Target v0.16.0. Design: [`2026-06-10-phase-16-trust-the-machinery-design.md`](specs/2026-06-10-phase-16-trust-the-machinery-design.md). |

---

## Phase Compaction Manifest

Hot manifest entries written by `/phase-compact` at gate pass (locked schema:
`docs/phase-manifest-entry.schema.md`). All phases 1–15 are now backfilled.

- phase: 1
  title: "Core Architecture Design"
  status: passed
  commits: 5ec7168..5ec7168
  detail: .advanced-plans/phases/phase-1/complete.md
  highlights:
    - Schemas, skills, agent roles, and state bus delivered in initial release commit
    - Targeted skill injection protocol formalised in core/agents/worker.md

- phase: 2
  title: "Claude Code Adapter"
  status: passed
  commits: 5ec7168..08b15ac
  detail: .advanced-plans/phases/phase-2/complete.md
  highlights:
    - Six slash commands, three agents, settings.json hooks, install.sh/install.ps1
    - Global skill fallback and Windows PowerShell installer added post-initial-release

- phase: 3
  title: "Cowork Adapter"
  status: passed
  commits: 5ec7168..5ec7168
  detail: .advanced-plans/phases/phase-3/complete.md
  highlights:
    - Routing SKILL.md + orchestrator/worker prompts + checkpoint.sh delivered
    - Zero .claude/ references; snapshot-based checkpointing replaces git commits

- phase: 4
  title: "Generic Adapter, Documentation & Release"
  status: passed
  commits: 5ec7168..698ef1a
  detail: .advanced-plans/phases/phase-4/complete.md
  highlights:
    - Python API (state_manager, plan_io, handoff) + full docs suite + CI workflow
    - MIT licence, CONTRIBUTING, portability scan clean; complexity field added

- phase: 5
  title: "Gate Review Sub-Phase & Invocation Improvements"
  status: passed
  commits: 2214691..9e1aef4
  detail: .advanced-plans/phases/phase-5/complete.md
  highlights:
    - Gate review machinery built: verdict schemas, 5 gate agents, /run-gate + /next-phase + versioning.py (70/70 tests)
    - Pre-gate-review phase (sentinel verdict form); plugin packaging deferred to phase 7

- phase: 6
  title: "Compaction Schema Audit & Lock"
  status: passed
  commits: 84a0e86..724e7d6
  detail: .advanced-plans/phases/phase-6/complete.md
  highlights:
    - phase-complete.schema.md + phase-manifest-entry.schema.md locked (LOCKED 2026-05-13)
    - phase-5-complete.md produced as worked example; anchor SHA mechanism decided

- phase: 7
  title: "/phase-compact Slash Command"
  status: passed
  commits: 72cd5f3..be24cb7
  detail: .advanced-plans/phases/phase-7/complete.md
  highlights:
    - /phase-compact command + verdict schema (criteria_outcomes, phase_title) implemented
    - Phase 6 compacted end-to-end; PLANS-INDEX.md Phase Completions section established

- phase: 8
  title: "Framework Consistency Remediation"
  status: passed
  commits: fdf96cb..05e5626
  detail: .advanced-plans/phases/phase-8/complete.md
  highlights:
    - Loop 027: planning-mode hook allowlist + phase-goals-agent tool cleanup + settings.json
    - Loops 028-031 absorbed into Phase 9 (.advanced-plans/ restructure)

- phase: 9
  title: ".advanced-plans/ Restructure"
  status: passed
  commits: ecdfca4..19199d3
  detail: .advanced-plans/phases/phase-9/complete.md
  highlights:
    - Data home migrated to .advanced-plans/; all 12 success criteria met (verdict attempt-2 PASS)
    - PLANNING.md YAML dashboard introduced for cold-start orientation

- phase: 10
  title: "/phase-compact Context-Compaction Reframe"
  status: passed
  commits: 6384f80..e881997
  detail: .advanced-plans/phases/phase-10/complete.md
  highlights:
    - /phase-compact reframed to write handoff.md digest + transparency report (attempt-1 PASS)
    - PreCompact hook + CLAUDE.md ## Compaction Instructions + AskUserQuestion consent gate

- phase: 11
  title: "Friction Remediation & v0.x Pre-Release"
  status: passed
  commits: 1bb073c..dc94b1b
  detail: .advanced-plans/phases/phase-11/complete.md
  highlights:
    - 9 friction items resolved; AST zero-dep checker + path-conventions.md (attempt-1 PASS, 189 tests)
    - v0.11.0 released; dogfood self-install verified; IRON-RULE resume-detection regression test

- phase: 12
  title: "Codex Cross-Model Second-Opinion Gate Reviewer"
  status: passed
  commits: fa799d3..68ab217
  detail: .advanced-plans/phases/phase-12/complete.md
  highlights:
    - codex_gate.py (extract/validate/aggregate) + run-gate parallel Codex wiring (attempt-1 PASS)
    - Degrade path: gate proceeds with two in-house agents when Codex absent

- phase: 13
  title: "Self-Correcting Gate (Gate-Remediation Loop)"
  status: passed
  commits: 7936b34..f988a71
  detail: .advanced-plans/phases/phase-13/complete.md
  highlights:
    - Bounded triage→safety→fix→re-gate self-heal in /next-phase --auto; all 11 criteria met (attempt-1 PASS)
    - Anti-gate-gaming safety spine: diff allowlist + frozen-criteria hash + full criteria_outcomes

- phase: 14
  title: "Install & Exercise Codex Gate + Self-Heal in Runtime"
  status: passed
  commits: 9465e55..d4aefc4
  detail: .advanced-plans/phases/phase-14/complete.md
  highlights:
    - Codex gate + self-heal installed to runtime; proven via 343 tests + witnessed worktree self-heal (attempt-1 PASS, override)
    - Framework gated itself: real backend:codex verdict written; first live run fixed 4 run-gate codex-invocation bugs

- phase: 15
  title: "Automation-Surface Audit"
  status: passed
  commits: bd9de6a..36efe6e
  detail: .advanced-plans/phases/phase-15/complete.md
  highlights:
    - Friction paydown: state-archiving wired, CI path-audit guard, /sync-plans, /next-loop --full (gate PASS attempt 1, 366 tests)
    - /run-gate now closes the phase out on pass (gate->close seam removed); gate-override policy formalised

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
| 037 | 10 | Context Meter Extension | `phases/phase-10/loops.md` | **complete** | — | 1 |
| 038 | 10 | Handoff Digest Schema + Generation | `phases/phase-10/loops.md` | **complete** | — | 1 |
| 039 | 10 | Command Reframe | `phases/phase-10/loops.md` | **complete** | — | 1 |
| 040 | 10 | PreCompact Hook + CLAUDE.md Policy | `phases/phase-10/loops.md` | **complete** | — | 1 |
| 041 | 10 | Verification + End-to-End | `phases/phase-10/loops.md` | **complete** | — | 1 |
| 042 | 11 | Constraints + Schema Cleanup | `phases/phase-11/loops.md` | **complete** | — | 1 |
| 043 | 11 | Skills + Agents | `phases/phase-11/loops.md` | **complete** | — | 1 |
| 044 | 11 | Migration Audit + Durability | `phases/phase-11/loops.md` | **complete** | — | 1 |
| 045 | 11 | Dogfood Self-Install | `phases/phase-11/loops.md` | **complete** | — | 1 |
| 046 | 11 | Verification + v0.11.0 Release | `phases/phase-11/loops.md` | **complete** | — | 1 |
| 047 | 12 | Schema + Tested Gate Core | `phases/phase-12/loops.md` | **complete** | — | 1 |
| 048 | 12 | Codex Reviewer Contract | `phases/phase-12/loops.md` | **complete** | — | 1 |
| 049 | 12 | run-gate Wiring (Parallel + Conflict UX) | `phases/phase-12/loops.md` | **complete** | — | 1 |
| 050 | 12 | Verification + v0.12.0 Release | `phases/phase-12/loops.md` | **complete** | — | 1 |
| 051 | 13 | Triage Core + Channel Move | `phases/phase-13/loops.md` | **complete** | — | 1 |
| 052 | 13 | Gate Isolation Contract | `phases/phase-13/loops.md` | **complete** | — | 1 |
| 053 | 13 | Remediation Controller | `phases/phase-13/loops.md` | **complete** | — | 1 |
| 054 | 13 | Verification + v0.13.0 Release | `phases/phase-13/loops.md` | **complete** | — | 1 |
| 055 | 14 | Runtime Install | `phases/phase-14/loops.md` | **complete** | — | 1 |
| 056 | 14 | Codex Gate Proof | `phases/phase-14/loops.md` | **complete** | — | 1 |
| 057 | 14 | Self-Heal Proof | `phases/phase-14/loops.md` | **complete** | — | 1 |
| 058 | 14 | Witnessed Exercise + v0.14.0 Release | `phases/phase-14/loops.md` | **complete** | — | 1 |
| 059 | 15 | Doc-Hygiene + Wire State-Archiving | `phases/phase-15/loops.md` | **complete** | — | 1 |
| 060 | 15 | CI Path-Convention Audit | `phases/phase-15/loops.md` | **complete** | — | 1 |
| 061 | 15 | /sync-plans Command | `phases/phase-15/loops.md` | **complete** | — | 1 |
| 062 | 15 | /next-loop --full One-Pass Population | `phases/phase-15/loops.md` | **complete** | — | 1 |
| 063 | 15 | Gate-Override Policy + codex Guard + Release | `phases/phase-15/loops.md` | **complete** | — | 1 |
| 064 | 16 | Install-Sync + Drift Guard | `phases/phase-16/loops.md` | **pending** | — | 1 |
| 065 | 16 | Trustworthy Record | `phases/phase-16/loops.md` | **pending** | — | 1 |
| 066 | 16 | Loop-Flow Economy | `phases/phase-16/loops.md` | **pending** | — | 1 |
| 067 | 16 | Compaction Backfill x9 | `phases/phase-16/loops.md` | **pending** | — | 1 |
| 068 | 16 | Auto-Compact at Close + Release | `phases/phase-16/loops.md` | **pending** | — | 1 |

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
