# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Fixed

- **The Markdown Lint job can now fail.** It ran
  `markdownlint-cli2 … --config .markdownlint.json || true` against a
  `.markdownlint.json` that did not exist in this repository, and swallowed the
  result. It had reported `SUCCESS` on every pull request ever opened here and
  could not have reported anything else — the same defect class as the rest of
  `0.18.0`, with a filename standing in for a fact read off the machine. The
  config now exists, the `|| true` is gone, and the linter version is pinned so
  an upstream release cannot turn `main` red on a day nobody here committed
  anything.

  Getting there took two passes over 8,430 default-rule violations. `MD013`
  (5,062) and `MD060` (1,496) are disabled as style, not defects; `MD024` is
  `siblings_only` because a CHANGELOG repeats `### Fixed` under every version.
  `MD038` and `MD029` are disabled for a different reason: **their autofixes
  are destructive on this repository specifically.** Much of this markdown is
  agent instructions, where the whitespace inside an inline code span is the
  content — `` `  anchor_sha: [SHA]` `` tells an agent to print an indented
  line — and `--fix` strips it, turning ``separated by `, ` `` into
  ``separated by `,` `` in 18 places. That was caught by checking whether the
  diff was whitespace-only rather than by trusting the tool.

  The remaining 329 were resolved by hand: 285 untagged code fences, 43 uses of
  emphasis as a heading, and one duplicate heading whose only inbound link
  (`#anchor-sha-decision-1`) resolved solely _because_ of the duplication. Two
  of the 43 are genuine emphasis — a subtitle and a colophon — and carry an
  inline exemption naming the reason rather than being promoted into sections
  that do not exist.

- **`platforms/claude-code/install.sh` no longer nests a copy of every skill
  inside itself, and no longer claims to have symlinked what it copied.** The
  `do_ln` guard landed in `setup/claude-code/install.sh` in `0.18.0` with a test
  class beside it; this second installer carried the identical defect the whole
  time, because no test named it. `ln -sf SRC DEST` where `DEST` already exists
  as a real directory does not replace it — it creates `DEST/basename(SRC)`
  inside it and exits 0, and the `cp -r` fallback nests identically. Installing
  twice into the same project therefore produced `.claude/skills/<name>/<name>`
  for all nine core skills while reporting a clean `Symlinked` both times. On a
  host where `ln -s` really does link, the second install resolves _through_ the
  first link and writes that nested copy into `core/skills/` in the source
  repository; it escaped that here only because MSYS silently degrades symlinks
  to copies.

  That degradation is the second half of the fix. `ln` on Windows copies and
  exits 0, so `Symlinked` was printed for a plain copy — a claim about the
  machine that nothing had read back off it. The installer now reads the
  destination back and names what is actually on disk.

  A destination that already exists is compared rather than refused outright,
  because refusing would break re-installing on every host where symlinks
  degrade to copies. Identical reports `unchanged`; a genuine divergence is
  refused by path with the reason; and `diff` exiting `>= 2` — _could not
  compare_ — is reported as its own outcome instead of being read as _differs_.
  The comparison uses `--strip-trailing-cr`, agreeing with `install_audit`
  rather than inventing a second answer to what counts as drift.

  Four tests cover it, and each was proven by restoring the pre-fix script
  byte-for-byte and rerunning: **4 of 4 fail against it**, all 4 pass with the
  fix, and the working tree was restored byte-identical by sha256.

---

## [0.18.0] - 2026-08-31

Eight fixes to checks that could not fail, and to two installers that could
destroy a user's files. Everything here was found by auditing 0.17.0 rather
than by using it: a full code review and a security review, fanned out across
several models, then verified one finding at a time against the machine.

One defect class accounts for nearly all of it. **A check fails silently
wherever its subject is a string it interpolated or parsed, rather than a fact
read off the machine.** Three audits exited 0 having opened no files. Three
remediation guards compared against something no writer emitted. Two test files
skipped their entire shell half on the only platform they run on. A guard was
hardened and then bypassed by a pre-delete on the path that mattered. In each
case the green was real and meant nothing.

The corollary matters too, and shaped the fixes: **a check that cannot pass is
also a defect**, because a permanently-red job teaches people to ignore red. So
none of these exit non-zero merely to be safe — each names its subject, says
what it could not find, and tells you what to do about it.

### Fixed

- **Three audits now assert a non-empty subject.** `ast_check` exits 2 when no
  `.py` files are found or a named `PATH` does not exist, instead of warning and
  skipping. `path_audit` counts the files it actually opened and exits 2 if the
  total is zero; its success line prints the roots it really scanned with
  per-root counts, rather than echoing the `DEFAULT_SCANNED_ROOTS` constant.
  `install_audit` exits 2 when an explicitly named `--layers` pair produces no
  verdicts. Two exclusion bugs went with them: `--exclude` matched against the
  absolute path, so a checkout under a directory named `tests` excluded its own
  contents, and `_is_excluded` matched a substring rather than a path segment,
  so `/home/ci/docs-build/` was silently skipped.

