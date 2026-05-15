---
phase: 9
name: ".advanced-plans/ Restructure"
status: draft
loops: [032, 033, 034, 035, 036]
design_spec: plans/2026-05-14-advanced-plans-restructure-design.md
supersedes_scope:
  - "phase-8.md Loops 028–031 (folded in)"
---

# Phase 9: .advanced-plans/ Restructure

## Objective

Migrate the framework's data home from `plans/` + `.claude/state/` + `.claude/logs/` into a single platform-agnostic `.advanced-plans/` directory, with a YAML-frontmatter dashboard (`PLANNING.md`) for cold-start agent orientation.

## Scope

### Included
- New `.advanced-plans/` tree: README, PLANNING (with frontmatter), PLANS-INDEX, master-plan, `phases/phase-N/`, `specs/`, `state/`, `logs/`
- `git mv` migration of every existing phase plan, ralph-loop file, gate verdict, completion artefact, design spec, state file, and log
- Slash command rewrites targeting new paths
- Absorbed Phase 8 work: sentinel consolidation, `/new-loop` → `/decompose-phase` rename + bug fixes, `/progress-report` dedup, command disambiguation
- Hook allowlists narrowed to `.advanced-plans/**` (with dual-allow transition in Wave 1)
- Permission allow rules in both `.claude/settings.json` (repo-root) and `platforms/claude-code/settings.json` covering Read/Write/Edit/MultiEdit for `.advanced-plans/**`
- Python API path constants (`plan_io.py`, `state_manager.py`)
- `install.sh` / `install.ps1` idempotent migration logic for existing target-project installations
- Documentation rewrites: CLAUDE.md, all `SKILL.md` references, README, PLANNING
- Test path updates, markdownlint config, CI workflow filters
- PLANS-INDEX.md backfill for Phases 6/7 (currently missing)
- `.gitignore` exception for `.claude/settings.json`

### Explicitly NOT included
- CI lint for frontmatter freshness (deferred until conventions stabilise)
- Worker-redesign / always-dispatch model (deferred from Phase 8)
- Automation surface audit (separate future phase)
- Cowork adapter alignment with new layout (separate phase)

## Key Deliverables

| Deliverable | Format | Location |
|---|---|---|
| `.advanced-plans/` directory tree | Filesystem | Repo root |
| `README.md` (directory map, conventions) | Markdown | `.advanced-plans/README.md` |
| `PLANNING.md` (live dashboard) | Markdown + YAML frontmatter | `.advanced-plans/PLANNING.md` |
| All phase plans, loops, verdicts, completes | Markdown / JSON | `.advanced-plans/phases/phase-N/` |
| Design specs | Markdown | `.advanced-plans/specs/` |
| State bus + history + logs | JSON / JSONL / log | `.advanced-plans/state/`, `.advanced-plans/logs/` |
| Rewritten slash commands | Markdown | `platforms/claude-code/commands/` |
| Renamed command: `/new-loop` → `/decompose-phase` | Markdown | `platforms/claude-code/commands/decompose-phase.md` |
| Updated hook configs | JSON | `platforms/claude-code/settings.json`, `platforms/claude-code/hooks/hooks.json` |
| Updated permission rules | JSON | `.claude/settings.json`, `platforms/claude-code/settings.json` |
| Python API path constants | Python | `platforms/python/plan_io.py`, `state_manager.py` |
| Idempotent install scripts | Shell / PowerShell | `setup/claude-code/install.sh`, `install.ps1` |
| Rewritten CLAUDE.md | Markdown | Repo root |
| `.gitignore` exception | Text | `.gitignore` |
| PLANS-INDEX.md with Phase 6/7 backfill | Markdown | `.advanced-plans/PLANS-INDEX.md` |

## Success Criteria

- ✓ `.advanced-plans/` exists at repo root with the full tree (README, PLANNING, PLANS-INDEX, master-plan, phases/, specs/, state/, logs/)
- ✓ Old `plans/`, `.claude/state/`, `.claude/logs/` directories removed from the repo
- ✓ `.claude/` contains only Claude-Code runtime (commands, agents, skills, schemas, settings.json)
- ✓ `.gitignore` has `!.claude/settings.json` exception; `git ls-files .claude/settings.json` returns the file
- ✓ `PLANNING.md` exists with fully populated frontmatter reflecting current programme state
- ✓ `README.md` exists, documents the layout, references PLANNING.md as the live dashboard
- ✓ All slash commands work end-to-end against new layout — verified by running `/next-loop` on a fresh test programme
- ✓ `python -m pytest platforms/python/tests/ -v` passes
- ✓ `git log --follow .advanced-plans/phases/phase-1/plan.md` shows history dating to Phase 1's original creation
- ✓ PLANS-INDEX.md covers Phases 1–8 inclusive (Phase 6/7 gap closed)
- ✓ Grep audit: zero occurrences of `plans/`, `.claude/state/`, `.claude/logs/`, `.claude/plans/` in `core/`, `platforms/`, `CLAUDE.md`, or any `SKILL.md` file
- ✓ `.claude/settings.json` (both repo-root and `platforms/claude-code/`) contains a permission allow rule for `.advanced-plans/**` covering Read, Write, Edit, MultiEdit — verified by writing a test file to `.advanced-plans/test.md` with no permission prompt

