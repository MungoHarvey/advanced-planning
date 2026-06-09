# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A hierarchical, multi-agent planning framework that structures complex programmes as bounded, verifiable loops. Three-tier hierarchy: Phase Plans (Opus) → Ralph Loops (Sonnet orchestrates) → Todos (Sonnet executes with skill injection).

> **Live programme state**: see `.advanced-plans/PLANNING.md` (YAML frontmatter dashboard) for current phase, loop, gate status, and active branches. All planning artefacts live under `.advanced-plans/`.

## Commands

```bash
# Run Python tests (standard library only, no dependencies beyond pytest)
python -m pytest platforms/python/tests/ -v

# Run a single test file
python -m pytest platforms/python/tests/test_state_manager.py -v

# Run a single test by node id
python -m pytest platforms/python/tests/test_state_manager.py::TestClassName::test_name -v

# Validate JSON schemas
python -c "import json, pathlib; [json.loads(f.read_text()) for f in pathlib.Path('core/state').glob('*.json')]"

# Install into a target project
sh setup/claude-code/install.sh --project /path/to/your/project          # Unix
powershell setup/claude-code/install.ps1 -Project /path/to/your/project  # Windows
```

## Architecture

> **Development workflow**: see `CONTRIBUTING.md` for dev-mode self-install (symlinks/junctions), quick verification steps, and how to run tests.

**Core** (`core/`) is platform-agnostic. **Adapters** (`platforms/`) wrap it for specific environments. Adapters reference the core but never duplicate it.

- `core/schemas/` — Markdown schema definitions for phase-plan, ralph-loop, todo, handoff
- `core/skills/` — Seven planning skills loaded per-todo by targeted injection (load → execute → unload). Includes `companion-detection`, which scans todos for Plannotator review opportunities.
- `core/agents/` — Abstract orchestrator, worker, and gate-reviewer role definitions
- `core/state/` — JSON schemas for the filesystem state bus

**Two-agent pattern**: Main thread spawns Orchestrator (Sonnet), which writes `loop-ready.json`. Main thread then spawns Worker (Sonnet), which executes todos and writes `loop-complete.json`. Neither agent spawns the other — main thread controls all sequencing.

**Targeted skill injection**: Worker loads a `SKILL.md` immediately before each todo that has one assigned, then discards it. No skill persists across todo boundaries.

**Handoff summaries**: Three fields only (`done`/`failed`/`needed`) — one sentence each. This is the only context carried between loops.

### State Bus Protocol

Three files in the `.advanced-plans/state/` directory coordinate the two-agent cycle:

| File | Writer | Reader | Purpose |
|------|--------|--------|---------|
| `loop-ready.json` | Orchestrator | Worker | Loop preparation handoff |
| `loop-complete.json` | Worker | Main thread | Loop completion signal |
| `history.jsonl` | Main thread | Any | Append-only audit log |

### Planning Mode Hooks

During `/plan-and-phase` exploration, a `.advanced-plans/state/planning-mode` sentinel file is created. `PreToolUse` hooks in `settings.json` block `Write`/`Edit`/`MultiEdit` to any path outside `.advanced-plans/` while this sentinel exists. This prevents accidental code changes during the exploration phase.

### Gate Review Protocol

At each phase boundary, `/run-gate` spawns gate agents (default: `code-review-agent`, `phase-goals-agent`) sequentially to evaluate whether phase success criteria have been met. While agents are running, a `gate-review-mode` sentinel at `.advanced-plans/state/gate-review-mode` restricts writes to `.advanced-plans/` only — preventing agents from modifying artefacts they are evaluating.

- **Gate pass**: All agents return `verdict: pass`. `/next-phase` marks the current phase complete, advances `CLAUDE.md` to the next phase, and appends a `gate_pass` event to `history.jsonl`.
- **Gate fail**: Any agent returns `verdict: fail`. `/next-phase` creates a versioned retry file (`.advanced-plans/phases/phase-N/loops-v2.md`) with `gate_failure_context` injected into affected loops, freezes the original file (`status: frozen`), updates `PLANS-INDEX.md`, and appends `gate_fail` and `phase_retry` events to `history.jsonl`.
- **Versioning utilities**: `platforms/python/versioning.py` provides `create_retry_version`, `inject_failure_context`, `get_active_version`, and `freeze_loop_file` — the Python API backing `/next-phase`'s retry logic.
- **Ralph-loop plugin compatibility**: This framework's state files live in `.advanced-plans/state/` (e.g. `loop-ready.json`, `loop-complete.json`). The ralph-loop plugin uses `.claude/ralph-loop.local.md` — no naming conflicts. Both `/next-loop --auto` and the plugin's `/ralph-loop` command can be active simultaneously.
- **Gate-pass-with-dissent override**: When a reviewer's `fail` is a verifiable environment/isolation false-negative with no deliverable defect, the human operator may override — see `docs/gate-override-policy.md` for the full policy (permitted conditions, required `history.jsonl` record, authorisation rules, and what is never a valid override).

