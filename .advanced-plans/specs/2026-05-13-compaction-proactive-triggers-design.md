# Design: Compaction Proactive Triggers & Tapered Strategy

**Date:** 2026-05-13
**Branch:** main
**Status:** DRAFT — pending /plan-eng-review
**Supersedes (partially):** `~/.gstack/projects/MungoHarvey-advanced-planning/mharvey2-main-design-20260513-103520.md` §7.2 (Hook event mechanism) and §7.3 (Clear-and-reload ownership). The original design's "main thread polls history.jsonl" approach is replaced by the PreCompact hook architecture below. All other sections of the original design remain authoritative.

---

## Problem

After Phase 7 shipped, three findings reshaped Phase 8 and 9 scope:

1. **`/compact` accepts a custom prompt** (`/compact <instructions>`). The original design treated /compact as an opaque user action; in fact it can be precisely guided.
2. **The `PreCompact` hook exists in Claude Code's hook system.** It fires before every compaction event (manual or auto-fired near 95% context). The original design described "main thread polls history.jsonl for gate_pass" — that approach is reactive and fragile compared to the deterministic hook.
3. **Auto-compact thresholds are configurable.** Either via settings.json or Agent SDK `compaction_control`.

The original design produced durable artefacts (cold + hot) but left conversation-context relief as a separate, vaguely-scoped Phase 9 concern. This revision makes that concrete:

- **The artefacts work** (Phase 7 shipped them) — `plans/phase-completes/` and `plans/PLANS-INDEX.md` Phase Completions are the durable record.
- **The session still carries everything** — even after writing artefacts, the active conversation still holds the verbose phase content as tokens.
- **The closing move** — a tapered `/compact` prompt that summarises older content into pointers, preserving the recent and current.

Compaction is **purely about conversation context**, not about file persistence. Claude can always re-read any cold artefact on demand. The compaction strategy controls what's *immediately in the message context*, not what's *available to read*.

---

## Solution shape

### Three components

| Component | Phase | Purpose |
|-----------|-------|---------|
| `/compact` prompt generator | 8 | Step 12 of `/phase-compact` outputs a tailored, tapered `/compact <prompt>` block the user can copy-paste |
| PreCompact hook | 9 | Fires at every compaction event; self-heals missing artefacts; writes session backup; emits the tapered prompt to stdout |
| `/load-phase-context` retrieval | 10 | Reverses the taper for one phase on demand — reads the cold artefact back into context |

### Two architectural decisions

1. **The PreCompact hook is the integration point**, not history.jsonl polling. The hook is deterministic, declarative (settings.json), and fires at the exact moment compaction is about to happen. Polling was the wrong model.
2. **Tapered compaction over flat compaction.** The `/compact` prompt is distance-weighted: recent stays full, just-completed is summarised, distant becomes pointer, never-drop preserves session metadata.

---

## Tapered Compaction Strategy

The single most important content rule. Generated *deterministically* from the current phase number — no model judgement at prompt-generation time.

| Distance | Tier | Treatment |
|----------|------|-----------|
| Current phase + next phase | **Preserve in full** | Active work needs full context: current task focus, plan being followed, recent decisions |
| Just-completed phase (N-1) | **Compress to summary** | One line per loop outcome, point at `plans/phase-completes/phase-{N-1}-complete.md` for detail |
| Distant phases (≤ N-2) | **Compress to pointer only** | Reference `plans/PLANS-INDEX.md` Phase Completions; drop verbose traces |
| Session metadata, skills, open tasks | **Never drop** | Continuity glue: user identity, active skills, open task list, unresolved bugs |

### Generated /compact prompt template