- **`install_audit` no longer announces its own failure and returns 0.**
  `if not results:` printed "Run is inconclusive" to stderr and passed;
  `install_audit --root /nonexistent --layers source,project` exited 0. A
  missing source directory printed an ERROR and then `continue`d, under a
  comment reading "Treat as drift: record all source files as missing" that
  described work the code did not do. An absent source surface now produces a
  real `source_missing` verdict that reaches `has_drift`, the report and the
  summary.

- **`validate_diff_allowlist` now consults the allowlist.** It checked only the
  never-touch list, so a path outside the allowlist entirely — not forbidden,
  simply not permitted — passed. It now returns `(path, reason)` pairs that
  distinguish `never_touch` from `not_allowlisted`.

- **Criteria coverage no longer passes on an empty criteria list.** Nothing to
  cover had satisfied "all covered". An empty `frozen_criteria` now returns
  `empty_criteria`, which the verdict reports distinctly from criteria that are
  missing.

- **The stale-state guard now keys on a field something writes.**
  `archive_cross_phase_state` compared a `phase` field in `loop-ready.json` that
  no writer emitted, so it archived nothing and had been inert since it was
  added. `write_loop_ready` now emits `phase` (or raises rather than writing a
  file the guard cannot use), `loop-ready.schema.json` requires it, and a file
  written before this change is archived as stale rather than trusted.

- **The claude-code installers no longer destroy files.** A pre-existing
  `.claude/settings.json` is left byte-identical and the installer's own
  configuration goes to `settings.planning.json` beside it. `--symlink` over a
  real `.claude/skills` directory refuses and exits 1, naming the path, instead
  of exiting 0 having created a nested `skills/skills` link inside it;
  `install.sh` no longer contains any `rm -rf`. The PowerShell host had been
  hardened and then bypassed — its self-install block recursively deleted
  `commands`, `skills` and `schemas` _before_ calling the guard that refuses a
  real directory, and deleted the `agents` directory unconditionally where the
  POSIX host refuses it. Both hosts now take the same decision, and so does the
  dry run, which previously promised a link the real run would refuse.

- **Uninstall fails closed when ownership cannot be established.** Codex and
  OpenCode share one skill tree through `skill-ownership.json`. With that
  registry missing or malformed, both uninstallers proceeded anyway and removed
  shared files including `bin/ap.py`, the launcher the other adapter's skills
  invoke. Both now exit 1, name the file, and leave the tree untouched;
  `--force-no-registry` / `-ForceNoRegistry` is the deliberate escape hatch and
  warns what it may remove. The malformed-registry message no longer advises
  deleting the file, which produced the missing-registry case that is refused
  for the same reason.

### Changed

- **Tests that could not fail were replaced, not deleted.** `exit_code in
  (0, 2)` in a test named for exit 2; two tests asserting that a layer was
  absent from a run in which no layer existed; a test asserting `rc == 0`
  against a home directory containing no `.claude/`; a test with no assertions
  at all; a test that passed _because_ of the bug it was named for; and, in the
  class whose stated job is catching silent skips, `assert available or True`
  with a comment noting that it always passes. Each is now an assertion that
  fails against the code it was written for — proven by restoring that code
  byte-for-byte and re-running.

- **The shell half of both installer test files runs on Windows.** Thirteen
  tests skipped unconditionally there, for the stated reason that bash cannot
  run these scripts from a Python subprocess. The symptom was real and the
  diagnosis wrong: the `bash` on `PATH` is WSL, which resolves `/mnt/c/...` and
  cannot open a Windows path, while Git Bash — present on the same machine —
  runs them without trouble. Both files now resolve Git Bash by path, pass
  forward-slash paths, and decode subprocess output as UTF-8, which installers
  require and `cp1252` cannot do. Each file also fails outright if neither host
  is available, so a run in which everything skipped can no longer be reported
  as green.

### Added

- **A static check for Python embedded in shell heredocs.** The uninstallers'
  ownership logic lives inside a `python` heredoc, where `bash -n` sees only an
  opaque string: a mis-indented line there leaves the script syntactically valid
  and fails at run time, on the exact path meant to protect the user's files.
  This was not hypothetical — an edit made during this release landed at the
  wrong indent and `bash -n` passed it. The test compiles every `python` heredoc
  it finds, and fails if it finds none, since a pattern that matches nothing
  would otherwise pass while testing nothing.

### Notes

Every fix in this release was verified by restoring the pre-fix code
byte-for-byte, running the new tests against it, confirming they fail, and
restoring the branch version with a byte-identical assertion — no `git reset`,
no operations on the working tree. Collection was diffed against `main` on each
branch to prove no test was silently dropped: **+64 added, 2 removed** across
the four. Both removals are named above — `test_no_archive_when_phase_field_absent`
and `test_empty_frozen_criteria_always_passes`, each asserting the defective
behaviour as though it were intended, and each replaced by its inverse in the
same commit. The full suite on merged `main` is **872 passed, 1 skipped**
(873 collected, against 811 before this release): the one skip creates a
symlink, which needs Windows Developer Mode, and it names `WinError 1314`
rather than skipping silently.

---

## [0.17.0] - 2026-08-31

Adapter expansion, and the checks that caught what it broke. Driven from the
Advanced AI Workflows controller programme rather than this repository's own
loop machinery, so there are no loop numbers to cite: the work arrived as seven
stacked branches and a nine-finding cross-model review that grew to fifteen.

