---
phase: 13
name: "Self-Correcting Gate (Gate-Remediation Loop)"
status: complete
loops: [051, 052, 053, 054]
design_spec: .advanced-plans/specs/2026-06-08-self-correcting-gate-design.md
anchor_sha: 7936b34
target_release: v0.13.0
---

# Phase 13: Self-Correcting Gate (Gate-Remediation Loop)

## Objective

Turn the gate-fail dead-end into a bounded, guard-railed self-heal so that under
`/next-phase --auto` the pipeline remediates the specific findings and re-gates with fresh,
blind agents, without ever being able to weaken the target to force a pass.

## Scope

### Included
- A zero-dependency, tested `platforms/python/remediate.py` with
  `triage_findings(verdict) -> {structural, localized, unfixable}` (keys on
  `severity=="critical"`; routes `loops_to_revert`→structural, critical findings with an
  actionable file/line→localized, otherwise→unfixable).
- Retarget `inject_failure_context` (`versioning.py`) from `loops.md` frontmatter to a
  worker-only sidecar `.advanced-plans/phases/phase-N/retry-context.json`; update
  `gate-failure-context.schema.json` wording.
- Isolation rule in `core/agents/gate-reviewer.md` (inherited by the CC gate agents):
  never read `retry-context.*` / `gate-verdicts/` / prior verdicts; evaluate the frozen
  criteria and emit `criteria_outcomes` for ALL criteria.
- The remediation controller in `/next-phase --auto`: bounded triage→safety→fix→re-gate
  loop with the **Remediation Safety** spine (diff allowlist, frozen criteria,
  full-criteria_outcomes enforcement), **Git-State Policy** (staged allowlist, transient
  exclusion, pre-remediation snapshot, dirty-tree preflight), **Composition Rules**
  (`--force`/`--skip-gate` skip, loop-fail STOP, contradictory-findings escalate,
  `passed_after_remediation` flag), cycle count from `history.jsonl` `gate_fail` events,
  sentinel sequencing, and new `gate_remediation` / `passed_after_remediation` events.
- Version bump to v0.13.0 with CHANGELOG entry.

### Explicitly NOT included
- **Gating `--auto` advance on `passed_after_remediation`** — v1 records the flag;
  enforcement (requiring human sign-off before building on a repaired phase) is a follow-on.
- **Structured `findings[].location` (file/line/loop) or per-finding confidence** in the
  verdict schema — triage works on the freeform `location` string + `severity` for v1;
  structured locations (better triage precision) are a separate schema evolution.
- **Cross-phase remediation** — a fail in phase N never reaches into phase N-1.
- **Fixing the latent Phase-12 attempt-count bug** beyond what this phase needs — the
  cycle counter here uses `history.jsonl` events, sidestepping it; repairing
  `attempt = verdict_count/agent_count` globally is a separate fix.
- **New top-level command** — reuses `/next-phase --auto`.

## Key Deliverables

| Deliverable | Format | Location |
|---|---|---|
| Triage helper (zero-dep, tested) | Python | `platforms/python/remediate.py` |
| Triage tests | Python (pytest) | `platforms/python/tests/test_remediate.py` |
| Failure-context channel retarget | Edit | `platforms/python/versioning.py` |
| Versioning tests (retarget regression) | Edit | `platforms/python/tests/test_versioning.py` |
| Failure-context schema wording | Edit | `core/state/gate-failure-context.schema.json` |
| Gate isolation rule | Edit | `core/agents/gate-reviewer.md` |
| Remediation controller | Edit | `platforms/claude-code/commands/next-phase.md` |
| Version + changelog | Text + Markdown | `VERSION`, `CHANGELOG.md` |
| Phase 13 decision-log entry | Markdown | `CLAUDE.md` |

## Success Criteria

- ✓ `platforms/python/remediate.py` defines `triage_findings` returning
  `{structural, localized, unfixable}`, keying on `severity=="critical"`; routes
  `loops_to_revert`→structural, critical+file/line→localized, else→unfixable; ignores
  warning/info; `python -m platforms.python.ast_check platforms/python/remediate.py` is NONE.
- ✓ `test_remediate.py` covers: structural, localized, unfixable, warning/info-ignored,
  empty verdict, multi-agent union, contradictory-location conflict; pytest passes.
- ✓ `inject_failure_context` writes `.advanced-plans/phases/phase-N/retry-context.json` and
  NO LONGER writes `gate_failure_context` into `loops.md` frontmatter; `test_versioning.py`
  asserts both (CRITICAL regression); `gate-failure-context.schema.json` describes the sidecar.
- ✓ `core/agents/gate-reviewer.md` states the isolation rule (no read of `retry-context.*`/
  `gate-verdicts/`/prior verdicts; evaluate frozen criteria; emit `criteria_outcomes` for
  ALL criteria); CC gate agents inherit it (no per-agent duplication).
- ✓ `/next-phase --auto` gate-fail branch: cycle count from `history.jsonl` `gate_fail`
  events; bound 2 → versioned-retry+STOP from the pre-remediation snapshot.
- ✓ **Remediation Safety enforced** (documented in next-phase.md + covered by controller
  predicate/trace tests): diff allowlist rejection → escalate; `criteria-frozen.md` written
  before cycle 1 and hash-checked before each re-gate; re-gate verdict missing any criterion
  → escalate.
- ✓ **Git-State Policy enforced**: remediation commit stages only allowlisted source (no
  `git add -A`); no-change detection excludes transient files; pre-remediation SHA recorded;
  dirty-tree preflight escalates.
