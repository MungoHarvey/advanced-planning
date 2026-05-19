---
phase: 9
title: ".advanced-plans/ Restructure"
status: passed
gate_verdict_ref: .advanced-plans/gate-verdicts/phase-9-attempt-2-phase-goals-agent.json
anchor_sha: ecdfca4
end_sha: 19199d3
commit_count: 13
loop_count: 5
created: 2026-05-19T09:05:00Z
---

## Goals met
- `.advanced-plans/` tree exists at repo root (README, PLANNING, PLANS-INDEX, master-plan, phases/, specs/, state/, logs/) — verified ls; attempt-2 phase-goals verdict.
- Old `plans/`, `.claude/state/`, `.claude/logs/` removed — all three ls return "No such file or directory".
- `.claude/` holds only runtime (settings.json, settings.local.json, skills/) — stray empty `.claude/plans/` removed in 19199d3.
- `.gitignore` `!.claude/settings.json` exception present; `git ls-files` returns the file — .gitignore line 6.
- `PLANNING.md` frontmatter fully populated (programme status, phases, gate_status, state_files).
- `README.md` documents the layout and references PLANNING.md as the live dashboard.
- All slash commands target the new layout; attempt-1 double-prefix corruption fully remediated — code-review-agent attempt-2 PASS confirms zero `.advanced-.advanced-plans` in command files.
- `pytest platforms/python/tests/` → 72 passed (0.65s).
- `git log --follow .advanced-plans/phases/phase-1/plan.md` traces through migrate 65903f5 to original release 5ec7168.
- PLANS-INDEX covers Phases 1–9 incl. Phase 6 (019–022) and Phase 7 (023–026); 6/7 gap closed.
- Grep audit: zero live old-path or double-prefix references in core/, platforms/, CLAUDE.md (intentional legacy shims excluded).
- Permission allow rules for `.advanced-plans/**` (R/W/E/ME) in both `.claude/settings.json` and `platforms/claude-code/settings.json`.

## Deferred
- (none)

## Opened
- `phase-9/plan.md` frontmatter `design_spec` still points to old `plans/2026-05-14-...` path (info; spec now under `.advanced-plans/specs/`; no runtime impact).
- `setup/claude-code/README.md` still documents the old `plans/` + `.claude/state/` layout (important; user-facing install doc, was outside the criteria-bearing grep-audit scope).
- `history.jsonl` recorded zero `loop_complete` events for Phase 9 (loops 032–036 were main-thread driven); loop_count derived from git `complete: ralph-loop-03X` commits and plan frontmatter instead.
