---
title: ".advanced-plans/ Restructure — Design Spec"
date: 2026-05-14
status: draft
phase: 9
supersedes_scope:
  - "plans/phase-8.md Loops 028–031 (folded into Phase 9)"
related:
  - plans/phase-8.md
  - plans/2026-05-13-framework-consistency-audit-remediation.md
---

# .advanced-plans/ Restructure — Design Spec

## Identity

This restructure makes the framework's *data* (plans, state, logs, specs) platform-agnostic by consolidating it into a single hidden top-level directory, `.advanced-plans/`. The framework's *runtime* (commands, agents, skills, schemas, settings) remains under `.claude/` as one of N possible platform adapters. After this change, any agentic coding platform (Cursor, Aider, Codex, future tools) can drive the framework by reading and writing the same `.advanced-plans/` tree — Claude Code becomes one consumer among several.

A secondary outcome: `.advanced-plans/PLANNING.md` becomes a machine-readable dashboard with YAML frontmatter. An agent starting cold can read ~15 lines and know the programme's current phase, loop, gate state, active branches, and recommended next action without grepping or reading multiple files.

## Locked Decisions (from brainstorming)

| Decision | Choice | Reasoning |
|---|---|---|
| Directory name | `.advanced-plans/` (hidden, framework-named) | Tidy at repo root; signals ownership; cross-platform-portable |
| Internal structure | Hybrid: top-level core + `phases/phase-N/` subdirs | Separates navigation/meta files from per-phase work; "everything for phase N" co-located |
| Scope | Full data home: plans + state + logs + specs | One portable directory for everything the workflow produces |
| Migration | Big-bang in one phase (Phase 9) | Project has a single primary user; dual-path code is wasteful overhead |
| Phase 8 fate | Close at Loop 027; fold Loops 028–031 into Phase 9 | Phase 9 will rewrite the same files Phase 8's remainder would have touched |
| Top-level files | Both `README.md` and `PLANNING.md` | Different audiences: README = static onboarding, PLANNING = live state |

## Target Layout

```
.advanced-plans/
├── README.md                    ← directory map, conventions, "what is this"
├── PLANNING.md                  ← live dashboard with YAML frontmatter (see below)
├── PLANS-INDEX.md               ← programme tracking table (moved from plans/)
├── master-plan.md               ← programme overview (moved from plans/)
├── phases/
│   ├── phase-1/
│   │   ├── plan.md              ← was plans/phase-1.md
│   │   ├── loops.md             ← was plans/phase-1-ralph-loops.md
│   │   ├── gate-verdicts/       ← gate JSON files for this phase
│   │   └── complete.md          ← was plans/phase-completes/phase-1-complete.md
│   └── phase-N/...
├── specs/
│   └── YYYY-MM-DD-<topic>-design.md   ← brainstorming outputs
├── state/
│   ├── loop-ready.json
│   ├── loop-complete.json
│   └── history.jsonl
└── logs/
    └── execution.log
```

After this change, `.claude/` contains only Claude-Code runtime artefacts:

```
.claude/
├── commands/
├── agents/
├── skills/
├── schemas/
└── settings.json                ← tracked via gitignore exception
```

## PLANNING.md Frontmatter

```yaml
---
programme: "Programme name"
status: in_progress              # draft | in_progress | complete | blocked
last_updated: YYYY-MM-DD

current_phase: N
current_loop: ralph-loop-NNN     # in flight or next pending
gate_status: not_due             # not_due | pending | passed | failed
next_action: "/next-loop"        # recommended command

active_branches:                 # supports parallel sessions
  - branch: main
    phase: N
    session: primary

phases:
  complete: [1, 2, 3, ...]
  pending: [N, N+1, ...]
  failed: []                     # phases needing retry

state_files:
  ready: .advanced-plans/state/loop-ready.json
  complete: .advanced-plans/state/loop-complete.json
  history: .advanced-plans/state/history.jsonl

notes: |
  Free-text notes about current programme state.
---
```

Frontmatter is the agent's 10-second orientation. Slash commands maintain it:

- `/next-loop` updates `current_loop`, `next_action`, `last_updated`
- `/run-gate` updates `gate_status`
- `/next-phase` updates `current_phase`, `phases.complete`, `phases.pending`, `phases.failed`
- `/phase-compact` updates `phases.complete`
- `/new-phase` (planning) updates `current_phase`, `phases.pending`

