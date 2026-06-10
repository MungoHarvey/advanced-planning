# Phase 16 Design: Trust the Machinery

**Date:** 2026-06-10
**Status:** Approved (brainstorming session, 2026-06-10)
**Source evidence:** `.context/retros/2026-06-09-1.json`, `docs/tool-friction-log.md`, Phase 14/15 session findings
**Target release:** v0.16.0
**Predecessor:** Phase 15 (Automation-Surface Audit) — closed, gate passed attempt 1

---

## 1. Problem

The 2026-06-09 retro (phases 12–15 window: 64 commits, 4 gate passes, 3 releases staged)
surfaced six gaps that degrade automation and agentic workflows. Two are silent-degradation
defects, two are agent-economy waste, two are record/hygiene debt:

| # | Gap | Evidence |
|---|-----|----------|
| 1 | **Command-layer drift.** Three install layers exist (source `platforms/claude-code/commands/`, project `.claude/commands/`, global `~/.claude/commands/`). The global layer is what executes in interactive sessions and it is two phases stale: 0 codex refs, 0 closeout refs, 0 archive/`--full` refs. Everything phases 12–15 built into the command bodies does not run. | grep counts on `C:/Users/mharvey2/.claude/commands/{run-gate,next-loop}.md` |
| 2 | **history.jsonl under-population.** 23 events across 15 phases / 63 loops; `loop_complete` exists for only 10/63 loops (phases 10–11). `/progress-report`, `/run-closeout`, `/phase-compact` Step 6 all read this log. | event counts, 2026-06-09 |
| 3 | **Patchy compaction coverage.** `complete.md` 6/15 phases; `handoff.md` 4/15; `phase-7/` directory empty. | artefact coverage matrix, 2026-06-09 |
| 4 | **Worker contract leaks.** Workers self-committed twice (loops 056, 061) and twice created mangled junk files via bash redirects to Windows absolute paths. Guards were hand-injected per spawn prompt instead of living in the agent definition. | friction log 2026-06-09 entries |
| 5 | **Orchestrator overhead.** For fully-populated loops the orchestrator spawn (~26–32k tokens, 30–45s) only copies the prior handoff into `loop-ready.json`. ~150k tokens per 5-loop phase of pure ceremony. | subagent token usage, phase 15 |
| 6 | **Checkpoint/git noise.** 17/64 commits are `checkpoint:` commits; `execution.log` churned 39× into git history. | commit-type breakdown, hotspots |

## 2. Decisions (locked in brainstorming)

1. **Scope: all six gaps** in one phase.
2. **Gap 1 strategy: refresh + drift-detection.** The global layer stays (other projects
   consume it) and becomes the **upgrade pathway**: improvements flow source → global so
   every consuming project receives them. Removal of the global layer is rejected.
3. **Gap 5 strategy: conditional fast-path.** Python writes `loop-ready.json` for fully
   populated loops; the orchestrator agent is reserved for stubs/ambiguity. The two-agent
   pattern remains the documented architecture; the fast-path is an optimisation.
4. **Gap 6 strategy: lightweight tags + ignore log.** Checkpoint commits become
   `checkpoint/loop-NNN` tags; `execution.log` is gitignored and rotated. No history
   rewriting.
5. **Gap 3 strategy: backfill all + auto-compact at close.** All 9 missing phases get
   `complete.md` + manifest entries; `/run-gate`'s closeout runs the compaction artefact
   steps automatically. The context `/compact` consent gate is unchanged.
6. **Gap 2: no event backfill.** history.jsonl is append-only evidence; fabricating past
   timestamps would corrupt it. The backfilled compaction artefacts carry the historical
   record instead.
7. **Structure: dependency-ordered, 5 loops** (064–068). Fix the machinery first; the
   phase dogfoods its own fixes from loop 3 onward.

## 3. Loop breakdown

### Loop 064 — Install-Sync + Drift Guard (gap 1)

Deliverables:
- `platforms/python/install_audit.py` — stdlib-only (pathlib/re/sys/argparse/hashlib,
  all in the `core/constraints.json` allow-set). Compares the three layers by content
  hash, EOL-insensitive. Resolves the global dir via `USERPROFILE` fallback on Windows
  (same lesson as the Phase 14 codex-auth fix; git-bash `~` may map elsewhere).
  Per-file report: `current / stale / missing`. Exit non-zero on drift.
