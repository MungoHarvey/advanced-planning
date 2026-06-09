---
phase: 14
name: "Install & Exercise Codex Gate + Self-Heal in Runtime"
status: draft
loops: [055, 056, 057, 058]
design_spec: .advanced-plans/specs/2026-06-09-phase-14-install-exercise-codex-self-heal-design.md
anchor_sha: 9465e55
target_release: v0.14.0
---

# Phase 14: Install & Exercise Codex Gate + Self-Heal in Runtime

## Objective

Wire the Phase 12 codex gate and Phase 13 self-heal — both built and tested in source but never
installed — into this repo's project `.claude/` runtime, then prove both work via automated tests
**and** a witnessed live exercise, closing the recursion so the framework checks, builds, and
corrects itself.

## Scope

### Included
- Refresh the two stale runtime command bodies (`.claude/commands/run-gate.md`,
  `.claude/commands/next-phase.md`) from their `platforms/claude-code/commands/` sources
  (plain `cp` — byte-identical).
- Copy `core/agents/codex-reviewer.md` → `.claude/agents/` for parity, and verify the path the
  refreshed run-gate references (`core/agents/codex-reviewer.md`) resolves in-repo.
- Automated proof of the codex gate: a real `codex` stdout fixture →
  `codex_gate.extract_and_validate` schema-valid verdict + the graceful-degrade path.
- Automated proof of the self-heal: a sandboxed synthetic-fail integration test driving
  `remediation_controller` triage → allowlist-breach escalation.
- A witnessed live self-heal exercise: a deliberately-induced gate fail on a throwaway git
  **worktree**, watched remediating + re-gating live, captured, then discarded so `main` is
  never touched.
- A guaranteed live codex run: Phase 14's own gate review writes a `backend: codex` verdict.
- A `CONTRIBUTING.md` drift note documenting that runtime command copies are not symlinked and
  the command to re-sync them from source.
- Version bump to v0.14.0 with CHANGELOG entry + CLAUDE.md decision-log entry.

### Explicitly NOT included
- **Refreshing user-level `~/.claude/commands/`** — affects every project on the machine, not
  just this repo; out of scope. (F1 confirmed the project copies are the live target.)
- **Any change to `codex_gate.py` / `remediate.py` / `remediation_controller.py` logic** — this
  phase installs and exercises existing tested code. Blocking bugs found during the exercise get
  a minimal scoped fix and are logged; non-blocking ones are recorded for a later phase.
- **A `platforms/claude-code/agents/codex-reviewer.md` duplicate** — F2 confirmed run-gate
  resolves the `core/agents/` path directly; a duplicate would only risk divergence.
- **New gate features** (structured `findings[].location`, `passed_after_remediation`
  enforcement) — remain the Phase 13 deferred list.
- **A general installer (`setup/`) refactor** — its own phase.

## Key Deliverables

| Deliverable | Format | Location |
|---|---|---|
| Refreshed run-gate command | Copy from source | `.claude/commands/run-gate.md` |
| Refreshed next-phase command | Copy from source | `.claude/commands/next-phase.md` |
| Installed codex-reviewer (parity copy) | Copy | `.claude/agents/codex-reviewer.md` |
| Codex gate live test + fixture | Python (pytest) | `platforms/python/tests/test_codex_gate_live.py` |
| Self-heal sandbox integration test | Python (pytest) | `platforms/python/tests/` |
| Witnessed exercise evidence | Transcript + history events | loop handoff + `.advanced-plans/state/history.jsonl` |
| Runtime drift note | Markdown | `CONTRIBUTING.md` |
| Version + changelog + decision log | Text + Markdown | `VERSION`, `CHANGELOG.md`, `CLAUDE.md` |

## Success Criteria

- ✓ `.claude/commands/run-gate.md` is byte-identical to
  `platforms/claude-code/commands/run-gate.md` (codex refs > 0); `.claude/commands/next-phase.md`
  byte-identical to its source (remediation refs > 0).
- ✓ `.claude/agents/codex-reviewer.md` present; the `core/agents/codex-reviewer.md` path the
  refreshed run-gate references resolves from the repo root.
- ✓ `test_codex_gate_live.py` passes: a real codex stdout fixture parses via
  `extract_and_validate` into a schema-valid verdict; AND the degrade path is asserted
  (codex unavailable → in-house agents proceed, `gate_codex_skipped` appended, no `codex.json`).
- ✓ A sandboxed self-heal integration test passes: synthetic gate fail → `remediation_controller`
  triage → a diff-allowlist breach escalates rather than commits.
- ✓ `python -m platforms.python.remediate` and the controller import/run cleanly from repo root
  (the runtime command invocation path).
- ✓ Witnessed live self-heal: a deliberately-induced gate fail in a git worktree runs the bounded
  remediation loop (≤2 cycles), emits `gate_remediation` / `passed_after_remediation` events, is
  captured, and the worktree is discarded leaving `main` clean (`git status` + `git worktree list`
  verified).
- ✓ Phase-level codex live run: Phase 14's own gate-verdicts include a `backend: codex` verdict
  for `phase-14-attempt-1`.
