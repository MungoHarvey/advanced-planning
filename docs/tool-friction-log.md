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

### [Canonical todo schema] — Orchestrator added non-canonical `complexity:` field

- **Observed**: ralph-orchestrator populated Loop 027 todos with a `complexity:`
  field between `status:` and `priority:`. CLAUDE.md specifies the canonical
  field order as `id/content/skill/agent/outcome/status/priority` — no
  `complexity` field. However, CLAUDE.md *also* references "`complexity: low`
  todos" in the model-tier routing section, treating complexity as a known
  field.
- **Friction**: the schema is internally inconsistent. Either `complexity` is
  canonical (in which case the field-order list is incomplete) or it isn't
  (in which case the model-tier routing reference is incoherent). The
  orchestrator picked the inclusive interpretation, but a future contributor
  could justifiably remove it on canonical-order grounds.
- **Suggested fix**: update `core/schemas/ralph-loop.schema.md` and
  CLAUDE.md to either include `complexity:` in the canonical order
  (positioned per existing usage) or explicitly document it as an optional
  metadata field. Choose one and align both references.

### [Skill discovery] — Phase plan "skill domains" treated as skill names

- **Observed**: Phase 8 plan lists `hook-and-permissions`, `code-editing`,
  `frontmatter-schema` as "broad skill categories". The orchestrator's
  `plan-skill-identification` step searched for installed skills with those
  names, found none, and assigned `skill: NA` to all 8 todos in Loop 027.
- **Friction**: there's no formal distinction in the framework between (a) a
  taxonomy of *skill domains* used during phase planning to describe broad
  capabilities and (b) the *installed skill names* used during execution.
  Both surface as bare strings; the planner can't tell them apart.
- **Suggested fix**: either (1) require phase plans to use only installed
  skill names (constrains the planner, may miss capabilities not yet
  installed), or (2) introduce a clear separator in phase plan templates
  between "skill domains" (descriptive) and "specific skills to use"
  (resolvable). The current ambiguity makes the planner's output less useful
  than it could be.

### [agent: field self-reference] — Orchestrator assigned ralph-loop-worker as agent for individual todos

- **Observed**: 5 of 8 Loop 027 todos have `agent: ralph-loop-worker`. The
  worker is the agent executing the loop itself; assigning it as an `agent:`
  for individual todos is self-referential. Combined with C2 from the audit
  (worker cannot dispatch), the assignment is doubly decorative.
- **Friction**: `plan-subagent-identification` has no clear rule about what
  to do when no specialized agent fits a todo. Picking the worker itself
  reads as a default-fallback, but it adds noise without semantic value.
- **Suggested fix**: the `plan-subagent-identification` skill should
  default to `agent: NA` when no specialized agent fits. Reserve named
  agents for actual delegation candidates. Aligns with the always-dispatch
  Phase 9 redesign — only set `agent:` when dispatch is intended.

### [Orchestrator protocol] — `.claude/agents/` referenced but agents live at `platforms/claude-code/agents/`

- **Observed**: orchestrator flagged that the protocol referenced
  `.claude/agents/` but actual agents live at `platforms/claude-code/agents/`.
  Mirror of the `.claude/plans/` vs `plans/` problem at the agent-resolution
  surface.
- **Friction**: the path confusion is systemic. The `.claude/` prefix appears
  in many command and skill docs but the actual layout in this repo is
  top-level `platforms/claude-code/` for everything Claude Code-related.
- **Suggested fix**: a single Loop 030 sub-task (during the rename sweep)
  could grep for all `.claude/agents/`, `.claude/plans/`, `.claude/skills/`
  references in forward-looking docs and triage which should stay (because
  they refer to installed-project layout where `.claude/` is canonical) and
  which should be corrected (because they refer to this repo's source
  layout).

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

---

## 2026-05-15 — Phase 9 planning session

### [Skill chaining] — phase-plan-creator does not auto-invoke ralph-loop-planner

- **Observed**: brainstorming → phase-plan-creator chains automatically (the
  brainstorming skill's terminal step explicitly invokes phase-plan-creator
  with the design doc path). But phase-plan-creator → ralph-loop-planner does
  NOT chain — phase-plan-creator's "Next Steps" section lists ralph-loop-planner
  as a manual recommendation rather than invoking it. The user has to type
  `/ralph-loop-planner` (or similar) themselves to continue the planning chain.