Two new host adapters (Codex, OpenCode) join claude-code, sharing one skill tree
through an ownership mechanism so neither uninstall removes the other's
registrations. Plannotator is gone. A zero-dependency JSON Schema validator and
three schemas make the controller/worker contract checkable. And a run of
repairs to checks that could not fail -- the recurring defect of this release,
found in five separate places.

### Added

- **Codex adapter** -- `setup/codex/install.{sh,ps1}`, uninstallers for both,
  and a shared routing skill. `skill-ownership.json` records which hosts
  registered which skills, so the last approved owner leaving does not strip a
  third party's registrations.
- **OpenCode adapter** -- `setup/opencode/`, the Codex scripts with the
  host-specific changes applied, and `setup/opencode` brought into the install
  audit.
- **A zero-dependency JSON Schema validator** (`minischema`) and three schemas:
  the external task envelope (controller to worker), collected evidence
  (post-execution), and run contracts. Wired into CI as its own job, with
  fixtures.
- `platforms/python/state_validate.py` -- validates `.advanced-plans/state/`
  against the schemas, anchored on the package location so it resolves from any
  working directory (Contract 6: an installed project has no `core/`).
- **Host-neutrality enforcement** in `path_audit` -- host directories, host-only
  tool names and host permission syntax, scoped to `core/`, with the violations
  it found resolved.
- `platforms/python/tests/test_adapter_lifecycle.py` -- install/uninstall pairs
  for every adapter, and the `AP_REQUIRE_ADAPTER_INTERPRETERS` escalation that
  turns a missing `sh` or `pwsh` from a silent skip into a failure.
- `.gitattributes` -- absent until now, which is how CRLF had been arriving
  unnoticed.
- An uninstall path for `setup/`, and the destination-link guard it needed.

### Changed

- `minischema` promoted from test helper to production module.
- CI's Path Convention Audit installs a real global layer and audits against it,
  rather than auditing a layer a fresh checkout cannot have.

### Removed

- **Plannotator.** The deprecation had been declared complete in two documents
  and was half done: `/plan-and-phase` Step 5b still detected the plugin and
  invoked it, and `companion-detection` still told a user without it installed
  to `git clone` it -- on the same branch whose new adapter READMEs asserted "No
  Plannotator". Now removed, with a detector that carries its own self-test.

### Fixed

- **The shared Python runtime is reachable from an installed project.** 14 call
  sites across 6 command files invoked `.advanced-plans/bin/ap.py`, but no
  installer had ever shipped `platforms/python/` into a project -- so every
  command died on the interpreter's own "can't open file", naming neither the
  product nor the repair. The installers now record `runtime.json` and copy the
  launcher (outside the scaffold guard, so an upgrade refreshes a stale
  `source_root`), and `ap_launcher.py` walks up to find it.
- **A `--global` install now works in projects the installer never touched.**
  `setup/claude-code/install.{sh,ps1}` and `platforms/claude-code/install.sh`
  write `<home>/.advanced-plans/{runtime.json,bin/ap.py}` and rewrite the
  launcher path in each command they copy. `<home>` resolves from `USERPROFILE`
  before `HOME`: under Git Bash on Windows those routinely disagree, and the
  install would otherwise land where native Python never looks.
- **The manifest walk stops at a project boundary.** A project holding
  `.advanced-plans/` without a manifest, or any `.git` without one, no longer
  borrows an enclosing checkout's runtime -- it falls through to the global
  record, and names both places it looked when there is none. A linked worktree
  or submodule (`.git` as a _file_, not a directory) is recognised.
- **The in-line `runpy` call sites print the guard, not a traceback.**
  `bootstrap()` catches `Unreachable`, reports, and exits 3 (`EXIT_UNREACHABLE`).
- `install_audit` no longer reports every globally installed command as
  permanently stale: the install-time launcher path is canonical, not drift,
  and is normalised out before hashing. Source call sites are quoted and
  raw-prefixed so the installers' rewrite swaps only the path.
- **Install no longer strips CRLF.** Source line endings are preserved in both
  hosts, with a self-detecting test.
- **Installers point at documentation that exists**, pinned so it stays that way.
- Skill trees are walked recursively when checking and rewriting, and `--global`
  is compared against what it would actually write rather than the raw source.
- The uninstall ownership merge is correct in both `sh` and `ps1`, and prunes
  `.agents/` properly.
- Workers may commit, and sign their commits, so authorship is visible in the
  history rather than inferred.

### Fixed -- checks that could not fail

The recurring defect of this release. A check whose subject is a string someone
interpolated, rather than a fact read off the machine, reports success without
having looked at anything. Five instances, each now carrying a test proven to
fail when the defect is put back:

- **Two differential tests could pass vacuously** -- the detector matched
  nothing, so the comparison was between two empty sets.
- **`test_removal_counts_agree` could not fail** at all.
- **The Path Convention Audit job had never once been able to pass.** It audited
  `--layers source,project`; `.gitignore` excludes `.claude/*` but tracks
  `.claude/settings.json`, so on a runner `.claude/` exists while its
  subdirectories do not, and the "not found -- skipped" guard tests directory
  presence. One tracked file defeated it and all 27 source files reported
  missing. The minimal repair would have been vacuous in the other direction --
  a missing layer is skipped and returns 0 -- so the runner now installs a real
  global layer, which makes a pass mean the installer reproduces every source
  file byte-for-byte.
