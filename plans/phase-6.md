# Phase 6: Compaction Schema Audit & Lock

## Objective
Audit the existing `phase-goals-agent` verdict file format and lock the cold (`phase-N-complete.md`) and hot (`PLANS-INDEX.md` block) artefact schemas, grounded in a retrospective worked example drawn from this repo's own completed phase history.

## Scope

### Included:
- Audit of the current `phase-goals-agent` verdict JSON written under `plans/gate-verdicts/`
- Decision: extend the verdict schema or leave it as-is, based on what the compactor will need to consume
- Cold artefact schema: `phase-N-complete.md` structure (frontmatter + body) documented in `docs/`
- Hot manifest schema: per-phase YAML block for `PLANS-INDEX.md`, hard-capped at ≤8 lines per entry
- Retrospective worked example: hand-write `phase-N-complete.md` for Phase 5 (Gate Review Sub-Phase) as the canonical example
- Documentation of schema decisions and field semantics
- Anchor SHA mechanism: decide and document (frontmatter on phase plan vs git tags vs inference)

### Explicitly NOT included:
- Any compactor implementation (Phase 7)
- Any slash command or agent definition (Phases 7–8)
- Automatic trigger wiring (Phase 9)
- Retrieval helper (Phase 10)
- Changes to `phase-goals-agent`'s judgement logic — only its output format may be extended if needed

## Key Deliverables

| Deliverable | Format | Location |
|-------------|--------|----------|
| Cold artefact schema document | Markdown | `docs/phase-complete.schema.md` |
| Hot manifest entry schema document | Markdown | `docs/phase-manifest-entry.schema.md` |
| Verdict format audit + extension spec | Markdown | `docs/phase-goals-verdict-audit.md` |
| Anchor SHA mechanism decision | Markdown section | within `docs/phase-complete.schema.md` |
| Retrospective worked example | Markdown | `plans/phase-completes/phase-5-complete.md` |
| Schema cross-references | Updated `core/schemas/` index | `core/schemas/README.md` (or equivalent) |

## Success Criteria

- ✓ `docs/phase-complete.schema.md` exists and defines every frontmatter field with type, requirement, valid values, and an example
- ✓ `docs/phase-manifest-entry.schema.md` exists and constrains entries to ≤8 lines with a worked example
- ✓ Verdict audit document states whether `phase-goals-agent`'s current output is sufficient; if not, names every additional field needed
- ✓ `plans/phase-completes/phase-5-complete.md` exists, validates against the cold schema, and faithfully represents Phase 5's outcomes drawn from `phase-5.md` + `history.jsonl` + `git log`
- ✓ The worked example's `## Goals met / ## Deferred / ## Opened` sections are each one line per bullet — no prose paragraphs
- ✓ Anchor SHA mechanism is decided (frontmatter recommended) and the decision is documented with rationale
- ✓ A reviewer reading only the three schema docs can correctly produce a new `phase-N-complete.md` for any future phase without ambiguity

## Dependencies

### Must Complete Before This Phase:
- Design doc approved: `~/.gstack/projects/MungoHarvey-advanced-planning/mharvey2-main-design-20260513-103520.md` — establishes the constraints this phase implements

### Blocked By:
- Nothing — this is the foundation phase of the compaction programme

### Optional:
- Reading the existing `phase-goals-agent` definition in `.claude/agents/` and any verdict files under `plans/gate-verdicts/` from completed phases — strengthens the audit

## Skills Required (Broad Categories)

- `schema-design`: Defining validatable, machine-parseable schemas grounded in real examples
- `documentation`: Writing reference docs for future implementers
- `retrospective-analysis`: Reconstructing what happened in Phase 5 from its plan, history, and git log to produce the worked example
- `resume-review`: Available throughout this build for cross-session pickup — particularly valuable here because the schema decisions touch multiple files and may span sessions

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Schema designed in the abstract, doesn't survive contact with real data | Medium | High | Worked example IS a deliverable — the schema must be exercised against Phase 5 before being locked |
| Hot manifest creeps past 8 lines under "useful additions" pressure | Medium | High | Hard ceiling. Anything that wants to exceed it goes in the cold artefact. Schema doc states this as a non-negotiable rule. |
| `phase-goals-agent`'s verdict format proves insufficient and requires invasive changes | Low | Medium | Audit is a separate deliverable; if changes are large, descope to a minimal extension and document the gap |
| Anchor SHA mechanism choice constrains later phases | Low | Medium | Decide based on frequency of phase plan rewrites in this repo's history; document tradeoffs in case revisit needed |
| Worked example reconstructs Phase 5 inaccurately | Low | Medium | Cross-check against `phase-5-ralph-loops.md`, `history.jsonl`, and `git log` for the phase-5 commit range; any ambiguity gets flagged in `## Opened` |

## Assumptions

- `phase-goals-agent verdict exists in structured form`: The agent currently writes a JSON verdict to `plans/gate-verdicts/` per CLAUDE.md. Validated in audit.
- `Phase 5 has enough history to serve as a worked example`: Phase 5 completed with six loops (013–018) and produced concrete deliverables. Validated by `PLANS-INDEX.md`.
- `Schema can be markdown + YAML frontmatter without needing JSON Schema`: Matches existing `core/schemas/*.md` pattern. If validation needs grow, JSON Schema can be added later.
- `history.jsonl carries enough event detail per phase to support compaction`: To be confirmed by examining real entries during the audit.

## Notes / Design Decisions

- **Why a worked example is a hard deliverable, not optional:** The original PHASE-COMPACTION-PLAN.md flagged "schemas designed without a real example are usually wrong" as a known risk. The retrospective worked example IS the schema's regression test.
- **Why Phase 5 specifically:** It is the most recent completed phase, has six loops (richer to compact than a 2-loop phase), and includes a gate review sub-phase that itself produced verdict files — good stress test for the compactor's downstream consumers.
- **Cold artefact format:** Markdown + YAML frontmatter, matching existing `phase-N.md` and `phase-N-ralph-loops.md` patterns. No JSON-only artefacts.
- **Hot manifest format:** YAML block per phase rendered inline in `PLANS-INDEX.md`. Hybrid §7.4 option (c) from the original plan — parseable enough for machines, browseable for humans.
- **Anchor SHA lean:** Frontmatter field on the phase plan, written by `phase-plan-creator` at creation time. Fallback to history.jsonl inference if missing. Matches the existing metadata-in-plan-frontmatter pattern.
- **Out-of-scope decisions deferred:** Compactor model tier (Sonnet, per design doc), trigger mechanism (history.jsonl polling, no PostToolUse hook), retrieval helper command name (`/load-phase-context N`) — these belong to Phases 7–10, not Phase 6.

## Ralph Loops (4)

| Loop | Name | Type | Key Outputs |
|------|------|------|-------------|
| 019 | Verdict Format Audit | Research | `docs/phase-goals-verdict-audit.md` with current format dump, gap analysis, and extension spec if needed |
| 020 | Schema Drafts | Design | `docs/phase-complete.schema.md` and `docs/phase-manifest-entry.schema.md` with full field specs, anchor SHA decision, and validation checklists |
| 021 | Retrospective Worked Example | Implementation | `plans/phase-completes/phase-5-complete.md` reconstructed from Phase 5's plan/history/git log; validates against the draft schemas |
| 022 | Schema Lock & Cross-Reference | Documentation | Update `core/schemas/` index, ensure `CLAUDE.md` references the new schemas, final pass to confirm schemas survived contact with the worked example; iterate schemas if the example surfaced gaps |
