# Phase 9 — Ralph Loops

5 loops decomposing the `.advanced-plans/` Restructure phase plan.

Source: `plans/phase-9.md`
Design: `plans/2026-05-14-advanced-plans-restructure-design.md`

---

```yaml
---
name: "ralph-loop-032"
task_name: "Skeleton + Preconditions"
max_iterations: 3
on_max_iterations: checkpoint

handoff_summary:
  done: "Created .advanced-plans/ skeleton (phases/, specs/, state/, logs/), authored README.md and PLANNING.md with full 10-field frontmatter, added !.claude/settings.json gitignore exception (file now tracked), and patched hook allowlists in both settings.json and hooks.json to dual-allow old (plans/*, .claude/state/*) and new (.advanced-plans/*) paths."
  failed: ""
  needed: "Run Loop 033 to perform git mv file migration from plans/, .claude/state/, .claude/logs/ into .advanced-plans/."

todos:
  - id: "loop-032-1"
    content: "Verify clean working tree: run `git status` and confirm no uncommitted changes in plans/, .claude/state/, or .claude/logs/. Abort if any exist; user must commit/stash/discard first."
    skill: "NA"
    agent: "NA"
    outcome: "Working tree shows no unstaged/staged changes in the three source directories; if it does, loop halts with explicit user-action message and no further todos run."
    status: completed
    priority: high
  - id: "loop-032-2"
    content: "Verify no in-flight loop: confirm `.claude/state/loop-ready.json` either does not exist or has status != 'ready'. Abort if a live loop is detected."
    skill: "NA"
    agent: "NA"
    outcome: "loop-ready.json absent or its status field is not 'ready'; precondition documented in commit log."
    status: completed
    priority: high
  - id: "loop-032-3"
    content: "Create .advanced-plans/ directory tree: top-level dir + phases/, specs/, state/, logs/ subdirectories. No files yet — just the empty skeleton."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: ".advanced-plans/ exists at repo root with phases/, specs/, state/, logs/ subdirs; verified by `ls -la .advanced-plans/`."
    status: completed
    priority: high
  - id: "loop-032-4"
    content: "Add `!.claude/settings.json` exception to .gitignore so the file from Loop 027 becomes trackable. Verify with `git check-ignore -v .claude/settings.json` (should NOT match an ignore rule)."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: ".gitignore contains `!.claude/settings.json` line; `git ls-files .claude/settings.json` returns the path after a single `git add`."
    status: completed
    priority: high
  - id: "loop-032-5"
    content: "Patch hook allowlists in platforms/claude-code/settings.json and platforms/claude-code/hooks/hooks.json to allow BOTH old paths (plans/*, .claude/state/*) AND new paths (.advanced-plans/*) so migration steps in later loops aren't blocked."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Both hook config files contain glob patterns matching both old and new path families; settings.json and hooks.json remain byte-identical for the planning-mode block."
    status: completed
    priority: high
  - id: "loop-032-6"
    content: "Author initial .advanced-plans/README.md: directory map (the layout tree), conventions (frontmatter required on plan.md / loops.md / PLANNING.md), workflow cheat sheet (which slash command does what), and explicit pointer to PLANNING.md as the live dashboard."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: ".advanced-plans/README.md exists, includes a directory tree diagram, lists all framework slash commands with one-line purposes, and links to PLANNING.md as the live state file."
    status: completed
    priority: medium
  - id: "loop-032-7"
    content: "Author initial .advanced-plans/PLANNING.md with YAML frontmatter populated from current programme state: programme name, status: in_progress, current_phase: 9, current_loop: ralph-loop-032 (this one), gate_status: not_due, next_action: '/next-loop', active_branches: [main], phases.complete: [1,2,3,4,5,6,7,8], phases.pending: [9], state_files pointing to .advanced-plans/state/* (where they'll live after Loop 033)."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: ".advanced-plans/PLANNING.md exists; frontmatter parses as valid YAML; all 10 fields from the design spec are populated; last_updated: 2026-05-15."
    status: completed
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Create the `.advanced-plans/` skeleton and gate preconditions so subsequent loops can perform the file migration safely.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-032"

  ## Success criteria
  - [ ] `.advanced-plans/` directory tree exists with all four subdirs (phases/, specs/, state/, logs/)
  - [ ] `.advanced-plans/README.md` exists with directory map + workflow cheat sheet
  - [ ] `.advanced-plans/PLANNING.md` exists with fully populated YAML frontmatter
  - [ ] `.gitignore` contains `!.claude/settings.json`; the settings file is now tracked
  - [ ] Hook allowlists in both settings.json and hooks.json allow `.advanced-plans/**` paths
  - [ ] Preconditions documented: clean working tree, no in-flight loop

  ## Required skills
  - None (NA): mechanical file/dir creation and JSON/YAML editing

  ## Inputs
  - Phase 9 plan: `plans/phase-9.md`
  - Design spec: `plans/2026-05-14-advanced-plans-restructure-design.md`
  - PLANNING.md frontmatter schema: see design spec section "PLANNING.md Frontmatter"

  ## Expected outputs
  - `.advanced-plans/` directory tree (skeleton; populated by Loop 033)
  - `.advanced-plans/README.md`
  - `.advanced-plans/PLANNING.md` (with frontmatter)
  - `.gitignore` updated
  - Hook allowlists patched (dual-allow)

  ## Constraints
  - Do NOT delete any old paths in this loop — Loop 033 handles migration; this loop only adds.
  - Do NOT yet update CLAUDE.md, slash commands, Python constants, or skill docs.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-032 — skeleton + preconditions"
  2. Update handoff_summary
  3. Mark all todos completed
  4. Write .claude/state/loop-complete.json

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

---

```yaml
---
name: "ralph-loop-033"
task_name: "File Migration"
max_iterations: 3
on_max_iterations: rollback

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-033-1"
    content: "Migrate phase plans: for each phase N in {1,2,3,4,5,6,7,8}, run `git mv plans/phase-N.md .advanced-plans/phases/phase-N/plan.md`. Create the phase-N/ subdir first if absent."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Each `.advanced-plans/phases/phase-N/plan.md` exists; old `plans/phase-N.md` does not; `git log --follow` on plan.md shows the original phase-N.md commits."
    status: completed
    priority: high
  - id: "loop-033-2"
    content: "Migrate ralph-loop files: for each phase N with `plans/phase-N-ralph-loops.md`, run `git mv` to `.advanced-plans/phases/phase-N/loops.md`."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Each phase-N's loops.md is co-located with plan.md under phases/phase-N/; old files gone; history preserved."
    status: completed
    priority: high
  - id: "loop-033-3"
    content: "Migrate gate verdicts: enumerate plans/gate-verdicts/phase-N-*.json files, group by phase, and `git mv` each into `.advanced-plans/phases/phase-N/gate-verdicts/`. Create subdir as needed."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "All gate verdict JSON files now live under their respective phases/phase-N/gate-verdicts/ subfolders; plans/gate-verdicts/ is empty."
    status: completed
    priority: high
  - id: "loop-033-4"
    content: "Migrate phase completion artefacts: `git mv plans/phase-completes/phase-N-complete.md` → `.advanced-plans/phases/phase-N/complete.md` for each existing file."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Each existing phase complete.md sits beside that phase's plan.md and loops.md; plans/phase-completes/ is empty."
    status: completed
    priority: high
  - id: "loop-033-5"
    content: "Migrate design specs: `git mv plans/2026-*.md` (any date-prefixed design doc, including this restructure's own spec) → `.advanced-plans/specs/`."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "All design specs reside in `.advanced-plans/specs/`; the file `.advanced-plans/specs/2026-05-14-advanced-plans-restructure-design.md` exists."
    status: completed
    priority: high
  - id: "loop-033-6"
    content: "Migrate top-level navigation files: `git mv plans/PLANS-INDEX.md` and `plans/master-plan.md` → `.advanced-plans/`."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "`.advanced-plans/PLANS-INDEX.md` and `.advanced-plans/master-plan.md` exist; old top-level files in plans/ are gone."
    status: completed
    priority: high
  - id: "loop-033-7"
    content: "Migrate state bus: `git mv .claude/state/loop-ready.json`, `loop-complete.json`, `history.jsonl` → `.advanced-plans/state/`."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "`.advanced-plans/state/` contains the three state files; `.claude/state/` is empty (or has only an `.archive/` subdir if previously created)."
    status: completed
    priority: high
  - id: "loop-033-8"
    content: "Migrate logs: `git mv .claude/logs/execution.log` (and any other log files) → `.advanced-plans/logs/`."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "All log files moved; `.claude/logs/` is empty."
    status: completed
    priority: medium
  - id: "loop-033-9"
    content: "Verify history preservation: run `git log --follow .advanced-plans/phases/phase-1/plan.md` and confirm the output includes commits predating today's session (i.e. the original Phase 1 creation in `plans/phase-1.md`)."
    skill: "NA"
    agent: "NA"
    outcome: "`git log --follow` on the sample file shows at least the original Phase 1 commit; if not, halt the loop and roll back via on_max_iterations: rollback."
    status: in_progress
    priority: high
  - id: "loop-033-10"
    content: "Remove now-empty source directories: `rmdir plans/gate-verdicts plans/phase-completes plans/ .claude/state/ .claude/logs/`. If any directory is non-empty, list its contents in the handoff and STOP — do not force-delete."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Old directories deleted; `ls plans/` and `ls .claude/state/` and `ls .claude/logs/` all return 'no such file or directory'. Any non-empty case is flagged in handoff.failed."
    status: pending
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Move every plan, loop file, gate verdict, completion artefact, design spec, state file, and log into `.advanced-plans/` via `git mv`, preserving history.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-033"

  ## Success criteria
  - [ ] All phase plans live at `.advanced-plans/phases/phase-N/plan.md`
  - [ ] All ralph-loop files live at `.advanced-plans/phases/phase-N/loops.md`
  - [ ] All gate verdicts live under their phase's `gate-verdicts/` subdir
  - [ ] All phase completion artefacts live at `.advanced-plans/phases/phase-N/complete.md`
  - [ ] All design specs live in `.advanced-plans/specs/`
  - [ ] PLANS-INDEX.md and master-plan.md live at `.advanced-plans/` root
  - [ ] State bus files live in `.advanced-plans/state/`
  - [ ] Log files live in `.advanced-plans/logs/`
  - [ ] `git log --follow` on a sample plan.md shows pre-migration history
  - [ ] Old `plans/`, `.claude/state/`, `.claude/logs/` directories no longer exist

  ## Required skills
  - None (NA): mechanical `git mv` operations

  ## Inputs
  - `.advanced-plans/` skeleton from Loop 032
  - Source directories: `plans/`, `.claude/state/`, `.claude/logs/`

  ## Expected outputs
  - Fully populated `.advanced-plans/phases/*/` subdirectories
  - Populated `.advanced-plans/specs/`, `.advanced-plans/state/`, `.advanced-plans/logs/`
  - Deleted source directories
  - Single commit recording the migration

  ## Constraints
  - Use `git mv` EXCLUSIVELY — never `cp` + `rm`, never `mv` outside of git.
  - Do NOT yet update any command file, hook config, Python constant, or doc — Loops 034–036 handle those.
  - on_max_iterations: rollback — if any step fails verification (especially the history check at todo 9), reset the working tree to the pre-loop checkpoint.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-033 — file migration"
  2. Update handoff_summary
  3. Mark all todos completed
  4. Update PLANNING.md frontmatter current_loop → ralph-loop-034
  5. Write .advanced-plans/state/loop-complete.json (NEW location now valid)

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

---

```yaml
---
name: "ralph-loop-034"
task_name: "Command Rewrites + Phase 8 Absorption"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-034-1"
    content: "Rewrite /next-loop command in platforms/claude-code/commands/next-loop.md to target .advanced-plans/ paths everywhere (replace .claude/plans/, plans/, .claude/state/ references). Fix step-1 plan-lookup bug logged in friction log."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "next-loop.md contains no occurrence of `plans/`, `.claude/plans/`, or `.claude/state/`; all references read from `.advanced-plans/...`."
    status: pending
    priority: high
  - id: "loop-034-2"
    content: "Rename /new-loop → /decompose-phase: `git mv platforms/claude-code/commands/new-loop.md platforms/claude-code/commands/decompose-phase.md`, update command name in frontmatter, fix `.md.md` template bug, fix save-location convention (write to `.advanced-plans/phases/phase-N/loops.md`)."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "decompose-phase.md exists; new-loop.md does not; command frontmatter name field is `decompose-phase`; no `.md.md` substring anywhere in the file; output path references `.advanced-plans/phases/phase-N/loops.md`."
    status: pending
    priority: high
  - id: "loop-034-3"
    content: "Rewrite /next-phase command to target new paths: gate-verdict reads from `.advanced-plans/phases/phase-N/gate-verdicts/`, phase plan reads from `.advanced-plans/phases/phase-N/plan.md`."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "next-phase.md contains no old-path references; all gate-verdict and phase-plan lookups use `.advanced-plans/`."
    status: pending
    priority: high
  - id: "loop-034-4"
    content: "Rewrite /run-gate command to write verdicts to `.advanced-plans/phases/phase-N/gate-verdicts/` instead of `plans/gate-verdicts/`. Update gate-review-mode sentinel allowlist references."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "run-gate.md writes to `.advanced-plans/phases/phase-N/gate-verdicts/`; no plans/gate-verdicts/ references."
    status: pending
    priority: high
  - id: "loop-034-5"
    content: "Rewrite /phase-compact command to read source from `.advanced-plans/phases/phase-N/` and write the complete.md output to `.advanced-plans/phases/phase-N/complete.md`. Update PLANS-INDEX manifest-append step to target `.advanced-plans/PLANS-INDEX.md`."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "phase-compact.md targets new paths only; the manifest-append step's bug (Phases 6/7 gap, per friction log) is patched."
    status: pending
    priority: high
  - id: "loop-034-6"
    content: "Rewrite /progress-report command: target new paths AND deduplicate overlapping logic with /loop-status (Phase 8 Loop 029 absorbed). Decide a clear division: /loop-status = current state snapshot, /progress-report = historical synthesis."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "progress-report.md and loop-status.md have non-overlapping descriptions; both target new paths; CLAUDE.md will be updated in Loop 036 to reflect the new boundary."
    status: pending
    priority: medium
  - id: "loop-034-7"
    content: "Rewrite /loop-status, /check-execution, /run-closeout, /model-check commands to target new paths. Each should be a path-substitution pass with no logic changes (except /loop-status which gets clearer scope per todo-6)."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "All four command files contain no occurrence of `plans/`, `.claude/plans/`, `.claude/state/`, or `.claude/logs/`."
    status: pending
    priority: high
  - id: "loop-034-8"
    content: "Consolidate sentinel ownership (Phase 8 Loop 028 absorbed): identify every reference to the planning-mode and gate-review-mode sentinels across commands, hooks, and docs; establish a single source of truth (likely a small section in CLAUDE.md or a dedicated file under .advanced-plans/) and update all references to point there."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Each sentinel has one canonical owning location; other references link or quote it rather than redefining. Grep for sentinel pattern strings shows references in ≤3 files (the owner + at most 2 places that quote with attribution)."
    status: pending
    priority: medium
  - id: "loop-034-9"
    content: "Disambiguate overlapping command surfaces (Phase 8 Loop 031 absorbed): produce a one-page command-surface map in CLAUDE.md showing which command does what and how they relate. Eliminate any two commands that are subsets of each other."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "CLAUDE.md contains a command-surface table; no two listed commands have overlapping core purposes; PLANS-INDEX.md workflow section aligns with the new table."
    status: pending
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Update every slash command to target `.advanced-plans/` paths, rename `/new-loop` → `/decompose-phase` with bug fixes, and absorb the consolidation/dedup/disambiguation work from Phase 8 Loops 028–031.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-034"

  ## Success criteria
  - [ ] Every file in `platforms/claude-code/commands/` contains zero references to `plans/`, `.claude/plans/`, `.claude/state/`, `.claude/logs/`
  - [ ] `decompose-phase.md` exists; `new-loop.md` does not
  - [ ] No `.md.md` substring anywhere in the commands directory
  - [ ] `/progress-report` and `/loop-status` have non-overlapping descriptions
  - [ ] Sentinels have one canonical owning location each
  - [ ] CLAUDE.md command-surface table exists (the table is final-edited in Loop 036, but its structure is decided here)

  ## Required skills
  - None (NA): structured markdown edits, path substitutions, file rename via `git mv`

  ## Inputs
  - All files in `platforms/claude-code/commands/`
  - Phase 8 plan: `plans/phase-8.md` (read but do not execute its absorbed Loops 028–031 separately — they happen here)
  - Friction log entries on /new-loop, /next-loop path bugs

  ## Expected outputs
  - All rewritten command files
  - Renamed `decompose-phase.md`
  - Notes on sentinel ownership decisions in handoff.done for Loop 036's CLAUDE.md rewrite
  - Notes on the /progress-report vs /loop-status boundary

  ## Constraints
  - Do NOT yet narrow the hook allowlists — they still need to allow old paths because Phase 9's own state files moved in Loop 033 but the worker spawning machinery may still reference both during a transition window. Wave 4 (Loop 035) narrows.
  - Preserve each command's behaviour; this is a path-substitution + light cleanup pass, not a redesign.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-034 — command rewrites + phase 8 absorption"
  2. Update handoff_summary (include sentinel-ownership decisions and the /progress-report vs /loop-status boundary in handoff.done for Loop 036 to consume)
  3. Mark all todos completed
  4. Update PLANNING.md frontmatter current_loop → ralph-loop-035

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

