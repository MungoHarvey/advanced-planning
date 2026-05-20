# Phase 11 — Ralph Loops (042–046)

Friction Remediation & v0.x Pre-Release. Source plan:
`.advanced-plans/phases/phase-11/plan.md`. Design:
`.advanced-plans/specs/2026-05-20-phase-11-friction-remediation-design.md`.

Sequencing: 042 → 043 → 044 → 045 → 046 (strictly sequential; 044 audit
depends on 042/043 edits being settled; 046 verifies all and cuts the tag).

---

```yaml
---
name: "ralph-loop-042"
task_name: "Constraints + Schema Cleanup"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "core/constraints.json + platforms/python/ast_check.py created; CI yml updated to module invocation; complexity field and Haiku tier removed from all files; CLAUDE.md Key Constraints references core/constraints.json; 168 tests pass, AST check NONE."
  failed: ""
  needed: "Execute Loop 043: create schema-design and permission-config skill stubs, install script updates, worker preflight check, and agent/command fixes."

todos:
  - id: "loop-042-1"
    content: "Create core/constraints.json with the canonical zero-dep allow-set (json, pathlib, re, datetime, typing, os, sys, tempfile, textwrap, argparse, asyncio); __future__ explicitly excluded; include a schema_version field"
    skill: "schema-design"
    agent: "NA"
    outcome: "core/constraints.json exists; valid JSON; lint passes; allow-set matches CLAUDE.md Key Constraints"
    status: completed
    priority: high
  - id: "loop-042-2"
    content: "Create platforms/python/ast_check.py (stdlib-only) exposing load_allowed_imports(), check_file(path) -> list[Violation], and CLI mode via python -m platforms.python.ast_check <paths...>"
    skill: "NA"
    agent: "NA"
    outcome: "Module exists; CLI on a clean file exits 0; CLI on a fixture with __future__ exits non-zero and names the violating file"
    status: completed
    priority: high
  - id: "loop-042-3"
    content: "Write platforms/python/tests/test_ast_check.py: parses fixture JSON, happy-path file with only allowed imports, violation fixture with __future__ produces non-empty result, round-trip test that load_allowed_imports() equals the JSON content"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Test file exists; pytest passes; coverage includes happy + violation + round-trip"
    status: completed
    priority: high
  - id: "loop-042-4"
    content: "Update .github/workflows/ci.yml: replace inline AST checker python with python -m platforms.python.ast_check platforms/python/ (excluding tests/)"
    skill: "permission-config"
    agent: "NA"
    outcome: "CI yml diff shows inline python block replaced by module invocation; YAML valid"
    status: completed
    priority: high
  - id: "loop-042-5"
    content: "Drop complexity: field everywhere — remove from CLAUDE.md text; remove the Haiku row from CLAUDE.md Model Tiers table entirely; sweep .advanced-plans/phases/** and core/schemas/** for stale complexity: lines and remove"
    skill: "NA"
    agent: "NA"
    outcome: "grep -r 'complexity:' .advanced-plans/phases/ core/schemas/ CLAUDE.md returns no matches; Model Tiers table has no Haiku row"
    status: completed
    priority: high
  - id: "loop-042-6"
    content: "Update CLAUDE.md Key Constraints section to reference core/constraints.json as the authoritative source of the allow-set"
    skill: "NA"
    agent: "NA"
    outcome: "CLAUDE.md text reads 'See core/constraints.json' (or similar) in Key Constraints; allow-set list either points-to or mirrors the JSON"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [first loop of Phase 11 — no prior handoff]
  Failed: []
  Needed: []

  ## Objective
  Establish core/constraints.json + platforms/python/ast_check.py as the single
  source of truth for the zero-dep AST allow-set, and drop the complexity: field
  and Haiku tier everywhere. Phase 11 scope items S1 + S2.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-042"

  ## Success criteria
  - [ ] core/constraints.json valid + lint passes
  - [ ] platforms/python/ast_check.py module + CLI mode work
  - [ ] tests/test_ast_check.py passes (happy + violation + round-trip)
  - [ ] CI workflow shells out to the module (no inline Python checker)
  - [ ] Zero complexity: matches anywhere in .advanced-plans/phases/, core/schemas/, CLAUDE.md
  - [ ] CLAUDE.md Model Tiers table no longer has a Haiku row
  - [ ] CLAUDE.md Key Constraints references core/constraints.json as authoritative
  - [ ] All existing tests still pass; AST check NONE

  ## Required skills
  - `schema-design`: constraints.json frontmatter / schema_version
  - `verification-before-completion`: round-trip test + AST-on-self
  - `permission-config`: CI workflow edit

  ## Inputs
  - CLAUDE.md (current allow-set in Key Constraints section)
  - .github/workflows/ci.yml (current inline AST checker)
  - .advanced-plans/specs/2026-05-20-phase-11-friction-remediation-design.md (S1, S2)

  ## Expected outputs
  - core/constraints.json
  - platforms/python/ast_check.py
  - platforms/python/tests/test_ast_check.py
  - Edited .github/workflows/ci.yml
  - Edited CLAUDE.md (no complexity, no Haiku row, Key Constraints points to JSON)

  ## Constraints
  - Standard library only in ast_check.py; CI AST checker enforces
  - ASCII-only console output (Windows cp1252 safe)
  - LOCKED files MUST remain byte-unchanged: docs/phase-complete.schema.md,
    docs/phase-manifest-entry.schema.md, docs/phase-handoff.schema.md,
    .advanced-plans/phases/phase-9/complete.md
  - Do NOT add Haiku back under a different name; the tier is removed

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-042 — constraints + schema cleanup"
  2. Update handoff_summary.done with one sentence
  3. Mark all todos completed
---
```