- ✓ **Composition Rules**: `--force`/`--skip-gate` skip remediation; a failing re-run loop
  hits the loop-fail STOP; contradictory findings escalate with a `remediation_conflict`
  note; `passed_after_remediation` recorded on a repaired pass.
- ✓ Without `--auto`, gate-fail behavior is byte-for-byte today's behavior (regression trace).
- ✓ `VERSION` is `0.13.0`; `CHANGELOG.md` has a `[0.13.0]` section; `CLAUDE.md` has a
  Phase 13 decision-log entry; tag deferred to gate pass.
- ✓ All pre-existing tests pass; AST zero-dep NONE; LOCKED files byte-unchanged
  (`docs/phase-complete.schema.md`, `docs/phase-manifest-entry.schema.md`,
  `docs/phase-handoff.schema.md`, `.advanced-plans/phases/phase-9/complete.md`).

## Dependencies

### Must Complete Before
- **Phase 12 gate pass**: complete (PASSED attempt 1; v0.12.0 staged). The codex gate work
  this builds on (verdict `backend` field, `codex_gate.py`) is in place.
- **Approved, doubly-reviewed design**: `.advanced-plans/specs/2026-06-08-self-correcting-gate-design.md`
  (brainstorming + /plan-eng-review CLEARED + /codex guardrails folded in).

### Blocked By
- None external.

### Optional
- Phase 12's run-gate codex wiring being installed to `.claude/` would let the new
  remediation loop compose with codex verdicts live; not required (works on subagent verdicts).

## Skills Required (Broad Categories)

- `python`: `remediate.py` + tests, `versioning.py` retarget preserving zero-dep.
- `schema-design`: the `gate-failure-context.schema.json` wording + the isolation-rule contract.
- `command-rewriting`: the `/next-phase` controller (the bounded loop + safety/git/composition).
- `verification-before-completion`: the controller trace/predicate tests + release gate.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Remediation games the gate** (edits criteria/tests to force a pass) | Med | High | Diff allowlist + frozen criteria + full-criteria_outcomes enforcement (the safety spine); controller aborts on out-of-bounds diff |
| Sentinel left up during remediation blocks every fix (exit 2) | Med | High | Controller asserts sentinel absent before any fix; sentinel brackets gates only |
| `git add -A` commits transient/unrelated state into a fix | Med | Med | Staged allowlist; transient-file exclusion; dirty-tree preflight |
| Cycle miscount (attempt division fragile under codex degrade) | Med | Med | Count `history.jsonl` `gate_fail` events instead of verdict-file division |
| Bad fix baked into escalation baseline | Med | Med | Versioned retry built from pre-remediation snapshot; bad-fix tree preserved on a ref |
| Controller logic untestable (markdown) | High | Med | Risky logic (triage) in tested `remediate.py`; controller covered by predicate + trace tests |
| Contradictory findings produce thrashing edits | Low | Med | Conflict detection → escalate, no guessing |

## Assumptions

- `The verdict findings/loops_to_revert fields are sufficient for triage`: confirmed by review
  — triage keys on `severity` + `loops_to_revert` + freeform `location`; no finding→loop
  inference needed.
- `Re-gate agents will honor the isolation rule + full-criteria_outcomes requirement`:
  enforced structurally (controller rejects verdicts missing criteria) not just by instruction.
- `analysis-worker can perform focused source edits given findings`: it has Read/Edit/Write/
  Bash/Glob; validated at Loop 053.
- `history.jsonl gate_fail events are a reliable cycle counter`: they are append-only and
  written by the gate path; robust against variable verdict counts.

## Notes / Design Decisions

- Reviewed twice: `/plan-eng-review` resolved 4 mechanical issues (scope 10→7 files, sentinel
  sequencing, history-based cycle counter, two-input triage); `/codex` caught the adversarial
  gap (gate-gaming) and added the diff-allowlist + frozen-criteria + full-criteria_outcomes
  safety spine, git-state policy, and composition rules. All folded into the spec.
- The core insight: **blind to the failure context, not blind to the contract.** Re-gate
  agents don't see why it failed, but must verify every original criterion.
- v0.13.0 follows the minor-version-per-phase convention.
- Once installed, this loop will exercise its own self-heal on a future gate fail — the
  recursion completing: a pipeline that checks, builds, and corrects.

## Ralph Loops (4)

| Loop | Name | Type | Key Outputs |
|---|---|---|---|
| 051 | Triage Core + Channel Move | Implementation | `remediate.py` (triage_findings) + tests; `inject_failure_context` retarget to sidecar + test regression; gate-failure-context.schema.json wording; AST NONE |
| 052 | Gate Isolation Contract | Implementation | `core/agents/gate-reviewer.md` isolation rule (blind to failure context, frozen criteria, full criteria_outcomes); inherited by CC agents; core-purity verified |
| 053 | Remediation Controller | Implementation | `/next-phase --auto` gate-fail branch: bounded triage→safety→fix→re-gate loop; diff allowlist; frozen-criteria write+hash; full-criteria_outcomes enforcement; git-state policy; composition rules; sentinel sequencing; gate_remediation / passed_after_remediation events; controller predicate/trace tests |
| 054 | Verification + v0.13.0 Release | Verification + Release | E2E trace of fix→re-gate→pass and bound→escalate; gate-gaming-attempt blocked by allowlist (test); without-`--auto` regression; gstack-coupling grep; VERSION 0.13.0 + CHANGELOG + CLAUDE.md decision log; full pytest + AST NONE; LOCKED files unchanged; tag deferred to gate pass |