- **A test module that could not pass on Linux.**
  `test_home_resolution_agreement.py` set `HOME` to a path that does not exist.
  Windows `pwsh` does not care; Linux `pwsh` exits 70 building its own profile,
  before the function under test runs. Six cases had failed on every Linux run
  since the module was introduced, and passed on Windows throughout. Invisible
  from a Windows machine, and found only by opening the pull requests.
- **A CI step no branch had ever reached.** `pytest` failed ahead of "Verify no
  external dependencies", so `ast_check` had never executed on any branch in the
  chain. Fixing the module above is what exposed it.

### Changed -- the import allow-set

`platforms` joins `core/constraints.json`'s `allowed_imports`. It is this
project's own package, not an external dependency, so the stdlib-only policy is
unchanged. The cost is recorded beside the entry rather than left implicit: an
installer copies `ap_launcher.py` into a directory where the package does not
exist, so a `platforms` import _there_ breaks the installed launcher and
`ast_check` no longer catches it.

`TestShippedModulesImportStdlibOnly` restores that protection for exactly the
modules an installer ships. It reads which modules those are off the installers
rather than naming one, so a module that starts being shipped is covered the day
it starts -- and reading it properly corrected the finding from one shipping
site to six, across all three hosts.

---

## [0.16.0] - 2026-06-10

Phase 16 — Trust the Machinery (Loops 064–068, 5 loops).
Wires the install-layer upgrade pathway, a trustworthy audit-log record, the orchestrator
fast-path for populated loops, a full 15-phase compaction backfill, and auto-compact at
gate close — then cuts the release.

### Added

- `platforms/python/install_audit.py` — stdlib-only drift auditor; compares source
  (`platforms/claude-code/{commands,agents}/` + `core/schemas/`) vs project (`.claude/`)
  vs global (`~/.claude/`, USERPROFILE-first on Windows) by EOL-insensitive content hash;
  per-file report current/stale/missing; `--layers` flag; exits non-zero on drift.
- `platforms/claude-code/commands/sync-install.md` (+ `.claude/` runtime copy) — `/sync-install`
  command; runs `install_audit`, then refreshes stale copies source→outward (plain `cp`);
  `--check` = audit only; never syncs backwards; CLAUDE.md Command Surface row added.
- `.github/workflows/ci.yml` job 5 — runs `install_audit --layers source,project` on push/PR;
  blocks on source↔project drift.
- `platforms/python/history_log.py` — `append_event(history_path, event_dict)`: compact JSON
  separators, ISO-8601 UTC timestamp injected if absent, append-only, parent dir auto-created;
  plus a tiny CLI (`python -m platforms.python.history_log <path> '<json>'`).
- `platforms/python/state_manager.prepare_loop_ready` — Python fast-path for `/next-loop`
  Step 4: parses the next pending loop's frontmatter and writes `loop-ready.json` directly when
  the loop is already fully populated (todos non-empty, every todo has id/content/outcome/status),
  skipping the ralph-orchestrator spawn; signals agent-needed on stub/partial loops.
- 9 backfilled `complete.md` artefacts — phases 1–4, 7, 8, 10–12 — all schema-valid per the
  LOCKED `docs/phase-complete.schema.md`; sentinel verdict form where pre-gate-review; SHAs
  anchored and verified; `phase-7/` directory created.
- 10 manifest entries in `PLANS-INDEX.md` — phases 1–4, 6–8, 10–12; all ≤8 lines; all 15
  phases now fully covered.
- `run-gate.md` Step 10.4 sub-step 4 — on a current-phase gate pass, `/run-gate` now also runs
  the `/phase-compact` artefact pipeline inline (cold artefact, manifest entry, `handoff.md` via
  `handoff_digest.py`) and commits the compaction artefacts automatically. Consent gate for
  conversation `/compact` is unchanged — artefacts are automatic; `/compact` is user-consented
  only.

### Changed

- `platforms/claude-code/commands/next-loop.md` Step 4 (+ `.claude/` copy) — conditional
  fast-path: fully-populated loop → Python fast-path (orchestrator skipped); stub or `--full` →
  orchestrator as before.
- `platforms/claude-code/commands/next-loop.md` Step 3 (+ `.claude/` copy) — checkpoint commits
  replaced by lightweight tags (`checkpoint/loop-NNN`); rollback documented as
  `git reset --hard checkpoint/loop-NNN`; old checkpoint commits preserved in history.
- `.advanced-plans/logs/execution.log` — added to `.gitignore`; `git rm --cached` applied; file
  stays on disk for the operator to rotate/truncate freely.
- `platforms/claude-code/agents/ralph-loop-worker.md`, `ralph-orchestrator.md`,
  `core/agents/worker.md`, `core/agents/orchestrator.md` — `## Hard Contract (non-negotiable)`
  section added to all four: (a) never commit, (b) Write/Edit tools only — no shell redirects,
  (c) no absolute Windows paths in shell commands. Installed copies refreshed byte-identical.
- `platforms/claude-code/commands/next-loop.md` Step 9 (+ `.claude/` copy) — `loop_complete`
  event wired via `history_log` CLI; `plan-and-phase.md` Step 8 and `new-phase.md` Step 12 emit
  `phase_planned` events.
