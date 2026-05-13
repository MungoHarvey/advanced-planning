# Phase 7 — Ralph Loops

Four loops delivering the `/phase-compact` slash command end-to-end, plus the verdict-schema extension and agent-permission fix surfaced by Phase 6.

---

## Ralph Loop 023: Verdict Schema Extension + Agent Fix

```yaml
---
name: "ralph-loop-023"
task_name: "Verdict Schema Extension + phase-goals-agent Permission Fix"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "Extended core/state/gate-verdict.schema.json with optional criteria_outcomes (array with criterion/status/evidence/deferred_to) and phase_title (string); added Write(plans/gate-verdicts/*) to phase-goals-agent tool allowlist; updated agent prompt to populate both fields during Step 3 and at verdict write time; all core/state schemas parse and Phase 6 verdict validates against the extended schema."
  failed: ""
  needed: "Proceed to loop 024: implement the /phase-compact slash command at platforms/claude-code/commands/phase-compact.md."

todos:
  - id: "loop-023-1"
    content: "Extend core/state/gate-verdict.schema.json with optional criteria_outcomes and phase_title fields per docs/phase-goals-verdict-audit.md extension spec"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "core/state/gate-verdict.schema.json validates as JSON Schema draft-07; contains optional criteria_outcomes (array with items.properties: criterion, status, evidence, deferred_to) and phase_title (string); additionalProperties remains false; existing required fields unchanged; existing verdict files (phase-6 attempt 1) still parse against the schema"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-023-2"
    content: "Locate phase-goals-agent definition and add Write permission scoped to plans/gate-verdicts/"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "phase-goals-agent definition file (under platforms/claude-code/agents/ or .claude/agents/) has Write in its tool allowlist with a path scope restricting to plans/gate-verdicts/; the change is committed and the agent definition's frontmatter remains valid"
    status: completed
    complexity: low
    priority: high
  - id: "loop-023-3"
    content: "Update phase-goals-agent prompt instructions to populate criteria_outcomes (one entry per success criterion) and phase_title (copied from phase plan) when writing verdicts"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "phase-goals-agent definition's body/prompt includes explicit instructions to populate criteria_outcomes (with status values pass/fail/deferred and evidence pointers) and phase_title; instructions reference the extended schema by path"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-023-4"
    content: "Verify all existing JSON schemas in core/state/ still parse cleanly with the extension applied"
    skill: "verification-before-completion"
    agent: "ralph-loop-worker"
    outcome: "python -c 'import json, pathlib; [json.loads(f.read_text()) for f in pathlib.Path(\"core/state\").glob(\"*.json\")]' exits 0 with no exceptions; existing verdict file plans/gate-verdicts/phase-6-attempt-1-phase-goals-agent.json still parses as a valid instance of the extended schema"
    status: completed
    complexity: low
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Extend gate-verdict.schema.json with the two fields from loop 019's extension spec, fix phase-goals-agent's Write permission gap surfaced during Phase 6 gate review, and update the agent's prompt to populate the new fields.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-023"

  ## Success criteria
  - [ ] core/state/gate-verdict.schema.json includes criteria_outcomes and phase_title as optional fields
  - [ ] phase-goals-agent has Write permission scoped to plans/gate-verdicts/
  - [ ] phase-goals-agent prompt populates the new fields
  - [ ] All core/state/*.json schemas still parse; existing verdicts still validate

  ## Required skills
  - `writing-skills`: Clear updates to the agent definition prompt
  - `verification-before-completion`: JSON parse check

  ## Inputs
  - Extension spec: docs/phase-goals-verdict-audit.md (Extension Spec section)
  - Current verdict schema: core/state/gate-verdict.schema.json
  - phase-goals-agent definition: platforms/claude-code/agents/phase-goals-agent.md (or wherever it is — locate first)
  - Existing verdict file (regression test): plans/gate-verdicts/phase-6-attempt-1-phase-goals-agent.json

  ## Expected outputs
  - Modified core/state/gate-verdict.schema.json
  - Modified phase-goals-agent definition file

  ## Constraints
  - Both new fields MUST be optional. Existing verdicts must continue to validate.
  - Write permission must be SCOPED to plans/gate-verdicts/ — no broader Write access.
  - Do not modify other agents in this loop.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-023 — verdict schema extended, agent permission fixed"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Lay the groundwork for `/phase-compact` by extending the verdict format with the fields the compactor will need, and by fixing the Write permission gap that surfaced during Phase 6 gate review.

## Success Criteria
- ✓ Schema extended without breaking backward compatibility
- ✓ phase-goals-agent definition now has scoped Write permission
- ✓ Existing Phase 6 verdict files still validate

## Skills Required

### Broad (from phase plan):
- `json-schema`: Extending the verdict schema cleanly
- `agent-definition`: Editing tool allowlist and prompt

### Specific (refined for this loop):
- `writing-skills`: Prompt edits
- `verification-before-completion`: Parse regression check

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Extension spec | `docs/phase-goals-verdict-audit.md` | Markdown |
| Verdict schema | `core/state/gate-verdict.schema.json` | JSON Schema |
| Agent definition | `platforms/claude-code/agents/phase-goals-agent.md` (TBC) | Markdown |
| Regression sample | `plans/gate-verdicts/phase-6-attempt-1-phase-goals-agent.json` | JSON |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Extended verdict schema | `core/state/gate-verdict.schema.json` | JSON Schema |
| Updated agent | `platforms/claude-code/agents/phase-goals-agent.md` | Markdown |

## Dependencies

### Must Complete Before
- Nothing — first loop in Phase 7

### Blocked By
- Nothing

## Complexity
**Scope**: Medium
**Estimated effort**: 45–60 minutes
**Key challenges**:
1. Backward compatibility — old verdicts must still validate
2. Locating the canonical phase-goals-agent definition file

---

## Ralph Loop 024: `/phase-compact` Command Implementation

```yaml
---
name: "ralph-loop-024"
task_name: "/phase-compact slash command implementation"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "Wrote platforms/claude-code/commands/phase-compact.md with frontmatter, description, 12-step numbered Steps section, Error Modes table, and Notes; covers arg parsing, anchor SHA resolution with history.jsonl fallback, gate verdict read, history slice, git log range, cold artefact write with idempotency, hot manifest write with idempotency, schema validation against both locked schema checklists, and gate-fail artefact naming."
  failed: ""
  needed: "Proceed to loop 025: execute /phase-compact 6 step-by-step against Phase 6 to produce plans/phase-completes/phase-6-complete.md and a PLANS-INDEX.md manifest entry, then verify idempotency."

