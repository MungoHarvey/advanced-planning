# Design: `/phase-compact` reframed as conversation-context compaction

**Status:** DESIGN — 2026-05-19
**Supersedes:** `.advanced-plans/specs/2026-05-19-phase-compact-context-reframe.md`
(folded in; that file becomes a stub pointing here)
**Approach:** A — two-tier (resume digest + unchanged terse git-index)
**Affects:** `platforms/claude-code/commands/phase-compact.md`, a new `PreCompact`
hook, `CLAUDE.md` (new `## Compaction Instructions` section + decision log),
`platforms/python/context_meter.py` (extend with breakdown)
**Does NOT affect:** `docs/phase-complete.schema.md`,
`docs/phase-manifest-entry.schema.md` (both remain LOCKED, unchanged)

## Problem

Long multi-phase programmes burn context. The loop tier already compresses via
`loop-complete.json`'s terse `done/failed/needed` handoff — the framework's
single most important compression mechanism. The phase tier has only
`complete.md`, which was designed as a **git-navigation index** (terse pointers,
premised on *re-reading git when detail is needed*). Re-reading is exactly the
cost we want to eliminate: a model resuming after a phase should know what was
done, why, and the outcome without re-reading files and without context bloat.

Evidence (measured from this programme's transcript, 1651 records, 3 prior
auto-compactions): **66% of context is raw tool I/O** (verbatim file Reads +
bash output, all already on disk), **18% is injected skill/command/tool bodies**
(reload on demand), carried compaction summaries are already lean (~4%). The
fat is recoverable detail, not decisions.

## Goals

- A model can resume on-task after a phase from a single small digest — no
  re-reading, no bloat.
- `/phase-compact` transparently reports *what* is using context, *how*, and
  *what the proposed compaction achieves*.
- Every compaction — manual `/compact` AND the non-deterministic auto-compact —
  follows one tuned retention policy.
- All detail remains accessible/findable (git + terse index), just not in
  context.

## Non-goals

- Programmatic/automatic invocation of `/compact` — **proven impossible**
  (no `SlashCommand` tool; `PreCompact` is reactive/block-only; SDK has no
  compaction API; custom commands cannot emit an executing `/compact`).
- `/clear`-based flow — explicitly rejected; `/clear` is for switching to an
  entirely different task, never the programme flow.
- Unlocking or expanding `complete.md` / the manifest schema.

## The `complete.md` verdict

Investigated and decided, not assumed. `complete.md` (per
`docs/PHASE-COMPACTION-PLAN.md`) is the git-navigation index: "pointers only,
never a substitute for git diffs", consumed loosely by `run-closeout` and
`progress-report`; its planned on-demand loader `/load-phase-context` was never
built. It is **still useful and is kept unchanged** as the
findable-but-not-in-context layer (deep detail stays in git, addressable by the
SHAs it records). It is **insufficient alone** for resume-without-re-reading —
hence one focused addition (the digest), no schema disturbed.

## Architecture

Five elements, file-boundary interfaces only.

1. **`context_meter.py`** (exists; extend) — at phase end reports measured
   occupancy plus the segment / content-type / activity breakdown. Drives the
   transparency report and the achieved-saving projection.
2. **Phase handoff digest** — new `.advanced-plans/phases/phase-N/handoff.md`.
   The resume seed. Phase-level analogue of the loop `done/failed/needed`
   handoff. Hard token ceiling.
3. **Unchanged `complete.md`** — LOCKED terse git-index, written by existing
   steps 1–12.
4. **`## Compaction Instructions` block in CLAUDE.md** — always-loaded tuned
   retention policy. Steers *every* compaction (manual + auto-threshold),
   because CLAUDE.md is always in context. Maintained (rewritten) by
   `/phase-compact` to point at the current digest.
5. **`PreCompact` hook** — cannot trigger compaction; fires before any
   compaction (manual or auto). It does **not** generate a digest (a digest is
   a phase-*end* artefact and compaction may fire mid-phase). It only (a)
   validates that the most recently written `handoff.md` still satisfies its
   schema/ceiling, and (b) emits a short stderr/context note naming that
   digest + the CLAUDE.md `## Compaction Instructions` block as the retention
   target, so even a mid-phase auto-compact is steered toward the last good
   seed plus the persistent policy. If no `handoff.md` exists yet (pre-first
   gate), it no-ops.

The digest is what the retention policy (4) names to keep; the hook (5)
guarantees it is current; `complete.md` (3) + git remain the recoverable detail.

## `handoff.md` schema

```markdown
---
phase: N
title: "<phase title>"
status: passed | failed_vM
created: <ISO8601>
complete_ref: .advanced-plans/phases/phase-N/complete.md
plan_ref: .advanced-plans/phases/phase-N/plan.md
loops_ref: .advanced-plans/phases/phase-N/loops.md
gate_verdict_refs: [.advanced-plans/gate-verdicts/phase-N-attempt-M-*.json]
token_ceiling: 1500
---

## What was done & why
- <one line per material outcome, including the rationale — the "why">

## Outcomes
- <observable end-state per goal; cites SHA or complete.md pointer>

## Errors & issues encountered
- <mandatory section: what went wrong, how resolved, or still open;
  "(none)" only if genuinely clean>

## Files touched (pointers, not contents)
- read:  `path` — why it mattered
- edited: `path` — what changed (one line)

## Gate review
- <one-paragraph verdict summary> -> full verdict: <gate_verdict_ref>

## Skills & methods used
- `skill/method` — what it was used for

## Resume pointers
- Plans: <plan_ref / loops_ref> · Spec: <spec path> · Next: <next action>
```

