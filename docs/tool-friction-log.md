# Tool Friction Log

A running record of friction encountered while using the framework's tools,
slash commands, skills, and the broader Claude Code harness. Append new
observations at the end. Each entry should name the tool/surface, describe the
friction concretely (with a session date), and suggest an improvement when
possible.

This log is **not** a defect tracker — it captures rough edges that may not
warrant a phase of their own but accumulate signal for future automation /
hygiene work. The deferred "automation surface audit" phase will likely consume
entries from here.

## Conventions

- One entry per friction point.
- Title format: `[Surface] — One-line description`.
- Body includes: when observed, what happened, why it's friction, suggested fix.
- Append-only. Mark obsolete entries with a strike-through header and a one-line
  resolution note rather than deleting.

---

## 2026-05-13 — Phase 8 planning session

### [Permissions] — Routine plan/loop edits prompt for approval

- **Observed**: every status flip from `pending` → `in_progress` on a todo, every
  small edit to `plans/phase-N.md`, requires the user to accept a permission
  prompt.
- **Friction**: the framework's bread-and-butter operations are exactly the ones
  that hit prompts. Breaks "seamless workflow" goal.
- **Suggested fix**: repo-root `.claude/settings.json` with permissive `allow`
  rules scoped to `plans/**`, `.claude/state/**`, `.claude/logs/**`. Already
  captured as Phase 8 Wave 1.3 / SC-3.

### [Write tool] — Forced full-file rewrite when restructure is extensive

- **Observed**: rewriting the spec and the phase plan to absorb brainstorming
  decisions. Many small Edit calls would have been noisier than a single Write
  rewrite, but a full Write loses incremental clarity in the git history.
- **Friction**: no middle path between "many surgical Edits" and "one wholesale
  Write". For major restructure, an in-place "rewrite from current Read" mode
  would land cleaner diffs.
- **Suggested fix**: harness convention only; tool semantics are correct as-is.
  Maybe a writing-skills note: when restructure is >40% of file, do it as one
  Write with a commit message that explains the intent.

### [Read tool] — Mandatory re-read before Edit when file was just Written

- **Observed**: after writing the spec file with full content, a later
  small-section Edit required a Read first per the Edit tool contract. The
  Read returned the file we just wrote.
- **Friction**: in a session where the file state is harness-tracked from the
  Write, the Read is a 280-line round-trip to learn what we already know.
- **Suggested fix**: harness-level — Write should satisfy the "you have read
  the file" precondition for subsequent Edits in the same session.

### [System reminders] — "Task tools haven't been used recently" appears even when not applicable

- **Observed**: three times during a session that was entirely conversational
  refinement of two files, the system suggested TaskCreate. The work was
  sequential, single-threaded, and didn't benefit from task tracking.
- **Friction**: false-positive nudges create noise. The reminder costs no
  tokens to ignore individually but adds up.
- **Suggested fix**: scope the reminder to sessions with explicit multi-step
  workflows. Could be heuristic on "n tool calls without a TodoWrite" rather
  than time-based.

### [AskUserQuestion] — Hard cap of 4 options forces premature collapsing

- **Observed**: surveying possible new names for `new-loop` (decompose-phase,
  plan-loops, expand-phase, loops-from-phase, plus "other"). Had to drop
  candidates to fit the 4-option ceiling.
- **Friction**: information density of a forced-choice prompt suffers when
  there are 5+ genuine candidates. "Other" mitigates this but loses the
  recommendation-context for the dropped options.
- **Suggested fix**: tool-level — allow 5–6 options. Or skill-level — when
  enumerating alternatives, present them inline as prose and use
  AskUserQuestion only for the binary "pick one" decision after the user has
  read all candidates.

### [phase-plan-creator skill] — Skill output is a template, not a generated artefact

- **Observed**: invoking the skill returned instructions on how to produce a
  phase plan, not the phase plan itself. The actual phase plan was produced
  by me applying the skill's template to the spec.