todos:
  - id: "loop-024-1"
    content: "Create platforms/claude-code/commands/phase-compact.md following the existing slash-command pattern (frontmatter + Steps section)"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "platforms/claude-code/commands/phase-compact.md exists with proper frontmatter, a one-paragraph description, and a numbered Steps section; matches the structural pattern of platforms/claude-code/commands/run-gate.md and platforms/claude-code/commands/next-phase.md"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-024-2"
    content: "Document the command's input parsing: <phase-id> argument, anchor SHA resolution from phase plan frontmatter with history.jsonl inference fallback"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "phase-compact.md Steps section includes explicit Step for parsing phase-id, reading phase plan frontmatter for anchor_sha, falling back to history.jsonl inference if absent, and erroring clearly if neither resolves"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-024-3"
    content: "Document the read protocol: phase plan, gate verdict file, history.jsonl slice, git log range"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "phase-compact.md Steps section enumerates inputs read (phase plan path, gate-verdict path, history.jsonl filter, git log <anchor>..<end>) with concrete commands shown for each"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-024-4"
    content: "Document the write protocol: cold artefact (plans/phase-completes/phase-N-complete.md) and hot manifest entry (PLANS-INDEX.md block); enforce idempotency by detect-and-update for both"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "phase-compact.md Steps section enumerates write outputs with paths, explicit idempotency rules (detect existing cold artefact / manifest entry for the same phase and update-in-place rather than duplicating), and a validation step that runs the schema checklists from docs/phase-complete.schema.md and docs/phase-manifest-entry.schema.md"
    status: completed
    complexity: high
    priority: high
  - id: "loop-024-5"
    content: "Document error modes and exit conditions: missing inputs, schema validation failures, gate-fail input handling"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "phase-compact.md includes an 'Error Modes' or 'Notes' section listing: missing phase plan (error), missing anchor SHA (error after fallback fails), schema validation failure (error with checklist diff), gate-failed input (writes phase-N-complete-v<attempt>-failed.md per design doc rather than the pass-form artefact)"
    status: completed
    complexity: medium
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Write the /phase-compact slash command as a complete, executable .md file with input parsing, read protocol, write protocol (with idempotency), schema validation, and error handling.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-024"

  ## Success criteria
  - [ ] platforms/claude-code/commands/phase-compact.md exists and matches the project's slash-command structural pattern
  - [ ] Command spec covers: arg parsing, anchor SHA resolution with fallback, all read inputs, both write outputs, idempotency, schema validation, error modes
  - [ ] Gate-fail input handling is documented per the design doc (failed artefact under different name)

  ## Required skills
  - `writing-skills`: Clean, tight command spec prose

  ## Inputs
  - Existing slash commands (style ref): platforms/claude-code/commands/run-gate.md, platforms/claude-code/commands/next-phase.md
  - Locked schemas: docs/phase-complete.schema.md, docs/phase-manifest-entry.schema.md
  - Design doc: ~/.gstack/projects/MungoHarvey-advanced-planning/mharvey2-main-design-20260513-103520.md (sections on trigger/orchestration sequence and gate-fail behaviour)
  - Anchor SHA decision: docs/phase-complete.schema.md (Anchor SHA Decision section)

  ## Expected outputs
  - platforms/claude-code/commands/phase-compact.md

  ## Constraints
  - This is a SLASH COMMAND spec, not an agent. It instructs the main thread directly. No subagent spawning.
  - Idempotency is mandatory. Document detect-and-update behaviour explicitly.
  - Schema validation must be a numbered step, not an afterthought. If validation fails, the command must fail loudly.
  - Do not implement /load-phase-context here — that's Phase 10.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-024 — /phase-compact slash command implemented"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Write the `/phase-compact` slash command specification. This is the central deliverable of Phase 7 — a complete, self-contained command file that the main thread can execute against any completed phase.

