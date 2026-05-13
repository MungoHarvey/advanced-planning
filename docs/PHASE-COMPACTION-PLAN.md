# Phase-End Compaction System — Implementation Plan

> A planning document for adding git-anchored, hook-triggered phase compaction to the Advanced AI Workflows ecosystem. The fundamentals are settled; several implementation specifics are deliberately left open and should be resolved in collaboration with Claude Code once full repository context is loaded.

---

## 1. Problem

Long-running agentic programmes burn context. The existing architecture already compresses at the **loop** level via `loop-complete.json`'s terse `done / failed / needed` handoff — this is the single most important compression mechanism in the system, and the ARCHITECTURE document explicitly notes that the terseness is a *design choice* to prevent context bleed between loops.

There is no equivalent mechanism at the **phase** level. By the time several loops have completed within a phase, the main thread carries far more loop context than it needs for the next phase's planning. Auto-compact (which fires near 95% capacity) is a poor solution: it lands non-deterministically, often mid-task, and degrades cumulatively across multiple compactions.

Meanwhile, every code change has already been persisted to git, which is durable, addressable by SHA, and recoverable on demand. The actual source-of-truth for "what changed in this phase" is already external to context — it is simply not being treated as such.

---

## 2. Solution shape (high confidence)

The fundamentals we have agreed on:

- **Git as source of truth.** Compaction artefacts reference commit SHAs rather than embedding diffs. Full state is always recoverable via `git show <sha>` when (and only when) a later phase actually needs it.
- **Hook-triggered automation.** Compaction fires automatically on Gate Review pass — never manually remembered, never run mid-task.
- **Dedicated subagent.** A `phase-compactor` agent produces the artefacts. Mirrors the existing two-agent handoff pattern (orchestrator → worker); the main thread spawns it, it writes files, it exits.
- **Two-tier hot/cold store.**
  - *Hot:* a per-phase block appended to `PLANS-INDEX.md`, always loaded in subsequent sessions. Few lines, goals + verdict + commit range.
  - *Cold:* a full `phase-N-complete.md` artefact, on disk, loaded only when explicitly requested.
- **Clear-and-reload between phases.** Once the artefact is written, the main thread issues `/clear` and starts the next phase with only the hot manifest in context.

Together, these mean context budget stays roughly constant as the programme grows from 3 phases to 30, and any historical detail remains recoverable without inflating ongoing sessions.

---

## 3. What this is NOT

To scope the work clearly:

- **Not a replacement for `/compact`.** The existing compact behaviour still serves *intra-phase* compression. Phase compaction is additive — it operates at boundaries the loop-level mechanism does not reach.
- **Not a replacement for git.** The artefacts are summaries with pointers, never substitutes for the diffs themselves.
- **Not a replacement for `loop-complete.json`.** Loop-level compression remains as-is. Phase compaction *synthesises* across loop completions; it does not duplicate them.
- **Not a new planning tool.** No changes to `phase-plan-creator`, `ralph-loop-planner`, or Plannotator. This is purely a post-execution / post-gate concern.

---

## 4. Architectural constraints to honour

These come directly from `ARCHITECTURE.md` and must not be violated:

- **Boundary integration only.** No shared databases, no IPC. Everything crosses boundaries as files. The phase-compactor reads files (phase plan, `history.jsonl`, git log) and writes files (`phase-N-complete.md`, `PLANS-INDEX.md` update). That is its entire interface.
- **Main thread is sole orchestrator.** The compactor never spawns other agents. It is itself spawned by the main thread.
- **No concurrent agents.** Compaction runs sequentially after Gate Review.
- **Targeted context.** The compactor receives only what it needs: the phase plan, the relevant slice of `history.jsonl`, and the git log range. Not the whole programme history.
- **Each tool independent.** This work lives within Advanced Planning's domain. It must not require changes to Plannotator or Superpowers internals.

---

## 5. Phase plan

Five phases, each with clear entry and exit criteria. Sub-phases are listed where useful.

### Phase 1 — Artefact contracts

Lock down the schemas before writing any executing code. Every downstream component depends on these.

**Sub-phases**

- 1a — Draft `phase-N-complete.md` schema (the cold artefact)
- 1b — Draft `PLANS-INDEX.md` extension schema (the hot manifest)
- 1c — Document recovery semantics — what does a future session do with each artefact?
- 1d — Validate the schemas against one or two retrospectively-imagined phases from the repo's own development

**Exit criteria**
- Both schemas committed as markdown documents under `docs/` or similar
- A worked example for each, ideally drawn from a real recent phase
- Explicit list of required vs optional fields

**Open here:** schema format choices (see §7).

---

### Phase 2 — Manual proof of concept via `/phase-compact` slash command