## Dependencies

### Must Complete Before
- **Phase 8 close-out**: Loop 027 complete and committed; Loops 028–031 explicitly absorbed into Phase 9 (not executed under Phase 8). PLANS-INDEX and CLAUDE.md updated to reflect Phase 8 closure. State bus must show no `loop-ready.json` (no in-flight work).
- **Clean working tree in source directories**: `git status` must show no uncommitted changes in `plans/`, `.claude/state/`, or `.claude/logs/` at Phase 9 start (Wave 1 precondition).

### Blocked By
- None external

### Optional
- None

## Skills Required (Broad Categories)

- `file-migration`: Batch `git mv` operations across nested directories, history preservation, post-move verification
- `command-rewriting`: Slash command edits, path standardisation across ~10 commands, rename mechanics
- `permission-config`: Hook allowlist patterns and settings.json `allow` rules; understanding of dual-allow transition state
- `python-refactor`: Path constant updates in `plan_io.py` and `state_manager.py`; preserve zero-dependency invariant
- `shell-scripting`: POSIX sh + PowerShell install script logic; idempotent old-layout detection and in-place migration
- `docs-rewrite`: CLAUDE.md restructure, README/PLANNING authoring, skill doc updates
- `schema-design`: PLANNING.md frontmatter schema definition, plan.md frontmatter alignment

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Git history lost on moves | Low | High | Use `git mv` exclusively; Wave 2 verifies with `git log --follow` on a sample file before proceeding |
| Stale references hide in tests / markdownlint / CI / skill docs | Med | Med | Final grep audit in Wave 5 covers all four roots; failure blocks gate |
| Hook config blocks its own migration mid-flight | Med | High | Wave 1 patches hook allowlists to allow BOTH old and new paths; Wave 4 narrows to new-only after migration completes |
| In-flight loop state at migration time | Low | High | Phase 9 only starts when no `loop-ready.json` is present; Phase 8 close-out ensures this |
| Cross-platform path separators (Windows) | Low | Med | All paths in source code use forward slashes; `pathlib.Path` for filesystem ops |
| Existing target-project installations break | Med | Med | `install.sh` becomes idempotent — detects old layout, performs in-place migration, prints summary |
| Frontmatter drifts out of sync with actual state | Med | Low | Commands maintain it as part of their existing state-update steps; CI lint deferred |
| Uncommitted changes in source dirs at migration time | Med | High | Wave 1 first step: refuse to proceed if `git status` shows changes in source dirs; user must commit/stash/discard first |

## Assumptions

- **No in-flight loop at Phase 9 start**: Phase 8 close-out commits Loop 027 cleanly and removes `loop-ready.json` / `loop-complete.json`. Validated by checking `.claude/state/` is empty of these files before Wave 1.
- **Single-user project**: Big-bang migration is safe without dual-path code. Validated by absence of forks or external contributors using non-default branches.
- **`git mv` preserves history**: Industry-standard; trusted but verified with `git log --follow` on a sample file in Wave 2.
- **Forward-slash paths in source work cross-platform via `pathlib`**: Existing Python code already follows this; Phase 9 doesn't introduce new path handling.
- **Hook dual-allow during migration is safe**: Patterns will match either old or new paths during Wave 1–3; Wave 4 narrows to new-only after old paths are gone.

## Notes / Design Decisions

- **Why hidden `.advanced-plans/` rather than visible `advanced-plans/`**: Locked in brainstorming. Tidy at repo root; signals framework ownership without visual clutter.
- **Why split README + PLANNING**: Different audiences. README is static onboarding ("what is this directory"); PLANNING is live machine-readable state (frontmatter-driven dashboard).
- **Why fold Phase 8 Loops 028–031 in**: They touch the same surface area (commands, hooks, CLAUDE.md, skill docs). Doing them under the old layout then immediately rewriting under the new one would be wasteful churn.
- **Why big-bang migration**: Single primary user, pre-1.0 framework. Dual-path code is overhead that pays off only if external consumers depend on the old layout, which they don't.
- **Open question for ralph-loop-planner**: whether Wave 3 (command rewrites + Phase 8 absorption) is one loop or two. Estimated ~10 command files + 4 absorbed sub-tasks = roughly 14 todos; may want to split.

## Ralph Loops (5)

| Loop | Name | Type | Key Outputs |
|---|---|---|---|
| 032 | Skeleton + Preconditions | Migration setup | `.advanced-plans/` tree created; initial README + PLANNING with frontmatter; `.gitignore` exception; hook dual-allow patches |
| 033 | File Migration | Migration | All plans/loops/verdicts/completes/specs/state/logs `git mv`'d to new homes; old dirs deleted; history verified |
| 034 | Command Rewrites + Phase 8 Absorption | Implementation | All slash commands target new paths; `/new-loop` renamed to `/decompose-phase` with bugs fixed; sentinel + progress-report + disambiguation work done |
| 035 | Hooks + Permissions + Python + Install | Implementation | Hook allowlists narrowed; permission allow rules updated; Python path constants updated; install scripts idempotent |
| 036 | Docs + Tests + Backfill + Audit | Implementation + verification | CLAUDE.md rewritten; skill docs updated; tests passing; CI filters updated; PLANS-INDEX backfilled for Phases 6/7; grep audit clean |