```
/compact

PRESERVE IN FULL (current and recent):
- Phase {N+1} plan and current task focus
- User's latest design decisions and stated preferences
- Open task list (snapshot from TaskList)
- Last 2-3 user messages and their direct context
- Skills currently in active use: {comma-separated list}

COMPRESS TO SUMMARY (just-completed Phase {N}):
- Phase {N} loop outcomes — see plans/phase-completes/phase-{N}-complete.md
- Gate review verdict: {pass|fail} ({agents})
- Key decisions made during Phase {N} (preserve decisions, drop deliberation)

COMPRESS TO POINTER ONLY (Phase {N-1} and earlier):
- See plans/PLANS-INDEX.md Phase Completions for the hot manifest summary
- Individual phase detail: plans/phase-completes/phase-{1..N-1}-complete.md
- Drop verbose loop traces, agent spawns, intermediate file edits

NEVER DROP (durable session metadata):
- User identity and role context
- Active skills loaded in this session
- Open tasks, unresolved bugs, known infrastructure issues
- Recent design decisions made by the user
```

### Recovery rule

If Claude later needs distant-phase detail, it reads `plans/phase-completes/phase-N-complete.md` directly. Phase 10's `/load-phase-context N` automates this lookup. **The taper is reversible per phase on demand.** Nothing is ever lost — only deferred from active context.

---

## Architecture

```
   USER ACTION OR AUTO-FIRE
   /compact <prompt>     or     Auto-compact near 95%
                │
                ▼
   PreCompact HOOK (Phase 9)
   settings.json declares hook → shell trampoline → Python
                │
                ▼
   platforms/python/pre_compact_hook.py:
     1. Read stdin (transcript metadata from Claude Code)
     2. Detect current phase from CLAUDE.md / PLANS-INDEX.md
     3. Gap detection: any completed phase lacking cold artefact?
     4. IF gap: invoke phase-compactor agent synchronously to fix
     5. Write session backup to .claude/state/compaction-backups/{ts}.json
     6. Generate tapered /compact prompt; print to stdout
     7. Append pre_compact event to .claude/state/history.jsonl
     8. Exit 0
                │
                ▼
   COMPACT PROCEEDS
   Session summarised per the tapered prompt
   Cold artefacts on disk remain authoritative for older detail
```

### Durability tiers

After compaction completes, three tiers of durable state survive:

| Tier | Location | Lifespan |
|------|----------|----------|
| Cold artefacts | `plans/phase-completes/phase-N-complete.md` | Forever (git-versioned) |
| Hot manifest | `plans/PLANS-INDEX.md` Phase Completions | Forever, accumulating, ≤8 lines per phase |
| Session backups | `.claude/state/compaction-backups/{ts}.json` | Per-compact-event audit trail |
| Audit log | `.claude/state/history.jsonl` | All events, append-only |

---

## Components per phase

### Phase 8 — Compactor Agent Promotion + Small Enhancements

| Loop | Deliverable |
|------|-------------|
| 027 | `phase-compactor` agent definition at `platforms/claude-code/agents/phase-compactor.md` |
| 028 | `/phase-compact` Step 12 outputs tailored, tapered `/compact <prompt>` block per the template above |
| 029 | Schema enum mismatch fix in Step 8 + Write-permission propagation bug investigation/fix |
| 030 | Phase 8 closeout — agent dogfooded against Phase 7, CLAUDE.md and PLANS-INDEX.md updated |

### Phase 9 — PreCompact Hook + Self-Healing

| Loop | Deliverable |
|------|-------------|
| 031 | `platforms/python/pre_compact_hook.py` — gap detector, backup writer, prompt emitter |
| 032 | `platforms/claude-code/hooks/pre-compact.sh` + `pre-compact.ps1` — shell trampolines |
| 033 | `platforms/claude-code/settings.json` declares PreCompact hook with `manual` and `auto` matchers |
| 034 | Self-healing logic: hook invokes `phase-compactor` agent synchronously on gap detection |
| 035 | Backup writer schema + writer for `.claude/state/compaction-backups/{ts}.json` |
| 036 | Tests + Phase 9 closeout — dogfooded via real compact event |

### Phase 10 — `/load-phase-context` Retrieval

Unchanged from original design. Three loops scoped previously.

---

## Data flow at compact time

