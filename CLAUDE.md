# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A hierarchical, multi-agent planning framework that structures complex programmes as bounded, verifiable loops. Three-tier hierarchy: Phase Plans (Opus) → Ralph Loops (Sonnet orchestrates) → Todos (Sonnet executes with skill injection; Haiku for `complexity: low` todos only).

## Commands

```bash
# Run Python tests (standard library only, no dependencies beyond pytest)
python -m pytest platforms/python/tests/ -v

# Run a single test file
python -m pytest platforms/python/tests/test_state_manager.py -v

# Validate JSON schemas
python -c "import json, pathlib; [json.loads(f.read_text()) for f in pathlib.Path('core/state').glob('*.json')]"

# Install into a target project
sh setup/claude-code/install.sh --project /path/to/your/project          # Unix
powershell setup/claude-code/install.ps1 -Project /path/to/your/project  # Windows
```

## Architecture

**Core** (`core/`) is platform-agnostic. **Adapters** (`platforms/`) wrap it for specific environments. Adapters reference the core but never duplicate it.

- `core/schemas/` — Markdown schema definitions for phase-plan, ralph-loop, todo, handoff
- `core/skills/` — Six planning skills loaded per-todo by targeted injection (load → execute → unload)
- `core/agents/` — Abstract orchestrator, worker, and gate-reviewer role definitions
- `core/state/` — JSON schemas for the filesystem state bus

**Two-agent pattern**: Main thread spawns Orchestrator (Sonnet), which writes `loop-ready.json`. Main thread then spawns Worker (Sonnet), which executes todos and writes `loop-complete.json`. Neither agent spawns the other — main thread controls all sequencing.

**Targeted skill injection**: Worker loads a `SKILL.md` immediately before each todo that has one assigned, then discards it. No skill persists across todo boundaries.

**Handoff summaries**: Three fields only (`done`/`failed`/`needed`) — one sentence each. This is the only context carried between loops.

### State Bus Protocol

Three files in the `state/` directory coordinate the two-agent cycle:

| File | Writer | Reader | Purpose |
|------|--------|--------|---------|
| `loop-ready.json` | Orchestrator | Worker | Loop preparation handoff |
| `loop-complete.json` | Worker | Main thread | Loop completion signal |
| `history.jsonl` | Main thread | Any | Append-only audit log |

### Planning Mode Hooks

During `/plan-and-phase` exploration, a `planning-mode` sentinel file is created. `PreToolUse` hooks in `settings.json` block `Write`/`Edit`/`MultiEdit` to any path outside `.claude/plans/` and `.claude/state/` while this sentinel exists. This prevents accidental code changes during the exploration phase.

### Gate Review Protocol

At each phase boundary, `/run-gate` spawns gate agents (default: `code-review-agent`, `phase-goals-agent`) sequentially to evaluate whether phase success criteria have been met. While agents are running, a `gate-review-mode` sentinel at `.claude/state/gate-review-mode` restricts writes to `plans/gate-verdicts/` and `.claude/state/` only — preventing agents from modifying artefacts they are evaluating.

- **Gate pass**: All agents return `verdict: pass`. `/next-phase` marks the current phase complete, advances `CLAUDE.md` to the next phase, and appends a `gate_pass` event to `history.jsonl`.
- **Gate fail**: Any agent returns `verdict: fail`. `/next-phase` creates a versioned retry file (`phase-N-ralph-loops-v2.md`) with `gate_failure_context` injected into affected loops, freezes the original file (`status: frozen`), updates `PLANS-INDEX.md`, and appends `gate_fail` and `phase_retry` events to `history.jsonl`.
- **Versioning utilities**: `platforms/python/versioning.py` provides `create_retry_version`, `inject_failure_context`, `get_active_version`, and `freeze_loop_file` — the Python API backing `/next-phase`'s retry logic.
- **Ralph-loop plugin compatibility**: This framework's state files live in `.claude/state/` (e.g. `loop-ready.json`, `loop-complete.json`). The ralph-loop plugin uses `.claude/ralph-loop.local.md` — no naming conflicts. Both `/next-loop --auto` and the plugin's `/ralph-loop` command can be active simultaneously.

## Platform Adapters

| Adapter | Location | Entry Point |
|---------|----------|-------------|
| Claude Code | `platforms/claude-code/` | Slash commands (`/plan-and-phase`, `/new-phase`, `/next-loop`, `/next-loop --auto`, `/run-gate`, `/run-closeout`, `/next-phase`, `/progress-report`, `/loop-status`, `/check-execution`, `/model-check`) |
| Cowork | `platforms/cowork/` | Routing `SKILL.md` + natural language |
| Python API | `platforms/python/` | `state_manager.py`, `plan_io.py`, `handoff.py` |

### Runtime Directory

`install.sh` creates this structure in the target project (not in this repo):

```
.claude/
├── commands/    ← Slash commands (copied from platforms/claude-code/commands/)
├── skills/      ← Planning skills (symlinked or copied from core/skills/)
├── agents/      ← Agent definitions (copied from platforms/claude-code/agents/)
├── schemas/     ← Schema docs (copied from core/schemas/)
├── state/       ← Filesystem state bus (loop-ready.json, loop-complete.json, history.jsonl)
├── logs/        ← execution.log (written by session hooks)
└── settings.json
plans/
└── gate-verdicts/  ← Verdict JSON files written by gate agents during /run-gate
```

## Model Tiers

| Role | Default Model | Frequency |
|------|--------------|-----------|
| Phase planning | Opus | Once per phase |
| Loop orchestration | Sonnet | Once per loop |
| Todo execution (worker) | Sonnet | Per todo (default) |
| Low-complexity todos | Haiku | Per todo (when `complexity: low`) |
| Gate review | Sonnet | Once per phase boundary |
| Closeout synthesis | Sonnet | Once per programme |
| Progress reporting | Sonnet | On demand |

Override tiers via the `model:` field in skill/agent frontmatter. Use `/model-check` to verify assignments.

## Code Conventions

**Python** (`platforms/python/`): Standard library only — no external dependencies in source modules. Type hints and NumPy-style docstrings on public functions. Tests use pytest, one class per function group.

**Markdown**: ATX headers, fenced code blocks with language tags, no trailing whitespace.

**Shell scripts**: POSIX sh (`#!/bin/sh`), `set -e`, quoted variables.

**Commit prefixes**: `fix:`, `feat:`, `docs:`, `refactor:`, `test:`

## Key Constraints

- Python 3.10+ required
- The Python API must remain zero-dependency (standard library only) — CI enforces this with an AST import checker. Allowed imports: `json`, `pathlib`, `re`, `datetime`, `typing`, `os`, `sys`, `tempfile`, `textwrap`, `argparse`, `asyncio`
- Core files must never reference platform-specific paths (no `.claude/` in core)
- New skills require frontmatter (`name`, `model`, `description`) and sections: `## When to Use`, `## Process`, `## Output Format`
- Plan files use YAML frontmatter in markdown; ralph loops contain `todos[]` arrays with canonical field order (`id`/`content`/`skill`/`agent`/`outcome`/`status`/`priority`)

## CI

Three jobs in `.github/workflows/ci.yml`, all must pass on `main` and PRs:
1. **Markdown lint** — `markdownlint-cli2` (currently non-blocking via `|| true`)
2. **JSON schema validation** — validates all `core/state/*.json` files parse correctly
3. **Python tests** — runs `pytest` across Python 3.10, 3.11, 3.12; then verifies zero external imports via AST checker
