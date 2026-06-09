---
phase: 15
name: "Automation-Surface Audit"
status: draft
loops: [059, 060, 061, 062, 063]
design_spec: .advanced-plans/exploration-notes.md
anchor_sha: bd9de6a
target_release: v0.15.0
---

# Phase 15: Automation-Surface Audit

## Objective

Pay down the recurring framework friction that `docs/tool-friction-log.md` repeatedly defers to
"the automation-surface audit phase" — wiring up already-built-but-unconnected capability, adding
the net-new automation that removes manual seams (sync, one-pass loop population), and installing
the CI guard that prevents the path-corruption bug class — then close the loose Phase 14 threads
and fix the live documentation-hygiene defects.

## Scope

### Included
- **Doc-hygiene + drift fixes**: correct the stale `**pending**` loop-status rows in
  `PLANS-INDEX.md` (042–046, 055–058 are complete); resolve `master-plan.md` staleness (it
  defines a 4-phase programme; 14 have run) by refreshing it or explicitly marking it historical.
- **Wire state-archiving into the loop flow**: call the existing, tested
  `state_manager.archive_cross_phase_state()` from `next-loop.md` (and/or the orchestrator) so
  stale `loop-ready.json`/`loop-complete.json` from a prior phase are archived at the boundary
  rather than silently consumed.
- **CI path-convention audit** (highest-leverage guard): a CI job asserting no command/agent/doc
  file references a non-canonical path (`.claude/plans/`, doubled-prefix `\.advanced-\.advanced-`,
  flat-vs-per-phase gate-verdicts mismatch). Must distinguish source-repo paths from legitimate
  installed-runtime `.claude/` references to avoid false positives.
- **`/sync-plans` command**: re-render downstream artefacts (phase plan / PLANS-INDEX entry) from
  the design spec to kill spec→plan→index drift.
- **`/next-loop --full`**: one-pass loop population chaining stubs→todos→skills→agents instead of
  four sequential skill invocations.
- **Formal gate-override policy**: a written policy doc for recording a gate-pass-with-dissent
  override (the Phase 14 codex-dissent precedent), plus — only if needed — an optional,
  backward-compatible field on `gate-verdict.schema.json` (logged decision required).
- **codex-cli version-coupling guard**: a small test that re-validates the run-gate codex capture
  path against codex output shape, so a future codex-cli upgrade fails loudly rather than silently
  degrading.