CLAUDE.md gets a one-line pointer to `.advanced-plans/PLANNING.md` near the top, so cold-starting agents know where the live state lives. Any existing "Planning State" section in CLAUDE.md (if present) is removed in favour of the pointer — there is one source of truth.

### Frontmatter extension to other documents

To keep document headers consistent and machine-scannable, lighter frontmatter blocks are added to:

- `phases/phase-N/plan.md` — `status`, `phase`, `loops_pending`, `loops_complete`, `gate_verdict`
- `PLANS-INDEX.md` — `dashboard: .advanced-plans/PLANNING.md` pointer
- `phases/phase-N/loops.md` — already has per-loop frontmatter (handoff_summary, todos); align field names with new conventions

## Bundled Cleanup (resolved by this migration)

| Item | Origin | How Phase 9 resolves it |
|---|---|---|
| `.claude/settings.json` gitignore conflict | Phase 8 Loop 027 | Add `!.claude/settings.json` exception to .gitignore; file stays where Loop 027 placed it |
| `/new-loop` path bugs (`.md.md`, wrong save dir) | Friction log | Command rewritten for new layout; bugs vanish |
| `/next-loop` looking in `.claude/plans/` | Friction log | Rewritten to target `.advanced-plans/phases/*/loops.md` |
| PLANS-INDEX.md gap for Phases 6/7 | Discovered during Phase 8 planning | Backfilled when rewriting PLANS-INDEX for new layout |
| Phase 8 Loops 028–031 (sentinel consolidation, progress-report dedup, new-loop rename, command disambiguation) | Phase 8 plan | Folded into Phase 9 command-rewrite waves |

## Wave Breakdown

Final decomposition by phase-plan-creator. Rough shape:

### Wave 1 — Skeleton
- Create `.advanced-plans/` directory tree
- Write initial `README.md` and `PLANNING.md` (with frontmatter populated from current state)
- Add `!.claude/settings.json` gitignore exception
- Patch hook allowlists to allow BOTH old and new paths (so the migration itself isn't blocked)

### Wave 2 — File Migration
- `git mv plans/phase-N.md` → `phases/phase-N/plan.md` for every existing phase
- `git mv plans/phase-N-ralph-loops.md` → `phases/phase-N/loops.md`
- `git mv plans/gate-verdicts/phase-N-*.json` → `phases/phase-N/gate-verdicts/`
- `git mv plans/phase-completes/phase-N-complete.md` → `phases/phase-N/complete.md`
- `git mv plans/2026-*.md` (design specs) → `specs/`
- `git mv plans/PLANS-INDEX.md` and `plans/master-plan.md` to `.advanced-plans/` root
- `git mv .claude/state/*` → `.advanced-plans/state/`
- `git mv .claude/logs/*` → `.advanced-plans/logs/`
- Verify `git log --follow` works on at least one moved file
- Delete now-empty `plans/`, `.claude/state/`, `.claude/logs/`

### Wave 3 — Command Rewrites
- Rewrite every slash command in `platforms/claude-code/commands/` to target new paths
- Rename `/new-loop` → `/decompose-phase` (Phase 8 Loop 030 absorbed)
- Fix `.md.md` extension bug in `/new-loop` (now `/decompose-phase`)
- Consolidate sentinel management (Phase 8 Loop 028 absorbed) — single source of truth for sentinel paths
- Deduplicate `/progress-report` logic (Phase 8 Loop 029 absorbed)
- Disambiguate overlapping command surfaces (Phase 8 Loop 031 absorbed)

### Wave 4 — Hooks + Permissions + Python API + Install Script
- Narrow hook allowlists in `platforms/claude-code/settings.json` and `platforms/claude-code/hooks/hooks.json` to new paths only (drop the dual-allow from Wave 1)
- Update **permission allow rules** in both `.claude/settings.json` (repo-root, from Loop 027) and `platforms/claude-code/settings.json` (the adapter installed into target projects) so Read/Write/Edit/MultiEdit operations targeting `.advanced-plans/**` are auto-allowed without permission prompts. Replaces the current `plans/**`, `.claude/state/**`, `.claude/logs/**` rules with a single `.advanced-plans/**` rule.
- Update `platforms/python/plan_io.py` and `state_manager.py` path constants
- Update `setup/claude-code/install.sh` and `install.ps1` to:
  - Create `.advanced-plans/` skeleton in target projects (including README + PLANNING template)
  - Detect old layout (presence of `plans/` or `.claude/state/`) and migrate idempotently
  - No longer create `.claude/state/` or `.claude/logs/`
  - Install the updated settings.json with `.advanced-plans/**` allow rules

### Wave 5 — Docs + Tests + Backfill
- Rewrite CLAUDE.md (Architecture, Runtime Directory, Workflow sections); remove any existing "Planning State" section and add a one-line pointer to `.advanced-plans/PLANNING.md` near the top of the file
- Update every `SKILL.md` reference (skill docs in `core/skills/` and global skills)
- Update `pytest` path references in `platforms/python/tests/`
- Update markdownlint config glob patterns
- Update CI workflow path filters (`.github/workflows/ci.yml`)
- Backfill Phase 6/7 entries in PLANS-INDEX.md
- Final grep audit: zero occurrences of `plans/`, `.claude/state/`, `.claude/logs/`, `.claude/plans/` in `core/`, `platforms/`, `CLAUDE.md`, `SKILL.md` files

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Git history lost on moves | Use `git mv` exclusively; verify with `git log --follow` on a sample file in Wave 2 |
| Stale references hide in tests / markdownlint / CI / skill docs | Final grep audit in Wave 5 covers all four roots; failure to find clean state blocks gate pass |
| Hook config blocks its own migration mid-flight | Wave 1 patches hook allowlists to allow BOTH old and new paths; Wave 4 narrows to new-only |
| In-flight loop state at migration time | Phase 9 only starts when no `loop-ready.json` is present; Phase 8 close-out ensures this |
| Cross-platform path separators (Windows) | All paths in source code use forward slashes; `pathlib.Path` for filesystem ops |
| Existing target-project installations | `install.sh` becomes idempotent — detects old layout, performs in-place migration, prints summary |
| Frontmatter drifts out of sync with actual state | Commands maintain it as part of their existing state-update steps; CI lint can flag stale `last_updated` (deferred — not in Phase 9 scope) |
| Unstaged/uncommitted changes in `plans/`, `.claude/state/`, or `.claude/logs/` at migration time | Wave 1 first step: refuse to proceed if `git status` shows changes in any source directory. User must commit, stash, or discard before Phase 9 can run. Documented as a precondition in Wave 1's prompt. |

## Success Criteria

- `.advanced-plans/` exists at repo root with the full tree (README, PLANNING, PLANS-INDEX, master-plan, phases/, specs/, state/, logs/)
- Old `plans/`, `.claude/state/`, `.claude/logs/` directories deleted
- `.claude/` contains only Claude-Code runtime (commands, agents, skills, schemas, settings.json)
- `.gitignore` has `!.claude/settings.json` exception; `git ls-files .claude/settings.json` returns the file
- `PLANNING.md` exists with fully populated frontmatter reflecting current programme state
- `README.md` exists, documents the layout, references PLANNING.md as the live dashboard
- All slash commands work end-to-end against new layout — verified by running `/next-loop` on a fresh test programme
- `python -m pytest platforms/python/tests/ -v` passes (path constants updated)
- `git log --follow .advanced-plans/phases/phase-1/plan.md` shows history dating to Phase 1's original creation
- PLANS-INDEX.md covers Phases 1–8 inclusive (Phase 6/7 gap closed)
- Grep audit: zero occurrences of `plans/`, `.claude/state/`, `.claude/logs/`, `.claude/plans/` in `core/`, `platforms/`, `CLAUDE.md`, or any `SKILL.md` file
- `.claude/settings.json` (both repo-root and `platforms/claude-code/`) contains a permission allow rule for `.advanced-plans/**` covering Read, Write, Edit, MultiEdit — verified by writing a test file to `.advanced-plans/test.md` and observing no permission prompt

## Deferred Work

The following items are explicitly **out of Phase 9 scope** and tracked for later:

- **CI lint for PLANNING.md frontmatter freshness** — e.g. warn if `last_updated` is older than the last commit touching `.advanced-plans/`. Deferred until frontmatter has stabilised in real use.
- **Phase 9 worker-redesign (always-dispatch model)** — already deferred from Phase 8; not affected by this restructure.
- **Automation surface audit** — deferred from Phase 8; will inherit the new layout when scheduled.
- **Cowork adapter (`platforms/cowork/`) alignment with new layout** — Cowork adapter currently shells out through natural language; update to read from `.advanced-plans/` is a separate concern from the Claude Code adapter changes here.