```
Claude Code about to compact
       │
       │  Invokes pre-compact.sh via settings.json hook
       ▼
pre-compact.sh / .ps1 trampoline
       │  Locates Python; pipes stdin through
       ▼
platforms/python/pre_compact_hook.py
       │
       ├── (1) Read stdin
       │     Claude Code provides: { "trigger": "manual"|"auto",
       │                             "matcher": "...",
       │                             "transcript_path": "..." }
       │
       ├── (2) Detect current phase
       │     Read CLAUDE.md / plans/PLANS-INDEX.md to find:
       │       - current_phase (pending)
       │       - just_completed_phase (most recent complete)
       │       - distant_phases (all earlier complete)
       │
       ├── (3) Gap detection
       │     For each completed phase N: does plans/phase-completes/phase-N-complete.md exist?
       │     If any phase is gate-passed but lacks artefact → GAP DETECTED
       │
       ├── (4a) IF gap: Self-heal
       │     Invoke phase-compactor agent synchronously for each missing phase
       │     Synchronous: hook does not return until artefacts exist
       │     Errors logged to compaction-warnings.log; exit 0 regardless
       │
       ├── (4b) IF no gap: proceed
       │
       ├── (5) Write session backup
       │     .claude/state/compaction-backups/{ISO-timestamp}.json
       │     Contains: current_phase, last_user_intent, open_tasks,
       │               recent_artefacts, trigger_reason
       │
       ├── (6) Generate tapered /compact prompt to stdout
       │     Per the template in "Tapered Compaction Strategy" above
       │     Substituted with current phase number, recent decisions hint, etc.
       │     Claude Code displays stdout to user before compact runs
       │
       ├── (7) Append audit event
       │     .claude/state/history.jsonl gets pre_compact event with:
       │       trigger, gap_detected, auto_heal_ran, backup_path, timestamp
       │
       └── (8) Exit 0
       │
       ▼
Compact proceeds, session summarised
```

### Properties

- **Hook always exits 0.** Compact must not be blocked.
- **Self-heal is synchronous.** ~30s if /phase-compact invocation needed. User sees the hook output, knows the wait is expected.
- **Backups are write-only.** Phase 10's retrieval reads them. The hook never reads its own backups.
- **stdin is the contract.** Whatever Claude Code provides is what the hook works with. Documented dependency on Claude Code's hook protocol.

---

## Error handling

**Iron rule:** the hook NEVER exits non-zero. Returning non-zero could abort compact and leave the session worse than no hook at all.

| Failure | Behaviour |
|---------|-----------|
| Python not on PATH | Trampoline writes `python-not-found` warning; exits 0. Compact proceeds without backup. |
| `pre_compact_hook.py` uncaught exception | Top-level try/except logs full traceback to compaction-warnings.log; exits 0. |
| Stdin malformed | Falls back to filesystem-only gap detection; logs `stdin-malformed`; exits 0. |
| `/phase-compact` fails during self-heal | Logs `auto-heal-failed: phase-N: <reason>`; backup still written; exits 0. User can re-run /phase-compact manually. |
| Backup write fails (disk full, perms) | Logs `backup-write-failed`; exits 0. |

**Warnings log:** `.claude/state/compaction-warnings.log` — plain text, ISO-timestamped one-liners. User can `tail` it.

---

## Testing

### Layer 1 — Unit tests
`platforms/python/tests/test_pre_compact_hook.py`. One test per code branch:
- gap_detection_no_phases_complete
- gap_detection_all_phases_compacted
- gap_detection_missing_artefact
- self_heal_invokes_phase_compact
- self_heal_failure_logs_warning
- backup_written_on_success
- backup_write_failure_logged
- stdin_malformed_falls_back
- python_top_level_exception_caught
- audit_event_appended
- tapered_prompt_generated_correctly (verify all four tiers substituted)

### Layer 2 — Integration test
`platforms/python/tests/test_pre_compact_integration.py`. Synthetic repo state in `tempfile.TemporaryDirectory`. Set up a gate-passed phase without artefact, invoke hook with simulated stdin, verify outputs.