- **Friction**: this is a slow bottleneck in the planning pipeline. The natural
  workflow is design → phase plan → ralph loops as one continuous decomposition.
  Stopping at the phase plan forces the user to remember the next step, switch
  context, and re-invoke. The hand-off is artificial — the phase plan is
  explicitly *designed* to feed ralph-loop-planner.
- **Suggested fix**: amend `~/.claude/skills/phase-plan-creator/SKILL.md` so the
  "Next Steps" section ends with an instruction equivalent to brainstorming's
  terminal step: "After writing the phase plan and updating PLANS-INDEX.md,
  invoke ralph-loop-planner immediately with the phase plan path as input.
  Do not ask the user to invoke it manually." This mirrors the
  brainstorming → phase-plan-creator chaining that already works well.
  Document this chain explicitly in CLAUDE.md's Architecture section so it's
  clear that the three-skill pipeline is intended to run end-to-end.

## 2026-05-18 — Phase 9 execution (Loop 035)

### [Worker durability] — ralph-loop-worker subagent died mid-loop on usage limit

- **Observed**: the Loop 035 ralph-loop-worker exhausted account usage after
  ~45 tool calls (todos 1–5 done, 6 in_progress, 7–9 pending). It returned a
  usage-limit string instead of writing loop-complete.json, so the state bus
  showed loop-complete.json still pointing at Loop 034. The `/next-loop --auto`
  chain had no signal that the loop was partially applied — files were edited
  and uncommitted but no completion record existed.
- **Friction**: a subagent that dies mid-loop leaves the state bus silently
  stale. Auto-chain can't distinguish "not started" from "half-applied,
  uncommitted." Recovery required a manual resume-review pass (git diff +
  per-todo status inspection in loops.md) from the main thread.
- **Suggested fix**: have the worker write a `loop-complete.json` with
  `status: partial` and per-todo progress as its *first* action would not help
  (it dies unpredictably). Better: `/next-loop` should, before spawning the
  orchestrator, detect "loop-ready.json newer than loop-complete.json AND
  working tree dirty" and run a resume-review verification automatically
  instead of assuming the prior loop landed. Also: prefer driving long
  mechanical path-rewrite loops from the main thread rather than a subagent
  when the work is deterministic and the subagent adds no isolation value.

## 2026-05-18 — Phase 9 gate review (attempt 1 FAILED)

### [Bulk substitution] — regex re-applied to already-migrated text (double-prefix)

- **Observed**: Loop 036 used a scripted ordered-substitution pass to re-point
  `plans/` → `.advanced-plans/` across 39 files. One rule,
  `plans/PLANS-INDEX.md` → `.advanced-plans/PLANS-INDEX.md`, also matched the
  `plans/PLANS-INDEX.md` *substring inside already-correct*
  `.advanced-plans/PLANS-INDEX.md`, producing `.advanced-.advanced-plans/PLANS-INDEX.md`
  in 4 command files (10 occurrences). Both gate agents independently caught it;
  it was a CRITICAL verdict-blocking defect.
- **Friction**: (1) substitution rules with no left-anchor/negative-lookbehind
  corrupt text that already contains the replacement as a substring. (2) The
  Loop 036 grep audit only searched for the *old* patterns, so it structurally
  could not detect a *new-shape* corruption — it reported "clean" while the
  repo was broken. A migration audit that only looks backward is half an audit.
- **Suggested fix**: (a) substitution rules must be anchored
  (`(?<![.\w-])plans/PLANS-INDEX\.md`) or run idempotently (assert a second
  pass is a no-op). (b) Post-migration audit must ALSO grep for corruption
  signatures of the *target* scheme (e.g. doubled prefix
  `\.advanced-\.advanced-plans`, `\.claude/\.advanced-plans`) — not just
  residual old paths. Add both checks to the loop-036-style audit todo.

### [Agent tooling] — phase-goals-agent had no Write tool, could not emit its verdict

- **Observed**: the spawned `phase-goals-agent` was provisioned with only
  Read/Glob/Grep. Its whole job is to *write* a verdict JSON to
  `.advanced-plans/gate-verdicts/...`. It produced the full verdict but had to
  return it as response text; the main thread had to write the file on its
  behalf. The agent type's advertised tool set (Read, Glob, Grep) omits Write.
- **Friction**: a gate agent that cannot persist its own verdict breaks the
  state-bus contract `/run-gate` relies on (immutable one-file-per-agent
  verdicts). It works only because the main thread babysits the write, which
  defeats the isolation the gate sentinel is meant to provide and risks the
  verdict never being persisted if the main thread doesn't notice.