- `platforms/claude-code/commands/sync-install.md` (+ runtime copies) — runs the audit,
  then refreshes stale copies **source → outward** (plain `cp`, byte-faithful — the
  established install method; never backwards). `--check` = audit only. Also syncs
  `agents/` and `schemas/` surfaces, not just `commands/`.
- CI step (job 4 or a new step): `install_audit.py --layers source,project` (CI cannot
  see a developer's global dir; source↔project is the pair that drifted in Phase 14).
- `/run-gate` Step 1 preflight: one-line warning when the project copy is stale.
- **First action of the loop: run the sync for real**, so the remainder of Phase 16
  executes on current commands (codex participates in the Phase 16 gate).
- Tests: `test_install_audit.py` — current/stale/missing detection, EOL-insensitivity,
  USERPROFILE resolution (via env monkeypatch + tmp dirs).

### Loop 065 — Trustworthy Record (gaps 2 + 4)

Deliverables:
- `platforms/python/history_log.py` — single `append_event(path, event_dict)` helper:
  compact-JSON (no spaces), append-only, timestamps in ISO-8601 UTC. Commands stop
  hand-rolling `echo` lines (inconsistent spacing already broke a grep in Phase 14).
- `/next-loop` Step 9 appends `loop_complete` (loop name, phase, todos done/failed,
  commit SHA). Planning paths append `phase_planned`. Release step appends
  `release_staged`. Source + runtime copies.
- Worker contract guards moved INTO the agent definitions —
  `platforms/claude-code/agents/ralph-loop-worker.md`, `ralph-orchestrator.md`, and the
  abstract role in `core/agents/`: (a) never commit, the main thread owns git;
  (b) create/edit files via Write/Edit tools only, never shell redirects; (c) never
  redirect to absolute Windows paths. (Project `.claude/agents/` copies refreshed via
  the new `/sync-install`.)
- Friction-log strikethroughs for the two worker-tooling entries.
- Tests: `test_history_log.py` — append-only, compact format, greppability
  (`'"phase":"phase-N"'` matches).

### Loop 066 — Loop-Flow Economy (gaps 5 + 6)

Deliverables:
- `prepare_loop_ready()` in `platforms/python/state_manager.py` (or a thin
  `loop_prep.py`): given the loop file and prior handoff, writes a valid
  `loop-ready.json`. **Conservative populated-predicate:** every todo has
  id/content/outcome/status and the todos array is non-empty; anything ambiguous →
  agent path.
- `/next-loop` Step 4 becomes conditional: populated → Python fast-path, prints
  `-> fast-path: loop already populated, orchestrator skipped`; stub/ambiguous/`--full`
  → spawn `ralph-orchestrator` as today.
- Checkpoint commits replaced by lightweight tags `checkpoint/loop-NNN` (rollback:
  `git reset --hard checkpoint/loop-NNN`). Old checkpoint commits untouched (no
  history rewriting).
- `execution.log` gitignored + `git rm --cached`; rotation note in the README.
- CLAUDE.md decision-log entry: fast-path is an optimisation, the two-agent pattern
  remains the architecture.
- Tests: fast-path writes schema-valid loop-ready.json; stub loop correctly signals
  agent-needed; predicate rejects partially-populated todos.

### Loop 067 — Compaction Backfill ×9 (gap 3)

Deliverables:
- `complete.md` for phases 1, 2, 3, 4, 7, 8, 10, 11, 12 via `/phase-compact`'s own
  steps per phase: anchor/end SHAs from git + history.jsonl; body sections from loop
  handoff summaries and (phases 10–12) gate verdicts; phases predating gate review use
  the documented sentinel form (`gate_verdict_ref: "n/a — pre-gate-review phase"` +
  `gate_verdict_note`). Phase 7 reconstructed from git history (its commits exist).
- ≤8-line PLANS-INDEX manifest entry per backfilled phase, ascending order.
- **handoff.md is NOT backfilled** — it is a context-resume seed; meaningless for
  phases nobody will resume. Purpose over symmetry.
- Every Goals-met bullet carries a commit-SHA or file-path evidence pointer.
- Writes only under `.advanced-plans/`. LOCKED schemas obeyed byte-for-byte.

### Loop 068 — Auto-Compact at Close + Release (gap 3 second half)

Deliverables:
- `/run-gate` Step 10.4 sub-step: after the closeout commit, run `/phase-compact`'s
  **artefact steps** (cold artefact, manifest entry, handoff digest) inline —
  idempotent, main-thread. The context `/compact` consent gate is unchanged: artefacts
  automatic, conversation compaction always user-consented.
- Verification sweep: full suite green (~380+ target), AST NONE, `path_audit` CLEAN,
  `install_audit` current, LOCKED docs byte-unchanged.
- v0.16.0: VERSION + CHANGELOG `[0.16.0]` + CLAUDE.md Phase 16 decision-log entry.
- Friction-log strikethroughs for all entries this phase resolves.
- Phase-close output prints the push reminder: `git push origin main --follow-tags`
  (automation cannot push — operator SSH key — but it can refuse to be forgotten).

## 4. Success criteria

1. `install_audit.py` reports all three layers **current** on this machine after
   `/sync-install`; CI runs the source↔project check and blocks on drift.
2. A planted stale project copy makes `install_audit` exit non-zero (negative test);
   EOL-only differences do NOT trip it (false-positive guard).
3. A live `/next-loop` run during this phase appends a `loop_complete` event to
   history.jsonl (greppable compact JSON).
4. `ralph-loop-worker.md` and `ralph-orchestrator.md` (source + installed copies)
   contain the three contract guards; no per-spawn hand-injection needed.
5. The fast-path demonstrably skips the orchestrator on a populated loop (printed
   marker + no Agent spawn), and a stub loop still routes to the agent.
6. Phase 16's own history contains **zero** `checkpoint:` commits; checkpoint tags
   exist instead; `execution.log` is untracked.
7. All 15 prior phases have `complete.md` + a PLANS-INDEX manifest entry; pre-gate
   phases use the sentinel form; every bullet has an evidence pointer.
8. A gate-pass closeout (this phase's own gate, or a witnessed simulation) produces
   compaction artefacts without a separate `/phase-compact` invocation.
9. Full suite green across 3.10–3.12; AST zero-dep NONE; `path_audit` CLEAN; LOCKED
   schema docs byte-unchanged; `core/` contains no platform-specific paths.
10. v0.16.0 cut (VERSION, CHANGELOG, decision log); resolved friction-log entries
    struck through with Loop 064–068 resolution notes.

## 5. Explicitly NOT included

- **Removing the user-global command layer** — other projects consume it; it stays and
  is kept current instead (Decision 2).
- **Backfilling history.jsonl events** — append-only evidence; not fabricated
  (Decision 6).
- **Backfilling handoff.md** — resume seeds for unreachable past phases are noise.
- **Retiring the orchestrator** — fast-path only; the agent remains for stubs and
  ambiguity (Decision 3).
- **Git history rewriting** — old checkpoint commits and execution.log history stay.
- **Push/release publication automation** — pushing requires the operator's SSH key;
  the framework prints the reminder, the operator pushes.
- **Changes to LOCKED schema docs** or `gate-verdict.schema.json`.
- **Logic changes to `codex_gate.py` / `remediate.py` / `remediation_controller.py`.**

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `/sync-install` writes to the machine-global dir, affecting every project | Med | High | `--check` is the CI/default-audit mode; the write path runs only on explicit invocation; Loop 064's live sync runs on the main thread under operator supervision, not inside a worker |
| Fast-path predicate misjudges "populated" and skips needed planning | Low | Med | Conservative predicate; ambiguity always routes to the agent; both branches tested |
| Backfilled artefacts misrepresent history | Low | High | Sentinel form for pre-gate phases; SHA-anchored evidence per bullet; the gate reviews the backfill like any deliverable |
| Mid-phase edits to `next-loop.md`/`run-gate.md` break the machinery running the phase (dogfooding hazard) | Med | High | Phase-15 pattern: command edits land + verify in loops 064–066 before loops 067–068 depend on them; byte-identity checks after every command edit |
| Checkpoint tags accumulate unboundedly | Low | Low | Tags namespaced `checkpoint/`; cleanup note documented; deletable in bulk |

## 7. Skills required (broad categories)

- `command-rewriting` / file-sync — command-body edits + three-layer refresh discipline
- `verification-before-completion` — negative tests, live demonstrations, release sweep
- `schema-design` — only if an event-shape question arises in `history_log.py` (none
  expected; gate-verdict schema untouched)

## 8. Open questions

(none — all design forks were resolved in the brainstorming session; see §2)