- Version bump to v0.15.0 with CHANGELOG entry + CLAUDE.md decision-log entry.
- Strike-through + resolution note in `docs/tool-friction-log.md` for each entry this phase closes
  (per the log's own convention).

### Explicitly NOT included
- **Path-constants-not-inlined refactor** — the largest-churn item; the CI path audit captures
  most of its safety value without the repo-wide churn. Deferred to a later phase unless promoted.
- **Worker-layer missing-skill preflight** — the plan layer already emits `MISSING:`; the
  execution-log warning is low-signal and deferred unless it falls out trivially.
- **Re-implementing `archive_cross_phase_state()`** — it exists and is tested; this phase only
  wires it in.
- **Any change to `codex_gate.py` / `remediate.py` / `remediation_controller.py` logic** — beyond
  the established minimal-scoped-fix-if-blocking allowance.
- **A general installer (`setup/`) refactor** — its own phase.

## Key Deliverables

| Deliverable | Format | Location |
|---|---|---|
| Corrected loop-status rows | Markdown edit | `.advanced-plans/PLANS-INDEX.md` |
| Refreshed/marked master plan | Markdown | `.advanced-plans/master-plan.md` |
| State-archiving wired into loop flow | Markdown command edit | `platforms/claude-code/commands/next-loop.md` (+ `.claude/` runtime copy) |
| CI path-convention audit | Python + workflow job | `platforms/python/path_audit.py`, `.github/workflows/ci.yml` |
| Path-audit tests | Python (pytest) | `platforms/python/tests/test_path_audit.py` |
| `/sync-plans` command | Markdown command | `platforms/claude-code/commands/sync-plans.md` |
| `/next-loop --full` behaviour | Markdown command edit | `platforms/claude-code/commands/next-loop.md` |
| Gate-override policy | Markdown doc | `docs/gate-override-policy.md` |
| codex version-coupling guard | Python (pytest) | `platforms/python/tests/test_codex_gate_live.py` (extend) |
| v0.15.0 release | VERSION + CHANGELOG + decision log | `VERSION`, `CHANGELOG.md`, `CLAUDE.md` |

## Success Criteria

- ✓ `PLANS-INDEX.md` shows no completed loop with a `**pending**` status row; an audit/grep
  confirms zero false "pending" entries for gate-passed phases.
- ✓ `master-plan.md` either reflects the true phase count or carries an explicit "historical /
  superseded" header — no longer asserts a 4-phase programme as current.
- ✓ Running `/next-loop` across a (simulated) phase boundary archives the prior phase's stale
  state files to `.advanced-plans/state/archive/` instead of consuming them; covered by a test.
- ✓ The CI path-audit job passes on the current tree and **fails** on a planted non-canonical
  path (doubled-prefix or `.claude/plans/`), proving it would have caught the Phase 9 corruption;
  legitimate installed-runtime `.claude/` references do not trip it.
- ✓ `/sync-plans` re-renders the PLANS-INDEX entry (and phase-plan metadata) from a spec with no
  manual edit; demonstrated on a real phase.
- ✓ `/next-loop --full` populates a stub loop's todos, skills, and agents in a single invocation;
  output is equivalent to the four-step manual chain.
- ✓ `docs/gate-override-policy.md` exists and defines when/how a gate-pass-with-dissent override
  is permitted and recorded; if `gate-verdict.schema.json` changed, the change is
  backward-compatible and logged in CLAUDE.md.
- ✓ A codex version-coupling guard test exists that fails if the run-gate codex capture path no
  longer matches expected codex output shape.
- ✓ Full suite green (pytest 3.10–3.12), AST zero-dep check NONE, all LOCKED schema docs
  byte-unchanged, v0.15.0 cut.
- ✓ Every friction-log entry closed by this phase is struck through with a resolution note.

## Dependencies

### Must Complete Before
- Phase 14 closed (done): runtime command surface installed and proven, so edits to
  `next-loop.md` and CI build on a known-good baseline.

### Blocked By
- (none external)

### Optional
- Path-constants refactor: would make the CI audit's job smaller, but is deferred.

## Skills Required (Broad Categories)
- `command-rewriting` / file-sync: editing slash-command bodies and keeping `.claude/` runtime
  copies byte-consistent with source.
- `verification-before-completion`: tests + CI proof + the planted-corruption negative test are
  the heart of the phase.
- `schema-design`: only if the gate-override item touches `gate-verdict.schema.json`.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Scope sprawl (10 candidates) | Med | High | Pruned to 5 loops; path-constants + worker-preflight explicitly deferred |
| Dogfooding hazard — editing `next-loop.md`/state wiring while using it to run this phase | Med | High | Land + test command/state changes in early loops; exercise risky changes in a throwaway worktree (Phase 14 pattern); never rely on an unproven edit mid-phase |
| CI path-audit false positives on legitimate `.claude/` refs | Med | Med | Audit distinguishes source-repo vs installed-runtime paths; negative + positive test cases both required |
| Gate-override schema churn breaks existing verdicts | Low | High | Keep any field additive/optional; validate existing verdicts still parse; log decision |
| codex guard couples tests to a specific codex-cli version | Med | Low | Guard asserts the *capture contract*, not an exact version string; documents the coupling |

## Assumptions
- `archive_cross_phase_state()` behaves as its tests assert and only needs wiring — validated by
  reading `state_manager.py:241` and `test_orchestrator_state_cleanup.py`.
- The CI runner has `git` + the repo checked out (path-audit greps tracked files).
- Zero-dependency rule holds: `path_audit.py` uses stdlib only (`pathlib`, `re`, `sys`).

## Notes / Design Decisions
- Source-of-truth for scope is `.advanced-plans/exploration-notes.md` (the /plan-and-phase
  exploration output) rather than a brainstorming spec — this phase is friction-paydown, not a
  greenfield design.
- Loop ordering puts low-risk hygiene + the CI guard first so the safety net exists before the
  net-new command automation lands.

## Ralph Loops (5)

| Loop | Name | Type | Key Outputs |
|------|------|------|-------------|
| 059 | Doc-Hygiene + Wire State-Archiving | Implementation | PLANS-INDEX fix, master-plan resolution, archive wiring + test |
| 060 | CI Path-Convention Audit | Implementation | `path_audit.py`, CI job, positive+negative tests |
| 061 | /sync-plans Command | Implementation | `sync-plans.md` + runtime copy, drift-kill demo |
| 062 | /next-loop --full One-Pass Population | Implementation | `--full` flag behaviour, equivalence to 4-step chain |
| 063 | Gate-Override Policy + codex Guard + Release | Implementation | policy doc, codex version guard, friction-log closeouts, v0.15.0 |
