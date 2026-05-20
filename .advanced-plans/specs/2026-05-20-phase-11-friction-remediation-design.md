---
title: "Phase 11 — Friction Remediation & v0.x Pre-Release"
date: 2026-05-20
status: draft
target_phase: 11
target_release: v0.x (first tagged pre-release; v1 deferred)
predecessor: .advanced-plans/specs/2026-05-19-phase-compact-context-compaction-design.md
friction_source: docs/tool-friction-log.md
---

# Phase 11 — Friction Remediation & v0.x Pre-Release

## Problem

`docs/tool-friction-log.md` accumulates ~25 entries spanning Phases 8–10. The
framework now passes its own gate reviews end-to-end (Phase 10 complete), but
several documented frictions block confident operator use and would embarrass
the framework on external eyes. The repo is 49 commits ahead of `origin/main`
with no tags and no version artefacts — a pre-release tag is overdue.

Phase 11 fixes the highest-impact frictions (correctness / foundation layer),
bootstraps a version scheme, and ships **v0.x** as the first tagged
pre-release. Phase 12 will address the workflow/auto-chain seams on top of
this clean foundation; v1 is deferred until both phases plus stability work
are done.

## Goals

- Single source of truth for CI/AST constraints (`core/constraints.json`)
- Schema integrity: drop the ill-defined `complexity:` field; align all
  references
- Skill discovery integrity: install missing skill stubs; worker preflight
  warning when a declared skill isn't installed
- Agent capability integrity: `phase-goals-agent` can persist its own verdict;
  `plan-subagent-identification` defaults to `NA` (no self-reference)
- Command-body integrity: CI assertion that no slash-command file contains
  pre-restructure path tokens
- Worker durability: `/next-loop` detects mid-loop death and stale state from
  prior phases before spawning the next agent
- Dogfood-clean: install script can self-install into the source repo so the
  live command surface is testable from this directory
- Version scheme bootstrap: `VERSION`, `CHANGELOG.md`, `v0.x` git tag at gate
  pass

## Non-Goals

- **Auto-chain seams** (phase-plan-creator → ralph-loop-planner;
  `/next-loop --auto` → gate). Deferred to Phase 12.
- **Three-artefact drift mitigation** (spec/phase plan/index sync). Deferred.
- **Checkpoint-commit conflation guard** (`/next-loop` refusing dirty unrelated
  changes). Deferred to Phase 12 alongside auto-chain.
- **Harness-level frictions** (Write/Read/AskUserQuestion caps, system
  reminders, skill-loading verbosity). Upstream Claude Code — out of scope
  permanently.
- **`brainstorming` skill HARD-GATE softening.** Upstream skill author.
- **v1 declaration.** Pushed to a later phase.
- **Backfill of `handoff.md` for historical Phases 1–9.** Phase 10 already
  established forward-only application.

## Scope Items (11)

Each is a discrete deliverable. Loop decomposition will group these into
~4–5 ralph loops.

### S1. `core/constraints.json` + `platforms/python/ast_check.py`

Single machine-readable source of truth for the zero-dep allow-set
(`json`, `pathlib`, `re`, `datetime`, `typing`, `os`, `sys`, `tempfile`,
`textwrap`, `argparse`, `asyncio` — `__future__` explicitly NOT included).

- `core/constraints.json` holds the allow-set
- `platforms/python/ast_check.py` (NEW, stdlib-only) exposes
  `load_allowed_imports()` and `check_file(path) -> list[Violation]`; supports
  `python -m platforms.python.ast_check <paths...>` CLI mode
- `.github/workflows/ci.yml` AST job shells out to
  `python -m platforms.python.ast_check platforms/python/`; no inline
  Python in the workflow
- Workers and any future loop AST check import the module directly
- CLAUDE.md "Key Constraints" section references `core/constraints.json`
  as authoritative
- Tests: lint the JSON, unit tests on `check_file` (happy path + violation
  fixture with `__future__`), plus a round-trip test that
  `load_allowed_imports()` and the JSON file produce identical sets

### S2. Drop `complexity:` field AND drop Haiku tier

