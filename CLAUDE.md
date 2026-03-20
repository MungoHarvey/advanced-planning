# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A hierarchical, multi-agent planning framework that structures complex programmes as bounded, verifiable loops. Three-tier hierarchy: Phase Plans (Opus) → Ralph Loops (Sonnet orchestrates) → Todos (Haiku executes with skill injection).

## Commands

```bash
# Run Python tests (standard library only, no dependencies beyond pytest)
python -m pytest platforms/python/tests/ -v

# Run a single test file
python -m pytest platforms/python/tests/test_state_manager.py -v

# Validate JSON schemas
python -c "import json, pathlib; [json.loads(f.read_text()) for f in pathlib.Path('core/state').glob('*.json')]"

# Install into a target project (Claude Code adapter)
sh setup/claude-code/install.sh --project /path/to/your/project
```

## Architecture

**Core** (`core/`) is platform-agnostic. **Adapters** (`platforms/`) wrap it for specific environments. Adapters reference the core but never duplicate it.

- `core/schemas/` — Markdown schema definitions for phase-plan, ralph-loop, todo, handoff
- `core/skills/` — Five planning skills loaded per-todo by targeted injection (load → execute → unload)
- `core/agents/` — Abstract orchestrator and worker role definitions
- `core/state/` — JSON schemas for the filesystem state bus (`loop-ready.json` → `loop-complete.json` → `history.jsonl`)

**Two-agent pattern**: Main thread spawns Orchestrator (Sonnet), which writes `loop-ready.json`. Main thread then spawns Worker (Haiku), which executes todos and writes `loop-complete.json`. Neither agent spawns the other — main thread controls all sequencing.

**Targeted skill injection**: Worker loads a `SKILL.md` immediately before each todo that has one assigned, then discards it. No skill persists across todo boundaries.

**Handoff summaries**: Three fields only (`done`/`failed`/`needed`) — one sentence each. This is the only context carried between loops.

## Platform Adapters

| Adapter | Location | Entry Point |
|---------|----------|-------------|
| Claude Code | `platforms/claude-code/` | Slash commands (`/plan-and-phase`, `/new-phase`, `/next-loop`, `/next-loop --auto`, `/progress-report`, `/loop-status`) |
| Cowork | `platforms/cowork/` | Routing `SKILL.md` + natural language |
| Python API | `platforms/python/` | `state_manager.py`, `plan_io.py`, `handoff.py` |

## Code Conventions

**Python** (`platforms/python/`): Standard library only — no external dependencies in source modules. Type hints and NumPy-style docstrings on public functions. Tests use pytest, one class per function group.

**Markdown**: ATX headers, fenced code blocks with language tags, no trailing whitespace.

**Shell scripts**: POSIX sh (`#!/bin/sh`), `set -e`, quoted variables.

**Commit prefixes**: `fix:`, `feat:`, `docs:`, `refactor:`, `test:`

## Key Constraints

- Python 3.10+ required
- The Python API must remain zero-dependency (standard library only) — CI enforces this with an AST import checker
- Core files must never reference platform-specific paths (no `.claude/` in core)
- New skills require frontmatter (`name`, `model`, `description`) and sections: `## When to Use`, `## Process`, `## Output Format`
- Plan files use YAML frontmatter in markdown; ralph loops contain `todos[]` arrays with canonical field order (`id`/`content`/`skill`/`agent`/`outcome`/`status`/`priority`)
