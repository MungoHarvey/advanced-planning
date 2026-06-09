# Phase 14 Design — Install & Exercise Codex Gate + Self-Heal in Runtime

**Date:** 2026-06-09
**Status:** approved (brainstorming)
**Anchor:** 9465e55
**Target release:** v0.14.0
**Origin:** 2026-06-09 resume-review gap analysis + adversarial review of the Phase 14 draft plan

## Problem

The Phase 12 codex gate and Phase 13 self-heal are fully built and tested **in the framework
source** (`platforms/`, `core/`) but were never installed into the runtime this repo actually
executes when it gates itself. The framework cannot yet dogfood its own check-build-correct
recursion.

Confirmed gaps:

| Surface | Installed (`.claude/`) | Source (`platforms/`) |
|---|---|---|
| `commands/run-gate.md` | 6.8 KB, May 21 — 0 codex refs | 20.4 KB, Jun 8 — 92 codex refs |
| `commands/next-phase.md` | 13.0 KB, May 18 — 0 remediation refs | 26.9 KB, Jun 8 — 46 remediation refs |

## Adversarial findings and resolutions

The draft plan was red-teamed. Five findings; two were fatal-if-true and are resolved
empirically before any loop is committed:

- **F1 — Is the install target correct? RESOLVED (yes, project-level).** The `/run-gate` that
  executed this session carried `Loop 043` + `CONTINGENCY` markers present **only** in the
  project `.claude/commands/run-gate.md` (6801 bytes). The user-level `~/.claude/commands/`
  copy (Apr 3) has neither. So the **project** `.claude/commands/` is the live lever; user-level
  copies stay out of scope. The `userSettings:` label seen in the harness was a red herring;
  content is decisive.
- **F2 — Does codex-reviewer need packaging? RESOLVED (no).** The refreshed run-gate references
  `core/agents/codex-reviewer.md` *by that path* (run-gate.md:169/187/196/508) and never spawns
  it via the Agent tool — it is a contract doc read by the subprocess. That path exists in this
  repo, so it resolves as-is. We copy it into `.claude/agents/` for parity (the installer already
  sources `core/agents/*.md` — `install.sh:132`) but create **no** `platforms/` duplicate.
- **F3 — How to exercise self-heal safely?** Addressed by the two-track proof strategy below
  (sandboxed tests + a worktree-isolated induced fail).
- **F4 — How to make an install-phase's success gate-verifiable?** Addressed by encoding the
  exercises as pytest tests (machine-checkable) and capturing live artefacts (verdict files,
  history events) the gate agents can inspect.
- **F5 — minor.** v0.14.0 bumps for a phase that changes no shipped *library* code; accepted per
  the minor-version-per-phase convention. Byte-identity is a valid criterion because install is
  plain `cp -r` with no token substitution (`install.sh:79`).

Already satisfied (no action): `codex-cli 0.124.0` on PATH; `codex_gate.py` / `remediate.py` /
`remediation_controller.py` / `versioning.py` resolve via `python -m platforms.python.*` from
repo root; `gate-verdict.schema.json` carries the `backend` field.

## Design: two-track proof strategy

The core insight: **prove the mechanisms in isolation with repeatable tests, then prove they
work end-to-end by running them for real.**

### Codex gate
- **Automated:** capture a real `codex` stdout sample as a fixture; assert
  `codex_gate.extract_and_validate` produces a schema-valid verdict; assert the graceful-degrade
  path (codex unavailable → in-house agents proceed, `gate_codex_skipped` appended to
  `history.jsonl`, no `codex.json` written).
- **Live (guaranteed):** once run-gate is refreshed, codex fires automatically when Phase 14's
  own gate is reviewed. Phase 14's `gate-verdicts/` will therefore include a `backend: codex`
  verdict for `phase-14-attempt-1` — self-evidencing.

### Self-heal
- **Automated:** a sandboxed synthetic-fail integration test drives `remediation_controller`
  triage → an allowlist-breach escalation, complementing Phase 13's existing unit/trace tests.
- **Live (deliberately induced, reverted):** on a throwaway git **worktree**, stage a controlled
  unmet criterion, run the refreshed `/next-phase --auto`, and watch the bounded
  triage→safety→fix→re-gate loop remediate + re-gate live. Capture the transcript +
  `gate_remediation` / `passed_after_remediation` history events, then **discard the worktree**
  so `main` is never touched. Revert is "delete the worktree," not "undo commits."

## Loop breakdown (4 loops + 1 phase-level criterion)

| Loop | Name | Type | Key outputs |
|---|---|---|---|
| 055 | Runtime Install | Implementation | Refresh `.claude/commands/{run-gate,next-phase}.md` from source (byte-identical); copy `core/agents/codex-reviewer.md` → `.claude/agents/`; verify path resolves + codex/remediation refs present; CONTRIBUTING.md drift-note (commands aren't symlinked → documented re-sync command) |
| 056 | Codex Gate Proof | Verification | Real codex stdout fixture; `test_codex_gate_live.py` (extract/validate + degrade path); codex preflight smoke (`codex --version`/auth) |
| 057 | Self-Heal Proof | Verification | Sandboxed synthetic-fail integration test (triage → allowlist-breach escalation); runtime reachability smoke for `remediate` / `remediation_controller` |
| 058 | Witnessed Exercise + v0.14.0 | Verification + Release | Worktree-isolated induced gate fail → live remediation + re-gate captured (transcript + history events) → worktree discarded, main clean; VERSION 0.14.0 + CHANGELOG `[0.14.0]` + CLAUDE.md Phase 14 decision-log entry; full pytest + AST NONE; LOCKED files byte-unchanged |

**Phase-level success criterion (codex live run):** Phase 14's own gate review (at the phase
boundary, via `/run-gate` or `/next-phase`) is conducted with the refreshed codex-wired run-gate,
and a `backend: codex` verdict is written for `phase-14-attempt-1`.

## Scope boundaries

**In:** project `.claude/` runtime install; automated tests for both mechanisms; one
worktree-isolated witnessed self-heal run; codex live participation in Phase 14's own gate;
CONTRIBUTING drift note; v0.14.0 release.

**Out:** refreshing user-level `~/.claude/commands/` (affects all projects); any change to
`codex_gate.py` / `remediate.py` / `remediation_controller.py` *logic* (install + exercise only;
blocking bugs found get a minimal scoped fix and are logged); new gate features (structured
findings[].location, passed_after_remediation enforcement — remain Phase 13 deferred); a general
installer refactor.

## Risks

| Risk | Mitigation |
|---|---|
| Induced-fail exercise mutates main | Runs in a discarded git worktree; never commits to main |
| Refreshed 20 KB command body has runtime issues never caught in document review | Loops 056/057 smoke-test every `python -m platforms.python.*` call the commands make; loop 058 is the first real execution, isolated |
| Codex CLI output drifts from `codex_gate` expectations | Validate against a real run; degrade path is the built-in safety net |
| Runtime silently drifts from source again | CONTRIBUTING drift-note + a gate criterion checking byte-identity |
| Worktree exercise leaves orphaned state | Explicit discard step + post-exercise `git worktree list` / status check in the loop |

## Open questions

None — F1/F2 resolved empirically; F3/F4 resolved by the two-track strategy; proof standard
(tests + witnessed induced fail) chosen by the user.
