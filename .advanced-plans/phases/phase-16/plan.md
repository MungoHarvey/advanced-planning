---
phase: 16
name: "Trust the Machinery"
status: draft
loops: [064, 065, 066, 067, 068]
design_spec: .advanced-plans/specs/2026-06-10-phase-16-trust-the-machinery-design.md
anchor_sha: 5ffaa64
target_release: v0.16.0
---

# Phase 16: Trust the Machinery

## Objective

Make the framework's own execution surfaces trustworthy and cheap — the commands that run are
the commands we ship, the audit log records what actually happened, the agents obey their
contracts structurally, and the loop flow stops paying for ceremony — then complete the
programme's documentary record.

## Scope

### Included
- **Install-sync + drift guard** (gap 1): `platforms/python/install_audit.py` (stdlib-only,
  EOL-insensitive content-hash comparison of source / project `.claude/` / global
  `~/.claude/` layers with `USERPROFILE` resolution on Windows); a `/sync-install` command
  that refreshes stale copies source → outward (plain `cp`; also covers `agents/` and
  `schemas/`, never syncs backwards; `--check` = audit only); a CI source↔project drift
  step; a `/run-gate` Step 1 staleness preflight warning. The global layer is the upgrade
  pathway — other projects receive phases 12–16's command improvements on sync.
- **Trustworthy record** (gaps 2+4): `platforms/python/history_log.py` append helper
  (compact JSON, ISO-8601 UTC); `loop_complete` / `phase_planned` / `release_staged`
  events wired into `/next-loop` and the planning/release paths; the three worker-contract
  guards (never commit; Write/Edit tools only, no shell redirects; no absolute-Windows-path
  redirects) moved into `ralph-loop-worker.md` + `ralph-orchestrator.md` + the `core/agents/`
  abstract role.
- **Loop-flow economy** (gaps 5+6): `prepare_loop_ready()` fast-path — `/next-loop` skips the
  orchestrator spawn when the next loop is fully populated (conservative predicate; stubs and
  `--full` still route to the agent); checkpoint commits replaced by `checkpoint/loop-NNN`
  lightweight tags; `execution.log` gitignored + `git rm --cached` + rotation note.
- **Compaction backfill ×9** (gap 3): `complete.md` + ≤8-line manifest entries for phases
  1–4, 7, 8, 10–12, using `/phase-compact`'s own steps; pre-gate-review phases use the
  documented sentinel verdict form; phase 7 reconstructed from git history; every bullet
  SHA- or path-anchored. handoff.md is NOT backfilled (resume seeds for unreachable phases
  are noise).
- **Auto-compact at close** (gap 3, second half): `/run-gate` Step 10.4 runs `/phase-compact`'s
  artefact steps (cold artefact, manifest, handoff digest) inline after the closeout commit;
  the context `/compact` consent gate is unchanged.
- v0.16.0: VERSION + CHANGELOG + CLAUDE.md decision-log entry; friction-log strikethroughs
  for every entry this phase resolves; phase-close output prints the push reminder.

### Explicitly NOT included
- **Removing the user-global command layer** — other projects consume it; it stays current
  instead (spec Decision 2).
- **Backfilling history.jsonl events** — append-only evidence is not fabricated; the
  backfilled compaction artefacts carry the historical record (spec Decision 6).
- **Backfilling handoff.md** for past phases.
- **Retiring the orchestrator** — fast-path only; the agent remains for stubs/ambiguity.
- **Git history rewriting** — existing checkpoint commits and execution.log history stay.
- **Push/release publication automation** — pushing needs the operator's SSH key; the
  framework prints the reminder.
- **Changes to LOCKED schema docs or `core/state/gate-verdict.schema.json`.**
- **Logic changes to `codex_gate.py` / `remediate.py` / `remediation_controller.py`.**

## Key Deliverables

| Deliverable | Format | Location |
|-------------|--------|----------|
| Install-layer drift auditor | Python (stdlib) + tests | `platforms/python/install_audit.py`, `tests/test_install_audit.py` |
| /sync-install command | Markdown command (+ runtime copies) | `platforms/claude-code/commands/sync-install.md` |
| CI drift step | Workflow edit | `.github/workflows/ci.yml` |
| History event helper | Python (stdlib) + tests | `platforms/python/history_log.py`, `tests/test_history_log.py` |
| Event wiring | Command edits | `platforms/claude-code/commands/next-loop.md` (+ planning/release paths) |
| Worker-contract guards | Agent definition edits | `platforms/claude-code/agents/{ralph-loop-worker,ralph-orchestrator}.md`, `core/agents/` |
| Orchestrator fast-path | Python + command edit + tests | `platforms/python/state_manager.py` (`prepare_loop_ready`), `next-loop.md` Step 4 |
| Checkpoint tags + log ignore | Command edit + .gitignore | `next-loop.md` Step 3, `.gitignore` |
| Compaction backfill ×9 | Markdown artefacts | `.advanced-plans/phases/phase-{1-4,7,8,10-12}/complete.md` + PLANS-INDEX entries |
| Auto-compact at close | Command edit | `platforms/claude-code/commands/run-gate.md` Step 10.4 |
| v0.16.0 release | VERSION + CHANGELOG + decision log | `VERSION`, `CHANGELOG.md`, `CLAUDE.md` |