- Remove all `complexity:` references from `CLAUDE.md`
- Remove the **Haiku row** from the Model Tiers table in `CLAUDE.md`
  entirely — the framework never tested Haiku routing in anger and the
  affordance was driven by the ill-defined `complexity` field. All
  worker invocations use Sonnet.
- Remove from `core/schemas/ralph-loop.schema.md` if present; reaffirm
  canonical order `id/content/skill/agent/outcome/status/priority`
- Sweep `.advanced-plans/phases/**` for stale `complexity:` lines; remove
- Add CI grep guard: zero `complexity:` matches in `.advanced-plans/phases/`
  loop files or schema docs
- Note in CHANGELOG (breaking schema change for any external user, of which
  there are none yet)

### S3. Install missing skill stubs

- Create `core/skills/schema-design/SKILL.md` with the standard sections
  (When to Use / Process / Output Format) — minimal but real
- Create `core/skills/permission-config/SKILL.md` similarly
- Update install script to copy/symlink them to runtime `.claude/skills/`
- Existing loops 038 and 040 (which declared these skills and fell back) get
  a retroactive note in their handoff sections — non-blocking

### S4. Worker preflight skill check

- `ralph-loop-worker`: at the start of each todo, resolve the declared
  `skill:` field. If skill not found at `core/skills/<name>/SKILL.md` or
  `.claude/skills/<name>/SKILL.md` (or `~/.claude/skills/<name>/SKILL.md`),
  log a visible warning to execution.log and to stdout
- Warning format: `WARN: skill '<name>' declared by todo <id> but not
  installed; proceeding without skill injection`
- Do NOT halt — fallback (use design doc / context) remains the behaviour

### S5. `phase-goals-agent` Write tool

- Update `platforms/claude-code/agents/phase-goals-agent.md` tools field:
  `Read, Glob, Grep, Write` (mirror `code-review-agent`)
- The `gate-review-mode` sentinel already restricts writes to
  `.advanced-plans/` so scope is safe
- Update `/run-gate` command file to remove the "expect text-only verdict"
  workaround prose; agent now persists its own verdict per the state-bus
  contract

**Runtime-propagation risk (must verify in Loop 046 E2E):** It is not
confirmed that editing the agent definition file updates Claude Code's
runtime tool set. If E2E shows the Write tool is still unavailable after
the edit, S5 is re-scoped to **"document the workaround in `/run-gate`"**
(formalise the main-thread persist-on-behalf pattern as the supported
contract) and the friction-log entry is marked partially-resolved with
upstream-blocked status.

### S6. `plan-subagent-identification` default = `NA`

- Update the skill so the default for a todo with no clear specialised agent
  is `agent: NA`, not `agent: ralph-loop-worker`
- Add an explicit "Reserved values" note: `ralph-loop-worker` is the loop
  executor and MUST NOT appear as `agent:` on individual todos
- Sweep existing `.advanced-plans/phases/**` for `agent: ralph-loop-worker`
  on todos; rewrite to `NA` (Phase 8 Loop 027 is the known offender)

### S7. Migration-consistency audit (path-directive integrity)

Reframed from "ban old paths via regex" to a positive integrity check.
The goal is to ensure the framework consistently directs Claude (and the
operator) to `.advanced-plans/` for planning data, and that no stale
directive misdirects to a path that no longer holds the truth.

- One-off audit pass over `platforms/claude-code/commands/**`,
  `platforms/claude-code/agents/**`, `core/skills/**`, `docs/**`, and
  `CLAUDE.md`:
  - List every reference to `plans/`, `.claude/plans/`, `.claude/state/`,
    `plans/gate-verdicts/`, `/new-loop` (the pre-restructure tokens)
  - For each occurrence, decide case-by-case: keep (legitimate runtime
    `.claude/` reference inside an installed-project context), or rewrite
    to `.advanced-plans/`
  - Rewrite the offenders identified by case-by-case review (Phase 9 Loop
    036 audit caught most data references but imperative step text in
    `/run-gate` and `/next-phase` is known to still carry stale tokens
    per friction-log 2026-05-18)
- Document the canonical path map in a new short doc
  `docs/path-conventions.md` (or in CLAUDE.md's existing Runtime
  Directory section) so future commands/agents have one place to
  reference rather than restating literal paths