- **Suggested fix**: add `Write` (scoped, the gate-review-mode sentinel already
  restricts it to `.advanced-plans/gate-verdicts/` + `.advanced-plans/state/`)
  to the `phase-goals-agent` definition's tool list, mirroring
  `code-review-agent` which wrote its own verdict successfully. Until fixed,
  `/run-gate` should explicitly expect phase-goals-agent to return verdict
  text and persist it main-thread-side (document this in run-gate.md).

### [Path schema] — flat vs per-phase gate-verdicts location was never canonical

- **Observed**: the framework shipped with two contradictory conventions for
  where gate verdict JSON lives. `run-gate.md` and `next-phase.md` step text
  used per-phase `.advanced-plans/phases/phase-N/gate-verdicts/`, while the
  agent definitions (`phase-goals-agent.md`, `programme-reporter.md`,
  `code-review-agent.md`), the CLAUDE.md Runtime Directory tree, and the
  historical Phase 6/7 artefacts variously used flat
  `.advanced-plans/gate-verdicts/`. Both gate agents flagged this as a
  (non-blocking) warning during Phase 9 attempt 1.
- **Friction**: there was no single source of truth for an artefact the state
  bus depends on. An agent writing per-phase while a command reads flat (or
  vice-versa) silently loses verdicts — the gate appears to produce no output.
  This is the same class of bug as the double-prefix corruption: a path
  convention asserted in prose in N places with no enforcement.
- **Resolution + suggested guard**: canonicalised to flat
  `.advanced-plans/gate-verdicts/` (matches CLAUDE.md, agent defs, and the
  Phase 9 verdicts already written). Phase 6/7 per-phase verdicts left as
  immutable history. Going forward, path conventions consumed by the state bus
  (verdicts, loop-ready/complete, history.jsonl) should be defined once in a
  single schema doc and referenced — not re-stated per command file. A CI/audit
  check should assert no command or agent file references a non-canonical
  gate-verdicts path.

### [Command rot] — slash-command step text carries stale hardcoded paths

- **Observed**: even after the Phase 9 restructure, `/run-gate` and
  `/next-phase` command bodies still contain pre-restructure hardcoded paths in
  their numbered step instructions (`.claude/plans/*.md`, `.claude/state/`,
  `plans/gate-verdicts/`, `mkdir -p plans/gate-verdicts`, `/new-loop`). The
  commands "worked" this session only because the operator (main thread)
  recognised the paths were stale and followed the new `.advanced-plans/`
  layout instead of the literal instructions.
- **Friction**: a command file whose prose instructs the agent to read/write
  paths that no longer exist is a latent trap — a less context-aware agent (or
  a fresh session) would follow the literal steps, create `.claude/state/`
  sentinels the hooks don't watch, and write verdicts where nothing reads them.
  The restructure migrated *data* and the command *frontmatter/examples* but
  left imperative step text behind. Migration completeness was judged by a
  grep audit that (per the earlier entry) only looked backward and excluded
  the installed command surface from its blocking scope.
- **Suggested fix**: the post-migration audit must treat slash-command step
  text as in-scope (not just frontmatter and code), and assert zero
  pre-restructure path tokens in `platforms/claude-code/commands/**`. Longer
  term, command files should reference path constants/a layout doc rather than
  inlining literal paths in every step, so a layout change is one edit not
  twelve.

### [Workflow gap] — auto flow stops at phase end instead of auto-running the gate

- **Observed**: `/next-loop --auto` chains loops until the phase plan is
  exhausted, then **stops** and prints "Phase complete — run /run-gate". The
  gate review is a separate manual step. This session demonstrated the cost:
  Phase 9's 5 loops auto-chained, then the operator had to manually trigger
  `/run-gate`, which caught a critical defect that the in-loop audit missed. A
  phase is not actually "done" until its gate passes — but the auto flow treats
  loop-exhaustion as the terminal state.
- **Friction**: "phase complete" is reported before the only check that
  validates phase completeness has run. The user has to remember to gate, and
  the loop→gate boundary is an artificial hand-off in what should be one
  continuous "run this phase to a verified conclusion" operation. Same class as
  the brainstorming→phase-plan-creator→ralph-loop-planner chaining gap logged
  earlier: the pipeline is designed to run end-to-end but stops at every seam.