- **Friction**: ambiguity about whether "the skill creates the plan" or "the
  skill tells me how to create the plan". The latter is the truth; the
  description suggests the former.
- **Suggested fix**: skill description tightened to "Provides a structured
  template and process for creating phase plans" rather than "Generate
  structured … phase plans". Honest about what it does.

### [Brainstorming skill] — HARD-GATE conflicts with iterative refinement work

- **Observed**: the brainstorming skill forbids "any implementation action".
  But the user-approved work in the session WAS substantive edits to the spec
  and phase plan. Those edits are not "implementation" in the code-change
  sense, but they are file mutations the skill could reasonably gate.
- **Friction**: the skill's gate is binary (no implementation) but the
  brainstorming output is meant to result in a written design doc, which is
  itself a mutation. The boundary between "approved design changes" and
  "implementation" is fuzzy.
- **Suggested fix**: skill could explicitly carve out exceptions for "edits
  to the design spec and phase plan it's producing". Or: gate language could
  be "no code edits to source files outside `plans/` and `docs/`".

### [Plans pipeline] — Three artefacts encode the same design

- **Observed**: a single design (Phase 8) is documented in three places:
  1. `plans/2026-05-13-framework-consistency-audit-remediation.md` (spec)
  2. `plans/phase-8.md` (phase plan)
  3. `plans/PLANS-INDEX.md` (index entry)
  Soon to be four when `plans/phase-8-ralph-loops.md` exists. Success
  criteria and scope statements appear in 2 of these; loop names appear in
  3 of them.
- **Friction**: keeping them in sync is manual. A spec edit doesn't propagate
  to the phase plan. A loop rename doesn't update the index. Drift risk is
  real.
- **Suggested fix**: longer-term — the phase plan could be derived from the
  spec rather than co-authored. Short-term — a single command (e.g.,
  `/sync-plans`) that re-renders downstream artefacts from the spec when it
  changes. Worth scoping in the deferred automation-surface phase.

### [PLANS-INDEX.md] — Manifest entries for completed phases were not appended

- **Observed**: Phases 6 and 7 are complete (per recent commits and the
  phase-completes/ artefacts) but are missing from the PLANS-INDEX.md
  "Phases" table.
- **Friction**: the index is supposed to be the canonical at-a-glance
  programme view. Missing entries break that property.
- **Suggested fix**: either `/phase-compact` is failing to append the
  manifest entry (defect to investigate) or the append step requires manual
  invocation that was forgotten at the last gate pass. Should be its own
  scoping ticket.

### [Skill loading] — Skill content arrives as a long inline message

- **Observed**: invoking `/brainstorming` and `/phase-plan-creator` produced
  multi-thousand-token skill documents inline as user-message content. These
  add context-window pressure even when the relevant section is one
  checklist.
- **Friction**: skill content becomes part of the working context whether or
  not the agent re-references it. Long skills compound this across multiple
  invocations.
