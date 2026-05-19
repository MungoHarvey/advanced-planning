# Phase 10 — Ralph Loops (037–041)

`/phase-compact` Context-Compaction Reframe. Source plan:
`.advanced-plans/phases/phase-10/plan.md`. Design:
`.advanced-plans/specs/2026-05-19-phase-compact-context-compaction-design.md`.

Sequencing: 037 → 038 → 039 → 040 → 041 (strictly sequential; 039 depends on
038's schema, 040 depends on 039's command shape, 041 verifies all).

---

```yaml
---
name: "ralph-loop-037"
task_name: "Context Meter Extension"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "context_meter.py extended with segment detection, content-type breakdown, activity attribution, and --report mode; 44-test suite written and passing; AST zero-dep checker reports NONE"
  failed: ""
  needed: ""

todos:
  - id: "loop-037-1"
    content: "Add segment detection to context_meter.py (split transcript at compaction-summary boundaries; per-segment record count, time span, approx tokens)"
    skill: "NA"
    agent: "NA"
    outcome: "context_meter.py exposes a function returning per-segment [start,end,span,tok] list; manual run on live transcript prints >=1 segment"
    status: completed
    priority: high
  - id: "loop-037-2"
    content: "Add content-type breakdown (tool_use / tool_result / text / thinking / str token shares) and activity attribution buckets"
    skill: "NA"
    agent: "NA"
    outcome: "Running the meter prints a content-type table summing to ~100% and an activity-attribution table"
    status: completed
    priority: high
  - id: "loop-037-3"
    content: "Add transparency-report output mode: occupancy + how-used narrative + projected post-compaction saving; keep one-line mode as default"
    skill: "NA"
    agent: "NA"
    outcome: "`python context_meter.py --report` prints occupancy, breakdown, and a projected-saving line; default invocation still prints the single line"
    status: completed
    priority: high
  - id: "loop-037-4"
    content: "Write pytest suite test_context_meter.py: occupancy math, segment split, content-type buckets, transcript auto-detect, missing-transcript degrade"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "pytest platforms/python/tests/test_context_meter.py passes; AST zero-dep checker reports NONE for context_meter.py"
    status: completed
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Extend context_meter.py with segment/content-type/activity breakdown and a
  transparency-report mode, fully tested and zero-dependency.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-037"

  ## Success criteria
  - [ ] Segment, content-type, and activity breakdown functions implemented
  - [ ] `--report` mode prints occupancy + breakdown + projected saving
  - [ ] Default one-line mode unchanged
  - [ ] test_context_meter.py passes; AST import checker reports NONE
  - [ ] Graceful degrade when no transcript found (no exception)

  ## Required skills
  - `verification-before-completion`: assert tests + zero-dep before done

  ## Inputs
  - platforms/python/context_meter.py (exists, verified)
  - A real session transcript under ~/.claude/projects/<slug>/*.jsonl

  ## Expected outputs
  - Extended platforms/python/context_meter.py
  - platforms/python/tests/test_context_meter.py

  ## Constraints
  - Standard library only (json, pathlib, sys, argparse, typing, re, os,
    datetime) — CI AST checker enforces this
  - ASCII-only console output (Windows cp1252 safe — no em-dashes)
  - Do not modify complete.md or any LOCKED schema

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-037 — context meter extension"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

---

```yaml
---
name: "ralph-loop-038"
task_name: "Handoff Digest Schema + Generation"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "docs/phase-handoff.schema.md written (LOCKED, Validation Checklist, 7 mandatory sections); platforms/python/handoff_digest.py implemented (zero-dep, ASCII-safe, ceiling-enforced, gate-fail path); 38 tests added, 154 total passing; AST checker: only pre-existing context_meter.py __future__ flag"
  failed: ""
  needed: "Loop 039: reframe phase-compact.md command to invoke generate_handoff_digest and add transparency-report + consent-gate steps"

