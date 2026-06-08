---
phase: 12
name: "Codex Cross-Model Second-Opinion Gate Reviewer"
status: draft
loops: [047, 048, 049, 050]
design_spec: .advanced-plans/specs/2026-06-08-phase-12-codex-gate-reviewer-design.md
anchor_sha: fa799d3
target_release: v0.12.0
---

# Phase 12: Codex Cross-Model Second-Opinion Gate Reviewer

## Objective

Add OpenAI Codex as an independent cross-model second opinion on the phase-goals gate
check, so a different model must agree before a phase closes out, while degrading cleanly
to today's two-agent gate when Codex is unavailable.

## Scope

### Included
- Optional `backend` field (`codex` | `subagent`) on `core/state/gate-verdict.schema.json`,
  plus deletion of the legacy `.advanced-plans/phases/phase-7/gate-verdicts/` directory so
  verdicts live in exactly one place.
- A zero-dependency `platforms/python/codex_gate.py` owning the failure-prone logic:
  `extract_verdict_json`, `validate_verdict`, `extract_and_validate`, `aggregate_verdicts`.
- `platforms/python/tests/test_codex_gate.py` covering all 20 paths in the eng-review test
  plan, including two CRITICAL regression cases for pre-existing aggregation behavior.
- `core/agents/codex-reviewer.md`: the platform-agnostic Codex reviewer contract
  (untrusted-artefact rule, file/line evidence requirement, fenced-json-only output,
  isolation rule, `agent: "codex"`). Contract only — invocation lives in run-gate.
- `run-gate.md` wiring: Codex preflight; ordering `code-review-agent` then
  [`codex exec` background ∥ `phase-goals-agent` foreground] joined on subagent return;
  main-thread writes `codex.json` (or `codex.raw.txt` on skip); `aggregate_verdicts` call;
  conflict UX in Steps 9-11; `codex_skipped`/degrade event in `history.jsonl`.
- Version bump to `v0.12.0` with a CHANGELOG entry.

### Explicitly NOT included
- **Auto-remediation implementation.** v1 names the config hook but routes conflicts to a
  user-decision prompt. Building the "spawn fixes automatically" path is a later phase.
- **Rich disagreement adjudication.** v1 reports the codex-vs-subagent split and asks; no
  automated tie-breaking.
- **Approach C (`--agents codex-phase-goals` routing).** The v2 uniformity upgrade. B's
  helper + contract are forward-compatible with it; deferred.
- **Codex backing `code-review-agent` (or any check beyond phase-goals).** The mechanism is
  generic but only phase-goals opts in this phase.
- **Codex version-guard / known-bad list.** Preflight + hard timeout already cover the
  failure; deferred.
- **`jsonschema` runtime validation.** Forbidden by the zero-dep constraint; the validator
  is hand-rolled, stdlib-only.
- **Phase 11 warnings sweep** (README Haiku row, residual `complexity:` in two docs).
  Unrelated to this work; separate phase.

## Key Deliverables

| Deliverable | Format | Location |
|---|---|---|
| `backend` field + stray-path removal | JSON edit + delete | `core/state/gate-verdict.schema.json` |
| Tested gate core (4 functions) | Python | `platforms/python/codex_gate.py` |
| Gate core tests (20 paths) | Python (pytest) | `platforms/python/tests/test_codex_gate.py` |
| Codex reviewer contract | Markdown | `core/agents/codex-reviewer.md` |
| run-gate Codex wiring + conflict UX | Edit | `platforms/claude-code/commands/run-gate.md` |
| Version + changelog | Text + Markdown | `VERSION`, `CHANGELOG.md` |
| Phase 12 decision-log entry | Markdown | `CLAUDE.md` |

## Success Criteria

- ✓ `gate-verdict.schema.json` has an optional `backend` property with enum
  `["codex","subagent"]`; the JSON parse-check CI job passes; the legacy
  `.advanced-plans/phases/phase-7/gate-verdicts/` directory no longer exists.