Before automating anything, validate the artefact shape against reality by running the workflow by hand at a real phase boundary.

**Sub-phases**

- 2a — Implement `/phase-compact` as a slash command that takes `<phase-id>` as argument
- 2b — Wire it to read the phase plan, slice `history.jsonl`, and run `git log <anchor>..HEAD`
- 2c — Produce both artefacts from a single invocation
- 2d — Run against a synthetic or retrospective phase; review the output critically

**Exit criteria**
- One real or simulated phase has been compacted by hand
- The output artefacts are useful enough that a fresh Claude session, given only the hot manifest, can plan the next phase coherently
- Iterate on artefact schemas if the output reveals gaps

**Open here:** phase-start anchor mechanism, exact prompt structure.

---

### Phase 3 — Promote to `phase-compactor` subagent

Move the slash command's logic into a proper subagent definition.

**Sub-phases**

- 3a — Define `.claude/agents/phase-compactor.md` with scoped tool allowlist
- 3b — Decide whether the compactor is invoked via slash command, by the gate agent, or both
- 3c — Ensure the agent runs with the smallest model that does the job reliably (probably Sonnet; possibly Haiku if the prompt is structured enough)
- 3d — Add validation: the agent should refuse to write artefacts if input contracts are violated (e.g. missing phase plan, missing anchor SHA)

**Exit criteria**
- Subagent file exists, is documented, and can be invoked manually
- Behaviour is equivalent to the Phase 2 slash command
- Tool permissions are minimal (likely: `Read`, `Bash(git log:*, git show:*)`, `Write` to specific paths)

**Open here:** agent invocation pattern, model tier.

---

### Phase 4 — Hook integration

Automate the trigger so compaction never has to be remembered.

**Sub-phases**

- 4a — Decide the trigger mechanism (see §7 — this is one of the more open questions)
- 4b — Implement the trigger
- 4c — Handle the `/clear` and reload sequence cleanly
- 4d — Test for misfire conditions: gate fail (must not compact), gate skip, interrupted execution

**Exit criteria**
- Compaction fires deterministically on gate pass and only on gate pass
- The main thread resumes with only the hot manifest after compaction
- Failure modes are documented (what happens if compaction itself errors?)

**Open here:** trigger mechanism (Claude Code hook vs gate-agent-driven spawn), clear-and-reload ownership.

---

### Phase 5 — Retrieval helpers

The cold tier is only useful if there is a clean way to reach back into it.

**Sub-phases**

- 5a — Add `/load-phase-context N` command (or skill) to pull a specific cold artefact into context on demand
- 5b — Document the pattern: when should a phase explicitly reach back?
- 5c — Consider whether `PLANS-INDEX.md` itself should hint at which phases are likely candidates for back-reference (e.g. "Phase 3 deferred work to Phase 5 — see commit range X..Y")

**Exit criteria**
- A future phase can selectively load earlier context without re-reading everything
- Documented examples of when to reach back vs when not to

**Open here:** whether retrieval is invoked by Claude autonomously or always by the user.

---

## 6. Key insights worth carrying into development

These are the reasoning steps that led to the current shape. Worth holding onto when judging design choices later.

- **Compression already exists at the loop tier.** The phase tier is an extension of an established pattern, not a new invention. Look at how `loop-complete.json`'s `done / failed / needed` structure achieves terseness — the phase artefact should be that disciplined, just at a larger scope.
- **Commit SHAs are durable pointers.** Anything that lives in git does not need to live in context. The artefact's job is to make the *index* into git navigable, not to duplicate git's contents.
- **The `phase-goals` gate agent already reasons about goals vs outcomes.** Compaction may overlap with what that agent computes. Consider whether to extend it or stand the compactor alongside it. Both are defensible; the former is cheaper, the latter is cleaner.
- **Hot/cold separation is what makes this scale.** A single growing manifest will eventually become its own context burden. The hot tier must stay small *per phase entry* so that even after 30 phases, the cumulative weight is manageable.
- **Conventional commits help disproportionately.** If commits are small and well-described, the compactor's job becomes near-trivial — it is mostly assembling existing facts. Worth flagging this as a precondition for the system to work well.

---

## 7. Open design questions

These are the specifics deliberately left unresolved. They should be worked through *with full repository context loaded* — likely during Phase 1 and Phase 4 development. Each lists the options identified so far and the trade-offs as currently understood; the right answer may turn out to be none of these or a hybrid.

### 7.1 Phase-start anchor — how does the compactor know where to begin `git log`?

Options identified:
- **(a)** Frontmatter field on the phase plan (`anchor_sha: abc123` written when the phase is created)
- **(b)** Git tags (`phase-2-start`, `phase-2-end`) applied programmatically
- **(c)** Inference from `history.jsonl` timestamps cross-referenced against `git log --since`
- **(d)** Hybrid: tag at start, frontmatter for redundancy