todos:
  - id: "loop-038-1"
    content: "Write docs/phase-handoff.schema.md: frontmatter fields, mandatory sections (incl. Errors & issues), pointers-not-contents rule, token_ceiling, validation checklist"
    skill: "NA"
    agent: "NA"
    outcome: "docs/phase-handoff.schema.md exists with a Validation Checklist; mirrors design-doc schema section"
    status: completed
    priority: high
  - id: "loop-038-2"
    content: "Implement handoff.md generation logic (from phase plan + complete.md + gate verdict + history slice) producing schema-conforming content"
    skill: "NA"
    agent: "NA"
    outcome: "Generation produces a valid .advanced-plans/phases/phase-N/handoff.md for a completed phase fixture"
    status: completed
    priority: high
  - id: "loop-038-3"
    content: "Implement token_ceiling enforcement: build fails listing offending sections if digest exceeds ceiling (no silent truncation)"
    skill: "NA"
    agent: "NA"
    outcome: "A fixture digest over ceiling causes a non-zero failure naming offending sections"
    status: completed
    priority: high
  - id: "loop-038-4"
    content: "Implement gate-fail path: status: failed_vM with non-empty Errors & issues section"
    skill: "NA"
    agent: "NA"
    outcome: "Given a fail verdict, generation yields handoff.md with status failed_vM and populated issues section"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Define the phase-handoff digest schema and implement its generation +
  ceiling enforcement + gate-fail path.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-038"

  ## Success criteria
  - [ ] docs/phase-handoff.schema.md written with validation checklist
  - [ ] Generation produces schema-conforming handoff.md for a fixture phase
  - [ ] Over-ceiling digest fails the build with offending sections listed
  - [ ] Gate-fail input yields status: failed_vM + non-empty issues section

  ## Required skills
  - `schema-design`: section/ceiling/pointer-rule definition

  ## Inputs
  - Design doc handoff.md schema section (authoritative)
  - .advanced-plans/phases/phase-9/{plan.md,complete.md} + gate verdicts (fixture)

  ## Expected outputs
  - docs/phase-handoff.schema.md
  - Generation + validation logic (zero-dep helper module or command-embedded;
    decide and record which)

  ## Constraints
  - Pointers + one-liners only, never pasted file contents
  - Standard library only if implemented in Python; CI AST enforced
  - complete.md + docs/phase-complete.schema.md + docs/phase-manifest-entry.schema.md
    remain byte-unchanged

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-038 — handoff schema + generation"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

---

```yaml
---
name: "ralph-loop-039"
task_name: "Command Reframe"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "phase-compact.md extended with steps 13-16: handoff.md generation via handoff_digest.py, transparency report via context_meter --report, idempotent CLAUDE.md ## Compaction Instructions maintenance, AskUserQuestion consent gate + ready /compact line + closing summary (never self-compacts); steps 1-12 byte-intact (zero removed lines in git diff)"
  failed: ""
  needed: "Loop 040: write PreCompact hook script + register in hooks.json/settings.json + add persistent ## Compaction Instructions block + decision-log entry to CLAUDE.md"

todos:
  - id: "loop-039-1"
    content: "Reframe platforms/claude-code/commands/phase-compact.md: keep steps 1-12 byte-intact; add step to write+validate handoff.md after complete.md"
    skill: "NA"
    agent: "NA"
    outcome: "phase-compact.md steps 1-12 unchanged; new write-handoff step present and ordered after complete.md write"
    status: completed
    priority: high
  - id: "loop-039-2"
    content: "Add transparency-report step invoking context_meter.py --report (what/how/projected-saving)"
    skill: "NA"
    agent: "NA"
    outcome: "Command step runs context_meter --report and presents occupancy + breakdown + projection"
    status: completed
    priority: high
  - id: "loop-039-3"
    content: "Add step to maintain CLAUDE.md ## Compaction Instructions block (rewrite pointing at current phase handoff.md)"
    skill: "NA"
    agent: "NA"
    outcome: "Command step idempotently rewrites the CLAUDE.md block; running twice yields one block"
    status: completed
    priority: high
  - id: "loop-039-4"
    content: "Add AskUserQuestion consent gate + ready /compact line handoff + closing summary (never self-compacts; order invariant)"
    skill: "NA"
    agent: "NA"
    outcome: "Command ends with consent gate; on yes presents ready /compact line; closing states context not yet compacted"
    status: completed
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Reframe phase-compact.md to write the handoff digest, report context
  transparently, maintain the CLAUDE.md policy block, and run a consent gate.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-039"

  ## Success criteria
  - [ ] Steps 1-12 of phase-compact.md byte-unchanged (git diff scoped)
  - [ ] handoff.md write+validate step added after complete.md
  - [ ] Transparency report step via context_meter --report
  - [ ] Idempotent CLAUDE.md ## Compaction Instructions maintenance step
  - [ ] AskUserQuestion consent gate + ready /compact line + closing summary
  - [ ] Order invariant documented: artefacts validated before any guidance

  ## Required skills
  - `command-rewriting`: step-sequence edit preserving existing steps

  ## Inputs
  - platforms/claude-code/commands/phase-compact.md (existing)
  - context_meter.py --report (Loop 037), handoff schema (Loop 038)
  - Design doc flow section (authoritative)

  ## Expected outputs
  - Reframed platforms/claude-code/commands/phase-compact.md

  ## Constraints
  - Command never self-invokes /compact (impossible + forbidden)
  - Do not alter steps 1-12 or any LOCKED schema/complete.md

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-039 — command reframe"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

---

```yaml
---
name: "ralph-loop-040"
task_name: "PreCompact Hook + CLAUDE.md Policy"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-040-1"
    content: "Write PreCompact hook script: validate latest handoff.md, emit retention note naming digest + CLAUDE.md block, no-op if no handoff.md, always exit 0"
    skill: "NA"
    agent: "NA"
    outcome: "Hook script exists; simulated invocation with and without a handoff.md both exit 0; never emits a blocking decision"
    status: pending
    priority: high
  - id: "loop-040-2"
    content: "Register PreCompact hook in platforms/claude-code/hooks/hooks.json and settings.json"
    skill: "permission-config"
    agent: "NA"
    outcome: "hooks.json + settings.json contain a valid PreCompact entry pointing at the script; JSON parses"
    status: pending
    priority: high
  - id: "loop-040-3"
    content: "Add persistent ## Compaction Instructions block to CLAUDE.md (tuned retention policy, generalised phase-pointer form)"
    skill: "NA"
    agent: "NA"
    outcome: "CLAUDE.md contains ## Compaction Instructions with the retention policy text"
    status: pending
    priority: high
  - id: "loop-040-4"
    content: "Add Phase 10 decision-log entry to CLAUDE.md per the design doc"
    skill: "NA"
    agent: "NA"
    outcome: "CLAUDE.md decision log records the phase-compact reframe decision"
    status: pending
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Add the PreCompact freshness hook (never blocks) and the persistent CLAUDE.md
  compaction policy + decision log.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-040"

  ## Success criteria
  - [ ] PreCompact hook script: validates latest handoff.md, no-ops if absent,
        always exits 0, never blocks compaction
  - [ ] Registered in hooks.json + settings.json; JSON valid
  - [ ] CLAUDE.md ## Compaction Instructions block present
  - [ ] CLAUDE.md decision-log entry added

  ## Required skills
  - `permission-config`: hooks.json / settings.json wiring

  ## Inputs
  - Design doc PreCompact + CLAUDE.md sections (authoritative)
  - platforms/claude-code/hooks/hooks.json, platforms/claude-code/settings.json

  ## Expected outputs
  - PreCompact hook script under platforms/claude-code/hooks/
  - Updated hooks.json, settings.json, CLAUDE.md

  ## Constraints
  - Hook MUST exit 0 on every path; never emit a blocking decision
  - If implemented in Python, stdlib only (CI AST enforced)
  - complete.md + both LOCKED schemas byte-unchanged

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-040 — PreCompact hook + CLAUDE.md policy"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