---

```yaml
---
name: "ralph-loop-043"
task_name: "Skills + Agents"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "core/skills/schema-design/SKILL.md and core/skills/permission-config/SKILL.md created; install scripts updated with skill comment; worker preflight protocol added to both worker.md files; run-gate state-bus contract clarified; plan-subagent-identification NA default + Reserved Values added to core/ and ~/.claude/ copies; no agent: ralph-loop-worker todo assignments found in any phase; 168 tests pass, AST check NONE."
  failed: ""
  needed: "Execute Loop 044: migration-consistency audit, path-conventions.md, /next-loop resume-detection, orchestrator stale-state cleanup."

todos:
  - id: "loop-043-1"
    content: "Create core/skills/schema-design/SKILL.md with mandatory sections (frontmatter name/description; ## When to Use; ## Process; ## Output Format); content describes producing schema docs (frontmatter + body sections + validation checklist) consistent with docs/phase-handoff.schema.md style"
    skill: "schema-design"
    agent: "NA"
    outcome: "SKILL.md exists at core/skills/schema-design/ with frontmatter + 3 mandatory sections; passes the skill-format check"
    status: completed
    priority: high
  - id: "loop-043-2"
    content: "Create core/skills/permission-config/SKILL.md similarly; content describes editing hooks.json / settings.json / agent tool sets and verifying that edits land"
    skill: "schema-design"
    agent: "NA"
    outcome: "SKILL.md exists at core/skills/permission-config/ with frontmatter + 3 mandatory sections"
    status: completed
    priority: high
  - id: "loop-043-3"
    content: "Update setup/claude-code/install.sh and install.ps1 to copy/symlink the two new skills into .claude/skills/ at install time"
    skill: "permission-config"
    agent: "NA"
    outcome: "Install scripts include schema-design and permission-config in their skill-copy step; manual dry-run on a temp project shows the skills land at .claude/skills/"
    status: completed
    priority: high
  - id: "loop-043-4"
    content: "Add worker preflight skill check to core/agents/ralph-loop-worker.md: at the start of each todo, resolve the declared skill: field; if not found at core/skills/<name>/SKILL.md, .claude/skills/<name>/SKILL.md, or ~/.claude/skills/<name>/SKILL.md, log WARN to stdout + execution.log and proceed (do NOT halt)"
    skill: "NA"
    agent: "NA"
    outcome: "Worker agent definition contains the preflight protocol; warning format is 'WARN: skill <name> declared by todo <id> but not installed; proceeding without skill injection'"
    status: completed
    priority: high
  - id: "loop-043-5"
    content: "Edit platforms/claude-code/agents/phase-goals-agent.md to add Write to the tools field (Read, Glob, Grep, Write). Mirror the change in any other agent-registry file if present"
    skill: "permission-config"
    agent: "NA"
    outcome: "phase-goals-agent.md tools field includes Write; git diff shows the single-line change"
    status: completed
    priority: high
  - id: "loop-043-6"
    content: "Update platforms/claude-code/commands/run-gate.md to remove the 'expect text-only verdict' workaround prose; document that gate agents persist their own verdicts per the state-bus contract"
    skill: "command-rewriting"
    agent: "NA"
    outcome: "run-gate.md no longer instructs the main thread to persist verdicts on behalf of phase-goals-agent (or any other agent)"
    status: completed
    priority: medium
  - id: "loop-043-7"
    content: "Update plan-subagent-identification SKILL.md (project core/ + user runtime) so the default for a todo with no clear specialised agent is agent: NA, NOT agent: ralph-loop-worker; add an explicit Reserved Values note that ralph-loop-worker is the loop executor and MUST NOT appear on individual todos"
    skill: "docs-rewrite"
    agent: "NA"
    outcome: "Skill text documents NA as default and reserves ralph-loop-worker; both project and ~/.claude/ copies updated (or the project core/ canonical version, with note to re-install)"
    status: completed
    priority: high
  - id: "loop-043-8"
    content: "Sweep .advanced-plans/phases/** for agent: ralph-loop-worker on individual todos and rewrite to agent: NA (Phase 8 Loop 027 is the known offender; check Phase 9/10 for any additional cases)"
    skill: "NA"
    agent: "NA"
    outcome: "grep -r 'agent: ralph-loop-worker' .advanced-plans/phases/ returns no matches"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Install the two missing skill stubs (schema-design, permission-config); add a
  worker preflight check that warns on unresolved skills without halting; widen
  phase-goals-agent to include Write; fix plan-subagent-identification default
  and sweep existing offenders. Phase 11 scope items S3, S4, S5 (in-file edit
  only — E2E verification deferred to Loop 046), S6.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-043"

  ## Success criteria
  - [ ] Both skill SKILL.md files exist with frontmatter + 3 mandatory sections
  - [ ] install.sh + install.ps1 include the new skills
  - [ ] Worker agent has preflight skill-check + non-halting warning protocol
  - [ ] phase-goals-agent.md has Write in tools (in-file edit confirmed)
  - [ ] /run-gate no longer documents the text-only workaround
  - [ ] plan-subagent-identification documents NA default + Reserved Values
  - [ ] grep -r 'agent: ralph-loop-worker' .advanced-plans/phases/ is empty
  - [ ] AST check NONE; pytest passes

  ## Required skills
  - `schema-design`: building the two SKILL.md stubs
  - `permission-config`: install script + agent tool-set edits
  - `command-rewriting`: /run-gate update
  - `docs-rewrite`: plan-subagent-identification

  ## Inputs
  - core/skills/ (existing skill layout for reference)
  - platforms/claude-code/agents/phase-goals-agent.md
  - platforms/claude-code/agents/code-review-agent.md (reference for Write tool form)
  - platforms/claude-code/commands/run-gate.md
  - .advanced-plans/phases/ (sweep for ralph-loop-worker assignments)

  ## Expected outputs
  - core/skills/schema-design/SKILL.md
  - core/skills/permission-config/SKILL.md
  - Edited install.sh + install.ps1
  - Edited core/agents/ralph-loop-worker.md (or platforms mirror)
  - Edited platforms/claude-code/agents/phase-goals-agent.md
  - Edited platforms/claude-code/commands/run-gate.md
  - Edited plan-subagent-identification SKILL.md
  - Phase plan loop files with agent: NA replacing ralph-loop-worker

  ## Constraints
  - Note: S5 Write-tool runtime-propagation is verified in Loop 046 E2E.
    This loop performs the in-file edit only. If Loop 046 confirms the edit
    is a no-op at runtime, Phase 11 falls back to documenting the workaround
    in /run-gate (per spec success criterion 5).
  - LOCKED files MUST remain byte-unchanged
  - ASCII-only output

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-043 — skills + agents"
  2. Update handoff_summary
  3. Mark all todos completed
---
```

