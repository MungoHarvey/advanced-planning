# Exploration Notes — Phase 15 Candidate: Automation-Surface Audit

## Exploration Focus

Pay down the recurring framework friction that `docs/tool-friction-log.md` repeatedly
defers to "the automation-surface audit phase", plus the loose Phase 14 "Opened" threads
and live documentation-hygiene defects. Determine which candidates are genuinely net-new
work versus already partially built, so the phase can be scoped to real gaps rather than
re-implementing existing capability.

Anchor: current HEAD (post phase-14 close). Target release: v0.15.0.

## Codebase Structure

- Slash commands (source): `platforms/claude-code/commands/` — 12 commands. No `sync-plans`.
- Python API: `platforms/python/` — 11 modules incl. `state_manager.py`, `plan_io.py`,
  `versioning.py`. Zero-dependency (stdlib only, enforced by `ast_check.py`).
- CI: `.github/workflows/ci.yml` — 3 jobs (md-lint non-blocking, JSON-schema validation of
  `core/state/*.json`, pytest 3.10–3.12 + AST zero-dep check). **No path-convention audit.**
- Path map: `docs/path-conventions.md` exists (canonical path reference).
- Skills (planning): `core/skills/plan-skill-identification/` etc.

## Key Findings — per-candidate triage

**Already implemented (capability exists):**
- *Stale state-file archiving* — `state_manager.archive_cross_phase_state()` (line 241) is
  built and tested (`test_orchestrator_state_cleanup.py`), and an `archive/` dir already holds
  phase-11/12/13 artefacts. **BUT it is not wired into `next-loop.md`** (grep for
  archive/stale/clear in the command body = nothing). Gap is *wiring*, not the function.
- *Missing-skill surfacing at PLAN layer* — `plan-skill-identification` already flags
  `MISSING: [description]` instead of silent `NA` (SKILL.md line 84). Planning layer is done.

**Partial / wiring-or-layer gap:**
- *Missing-skill preflight at EXECUTION layer* — the friction entry asked the *worker* to log
  missing skills to `execution.log` at run time. Plan layer handles it; worker preflight needs
  verifying/adding. (Needs a quick read of the worker agent def to confirm.)
- *Prerequisites guard (dirty-tree)* — `next-loop.md` Step 3a already has a mid-loop-death
  guard (loop-ready newer than loop-complete + dirty tree → pause). The friction ask is
  subtly different: refuse to run when the tree carries changes *unrelated* to loop execution.
  Related machinery exists; the "unrelated changes" discrimination does not.

**Genuinely net-new:**
- `/sync-plans` command — re-render downstream artefacts (phase plan, PLANS-INDEX) from the
  spec to kill spec→plan→index drift. No equivalent exists.
- `/next-loop --full` — one-pass loop population (stubs→todos→skills→agents) instead of four
  sequential skill invocations. No flag exists today.
- CI path-convention audit — assert no command/agent/doc file references a non-canonical path
  (`.claude/plans/`, doubled-prefix, flat-vs-per-phase gate-verdicts). Net-new CI job. This is
  the enforcement that would have caught the Phase 9 double-prefix corruption.
- Path-constants-not-inlined — refactor command files to reference a layout doc/constant
  rather than inlining literal paths in every step. Larger refactor; pairs with the CI audit.

**Phase 14 "Opened" threads:**
- Formal gate-override policy — written rule + (optional) schema/field for recording a
  gate-pass-with-dissent override. Precedent set in phase-14 history.jsonl; no policy doc.
- codex-cli output version-coupling — a guard/test that re-validates the run-gate codex
  capture path against codex-cli output shape (small, test-centric).

**Live documentation-hygiene defects (cheap, high-signal):**
- `PLANS-INDEX.md` loop rows **042–046 and 055–058 still read `**pending**`** though all are
  complete + gate-passed. The index's headline status is wrong.
- `master-plan.md` is **stale**: defines a 4-phase programme; 14 phases have run. Either
  refresh to reflect reality or explicitly mark it historical.

## Risks & Concerns

- **Scope sprawl** — this is 10 candidate items across 4 categories. Trying to land all in one
  phase risks a sprawling, hard-to-gate phase. Strong candidate for ruthless prioritisation at
  the review gate (recommend 4–6 loops max).
- **Dogfooding hazard** — changes to `next-loop.md` / state wiring alter the very machinery used
  to execute this phase's own loops. Sequence carefully: land + test command/state changes
  before relying on them mid-phase, or exercise in a worktree (per the phase-14 pattern).
- **Zero-dep constraint** — any new Python stays stdlib-only; CI enforces it.
- **LOCKED schemas** — `phase-complete`, `phase-manifest-entry`, `phase-handoff` schema docs are
  locked; the gate-override item must not silently mutate them (needs a logged decision if it
  touches `gate-verdict.schema.json`).
- **CI path-audit false positives** — some `.claude/` references are *correct* (installed-project
  layout). The audit must distinguish source-repo paths from installed-runtime paths, or it will
  flag legitimate references (this nuance is already noted in the friction log).

## Recommendations

1. **Split into two tiers and let the user prune at the review gate:**
   - **Tier A — quick hygiene + small wins (low risk, high signal):** fix PLANS-INDEX `pending`
     rows; resolve/refresh `master-plan.md`; wire `archive_cross_phase_state()` into
     `next-loop.md`; codex version-coupling guard. These are mostly wiring/doc + test.
   - **Tier B — net-new automation (higher value, higher risk):** `/sync-plans`, `/next-loop
     --full`, CI path-convention audit (+ optional path-constants refactor), formal
     gate-override policy.
2. **Suggested first cut (~5 loops):** (055-equivalent numbering continues at 059)
   - Loop 1: Doc-hygiene + drift fixes (PLANS-INDEX, master-plan) + wire state archiving.
   - Loop 2: CI path-convention audit (the highest-leverage guard; prevents a whole bug class).
   - Loop 3: `/sync-plans` command.
   - Loop 4: `/next-loop --full` one-pass population.
   - Loop 5: Gate-override policy doc + codex version-coupling guard + verification + v0.15.0.
3. **Defer** the path-constants refactor unless the user wants it — it's the largest item and
   the CI audit captures most of its safety value without the churn.
4. Treat `docs/tool-friction-log.md` open entries as the acceptance backlog: each closed item
   should be struck through with a resolution note (per the log's own convention).
