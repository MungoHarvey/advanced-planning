# Context Monitor — Lightweight Compaction Guidance

> A minimal, advisory mechanism that surfaces context-window pressure to the user at phase-gate boundaries and recommends a proportional `/compact` invocation. Deliberately scoped as guidance, not automation.

## 1. Problem

Long programmes accumulate context faster than users notice. By the time `/compact` becomes urgent, work has already been degraded by token pressure (worse reasoning, truncated reads, missed instructions). Users have no in-workflow signal telling them how full their window is until Claude Code's own auto-compact triggers near 95% — too late to be deliberate about what gets dropped.

We do **not** want to solve compaction itself. Anthropic and Claude Code will keep iterating on `/compact`, context-aware models, and 1M windows. Our job is narrower: **measure pressure, surface it at natural decision points, and recommend a proportional response.**

## 2. Scope

In:

- A pressure gauge that fires after each gate pass and prints a one-line banner.
- Five named compaction tiers, each with a concrete prompt the user can copy into `/compact <instructions>` (or that `/next-phase` can render for them).
- Integration into `/next-phase` so the recommendation appears as part of the existing gate-pass flow.

Out:

- Durable `phase-N-complete.md` artefacts (deferred — see PHASE-COMPACTION-PLAN.md if we ever want them).
- Automatic compaction execution. The user always confirms.
- Mid-phase / per-loop monitoring. Gate boundaries only, for now.
- Raw token counts in the user-facing banner. Percentages only — keeps the signal stable across 200k and 1M users and avoids spreading model-specific numbers through the codebase.
- A standalone `/context-check` slash command. Possible v2 follow-up.

## 3. Mechanism

**Specialised `context-agent` spawned at phase boundary.** Mirrors the existing two-agent pattern: `/next-phase` (running on the main thread, after a gate pass) spawns a single `context-agent` whose sole responsibility is reporting on context pressure and proposing a compaction prompt. The agent writes its findings to a small state file and exits. The main thread reads the file and surfaces the recommendation to the user.

**Two targeted skills, injected per the framework's existing pattern:**

1. `context-usage` — load → read the session transcript → compute window-fill percent and tier → unload.
2. `compaction-prompt` — load → take a tier name → return the literal `/compact <instructions>` prompt → unload.

These are kept separate deliberately. `context-usage` is pure measurement (reusable by a future `/loop-status`-style command). `compaction-prompt` is pure tier-mapping (reusable by a manual `/context-check` command without spawning the agent at all).

**Transcript path discovery via a tiny passive hook.** Claude Code exposes the active session's `transcript_path` to hook scripts but not to slash commands or spawned subagents. To bridge that gap we add one passive hook entry to the existing `platforms/claude-code/hooks/hooks.json` (which already contains SubagentStart, SubagentStop, and PreToolUse hooks):

```jsonc
"SessionStart": [
  { "matcher": "*",
    "hooks": [{ "type": "command",
      "command": "echo \"${CLAUDE_TRANSCRIPT_PATH}\" > .claude/state/transcript-path.txt" }]}
]
```

Both `/next-phase` and `context-agent` read `.claude/state/transcript-path.txt` to locate the active transcript. Single source of truth, no slash-command shell-glob hackery, no untested env-var propagation assumptions.

**Token counting via transcript.** Claude Code records every session as a JSONL log; each assistant turn includes a `usage` block. The agent reads the file, walks lines in reverse, and finds the most recent assistant turn carrying a `usage` block. **Tokens used** for that snapshot:

```
tokens_used = input_tokens
            + cache_read_input_tokens
            + cache_creation_input_tokens
            + output_tokens_of_latest_turn
```

Including the latest turn's `output_tokens` corrects for the ~1–2% gap that exists immediately after a turn before the next request bakes those output tokens into its prompt.

**Reading discipline.** The transcript is appended-to live by Claude Code. The agent must:

- Skip the very last line if it fails to parse as JSON (a turn currently being flushed).
- Accept that the reported usage may lag by one turn if the gate just finished mid-flush; for an advisory gauge this is fine.
- Read only the tail (last ~100 KB) of the file for performance; older turns are irrelevant.

**Trigger: `/next-phase` invokes the agent inline.** No new gate-time hook needed (which would have ordering issues with gate-verdict writes and the `gate-review-mode` sentinel). The existing `/next-phase` command spawns `context-agent` as its final step after a gate pass, waits for the state file, then appends the banner + recommended prompt to the user-facing report.

**Graceful failure.** If `context-agent` errors for any reason (transcript missing, skill load failure, state file write fails, agent times out), `/next-phase` logs the failure to `.claude/logs/execution.log` and continues. The gauge is advisory; its absence must never block phase advancement.

## 4. Tiers

Window-fill thresholds and the matching guidance. Boundaries are **inclusive on the low end, exclusive on the high end** (i.e., exactly 25% lands in `Light`, not `Tidy`):

