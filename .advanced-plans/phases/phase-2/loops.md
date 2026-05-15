# Phase 2 — Ralph Loops: Claude Code Adapter

Loops 005–007 wrap the platform-independent core into a fully-installable Claude Code adapter with slash commands, agent files, hooks, and an end-to-end verified two-agent execution cycle.

---

## ralph-loop-005: Commands & Install

```yaml
name: "ralph-loop-005"
task_name: "Commands & Install"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "6 slash command files, install.sh (3-mode), and CLAUDE.md template created in platforms/claude-code/."
  failed: ""
  needed: ""

todos:
  - id: "loop-005-1"
    content: "Create new-phase.md command that runs the 5-skill planning pipeline end-to-end with targeted skill loading"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/claude-code/commands/new-phase.md exists with allowed-tools frontmatter, references core skills via .claude/skills/ paths, and documents all 12 pipeline steps"
    status: completed
    priority: high

  - id: "loop-005-2"
    content: "Create new-loop.md command that decomposes a phase plan into ralph loops using the ralph-loop-planner skill"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/claude-code/commands/new-loop.md exists with allowed-tools frontmatter, finds phase plan by argument or most-recent, and saves output to .claude/plans/"
    status: completed
    priority: high

  - id: "loop-005-3"
    content: "Create next-loop.md command implementing the full 10-step two-agent cycle with loop-ready.json and loop-complete.json handoff"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/claude-code/commands/next-loop.md exists with the complete spawn-orchestrator → read-ready → spawn-worker → read-complete → update-state cycle"
    status: completed
    priority: high

  - id: "loop-005-4"
    content: "Create loop-status.md, check-execution.md, and model-check.md diagnostic commands"
    skill: "NA"
    agent: "NA"
    outcome: "All three diagnostic commands exist in platforms/claude-code/commands/ with correct frontmatter and matching their v8 originals updated for the v8-release path conventions"
    status: completed
    priority: high

  - id: "loop-005-5"
    content: "Create install.sh supporting --project, --global, and --reference modes"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/claude-code/install.sh is executable, handles --project/--global/--reference flags, copies or symlinks core/skills and adapter files to the correct target directories, and prints usage on --help"
    status: completed
    priority: high

  - id: "loop-005-6"
    content: "Create claude-md-template.md with the Planning State section and Skills/Subagents Available sections"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/claude-code/claude-md-template.md exists with the complete Planning State YAML blocks, Completed Phases table, Learnings section, and Skills/Subagents Available sections"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: Phase 1 complete — core schemas, 5 skills, 2 agent role definitions, state bus protocol all in advanced-planning/core/.
  Failed:
  Needed:

  ## Objective
  Build the 6 slash commands, install script, and CLAUDE.md template for the Claude Code adapter, referencing core skills rather than duplicating them.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-005 commands and install"

  ## Success criteria
  - [ ] 6 command files exist in platforms/claude-code/commands/ with correct frontmatter
  - [ ] Commands reference .claude/skills/ paths (installed location), not core/skills/
  - [ ] next-loop.md implements the full 10-step two-agent cycle
  - [ ] install.sh handles --project, --global, --reference modes
  - [ ] claude-md-template.md contains the complete Planning State section

  ## Required skills
  - None (command files are Claude Code markdown; install.sh is standard bash)

  ## Inputs
  - v8 prototype commands: advanced-planning/platforms/claude-code/commands/
  - v8 prototype settings: advanced-planning/platforms/claude-code/settings.json
  - Core skills: advanced-planning/core/skills/
  - Core agents: advanced-planning/core/agents/

  ## Expected outputs
  - platforms/claude-code/commands/new-phase.md
  - platforms/claude-code/commands/new-loop.md
  - platforms/claude-code/commands/next-loop.md
  - platforms/claude-code/commands/loop-status.md
  - platforms/claude-code/commands/check-execution.md
  - platforms/claude-code/commands/model-check.md
  - platforms/claude-code/install.sh
  - platforms/claude-code/claude-md-template.md

  ## Constraints
  - Commands must reference .claude/skills/ not core/skills/ (the installed path)
  - No skill content should be duplicated into command files
  - install.sh must be POSIX sh compatible (not bash-specific) for cross-platform use

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-005 — 6 commands + install.sh + CLAUDE.md template"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
```

## Overview

Produce the six slash commands and installation tooling that make the planning system operable in Claude Code. Commands are thin wrappers that load core skills by path and map Claude Code's invocation pattern to the core skill process — no duplication.

## Success Criteria

- ✓ 6 command files with correct `allowed-tools` frontmatter
- ✓ Commands reference `.claude/skills/` (installed path), not `core/skills/`
- ✓ `/next-loop` implements the full 10-step two-agent cycle
- ✓ `install.sh` supports `--project`, `--global`, `--reference` modes
- ✓ `claude-md-template.md` includes all Planning State YAML blocks