### Phase Compaction Schemas

Two locked schema documents govern the compaction artefacts produced by `/phase-compact` at each gate pass:

- `docs/phase-complete.schema.md` — defines the cold artefact (`.advanced-plans/phases/phase-N/complete.md`): a structured git-index document with frontmatter fields, one-line-bullet body sections, and a validation checklist; **Status: LOCKED** (2026-05-13).
- `docs/phase-manifest-entry.schema.md` — defines the hot manifest entry appended to `PLANS-INDEX.md`: a YAML block with a hard ≤8-line ceiling and maximum 2 highlights; **Status: LOCKED** (2026-05-13).

Changes to either schema require an explicit decision logged in this file.

**Decision log:**
- `/phase-compact` reframed (2026-05-19) from terse-artefact writer to conversation-context
  compaction. Adds per-phase `handoff.md` resume digest (Approach A), a transparency report
  via `context_meter.py`, a persistent `## Compaction Instructions` block steering all
  compactions, and a `PreCompact` freshness hook. `complete.md` and both compaction schemas
  remain LOCKED and unchanged. Programmatic `/compact` invocation confirmed impossible;
  consent + ready-to-run handoff is the maximum. `/clear`-based flow rejected.
- Phase 12 (2026-06-08): Codex cross-model second-opinion gate reviewer added (augment
  mode, "B+" approach). Codex runs as a read-only background subprocess parallel to
  `phase-goals-agent`; the main thread writes its verdict on its behalf via
  `codex_gate.extract_and_validate`. Gate degrades gracefully when Codex is unavailable
  (preflight fails or stdout unparseable): two in-house agents proceed, a
  `gate_codex_skipped` event is appended to `history.jsonl`, and no `codex.json` is
  written. `core/state/gate-verdict.schema.json` gained an optional `backend` field
  (enum: `["codex", "subagent"]`) — backward-compatible; existing verdicts remain valid.
- Phase 13 (2026-06-08): Self-correcting gate added to `/next-phase --auto`. Gate fail
  under `--auto` now triggers a bounded triage→fix→re-gate loop (capped at 2 cycles from
  the pre-remediation snapshot; escalates to versioned-retry+STOP on bound or unfixable
  findings). Anti-gate-gaming safety spine: diff allowlist with NEVER-TOUCH list, frozen
  criteria (`criteria-frozen.md`) SHA-256 hash-verified before each re-gate, full
  `criteria_outcomes` required from every re-gate verdict. `gate_failure_context` now
  rides the worker-only `retry-context.json` sidecar rather than `loops.md` frontmatter,
  keeping re-gate agents blind to failure context. `hashlib` added to the stdlib allow-set
  in `core/constraints.json` (used by `remediation_controller.compute_criteria_hash`).
- Phase 14 (2026-06-09): Codex gate (Phase 12) and self-heal (Phase 13) — built and tested
  in source but never installed — wired into this repo's own `.claude/` runtime and proven
  via a two-track strategy: automated tests **plus** a witnessed live exercise. Runtime
  command bodies (`.claude/commands/{run-gate,next-phase}.md`) are refreshed byte-identical
  from `platforms/claude-code/commands/` source (install is plain `cp`, no token
  substitution, so byte-identity is the correct criterion); a `CONTRIBUTING.md` drift note
  documents the copy-not-symlink re-sync. Decision: `codex_gate.extract_verdict_json` was
  given a **minimal scoped fix** — multiple structurally-identical fenced blocks now resolve
  to the last block rather than degrading, because `codex exec` echoes its verdict block
  twice (Loop 056 finding); genuinely-differing blocks still degrade. This was permitted as
  the in-scope "blocking bug found during the exercise gets a minimal scoped fix" path and
  makes the runtime codex live-run criterion achievable. The witnessed self-heal exercise
  (Loop 058) ran a deliberately-induced gate fail through the real remediation guards
  (`triage_findings`, `validate_diff_allowlist`, frozen-criteria hash verify) inside a
  throwaway git **worktree**, emitting `gate_remediation` + `passed_after_remediation`
  events, then discarded the worktree — `main` history untouched. No new gate features;
  no logic change to `remediate.py` / `remediation_controller.py`.
