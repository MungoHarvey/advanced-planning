---
phase: 11
name: "Friction Remediation & v0.x Pre-Release"
status: draft
loops: [042, 043, 044, 045, 046]
design_spec: .advanced-plans/specs/2026-05-20-phase-11-friction-remediation-design.md
anchor_sha: 1bb073c
target_release: v0.11.0
---

# Phase 11: Friction Remediation & v0.x Pre-Release

## Objective

Resolve the highest-impact tool-friction-log entries (correctness / foundation
layer) and bootstrap a version scheme so the framework can cut its first tagged
pre-release `v0.11.0`. v1 is deferred; Phase 12 will address workflow / auto-chain
seams on top of this clean foundation.

## Scope

### Included
- Single source of truth for the zero-dep AST allow-set: `core/constraints.json`
  + `platforms/python/ast_check.py` (stdlib-only reader); CI shells out to it
- Drop the `complexity:` field everywhere; drop the Haiku tier from CLAUDE.md
  Model Tiers (the framework never tested Haiku routing in anger)
- Install missing skill stubs (`core/skills/schema-design`,
  `core/skills/permission-config`) + worker preflight warning for declared
  skills that don't resolve
- Add `Write` tool to `phase-goals-agent` so it can persist its own verdict;
  fallback path scoped if runtime propagation doesn't apply
- `plan-subagent-identification` defaults `agent: NA`; reserve
  `ralph-loop-worker` so it can never appear as a per-todo agent; sweep
  existing offenders in `.advanced-plans/phases/**`
- Migration-consistency audit: case-by-case review of all command / agent /
  skill / doc files for stale path directives; rewrite to `.advanced-plans/`;
  publish `docs/path-conventions.md` as the canonical path map
- `/next-loop` resume-detection (Loop-035 regression) and orchestrator
  stale-state cleanup at phase boundary
- Self-install support for the framework's own source repo (idempotent
  skip-data-scaffold guard against existing `.advanced-plans/`)
- Version-scheme bootstrap: `VERSION` file, `CHANGELOG.md` covering
  v0.6–v0.11, annotated tag `v0.11.0` cut on gate pass, GitHub Release
  body sourced from the CHANGELOG
- End-to-end verification of the three highest-risk items (S5, S8, S10)
  bundled in Loop 046 with explicit fallback handling for S5

### Explicitly NOT included
- **Auto-chain seams** (`phase-plan-creator` → `ralph-loop-planner`;
  `/next-loop --auto` → gate). Phase 12.
- **Three-artefact drift mitigation** (spec / phase plan / index sync). Phase 12.
- **Checkpoint-commit conflation guard** (`/next-loop` refusing dirty unrelated
  changes). Phase 12.
- **`handoff.md` backfill for historical Phases 1–9**. Permanently deferred
  (Phase 10 established forward-only).
- **Harness-level frictions** (Write/Read/AskUserQuestion caps, system
  reminders, skill loading verbosity, brainstorming HARD-GATE softening).
  Permanently deferred, upstream.
- **v1 declaration**. Pushed to a later phase after Phase 12 + stability runway.
- **Package registry publish (PyPI / npm)**. Not applicable for zero-dep
  Python + shell + markdown; GitHub Releases off the tag is sufficient.
- **Retroactive CI for command-body path audit** on prior phases. One-shot
  sweep at S7 covers current state; CI guard deferred to Phase 12.

## Key Deliverables

| Deliverable | Format | Location |
|---|---|---|
| Zero-dep allow-set source of truth | JSON | `core/constraints.json` |
| Shared AST reader (stdlib-only) | Python | `platforms/python/ast_check.py` |
| AST reader tests | Python (pytest) | `platforms/python/tests/test_ast_check.py` |
| Skill stubs | Markdown | `core/skills/schema-design/SKILL.md`, `core/skills/permission-config/SKILL.md` |
| Worker preflight warning | Edit | `core/agents/ralph-loop-worker.md` (+ runtime mirror) |
| phase-goals-agent +Write | Edit | `platforms/claude-code/agents/phase-goals-agent.md` |
| /run-gate cleanup | Edit | `platforms/claude-code/commands/run-gate.md` |
| plan-subagent-identification NA default | Edit | `~/.claude/skills/plan-subagent-identification/SKILL.md` (+ core mirror) |
| Canonical path map | Markdown | `docs/path-conventions.md` |
| /next-loop resume detection | Edit | `platforms/claude-code/commands/next-loop.md` |
| Orchestrator stale-state cleanup | Edit | `core/agents/ralph-orchestrator.md` |
| Self-install idempotency | Edit | `setup/claude-code/install.sh`, `install.ps1` |
| Dev-mode docs | Markdown | `CONTRIBUTING.md` (new) or CLAUDE.md addendum |
| Version scheme | Text | `VERSION` |
| Changelog | Markdown | `CHANGELOG.md` |
| README installation pointer | Edit | `README.md` |
| Phase 11 decision-log entry | Markdown | `CLAUDE.md` |