---

```yaml
---
name: "ralph-loop-035"
task_name: "Hooks + Permissions + Python + Install"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-035-1"
    content: "Narrow hook allowlists in platforms/claude-code/settings.json: drop the dual-allow patterns from Loop 032; keep only `.advanced-plans/**` patterns for planning-mode and gate-review-mode PreToolUse blocks."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "settings.json contains no `plans/*` or `.claude/plans/*` or `.claude/state/*` patterns in hook blocks; only `.advanced-plans/**`-anchored patterns remain."
    status: pending
    priority: high
  - id: "loop-035-2"
    content: "Apply the identical narrowing to platforms/claude-code/hooks/hooks.json. Verify diff between settings.json and hooks.json shows no discrepancy in hook blocks (use `python -c` or `diff` on extracted blocks)."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "hooks.json hook blocks are byte-identical to settings.json hook blocks; verified by a script-or-manual diff."
    status: pending
    priority: high
  - id: "loop-035-3"
    content: "Update permission allow rules in repo-root .claude/settings.json: replace the existing `plans/**`, `.claude/state/**`, `.claude/logs/**` triplet with a single `.advanced-plans/**` rule covering Read, Write, Edit, MultiEdit. Preserve any unrelated allow rules."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: ".claude/settings.json permissions.allow array contains `.advanced-plans/**` entries for Read/Write/Edit/MultiEdit; no old-path entries remain."
    status: pending
    priority: high
  - id: "loop-035-4"
    content: "Apply the same permission-rule update to platforms/claude-code/settings.json (the adapter that gets installed into target projects) so installs auto-allow `.advanced-plans/**`."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "platforms/claude-code/settings.json permissions.allow mirrors the repo-root file's `.advanced-plans/**` rules."
    status: pending
    priority: high
  - id: "loop-035-5"
    content: "Update path constants in platforms/python/plan_io.py: any reference to `plans/`, `phase-completes/`, `gate-verdicts/`, etc., re-pointed to the new `.advanced-plans/` structure. Preserve zero-dependency invariant (no new external imports)."
    skill: "NA"
    agent: "analysis-worker"
    outcome: "plan_io.py path constants resolve to `.advanced-plans/phases/phase-N/plan.md`, `.advanced-plans/specs/`, etc.; `python -m pytest platforms/python/tests/test_plan_io.py -v` passes."
    status: pending
    priority: high
  - id: "loop-035-6"
    content: "Update path constants in platforms/python/state_manager.py: state-bus paths re-pointed to `.advanced-plans/state/`. Preserve zero-dependency invariant."
    skill: "NA"
    agent: "analysis-worker"
    outcome: "state_manager.py reads/writes to `.advanced-plans/state/`; `python -m pytest platforms/python/tests/test_state_manager.py -v` passes."
    status: pending
    priority: high
  - id: "loop-035-7"
    content: "Update setup/claude-code/install.sh: create `.advanced-plans/` skeleton in target projects (with starter README + PLANNING template); add idempotent migration logic that detects old layouts (existence of `plans/` or `.claude/state/`) and migrates them in place; stop creating `.claude/state/` and `.claude/logs/`."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "install.sh creates `.advanced-plans/` tree; detects + migrates `plans/` and `.claude/state/` if present; no longer creates `.claude/state/` or `.claude/logs/`; passes a shellcheck or syntax pass."
    status: pending
    priority: high
  - id: "loop-035-8"
    content: "Apply equivalent logic to setup/claude-code/install.ps1: PowerShell-idiomatic version of the same migration logic, using forward-slash paths internally."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "install.ps1 has feature parity with install.sh; runs without parse errors on Windows PowerShell."
    status: pending
    priority: high
  - id: "loop-035-9"
    content: "Run the AST import checker on platforms/python/ to confirm zero external imports were introduced. Run `python -m pytest platforms/python/tests/ -v` and confirm all tests pass with updated path constants."
    skill: "NA"
    agent: "NA"
    outcome: "AST checker passes; full pytest suite passes; pytest count ≥ pre-loop count (no tests skipped or removed)."
    status: pending
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Narrow hook allowlists to new paths only; update permission allow rules in both `.claude/settings.json` files for `.advanced-plans/**` auto-allow; update Python path constants; make install scripts idempotently migrate target projects.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-035"

  ## Success criteria
  - [ ] Hook allowlists in both settings.json and hooks.json contain only `.advanced-plans/**`-anchored patterns
  - [ ] Permission allow rules in both `.claude/settings.json` (repo-root + adapter) cover `.advanced-plans/**` for Read/Write/Edit/MultiEdit
  - [ ] plan_io.py and state_manager.py path constants resolve to `.advanced-plans/...`
  - [ ] install.sh and install.ps1 create `.advanced-plans/` skeleton and migrate old layouts
  - [ ] `python -m pytest platforms/python/tests/ -v` passes; AST import checker passes

  ## Required skills
  - None (NA) for hooks/permissions/install — JSON + shell edits
  - `analysis-worker` for Python constant updates (touches multiple modules; benefits from isolation)

  ## Inputs
  - Hook configs: `platforms/claude-code/settings.json`, `platforms/claude-code/hooks/hooks.json`
  - Permission configs: `.claude/settings.json`, `platforms/claude-code/settings.json`
  - Python modules: `platforms/python/plan_io.py`, `state_manager.py`
  - Install scripts: `setup/claude-code/install.sh`, `install.ps1`

  ## Expected outputs
  - All five config/script types updated for new layout
  - Verified test pass + AST clean

  ## Constraints
  - Preserve zero-dependency invariant in Python — standard library only (CI enforces).
  - Use forward-slash paths in PowerShell where possible; rely on `pathlib` or `Join-Path` for OS-specific work.
  - Do NOT yet update CLAUDE.md, SKILL.md files, tests path globs, or markdownlint config — Loop 036 covers all that.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-035 — hooks + permissions + python + install"
  2. Update handoff_summary
  3. Mark all todos completed
  4. Update PLANNING.md frontmatter current_loop → ralph-loop-036

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```

---

```yaml
---
name: "ralph-loop-036"
task_name: "Docs + Tests + Backfill + Audit"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-036-1"
    content: "Rewrite CLAUDE.md: Architecture, Runtime Directory, Workflow sections updated for `.advanced-plans/` layout. Remove any existing 'Planning State' section. Add a one-line pointer to `.advanced-plans/PLANNING.md` near the top of the file (under the project overview)."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "CLAUDE.md contains the pointer line; no 'Planning State' section remains; Architecture and Workflow sections describe `.advanced-plans/` exclusively; no `plans/` or `.claude/state/` references."
    status: pending
    priority: high
  - id: "loop-036-2"
    content: "Add the command-surface table (decided in Loop 034) to CLAUDE.md with clear non-overlapping purposes; align with PLANS-INDEX.md's workflow block. Use the boundary decision from Loop 034's handoff: /loop-status = current state, /progress-report = historical synthesis."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "CLAUDE.md contains a single command-surface table; PLANS-INDEX.md's workflow block references the same canonical list; no contradictions between the two."
    status: pending
    priority: high
  - id: "loop-036-3"
    content: "Update every SKILL.md reference to `.claude/plans/` or top-level `plans/` across both core/skills/ and any global skills under platforms/. Includes ralph-loop-planner, phase-plan-creator, companion-detection, plan-todos, plan-skill-identification, plan-subagent-identification."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Grep for `plans/` and `.claude/plans/` in all SKILL.md files (core/skills/, platforms/*/skills/, ~/.claude/skills/ for any framework-installed skills) returns zero matches."
    status: pending
    priority: high
  - id: "loop-036-4"
    content: "Update pytest path references in platforms/python/tests/*.py: any fixture or constant referencing old paths re-pointed to `.advanced-plans/`. Add at least one test asserting the new path structure."
    skill: "NA"
    agent: "analysis-worker"
    outcome: "All tests reference `.advanced-plans/` paths exclusively; pytest suite passes; at least one new test asserts that `.advanced-plans/phases/phase-N/plan.md` is the canonical path."
    status: pending
    priority: high
  - id: "loop-036-5"
    content: "Update markdownlint config (if present in repo) and CI workflow path filters in .github/workflows/ci.yml to reference `.advanced-plans/**` instead of `plans/**`."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "markdownlint config lints `.advanced-plans/**`; CI workflow path filters trigger on `.advanced-plans/**` changes; CI passes on a test push."
    status: pending
    priority: medium
  - id: "loop-036-6"
    content: "Backfill Phase 6 and Phase 7 entries in `.advanced-plans/PLANS-INDEX.md`: add their Phases table rows from the compaction manifests in `.advanced-plans/phases/phase-6/complete.md` and `phase-7/complete.md`; add their loops (019-022 for Phase 6, 023-026 for Phase 7) to the Ralph Loops table."
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "PLANS-INDEX.md Phases table contains rows for Phases 1-9 inclusive; Ralph Loops table contains entries for loops 001-036 inclusive; the 'Index gap' note is removed."
    status: pending
    priority: high
  - id: "loop-036-7"
    content: "Run the final grep audit: search for `plans/`, `.claude/state/`, `.claude/logs/`, `.claude/plans/` across `core/`, `platforms/`, `CLAUDE.md`, and all `SKILL.md` files. Any match is a blocker — document and fix before proceeding."
    skill: "NA"
    agent: "NA"
    outcome: "Grep audit returns zero matches across all four search roots; result documented in handoff.done."
    status: pending
    priority: high
  - id: "loop-036-8"
    content: "Smoke test: write a throwaway file to `.advanced-plans/test.md` (e.g. `echo test > .advanced-plans/test.md`) and confirm no permission prompt is triggered. Delete the test file. Document outcome (pass/fail) in handoff."
    skill: "NA"
    agent: "NA"
    outcome: "Permission rules verified end-to-end; test file written without prompt, then cleaned up; result recorded."
    status: pending
    priority: medium
  - id: "loop-036-9"
    content: "Final verification: confirm `python -m pytest platforms/python/tests/ -v` passes; confirm `git log --follow .advanced-plans/phases/phase-1/plan.md` shows the original Phase 1 commit; confirm `git ls-files .claude/settings.json` returns the file (tracked via gitignore exception). All three are gate-blocking."
    skill: "NA"
    agent: "NA"
    outcome: "All three verifications pass; recorded in handoff.done as 'Phase 9 ready for gate review'."
    status: pending
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Rewrite all documentation, update tests + CI filters, backfill Phases 6/7 in PLANS-INDEX, run the final grep audit, and verify migration end-to-end. This loop produces the gate-ready state.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-036"

  ## Success criteria
  - [ ] CLAUDE.md rewritten with PLANNING.md pointer + command-surface table
  - [ ] All SKILL.md files reference new paths exclusively
  - [ ] pytest suite passes
  - [ ] markdownlint + CI filters target new paths
  - [ ] PLANS-INDEX.md covers Phases 1-9 inclusive (Phase 6/7 gap closed)
  - [ ] Grep audit returns zero matches for old paths in all four search roots
  - [ ] Smoke test: write to `.advanced-plans/test.md` produces no permission prompt
  - [ ] git log --follow on sample plan.md shows pre-migration history
  - [ ] .claude/settings.json is tracked

  ## Required skills
  - None (NA) for docs / audit / verification
  - `analysis-worker` for pytest path updates (multi-file change benefits from isolation)

  ## Inputs
  - All previous loops' outputs (especially Loop 034's sentinel + command-boundary decisions in handoff)
  - CLAUDE.md, SKILL.md files, pytest fixtures, markdownlint config, CI workflow
  - Phase 6/7 compaction manifests at `.advanced-plans/phases/phase-6/complete.md`, `phase-7/complete.md`

  ## Expected outputs
  - Rewritten CLAUDE.md
  - Updated SKILL.md files
  - Updated pytest tests, markdownlint config, CI workflow
  - Backfilled PLANS-INDEX.md
  - Clean grep audit output recorded in handoff
  - All gate-ready verifications recorded in handoff

  ## Constraints
  - This is the last loop before gate review; do NOT introduce new scope.
  - If any verification fails, halt and surface the failure via on_max_iterations: escalate.

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-036 — docs + tests + backfill + audit"
  2. Update handoff_summary; set `needed: "Run /run-gate for Phase 9"`
  3. Update PLANNING.md frontmatter: current_loop → null, gate_status → pending, next_action → "/run-gate"
  4. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---
```
