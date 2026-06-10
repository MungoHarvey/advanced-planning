# Phase 16 — Ralph Loops

Decomposition of `.advanced-plans/phases/phase-16/plan.md` (Trust the Machinery) into 5
executable loops. Design spec (authoritative):
`.advanced-plans/specs/2026-06-10-phase-16-trust-the-machinery-design.md`.

---

```yaml
---
name: "ralph-loop-064"
task_name: "Install-Sync + Drift Guard"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "install_audit.py (EOL-insensitive, USERPROFILE-first) + 18 tests (384 green, AST NONE); /sync-install command; CI drift step; run-gate Step 1 preflight; LIVE SYNC DONE main-thread: project (2 stale fixed) + global (14 commands/8 agents/5 schemas) refreshed -- install_audit reports all layers current; global run-gate now codex+closeout wired."
  failed: ""
  needed: "Begin loop-065: history_log.py + event wiring + worker-contract guards in agent definitions."

todos:
  - id: "loop-064-1"
    content: "Write platforms/python/install_audit.py (stdlib only: pathlib/re/sys/argparse/hashlib): compare source (platforms/claude-code/{commands,agents}/ + core/schemas/) vs project (.claude/) vs global (~/.claude/, resolved USERPROFILE-first on Windows) by EOL-insensitive content hash; per-file report current/stale/missing; --layers flag to select layer pairs; exit non-zero on drift"
    skill: "NA"
    agent: "NA"
    outcome: "install_audit.py exists; exits 0 when layers match, non-zero with a per-file report on drift; EOL-only differences do not trip it; global dir resolved via USERPROFILE before HOME"
    status: completed
    complexity: high
    priority: high
  - id: "loop-064-2"
    content: "Write platforms/python/tests/test_install_audit.py: current/stale/missing detection, EOL-insensitivity (CRLF vs LF same content passes), USERPROFILE resolution (env monkeypatch + tmp dirs), --layers selection"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Tests cover all four behaviours; full suite green under pytest"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-064-3"
    content: "Write platforms/claude-code/commands/sync-install.md (+ byte-identical .claude/ copy): runs install_audit, then refreshes stale copies source->outward (plain cp; commands, agents, schemas surfaces); --check = audit only, no writes; never syncs backwards; add to CLAUDE.md Command Surface"
    skill: "NA"
    agent: "NA"
    outcome: "sync-install.md exists (source + content-identical runtime copy); documents source->outward direction and --check; CLAUDE.md Command Surface row added; path_audit stays CLEAN"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-064-4"
    content: "Add a CI drift step to .github/workflows/ci.yml running install_audit --layers source,project (CI cannot see a developer's global dir); add a one-line staleness preflight warning to run-gate.md Step 1 (source + runtime copy, byte-identical)"
    skill: "NA"
    agent: "NA"
    outcome: "ci.yml runs the source<->project drift check and blocks on drift; run-gate.md Step 1 warns when the project copy is stale"
    status: completed
    complexity: medium
    priority: medium
  - id: "loop-064-5"
    content: "MAIN-THREAD STEP (operator-supervised, NOT a worker task): run the live sync — refresh the stale global ~/.claude/commands+agents from source so all projects receive phases 12-16 improvements; then run install_audit and confirm all three layers report current"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "install_audit reports all three layers current on this machine; the stale global run-gate/next-loop now carry codex/closeout/--full/archive content"
    status: completed
    complexity: low
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Build the install-layer drift auditor and /sync-install upgrade pathway, wire the CI guard,
  and bring all three command layers current so the rest of Phase 16 runs on shipped commands.

  ## Git checkpoint (run first)
  git tag checkpoint/loop-064 2>/dev/null || true

  ## Success criteria
  - [ ] install_audit.py detects current/stale/missing, EOL-insensitive, USERPROFILE-first
  - [ ] Tests green (full suite); AST NONE
  - [ ] /sync-install command exists (source + runtime copy) with --check mode
  - [ ] CI source<->project drift step present; run-gate Step 1 preflight warning added
  - [ ] Live sync done (main thread): all three layers report current

  ## Required skills
  - verification-before-completion

  ## Inputs
  - platforms/python/path_audit.py (style template: CLI, report shape, exit codes)
  - docs/path-conventions.md; CONTRIBUTING.md runtime-drift note
  - .github/workflows/ci.yml

  ## Constraints
  - Zero-dependency Python (stdlib only; hashlib is in the allow-set)
  - WORKER CONTRACT: do not commit; Write/Edit tools only, no shell redirects, no absolute
    Windows paths in redirects
  - Todo 064-5 is executed by the MAIN THREAD under operator supervision — the worker must
    NOT write outside the repo; it stops after 064-4 and records 064-5 as main-thread-pending

  ## On completion
  1. Update handoff_summary (done/failed/needed)
  2. Mark completed todos; leave 064-5 for the main thread if not yet run
  3. Write .advanced-plans/state/loop-complete.json
```