- **Desired behaviour (to implement)**: when the last loop of a phase completes
  in `--auto` mode, `/next-loop --auto` should automatically invoke the gate
  review (spawn the default gate agents sequentially, aggregate the verdict)
  rather than stopping. On gate **pass** → report phase verified-complete (and,
  under `/next-phase --auto`, advance to the next phase). On gate **fail** →
  stop the chain, surface the failing verdict, and require human intervention
  (do not auto-retry). Single-loop `/next-loop` (no `--auto`) keeps the current
  manual-gate behaviour. Net effect: a phase can be initiated and run to a
  gated, verified conclusion in one autonomous flow.
- **Implementation note**: lives in the `/next-loop` auto-chain decision step
  ("All loops complete" branch) — instead of `stop + print "run /run-gate"`,
  invoke the gate-review sequence inline, then branch on the aggregated
  verdict. Must reuse the existing gate machinery (gate-review-mode sentinel,
  per-agent immutable verdicts, history.jsonl event) — not a parallel
  implementation.

---

## 2026-05-19 -- Phase 10 (context-compaction reframe) session

### [AST checker] -- Worker used wrong allow-set in Loop 037, permitting `__future__`

- **Observed**: Loop 037's worker ran its AST zero-dep check with an allow-set
  that included `__future__`. The CI-canonical allow-set (CLAUDE.md) explicitly
  excludes it. The discrepancy meant context_meter.py shipped with a
  `from __future__ import annotations` import that would have failed the real CI
  job. Loop 038's advance caught and removed the import.
- **Friction**: the allow-set is defined in prose in CLAUDE.md, not in a
  machine-readable constant shared between the CI workflow, the worker's
  inline check, and the test suite. Each executor re-types it and can
  silently diverge.
- **Suggested fix**: define the canonical allowed-import set once in a
  `core/constraints.json` (or similar) file and read it from the CI job, the
  AST-checker helper, and any worker todo that runs the check. A single source
  of truth prevents per-worker drift.

### [Skills] -- `schema-design` and `permission-config` not installed; loops fell back to design doc

- **Observed**: Loops 038 and 040 declared `skill: "schema-design"` and
  `skill: "permission-config"` respectively. Neither skill exists at
  `.claude/skills/` or `~/.claude/skills/` in this repo. The worker logged
  "skill not found" and proceeded using the design-doc section as a substitute
  reference.
- **Friction**: the loop plan was written assuming installed skills that are
  actually absent. The fallback worked here because the design doc was
  authoritative and nearby, but the silent degradation gives no warning to the
  operator and would fail silently in a context-lean session.
- **Suggested fix**: (a) add a preflight check in the worker that surfaces
  missing skills as a visible warning (not a halt) in execution.log; (b)
  audit loop plans against installed skills before execution, or add
  `schema-design` and `permission-config` as stubs under `core/skills/`.

### [Slash commands] -- `/next-loop` and `/decompose-phase` unusable in the framework's own source repo

- **Observed**: the framework's slash commands live under
  `platforms/claude-code/commands/` (source), not `.claude/commands/` (runtime).
  Running `/next-loop` or `/decompose-phase` from within the source repo itself
  fails because Claude Code only discovers commands under `.claude/commands/`.
  All Phase 10 loops were driven via direct worker invocations rather than
  through the command interface.
- **Friction**: developing the framework involves testing the very machinery
  that cannot be invoked via its own interface. Every loop requires a manual
  "spawn worker" step; the `/next-loop --auto` chain that the framework
  documents as its primary execution path is unavailable.
- **Suggested fix**: the install script (`setup/claude-code/install.sh`) should
  be run against the source repo itself (self-install), or a dev-mode symlink
  from `.claude/commands/` -> `platforms/claude-code/commands/` should be
  established and documented so framework developers can exercise the live
  command surface.

- 2026-06-08 /next-loop: double complete-commit per loop — loop prompt on-completion commit AND /next-loop Step 9 main-thread commit both fire (e.g. 047 -> fac46a9 + 87fd2ce). Harmless but noisy; pick one owner.