- No CI ban regex this phase — the friction log's "single source of
  truth for state-bus paths" suggestion (2026-05-18) is captured here as
  the doc, with a CI guard deferred to Phase 12 once the conventions
  doc has settled

### S8. Worker durability — `/next-loop` resume detection

- Step 3 of `/next-loop` (before spawning orchestrator) adds a check:
  - If `loop-ready.json` mtime > `loop-complete.json` mtime AND working tree
    is dirty → invoke `resume-review` skill automatically and require
    operator acknowledgment before continuing
  - If either file is missing or both are stale (older than 24h) → log and
    proceed
- Detects the Loop 035 failure mode (worker dies, state bus silently stale)
- Does NOT change auto-chain behaviour when state is clean
- **Mandatory regression test (IRON RULE)**: fixture that creates a
  loop-ready.json with mtime newer than loop-complete.json plus a dirty
  working tree; assert `/next-loop` invokes `resume-review` and pauses
  for acknowledgment before spawning the orchestrator. This test is
  non-negotiable — Loop 035 is the documented regression this scope item
  resolves.

### S9. Stale state cleanup at phase boundary

- Orchestrator (`ralph-orchestrator`) on startup:
  1. Read current phase from PLANNING.md frontmatter
  2. Read existing `loop-ready.json` (if present); compare `phase` field to
     current phase
  3. If mismatch → move `loop-ready.json` and `loop-complete.json` to
     `.advanced-plans/state/archive/<old-phase>-<timestamp>.json` before
     writing the new ones
- Prevents the "Phase 8 starts with Phase 7's loop-ready.json" failure mode

### S10. Dogfood self-install

- `setup/claude-code/install.sh` (and `.ps1`) accepts the source repo as a
  valid target: if `--project` resolves to this repo's root, symlink rather
  than copy the runtime directories so source edits surface immediately
- **Idempotent data scaffold**: before creating `.advanced-plans/` skeleton
  contents, check `if [ -d .advanced-plans ]; then echo "preserving
  existing planning data, skipping scaffold"; fi`. The script must NEVER
  overwrite an existing `.advanced-plans/` tree. Only `.claude/` runtime
  directories get installed or symlinked.
- Document the dev-mode invocation in CONTRIBUTING.md (new) or in CLAUDE.md
- Result: `/next-loop`, `/run-gate`, `/decompose-phase` are usable inside
  the framework's own source repo for the first time
- Tests: unit (existing `.advanced-plans/` triggers skip-data-scaffold
  path); smoke test (CI job or pre-tag local check) that runs at minimum
  `/loop-status` against the source repo and asserts non-error exit

### S11. Version scheme bootstrap + v0.x tag

- Create `VERSION` file at repo root: `0.11.0` (matches Phase 11)
- Create `CHANGELOG.md` (Keep-a-Changelog format) with sections for v0.6
  through v0.11 backfilled from PLANS-INDEX.md phase outcomes
- **CHANGELOG completeness criterion**: every phase row from
  PLANS-INDEX.md must appear in CHANGELOG.md with a matching version
  heading; loop counts in each version section must equal the phase's
  loop count in PLANS-INDEX. Verified at gate review.
- Update README.md "Installation" section to reference `VERSION`
- On Phase 11 gate pass: cut annotated tag `v0.11.0`, push origin
- **Distribution**: GitHub Releases page generated off the tag with body
  pulled from the CHANGELOG section. No PyPI / npm publish (zero-dep
  Python + shell + markdown — no package registry applies). Install
  remains shell-script-driven.
- Subsequent phases bump minor (`0.12.0`, ...); v1 is a separate decision

## Architecture

This phase is mostly localised edits + a few CI/sweep additions. No new
architecture; reinforces existing patterns.

