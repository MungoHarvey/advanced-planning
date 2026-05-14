---
title: Framework Consistency Audit — Remediation
date: 2026-05-13
status: approved
type: design-spec
revised: 2026-05-13 (post-brainstorming)
---

# Framework Consistency Audit — Remediation Plan

## Identity Statement

The framework is a **structured execution engine**, not a flexible chat-style assistant.
Planning is paramount; execution is mechanical. The orchestrator manages stop/review
points at phase boundaries via gate review (`/run-gate`). Audit trail (phase tracking,
handoffs, history.jsonl) is a deliverable, not a side effect.

Phase 8 consolidates overlapping skills, commands, and processes so each step in the
workflow works together seamlessly — **without altering the workflow itself**. Capability
preservation is preferred over deletion; resolved overlaps come from clarifying lifecycle
stages, not from removing functionality.

## Context

A consistency audit of the advanced-planning framework (commands, agents, skills, hooks)
identified four real conflicts and five overlap/ambiguity issues that cause Claude to
behave differently across sessions on the same task. A brainstorming session refined
the scope and confirmed the framework identity above. This plan converts the audit
findings, filtered through the identity statement, into an ordered remediation programme.

Audit scope covered:

- `platforms/claude-code/commands/*.md` (12 commands)
- `platforms/claude-code/agents/*.md` (8 agents)
- `core/skills/*/SKILL.md` (7 skills)
- `platforms/claude-code/settings.json` and `platforms/claude-code/hooks/hooks.json`
- `CLAUDE.md` instructions and cross-references in `docs/`, `STRUCTURE.md`, `README.md`

## Decisions from Brainstorming (locked)

1. **Stop/review points**: existing gate review (`/run-gate` at phase boundaries) is
   sufficient. Phase 8 does not expand orchestrator responsibilities. Wave 2 sentinel
   ownership consolidation IS the "clarify ownership" piece.
2. **Audit scope**: execution-surface only. Planning artefacts (phase plan schema,
   ralph loop YAML, handoff fields, PLANS-INDEX.md) are not in scope for Phase 8.
3. **Worker redesign deferred**: the always-dispatch worker model (worker becomes a
   dispatcher, `agent:` field becomes universally meaningful, `analysis-worker` is the
   generic default) is the correct future direction but is deferred to **Phase 9** for
   its own scoping cycle. Phase 8 ships consolidation only.
4. **Skill activation**: two-stage pipeline. Description trigger keywords are scoped as
   *planning-time* input (consumed by `plan-skill-identification`). The frontmatter
   `skill:` field on each todo is the *only* execution-time source. Documented in
   CLAUDE.md.
5. **Permission friction**: a repo-root `.claude/settings.json` with permissive `allow`
   rules for routine `plans/**`, `.claude/state/**`, `.claude/logs/**` edits will
   eliminate per-edit permission prompts on status flips. Added to Wave 1.
6. **Automation surface audit deferred**: a survey of where `--auto` can be expanded
   (commands, mid-flow decision points, status-flip automation) is recognised as
   valuable future work but is deferred to its own scoping exercise. Not in Phase 8.

## Deferred to Future Phases

- **Phase 9 — Worker redesign as always-dispatcher.** Worker gains the Agent tool;
  every todo dispatches to either the named `agent:` or the `analysis-worker` default.
  Resolves C2 (`agent:` field semantics) and consolidates the "inline vs dispatched"
  bifurcation.
- **Future phase (TBD) — Automation surface audit.** Catalogue current `--auto` usage,
  identify expansion candidates (`/run-gate`, `/phase-compact`, `/run-closeout`,
  others), classify mid-flow decision points by risk, and produce
  `docs/automation-surface.md` as a reference for sequencing automation work.

## Problem Statement

Three classes of defect were found:

1. **Silent failure conditions** — hook allowlists and frontmatter tool scopes that
   either block legitimate writes or imply containment the harness does not enforce.
2. **Duplicated lifecycle ownership** — two commands manage the same sentinel,
   creating stale-state risk on nested invocation.
3. **Naming and surface-area ambiguity** — duplicated names, near-identical commands,
   and dual skill-activation mechanisms that produce non-deterministic routing.

Plus one workflow-friction issue surfaced during brainstorming:

4. **Permission noise** — routine edits to plan/loop/state files prompt for user
   approval despite being the framework's bread-and-butter operations.

## Findings (verbatim from audit)

### Real conflicts

- **C1 — `plans/` vs `.claude/plans/` path mismatch.** Planning-mode hook
  (`settings.json:69,82,95`) allows `*.claude/plans/*` only, but phase plans live in
  top-level `plans/`. Currently survives because `/plan-and-phase` removes the sentinel
  before writing real plans.
- **C2 — Worker cannot honor `agent:` field.** `ralph-orchestrator` runs
  `plan-subagent-identification` to populate `agent:` per todo, but `ralph-loop-worker`
  has no Agent tool. **Resolution deferred to Phase 9** (worker redesign).