## Success Criteria

- ✓ `core/constraints.json` exists; `platforms/python/ast_check.py` exists
  with `load_allowed_imports()` + `check_file()` + CLI mode; CI workflow
  shells out to `python -m platforms.python.ast_check`; round-trip test
  confirms JSON and reader produce identical sets; pytest passes
- ✓ Zero `complexity:` matches under `.advanced-plans/phases/**` and
  `core/schemas/`; CLAUDE.md Model Tiers table no longer contains a Haiku
  row; CHANGELOG.md documents the schema break
- ✓ `core/skills/schema-design/SKILL.md` and
  `core/skills/permission-config/SKILL.md` exist with all mandatory sections;
  install script copies them to `.claude/skills/`
- ✓ Worker preflight check: a fixture with a non-existent declared skill
  produces a visible warning and proceeds; tests cover this
- ✓ **PRIMARY** `phase-goals-agent` writes its own verdict file in the
  Loop 046 E2E dry-run; `/run-gate` no longer documents the text-only
  workaround. **FALLBACK** (if Write doesn't propagate at runtime):
  `/run-gate` formally documents the main-thread persist-on-behalf
  contract and the friction entry is marked partially-resolved
  (upstream-blocked)
- ✓ Zero `agent: ralph-loop-worker` on todos under
  `.advanced-plans/phases/**`; `plan-subagent-identification` documents
  `NA` as default and reserves `ralph-loop-worker` as the loop executor
- ✓ Migration-consistency audit complete: `docs/path-conventions.md`
  exists with the canonical path map; all command, agent, skill, doc files
  case-by-case reviewed; stale directives rewritten to `.advanced-plans/`
- ✓ `/next-loop` resume-detection: regression fixture (loop-ready newer
  than loop-complete + dirty tree) triggers `resume-review` invocation
  before orchestrator spawn (mandatory IRON-RULE regression test)
- ✓ Orchestrator stale-state cleanup: simulated cross-phase
  `loop-ready.json` is archived (not consumed) on next orchestrator
  startup
- ✓ Dogfood self-install: running install on this repo preserves existing
  `.advanced-plans/` byte-unchanged AND populates `.claude/` runtime dirs;
  `/loop-status` exits cleanly from the source repo
- ✓ `VERSION` file exists (`0.11.0`); `CHANGELOG.md` covers v0.6–v0.11
  with one heading per PLANS-INDEX phase and matching loop counts;
  annotated tag `v0.11.0` cut on gate pass; remote pushed; GitHub Release
  created off the tag with body sourced from CHANGELOG
- ✓ All existing tests still pass (154 pre-Phase-11); new tests added per
  S1, S4, S6, S8, S9, S10 succeed; AST zero-dep check NONE
- ✓ LOCKED files byte-unchanged: `docs/phase-complete.schema.md`,
  `docs/phase-manifest-entry.schema.md`, `docs/phase-handoff.schema.md`,
  `.advanced-plans/phases/phase-9/complete.md`

## Dependencies

### Must Complete Before
- **Phase 10 gate pass**: complete (PASSED attempt 1; both verdicts
  committed `e881997`). State bus has no in-flight `loop-ready.json`.
- **Approved design doc**: `.advanced-plans/specs/2026-05-20-phase-11-friction-remediation-design.md`
  (user-approved; eng-reviewed; committed `1bb073c`).

### Blocked By
- None external. Phase-goals-agent runtime tool propagation is a known
  risk but has a scoped fallback in S5 success criterion.

### Optional
- Pushing `origin/main` before starting Phase 11 reduces remote drift
  (49 commits ahead pre-Phase-11). Not required.

## Skills Required (Broad Categories)

- `python-refactor`: extract / build `ast_check.py` preserving zero-dependency invariant
- `schema-design`: skill stubs + `docs/path-conventions.md`
- `permission-config`: agent tool-set edits + install-script idempotency
- `command-rewriting`: `/next-loop` resume-detection step + `/run-gate` cleanup
- `docs-rewrite`: CHANGELOG backfill + README + CLAUDE.md decision log
- `verification-before-completion`: Loop 046 E2E checks for S5/S8/S10 + tag-cut

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **S5 Write-tool edit no-op at runtime** | Med | Med | Loop 046 E2E catches it; fallback path scoped in success criterion |
| Dropping `complexity:` + Haiku breaks user routing | Low | Low | No external users yet; CHANGELOG documents break |
| Self-install symlink semantics differ on Windows | Med | Low | `install.ps1` uses junction; CI smoke on both platforms |
| Self-install corrupts existing `.advanced-plans/` data | Med | High | Idempotent skip-data-scaffold (S10); unit + E2E test |
| `constraints.json` drift across loops | Low | Med | S1 round-trip test; CI shells out to shared reader |
| CHANGELOG backfill drifts from PLANS-INDEX | Med | Low | S11 explicit completeness criterion at gate review |
| Migration audit misses stale directive | Low | Med | Case-by-case review across 4 directories; canonical doc captures intent |

## Assumptions

- **Sonnet is sufficient for all worker invocations**: validated by Phases 1–10;
  the Haiku tier was a planning concept never tested in anger.
- **`phase-goals-agent.md` is read at agent-spawn time**: assumption for S5
  primary path; explicitly checked in Loop 046 E2E with fallback if false.
- **Install script can detect repo root reliably**: `git rev-parse --show-toplevel`
  is the canonical check (already used elsewhere in the framework).
- **GitHub Releases generation from a tag is sufficient distribution**: no
  external user expects PyPI / npm; install remains shell-driven.
- **CLAUDE.md is always in context**: continues from Phase 10; basis for
  decision-log additions and Model Tiers edits to take effect.

## Notes / Design Decisions

- 9 friction-log entries resolved this phase. Phase 12 will address the
  remaining workflow seams (skill chaining, `/next-loop --auto` → gate,
  checkpoint conflation, three-artefact drift).
- v0.11.0 is the first tagged pre-release; tag minor-version-per-phase
  going forward (v0.12 = Phase 12, etc.); v1 is a separate decision
  after Phase 12 + stability runway.
- Per-spec /plan-eng-review: 5 loops retained (slight imbalance but each
  loop has a single concern; matches Phase 10 sizing which gate-passed
  cleanly). Loop 046 carries Verification Plan + tag-cut.
- S5 is the highest-risk item — Write-tool runtime propagation is
  unverified; fallback re-scopes to "document workaround" without
  blocking the phase.

## Ralph Loops (5)

| Loop | Name | Type | Key Outputs |
|---|---|---|---|
| 042 | Constraints + Schema Cleanup | Implementation | `core/constraints.json`; `platforms/python/ast_check.py` + tests; drop `complexity:` + Haiku tier; CLAUDE.md edits; CI shells out to ast_check |
| 043 | Skills + Agents | Implementation | Skill stubs (schema-design, permission-config); worker preflight warning; phase-goals-agent +Write tool (in-file edit); plan-subagent-identification NA default + sweep of existing offenders |
| 044 | Migration Audit + Durability | Implementation | `docs/path-conventions.md`; case-by-case audit of commands/agents/skills/docs; rewrite stale directives; `/next-loop` resume-detection step; orchestrator stale-state cleanup |
| 045 | Dogfood Self-Install | Implementation | Idempotent install.sh / .ps1; CONTRIBUTING.md (or CLAUDE.md addendum) for dev-mode invocation |
| 046 | Verification + v0.11.0 Release | Verification + Release | Loop 046 E2E checks (S5/S8/S10 per spec Verification Plan); VERSION file; CHANGELOG.md backfilled v0.6–v0.11; README.md install link; full pytest + AST NONE; annotated tag `v0.11.0` at gate pass; GitHub Release body from CHANGELOG |