Lean: (a) is simplest and lives alongside the plan, but (b) is more durable across plan rewrites. Worth deciding based on how often phase plans are edited mid-phase.

### 7.2 Hook event mechanism — how is compaction actually triggered on gate pass?

Options identified:
- **(a)** Claude Code `PostToolUse` hook on whatever tool the gate agent uses to write its verdict
- **(b)** The gate agent itself spawns the compactor as its final action — no Claude Code hook involved
- **(c)** Slash command only — accept manual invocation as the cost of avoiding hook complexity

Lean: (b) keeps "main thread is sole orchestrator" intact and avoids interacting with the `EnterPlanMode` hook coexistence issues already documented in `ARCHITECTURE.md` §7. But check whether the gate agent has authority to spawn — current pattern says only the main thread does. May require revising the gate agent's contract, or having it write a `gate-pass.json` signal file the main thread polls.

### 7.3 Clear-and-reload ownership — who issues `/clear` and reloads the manifest?

Options identified:
- **(a)** The compactor agent itself, as its final action
- **(b)** The main thread, after observing the compactor's output
- **(c)** A separate small skill invoked after compaction

Lean: (b). Agents produce files; the main thread manages context. Mixing those concerns inside the compactor breaks the existing pattern. But this means the main thread needs a clean way to detect compaction completion — probably a file marker.

### 7.4 `PLANS-INDEX.md` format — hot manifest schema

Options identified:
- **(a)** Pure markdown table — most human-readable, hardest to parse
- **(b)** YAML frontmatter / YAML blocks — most machine-parseable, less browsable
- **(c)** Hybrid: YAML block per phase for parseability, rendered as a markdown table by a small script for human reading
- **(d)** Append-only JSONL alongside the markdown for programmatic access

Lean: (c) for the artefact itself; (d) is overkill given the file will only have N entries for N phases. Verify by drafting one example in each format and judging readability.

### 7.5 Subagent vs gate-agent extension

Options identified:
- **(a)** Standalone `phase-compactor` subagent (current plan)
- **(b)** Extend the existing `phase-goals` gate agent to emit compaction artefacts as a side effect

Lean: (a) for separation of concerns, but (b) saves an agent spawn and the gate agent already has all the needed information. Decide based on whether the gate agent's prompt can absorb the extra responsibility without losing focus on its primary task.

### 7.6 What happens on gate fail?

Currently the plan assumes compaction only fires on gate pass. But gate failure also produces useful state worth recording. Options:
- **(a)** No artefact on fail — phase isn't "complete" yet
- **(b)** Write a partial artefact under a different name (`phase-N-attempt-M.md`) for retry context
- **(c)** Always write, with a `status: failed` flag

Lean: (a) for cleanliness, but (b) might help when a phase needs multiple retry passes — the versioned retry pattern is already in the architecture.

### 7.7 Compactor failure handling

If the compactor errors (git log fails, write permission denied, model output malformed), what should happen?
- Block the next phase?
- Log and continue with a degraded manifest entry?
- Retry?

Worth deciding before Phase 4 — automation amplifies the cost of getting this wrong.

---

## 8. Definition of done

The integrated system is complete when all of the following hold:

- A long-running programme (10+ phases) can be conducted with roughly constant per-session context load
- A fresh Claude session, loaded with only `PLANS-INDEX.md`, can plan the next phase coherently without back-reference in the common case
- When back-reference is genuinely needed, the relevant cold artefact can be loaded with one command
- Compaction has never been forgotten, because it fires automatically on every gate pass
- No tool other than Advanced Planning has been modified
- The system fails closed: if compaction itself errors, the user is told, and the next phase does not silently proceed with stale or missing manifest entries

---

## 9. References

Existing repository documents that this plan should be consistent with:

- `ARCHITECTURE.md` — especially §2 (Boundary Integration), §5 (State Management), §6 (Agent Orchestration), §7 (Hook Coexistence)
- `DESIGN-RATIONALE.md` — for the philosophical commitments that constrain how new components fit in
- `ROADMAP.md` — check whether phase compaction is already noted there and if so, this plan supersedes / refines it
- `.claude/skills/setup-with-claude/SKILL.md` — for how new components get bootstrapped into projects

External:
- Claude Code best practices on `/compact`, subagents, and hooks — confirm current hook event names and `PostToolUse` semantics before implementing Phase 4

---

## 10. First step

Phase 1, sub-phase 1a: draft the `phase-N-complete.md` schema. Everything else is downstream of this. Once that artefact's shape is right, the rest of the system is largely mechanical.