---

```yaml
---
name: "ralph-loop-065"
task_name: "Trustworthy Record"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "history_log.py (append_event + CLI, compact/greppable, stdlib-only, AST NONE); 13 tests added (397 total green); loop_complete event wired into next-loop.md Step 9, phase_planned into plan-and-phase.md Step 8 and new-phase.md Step 12 (source + byte-identical runtime copies); Hard Contract guards (no commit / Write-Edit only / no Windows absolute paths) added to ralph-loop-worker.md, ralph-orchestrator.md, core/agents/worker.md, core/agents/orchestrator.md; both Phase 15 friction-log entries struck through."
  failed: ""
  needed: "Continue with loop-066: prepare_loop_ready fast-path + checkpoint tags + execution.log untracking."

todos:
  - id: "loop-065-1"
    content: "Write platforms/python/history_log.py: append_event(history_path, event_dict) — compact JSON separators, ISO-8601 UTC timestamp injected if absent, append-only, parent dir created; plus a tiny CLI (python -m platforms.python.history_log <path> '<json>') so command bodies can call it in one line"
    skill: "NA"
    agent: "NA"
    outcome: "history_log.py exists; events written compact (no spaces) and greppable ('\"phase\":\"phase-N\"' matches); append-only proven"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-065-2"
    content: "Write platforms/python/tests/test_history_log.py: compact format, timestamp injection, append-only (existing lines untouched), greppability, CLI invocation"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Tests cover the five behaviours; full suite green"
    status: completed
    complexity: low
    priority: high
  - id: "loop-065-3"
    content: "Wire events into command bodies (source + byte-identical runtime copies): next-loop.md Step 9 appends loop_complete (loop_name, phase, todos done/failed, commit sha); plan-and-phase/new-phase planning completion appends phase_planned; the release todo convention appends release_staged — all via the history_log CLI"
    skill: "NA"
    agent: "NA"
    outcome: "next-loop.md Step 9 emits loop_complete; planning paths emit phase_planned; runtime copies content-identical; path_audit CLEAN"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-065-4"
    content: "Move the worker-contract guards into agent definitions: ralph-loop-worker.md + ralph-orchestrator.md (platforms/claude-code/agents/) and the core/agents/ abstract role — (a) never commit, main thread owns git; (b) create/edit files via Write/Edit tools only, never shell redirects; (c) never redirect to absolute Windows paths; refresh installed .claude/agents/ copies"
    skill: "NA"
    agent: "NA"
    outcome: "All three guards present in both agent files (source + installed); core/agents/ role updated; no .claude/ paths added to core files"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-065-5"
    content: "Strike through the two worker-tooling friction-log entries (Windows-redirect junk files; worker self-commits) with a Loop 065 resolution note"
    skill: "NA"
    agent: "NA"
    outcome: "Both entries struck through per the log convention"
    status: completed
    complexity: low
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Make the audit log record what actually happens (history_log helper + event wiring) and make
  the worker contract structural (guards in agent definitions, not per-spawn prompts).

  ## Git checkpoint (run first)
  git tag checkpoint/loop-065 2>/dev/null || true

  ## Success criteria
  - [ ] history_log.py + tests green; compact greppable events
  - [ ] next-loop.md Step 9 emits loop_complete; planning paths emit phase_planned
  - [ ] Three contract guards in ralph-loop-worker.md + ralph-orchestrator.md + core role
  - [ ] Runtime copies content-identical; path_audit CLEAN; AST NONE
  - [ ] Friction-log entries struck through

  ## Required skills
  - verification-before-completion

  ## Inputs
  - .advanced-plans/state/history.jsonl (current event shapes — match their field names)
  - platforms/claude-code/agents/{ralph-loop-worker,ralph-orchestrator}.md; core/agents/
  - platforms/claude-code/commands/next-loop.md

  ## Constraints
  - Zero-dependency Python; do NOT change core/state/gate-verdict.schema.json
  - Do NOT backfill past history.jsonl events (spec Decision 6)
  - WORKER CONTRACT: do not commit; Write/Edit tools only; no absolute-Windows-path redirects
  - Core files must not reference platform paths (no .claude/ in core/agents/)

  ## On completion
  1. Update handoff_summary
  2. Mark all todos completed
  3. Write .advanced-plans/state/loop-complete.json
```

