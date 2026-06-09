# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

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

[0.12.0]: https://github.com/advanced-planning/advanced-planning/releases/tag/v0.12.0
[0.11.0]: https://github.com/advanced-planning/advanced-planning/releases/tag/v0.11.0
[0.10.0]: https://github.com/advanced-planning/advanced-planning/releases/tag/v0.10.0
[0.9.0]: https://github.com/advanced-planning/advanced-planning/releases/tag/v0.9.0
[0.8.0]: https://github.com/advanced-planning/advanced-planning/releases/tag/v0.8.0
[0.7.0]: https://github.com/advanced-planning/advanced-planning/releases/tag/v0.7.0
[0.6.0]: https://github.com/advanced-planning/advanced-planning/releases/tag/v0.6.0
[Unreleased]: https://github.com/advanced-planning/advanced-planning/compare/v0.12.0...HEAD