## Success Criteria

- ✓ `install_audit.py` reports all three layers current on this machine after `/sync-install`;
  CI runs the source↔project check and blocks on drift.
- ✓ A planted stale project copy makes `install_audit` exit non-zero; EOL-only differences do
  NOT trip it (false-positive guard).
- ✓ A live `/next-loop` run during this phase appends a `loop_complete` event to
  history.jsonl in greppable compact JSON.
- ✓ `ralph-loop-worker.md` and `ralph-orchestrator.md` (source + installed copies) contain
  the three contract guards; no per-spawn hand-injection needed.
- ✓ The fast-path demonstrably skips the orchestrator on a populated loop (printed marker +
  no Agent spawn), and a stub loop still routes to the agent.
- ✓ Phase 16's own history contains zero `checkpoint:` commits; `checkpoint/loop-NNN` tags
  exist instead; `execution.log` is untracked.
- ✓ All 15 prior phases have `complete.md` + a PLANS-INDEX manifest entry; pre-gate phases
  use the sentinel form; every bullet has an evidence pointer.
- ✓ A gate-pass closeout produces compaction artefacts without a separate `/phase-compact`
  invocation (this phase's own gate, or a witnessed simulation).
- ✓ Full suite green (pytest 3.10–3.12), AST zero-dep NONE, `path_audit` CLEAN, LOCKED
  schema docs byte-unchanged, no platform paths in `core/`.
- ✓ v0.16.0 cut; every friction-log entry resolved this phase struck through with a
  Loop 064–068 resolution note.

## Dependencies

### Must Complete Before
- Phase 15 closed (done): `/sync-plans`, `path_audit`, `--full`, and the gate→close
  progression all exist and are the baseline this phase builds on.

### Blocked By
- (none external)

### Optional
- Operator push (`git push origin main --follow-tags`) — orthogonal; the phase reminds
  but does not require it.

## Skills Required (Broad Categories)
- `command-rewriting` / file-sync: command-body edits + three-layer refresh discipline.
- `verification-before-completion`: negative tests, live demonstrations, release sweep.
- `schema-design`: only if an event-shape question arises in `history_log.py` (none
  expected; gate-verdict schema untouched).

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| `/sync-install` writes to the machine-global dir, affecting every project | Med | High | `--check` is the audit/CI mode; writes only on explicit invocation; Loop 064's live sync runs on the main thread under operator supervision, never inside a worker |
| Fast-path predicate misjudges "populated" and skips needed planning | Low | Med | Conservative predicate (every todo has id/content/outcome/status, non-empty array); ambiguity always routes to the agent; both branches tested |
| Backfilled artefacts misrepresent history | Low | High | Sentinel form for pre-gate phases; SHA-anchored evidence per bullet; the gate reviews the backfill like any deliverable |
| Mid-phase edits to next-loop.md/run-gate.md break the machinery running this phase | Med | High | Phase-15 pattern: command edits land + verify in loops 064–066 before loops 067–068 depend on them; byte-identity checks after every command edit |
| Checkpoint tags accumulate unboundedly | Low | Low | Namespaced `checkpoint/`; bulk-deletable; cleanup note documented |

## Assumptions
- `hashlib`, `argparse`, `pathlib`, `re`, `sys`, `json`, `datetime` cover everything
  `install_audit.py` and `history_log.py` need — all already in the `core/constraints.json`
  allow-set; validated by the AST check.
- The global commands dir on this machine is `C:\Users\mharvey2\.claude\commands\`
  (`USERPROFILE`), while git-bash `~` may resolve elsewhere — `install_audit` must resolve
  via `USERPROFILE` first (validated during the retro: `~` pointed at a mapped drive).
- Phase 7's git commits exist and are sufficient to reconstruct its `complete.md`
  (validated: its work is in history even though the phase dir is empty).

## Notes / Design Decisions

All design forks were resolved in the 2026-06-10 brainstorming session and are recorded in
the spec's §2 Decisions (authoritative): all-six scope; refresh-not-remove for the global
layer (upgrade pathway); conditional orchestrator fast-path (two-agent pattern remains the
architecture); checkpoint tags + log ignore (no history rewriting); backfill-all +
auto-compact-at-close; no history.jsonl event fabrication. Loop ordering is
dependency-driven: the sync lands first so the rest of the phase executes on current
commands (codex participates in this phase's gate), and command edits land before the loops
that depend on them.

## Ralph Loops (5)

| Loop | Name | Type | Key Outputs |
|------|------|------|-------------|
| 064 | Install-Sync + Drift Guard | Implementation | `install_audit.py` + tests, `/sync-install`, CI step, live sync, gate preflight |
| 065 | Trustworthy Record | Implementation | `history_log.py` + tests, event wiring, worker-contract guards in agent defs |
| 066 | Loop-Flow Economy | Implementation | `prepare_loop_ready()` fast-path + tests, checkpoint tags, log ignore |
| 067 | Compaction Backfill ×9 | Implementation | `complete.md` + manifest entries for phases 1–4, 7, 8, 10–12 |
| 068 | Auto-Compact at Close + Release | Implementation | run-gate Step 10.4 artefact wiring, verification sweep, v0.16.0 |