---

```yaml
---
name: "ralph-loop-066"
task_name: "Loop-Flow Economy"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "prepare_loop_ready + 6 tests (403 total green, AST NONE); next-loop.md Step 4 conditional fast-path + Step 3 checkpoint tags (source + byte-identical runtime copy); execution.log untracked (.gitignore + git rm --cached); rotation note in README.md; CLAUDE.md decision log updated; path_audit CLEAN; install_audit current."
  failed: ""
  needed: "Continue with loop-067: Compaction Backfill x9 (complete.md + manifest entries for phases 1-4, 7, 8, 10-12)."

todos:
  - id: "loop-066-1"
    content: "Add prepare_loop_ready(loops_md_path, prior_handoff) to platforms/python/state_manager.py: parses the next pending loop's frontmatter; conservative populated-predicate (todos non-empty AND every todo has id/content/outcome/status); returns the loop-ready dict and writes loop-ready.json, or signals agent-needed when the predicate fails"
    skill: "NA"
    agent: "NA"
    outcome: "prepare_loop_ready exists; populated loop -> valid loop-ready.json (loop_name, loop_file, task_name, todos_count, status ready, handoff_injected x3); stub/partial loop -> agent-needed signal, no file written"
    status: completed
    complexity: high
    priority: high
  - id: "loop-066-2"
    content: "Write tests for prepare_loop_ready: populated path writes schema-valid loop-ready.json; empty todos -> agent-needed; partially-populated todo (missing outcome) -> agent-needed; handoff injection carries done/failed/needed"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Four test cases green; full suite green; AST NONE"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-066-3"
    content: "Make next-loop.md Step 4 conditional (source + byte-identical runtime copy): populated -> Python fast-path, print '-> fast-path: loop already populated, orchestrator skipped'; stub/ambiguous/--full -> spawn ralph-orchestrator as today; existing Steps (3a archive, 3b resume, 3c --full) untouched"
    skill: "NA"
    agent: "NA"
    outcome: "next-loop.md Step 4 documents the conditional; all existing steps intact; runtime copy content-identical; path_audit CLEAN"
    status: completed
    complexity: medium
    priority: high
  - id: "loop-066-4"
    content: "Replace the Step 3 checkpoint commit with a lightweight tag checkpoint/loop-NNN (rollback documented: git reset --hard checkpoint/loop-NNN); gitignore .advanced-plans/logs/execution.log + git rm --cached it; add a rotation note to .advanced-plans/README.md; no history rewriting"
    skill: "NA"
    agent: "NA"
    outcome: "next-loop.md Step 3 tags instead of committing; execution.log untracked and ignored; rollback + rotation documented"
    status: completed
    complexity: medium
    priority: medium
  - id: "loop-066-5"
    content: "Add the CLAUDE.md decision-log entry: fast-path is an optimisation, the two-agent pattern remains the documented architecture; note checkpoint tags + log untracking; strike through the orchestrator-overhead/checkpoint-noise friction observations if logged"
    skill: "NA"
    agent: "NA"
    outcome: "CLAUDE.md decision log updated; friction log reconciled"
    status: completed
    complexity: low
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Stop paying for ceremony: Python fast-path for populated loops (orchestrator reserved for
  real planning), checkpoint tags instead of commits, execution.log out of git.

  ## Git checkpoint (run first)
  git tag checkpoint/loop-066 2>/dev/null || true

  ## Success criteria
  - [ ] prepare_loop_ready + 4 tests green; conservative predicate proven both ways
  - [ ] next-loop.md Step 4 conditional; Steps 3a/3b/3c intact; runtime copy identical
  - [ ] Checkpoint tagging replaces checkpoint commits; execution.log untracked
  - [ ] CLAUDE.md decision logged; suite green; AST NONE; path_audit CLEAN

  ## Required skills
  - verification-before-completion

  ## Inputs
  - platforms/python/state_manager.py + plan_io.py (frontmatter parsing already exists)
  - .advanced-plans/state/loop-ready.json (current shape to replicate)
  - platforms/claude-code/commands/next-loop.md

  ## Constraints
  - DOGFOODING-SENSITIVE: next-loop.md runs this phase — only ADD/SWAP the specified steps,
    verify byte-identity after the edit
  - Zero-dependency Python; no history rewriting; old checkpoint commits stay
  - WORKER CONTRACT: do not commit; Write/Edit tools only; no absolute-Windows-path redirects

  ## On completion
  1. Update handoff_summary
  2. Mark all todos completed
  3. Write .advanced-plans/state/loop-complete.json
```