## Skills Required

### Broad (from phase plan):
- `skill-creator`: Adapting core skills into Claude Code command format

### Specific (refined for this loop):
- None — command files follow a simple markdown+frontmatter pattern

### Discovered:
- None

## Inputs

| Input | Source | Format |
|-------|--------|--------|
| v8 commands | `advanced-planning/platforms/claude-code/commands/` | Markdown |
| v8 settings | `advanced-planning/platforms/claude-code/settings.json` | JSON |
| Core skills directory | `advanced-planning/core/skills/` | SKILL.md files |

## Outputs

| Output | Location |
|--------|----------|
| 6 slash commands | `platforms/claude-code/commands/` |
| Install script | `platforms/claude-code/install.sh` |
| CLAUDE.md template | `platforms/claude-code/claude-md-template.md` |

## Dependencies
- Loop 001–004 (Phase 1): core skills must exist before commands can reference them

## Complexity
**Scope**: Medium — 8 files, mostly migration with path-convention updates
**Estimated effort**: 2–3 hours
**Key challenges**: Ensuring install.sh handles edge cases (existing files, missing git, no write permission)

---

## ralph-loop-006: Agents & Settings

```yaml
name: "ralph-loop-006"
task_name: "Agents & Settings"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "3 agent files, settings.json, and adapter README created in platforms/claude-code/."
  failed: ""
  needed: ""

todos:
  - id: "loop-006-1"
    content: "Create ralph-orchestrator.md agent wrapping the core orchestrator role with Claude Code frontmatter"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/claude-code/agents/ralph-orchestrator.md exists with name/description/model/tools/skills frontmatter, references core/agents/orchestrator.md for the protocol, and adds Claude Code-specific path conventions"
    status: completed
    priority: high

  - id: "loop-006-2"
    content: "Create ralph-loop-worker.md agent wrapping the core worker role with Claude Code frontmatter and TodoWrite in tools"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/claude-code/agents/ralph-loop-worker.md exists with model: haiku, TodoWrite in tools list, references core/agents/worker.md for the protocol, and specifies the .claude/skills/ path for skill injection"
    status: completed
    priority: high

  - id: "loop-006-3"
    content: "Create analysis-worker.md as a general-purpose bounded execution agent for delegated todos"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/claude-code/agents/analysis-worker.md exists with model: haiku, tools covering Read/Write/Edit/Bash/Glob, and a clear description of when to delegate vs keep inline"
    status: completed
    priority: medium

  - id: "loop-006-4"
    content: "Create settings.json with full permissions whitelist and all six hook types logging to .claude/logs/execution.log"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/claude-code/settings.json is valid JSON with permissions.allow array covering all tools, and hooks for SessionStart/End, SubagentStart/Stop, and PostToolUse (TodoWrite/Bash/Write/Edit)"
    status: completed
    priority: high

  - id: "loop-006-5"
    content: "Create adapter README.md with installation instructions, quick-start (5-minute setup), command reference, and troubleshooting"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/claude-code/README.md exists with install instructions for all three modes, a quick-start walkthrough covering new-phase through next-loop, a command reference table, and a troubleshooting section covering the top 3 failure modes"
    status: completed
    priority: high

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Build the three agent files, settings.json hooks, and adapter README to complete the Claude Code adapter.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-006 agents and settings"

  ## Success criteria
  - [ ] ralph-orchestrator.md has model: sonnet and references core orchestrator protocol
  - [ ] ralph-loop-worker.md has model: haiku and TodoWrite in tools
  - [ ] analysis-worker.md is a general delegation agent at model: haiku
  - [ ] settings.json is valid JSON with all hooks wired to execution.log
  - [ ] README.md has 5-minute quick-start and command reference table

  ## Required skills
  - None (agent files and settings.json follow established Claude Code patterns)

  ## Inputs
  - v8 prototype agents: advanced-planning/platforms/claude-code/agents/
  - v8 settings: advanced-planning/platforms/claude-code/settings.json
  - Core agent role definitions: advanced-planning/core/agents/

  ## Expected outputs
  - platforms/claude-code/agents/ralph-orchestrator.md
  - platforms/claude-code/agents/ralph-loop-worker.md
  - platforms/claude-code/agents/analysis-worker.md
  - platforms/claude-code/settings.json
  - platforms/claude-code/README.md

  ## Constraints
  - Agent frontmatter must use Claude Code field names: name, description, model, tools, skills
  - settings.json must be valid JSON (validate before completing)
  - README must be usable by a developer who has never seen this system before

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-006 — agents, settings.json, README created"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
```

## Overview