| Tier        | Range          | Banner                                    | Action                                                                                                                                                                                                                                                                          |
|-------------|----------------|-------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **None**    | `[0%, 10%)`    | `[ctx 7% — healthy]`                      | Nothing. Carry on.                                                                                                                                                                                                                                                              |
| **Tidy**    | `[10%, 25%)`   | `[ctx 18% — light tidy suggested]`        | Reason: early signs of bloat from completed loops. Custom instructions: drop agent tool-call outputs, gate-verdict JSON dumps, and transient file reads from earlier loops in this phase. Keep all user messages, decisions, written artefacts, and the current phase plan.     |
| **Light**   | `[25%, 50%)`   | `[ctx 34% — light compaction suggested]`  | Tier-Tidy actions, **plus**: collapse completed loop transcripts to their `done / failed / needed` handoff line. Keep the current phase's loops verbatim.                                                                                                                       |
| **Strong**  | `[50%, 75%)`   | `[ctx 61% — stronger compaction needed]`  | Tier-Light actions, **plus**: drop phases older than the previous one entirely. They survive in `plans/` on disk and in `history.jsonl`. Keep current + previous phase loops only.                                                                                              |
| **Urgent**  | `[75%, 100%]`  | `[ctx 82% — IMMEDIATE compaction]`        | Recommend `/clear` and reload only `CLAUDE.md` + `PLANS-INDEX.md` + the current phase plan. Anything else must be explicitly re-read from disk when needed.                                                                                                                     |

The "Action" column is the literal text passed to `/compact <instructions>`. The user is always in the loop — the monitor never invokes `/compact` itself.

## 5. Components

Built in dependency order. Six small additions, in framework-idiomatic locations:

1. **`core/skills/context-usage/SKILL.md`** — skill that:
   - Reads `.claude/state/transcript-path.txt` to find the active transcript JSONL.
   - Tail-reads the file (last ~100 KB), walks lines in reverse, finds the most recent assistant turn with a `usage` block. Skips malformed last line silently.
   - Computes tokens used per the formula in §3.
   - **Window-size detection (ordered):**
     1. **`CONTEXT_WINDOW` env var** (or explicit agent argument) — wins unconditionally. Documented escape hatch.
     2. **Observed-token inference** — scan all turns in this session's transcript. If any turn's `input_tokens + cache_read_input_tokens + cache_creation_input_tokens` exceeded **200,000**, the window must be 1M (otherwise the request would have been rejected). Record `window_source: "inferred-1m"`.
     3. **Model-table lookup** — match the `model` field on the latest assistant turn against a small built-in table (Opus 4.x = 200k, Sonnet 4.x = 200k, Haiku 4.x = 200k as of writing). Record `window_source: "model-table"`. Unknown model falls through to step 4.
     4. **Fallback** — assume 200k and emit a warning to `.claude/logs/execution.log`. Record `window_source: "fallback"`. This is the only case where the reported percent could be materially wrong; the warning makes it diagnosable.
   - The order is deliberate: observed tokens are ground truth (a 250k turn definitively means a 1M window), model lookup is a reasonable guess, fallback is a last resort. v1 ships with the model table containing only currently-known 200k models, so inference does the heavy lifting for 1M users without us needing to track beta-header changes.
   - **Reporting policy:** the percent is the only number that reaches the user-facing banner. Raw `tokens_used` and `window_size` are recorded in the state file for debugging but never rendered in the banner.
   - **Output:** `{ "tokens_used": 68421, "window_size": 200000, "percent": 34, "tier": "Light", "model": "claude-opus-4-7", "window_source": "model-table" }`. The `window_source` field is one of `env-override` / `inferred-1m` / `model-table` / `fallback`.

2. **`core/skills/compaction-prompt/SKILL.md`** — pure mapping. Input: tier name. Output: the literal `/compact <instructions>` prompt for that tier from the §4 table. No I/O, no state, no measurement. Trivial to unit-test.

3. **`core/agents/context-agent.md`** — agent definition.
   - **Tool allowlist (tight):** `Read` (scoped to the transcript path and skill files), `Write` (scoped to `.claude/state/context-pressure.json`). No `Bash`, no `Glob`, no `Grep`, no exploratory tools.
   - **Lifecycle:** load `context-usage` skill → run measurement → unload → load `compaction-prompt` skill with the resolved tier → unload → write `context-pressure.json` → exit.
   - **Model tier:** Haiku is sufficient — the agent does no reasoning, just orchestrates two deterministic skill outputs. Spec calls for Haiku; falls back to Sonnet if Haiku unavailable.
   - ~40 lines of frontmatter + instructions.

4. **`core/state/context-pressure.schema.json`** — JSON schema joining `loop-ready`, `loop-complete`, and `history.jsonl` in `core/state/`. Required fields: `phase_id`, `timestamp`, `window_size`, `tokens_used`, `percent`, `tier`, `window_source`. Note: **no `recommended_prompt` field** — that is derived at render time from the tier name via the `compaction-prompt` skill, ensuring a single source of truth for prompt wording.