```
core/constraints.json           ← NEW: zero-dep allow-set (S1)
core/skills/schema-design/      ← NEW: skill stub (S3)
core/skills/permission-config/  ← NEW: skill stub (S3)
platforms/python/ast_check.py   ← NEW: shared AST allow-set reader (S1)
docs/path-conventions.md        ← NEW: canonical path map (S7)

CLAUDE.md                       ← edit: drop complexity, drop Haiku tier row, point at constraints.json (S1, S2)
core/schemas/ralph-loop.schema.md ← edit: reaffirm canonical order (S2)

platforms/claude-code/agents/phase-goals-agent.md ← edit: +Write tool (S5)
platforms/claude-code/commands/run-gate.md        ← edit: remove text-only workaround (S5)
platforms/claude-code/commands/next-loop.md       ← edit: add resume-detection step (S8)

ralph-orchestrator (agent def)  ← edit: stale-state cleanup (S9)
ralph-loop-worker (agent def)   ← edit: preflight skill check (S4)
plan-subagent-identification    ← edit: default NA, ban worker self-ref (S6)

.github/workflows/ci.yml        ← edit: shell out to ast_check.py (S1)

setup/claude-code/install.sh    ← edit: self-install detection, idempotent data scaffold (S10)
setup/claude-code/install.ps1   ← edit: parallel change (S10)

VERSION                         ← NEW
CHANGELOG.md                    ← NEW
README.md                       ← edit: link VERSION (S11)
CONTRIBUTING.md                 ← NEW (or edit CLAUDE.md): dev-mode invocation (S10)
```

## Verification Plan

The three highest-risk items (S5, S8, S10) need integration-style
verification beyond unit tests. Loop 046 bundles these into an explicit
verification block:

| Item | E2E Check | Failure handling |
|---|---|---|
| S5 phase-goals-agent +Write | Spawn agent in dry-run gate context with sentinel active; assert verdict JSON file is created BY the agent (not main-thread) at the expected path | If Write tool unavailable at runtime → re-scope S5 to "document workaround"; mark friction entry partially-resolved (upstream-blocked); gate criterion 5 reframes to "workaround formalised" |
| S8 /next-loop resume detection | Fixture: `loop-ready.json` mtime > `loop-complete.json` mtime + dirty tree; invoke `/next-loop`; assert resume-review skill invocation precedes orchestrator spawn | If detection misses → loop fails gate; S8 must land before Phase 11 closes |
| S10 self-install on source repo | Run `setup/claude-code/install.sh --project .` on this repo; assert (a) `.advanced-plans/` planning data byte-unchanged, (b) `.claude/commands/` populated with symlinks, (c) `/loop-status` exits 0 | If data scaffold runs over existing `.advanced-plans/` → critical failure; S10 must land before Phase 11 closes |

These checks are mandatory and run before gate review. If any fail, the
loop fails and the failure block lands in Phase 11 attempt 1's
gate-fail context.

## Success Criteria

1. `core/constraints.json` exists; `platforms/python/ast_check.py` exists
   with `load_allowed_imports()` + `check_file()` + CLI mode; CI workflow
   shells out to `python -m platforms.python.ast_check`; round-trip test
   confirms JSON and reader produce identical sets; pytest passes
2. Zero `complexity:` matches under `.advanced-plans/phases/**` and
   `core/schemas/`; CLAUDE.md Model Tiers table no longer contains a
   Haiku row; CHANGELOG.md documents the schema break
3. `core/skills/schema-design/SKILL.md` and
   `core/skills/permission-config/SKILL.md` exist with all mandatory sections;
   install script copies them to `.claude/skills/`
4. Worker preflight check: a fixture with a non-existent declared skill
   produces a visible warning and proceeds; tests cover this
5. **PRIMARY**: `phase-goals-agent` writes its own verdict file in the
   Loop 046 E2E dry-run; `/run-gate` command file no longer documents the
   text-only workaround. **FALLBACK** (if Write tool doesn't propagate at
   runtime): `/run-gate` formally documents the main-thread persist-on-behalf
   contract and the friction-log entry is marked partially-resolved with
   upstream-blocked status.
6. Zero `agent: ralph-loop-worker` on todos under `.advanced-plans/phases/**`;
   `plan-subagent-identification` documents `NA` as default and explicitly
   reserves `ralph-loop-worker` as the loop executor (never a per-todo agent)
7. Migration-consistency audit complete: `docs/path-conventions.md` exists
   with the canonical path map; all command, agent, skill, and doc files
   case-by-case reviewed; any stale directives identified by the audit
   rewritten to `.advanced-plans/`
