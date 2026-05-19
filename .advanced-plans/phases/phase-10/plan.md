---
phase: 10
name: "/phase-compact Context-Compaction Reframe"
status: draft
loops: [037, 038, 039, 040, 041]
design_spec: .advanced-plans/specs/2026-05-19-phase-compact-context-compaction-design.md
anchor_sha: 6384f80
---

# Phase 10: /phase-compact Context-Compaction Reframe

## Objective

Reframe `/phase-compact` from a terse-artefact writer into a conversation-context
compaction system, so any model can resume after a phase from a small fresh digest
without re-reading files and without context bloat.

## Scope

### Included
- Extend `platforms/python/context_meter.py`: segment / content-type / activity
  breakdown + transparency-report output (occupancy, how used, projected saving),
  zero-dep, with pytest coverage
- New per-phase resume digest `.advanced-plans/phases/phase-N/handoff.md` —
  schema doc + generation logic + hard `token_ceiling` enforcement (build fails
  if exceeded) + mandatory errors/issues section + gate-fail (`failed_vM`) path
- Reframe `platforms/claude-code/commands/phase-compact.md`: keep existing
  steps 1–12 (unchanged `complete.md`), add write-handoff, transparency report,
  maintain CLAUDE.md `## Compaction Instructions`, `AskUserQuestion` consent
  gate, ready `/compact` line handoff, closing summary
- Persistent `## Compaction Instructions` block in `CLAUDE.md` (tuned retention
  policy steering manual + auto compaction) + decision-log entry
- `PreCompact` hook (`hooks.json` + `settings.json` + hook script): validates
  latest `handoff.md`, emits retention note, no-ops pre-first-gate, never blocks
  compaction
- End-to-end verification on a completed phase; tests for all new logic

### Explicitly NOT included
- Programmatic / automatic `/compact` invocation (proven impossible — design
  accounts for this; consent + ready-to-run handoff is the maximum)
- `/clear`-based flow (explicitly rejected)
- Changes to `complete.md` or `docs/phase-complete.schema.md` /
  `docs/phase-manifest-entry.schema.md` (remain LOCKED, untouched)
- Backfill of `handoff.md` for historical Phases 1–9 (applies from next phase on)
- `run-closeout` / `progress-report` consuming `handoff.md` (future phase)

## Key Deliverables

| Deliverable | Format | Location |
|---|---|---|
| Extended context meter + breakdown | Python | `platforms/python/context_meter.py` |
| Context-meter tests | Python (pytest) | `platforms/python/tests/test_context_meter.py` |
| Handoff digest schema | Markdown | `docs/phase-handoff.schema.md` |
| Handoff generation + ceiling validation | (logic in command + helper) | `platforms/claude-code/commands/phase-compact.md` (+ helper if needed) |
| Reframed command | Markdown | `platforms/claude-code/commands/phase-compact.md` |
| Compaction Instructions block + decision log | Markdown | `CLAUDE.md` |
| PreCompact hook | Shell/Python + JSON | `platforms/claude-code/hooks/` , `hooks.json`, `settings.json` |
| Per-phase resume digest (produced at gate pass) | Markdown | `.advanced-plans/phases/phase-N/handoff.md` |

## Success Criteria

- ✓ `context_meter.py` emits the one-line occupancy AND a segment/content-type/
  activity breakdown; degrades gracefully when no transcript is found; pytest
  suite for it passes; AST zero-dep checker reports NONE
- ✓ `docs/phase-handoff.schema.md` exists defining the digest (frontmatter,
  mandatory sections incl. errors/issues, pointers-not-contents rule,
  `token_ceiling`)
- ✓ Reframed `phase-compact.md` produces `handoff.md` within `token_ceiling`,
  presents the transparency report, maintains the CLAUDE.md block, runs the
  `AskUserQuestion` consent gate, and emits a ready `/compact` line — verified
  by a dry run on a completed phase
- ✓ Digest over ceiling fails the build with offending sections listed (no
  silent bloat) — verified by a fixture test
- ✓ Gate-fail input yields `handoff.md` with `status: failed_vM` and a
  non-empty errors/issues section
- ✓ `CLAUDE.md` contains a `## Compaction Instructions` block and a decision-log
  line; `complete.md` and both LOCKED schemas are byte-unchanged (git diff empty)
- ✓ `PreCompact` hook registered in `hooks.json` + `settings.json`; on a
  simulated compaction it validates the latest `handoff.md` and exits zero
  (never blocks); no-ops cleanly when no `handoff.md` exists