- **Suggested fix**: skills could include a short "TL;DR" header that the
  agent loads first, with a path to the full content for re-reference.
  Targeted skill injection (per the framework's own pattern) already
  partially solves this but only at the ralph-loop-worker layer, not in
  conversational Claude Code use.

---

## 2026-05-14 — Phase 8 loop decomposition session

### [/new-loop command] — Lookup path has a double-extension bug

- **Observed**: the command's "Find the phase plan" step says
  `Try .claude/plans/phase-plans/phase-8.md.md (e.g. phase-2.md for /new-loop 2)`.
  Double `.md` extension. Whatever template substitution generated this was
  miswired.
- **Friction**: a literal read would have looked for a path that can't exist
  and failed silently. Worked anyway because I treated the argument as a
  direct file path.
- **Suggested fix**: fix the template in
  `platforms/claude-code/commands/new-loop.md`. The lookup should be
  `.claude/plans/phase-{N}.md`.

### [/new-loop command] — Output path contradicts framework convention

- **Observed**: the command tells me to save to
  `.claude/plans/phase-[N]-ralph-loops.md` (under `.claude/`). But every
  existing ralph-loops file (`plans/phase-1-ralph-loops.md` through
  `plans/phase-5-ralph-loops.md`) lives at the repo's top-level `plans/`
  directory. The ralph-loop-planner skill itself correctly specifies
  `plans/phase-{N}-ralph-loops.md`.
- **Friction**: same root cause as C1 in the audit — the `.claude/plans/` vs
  `plans/` confusion is present in the command guidance too, not just the
  hook allowlist.
- **Suggested fix**: fold into Phase 8 Wave 1 or treat as a sibling defect
  surfaced during execution. Update
  `platforms/claude-code/commands/new-loop.md` (or its post-Wave-4 successor
  `decompose-phase.md`) to specify `plans/` instead of `.claude/plans/`.

### [/next-loop command] — Plan lookup path is wrong

- **Observed**: step 1 runs `ls .claude/plans/*.md`. Phase plans actually live in
  top-level `plans/`. A literal read produces "NONE" and stops the command.
- **Friction**: same root cause as the `/new-loop` path bug — the `.claude/plans/`
  vs `plans/` confusion has propagated into multiple command files. This is
  exactly the C1 audit finding manifesting at the slash-command surface.
- **Suggested fix**: fold into Phase 8 Loop 027 as part of the hook+permissions
  hygiene scope, OR add a `decompose-phase` Loop 030 sub-task that sweeps the
  command file system for `.claude/plans/` references and corrects them.

### [State files] — Stale loop-ready.json and loop-complete.json from previous phases

- **Observed**: starting Phase 8 with `loop-ready.json` and `loop-complete.json`
  in `.claude/state/` from Phase 7. /next-loop's step 5 reads these without
  detecting that they belong to a previous phase.
- **Friction**: a hung or partial state file from a previous phase could be
  silently consumed as if it referred to the current phase, leading to confused
  worker assignments.
- **Suggested fix**: orchestrator (or /next-loop step 3) should clear stale
  state files at phase boundary. Could check the loop_name in loop-ready.json
  against the next pending loop in the current phase; if they don't match,
  archive the old file to `.claude/state/archive/` before writing.

### [Git checkpoint pattern] — In-flight planning work gets bundled with execution checkpoint

- **Observed**: /next-loop step 3 does `git add -A && git commit -m "checkpoint:
  before next-loop cycle"`. At this moment the working tree has both this
  session's planning artefacts (design spec, phase plan, ralph loops file,
  index updates, friction log) AND legacy uncommitted file deletions from
  Phases 6/7 compaction.
- **Friction**: the checkpoint commit conflates many unrelated changes under
  one generic message. Git history becomes harder to bisect; the "checkpoint"
  marker stops being a clean rollback point.
- **Suggested fix**: /next-loop could check `git status` and refuse to run if
  the working tree contains uncommitted changes unrelated to loop execution.
  Or: prompt to commit planning work under its own message first. This is a
  candidate for the future automation surface phase's "prerequisites guard"
  pattern.

### [Workflow chaining] — Stub generation and todo population are separate steps with no automation

- **Observed**: the ralph-loop-planner skill says to generate stubs with
  empty `todos[]`, then run `plan-todos`, then `plan-skill-identification`,
  then `plan-subagent-identification` — four sequential steps before a loop
  is execution-ready.
- **Friction**: each step is a separate invocation. For a phase as
  well-specified as Phase 8 (where the phase plan already names deliverables
  per loop), much of the populating work is mechanical and could be done in
  one pass.
- **Suggested fix**: candidate for the future automation surface phase —
  `/new-loop --full` could chain stubs → todos → skill assignment → agent
  assignment in one call. Probably a default behaviour rather than a flag
  once it's proven safe.

---

## Template for new entries

```
### [Surface] — One-line description

- **Observed**: when, what happened.
- **Friction**: why it's friction; impact.
- **Suggested fix**: concrete improvement if known, or "needs scoping".
```