## Success Criteria
- ✓ Command file exists and is structurally consistent with existing commands
- ✓ All read inputs and write outputs documented with concrete paths
- ✓ Idempotency, schema validation, error modes all explicit

## Skills Required

### Broad (from phase plan):
- `slash-command-authoring`: Writing a complete .md command spec
- `writing-skills`: Tight prose for a reference command

### Specific (refined for this loop):
- `writing-skills`

### Discovered (new, identified during planning):
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Existing commands (style) | `platforms/claude-code/commands/*.md` | Markdown |
| Cold schema | `docs/phase-complete.schema.md` | Markdown |
| Hot schema | `docs/phase-manifest-entry.schema.md` | Markdown |
| Design doc | `~/.gstack/projects/.../mharvey2-main-design-20260513-103520.md` | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Slash command spec | `platforms/claude-code/commands/phase-compact.md` | Markdown |

## Dependencies

### Must Complete Before
- Loop 023: needs the extended verdict format so the command can consume `criteria_outcomes`

### Blocked By
- Nothing else

## Complexity
**Scope**: High — this loop produces the core artefact of Phase 7
**Estimated effort**: 1.5–2 hours
**Key challenges**:
1. Idempotency rules must be precise — detect-and-update logic stated as steps
2. Schema validation must be a real step, not "verify it works"

---

## Ralph Loop 025: End-to-End Run Against Phase 6