- **C3 — Dual sentinel ownership.** Both `run-gate` and `next-phase` manage the
  `gate-review-mode` sentinel.
- **C4 — Cosmetic tool scope.** `phase-goals-agent` declares
  `Write(plans/gate-verdicts/*)` — harness ignores the parenthetical.

### Overlaps and ambiguity

- **O1 — Duplicate `progress-report`** (skill and command).
- **O2 — `new-phase` vs `plan-and-phase`** — disambiguation needed.
- **O3 — `new-loop` vs `next-loop`** — prefix collision.
- **O4 — `phase-plan-creator` skill ↔ `new-phase` command** — verify wrapper, not drift.
- **O5 — Two skill-activation mechanisms** — resolved by two-stage pipeline.

## Goals

1. Eliminate the conflicts C1, C3, C4 with the smallest change set that removes the
   defect. (C2 deferred to Phase 9.)
2. Resolve overlaps O1, O2, O3, O4, O5 by collapsing duplicates and clarifying
   intended use.
3. Eliminate permission friction for routine plan/loop/state edits.
4. Preserve all current passing behavior — no regressions in `/plan-and-phase`,
   `/new-phase`, `/next-loop`, `/run-gate`, or `/next-phase` flows.
5. Leave the framework with one source of truth for each lifecycle (sentinels,
   skill-activation pipeline stages, command-to-skill wrapping).

## Non-Goals

- No new commands, skills, or agents.
- No changes to the state-bus protocol or its writer/reader assignments.
- No changes to model-tier routing.
- No changes to locked schemas (`docs/phase-complete.schema.md`,
  `docs/phase-manifest-entry.schema.md`).
- No worker redesign. The "worker cannot spawn subagents" invariant is preserved
  through Phase 8; redesign happens in Phase 9.
- No changes to the `agent:` field in the ralph loop schema.

## Approach

Execute remediation in five waves, ordered by effort-to-impact ratio. Each wave is
independently shippable.

### Wave 1 — Hook + permissions hygiene

- **1.1** Fix planning-mode hook path allowlist in `settings.json` and `hooks.json` to
  include `*plans/*` alongside `*.claude/plans/*`. Update CLAUDE.md:56 to match.
- **1.2** Drop the cosmetic `Write(plans/gate-verdicts/*)` scope on `phase-goals-agent`;
  rely on the gate-review-mode hook for path containment.
- **1.3** Create repo-root `.claude/settings.json` (checked-in, applies to every
  developer of this repo — not `.claude/settings.local.json` which is per-developer
  and gitignored) with permissive `allow` rules for `Edit(plans/**)`,
  `Write(plans/**)`, `Edit(.claude/state/**)`, `Write(.claude/state/**)`,
  `Edit(.claude/logs/**)`, `Write(.claude/logs/**)`. Eliminates per-edit permission
  prompts on status updates.

### Wave 2 — Sentinel ownership

- **2.1** Make `run-gate` the sole owner of the `gate-review-mode` sentinel. Remove
  sentinel create/remove from `next-phase.md`. Ensure `next-phase` invokes `run-gate`
  rather than inlining gate steps.

### Wave 3 — Deduplicate `progress-report`

- **3.1** Confirm the `progress-report` command body invokes the
  `core/skills/progress-report` skill rather than re-implementing it. If it
  re-implements, refactor the command to invoke the skill.

### Wave 4 — Rename `new-loop` → `decompose-phase`

- **4.1** Rename `platforms/claude-code/commands/new-loop.md` →
  `decompose-phase.md`. Sweep all forward-looking references.
- **4.2** Add a tombstone `new-loop.md` containing a redirect notice pointing to
  `/decompose-phase`. Removable in a future phase.
- **4.3** Append a "Command Renames" table to `plans/PLANS-INDEX.md` recording the
  rename and rationale.

### Wave 5 — Command disambiguation + skill-activation policy

- **5.1** Add one-line "use this when…" headers to `new-phase.md` and
  `plan-and-phase.md` so the difference (codebase exploration vs direct planning) is
  the first thing a reader sees.
- **5.2** Document the two-stage skill-activation pipeline in CLAUDE.md:
  description-trigger keywords are planner input; frontmatter `skill:` field is the
  only execution-time source. Update `plan-skill-identification` skill body to make
  the keyword-parsing role explicit.
- **5.3** Verify O4: confirm the `new-phase` command body invokes the
  `phase-plan-creator` skill rather than re-implementing it. Refactor if drifted.

## Success Criteria

- **SC-1** Planning-mode hook allows writes to `plans/`, `.claude/plans/`, and
  `.claude/state/`; blocks all other paths when sentinel is present. Verified by
  manual smoke test.
- **SC-2** `phase-goals-agent` frontmatter declares `tools: Read, Glob, Grep, Write`
  with no parenthetical scope. Gate-review-mode hook still blocks non-verdict writes.