- `run-gate.md` frontmatter description and Step 11 pass summary updated to reflect that
  compaction artefacts are written automatically at close; "Run /phase-compact [N]" guidance
  replaced by "artefacts written automatically; run the offered /compact line when ready".

---

## [0.15.0] - 2026-06-09

Phase 15 — Automation-Surface Audit (Loops 059–063, 5 loops).
Closes the loose Phase 14 threads (gate-override policy, codex version-coupling guard),
wires in four automation improvements discovered during the friction-log audit, and
cuts the release.

### Added

- `platforms/python/path_audit.py` — stdlib-only CI path-convention audit; scans
  command/agent/doc files for non-canonical path tokens (doubled prefix, `.claude/plans/`,
  `.claude/.advanced-plans`); exits non-zero with a clear report on any match.
- `.github/workflows/ci.yml` job 4 — runs `path_audit.py` on push/PR; blocks on failure.
- `platforms/claude-code/commands/sync-plans.md` (+ `.claude/` runtime copy) — `/sync-plans`
  command that re-renders PLANS-INDEX.md phase and loop rows from `plan.md`/`loops.md`
  without manual edits; idempotent and drift-killing.
- `platforms/claude-code/commands/next-loop.md` Step 3c `--full` flag (+ `.claude/` copy) —
  one-pass stub population: chains `plan-todos` → `plan-skill-identification` →
  `plan-subagent-identification` before the orchestrator runs; composable with `--auto`.
- `docs/gate-override-policy.md` — formal gate-pass-with-dissent override policy; defines
  permitted conditions (environment/isolation false-negative, no deliverable defect, both
  in-house agents pass), required `history.jsonl` record (`override: true` +
  `override_reason`), authorisation rule (human operator only, never an agent), and what
  is never a valid override.
- `TestCaptureContractVersionGuard` in `test_codex_gate_live.py` — 6 new tests asserting
  the run-gate codex capture contract (single fenced JSON block from `-o <file>` parses to
  a schema-valid `backend: codex` verdict); fails loudly if codex output shape changes.

### Changed

- `platforms/claude-code/commands/next-loop.md` Step 3a (+ `.claude/` copy) — wired
  `archive_cross_phase_state()` call to archive stale prior-phase `loop-ready.json` /
  `loop-complete.json` to `.advanced-plans/state/archive/` at phase boundary.
- `.advanced-plans/PLANS-INDEX.md` — corrected stale `**pending**` status rows for
  completed loops 042–046 and 055–058; phase-14 entry updated from `**draft**` to
  `**complete**`.
- `docs/master-plan.md` — marked historical; programme ran 15+ phases beyond the original
  4-phase scope.
- `CLAUDE.md` — Gate Review Protocol section now cross-references
  `docs/gate-override-policy.md`; Phase 15 decision-log entry added; `--full` flag
  documented.
- `platforms/claude-code/commands/run-gate.md` Step 10.4 (+ `.claude/` copy) — on a gate
  **pass for the current phase**, `/run-gate` now closes the phase out automatically (moves
  it to `phases.complete`, advances `current_phase`, appends a `phase_closed` event, commits)
  and directs to `/phase-compact`. Removes the "gated but not closed" seam. `--phase N` on a
  non-current phase does not auto-close.
- `platforms/claude-code/commands/next-phase.md` Step 1a (+ `.claude/` copy) — detects a phase
  already closed by `/run-gate` (current-phase plan absent ⇒ pointer already advanced) and
  skips re-gating; under `--auto` proceeds to plan the freshly-pointed phase, otherwise directs
  to `/phase-compact` + `/plan-and-phase`. Command Surface descriptions updated accordingly.

---

## [0.14.0] - 2026-06-09

Phase 14 — Install & Exercise Codex Gate + Self-Heal in Runtime (Loops 055–058, 4 loops).
Wires the Phase 12 codex gate and Phase 13 self-heal — built and tested in source but never
installed — into this repo's own `.claude/` runtime, then proves both via automated tests
**and** a witnessed live exercise, closing the framework's check-build-correct recursion.

### Added

- `platforms/python/tests/test_codex_gate_live.py` — live codex-gate proof: a real
  `codex exec` stdout fixture parses via `extract_and_validate` into a schema-valid
  `backend: codex` verdict, the graceful-degrade path is asserted (genuine ambiguity →
  no `codex.json`, `gate_codex_skipped`), and the codex preflight is smoke-tested.
- `platforms/python/tests/fixtures/` — real captured `codex-cli 0.124.0` stdout (+ provenance
  README) used by the live test.
- `platforms/python/tests/test_self_heal_integration.py` — 26 sandboxed integration tests
  driving `remediation_controller` triage → diff-allowlist NEVER-TOUCH breach escalation,
  sentinel/criteria-hash guards, cycle-bound escalation, and a full synthetic remediation
  trace — all in `tmp_path`, touching no real file or git history.
- `.claude/agents/codex-reviewer.md` — parity copy of the `core/agents/` codex contract doc.
- `.advanced-plans/phases/phase-14/exercise-058-transcript.md` — captured transcript of the
  witnessed live self-heal run (induced gate fail → triage → allowlisted fix → re-gate pass),
  executed in a throwaway git worktree and discarded, leaving `main` pristine.

