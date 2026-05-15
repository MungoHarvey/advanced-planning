---
phase: 8
name: Framework Consistency Remediation
status: draft
source_spec: plans/2026-05-13-framework-consistency-audit-remediation.md
date: 2026-05-13
revised: 2026-05-13 (post-brainstorming)
---

# Phase 8: Framework Consistency Remediation

## Objective

Consolidate overlapping skills, commands, and processes identified in the 2026-05-13
consistency audit so each step in the workflow works together seamlessly, **without
altering the workflow itself**. Eliminate silently-blocked write paths, dual sentinel
ownership, duplicated names, and skill-activation ambiguity. Defer the always-dispatch
worker redesign to Phase 9.

## Scope

### Included

- Path-allowlist fix for the planning-mode PreToolUse hook
  (`settings.json`, `hooks.json`, CLAUDE.md cross-reference).
- Drop the cosmetic `Write(plans/gate-verdicts/*)` scope on `phase-goals-agent`;
  rely on the gate-review-mode hook for containment.
- Repo-root `.claude/settings.json` with permissive `allow` rules for routine
  `plans/**`, `.claude/state/**`, `.claude/logs/**` edits.
- Consolidate `gate-review-mode` sentinel ownership in `run-gate`; remove sentinel
  management from `next-phase`.
- Deduplicate the `progress-report` skill ↔ command pair (command invokes skill).
- Rename the `new-loop` command to `decompose-phase` with a tombstone redirect
  and a rename-log entry in `PLANS-INDEX.md`.
- Add disambiguation headers to `new-phase.md` and `plan-and-phase.md`.
- Document the two-stage skill-activation pipeline in CLAUDE.md
  (description-trigger keywords inform planning; frontmatter `skill:` field is the
  only execution-time source).
- Verify `new-phase` command invokes `phase-plan-creator` skill rather than
  re-implementing it.

### Explicitly NOT included

- Worker redesign as always-dispatcher (deferred to Phase 9 for separate scoping).
- Changes to the `agent:` field schema or semantics (linked to Phase 9).
- Changes to the state-bus protocol (`loop-ready.json`, `loop-complete.json`,
  `history.jsonl`).
- Changes to model-tier routing.
- Changes to locked schemas (`docs/phase-complete.schema.md`,
  `docs/phase-manifest-entry.schema.md`).
- New commands, skills, or agents.
- Edits to historical phase plans or phase-complete artefacts (forward-looking
  surface only).

## Key Deliverables

| Deliverable | Format | Location |
|-------------|--------|----------|
| Patched PreToolUse allowlist (planning-mode) | JSON edits | `platforms/claude-code/settings.json`, `platforms/claude-code/hooks/hooks.json` |
| `phase-goals-agent` frontmatter cleanup | Markdown frontmatter | `platforms/claude-code/agents/phase-goals-agent.md` |
| Repo-root permission settings | New JSON file | `.claude/settings.json` (checked-in; NOT settings.local.json) |
| Sentinel-ownership refactor | Markdown command edits | `platforms/claude-code/commands/next-phase.md`, `run-gate.md` |
| `progress-report` deduplication | Markdown command rewrite | `platforms/claude-code/commands/progress-report.md` |
| `new-loop` → `decompose-phase` rename | File rename + tombstone + ref sweep | `platforms/claude-code/commands/`, `CLAUDE.md`, `docs/`, `plans/PLANS-INDEX.md` |
| Command disambiguation headers | Markdown edits | `platforms/claude-code/commands/new-phase.md`, `plan-and-phase.md` |
| Two-stage skill-activation policy | Markdown documentation | `CLAUDE.md`, `core/skills/plan-skill-identification/SKILL.md` |
| `new-phase` ↔ `phase-plan-creator` wrapper verification | Markdown edit or no-op | `platforms/claude-code/commands/new-phase.md` |
| Updated index entry | Markdown table row | `plans/PLANS-INDEX.md` |

## Success Criteria

- ✓ Planning-mode hook allows writes to `plans/`, `.claude/plans/`, and
  `.claude/state/`; blocks all other paths when sentinel is present. Verified by
  manual smoke test.
- ✓ `phase-goals-agent` frontmatter declares `tools: Read, Glob, Grep, Write` with no
  parenthetical scope.
- ✓ Repo-root `.claude/settings.json` exists with permissive allow rules scoped to
  `plans/**`, `.claude/state/**`, `.claude/logs/**`. Routine status-flip edits no
  longer prompt for permission in this repo.
- ✓ `next-phase.md` contains no `gate-review-mode` sentinel writes or removes;
  `run-gate.md` remains the sole sentinel manager. Early-exit from `next-phase` after
  `run-gate` leaves no stale sentinel.
- ✓ Exactly one definition of `progress-report` is reachable from the user surface;
  command invokes skill rather than duplicating logic.
- ✓ No forward-looking file contains the literal string `new-loop` as a command
  reference. Renamed command is documented in CLAUDE.md alongside `next-loop` with a
  one-line disambiguation. Tombstone `new-loop.md` redirects users to
  `/decompose-phase`. `plans/PLANS-INDEX.md` records the rename.
- ✓ `new-phase.md` and `plan-and-phase.md` each open with a one-sentence
  disambiguation line. `new-phase` command body invokes `phase-plan-creator` skill
  without re-implementing it.
- ✓ CLAUDE.md documents the two-stage skill-activation pipeline in one paragraph
  with a concrete example. `core/skills/plan-skill-identification/SKILL.md`
  references its planner-stage consumer role explicitly.