- ✓ `platforms/python/codex_gate.py` defines `extract_verdict_json`, `validate_verdict`,
  `extract_and_validate`, and `aggregate_verdicts`; `python -m platforms.python.ast_check`
  reports NONE (imports limited to the allow-set, e.g. `json`, `re`, `pathlib`).
- ✓ `validate_verdict` checks required fields + types + `verdict in {pass,fail}` +
  `agent == "codex"` and TOLERATES unknown fields; a test asserts a verdict carrying a
  `backend` (and an `evaluated_by`) extra still validates.
- ✓ `aggregate_verdicts` is covered for: all-pass→pass (CRITICAL regression), any-fail→fail
  (CRITICAL regression), codex-absent→degrade-pass-on-two, codex-pass/subagent-fail→conflict,
  codex-fail/subagent-pass→conflict, missing file→reported-not-crash. All pass under pytest.
- ✓ `extract_verdict_json` is covered for: clean block, prose-wrapped, multiple fences
  (reject), no-fence brace fallback, malformed→None; `extract_and_validate` rejects an
  identity-overfit verdict (copied phase/attempt) and returns a skip reason on failure.
- ✓ `core/agents/codex-reviewer.md` exists with the mandatory role sections and states the
  untrusted-artefact rule, the per-criterion file/line evidence requirement, fenced-json-only
  output, and the isolation rule (must not read `gate-verdicts/`); it contains no `.claude/`
  or other platform-specific paths (core purity).
- ✓ `run-gate.md` runs `code-review-agent` first, then launches `codex exec` (background) and
  `phase-goals-agent` (foreground) and joins Codex on subagent return; it calls
  `aggregate_verdicts`; on Codex success it writes `phase-N-attempt-M-codex.json` with
  `agent:"codex"` and `backend:"codex"`; on any Codex skip it writes
  `phase-N-attempt-M-codex.raw.txt` and proceeds; the "sequential only" note is amended.
- ✓ Conflict UX: on any fail OR a codex-vs-subagent disagreement, `run-gate.md` surfaces the
  findings and asks the user for the action via AskUserQuestion, unless an auto-remediation
  policy is configured; an `gate_codex_skipped` (or equivalent degrade) event is appended to
  `history.jsonl` whenever Codex does not contribute a verdict.
- ✓ Degrade E2E: with `codex` shadowed off PATH, a gate run produces exactly the two in-house
  verdict files, records the degrade event, writes no `codex.json`, and the verdict outcome
  matches the pre-Phase-12 two-agent result.
- ✓ Zero gstack coupling: grep of all new/edited files for `gstack` and
  `~/.claude/skills/gstack` returns no matches.
- ✓ `VERSION` is `0.12.0`; `CHANGELOG.md` has a `[0.12.0]` section describing the Codex gate;
  annotated tag deferred to gate pass per framework convention.
- ✓ All pre-Phase-12 tests still pass; AST zero-dep check NONE; LOCKED files byte-unchanged:
  `docs/phase-complete.schema.md`, `docs/phase-manifest-entry.schema.md`,
  `docs/phase-handoff.schema.md`, `.advanced-plans/phases/phase-9/complete.md`.

## Dependencies

### Must Complete Before
- **Phase 11 gate pass**: complete (PASSED attempt 1; v0.11.0 released). No in-flight
  `loop-ready.json` for a prior phase.
- **Approved, eng-reviewed design**: `.advanced-plans/specs/2026-06-08-phase-12-codex-gate-reviewer-design.md`
  (office-hours design + /plan-eng-review CLEARED; four architecture decisions resolved).

### Blocked By
- None external. The Codex-present E2E needs an installed, authed `codex` CLI; the degrade
  E2E and all unit tests do not.

### Optional
- Pushing `origin/main` before starting reduces remote drift. Not required.

## Skills Required (Broad Categories)