---

```yaml
---
name: "ralph-loop-044"
task_name: "Migration Audit + Durability"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "docs/path-conventions.md created; migration audit complete (KEEP/REWRITE disposition applied to docs/); /next-loop Step 3a resume-detection inserted; detect_mid_loop_death() + archive_cross_phase_state() added to state_manager.py; 16 new tests pass (7 resume + 9 cleanup); ralph-orchestrator Step 0 stale-state cleanup protocol added to both core/ and platforms/ agent files; CLAUDE.md links to path-conventions.md; 184 tests pass, AST NONE."
  failed: ""
  needed: "Execute Loop 045: dogfood self-install (idempotent install.sh/ps1, CONTRIBUTING.md, install idempotency test)."

todos:
  - id: "loop-044-1"
    content: "Author docs/path-conventions.md: canonical path map (source repo: platforms/claude-code/, core/, .advanced-plans/; installed: .claude/runtime + .advanced-plans/ data); note which path tokens are deprecated (plans/, .claude/state/, plans/gate-verdicts/, /new-loop); reference from CLAUDE.md Runtime Directory section"
    skill: "schema-design"
    agent: "NA"
    outcome: "docs/path-conventions.md exists; CLAUDE.md Runtime Directory section links to it"
    status: completed
    priority: high
  - id: "loop-044-2"
    content: "Migration-consistency audit pass: grep platforms/claude-code/commands/**, platforms/claude-code/agents/**, core/skills/**, docs/** for occurrences of plans/, .claude/plans/, .claude/state/, plans/gate-verdicts/, /new-loop; for each occurrence, decide case-by-case (keep legitimate runtime .claude/ references; rewrite stale data references to .advanced-plans/)"
    skill: "NA"
    agent: "NA"
    outcome: "Audit table in the loop-044 commit message lists every match with disposition (keep/rewrite); offenders rewritten in-place"
    status: completed
    priority: high
  - id: "loop-044-3"
    content: "Add /next-loop resume-detection step (Step 3a, before orchestrator spawn): check if loop-ready.json mtime > loop-complete.json mtime AND working tree is dirty; if so, invoke resume-review skill and require operator acknowledgment before continuing"
    skill: "command-rewriting"
    agent: "NA"
    outcome: "platforms/claude-code/commands/next-loop.md has the new step inserted at the correct position; clean state still passes through unchanged"
    status: completed
    priority: high
  - id: "loop-044-4"
    content: "Write IRON-RULE regression test for S8: fixture creates loop-ready.json with mtime newer than loop-complete.json + a dirty working tree; assert /next-loop invokes resume-review before spawning orchestrator (test via platforms/python/test_next_loop_resume.py or similar shim — implement the assert mechanism that fits the existing test layout)"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Regression test exists and passes; documents the Loop-035 failure mode it guards against"
    status: completed
    priority: high
  - id: "loop-044-5"
    content: "Update core/agents/ralph-orchestrator.md to add stale-state cleanup at startup: read current phase from PLANNING.md frontmatter; compare to phase field in existing loop-ready.json; if mismatch, archive both loop-ready.json and loop-complete.json to .advanced-plans/state/archive/<old-phase>-<timestamp>.json before writing new ones"
    skill: "NA"
    agent: "NA"
    outcome: "Orchestrator agent definition contains the cleanup protocol with explicit archive path; archive dir created if not present"
    status: completed
    priority: high
  - id: "loop-044-6"
    content: "Write test for orchestrator stale-state cleanup: fixture with cross-phase loop-ready.json; assert archive directory contains the moved file and the new orchestrator startup wrote fresh files"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Test exists and passes; archived file path matches the documented format"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Migration-consistency audit: write the canonical path map and rewrite any
  stale directives. Add worker durability: /next-loop detects mid-loop death
  (loop-ready newer than loop-complete + dirty) and orchestrator archives
  stale cross-phase state. Phase 11 scope items S7, S8, S9.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-044"

  ## Success criteria
  - [ ] docs/path-conventions.md exists + linked from CLAUDE.md
  - [ ] Audit table in commit message; all stale directives rewritten
  - [ ] /next-loop has Step 3a resume-detection
  - [ ] IRON-RULE regression test for S8 passes
  - [ ] ralph-orchestrator has stale-state cleanup with archive dir
  - [ ] Stale-state cleanup test passes
  - [ ] AST check NONE; pytest passes

  ## Required skills
  - `schema-design`: docs/path-conventions.md
  - `command-rewriting`: /next-loop step insertion
  - `verification-before-completion`: regression tests

  ## Inputs
  - platforms/claude-code/commands/**, agents/**, core/skills/**, docs/**
  - .advanced-plans/specs/2026-05-20-phase-11-friction-remediation-design.md
    (S7 reframed, S8 IRON-RULE, S9 cleanup protocol)

  ## Expected outputs
  - docs/path-conventions.md
  - Edited CLAUDE.md (Runtime Directory section linking the new doc)
  - Edits to any files identified by the audit
  - Edited platforms/claude-code/commands/next-loop.md
  - Edited core/agents/ralph-orchestrator.md
  - Regression tests (S8 + S9 fixtures)

  ## Constraints
  - LOCKED files MUST remain byte-unchanged
  - ASCII-only output
  - Audit must NOT delete legitimate runtime .claude/ references in installed-project context

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-044 — migration audit + durability"
  2. Update handoff_summary
  3. Mark all todos completed
---
```