- 2026-06-08 /brainstorming: default spec save path .claude/plans/ is gitignored in the framework self-host repo (.claude/* excluded). Design specs land untracked. Mirror to .advanced-plans/specs/ for version control.

---

## 2026-06-09 — Phase 14 Loop 056 (Codex Gate Proof)

### [codex exec / exec review] — Non-interactive mode emits fenced JSON block TWICE

- **Observed**: `codex exec review --ephemeral -m gpt-5.5 "<prompt>"` and
  `codex exec --ephemeral --full-auto "<prompt>"` both emit the model response
  twice in stdout: once as part of the conversation transcript (after the
  `codex` speaker label), and once as a final standalone output. A prompt
  asking for a single fenced JSON block produces two identical fenced JSON
  blocks in stdout.
- **Friction**: `extract_verdict_json` returns `None` for multiple fenced
  blocks (the ambiguity guard). This means the real codex stdout from
  `codex exec` always triggers the degrade path (`gate_codex_skipped`) rather
  than a successful extraction. The run-gate design assumes codex produces a
  single fenced block (per the codex-reviewer contract), but the CLI wrapper
  adds a second copy unconditionally.
- **Observed invocation**: `codex exec review --ephemeral -m gpt-5.5 "..."
  2>&1 | tee fixture.txt` — codex-cli 0.124.0, ChatGPT account auth.
  Real fixture saved at: `platforms/python/tests/fixtures/codex_stdout_sample.txt`
- **Suggested fix**: (a) pre-process codex stdout before passing to
  `extract_and_validate` — extract only the last fenced JSON block rather
  than rejecting ambiguous output (a lenient extraction variant). (b)
  Alternatively, use `--output-last-message <file>` flag to capture just the
  final message, which should be a single block. (c) Minimal scoped fix:
  add a `_extract_last_fenced_block` helper to `codex_gate.py` that returns
  the last fenced block when multiple are present, used when the blocks are
  structurally identical — this avoids false ambiguity rejections without
  changing the semantics for genuinely ambiguous (different) blocks.
  Note: this loop does NOT modify `codex_gate.py` (hard constraint); the fix
  is deferred to a future loop.

  **RESOLVED (Loop 058, 2026-06-09):** applied option (c) — `extract_verdict_json`
  now parses all fenced blocks when more than one is present and, if they are
  structurally identical, returns the last block; genuinely-differing or
  malformed blocks still return `None` (degrade). Covered by new unit tests
  (`test_collapses_identical_duplicate_fenced_blocks`,
  `test_returns_none_on_malformed_among_multiple_blocks`) and the live test
  (`test_real_fixture_identical_double_block_resolves`,
  `test_differing_double_block_still_degrades`). Logged as a CLAUDE.md Phase 14
  decision (minimal scoped fix for a blocking bug found during the exercise).

## 2026-06-09 — Phase 14 gate (run-gate.md codex invocation, first real execution)

Loop 058 / the Phase 14 gate was the first time the codex-wired `run-gate.md` was
executed for real (Phase 12/13 gated it as a document only). Four defects surfaced and
were fixed in the same gate session (source + byte-identical runtime copy):

1. **Invalid flag.** `codex exec --read-only` errors in codex-cli 0.124.0
   (`unexpected argument '--read-only'`). Correct flag is `-s read-only`
   (`--sandbox read-only`). FIXED.
2. **Ambiguous stdout parsing.** `codex exec` streams a full reasoning transcript
   (observed 12 fenced json blocks, 8 distinct) → `extract_and_validate` correctly
   returns ambiguous/None. The single clean verdict is the agent's LAST message; capture
   it with `-o <file>` and parse that file, not stdout. FIXED.
3. **stdin block.** Backgrounded `codex exec` hung on "Reading additional input from
   stdin..."; needs `</dev/null`. FIXED.
4. **Auth preflight false-negative on Windows.** Preflight checked only
   `~/.codex/auth.json`, but git-bash `HOME` here is `/m/` while codex stores auth at
   `$USERPROFILE/.codex/auth.json` — preflight would have falsely degraded (skipped codex)
   even though codex was authenticated. Added a `$USERPROFILE/.codex/auth.json` fallback.
   FIXED.

Also: a *criterion-scoping* gap (not a code bug). A phase success criterion asked codex to
confirm a `backend:codex` verdict EXISTS in `gate-verdicts/`, but the isolation rule
forbids codex reading that directory, so codex marked it `failed` (false-negative). The
isolation rule is correct and unchanged; instead the run-gate codex prompt now instructs
codex to mark gate-verdicts-existence criteria `not_applicable` (main-thread-verified) and
sandbox-blocked test criteria `deferred`, not `failed`. Recorded as the Phase 14 gate
override rationale in `history.jsonl`.