- ✓ `python -m pytest platforms/python/tests/ -v` passes.
- ✓ All `core/state/*.json` files parse as valid JSON.
- ✓ `plans/PLANS-INDEX.md` lists Phase 8 with status and loop range.

## Dependencies

### Must Complete Before

- Phase 7 gate pass (already complete per recent commits).

### Blocked By

- None. All open questions from the original draft are resolved.

### Optional

- A regression test that asserts sentinel-cleanup invariants. Covered loosely by the
  Wave 2 smoke-test step; could be promoted to a dedicated test if scope expands.

## Skills Required (Broad Categories)

- `code-editing`: Direct edits to JSON, markdown, frontmatter.
- `cross-reference-sweep`: Grep-and-replace across docs, plans, READMEs for the
  Wave 4 rename.
- `frontmatter-schema`: Maintaining canonical YAML field order in agent and skill
  files.
- `hook-and-permissions`: Understanding PreToolUse semantics, path glob matching,
  and Claude Code permission allow rules.
- `gate-review-workflow`: Following the existing gate-review protocol for verification.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Rename sweep misses references in historical phase plans | Med | Low | Limit sweep to forward-looking surface; add tombstone command + PLANS-INDEX.md rename log + CLAUDE.md disambiguation line |
| Sentinel refactor regresses gate-review write protection | Low | High | Add explicit smoke test that sentinel exists during `run-gate`'s agent-spawn step; verify with `--phase N` dry run |
| Repo-root permission rules too permissive | Low | Med | Scope rules explicitly to `plans/**`, `.claude/state/**`, `.claude/logs/**` — no repo-wide globs |
| Two-stage skill-activation confuses readers | Low | Low | One paragraph in CLAUDE.md with a concrete worked example; pipeline made explicit, not implicit |
| Hook path glob `*plans/*` matches unintended paths | Low | Med | Anchor case-statement pattern precisely; manual review of resulting allowlist |

## Assumptions

- `Audit findings remain accurate as of 2026-05-13`: validated by direct inspection
  during the audit and brainstorming session.
- `ralph-loop-worker behavior is intentional through Phase 8` (no Agent tool,
  executes inline): preserved deliberately; worker redesign scoped to Phase 9.
- `agent: field stays in the ralph loop schema unchanged through Phase 8`:
  validated by brainstorming decision; consistency with Phase 9 redesign will be
  re-validated there.
- `Locked schemas remain locked`: explicit decision in CLAUDE.md requires logged
  override; this phase will not change them.
- `Forward-looking-only rename is acceptable`: validated by the convention that
  phase-complete artefacts are frozen historical records.

## Notes / Design Decisions

- **Wave ordering rationale**: Waves 1–3 are pure defect fixes. Wave 4 (rename)
  touches the most files; sequence it after Waves 1–3 to minimise merge churn.
  Wave 5 is documentation + verification and naturally lands last because it
  ratifies decisions in earlier waves.
- **No open questions remain**: brainstorming locked the always-dispatch worker
  redesign as Phase 9, the rename target as `decompose-phase`, and the
  skill-activation pipeline as two-stage. Phase 8 executes without blocking.
- **Capability preservation principle**: Phase 8 collapses overlaps by assigning
  lifecycle stages, not by deletion. Trigger keywords stay (as planning input);
  the `agent:` field stays (semantics revisited in Phase 9). The framework
  consolidates without losing functionality.
- **Atomicity**: each wave is independently shippable. Gate review can pass on
  partial completion if a wave is explicitly deferred with rationale.
- **Known deferrals** (recorded so they survive Phase 8 closeout):
  - **Phase 9** — always-dispatch worker redesign. Resolves C2 from the audit.
  - **Future phase (TBD)** — automation surface audit producing
    `docs/automation-surface.md`. Catalogues `--auto` expansion candidates and
    mid-flow decision points where the framework can act deterministically.

## Ralph Loops (5)

| Loop | Name | Type | Key Outputs |
|------|------|------|-------------|
| 027 | Hook + Permissions Hygiene (Wave 1) | Implementation | `settings.json` + `hooks.json` patched allowlist; `phase-goals-agent.md` frontmatter cleanup; repo-root `.claude/settings.json` with permissive allow rules; CLAUDE.md:56 updated; manual smoke test recorded (sentinel present → write to `plans/test.md` allowed, write to `core/skills/foo.md` blocked) |
| 028 | Sentinel Ownership Consolidation (Wave 2) | Refactor | `next-phase.md` sentinel ops removed; `run-gate.md` confirmed as sole owner; smoke test documented |
| 029 | `progress-report` Deduplication (Wave 3) | Refactor | Command body verified or refactored to invoke skill; no logic duplication |
| 030 | `new-loop` Rename to `decompose-phase` (Wave 4) | Migration | Command renamed; forward-looking refs updated; tombstone command added; PLANS-INDEX.md rename log appended; CLAUDE.md disambiguation line added |
| 031 | Disambiguation + Skill-Activation Policy (Wave 5) | Documentation | `new-phase.md` + `plan-and-phase.md` one-line "use this when…" headers; CLAUDE.md documents the two-stage skill-activation pipeline with example; `plan-skill-identification` skill body references planner-stage consumer role; `new-phase` wrapper verified against `phase-plan-creator` skill; `plans/PLANS-INDEX.md` updated with Phase 8 entry |