---

```yaml
---
name: "ralph-loop-045"
task_name: "Dogfood Self-Install"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-045-1"
    content: "Update setup/claude-code/install.sh: add idempotent skip-data-scaffold check (if .advanced-plans/ exists, preserve it; never overwrite); add self-install detection (if --project resolves to git root of this repo, symlink rather than copy runtime dirs); skip .claude/commands/, .claude/skills/, .claude/agents/, .claude/schemas/ copy if symlink target equals source"
    skill: "permission-config"
    agent: "NA"
    outcome: "install.sh script with idempotent guards; dry-run on a temp dir with existing .advanced-plans/ preserves it; dry-run on source repo creates .claude/ symlinks pointing at platforms/claude-code/"
    status: pending
    priority: high
  - id: "loop-045-2"
    content: "Mirror the changes to setup/claude-code/install.ps1: same idempotent guards; symlink via New-Item -ItemType Junction (Windows-safe equivalent)"
    skill: "permission-config"
    agent: "NA"
    outcome: "install.ps1 parallels install.sh behaviour; dry-run on Windows preserves existing .advanced-plans/ and creates junctions"
    status: pending
    priority: high
  - id: "loop-045-3"
    content: "Write CONTRIBUTING.md (new) with a Dev-Mode section documenting: how to self-install in the source repo; what gets symlinked vs copied; expected behaviour with existing .advanced-plans/; quick verification step (running /loop-status)"
    skill: "docs-rewrite"
    agent: "NA"
    outcome: "CONTRIBUTING.md exists with the dev-mode section; CLAUDE.md Architecture section cross-references it"
    status: pending
    priority: medium
  - id: "loop-045-4"
    content: "Unit test for the install idempotency: temp dir fixture with a pre-existing .advanced-plans/ tree; run install; assert .advanced-plans/ content byte-unchanged and .claude/ populated"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Test exists; passes; covers both Unix and (skip if not on Windows) PowerShell paths"
    status: pending
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Make install.sh and install.ps1 idempotent over existing .advanced-plans/ data
  and able to self-install in the framework's source repo. Document dev-mode in
  CONTRIBUTING.md. Phase 11 scope item S10.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-045"

  ## Success criteria
  - [ ] install.sh has idempotent skip-data-scaffold + self-install detection
  - [ ] install.ps1 mirrors the changes (junctions on Windows)
  - [ ] CONTRIBUTING.md documents dev-mode invocation
  - [ ] Unit test for install idempotency passes
  - [ ] LOCKED .advanced-plans/phases/phase-9/complete.md byte-unchanged after a dry-run install
  - [ ] AST check NONE; pytest passes

  ## Required skills
  - `permission-config`: install script edits
  - `docs-rewrite`: CONTRIBUTING.md
  - `verification-before-completion`: idempotency test

  ## Inputs
  - setup/claude-code/install.sh (current)
  - setup/claude-code/install.ps1 (current)

  ## Expected outputs
  - Edited install.sh and install.ps1
  - CONTRIBUTING.md (new)
  - Unit test for idempotency

  ## Constraints
  - Install script MUST NEVER overwrite an existing .advanced-plans/ tree
  - Symlink behaviour on Windows uses junctions (not soft links)
  - LOCKED files MUST remain byte-unchanged
  - The actual E2E run (install.sh against this repo) happens in Loop 046;
    this loop only verifies behaviour with unit tests + dry runs

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-045 — dogfood self-install"
  2. Update handoff_summary
  3. Mark all todos completed
---
```