- ✓ `CONTRIBUTING.md` documents the runtime-drift mechanism (commands copied not symlinked) and
  the re-sync command.
- ✓ `VERSION` is `0.14.0`; `CHANGELOG.md` has a `[0.14.0]` section; `CLAUDE.md` has a Phase 14
  decision-log entry; tag deferred to gate pass.
- ✓ All tests pass (no regression; new tests added); AST zero-dep NONE; LOCKED files byte-unchanged
  (`docs/phase-complete.schema.md`, `docs/phase-manifest-entry.schema.md`,
  `docs/phase-handoff.schema.md`, `.advanced-plans/phases/phase-9/complete.md`).

## Dependencies

### Must Complete Before
- **Phase 13 gate pass**: complete (PASSED attempt 1; v0.13.0). Self-heal code is in place, 300 tests.
- **Phase 12 codex work**: complete (`codex_gate.py`, `core/agents/codex-reviewer.md`, verdict
  `backend` field).

### Blocked By
- None external. `codex-cli 0.124.0` is on PATH.

### Optional
- A fuller installer refactor would make future runtime refreshes one command; the manual
  `cp` + CONTRIBUTING note is sufficient for v1.

## Skills Required (Broad Categories)

- `command-rewriting` / file-sync: faithful refresh of the runtime command bodies.
- `verification-before-completion`: the tests + preflight + witnessed exercise are the heart of
  this phase — evidence over assertion.
- `schema-design`: confirming codex verdicts validate against `gate-verdict.schema.json`.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Induced-fail exercise mutates `main` | Med | High | Runs in a discarded git worktree; never commits to main; post-exercise `git status`/`worktree list` check |
| Refreshed 20 KB command body has runtime issues never caught in document review | Med | Med | Loops 056/057 smoke-test every `python -m platforms.python.*` call; loop 058 is the first real execution, isolated |
| Codex CLI output drifts from `codex_gate` expectations | Med | Med | Validate against a real run; built-in degrade path is the safety net |
| Runtime silently drifts from source again | High | Med | CONTRIBUTING drift-note + byte-identity gate criterion |
| Worktree exercise leaves orphaned state | Low | Med | Explicit discard step + status verification in the loop |

## Assumptions

- `Project .claude/commands/ is the executed runtime` (F1): confirmed by content-fingerprint —
  the `/run-gate` that ran this session carried markers unique to the project copy.
- `codex-reviewer needs no packaging` (F2): confirmed — run-gate references the `core/agents/`
  path directly and never spawns it as an Agent; the path exists in-repo.
- `The source command bodies are correct as written` (passed Phase 12/13 gates as documents):
  this phase installs them; loop 058's live run is the first runtime validation.
- `A gate fail can be induced in isolation`: the controller keys off `history.jsonl` gate_fail
  events + verdict files, both stageable inside a worktree.

## Notes / Design Decisions

- Two-track proof strategy (from the approved spec): prove each mechanism in isolation with
  repeatable tests, then prove end-to-end by running for real. Codex gate gets a guaranteed live
  run (Phase 14's own gate); self-heal gets a deliberately-induced, reverted worktree run.
- F1 and F2 were resolved empirically during the adversarial review — they are recorded as
  assumptions with their evidence, not re-litigated as loop work.
- The witnessed self-heal fail is *contrived on purpose* and isolated in a worktree precisely so
  the framework can observe its own correction loop without risking the live tree.
- v0.14.0 follows the minor-version-per-phase convention even though no shipped library logic
  changes — the runtime install + tests are the deliverable.
- This is the recursion the Phase 13 plan anticipated ("once installed, this loop will exercise
  its own self-heal on a future gate fail") made real.

## Ralph Loops (4)

| Loop | Name | Type | Key Outputs |
|---|---|---|---|
| 055 | Runtime Install | Implementation | `.claude/commands/{run-gate,next-phase}.md` refreshed byte-identical from source; `core/agents/codex-reviewer.md` copied to `.claude/agents/`; path resolution + codex/remediation refs verified; CONTRIBUTING.md drift note (commands copied not symlinked → re-sync command) |
| 056 | Codex Gate Proof | Verification | Real codex stdout fixture; `test_codex_gate_live.py` (extract/validate → schema-valid verdict + degrade path: `gate_codex_skipped`, no `codex.json`); codex preflight smoke (`codex --version`/auth) |
| 057 | Self-Heal Proof | Verification | Sandboxed synthetic-fail integration test (triage → diff-allowlist-breach escalation); runtime reachability smoke for `remediate` / `remediation_controller` from repo root |
| 058 | Witnessed Exercise + v0.14.0 Release | Verification + Release | Worktree-isolated induced gate fail → live remediation + re-gate captured (transcript + `gate_remediation`/`passed_after_remediation` events) → worktree discarded, `main` clean; VERSION 0.14.0 + CHANGELOG `[0.14.0]` + CLAUDE.md Phase 14 decision-log entry; full pytest + AST NONE; LOCKED files byte-unchanged; tag deferred to gate pass |