### Changed

- `.claude/commands/run-gate.md`, `.claude/commands/next-phase.md` — refreshed byte-identical
  from `platforms/claude-code/commands/` source, installing the codex gate (92 codex refs) and
  the self-correcting gate / remediation flow (46 remediation refs) into the live runtime.
- `platforms/python/codex_gate.py` — `extract_verdict_json` now treats multiple _structurally
  identical_ fenced JSON blocks as non-ambiguous (returns the last block), since `codex exec`
  echoes its verdict block twice. Genuinely-differing blocks still degrade. Minimal scoped fix
  for a blocking bug surfaced during the live exercise (Loop 056 finding); the runtime codex
  live-run criterion is now achievable.
- `CONTRIBUTING.md` — added a runtime-drift note: `.claude/commands/*` are copied (not
  symlinked) from source at install time, with the explicit `cp` re-sync commands.
- `platforms/claude-code/commands/run-gate.md` (+ runtime copy) — fixed the codex
  invocation, exercised for real for the first time at the Phase 14 gate: `--read-only`
  (not a valid codex-cli flag) → `-s read-only`; capture the verdict from the `-o`
  last-message file instead of parsing the multi-block `codex exec` stdout transcript;
  `</dev/null` so `codex exec` does not block on stdin; auth preflight also checks
  `$USERPROFILE/.codex/auth.json` (git-bash `HOME` may differ from the Windows profile);
  and a criterion-scoping rule so codex marks gate-verdicts-existence criteria
  `not_applicable` (main-thread-verified) and sandbox-blocked test criteria `deferred`
  rather than `failed`. Runtime copy kept byte-identical.

---

## [0.13.0] - 2026-06-09

Phase 13 — Self-Correcting Gate (Loops 051–054, 4 loops). Gate PASSED (attempt 1).

### Added

- `platforms/python/remediate.py` — zero-dependency triage helper (`triage_findings`)
  classifying gate-verdict findings into `structural`, `localized`, `unfixable`, and
  `conflict` buckets, keying on `severity == "critical"` and actionable location strings.
- `platforms/python/remediation_controller.py` — eight zero-dependency predicate helpers
  encoding the bounded remediation controller's guard rails: `count_gate_fail_cycles`,
  `is_path_never_touch`, `is_path_in_allowlist`, `validate_diff_allowlist`,
  `is_transient_path`, `has_allowlisted_source_changes`, `compute_criteria_hash`,
  `validate_criteria_hash`, `validate_regateverdict_criteria_outcomes`, `has_sentinel`.
- `platforms/python/tests/test_remediate.py` — 19 tests covering all triage routes.
- `platforms/python/tests/test_remediation_controller.py` — 62 tests covering all 7 required
  escalation paths, two E2E controller traces (fix→re-gate→pass; bound→escalate at cycles≥2),
  and two gate-gaming guard traces (loops.md edit rejected; criteria-frozen.md edit rejected).
- **Bounded self-heal in `/next-phase --auto` (Step 7-AUTO, next-phase.md):**
  - Cycle counter from `history.jsonl` `gate_fail` events; escalate at `cycles >= 2` to
    versioned-retry+STOP from the pre-remediation snapshot (`PRE_REMEDIATION_SHA`).
  - Triage dispatch: structural findings re-run the affected loops; localized findings
    spawn `analysis-worker` with a focused-fix prompt.
  - **Anti-gate-gaming safety spine:**
    - Diff allowlist: remediation diffs are validated against a NEVER-TOUCH list
      (plan.md, loops\*.md, criteria-frozen.md, core/schemas/, core/state/,
      gate-reviewer docs, gate-verdicts/, history.jsonl, sentinels); any match → escalate.
    - Frozen criteria: `## Success Criteria` from `plan.md` frozen to
      `criteria-frozen.md` before cycle 1 and SHA-256 hash-verified before each re-gate;
      any drift → escalate.
    - Full `criteria_outcomes`: re-gate verdicts must contain an entry for every frozen
      criterion; any missing criterion → escalate.
  - Git-state policy: remediation commit stages only allowlisted source paths (no
    `git add -A`); no-change detection excludes transient files; dirty-tree preflight
    escalates on unrelated uncommitted changes.
  - Composition rules: `--force`/`--skip-gate` bypass remediation (precedence documented
    in Step 7.0); a failing structural re-run loop hits the existing loop-fail STOP;
    contradictory findings escalate with `remediation_conflict`.
  - New history events: `gate_remediation` (per cycle) and `passed_after_remediation: true`
    flag on a `gate_pass` following ≥1 cycle.
- **Re-Gate Isolation Rule in `core/agents/gate-reviewer.md`:** gate agents must not read
  `retry-context.*`, `gate-verdicts/`, or prior verdicts on a re-gate; must evaluate
  `criteria-frozen.md` (or phase-plan fallback); must emit `criteria_outcomes` for ALL
  criteria. CC agents inherit via their existing protocol reference.
- `gate_failure_context` now rides the `retry-context.json` sidecar
  (`.advanced-plans/phases/phase-N/retry-context.json`) rather than being injected into
  `loops.md` frontmatter, so re-gate agents remain blind to failure context.