- **SC-3** Repo-root `.claude/settings.json` exists with permissive allow rules for
  `plans/**`, `.claude/state/**`, `.claude/logs/**`. Routine status edits no longer
  prompt for permission in this repo.
- **SC-4** `next-phase.md` contains no `gate-review-mode` sentinel writes or removes;
  `run-gate.md` remains the sole sentinel manager. Early-exit from `next-phase` after
  `run-gate` leaves no stale sentinel.
- **SC-5** Exactly one definition of `progress-report` is reachable from the user
  surface (the command), and it invokes the skill rather than duplicating logic.
- **SC-6** No forward-looking file contains the literal string `new-loop` as a command
  reference (historical phase artefacts excluded). Renamed command is documented in
  CLAUDE.md alongside `next-loop` with a one-line disambiguation. A tombstone
  `new-loop.md` redirects users to `/decompose-phase`. `plans/PLANS-INDEX.md` records
  the rename.
- **SC-7** `new-phase.md` and `plan-and-phase.md` each open with a one-sentence
  disambiguation line. The `new-phase` command body invokes `phase-plan-creator`
  without re-implementing it.
- **SC-8** CLAUDE.md documents the two-stage skill-activation pipeline (keywords at
  planning, frontmatter at execution) in one paragraph.
  `core/skills/plan-skill-identification/SKILL.md` references the pipeline and its
  consumer role explicitly.
- **SC-9** `python -m pytest platforms/python/tests/ -v` passes.
- **SC-10** All `core/state/*.json` files parse as valid JSON.
- **SC-11** `plans/PLANS-INDEX.md` lists Phase 8 with status, loop range, and outcome.

## Inputs

- Audit findings (this document, sections "Findings" and "Approach").
- Brainstorming decisions (this document, section "Decisions from Brainstorming").
- Files identified in audit:
  - `platforms/claude-code/settings.json`
  - `platforms/claude-code/hooks/hooks.json`
  - `platforms/claude-code/commands/{new-phase,next-phase,run-gate,new-loop,next-loop,plan-and-phase,progress-report}.md`
  - `platforms/claude-code/agents/{phase-goals-agent,ralph-loop-worker,ralph-orchestrator}.md`
  - `core/skills/{progress-report,plan-skill-identification}/SKILL.md`
  - `CLAUDE.md`, `STRUCTURE.md`, `docs/concepts.md`
- Existing test suite (`platforms/python/tests/`).

## Outputs

- One or two atomic commits per wave where practical, mapping to the success criteria.
- Updated `CLAUDE.md` reflecting renamed commands, skill-activation pipeline policy,
  and `.claude/settings.json` presence.
- Migration note in `plans/PLANS-INDEX.md` summarising the rename and Phase 8 entry.

## Constraints

- Python API must remain zero-dependency (standard library only).
- Core files must not reference platform-specific paths (no `.claude/` in core).
- Locked schemas (`docs/phase-complete.schema.md`,
  `docs/phase-manifest-entry.schema.md`) must not change.
- Existing locked behavior: `ralph-loop-worker` cannot spawn subagents — preserved
  through Phase 8. Reconsidered in Phase 9.
- The `agent:` field on todos retains its current schema and semantics through
  Phase 8.

## Dependencies

- All waves are mutually independent and can ship in any order.
- Wave 4 (rename) touches the most files; sequence it after Waves 1–3 to minimise
  rebase churn.
- Wave 5 (`.5.3` — verify O4 wrapper) depends on `new-phase.md` being readable; no
  blocker.

## Risks

- **Rename sweep miss (Wave 4)** — historical references in `plans/phase-N-*.md` may
  refer to the old name. Mitigation: tombstone command + PLANS-INDEX.md rename log +
  CLAUDE.md disambiguation line. Three discoverable paths to the new name.
- **Sentinel refactor regression (Wave 2)** — `next-phase` could lose gate-review
  protection if the `run-gate` invocation is skipped on certain paths. Mitigation:
  add an explicit smoke test that the sentinel exists during `run-gate`'s
  agent-spawn step.
- **Permission rules too permissive (Wave 1.3)** — repo-root settings could allow
  writes to paths the user did not intend. Mitigation: scope rules explicitly to
  `plans/**`, `.claude/state/**`, `.claude/logs/**` — no globs at repo root.
- **Skill-activation pipeline confusion (Wave 5)** — the two-stage model is new
  vocabulary in CLAUDE.md. Mitigation: one paragraph with concrete example showing
  a skill description, the planner parsing keywords, and the resulting frontmatter
  entry in a loop. Two-stage is explicit, not implicit.

## Open Questions

None. All open questions from the original draft were resolved through brainstorming.

## Assignment

Use `plans/phase-8.md` (the structured phase plan) as the input for
`/decompose-phase` (or `/new-loop` until Wave 4 lands) to break each wave into
executable ralph loops.
