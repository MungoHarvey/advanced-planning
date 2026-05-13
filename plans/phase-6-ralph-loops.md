# Phase 6 — Ralph Loops

Four loops delivering the Compaction Schema Audit & Lock. Each loop is bounded, verifiable, and produces concrete files that feed Phase 7's `/phase-compact` implementation.

---

## Ralph Loop 019: Verdict Format Audit

```yaml
---
name: "ralph-loop-019"
task_name: "Verdict Format Audit"
max_iterations: 3
on_max_iterations: checkpoint

handoff_summary:
  done: "docs/phase-goals-verdict-audit.md produced with Current Format, Concrete Example (synthetic — no real verdicts exist yet), Gap Analysis table, and Extension Spec defining two new optional fields (criteria_outcomes, phase_title) for core/state/gate-verdict.schema.json."
  failed: ""
  needed: "Loop 020: draft cold artefact schema (docs/phase-complete.schema.md) and hot manifest entry schema (docs/phase-manifest-entry.schema.md) using the design doc and the verdict audit as inputs."

todos:
  - id: "loop-019-1"
    content: "Read phase-goals-agent definition and document its current verdict file format and write path"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "docs/phase-goals-verdict-audit.md exists with a 'Current Format' section that quotes the agent's verdict schema verbatim (fields, types, write path under plans/gate-verdicts/) and references the exact agent definition file"
    status: completed
    complexity: low
    priority: high
  - id: "loop-019-2"
    content: "Survey any existing verdict files written by completed phases under plans/gate-verdicts/ and record one concrete example"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "docs/phase-goals-verdict-audit.md contains a 'Concrete Example' section with at least one real verdict file dump (or notes if none exist yet) and a brief field-by-field annotation"
    status: completed
    complexity: low
    priority: high
  - id: "loop-019-3"
    content: "Map the compactor's required inputs against the current verdict format and produce a gap list"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "docs/phase-goals-verdict-audit.md contains a 'Gap Analysis' table listing each field the compactor needs (per design doc), whether it exists today, and what extension is required if missing"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-019-4"
    content: "Produce an extension spec if gaps exist, or state explicitly that no extension is needed"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "docs/phase-goals-verdict-audit.md ends with an 'Extension Spec' section that either lists each new field (name, type, semantics, default) OR states 'No extension required — current format is sufficient' with one-paragraph justification"
    status: completed
    complexity: medium
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Audit the current phase-goals-agent verdict format and produce a gap analysis against what the phase-compactor will need to consume, with a concrete extension spec or explicit no-change decision.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-019"

  ## Success criteria
  - [ ] docs/phase-goals-verdict-audit.md exists with Current Format, Concrete Example, Gap Analysis, and Extension Spec sections
  - [ ] All sections reference concrete files (agent definition path, verdict file path if any, design doc path)
  - [ ] Gap Analysis table covers every input the compactor needs per the design doc
  - [ ] Extension Spec is either a complete field-by-field plan or a justified no-change decision

  ## Required skills
  - `writing-skills`: Clear, factual reference documentation with no padding

  ## Inputs
  - phase-goals-agent definition: locate under .claude/agents/ or platforms/claude-code/agents/
  - Any existing verdict files: plans/gate-verdicts/*.json
  - Design doc: ~/.gstack/projects/MungoHarvey-advanced-planning/mharvey2-main-design-20260513-103520.md (compactor input requirements)

  ## Expected outputs
  - docs/phase-goals-verdict-audit.md

  ## Constraints
  - Do NOT modify phase-goals-agent in this loop. Audit only — extension implementation is out of scope for Phase 6.
  - If no verdict files exist yet (programme hasn't run gate review), say so and use the agent definition as the source of truth.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-019 — verdict format audit and gap analysis"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Audit what `phase-goals-agent` currently writes at gate time and decide whether its output is sufficient for the compactor to consume, or whether a minimal extension is required.

## Success Criteria
- ✓ Audit document covers current format, concrete example, gap analysis, extension spec
- ✓ Decision is binary and justified: extend the verdict format with named fields, OR leave it alone

## Skills Required

### Broad (from phase plan):
- `documentation`: Writing reference docs grounded in real evidence

### Specific (refined for this loop):
- `writing-skills`: Clear, factual prose for a reference document

### Discovered (new, identified during planning):
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| phase-goals-agent definition | `.claude/agents/` or `platforms/claude-code/agents/` | Markdown |
| Existing verdicts (if any) | `plans/gate-verdicts/*.json` | JSON |
| Design doc | `~/.gstack/projects/MungoHarvey-advanced-planning/mharvey2-main-design-20260513-103520.md` | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Verdict audit | `docs/phase-goals-verdict-audit.md` | Markdown |

## Dependencies

### Must Complete Before
- Nothing — first loop in Phase 6

### Blocked By
- Nothing

## Complexity
**Scope**: Low
**Estimated effort**: 30–45 minutes
**Key challenges**:
1. Locating the canonical phase-goals-agent definition (project-local vs global)
2. Distinguishing what the agent writes today from what would be ideal — focus on minimal-extension thinking

---

## Ralph Loop 020: Schema Drafts

```yaml
---
name: "ralph-loop-020"
task_name: "Schema Drafts (Cold + Hot)"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-020-1"
    content: "Draft docs/phase-complete.schema.md with frontmatter field spec, body section rules, and a worked example skeleton"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "docs/phase-complete.schema.md exists with sections: Purpose, Frontmatter Fields (table: name/type/required/valid values/example), Body Sections (goals_met/deferred/opened with one-line bullet rule), Anchor SHA Decision, Validation Checklist, and a complete worked-example skeleton showing the full structure"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-020-2"
    content: "Draft docs/phase-manifest-entry.schema.md constraining hot manifest blocks to ≤8 lines"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "docs/phase-manifest-entry.schema.md exists with: Purpose, YAML field spec table (phase, title, status, commits, detail, highlights), Hard Rules section stating the ≤8-line ceiling explicitly, max 2 highlights bullets, one complete worked example block, and a Validation Checklist"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-020-3"
    content: "Document the anchor SHA mechanism decision within docs/phase-complete.schema.md"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "docs/phase-complete.schema.md 'Anchor SHA Decision' section names the chosen mechanism (frontmatter on phase plan with history.jsonl inference fallback), states who writes it and when, and includes one alternative considered with the reason it was rejected"
    status: pending
    complexity: low
    priority: high
  - id: "loop-020-4"
    content: "Cross-reference the new schemas from core/schemas/ index"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "core/schemas/README.md (or equivalent index) lists the two new schemas under docs/ with one-line descriptions and links; if no index file exists, create core/schemas/README.md with entries for all existing core schemas plus the two new ones"
    status: pending
    complexity: low
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Draft the cold artefact schema and hot manifest entry schema, lock the anchor SHA mechanism, and register the new schemas in the core schemas index.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-020"

  ## Success criteria
  - [ ] docs/phase-complete.schema.md exists with all required sections and a worked-example skeleton
  - [ ] docs/phase-manifest-entry.schema.md exists and enforces ≤8 lines per entry as a hard rule
  - [ ] Anchor SHA mechanism is decided and documented with rationale
  - [ ] core/schemas/ index references the two new schemas

  ## Required skills
  - `writing-skills`: Schema reference documentation
  - Pattern reference: existing schemas in core/schemas/ for style consistency

  ## Inputs
  - Design doc: ~/.gstack/projects/MungoHarvey-advanced-planning/mharvey2-main-design-20260513-103520.md (section "Schema (cold artefact)" and "Schema (hot manifest entry)")
  - Existing schemas: core/schemas/*.schema.md (for style)
  - Verdict audit from loop 019: docs/phase-goals-verdict-audit.md (informs what the cold artefact can reference)

  ## Expected outputs
  - docs/phase-complete.schema.md
  - docs/phase-manifest-entry.schema.md
  - Updated core/schemas/README.md (or new file if absent)

  ## Constraints
  - The ≤8-line rule for hot manifest entries is a HARD CEILING. The schema must state this and the validation checklist must include a line-count check.
  - Frontmatter fields must mirror the design doc exactly. No invention of new fields.
  - Body sections (goals_met / deferred / opened) must enforce one-line bullets — no prose paragraphs in the schema's worked example.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-020 — cold and hot schemas drafted"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Lock the cold artefact schema (`phase-N-complete.md`) and hot manifest entry schema (`PLANS-INDEX.md` block), and decide the anchor SHA mechanism. These schemas are the contract every downstream phase implements against.

## Success Criteria
- ✓ Both schema docs exist with complete field specs and validation checklists
- ✓ Hot manifest's ≤8-line ceiling is documented as non-negotiable
- ✓ Anchor SHA decision is final and rationalised

## Skills Required

### Broad (from phase plan):
- `schema-design`: Defining validatable, machine-parseable schemas
- `documentation`: Writing reference docs

### Specific (refined for this loop):
- `writing-skills`: Tight, unambiguous schema prose

### Discovered (new, identified during planning):
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Design doc | `~/.gstack/projects/MungoHarvey-advanced-planning/mharvey2-main-design-20260513-103520.md` | Markdown |
| Existing schemas (style ref) | `core/schemas/*.schema.md` | Markdown |
| Verdict audit | `docs/phase-goals-verdict-audit.md` | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Cold artefact schema | `docs/phase-complete.schema.md` | Markdown |
| Hot manifest schema | `docs/phase-manifest-entry.schema.md` | Markdown |
| Schemas index | `core/schemas/README.md` | Markdown |

## Dependencies

### Must Complete Before
- ralph-loop-019: needs the verdict audit to know what the cold artefact can reference

### Blocked By
- Nothing else

## Complexity
**Scope**: Medium
**Estimated effort**: 1.5–2 hours
**Key challenges**:
1. Resisting fields beyond what the design doc specifies — schemas must reflect the spec, not extend it
2. Worked-example skeleton must be realistic enough to be useful as a regression test for loop 021

---

## Ralph Loop 021: Retrospective Worked Example

```yaml
---
name: "ralph-loop-021"
task_name: "Retrospective Worked Example (Phase 5)"
max_iterations: 3
on_max_iterations: checkpoint

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-021-1"
    content: "Reconstruct Phase 5 outcomes from phase-5.md, phase-5-ralph-loops.md, history.jsonl, and git log"
    skill: "resume-review"
    agent: "ralph-loop-worker"
    outcome: "An internal working note (committed alongside the artefact or as a scratch section) enumerates Phase 5's stated success criteria, the actual outcomes per loop (013-018), the commit range for the phase, and any deferred or opened items — drawn from primary sources only, no speculation"
    status: pending
    complexity: high
    priority: high
  - id: "loop-021-2"
    content: "Determine the Phase 5 anchor and end SHAs from git log and history.jsonl"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Phase 5 anchor_sha and end_sha are both identified with the exact short SHAs documented; rationale states why each was selected (first phase-5 commit and gate-pass / phase complete commit)"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-021-3"
    content: "Write plans/phase-completes/phase-5-complete.md following the cold artefact schema"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "plans/phase-completes/phase-5-complete.md exists; passes the validation checklist from docs/phase-complete.schema.md; contains complete frontmatter (phase, title, status, gate_verdict_ref, anchor_sha, end_sha, commit_count, loop_count, created); each body section (goals_met/deferred/opened) contains only one-line bullets, no prose paragraphs"
    status: pending
    complexity: high
    priority: high
  - id: "loop-021-4"
    content: "Write the corresponding hot manifest entry block as a standalone YAML snippet for verification"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "plans/phase-completes/phase-5-manifest-entry.yaml (or appended within the .md as a fenced block) exists; passes docs/phase-manifest-entry.schema.md validation; total entry length ≤8 lines including all fields and at most 2 highlights"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-021-5"
    content: "Verify both artefacts against their schema validation checklists and record any schema gaps"
    skill: "verification-before-completion"
    agent: "ralph-loop-worker"
    outcome: "A verification note (in handoff_summary.done or appended to the artefact) confirms each item in docs/phase-complete.schema.md's checklist and docs/phase-manifest-entry.schema.md's checklist passes; any failures are listed as schema gaps for loop 022 to address"
    status: pending
    complexity: medium
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Produce a retrospective worked example by reconstructing Phase 5's completion artefact and manifest entry from primary sources, validating both against the locked schemas.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-021"

  ## Success criteria
  - [ ] plans/phase-completes/phase-5-complete.md exists and validates against docs/phase-complete.schema.md
  - [ ] A corresponding manifest entry block exists and validates against docs/phase-manifest-entry.schema.md
  - [ ] Both artefacts use one-line bullets only — no prose paragraphs in goals_met / deferred / opened
  - [ ] Schema validation gaps (if any) are explicitly listed for loop 022 to address

  ## Required skills
  - `resume-review`: Reconstructing prior session outcomes from plan, history, and git log
  - `writing-skills`: Tight one-line bullet discipline
  - `verification-before-completion`: Checklist-based validation before marking todos complete

  ## Inputs
  - Phase 5 plan: plans/phase-5.md
  - Phase 5 loops: plans/phase-5-ralph-loops.md (loops 013–018)
  - History: .claude/state/history.jsonl (filter for phase 5 events)
  - Git log: git log --oneline (find phase-5 commit range)
  - Schemas (from loop 020): docs/phase-complete.schema.md, docs/phase-manifest-entry.schema.md

  ## Expected outputs
  - plans/phase-completes/phase-5-complete.md
  - Manifest entry block (within the .md or as a sibling .yaml)
  - Schema gap list (in handoff_summary or scratch note) if any

  ## Constraints
  - Primary sources only. No invention. If something can't be reconstructed from plan/history/git, list it under 'opened' as a known gap.
  - One-line bullets everywhere in the body sections. If a goal needs more context, write it tighter or move detail into git via commit-range pointers.
  - Hot manifest entry MUST be ≤8 lines total. Count them.
  - Do not modify the schemas in this loop. If the schemas prove insufficient, log the gap for loop 022.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-021 — phase-5 retrospective worked example"
  2. Update handoff_summary (note any schema gaps in 'failed' or 'needed')
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Produce the schema's regression test by reconstructing Phase 5's completion as it should have appeared had compaction existed. This exercise validates the schemas against real data and surfaces any gaps for the lock loop to address.

## Success Criteria
- ✓ Cold artefact for Phase 5 exists and validates
- ✓ Hot manifest entry exists, validates, fits ≤8 lines
- ✓ Schema gaps surfaced are explicit and actionable for loop 022

## Skills Required

### Broad (from phase plan):
- `retrospective-analysis`: Reconstructing what happened from durable records
- `documentation`: Producing the artefacts

### Specific (refined for this loop):
- `resume-review`: This skill exists precisely for picking up prior work from durable records — natural fit for reconstructing Phase 5 from plan + history + git log
- `writing-skills`: One-line-bullet discipline
- `verification-before-completion`: Checklist-driven validation

### Discovered (new, identified during planning):
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Phase 5 plan | `plans/phase-5.md` | Markdown |
| Phase 5 loops | `plans/phase-5-ralph-loops.md` | Markdown + YAML |
| State history | `.claude/state/history.jsonl` | JSONL |
| Git log | `git log` | git |
| Cold schema | `docs/phase-complete.schema.md` | Markdown |
| Hot schema | `docs/phase-manifest-entry.schema.md` | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Phase 5 complete artefact | `plans/phase-completes/phase-5-complete.md` | Markdown + YAML frontmatter |
| Phase 5 manifest entry | `plans/phase-completes/phase-5-manifest-entry.yaml` (or fenced in the .md) | YAML |

## Dependencies

### Must Complete Before
- ralph-loop-020: needs the locked schemas to validate against

### Blocked By
- Nothing else

## Complexity
**Scope**: High — this is the loop most likely to surface schema gaps
**Estimated effort**: 2–3 hours
**Key challenges**:
1. Reconstructing Phase 5 faithfully without inventing detail not in primary sources
2. Holding the one-line-bullet rule under the temptation to add context
3. Fitting the manifest entry into ≤8 lines without losing essential information

---

## Ralph Loop 022: Schema Lock & Cross-Reference

```yaml
---
name: "ralph-loop-022"
task_name: "Schema Lock & Cross-Reference"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-022-1"
    content: "Review schema gaps surfaced by loop 021 and patch docs/phase-complete.schema.md and docs/phase-manifest-entry.schema.md as needed"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "Every gap listed in loop-021's handoff is either resolved (schema edited and gap closed) or explicitly deferred with a documented reason; both schema documents reflect the final locked form"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-022-2"
    content: "Mark both schemas as locked with a Status: LOCKED note and date in their frontmatter or top of file"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "docs/phase-complete.schema.md and docs/phase-manifest-entry.schema.md each contain a 'Status: LOCKED' marker with the lock date; downstream phases will treat these as frozen contracts"
    status: pending
    complexity: low
    priority: high
  - id: "loop-022-3"
    content: "Update CLAUDE.md to reference the new schemas in the relevant architecture section"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "CLAUDE.md contains a reference to docs/phase-complete.schema.md and docs/phase-manifest-entry.schema.md under the Architecture section (or a new Phase Compaction subsection), describing each schema in one sentence"
    status: pending
    complexity: low
    priority: high
  - id: "loop-022-4"
    content: "Run a verification scan to confirm the Phase 5 worked example still validates against the locked schemas"
    skill: "verification-before-completion"
    agent: "ralph-loop-worker"
    outcome: "plans/phase-completes/phase-5-complete.md and its manifest entry are re-validated against the locked schemas; any newly surfaced inconsistency is fixed before marking complete; a verification note is included in handoff"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-022-5"
    content: "Update plans/PLANS-INDEX.md to note Phase 6 schema deliverables and Phase 7 readiness"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "plans/PLANS-INDEX.md is updated: Phase 6 row shows status complete, all four loops (019-022) show status complete, and the Compaction Programme block notes that Phase 7 (/phase-compact slash command) is now ready to plan"
    status: pending
    complexity: low
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Close out Phase 6 by patching any schema gaps surfaced by the worked example, locking the schemas, cross-referencing them from CLAUDE.md, and updating the plans index.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-022"

  ## Success criteria
  - [ ] All schema gaps from loop 021 are resolved or explicitly deferred
  - [ ] Both schema documents marked Status: LOCKED with date
  - [ ] CLAUDE.md references the new schemas
  - [ ] Phase 5 worked example re-validates against the locked schemas
  - [ ] PLANS-INDEX.md updated to reflect Phase 6 completion and Phase 7 readiness

  ## Required skills
  - `writing-skills`: Schema editing
  - `verification-before-completion`: Final validation pass before lock

  ## Inputs
  - Loop 021 handoff (schema gaps list)
  - docs/phase-complete.schema.md (draft from loop 020)
  - docs/phase-manifest-entry.schema.md (draft from loop 020)
  - plans/phase-completes/phase-5-complete.md (worked example from loop 021)
  - CLAUDE.md

  ## Expected outputs
  - Patched schemas with Status: LOCKED markers
  - Updated CLAUDE.md
  - Updated PLANS-INDEX.md

  ## Constraints
  - The lock is meaningful: after this loop, schemas may only change via a new phase plan or explicit decision logged in CLAUDE.md.
  - Re-validation must be checklist-driven, not 'looks fine'.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-022 — schemas locked, Phase 6 complete"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Final loop of Phase 6. Closes the gaps surfaced by the worked example, locks the schemas as frozen contracts, and signals downstream phase readiness.

## Success Criteria
- ✓ Schemas marked LOCKED
- ✓ CLAUDE.md references them
- ✓ Worked example re-validates
- ✓ PLANS-INDEX.md current

## Skills Required

### Broad (from phase plan):
- `documentation`: Final cross-references and lock metadata

### Specific (refined for this loop):
- `writing-skills`: Schema patching
- `verification-before-completion`: Closing-pass validation

### Discovered (new, identified during planning):
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Loop 021 handoff (gaps) | `phase-6-ralph-loops.md` handoff_summary | YAML |
| Draft schemas | `docs/phase-complete.schema.md`, `docs/phase-manifest-entry.schema.md` | Markdown |
| Worked example | `plans/phase-completes/phase-5-complete.md` | Markdown + YAML |
| Project context | `CLAUDE.md` | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Locked schemas | `docs/phase-complete.schema.md`, `docs/phase-manifest-entry.schema.md` | Markdown |
| CLAUDE.md update | `CLAUDE.md` | Markdown |
| Plans index update | `plans/PLANS-INDEX.md` | Markdown |

## Dependencies

### Must Complete Before
- ralph-loop-021: needs the gap list and worked example

### Blocked By
- Nothing else

## Complexity
**Scope**: Low–Medium
**Estimated effort**: 45–60 minutes
**Key challenges**:
1. Avoiding scope creep — only patch gaps surfaced by loop 021, not redesign
2. The 'lock' must be enforceable: any future change reopens the schema explicitly

---

## Phase 6 Summary

| Loop | Name | Complexity | Worker Agent | Key Output |
|------|------|------------|--------------|------------|
| 019 | Verdict Format Audit | Low | ralph-loop-worker | `docs/phase-goals-verdict-audit.md` |
| 020 | Schema Drafts | Medium | ralph-loop-worker | `docs/phase-complete.schema.md`, `docs/phase-manifest-entry.schema.md` |
| 021 | Retrospective Worked Example | High | ralph-loop-worker | `plans/phase-completes/phase-5-complete.md` + manifest entry |
| 022 | Schema Lock & Cross-Reference | Low–Medium | ralph-loop-worker | Locked schemas, updated CLAUDE.md, updated PLANS-INDEX.md |

**Total estimated effort**: 4.5–7 hours across four loops.

**Critical path**: 019 → 020 → 021 → 022 (strictly sequential — each loop consumes its predecessor's output).

**Skill usage map**:
- `writing-skills` — used in loops 019, 020, 021, 022 for prose discipline
- `resume-review` — primary skill for loop 021's retrospective reconstruction
- `verification-before-completion` — used in loops 021 and 022 for checklist validation

**Recommended execution**: `/next-loop --auto` to chain all four loops without manual handoff.