### Changed

- `platforms/python/versioning.py` — `inject_failure_context` retargeted to write
  `phase-N/retry-context.json` sidecar; no longer injects into `loops.md` frontmatter.
- `core/state/gate-failure-context.schema.json` — description updated to reference the
  worker-only `retry-context.json` sidecar.
- `core/constraints.json` — `hashlib` added to the stdlib allow-set (used by
  `remediation_controller.compute_criteria_hash`).

### Fixed

- `remediation_controller.validate_regateverdict_criteria_outcomes` now parses the
  schema-compliant `criteria_outcomes` **array** of `{criterion, status, evidence}`
  objects (union of `criterion` values), with tolerance for the legacy dict form and
  malformed entries. Previously it tested membership against a list-of-dicts, so a
  real schema-compliant re-gate verdict read every criterion as missing and would have
  wrongly escalated. Caught by the Phase 13 gate; +4 array-form tests close the blind
  spot (300 tests total).

---

## [0.12.0] - 2026-06-08

Phase 12 — Codex Cross-Model Second-Opinion Gate Reviewer (Loops 047–050, 4 loops).
Gate pending at time of this entry.

### Added

- `platforms/python/codex_gate.py` — zero-dependency (stdlib: `json`, `re`, `pathlib`)
  helper with four public functions: `extract_verdict_json`, `validate_verdict`,
  `extract_and_validate`, and `aggregate_verdicts`. Handles fenced-block extraction,
  lenient structural validation, identity-overfit detection, and multi-verdict AND
  aggregation with conflict detection.
- `platforms/python/tests/test_codex_gate.py` — 26 tests covering all original 20 paths
  (extraction × 5, validation × 6, extract-and-validate × 3, aggregation × 6) plus 6
  new tests for the degrade path (codex absent) and three-verdict AND (codex present).
- `core/agents/codex-reviewer.md` — platform-agnostic Codex reviewer contract:
  untrusted-artefact rule, isolation rule (no `gate-verdicts/` reads), fenced-json-only
  output, `agent: "codex"` identity, per-criterion file/line evidence requirement.
- Codex integration wired into `platforms/claude-code/commands/run-gate.md`:
  - Preflight: `which codex` + local auth check (`~/.codex/auth.json` /
    `$CODEX_API_KEY` / `$OPENAI_API_KEY`); no gstack coupling.
  - Execution ordering: `code-review-agent` foreground → `codex(background)` +
    `phase-goals-agent(foreground)` concurrent → join.
  - Verdict write: main thread calls `codex_gate.extract_and_validate`, writes
    `phase-N-attempt-M-codex.json` (`agent:codex`, `backend:codex`) on success or
    `codex.raw.txt` on skip.
  - Aggregation: Step 9 replaced by `aggregate_verdicts` call (no hand-derived prose).
  - Conflict UX: `AskUserQuestion` on fail or codex-vs-subagent disagreement; no
    auto-revert.
  - Degrade: `gate_codex_skipped` event appended to `history.jsonl`; gate never blocks
    on Codex absence (proceeds on two in-house agents).
  - Background-join primary path + sequential-blind fallback documented.

### Changed

- `core/state/gate-verdict.schema.json` — optional `backend` field added (enum:
  `["codex", "subagent"]`); `additionalProperties` remains `false`; all existing
  schema-valid verdicts remain valid.

---

## [0.11.0] - 2026-05-21

Phase 11 — Friction Remediation & v0.x Pre-Release (Loops 042–046, 5 loops).
Gate pending at time of this entry.

### Changed (BREAKING)

- **`complexity:` field removed** from the todo schema and all loop files.
  Any external tooling that reads `complexity:` from todo YAML frontmatter
  must drop this field. The canonical todo field order is now
  `id / content / skill / agent / outcome / status / priority`.
- **Haiku tier dropped.** All worker invocations now use Sonnet. The
  `complexity: low` signal that previously triggered Haiku routing no longer
  exists. The Model Tiers table in CLAUDE.md no longer has a Haiku row.

### Added

- `core/constraints.json` — machine-readable source of truth for the
  zero-dependency import allow-set (S1).
- `platforms/python/ast_check.py` — stdlib-only AST import checker; exposes
  `load_allowed_imports()`, `check_file()`, and CLI mode via
  `python -m platforms.python.ast_check` (S1).
- `core/skills/schema-design/SKILL.md` — new skill stub for schema document
  authoring (S3).
- `core/skills/permission-config/SKILL.md` — new skill stub for hooks/settings
  and agent tool-set edits (S3).
- `docs/path-conventions.md` — canonical path map (source repo vs installed
  project); deprecated token list (`plans/`, `.claude/state/`, `/new-loop`) (S7).
- `docs/tool-friction-log.md` entries S1–S10 resolved (9 friction items closed).
- Worker preflight protocol: `ralph-loop-worker` emits `WARN` on unresolved
  skill declarations instead of halting (S4).
- `phase-goals-agent` `tools:` field widened to include `Write` so the agent
  can persist its own verdict; fallback CONTINGENCY block added to `/run-gate`
  documenting main-thread persist-on-behalf path if runtime tool propagation
  fails (S5).