---

```yaml
---
name: "ralph-loop-046"
task_name: "Verification + v0.11.0 Release"
max_iterations: 3
on_max_iterations: checkpoint

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-046-1"
    content: "E2E for S5 (phase-goals-agent Write tool): spawn phase-goals-agent in a dry-run gate context with sentinel active; assert the verdict JSON file is created BY the agent (not by main thread) at the expected path. If the Write tool is unavailable at runtime, log the failure, invoke the fallback path: update /run-gate to formally document the main-thread persist-on-behalf workaround as the supported contract; mark the friction-log entry partially-resolved (upstream-blocked)"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Either: (a) PRIMARY path — agent writes the verdict file directly, /run-gate workaround prose stays removed; OR (b) FALLBACK path — /run-gate documents the workaround as the contract, friction-log entry marked upstream-blocked"
    status: pending
    priority: high
  - id: "loop-046-2"
    content: "E2E for S8 (resume-detection): create the regression fixture (loop-ready.json mtime newer than loop-complete.json + dirty tree); invoke /next-loop; assert resume-review skill invocation precedes orchestrator spawn"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Test run captured in commit message; resume-detection observed firing in the expected position"
    status: pending
    priority: high
  - id: "loop-046-3"
    content: "E2E for S10 (self-install on this repo): run setup/claude-code/install.sh --project . on the source repo; verify .advanced-plans/ byte-unchanged via git diff; verify .claude/commands/, .claude/skills/, .claude/agents/, .claude/schemas/ populated with symlinks; run /loop-status and assert exit 0"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "Install completes; data preserved; runtime dirs populated; /loop-status exits clean; commit captures the verification output"
    status: pending
    priority: high
  - id: "loop-046-4"
    content: "Create VERSION file at repo root containing the single line 0.11.0"
    skill: "NA"
    agent: "NA"
    outcome: "VERSION exists; matches /^0\\.11\\.0$/"
    status: pending
    priority: medium
  - id: "loop-046-5"
    content: "Create CHANGELOG.md (Keep-a-Changelog format) with sections backfilled from PLANS-INDEX.md v0.6 through v0.11; each version section names the phase, completion date, and loop count matching PLANS-INDEX; v0.11.0 section includes the breaking-change note (complexity field removed, Haiku tier dropped) and lists the 9 friction entries resolved"
    skill: "docs-rewrite"
    agent: "NA"
    outcome: "CHANGELOG.md exists; one heading per PLANS-INDEX phase from v0.6; loop counts match; v0.11.0 section complete"
    status: pending
    priority: high
  - id: "loop-046-6"
    content: "Update README.md Installation section to reference VERSION; add a brief 'Releases' subsection pointing at GitHub Releases and the CHANGELOG"
    skill: "docs-rewrite"
    agent: "NA"
    outcome: "README.md mentions VERSION and CHANGELOG; install instructions reference the tag"
    status: pending
    priority: medium
  - id: "loop-046-7"
    content: "Final verification gate: python -m pytest platforms/python/tests/ -v (all green); python -m platforms.python.ast_check platforms/python/ (NONE); grep guards (no complexity:, no agent: ralph-loop-worker on todos); LOCKED files git diff empty"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "All five checks pass; output captured in commit message; ready for gate review"
    status: pending
    priority: high
  - id: "loop-046-8"
    content: "Post-gate-pass actions (DO NOT execute until /run-gate returns PASS): cut annotated git tag v0.11.0 with message sourced from CHANGELOG.md v0.11.0 section; push origin main + tag; draft GitHub Release body from the CHANGELOG section; create release via gh release create v0.11.0 --notes-file <(extract CHANGELOG section)"
    skill: "NA"
    agent: "NA"
    outcome: "Tag exists locally + on origin; GitHub Release page exists with the CHANGELOG-sourced body; remote in sync"
    status: pending
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Run the three E2E checks bundled by the spec Verification Plan (S5, S8, S10),
  bootstrap the version scheme, and prepare the v0.11.0 release. The tag cut
  and remote push happen ONLY after /run-gate returns PASS — never inside this
  loop. Phase 11 scope item S11 + Verification Plan E2Es.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-046"

  ## Success criteria
  - [ ] S5 E2E: PRIMARY (agent writes verdict) OR FALLBACK (workaround documented) landed
  - [ ] S8 E2E: resume-detection observed firing on fixture
  - [ ] S10 E2E: self-install on this repo preserves data + populates .claude/
  - [ ] VERSION file = 0.11.0
  - [ ] CHANGELOG.md complete (v0.6 through v0.11; matching loop counts)
  - [ ] README.md updated
  - [ ] Final verification gate passes (pytest, AST, grep guards, LOCKED diff)
  - [ ] All gate-review prerequisites green; phase ready for /run-gate
  - [ ] (POST-GATE only) v0.11.0 tag exists locally + on origin; GitHub Release published

  ## Required skills
  - `verification-before-completion`: all three E2E checks + final gate
  - `docs-rewrite`: CHANGELOG + README

  ## Inputs
  - All Phase 11 prior-loop outputs (042-045)
  - .advanced-plans/PLANS-INDEX.md (source for CHANGELOG backfill)
  - .advanced-plans/specs/2026-05-20-phase-11-friction-remediation-design.md (Verification Plan)

  ## Expected outputs
  - VERSION
  - CHANGELOG.md
  - Edited README.md
  - E2E verification artefacts captured in commit messages
  - (Post-gate) annotated tag v0.11.0 + GitHub Release

  ## Constraints
  - DO NOT cut the v0.11.0 tag inside this loop; tag cut is the post-gate-pass
    action. The loop ends with "ready for /run-gate" state, not "tagged".
  - LOCKED files MUST remain byte-unchanged
  - If S5 E2E shows the Write tool didn't propagate, take the FALLBACK path
    cleanly (per spec success criterion 5); do NOT keep trying to make
    the primary path work
  - If S8 or S10 E2E fails, the loop fails — those have no fallback

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-046 — verification + v0.11.0 prepared"
  2. Update handoff_summary
  3. Mark all todos completed
  4. Print: "Phase 11 ready for /run-gate. After PASS, execute todo loop-046-8."
---
```