Create the Claude Code agent files with platform-specific frontmatter, the settings.json hooks, and the adapter README that makes the system accessible to new colleagues. The agents wrap the core role definitions with Claude Code's configuration format.

## Success Criteria

- ✓ `ralph-orchestrator.md` and `ralph-loop-worker.md` wrap their core counterparts correctly
- ✓ `settings.json` hooks cover all six event types
- ✓ `README.md` passes the colleague-ready criterion: a new developer can install and run `/loop-status` in 5 minutes

## Dependencies
- Loop 005: commands must exist before README references them

## Complexity
**Scope**: Low-Medium — 5 files; agent files are largely configuration wrapping
**Estimated effort**: 1–2 hours

---

## ralph-loop-007: End-to-End Verification

```yaml
name: "ralph-loop-007"
task_name: "End-to-End Verification"
max_iterations: 2
on_max_iterations: checkpoint

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-007-1"
    content: "Verify all adapter files exist and have correct structure by running a completeness scan"
    skill: "NA"
    agent: "NA"
    outcome: "find platforms/claude-code/ reports all 13 expected files; no empty files; all command .md files have frontmatter with allowed-tools; settings.json is valid JSON"
    status: pending
    priority: high

  - id: "loop-007-2"
    content: "Verify command files reference .claude/skills/ paths (not core/skills/) and no skill content is duplicated"
    skill: "NA"
    agent: "NA"
    outcome: "grep scan confirms zero occurrences of 'core/skills/' in any platforms/claude-code/commands/ file; all skill references use .claude/skills/"
    status: pending
    priority: high

  - id: "loop-007-3"
    content: "Verify install.sh is executable and --help output describes all three modes"
    skill: "NA"
    agent: "NA"
    outcome: "chmod +x install.sh succeeds; bash install.sh --help prints usage text describing --project, --global, and --reference modes without error"
    status: pending
    priority: high

  - id: "loop-007-4"
    content: "Trace the /next-loop cycle on paper: confirm loop-ready.json fields written by orchestrator are consumed by worker, and loop-complete.json fields match the state bus schema"
    skill: "NA"
    agent: "NA"
    outcome: "Written trace document confirms: loop-ready.json has all required fields per loop-ready.schema.json; loop-complete.json has all required fields per loop-complete.schema.json; handoff field names match handoff.schema.md (done/failed/needed)"
    status: pending
    priority: high

  - id: "loop-007-5"
    content: "Document any issues found during verification and either fix them or record them in a known-issues section of the adapter README"
    skill: "NA"
    agent: "NA"
    outcome: "Either: all issues fixed and verification re-run clean; OR: platforms/claude-code/README.md contains a Known Issues section listing unresolved items with workarounds"
    status: pending
    priority: medium

  - id: "loop-007-6"
    content: "Update PLANS-INDEX.md to mark Phase 2 complete and set next action to Phase 3"
    skill: "NA"
    agent: "NA"
    outcome: "PLANS-INDEX.md shows loops 005-007 as complete and Phase 2 status as complete; next action points to Phase 3"
    status: pending
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Verify the Claude Code adapter is complete, internally consistent, and colleague-ready before declaring Phase 2 done.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-007 end-to-end verification"

  ## Success criteria
  - [ ] All 13 adapter files exist and are non-empty
  - [ ] Command files reference .claude/skills/ not core/skills/
  - [ ] install.sh --help works without error
  - [ ] /next-loop cycle trace confirms state bus field consistency
  - [ ] Any issues are fixed or documented with workarounds

  ## Required skills
  - None (verification is scripted checks and manual trace)

  ## Inputs
  - All platforms/claude-code/ files
  - core/state/ schemas (for trace verification)
  - core/schemas/handoff.schema.md

  ## Expected outputs
  - Verification confirmation (all checks pass)
  - Known issues section in README (if any)
  - Updated PLANS-INDEX.md

  ## Constraints
  - on_max_iterations: checkpoint — partial verification findings have value; commit and surface if stuck
  - Do not declare Phase 2 complete if any critical file is missing or the state bus trace fails

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-007 — Phase 2 adapter verified"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
```

## Overview

Systematic verification that the Claude Code adapter is complete, consistent, and ready for a colleague to install and use. Covers file completeness, path convention correctness, install script execution, and a state bus trace to confirm the two-agent handoff is sound.

## Success Criteria

- ✓ 13 adapter files exist and are non-empty
- ✓ No `core/skills/` path references in command files
- ✓ `install.sh --help` executes without error
- ✓ State bus trace confirms `loop-ready.json` → worker → `loop-complete.json` field consistency

## Dependencies
- Loops 005 and 006 must be complete before verification can run

## Complexity
**Scope**: Low — scripted scans and manual trace; no new file creation
**Estimated effort**: 1 hour