---

```yaml
---
name: "ralph-loop-067"
task_name: "Compaction Backfill x9"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-067-1"
    content: "Backfill complete.md for phases 1-4 (pre-gate-review): anchor/end SHAs from git history; Goals met from loops.md handoff summaries with SHA evidence pointers; gate_verdict_ref sentinel ('n/a — pre-gate-review phase') + gate_verdict_note; LOCKED phase-complete schema obeyed"
    skill: "NA"
    agent: "NA"
    outcome: "phases 1-4 each have a schema-valid complete.md with sentinel verdict form and SHA-anchored bullets"
    status: pending
    complexity: high
    priority: high
  - id: "loop-067-2"
    content: "Backfill complete.md for phases 7 and 8: phase 7 reconstructed from git history (its dir is empty — commits exist) with sentinel verdict; phase 8 from its plan.md + loop-027 handoff (loops 028-031 absorbed into phase 9 — note in Deferred)"
    skill: "NA"
    agent: "NA"
    outcome: "phase-7/ and phase-8/ each have a schema-valid complete.md; phase-7's reconstruction is SHA-anchored; phase-8 records the 028-031 absorption"
    status: pending
    complexity: high
    priority: high
  - id: "loop-067-3"
    content: "Backfill complete.md for phases 10, 11, 12 (gate-reviewed — verdicts exist): use criteria_outcomes from the phase-goals verdicts for Goals met; real gate_verdict_ref paths; anchor/end SHAs from git + history.jsonl"
    skill: "NA"
    agent: "NA"
    outcome: "phases 10-12 each have a schema-valid complete.md referencing their real verdict files"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-067-4"
    content: "Append a <=8-line PLANS-INDEX manifest entry per backfilled phase (1-4, 7, 8, 10-12), ascending order among existing entries (9, 13, 14, 15); remove the 'phases 6/7 not yet backfilled' caveat line if now false"
    skill: "NA"
    agent: "NA"
    outcome: "All 15 phases have manifest entries; each <=8 lines, max 2 highlights; manifest section header caveat updated"
    status: pending
    complexity: medium
    priority: medium
  - id: "loop-067-5"
    content: "Validate every backfilled artefact against the LOCKED schema checklists (SHAs resolve via git rev-parse; commit_count within +-1 of rev-list; one-line bullets; sentinel form only where verdicts are absent); record validation evidence in the handoff"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "All 9 artefacts + 9 manifest entries pass the schema checklists; evidence recorded"
    status: pending
    complexity: medium
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Complete the programme's documentary record: complete.md + manifest entry for all 9
  uncompacted phases, schema-valid, SHA-anchored, sentinel form where pre-gate.

  ## Git checkpoint (run first)
  git tag checkpoint/loop-067 2>/dev/null || true

  ## Success criteria
  - [ ] 9 schema-valid complete.md artefacts (1-4, 7, 8, 10-12)
  - [ ] 9 manifest entries, all <=8 lines; all 15 phases now covered
  - [ ] Pre-gate phases use the sentinel verdict form; 10-12 reference real verdicts
  - [ ] Every bullet SHA- or path-anchored; validation evidence in handoff

  ## Required skills
  - verification-before-completion

  ## Inputs
  - docs/phase-complete.schema.md + docs/phase-manifest-entry.schema.md (LOCKED — obey, never edit)
  - git log; .advanced-plans/state/history.jsonl; per-phase loops.md handoffs
  - .advanced-plans/gate-verdicts/phase-{10,11,12}-*.json

  ## Constraints
  - Writes ONLY under .advanced-plans/ — no source/code changes in this loop
  - Do NOT backfill handoff.md (spec decision); do NOT fabricate history.jsonl events
  - LOCKED schema docs byte-unchanged
  - WORKER CONTRACT: do not commit; Write/Edit tools only; no absolute-Windows-path redirects

  ## On completion
  1. Update handoff_summary
  2. Mark all todos completed
  3. Write .advanced-plans/state/loop-complete.json
```