Hard rules: pointers + one-liners only, **never pasted file contents**;
`token_ceiling` enforced (build fails if exceeded — no silent bloat); the
errors/issues section is mandatory.

## Reframed `/phase-compact` flow

1. **Write `complete.md`** — existing steps 1–12, unchanged.
2. **Write `handoff.md`** — schema above; validate ceiling.
3. **Transparency report** — run `context_meter.py`; present in plain language:
   - *What's using context*: live occupancy (e.g. `~141k/200k, 70%`) +
     segment/content-type/activity breakdown.
   - *How*: e.g. "66% raw tool I/O already on disk; 18% skill/command bodies
     that reload on demand."
   - *What compaction achieves*: projected post-compact occupancy; the resume
     seed becomes `handoff.md` (~1.5k) + dashboard — on-task, no re-reading.
4. **Maintain CLAUDE.md `## Compaction Instructions`** — rewrite the block with
   the tuned retention policy pointing at this phase's `handoff.md`.
5. **Consent gate** — `AskUserQuestion`: proceed with compaction now?
   - *Yes*: present the ready `/compact <prompt>` line for the user to run
     (one keystroke); confirm digest written/validated (safe-to-compact
     precondition met).
   - *No*: leave intact; prompt + CLAUDE.md block remain available.
6. **Closing summary** — artefacts written+validated; context NOT yet compacted
   (the command never self-compacts); running the line is the user's step.

## Tuned `/compact` prompt template

```
/compact Retain verbatim: .advanced-plans/phases/phase-N/handoff.md (the
validated phase resume digest), .advanced-plans/PLANNING.md frontmatter, and
any open cross-phase decisions/threads. Preserve all DECISIONS and their
rationale. Discard: verbatim file-Read contents and bash/tool_result output
(recoverable from disk + git); injected skill/command/tool-schema bodies;
gate-review agent-by-agent back-and-forth (final verdicts are on disk);
prior compaction summaries now superseded by handoff.md; resolved remediation
detail. Goal: keep the distilled signal, shed the raw I/O that dominates
context.
```

The same text is what lives (generalised, phase-pointer-substituted) in
CLAUDE.md `## Compaction Instructions`, so auto-compact obeys it too.

## Error & edge handling

- Digest over `token_ceiling` → build fails listing offending sections (forces
  tighter pointers; never silent bloat).
- Gate-fail phase → digest still written with `status: failed_vM`; the
  errors/issues section is the point on a fail.
- `context_meter` cannot find transcript → report says "occupancy unavailable",
  flow still emits prompt + maintains CLAUDE.md block (degrade, don't block).
- Order invariant: artefacts written + validated **before** any compaction
  guidance. Command never self-compacts.
- `PreCompact` hook failure → must not block compaction; on error it no-ops and
  logs, leaving the last good `handoff.md` as the seed.
- Compaction fires mid-phase (before any gate) → no `handoff.md` exists; the
  hook no-ops and the CLAUDE.md `## Compaction Instructions` block alone steers
  retention. Acceptable degraded mode (loop-level handoffs still on disk).

## Impact / migration

- `complete.md` and both LOCKED schemas: untouched.
- `run-closeout` / `progress-report`: unaffected (still glob `complete.md`);
  may optionally also surface `handoff.md` later — out of scope here.
- New files: `handoff.md` per phase; `PreCompact` hook entry in
  `platforms/claude-code/hooks/hooks.json` + `settings.json`; CLAUDE.md gains
  `## Compaction Instructions` + a decision-log line.
- Backfill of `handoff.md` for historical phases (1–9): out of scope; the
  digest applies from next phase onward.

## Testing

- `context_meter.py`: unit tests for occupancy math, breakdown buckets,
  transcript auto-detect, missing-transcript degrade (pytest, zero-dep).
- Digest ceiling enforcement: a fixture digest over ceiling fails the build.
- Gate-fail path: produces `status: failed_vM` with non-empty issues section.
- `PreCompact` hook: dry-run that it refreshes `handoff.md` and never exits
  non-zero in a way that blocks compaction.
- Manual end-to-end: run reframed `/phase-compact` on a completed phase, verify
  transparency report numbers against `context_meter`, run the emitted
  `/compact`, confirm the resumed context contains the digest and not the raw
  I/O.

## CLAUDE.md decision-log entry (to add on implementation)

> `/phase-compact` reframed (2026-05-19) from terse-artefact writer to
> conversation-context compaction. Adds per-phase `handoff.md` resume digest
> (Approach A), a transparency report via `context_meter.py`, a persistent
> `## Compaction Instructions` block steering all compactions, and a
> `PreCompact` freshness hook. `complete.md` and both compaction schemas remain
> LOCKED and unchanged. Programmatic `/compact` invocation confirmed
> impossible; consent + ready-to-run handoff is the maximum. `/clear`-based
> flow rejected.