- Phase 15 (2026-06-09): Automation-Surface Audit — state-archiving wired into `/next-loop`
  Step 3a (`archive_cross_phase_state`); CI path-convention audit job added (`path_audit.py`,
  job 4 in `ci.yml`); `/sync-plans` command added (reconciles PLANS-INDEX from phase artefacts);
  `/next-loop --full` flag added (one-pass stub population via `plan-todos` →
  `plan-skill-identification` → `plan-subagent-identification`); formal gate-override policy
  written (`docs/gate-override-policy.md`, codifying the Phase 14 codex-dissent precedent).
  Schema decision: **no change to `core/state/gate-verdict.schema.json`** — the override record
  (`override: true`, `override_reason`) lives on the `history.jsonl` `gate_pass` event (main-thread
  decision), not on the per-agent verdict file; existing verdicts remain fully valid.
- Phase 15 follow-on (2026-06-09): **gate-pass closeout folded into `/run-gate`.** A passing gate
  for the *current* phase is now the natural end of that phase, so `/run-gate` Step 10.4 closes it
  out automatically — moves the phase to `phases.complete`, advances `current_phase`, appends a
  `phase_closed` event (`trigger: run-gate-pass`), commits, and directs to `/phase-compact`. No
  separate `/next-phase` call is needed merely to advance. `/run-gate --phase N` on a non-current
  phase does NOT auto-close (re-gate of history). `/next-phase` gained Step 1a, which detects a
  phase already closed by `/run-gate` (current-phase plan absent ⇒ pointer already advanced) and
  skips re-gating — under `--auto` it proceeds to plan the freshly-pointed phase; otherwise it
  directs to `/phase-compact` + `/plan-and-phase`. Removes the "gated but not closed" seam. This
  edits the framework source (`platforms/claude-code/commands/{run-gate,next-phase}.md`) + this
  repo's `.claude/` runtime copies; the machine-global `~/.claude/commands/` copies are a separate
  install surface and are intentionally left to the operator to refresh.

## Platform Adapters

| Adapter | Location | Entry Point |
|---------|----------|-------------|
| Claude Code | `platforms/claude-code/` | Slash commands (see Command Surface below) |
| Cowork | `platforms/cowork/` | Routing `SKILL.md` + natural language |
| Python API | `platforms/python/` | `state_manager.py`, `plan_io.py`, `handoff.py` |

**`--auto` flag**: `/next-loop --auto` chains loops until the phase plan is exhausted; `/next-phase --auto` chains gate review → next-phase planning → loop execution across phase boundaries until the programme completes or a gate fails.

**`--full` flag**: `/next-loop --full` enables one-pass population of stub loops — when the next pending loop's `todos[]` is empty or unpopulated, it chains `plan-todos` → `plan-skill-identification` → `plan-subagent-identification` in sequence (Step 3c) to fully populate the loop (todos, skills, agents) before the orchestrator runs. When `--full` is absent, behaviour is unchanged. `--auto` and `--full` are composable: `/next-loop --auto --full` chains loops and populates any stubs encountered.

### Runtime Directory

See `docs/path-conventions.md` for the full canonical path map, deprecated tokens, and
"where to find what" reference.

`install.sh` creates this structure in the target project (not in this repo):

```
.claude/
├── commands/    ← Slash commands (copied from platforms/claude-code/commands/)
├── skills/      ← Planning skills (symlinked or copied from core/skills/)
├── agents/      ← Agent definitions (copied from platforms/claude-code/agents/)
├── schemas/     ← Schema docs (copied from core/schemas/)
└── settings.json
.advanced-plans/             ← Platform-agnostic planning data home
├── PLANNING.md              ← Live programme dashboard (YAML frontmatter)
├── README.md                ← Directory map + conventions
├── PLANS-INDEX.md           ← Index of all phases and loops
├── phases/phase-N/          ← plan.md + loops.md (+ complete.md at gate pass) per phase
├── specs/                   ← Design specs (brainstorming output)
├── gate-verdicts/           ← Verdict JSON written by gate agents during /run-gate
├── state/                   ← Filesystem state bus (loop-ready.json, loop-complete.json, history.jsonl)
└── logs/                    ← execution.log (written by session hooks)
```

Skills, agents, schemas, and slash commands are Claude Code runtime adapters and stay under `.claude/`. Everything the planning pipeline produces or consumes lives under `.advanced-plans/`, making the data home portable across agentic coding platforms.

### Command Surface

Each slash command has a single non-overlapping purpose. `/loop-status` reports current state; `/progress-report` synthesises history — they do not overlap.