---

```yaml
---
name: "ralph-loop-068"
task_name: "Auto-Compact at Close + Release"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-068-1"
    content: "Extend run-gate.md Step 10.4 (source + byte-identical runtime copy): after the closeout commit, run /phase-compact's artefact steps inline (cold artefact, manifest entry, handoff digest via handoff_digest.py) — idempotent, main-thread; the context /compact consent gate is explicitly unchanged"
    skill: "NA"
    agent: "NA"
    outcome: "run-gate.md Step 10.4 produces compaction artefacts on a current-phase pass without a separate /phase-compact call; consent semantics for conversation compaction untouched"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-068-2"
    content: "Demonstrate the close->compact wiring: a witnessed simulation (throwaway worktree or fixture phase) OR rely on this phase's own gate as the live proof — capture which path was used and the evidence in the handoff"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Evidence that a gate-pass closeout yields complete.md + manifest + handoff.md unprompted"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-068-3"
    content: "Verification sweep: full suite (pytest), AST zero-dep (CI flags), path_audit, install_audit --layers source,project; confirm LOCKED schema docs + gate-verdict.schema.json + codex_gate/remediate/remediation_controller byte-unchanged vs anchor 5ffaa64"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "All checks green/CLEAN/current; byte-unchanged confirmations recorded"
    status: pending
    complexity: low
    priority: high
  - id: "loop-068-4"
    content: "Cut v0.16.0: VERSION bump; CHANGELOG [0.16.0] section (Added: install_audit + /sync-install + CI drift step, history_log + event wiring, prepare_loop_ready fast-path, 9 backfilled complete.md; Changed: worker-contract guards in agent defs, checkpoint tags, execution.log untracked, run-gate auto-compact); CLAUDE.md Phase 16 decision-log entry"
    skill: "NA"
    agent: "NA"
    outcome: "VERSION=0.16.0; CHANGELOG + decision log consistent with shipped work"
    status: pending
    complexity: low
    priority: high
  - id: "loop-068-5"
    content: "Friction-log closeouts for everything Phase 16 resolved; ensure the phase-close output prints the operator push reminder (git push origin main --follow-tags)"
    skill: "NA"
    agent: "NA"
    outcome: "Friction log reconciled with strikethrough + Loop notes; push reminder present in the close path output"
    status: pending
    complexity: low
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Close the loop on the gate->close->compact progression (artefacts automatic, consent
  manual), verify the whole phase, and cut v0.16.0.

  ## Git checkpoint (run first)
  git tag checkpoint/loop-068 2>/dev/null || true

  ## Success criteria
  - [ ] Gate-pass closeout yields compaction artefacts unprompted; consent gate unchanged
  - [ ] Full suite green; AST NONE; path_audit CLEAN; install_audit current
  - [ ] LOCKED docs + protected modules byte-unchanged vs anchor
  - [ ] v0.16.0 cut; friction log reconciled; push reminder in close output

  ## Required skills
  - verification-before-completion

  ## Inputs
  - platforms/claude-code/commands/{run-gate,phase-compact}.md
  - platforms/python/handoff_digest.py; VERSION; CHANGELOG.md; CLAUDE.md

  ## Constraints
  - The context /compact consent gate must remain user-consented — artefacts only are automated
  - LOCKED schema docs + gate-verdict.schema.json byte-unchanged; no logic changes to
    codex_gate.py / remediate.py / remediation_controller.py
  - WORKER CONTRACT: do not commit; Write/Edit tools only; no absolute-Windows-path redirects

  ## On completion
  1. Update handoff_summary
  2. Mark all todos completed
  3. Write .advanced-plans/state/loop-complete.json
```