```yaml
---
name: "ralph-loop-025"
task_name: "End-to-End Validation Run (Phase 6 target)"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-025-1"
    content: "Execute /phase-compact 6 step-by-step manually following platforms/claude-code/commands/phase-compact.md"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Each step in phase-compact.md is executed in order against phase 6; intermediate state (anchor SHA, end SHA, gate verdict ref, history.jsonl slice, git log range) is captured in working memory or scratch notes for verification"
    status: pending
    complexity: high
    priority: high
  - id: "loop-025-2"
    content: "Produce plans/phase-completes/phase-6-complete.md and validate against docs/phase-complete.schema.md checklist"
    skill: "verification-before-completion"
    agent: "ralph-loop-worker"
    outcome: "plans/phase-completes/phase-6-complete.md exists with all required frontmatter fields; all 14 (or current) validation checklist items pass; body sections (goals_met/deferred/opened) use one-line bullets only; gate_verdict_ref points to the real plans/gate-verdicts/phase-6-attempt-1-phase-goals-agent.json (no sentinel needed — Phase 6 has real verdicts)"
    status: pending
    complexity: high
    priority: high
  - id: "loop-025-3"
    content: "Append a Phase 6 hot manifest entry to plans/PLANS-INDEX.md and validate against docs/phase-manifest-entry.schema.md checklist"
    skill: "verification-before-completion"
    agent: "ralph-loop-worker"
    outcome: "plans/PLANS-INDEX.md contains a new Phase 6 manifest entry (YAML block); the entry is ≤8 lines; all manifest schema checklist items pass; the entry's commits field points to the correct phase 6 SHA range; the entry sits in ascending phase order"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-025-4"
    content: "Run /phase-compact 6 a second time and verify idempotency (no duplicates, no corruption)"
    skill: "verification-before-completion"
    agent: "ralph-loop-worker"
    outcome: "Second invocation of the command leaves plans/phase-completes/phase-6-complete.md unchanged in semantically meaningful ways (timestamps may update but content is stable); PLANS-INDEX.md contains exactly ONE Phase 6 manifest entry, not two; a diff confirms this"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-025-5"
    content: "Record any schema gaps or command spec gaps surfaced by the run for loop 026 to address"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "If any inconsistency was found during validation, a 'Gaps' section appears in this loop's handoff_summary listing each gap (location + description) so loop 026 can address them; if no gaps, handoff explicitly states 'no schema or command gaps surfaced'"
    status: pending
    complexity: low
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Execute /phase-compact 6 end-to-end, producing a real cold artefact and hot manifest entry for the just-completed Phase 6. Validate both against locked schemas. Confirm idempotency.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-025"

  ## Success criteria
  - [ ] /phase-compact 6 executed step-by-step
  - [ ] plans/phase-completes/phase-6-complete.md produced and validates
  - [ ] PLANS-INDEX.md manifest entry appended and validates (≤8 lines)
  - [ ] Idempotency confirmed by second run + diff
  - [ ] Any gaps recorded for loop 026

  ## Required skills
  - `verification-before-completion`: Checklist-driven validation

  ## Inputs
  - Command spec: platforms/claude-code/commands/phase-compact.md (from loop 024)
  - Phase 6 plan: plans/phase-6.md
  - Phase 6 verdicts: plans/gate-verdicts/phase-6-attempt-1-*.json
  - History: .claude/state/history.jsonl
  - Git log: git log --oneline (find phase 6 commit range)
  - Locked schemas: docs/phase-complete.schema.md, docs/phase-manifest-entry.schema.md

  ## Expected outputs
  - plans/phase-completes/phase-6-complete.md
  - Updated plans/PLANS-INDEX.md (new manifest entry)

  ## Constraints
  - Phase 6 HAS real verdicts — no sentinel value needed for gate_verdict_ref.
  - The phase-6.md plan does NOT have an anchor_sha frontmatter field (Phase 6 was created before that pattern existed). Use the history.jsonl/git log inference fallback.
  - One-line bullets only in goals_met/deferred/opened.
  - Hot manifest entry MUST be ≤8 lines. Count.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-025 — phase 6 compacted end-to-end"
  2. Update handoff_summary (list any gaps for loop 026)
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
First production-path run of `/phase-compact`. Phase 6 just completed with real gate verdicts — ideal test target. This loop confirms the command works end-to-end before the agent promotion in Phase 8.

## Success Criteria
- ✓ Cold artefact + manifest entry produced
- ✓ Both validate against locked schemas
- ✓ Idempotency verified

## Skills Required

### Broad (from phase plan):
- `verification-before-completion`: Checklist validation

### Specific (refined for this loop):
- `verification-before-completion`

### Discovered (new, identified during planning):
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Command spec | `platforms/claude-code/commands/phase-compact.md` | Markdown |
| Phase 6 plan | `plans/phase-6.md` | Markdown |
| Verdicts | `plans/gate-verdicts/phase-6-attempt-1-*.json` | JSON |
| History | `.claude/state/history.jsonl` | JSONL |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Phase 6 cold artefact | `plans/phase-completes/phase-6-complete.md` | Markdown |
| Updated manifest | `plans/PLANS-INDEX.md` | Markdown |

## Dependencies

### Must Complete Before
- Loop 024: needs the command spec

### Blocked By
- Nothing else

## Complexity
**Scope**: High
**Estimated effort**: 1.5–2 hours
**Key challenges**:
1. Anchor SHA inference for Phase 6 (no frontmatter)
2. Schema validation must be checklist-driven, not vibes

---

## Ralph Loop 026: Agent Permission Template + Phase 7 Closeout

```yaml
---
name: "ralph-loop-026"
task_name: "Agent Permission Template + Phase 7 Closeout"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-026-1"
    content: "Address any gaps surfaced by loop 025 (schema or command spec patches)"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "Every gap listed in loop-025's handoff is either resolved (patch applied) or explicitly deferred with reason; relevant files (schemas or command spec) updated accordingly"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-026-2"
    content: "Document agent permission template for phase-compactor (Phase 8 enabler)"
    skill: "writing-skills"
    agent: "ralph-loop-worker"
    outcome: "A short documentation section (in platforms/claude-code/commands/phase-compact.md or a new file at platforms/claude-code/agents/README.md) describes the required tool allowlist for the future phase-compactor agent: Read, Write scoped to plans/phase-completes/ and plans/PLANS-INDEX.md, Bash scoped to git log/show, Glob, Grep; mirrors the phase-goals-agent permission pattern"
    status: pending
    complexity: low
    priority: high
  - id: "loop-026-3"
    content: "Update CLAUDE.md to reference /phase-compact under the Architecture or Commands section"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "CLAUDE.md contains a one-paragraph reference to /phase-compact under the relevant section (likely Platform Adapters or the Commands list); the entry links to platforms/claude-code/commands/phase-compact.md"
    status: pending
    complexity: low
    priority: medium
  - id: "loop-026-4"
    content: "Update plans/PLANS-INDEX.md to mark Phase 7 complete and Phase 8 ready to plan"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "plans/PLANS-INDEX.md: Phase 7 row status complete; loops 023-026 all status complete in Ralph Loops table; Compaction Programme block updated (Phase 7 complete, Phase 8 ready to plan)"
    status: pending
    complexity: low
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Close out Phase 7: patch any gaps surfaced by the end-to-end run, document the agent permission template for Phase 8, cross-reference the new command from CLAUDE.md, and update PLANS-INDEX.md.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-026"

  ## Success criteria
  - [ ] Gaps from loop 025 resolved or explicitly deferred
  - [ ] Agent permission template documented for Phase 8
  - [ ] CLAUDE.md references /phase-compact
  - [ ] PLANS-INDEX.md reflects Phase 7 complete and Phase 8 ready

  ## Required skills
  - `writing-skills`: Patches and documentation

  ## Inputs
  - Loop 025 handoff (gap list)
  - Existing CLAUDE.md
  - Existing PLANS-INDEX.md

  ## Expected outputs
  - Patched schemas / command spec (if gaps)
  - Agent permission template documentation
  - Updated CLAUDE.md
  - Updated PLANS-INDEX.md

  ## Constraints
  - Only patch gaps surfaced — no redesign
  - Permission template must be precise: list each tool with its scope

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-026 — agent template, Phase 7 complete"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