| Command | Purpose |
|---------|---------|
| `/plan-and-phase` | Interactive explore + plan pipeline (brainstorm → phase plan → loops) |
| `/new-phase` | Headless phase-plan pipeline |
| `/decompose-phase` | Decompose one phase plan into ralph loops |
| `/next-loop` | Execute one loop (orchestrator → worker); `--auto` chains until phase done |
| `/next-phase` | Plan/advance the next phase; gates first if not already gated; `--auto` chains across boundaries. Detects a phase already closed by `/run-gate` and skips re-gating |
| `/run-gate` | Gate review of the current phase; on a pass for the current phase it **closes the phase out** (marks complete + advances the pointer) and directs to `/phase-compact` |
| `/phase-compact` | Produce compaction artefacts at a gate pass |
| `/loop-status` | Live snapshot: pending/in-progress todos |
| `/progress-report` | Historical synthesis: completed work across loops/phases |
| `/check-execution` | Health diagnostic for an interrupted/odd loop |
| `/run-closeout` | Final programme narrative |
| `/model-check` | Verify agent model routing |
| `/sync-plans` | Reconcile PLANS-INDEX.md Phases and loop-status rows for a phase from plan frontmatter |

## Model Tiers

| Role | Default Model | Frequency |
|------|--------------|-----------|
| Phase planning | Opus | Once per phase |
| Loop orchestration | Sonnet | Once per loop |
| Todo execution (worker) | Sonnet | Per todo |
| Gate review | Sonnet | Once per phase boundary |
| Closeout synthesis | Sonnet | Once per programme |
| Progress reporting | Sonnet | On demand |

Override agent tiers via the `model:` field in agent frontmatter. Skills are model-agnostic (no `model:` field). Use `/model-check` to verify agent assignments.

## Code Conventions

**Python** (`platforms/python/`): Standard library only — no external dependencies in source modules. Type hints and NumPy-style docstrings on public functions. Tests use pytest, one class per function group.

**Markdown**: ATX headers, fenced code blocks with language tags, no trailing whitespace.

**Shell scripts**: POSIX sh (`#!/bin/sh`), `set -e`, quoted variables.

**Commit prefixes**: `fix:`, `feat:`, `docs:`, `refactor:`, `test:`

## Key Constraints

- Python 3.10+ required
- The Python API must remain zero-dependency (standard library only) — CI enforces this with `python -m platforms.python.ast_check`. The canonical allow-set is defined in `core/constraints.json` (see that file for the authoritative list; currently: `ast`, `hashlib`, `json`, `pathlib`, `re`, `datetime`, `typing`, `os`, `sys`, `tempfile`, `textwrap`, `argparse`, `asyncio`; `__future__` is explicitly excluded)
- Core files must never reference platform-specific paths (no `.claude/` in core)
- New skills require frontmatter (`name`, `description`) and sections: `## When to Use`, `## Process`, `## Output Format`. Skills are model-agnostic — the executing agent's model determines capability, not the skill.
- Plan files use YAML frontmatter in markdown; ralph loops contain `todos[]` arrays with canonical field order (`id`/`content`/`skill`/`agent`/`outcome`/`status`/`priority`)
- Todos may declare a single skill (string) or multiple skills (array); discovery checks both project-local (`.claude/skills/`) and global (`~/.claude/skills/`) directories

## CI

Three jobs in `.github/workflows/ci.yml`, all must pass on `main` and PRs:
1. **Markdown lint** — `markdownlint-cli2` (currently non-blocking via `|| true`)
2. **JSON schema validation** — validates all `core/state/*.json` files parse correctly
3. **Python tests** — runs `pytest` across Python 3.10, 3.11, 3.12; then verifies zero external imports via AST checker

## Compaction Instructions

When compacting this conversation (via `/compact` or auto-threshold), use this retention policy:

**Retain verbatim:** `.advanced-plans/phases/phase-15/handoff.md` (the validated phase
resume digest for the most recently completed phase), `.advanced-plans/PLANNING.md`
frontmatter, and any open cross-phase decisions/threads.

**Preserve:** all DECISIONS and their rationale.

**Discard:** verbatim file-Read contents and bash/tool_result output (recoverable from
disk and git); injected skill/command/tool-schema bodies (reload on demand); gate-review
agent-by-agent back-and-forth (final verdicts are on disk); prior compaction summaries
now superseded by handoff.md; resolved remediation detail.

**Goal:** keep the distilled signal, shed the raw I/O that dominates context.

> This block is maintained by `/phase-compact` (rewritten to point at the current
> phase handoff.md after each gate pass). The `PreCompact` hook validates the digest
> before every compaction. If no handoff.md exists yet (mid-phase), this policy alone
> steers retention.