### Layer 3 — Manual smoke test
At Phase 9 closeout: trigger `/compact` in a real session at a phase boundary. Verify hook output (stdout, log, backup), session summarises correctly, observe context-token reduction qualitatively.

### CI implications
- Tests run in existing pytest job
- Hook code passes zero-external-imports AST checker (uses `subprocess` for invoking agent — stdlib)
- Install script manifest updated to copy hook scripts to target projects

---

## Success criteria

After Phases 8 + 9 + 10:

- ✓ `/phase-compact` outputs a tapered `/compact <prompt>` users can copy-paste
- ✓ PreCompact hook fires automatically on every compaction event
- ✓ Hook self-heals: missing cold artefacts are created before compact proceeds
- ✓ Hook writes a session backup for every compact event
- ✓ Tapered prompt is deterministic from current phase number — same inputs → same prompt
- ✓ Distant phases compress to pointer; recent stays full; nothing is silently lost
- ✓ `/load-phase-context N` brings any phase back to full detail on demand
- ✓ Hook always exits 0; compact is never blocked by hook failures
- ✓ A long-running programme (10+ phases) maintains roughly constant context-per-session
- ✓ Recovery from any compact event is possible via backup + cold artefacts + git

---

## Open questions for /plan-eng-review

These are the questions the engineering review should press on:

1. **Subprocess invocation from Python to agent.** When the hook self-heals, `pre_compact_hook.py` needs to invoke the `phase-compactor` agent. How does Python invoke an agent? Agents are spawned by the Claude Code harness, not by shell commands. Possible answers: (a) the hook invokes `/phase-compact` as a slash command via some Claude Code CLI — but it's not clear that's possible from inside a hook script; (b) the hook directly executes the *logic* of /phase-compact (read plan, write artefact) without going through the agent layer — duplicating logic; (c) the hook only flags the gap and lets the conversation handle it on next user turn. **This is the biggest implementation unknown.**
2. **stdin contract stability.** Claude Code's PreCompact hook stdin contract isn't a fully stable API. What happens if a future Claude Code version changes the contract? Mitigation: defensive parsing + best-effort fallback (already in design) + integration test that documents the assumed contract.
3. **Retry / multi-version phases.** A phase with `phase-N-complete-v1-failed.md` AND `phase-N-complete.md` — which does the hook treat as canonical? Likely the pass-form version, but needs explicit rule.
4. **Backup retention.** `.claude/state/compaction-backups/` grows unboundedly. Need a retention policy: keep last N? Last 30 days? Clean up at gate review time?
5. **Race conditions on PLANS-INDEX.md.** If the hook is running self-heal at the same time the user is running /phase-compact manually, two processes could write the manifest. Mitigation: simple file lock or just document it (single-user single-session usage).
6. **What "session metadata" actually means.** "Never drop" tier needs concrete enumeration. Skills, open tasks, user identity — but what else? Recent tool failures? Recent file edits? Active model name?
7. **Prompt token budget.** The tapered prompt itself consumes tokens during compact. ~10-15 lines is the target. Stress-test: does it stay under ~200 tokens?
8. **Idempotency of the hook.** Running compact twice rapidly — second invocation finds artefacts present, skips self-heal, still writes backup. Confirm this is the right behaviour vs deduplicating backups.

---

## References

- Original design: `~/.gstack/projects/MungoHarvey-advanced-planning/mharvey2-main-design-20260513-103520.md`
- Locked schemas: `docs/phase-complete.schema.md`, `docs/phase-manifest-entry.schema.md`
- Existing slash command: `platforms/claude-code/commands/phase-compact.md`
- Existing agents (pattern reference): `platforms/claude-code/agents/phase-goals-agent.md`
- Claude Code hooks reference: <https://code.claude.com/docs/en/hooks>
- PreCompact feature request (prompt injection): <https://github.com/anthropics/claude-code/issues/43733>

---

## Status / Next Steps

**Status:** DRAFT
**Next:** /plan-eng-review on this spec, then user approval, then phase-plan-creator for Phase 8 and Phase 9 plans.