- ✓ `python -m pytest platforms/python/tests/ -v` passes across supported
  versions; CI green
- ✓ End-to-end: run reframed `/phase-compact` on a completed phase, run the
  emitted `/compact`, confirm resumed context carries the digest, not raw I/O

## Dependencies

### Must Complete Before
- **Phase 9 gate pass + closeout**: complete (gate PASSED attempt 2; artefacts
  committed `19199d3`/`6384f80`). State bus shows no in-flight `loop-ready.json`.
- **Approved design doc**: `.advanced-plans/specs/2026-05-19-phase-compact-context-compaction-design.md` (user-approved).

### Blocked By
- None external

### Optional
- `context_meter.py` already exists and is verified — reduces Loop 037 scope to
  extension + tests rather than greenfield

## Skills Required (Broad Categories)

- `python-refactor`: extend `context_meter.py` preserving zero-dependency invariant
- `schema-design`: `phase-handoff.schema.md` (sections, ceiling, pointer rule)
- `command-rewriting`: reframe `phase-compact.md` step sequence + handoff/consent
- `permission-config`: `PreCompact` hook wiring in `hooks.json` / `settings.json`
- `docs-rewrite`: CLAUDE.md `## Compaction Instructions` + decision log
- `verification-before-completion`: ceiling/gate-fail/hook dry-run + e2e checks

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Digest ceiling too tight to carry resume signal | Med | Med | Ceiling configurable in schema; tune against a real phase in the e2e loop before lock |
| PreCompact hook accidentally blocks compaction | Low | High | Hook must exit 0 on all paths; explicit test that a failing hook does not block; never use blocking exit codes |
| Transcript format / usage block changes across CC versions | Low | Med | `context_meter` already tolerant (missing-field defaults, graceful degrade); add a fixture test on a captured transcript |
| Accidental edit to LOCKED complete.md/schemas | Low | High | Success criterion asserts byte-unchanged via git diff; loop instructions forbid touching them |
| Zero-dep invariant broken by extension | Low | High | AST import checker in CI; success criterion re-asserts NONE |
| Mid-phase auto-compact has no digest | Med | Low | Accepted degraded mode in design; CLAUDE.md block still steers; loop-level handoffs remain on disk |

## Assumptions

- **`context_meter.py` transcript parsing remains valid**: verified this session
  against the live transcript; validated again by a fixture test in Loop 037.
- **Single primary user, big-bang reframe is safe**: consistent with the
  programme's established model; no external consumers of `phase-compact.md`.
- **CLAUDE.md is always in context**: basis for the `## Compaction Instructions`
  lever; true for Claude Code project instructions.
- **`PreCompact` hook fires before manual and auto compaction**: per Claude Code
  hook docs; validated by the hook dry-run in Loop 040.

## Notes / Design Decisions

- Approach A (two-tier) chosen over unlocking `complete.md` or a rolling log —
  see design doc rationale; lowest risk, framework-consistent (phase-level
  analogue of the loop `done/failed/needed` handoff).
- Programmatic `/compact` confirmed impossible via claude-code-guide
  investigation; design's value is making *every* compaction (manual + auto)
  obey one policy and resume from a fresh digest.
- `complete.md` deliberately retained unchanged as the git-navigation layer
  after explicit investigation of its original purpose.
- Open question for ralph-loop-planner: whether handoff generation logic lives
  inline in the command or in a small zero-dep helper module (Loop 038/039
  boundary) — decide at decomposition.

## Ralph Loops (5)

| Loop | Name | Type | Key Outputs |
|---|---|---|---|
| 037 | Context Meter Extension | Implementation | `context_meter.py` segment/content-type/activity breakdown + transparency output; pytest suite; zero-dep verified |
| 038 | Handoff Digest Schema + Generation | Design + Implementation | `docs/phase-handoff.schema.md`; digest generation + `token_ceiling` enforcement; gate-fail path |
| 039 | Command Reframe | Implementation | Reframed `phase-compact.md` (steps 1–12 intact + handoff/report/consent/handoff line/closing) |
| 040 | PreCompact Hook + CLAUDE.md Policy | Implementation | `PreCompact` hook + `hooks.json`/`settings.json` wiring; CLAUDE.md `## Compaction Instructions` + decision log |
| 041 | Verification + End-to-End | Verification | Ceiling/gate-fail/hook tests; full pytest + CI green; e2e dry run on a completed phase |