---

```yaml
---
name: "ralph-loop-041"
task_name: "Verification + End-to-End"
max_iterations: 3
on_max_iterations: checkpoint

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-041-1"
    content: "Run full pytest suite + AST zero-dep checker; assert all green across supported Python versions"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "python -m pytest platforms/python/tests/ -v passes; AST checker reports NONE"
    status: pending
    priority: high
  - id: "loop-041-2"
    content: "Assert complete.md + docs/phase-complete.schema.md + docs/phase-manifest-entry.schema.md byte-unchanged across the phase (git diff against phase anchor)"
    skill: "NA"
    agent: "NA"
    outcome: "git diff 6384f80..HEAD -- those three paths is empty"
    status: pending
    priority: high
  - id: "loop-041-3"
    content: "End-to-end dry run: run reframed /phase-compact logic on a completed phase, verify report numbers vs context_meter, verify handoff.md within ceiling, verify CLAUDE.md block + PreCompact present"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Dry run produces a valid handoff.md, accurate transparency report, and a ready /compact line; documented in loop handoff"
    status: pending
    priority: high
  - id: "loop-041-4"
    content: "Confirm gate-fail path and ceiling-fail test both behave per design; update docs/tool-friction-log.md with any friction observed this phase"
    skill: "NA"
    agent: "NA"
    outcome: "Both negative paths verified; friction log appended if applicable"
    status: pending
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Verify the full Phase 10 reframe end-to-end and prove the LOCKED invariants
  held.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-041"

  ## Success criteria
  - [ ] Full pytest + AST zero-dep green
  - [ ] complete.md + both LOCKED schemas byte-unchanged (git diff empty)
  - [ ] E2E dry run yields valid handoff.md + accurate report + ready /compact line
  - [ ] Gate-fail and ceiling-fail negative paths verified
  - [ ] Friction log updated if anything was observed

  ## Required skills
  - `verification-before-completion`: evidence-backed sign-off

  ## Inputs
  - All Phase 10 outputs (Loops 037-040)
  - A completed phase for the e2e dry run (e.g. phase-9)

  ## Expected outputs
  - Verification evidence captured in this loop's handoff_summary
  - Optional appended docs/tool-friction-log.md entry

  ## Constraints
  - This loop must not modify production logic except trivial test-only fixes;
    real defects escalate (checkpoint) rather than silent patch

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-041 — verification + e2e"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```