5. **`platforms/claude-code/agents/context-agent.md`** — Claude Code adapter referencing the core agent definition, parallel to how `worker.md` and `orchestrator.md` are exposed.

6. **`platforms/claude-code/hooks/hooks.json`** — extend with the `SessionStart` entry from §3 that writes `.claude/state/transcript-path.txt`. And **`platforms/claude-code/commands/next-phase.md`** — add a final step after the gate-pass branch: spawn `context-agent`, await `.claude/state/context-pressure.json`, render the banner + recommended prompt to the user-facing report. Graceful failure path per §3.

State file (`.claude/state/context-pressure.json`):

```json
{
  "phase_id": "phase-7",
  "timestamp": "2026-05-13T14:22:00Z",
  "window_size": 200000,
  "tokens_used": 68421,
  "percent": 34,
  "tier": "Light",
  "model": "claude-opus-4-7",
  "window_source": "default-200k"
}
```

**Optional audit:** the main thread may append a `context_pressure` event to `history.jsonl` after rendering. One line, free. Spec leaves this as a nice-to-have, not required.

## 6. Open questions

- **Model-table maintenance.** The model → window-size table in `context-usage` will drift as new models ship. Acceptable cost: it lives in one file, and observed-token inference catches the only case where the table's wrong answer would actually matter (a 1M-capable model the table doesn't know about). A one-line entry in CLAUDE.md flags the file for future contributors.
- **Edge case: first-turn 1M user.** Observed-token inference only kicks in after the user crosses 200k once. A 1M-aware user whose first 200 turns all stay under 200k will be classified as 200k — which is technically harmless because the gauge stays accurate up to 200k tokens, and the moment they exceed 200k the inference flips. Accept.

## 6.1 Decisions locked in

- **Per-phase only — never per-loop.** A loop-level banner is too chatty and would normalise the signal away. The monitor fires exclusively at gate-pass inside `/next-phase`. A future `/context-check` slash command can reuse the same agent for on-demand checks if needed.
- **Window size is detected, not assumed.** Four-step resolution (env var → observed-tokens inference → model table → fallback). v1 ships with real 1M detection via observed-tokens; the model table is just a faster path for the common case.
- **Banner reports percentages only.** Raw token counts and absolute window size stay in the state file for debugging, never in user-facing output. Keeps the signal model-agnostic.
- **State file stores tier name only.** Rendered prompts come from the `compaction-prompt` skill at read time. Single source of truth for prompt wording.
- **Transcript path discovery via a passive SessionStart hook.** Cleanest fit with the existing `hooks.json` pattern; no slash-command shell-globbing, no env-var propagation assumptions.
- **Graceful failure is mandatory.** `/next-phase` must never be blocked by a context-agent error.

## 7. Implementation order

1. Draft `context-usage` skill with worked examples against a synthetic transcript JSONL. Include unit tests for: empty file, no-usage-block file, each tier boundary (none/tidy/light/strong/urgent), boundary inclusivity (exactly 10%, 25%, 50%, 75%), `CONTEXT_WINDOW` env-override path, observed-tokens 1M inference (one prior turn at 250k forces 1M), model-table hit (known opus → 200k), model-table miss with fallback warning, and verification that the banner-render path receives only the percent (not raw counts).
2. Draft `compaction-prompt` skill — pure tier-to-prompt mapping. Unit-test each of the five tier names returns the correct prompt; unknown tier raises.
3. Add `core/state/context-pressure.schema.json` and validate sample documents against it.
4. Define `context-agent` with the tight allowlist. Hand-test against fixture transcripts.
5. Add the `SessionStart` hook to `platforms/claude-code/hooks/hooks.json` and wire `context-agent` into `platforms/claude-code/commands/next-phase.md`'s gate-pass branch. Include the regression test: when `context-agent` is deliberately broken, `/next-phase` still advances the phase.
6. Update `CLAUDE.md`'s State Bus Protocol table to include `context-pressure.json` as a fourth state file.
7. Dogfood for a phase or two. Adjust thresholds and prompt wording based on what felt right vs noisy.

Estimated effort: half a day end-to-end. No new dependencies; consistent with the framework's zero-dep, skill-injection, file-bus conventions.

## 8. Why this is enough

The temptation with context management is to build infrastructure: durable artefacts, retrieval helpers, cold stores, hot manifests. Those are real ideas, but they assume context will keep getting *more* scarce. The opposite is happening — Claude's windows are growing, `/compact` is getting smarter, and the half-life of any custom compaction tooling we build is probably under a year.

What stays useful regardless of how the platform evolves is **a clear signal at a clear moment**, telling the user where they stand. This document specifies exactly that, and nothing more.
