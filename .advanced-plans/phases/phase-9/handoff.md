---
phase: 9
title: ".advanced-plans/ Restructure"
status: passed
created: 2026-05-19T17:36:25Z
complete_ref: .advanced-plans/phases/phase-9/complete.md
plan_ref: .advanced-plans/phases/phase-9/plan.md
loops_ref: .advanced-plans/phases/phase-9/loops.md
gate_verdict_refs:
  - .advanced-plans/gate-verdicts/phase-9-attempt-1-code-review-agent.json
  - .advanced-plans/gate-verdicts/phase-9-attempt-1-phase-goals-agent.json
  - .advanced-plans/gate-verdicts/phase-9-attempt-2-code-review-agent.json
  - .advanced-plans/gate-verdicts/phase-9-attempt-2-phase-goals-agent.json
token_ceiling: 1500
---

## What was done & why
- `.advanced-plans/` tree exists at repo root (README, PLANNING, PLANS-INDEX, master-plan, phases/, specs/, state/, logs/) -- verified ls; attempt-2 phase-goa...
- Old `plans/`, `.claude/state/`, `.claude/logs/` removed -- all three ls return "No such file or directory".
- `.claude/` holds only runtime (settings.json, settings.local.json, skills/) -- stray empty `.claude/plans/` removed in 19199d3.
- `.gitignore` `!.claude/settings.json` exception present; `git ls-files` returns the file -- .gitignore line 6.
- `PLANNING.md` frontmatter fully populated (programme status, phases, gate_status, state_files).
- `README.md` documents the layout and references PLANNING.md as the live dashboard.
- All slash commands target the new layout; attempt-1 double-prefix corruption fully remediated -- code-review-agent attempt-2 PASS confirms zero `.advanced-....
- `pytest platforms/python/tests/` -> 72 passed (0.65s).
- `git log --follow .advanced-plans/phases/phase-1/plan.md` traces through migrate 65903f5 to original release 5ec7168.
- PLANS-INDEX covers Phases 1-9 incl. Phase 6 (019-022) and Phase 7 (023-026); 6/7 gap closed.
- Grep audit: zero live old-path or double-prefix references in core/, platforms/, CLAUDE.md (intentional legacy shims excluded).
- Permission allow rules for `.advanced-plans/**` (R/W/E/ME) in both `.claude/settings.json` and `platforms/claude-code/settings.json`.

## Outcomes
- `.advanced-plans/` tree exists at repo root (README, PLANNING, PLANS-INDEX, master-plan, phases/, specs/, state/, logs/) -- verified ls; attempt-2 phase-goa...
- Old `plans/`, `.claude/state/`, `.claude/logs/` removed -- all three ls return "No such file or directory".
- `.claude/` holds only runtime (settings.json, settings.local.json, skills/) -- stray empty `.claude/plans/` removed in 19199d3.
- `.gitignore` `!.claude/settings.json` exception present; `git ls-files` returns the file -- .gitignore line 6.
- `PLANNING.md` frontmatter fully populated (programme status, phases, gate_status, state_files).
- `README.md` documents the layout and references PLANNING.md as the live dashboard.
- All slash commands target the new layout; attempt-1 double-prefix corruption fully remediated -- code-review-agent attempt-2 PASS confirms zero `.advanced-....
- `pytest platforms/python/tests/` -> 72 passed (0.65s).
- `git log --follow .advanced-plans/phases/phase-1/plan.md` traces through migrate 65903f5 to original release 5ec7168.
- PLANS-INDEX covers Phases 1-9 incl. Phase 6 (019-022) and Phase 7 (023-026); 6/7 gap closed.
- Grep audit: zero live old-path or double-prefix references in core/, platforms/, CLAUDE.md (intentional legacy shims excluded).
- Permission allow rules for `.advanced-plans/**` (R/W/E/ME) in both `.claude/settings.json` and `platforms/claude-code/settings.json`.

## Errors & issues encountered
- `phase-9/plan.md` frontmatter `design_spec` still points to old `plans/2026-05-14-...` path (info; spec now under `.advanced-plans/specs/`; no runtime impact)
- (+2 more observations -- see complete.md ## Opened)

## Files touched (pointers, not contents)
- edited: `Repo root` -- `.advanced-plans/` directory tree
- edited: ``.advanced-plans/README.md`` -- `README.md` (directory map, conventions)
- edited: ``.advanced-plans/PLANNING.md`` -- `PLANNING.md` (live dashboard)
- edited: ``.advanced-plans/phases/phase-N/`` -- All phase plans, loops, verdicts, completes
- edited: ``.advanced-plans/specs/`` -- Design specs
- edited: ``.advanced-plans/state/`, `.advanced-plans/logs/`` -- State bus + history + logs
- edited: ``platforms/claude-code/commands/`` -- Rewritten slash commands
- edited: ``platforms/claude-code/commands/decompose-phase.md`` -- Renamed command: `/new-loop` -> `/decompose-phase`
- edited: ``platforms/claude-code/settings.json`, `platforms/claude-code/hooks/hooks.json`` -- Updated hook configs
- edited: ``.claude/settings.json`, `platforms/claude-code/settings.json`` -- Updated permission rules

## Gate review
Attempt 2 pass at confidence 95 . Note: Still documents the old plans/ + .claude/state/ layout; user-facing install doc. Out of the criteria-bearing audit scope. -> full verdict: .advanced-plans/gate-verdicts/phase-9-attempt-2-phase-goals-agent.json

## Skills & methods used
- `file-migration` -- Batch `git mv` operations across nested directories, history preservation, post-
- `command-rewriting` -- Slash command edits, path standardisation across ~10 commands, rename mechanics
- `permission-config` -- Hook allowlist patterns and settings.json `allow` rules; understanding of dual-a
- `python-refactor` -- Path constant updates in `plan_io.py` and `state_manager.py`; preserve zero-depe
- `shell-scripting` -- POSIX sh + PowerShell install script logic; idempotent old-layout detection and 
- `docs-rewrite` -- CLAUDE.md restructure, README/PLANNING authoring, skill doc updates
- `schema-design` -- PLANNING.md frontmatter schema definition, plan.md frontmatter alignment

## Resume pointers
- Plans: .advanced-plans/phases/phase-9/plan.md / .advanced-plans/phases/phase-9/loops.md - Spec: .advanced-plans/specs/2026-05-14-advanced-plans-restructure-design.md - Next: Start phase-10