- `/next-loop` Step 3a resume-detection: detects mid-loop worker death
  (loop-ready newer + dirty tree) and pauses for operator acknowledgment
  before spawning the next orchestrator (S8).
- `detect_mid_loop_death()` and `archive_cross_phase_state()` added to
  `platforms/python/state_manager.py`; 16 new regression tests (S8, S9).
- `ralph-orchestrator` stale-state cleanup: archives cross-phase `loop-ready.json`
  and `loop-complete.json` to `.advanced-plans/state/archive/` on startup (S9).
- `setup/claude-code/install.sh` and `install.ps1` idempotent: skip
  `.advanced-plans/` scaffold when data already exists; self-install mode creates
  symlinks/junctions so source edits surface immediately (S10).
- `CONTRIBUTING.md` with Dev-Mode section documenting self-install workflow (S10).
- `VERSION` file at repo root (`0.11.0`).

### Fixed

- CI workflow AST checker changed from inline Python to
  `python -m platforms.python.ast_check` module invocation (S1).
- `plan-subagent-identification` skill default changed from
  `agent: ralph-loop-worker` to `agent: NA`; Reserved Values note added (S6).
- Stale `agent: ralph-loop-worker` assignments on individual todos in
  `.advanced-plans/phases/` rewritten to `agent: NA` (S6).
- Migration-consistency audit: stale path directives (`plans/`, `.claude/state/`)
  rewritten to `.advanced-plans/` across command and agent files (S7).

---

## [0.10.0] - 2026-05-20

Phase 10 — `/phase-compact` Context-Compaction Reframe (Loops 037–041, 5 loops).
Gate PASSED attempt 1, both agents. Completed 2026-05-20.

### Added

- `context_meter.py` transparency report for compaction artefacts.
- Per-phase `handoff.md` resume digest schema (`docs/phase-handoff.schema.md`)
  and generation logic; `/phase-compact` now produces a hot `handoff.md` in
  addition to the locked `complete.md`.
- `PreCompact` hook: validates `handoff.md` freshness before every compaction.
- `## Compaction Instructions` block in `CLAUDE.md` steering all compactions
  toward the distilled-signal retention policy.
- `AskUserQuestion` consent step in `/phase-compact` so operators can review
  the handoff digest before proceeding.

### Changed

- `/phase-compact` reframed from terse-artefact writer to conversation-context
  compaction (Approach A). The `complete.md` cold artefact and both compaction
  schemas remain LOCKED and unchanged.

---

## [0.9.0] - 2026-05-19

Phase 9 — `.advanced-plans/` Restructure (Loops 032–036, 5 loops).
Gate PASSED attempt 2. Completed 2026-05-19.

### Added

- `.advanced-plans/` as the canonical planning data home, replacing `plans/`.
- `PLANNING.md` YAML frontmatter dashboard for cold-start orientation.
- `docs/path-conventions.md` predecessor: all command/agent files updated to
  reference `.advanced-plans/` paths.
- Phase 8 Loops 028–031 absorbed into this phase (sentinel ownership,
  progress-report deduplication, `decompose-phase` rename, disambiguation).

### Changed

- All state bus paths migrated from `.claude/state/` to `.advanced-plans/state/`.
- All gate-verdict paths migrated from `plans/gate-verdicts/` to
  `.advanced-plans/gate-verdicts/`.
- `/new-loop` renamed to `/decompose-phase` (command surface clarity).

---

## [0.8.0] - 2026-05-18

Phase 8 — Framework Consistency Remediation (Loop 027 only; Loops 028–031
absorbed into Phase 9). Partially completed.

### Fixed

- Hook and permissions hygiene: `gate-review-mode` sentinel path canonicalised;
  settings.json and hooks.json updated consistently.

---

## [0.7.0] - 2026-05-13

Phase 7 — `/phase-compact` Slash Command (Loops 023–026, 4 loops).
Gate PASSED attempt 1, both agents. Completed 2026-05-13.

### Added

- `/phase-compact` slash command implementing the cold/hot compaction workflow.
- `criteria_outcomes` and `phase_title` extended fields in
  `core/state/gate-verdict.schema.json`.
- Agent template documented for future gate agents.
- Phase 6 compacted end-to-end as the worked example.

---

## [0.6.0] - 2026-05-13

Phase 6 — Compaction Schema Audit & Lock (Loops 019–022, 4 loops).
Gate PASSED attempt 1, both agents. Completed 2026-05-13.

### Added

- `docs/phase-complete.schema.md` — cold compaction artefact schema; **LOCKED**.
- `docs/phase-manifest-entry.schema.md` — hot manifest entry schema; **LOCKED**.
- Verdict format audit confirming gate-verdict schema consistency.
- Phase 5 retrospective worked example as a compaction demonstration.

---

[0.18.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.18.0
[0.17.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.17.0
[0.16.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.16.0
[0.15.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.15.0
[0.14.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.14.0
[0.13.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.13.0
[0.12.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.12.0
[0.11.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.11.0
[0.10.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.10.0
[0.9.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.9.0
[0.8.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.8.0
[0.7.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.7.0
[0.6.0]: https://github.com/MungoHarvey/advanced-planning/releases/tag/v0.6.0
[Unreleased]: https://github.com/MungoHarvey/advanced-planning/compare/v0.18.0...HEAD