8. `/next-loop` resume-detection: regression fixture (loop-ready newer than
   loop-complete + dirty tree) triggers `resume-review` invocation before
   orchestrator spawn (mandatory IRON RULE regression test)
9. Orchestrator stale-state cleanup: simulated cross-phase
   `loop-ready.json` is archived (not consumed) on next orchestrator startup
10. Dogfood self-install: running install on this repo preserves existing
    `.advanced-plans/` byte-unchanged AND populates `.claude/` runtime dirs;
    `/loop-status` exits cleanly from the source repo
11. `VERSION` file exists (`0.11.0`); `CHANGELOG.md` covers v0.6–v0.11 with
    one heading per PLANS-INDEX phase and matching loop counts; annotated
    tag `v0.11.0` cut on gate pass; remote pushed; GitHub Release created
    off the tag with body sourced from CHANGELOG
12. All existing tests still pass (154 pre-Phase-11); new tests added per
    S1, S4, S6, S8, S9, S10 succeed; AST zero-dep check NONE
13. LOCKED files (`docs/phase-complete.schema.md`,
    `docs/phase-manifest-entry.schema.md`, `docs/phase-handoff.schema.md`,
    `.advanced-plans/phases/phase-9/complete.md`) byte-unchanged

## Loop Decomposition (preliminary; ralph-loop-planner will finalise)

5 loops, slightly uneven but kept per /plan-eng-review decision:

- **Loop 042** — Constraints + schema cleanup (S1, S2)
- **Loop 043** — Skills + agents (S3, S4, S5 in-file edit only, S6)
- **Loop 044** — Audits + durability (S7, S8, S9)
- **Loop 045** — Dogfood self-install (S10)
- **Loop 046** — Version bootstrap + Verification Plan E2E + final tests
  (S11 + the three E2E checks for S5/S8/S10 listed in Verification Plan
  table)

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **S5 Write-tool edit is no-op at runtime** (highest-risk item) | Medium | Medium | Loop 046 E2E catches it; fallback path scoped (document workaround); friction entry marked upstream-blocked |
| Dropping `complexity:` + Haiku breaks routing for users relying on it | Low | Low | No external users yet; CHANGELOG breaking-change note documents removal |
| Self-install symlink semantics differ on Windows | Medium | Low | install.ps1 uses junction; document; CI smoke test on both platforms |
| Self-install corrupts existing `.advanced-plans/` data | Medium | High | Idempotent skip-data-scaffold guard (S10); unit + E2E test |
| Constraints.json drift across loops | Low | Medium | S1's round-trip test catches divergence; CI shells out to shared reader |
| CHANGELOG backfill drifts from PLANS-INDEX | Medium | Low | S11 explicit completeness criterion verified at gate review |

## Tool-Friction-Log Triage Outcomes

After Phase 11 ships, the following entries can be marked resolved (with
strikethrough + resolution note in the log):

- AST checker wrong allow-set → S1
- complexity field inconsistency → S2
- schema-design / permission-config not installed → S3 (and S4 for the
  silent-degrade aspect)
- phase-goals-agent no Write tool → S5
- agent self-reference → S6
- Command rot (slash-command stale paths) → S7
- Worker durability (mid-loop death) → S8
- Stale state files cross-phase → S9
- Slash commands unusable in source repo → S10

Phase 12 will address the remaining workflow seams (skill chaining,
`/next-loop --auto` → gate, checkpoint conflation, three-artefact drift).
Harness-level entries (Write/Read/AskUserQuestion/system reminders/skill
loading verbosity) remain permanently deferred as upstream.

## Decision Log Entry (to add to CLAUDE.md on Phase 11 completion)

- Phase 11 (2026-05-20): tool-friction-log triaged. 9 entries resolved this
  phase (S1–S10 mapping above). Version scheme bootstrapped (v0.11.0);
  pre-v1. Phase 12 will address workflow seams. Harness-level frictions
  remain permanently deferred.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAR | 6 issues + 1 critical gap (CHANGELOG completeness), all resolved via spec updates |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | n/a (no UI) |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **UNRESOLVED:** 0
- **VERDICT:** ENG CLEARED — spec ready for phase-plan-creator. Highest-risk
  item is S5 Write-tool runtime propagation; fallback path scoped in
  success criterion 5.