## Overview
Final loop of Phase 7. Closes the loop on gap-patching, prepares Phase 8 by documenting the agent permission template, and signals Phase 8 readiness.

## Success Criteria
- ✓ Loop 025 gaps closed
- ✓ Phase 8 agent permission template in place
- ✓ CLAUDE.md and PLANS-INDEX.md current

## Skills Required

### Broad (from phase plan):
- `writing-skills`: Documentation and patches

### Specific (refined for this loop):
- `writing-skills`

### Discovered (new, identified during planning):
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Loop 025 handoff | `phase-7-ralph-loops.md` frontmatter | YAML |
| CLAUDE.md | `CLAUDE.md` | Markdown |
| PLANS-INDEX.md | `plans/PLANS-INDEX.md` | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Permission template doc | `platforms/claude-code/agents/README.md` or within command spec | Markdown |
| CLAUDE.md update | `CLAUDE.md` | Markdown |
| PLANS-INDEX.md update | `plans/PLANS-INDEX.md` | Markdown |

## Dependencies

### Must Complete Before
- Loop 025: needs the gap list

### Blocked By
- Nothing else

## Complexity
**Scope**: Low–Medium
**Estimated effort**: 45–60 minutes
**Key challenges**:
1. Scope discipline — only patch surfaced gaps
2. Permission template precision

---

## Phase 7 Summary

| Loop | Name | Complexity | Key Output |
|------|------|------------|------------|
| 023 | Verdict Schema Extension + Agent Fix | Medium | Extended schema, fixed phase-goals-agent permissions |
| 024 | `/phase-compact` Command Implementation | High | `platforms/claude-code/commands/phase-compact.md` |
| 025 | End-to-End Run Against Phase 6 | High | `plans/phase-completes/phase-6-complete.md` + manifest entry |
| 026 | Agent Permission Template + Closeout | Low–Medium | Permission template, CLAUDE.md + PLANS-INDEX.md updates |

**Critical path:** 023 → 024 → 025 → 026 (strict sequential).

**Skill usage map:**
- `writing-skills` — used in all four loops
- `verification-before-completion` — primary skill for loop 025 (and loop 023 regression check)

**Total estimated effort:** 5–7 hours across four loops.