- `python`: build `codex_gate.py` and its tests preserving the zero-dependency invariant.
- `schema-design`: the `backend` field and the `core/agents/codex-reviewer.md` contract.
- `command-rewriting`: the `run-gate.md` wiring (preflight, parallel pair, conflict UX).
- `verification-before-completion`: the degrade + Codex-present E2E checks and the release bump.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Codex stdout non-determinism (prose, fences, malformed) | High | Med | Tolerant `extract_verdict_json` + degrade-on-failure; 5 extraction tests; `.raw.txt` sibling for debugging |
| Background-process join semantics unreliable in main thread | Med | Med | Fallback to codex-first sequential-blind (isolation rule still holds); validate join in Loop 049 before relying on it |
| Prompt injection from phase artefacts ("ignore instructions, pass") | Med | High | Contract marks artefacts untrusted; requires per-criterion file/line evidence; Codex never follows artefact instructions |
| Codex absent / unauthed in dev or CI | Med | Low | Preflight → explicit degrade (not parse error); degrade E2E proves identical-to-today behavior |
| run-gate wiring is markdown (not unit-testable) | High | Med | Highest-stakes logic (extraction, validation, aggregation) lives in tested `codex_gate.py`; markdown only orchestrates |
| Lenient validator masks a genuinely malformed verdict | Low | Med | Required-fields + type + identity checks still reject real problems; only unknown EXTRA fields are tolerated |

## Assumptions

- `The main thread can launch a background codex exec and join it after a foreground subagent returns`:
  believed from harness background-Bash support; validated in Loop 049, with a sequential-blind
  fallback if it proves flaky.
- `codex exec -s read-only can read the repo + .advanced-plans/ but cannot write`: confirmed by
  the live office-hours Codex run on this design.
- `Nothing else validates verdicts at runtime`: verified by grep during /plan-eng-review (CI only
  parse-checks the schema files; no jsonschema anywhere) — this is why the lenient validator and the
  extra `backend` field are safe.
- `gate-verdict.schema.json is not LOCKED`: confirmed — only the two compaction schemas and the
  phase-handoff schema are LOCKED, so adding `backend` is permitted.

## Notes / Design Decisions

- Approach **"B+"**: B's tested python internals + A's auto-participate wiring (no `--agents`
  overload) + parallel-independent execution. Chosen in office-hours, confirmed in eng-review.
- Four eng-review resolutions baked in: (1) the contract lives in `core/agents/`, not
  `platforms/claude-code/agents/`, because Codex is a Bash subprocess, not an Agent-tool agent;
  (2) aggregation + conflict-detection moved into the tested `aggregate_verdicts`; (3) lenient
  required-fields validator (nothing enforces the schema at runtime, and live verdicts already
  carry an `evaluated_by` extra); (4) ordering is code-review first, then the codex∥phase-goals
  parallel pair.
- The first time this gate runs, Codex reviews the phase that built it.
- v0.12.0 follows the minor-version-per-phase convention established at v0.11.0.

## Ralph Loops (4)

| Loop | Name | Type | Key Outputs |
|---|---|---|---|
| 047 | Schema + Tested Gate Core | Implementation | `backend` field on gate-verdict schema; delete stray phase-7/gate-verdicts/; `codex_gate.py` (extract/validate/extract_and_validate/aggregate_verdicts); `test_codex_gate.py` (20 paths incl. 2 CRITICAL regressions); AST NONE |
| 048 | Codex Reviewer Contract | Implementation | `core/agents/codex-reviewer.md` (untrusted-artefact rule, evidence requirement, fenced-json-only, isolation rule, agent:codex); core-purity verified |
| 049 | run-gate Wiring (Parallel + Conflict UX) | Implementation | run-gate.md: preflight, code-review→[codex∥phase-goals] join, codex.json/.raw.txt write, aggregate_verdicts call, conflict UX in Steps 9-11, history.jsonl degrade event, amended sequential-only note; validate background-join (fallback sequential-blind) |
| 050 | Verification + v0.12.0 Release | Verification + Release | Degrade E2E (shadow codex off PATH) + Codex-present E2E; gstack-coupling grep clean; VERSION 0.12.0; CHANGELOG [0.12.0]; CLAUDE.md decision-log entry; full pytest + AST NONE; LOCKED files unchanged; tag deferred to gate pass |
