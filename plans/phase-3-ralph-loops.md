# Phase 3 — Ralph Loops: Cowork Adapter

Loops 008–009 wrap the platform-independent core into a Cowork adapter using a routing SKILL.md as the entry point, the Agent tool for two-agent spawning, and file-based snapshots replacing git checkpoints.

---

## ralph-loop-008: Routing SKILL & Agent Integration

```yaml
name: "ralph-loop-008"
task_name: "Routing SKILL & Agent Integration"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "Three Cowork adapter files created: platforms/cowork/SKILL.md (routing skill, 6 intents, 7-step loop cycle), platforms/cowork/agents/orchestrator-prompt.md (self-contained Sonnet prompt with loop-ready.json write contract), and platforms/cowork/agents/worker-prompt.md (self-contained Haiku prompt with targeted skill injection protocol and snapshot checkpoints). Zero .claude/ references confirmed."
  failed: ""
  needed: "Create platforms/cowork/checkpoint.sh (save/restore/list subcommands) and platforms/cowork/README.md for loop-009."

todos:
  - id: "loop-008-1"
    content: "Create platforms/cowork/SKILL.md as a routing skill with dispatch table mapping user intent to core planning skills and Agent tool invocations"
    skill: "skill-creator"
    agent: "NA"
    outcome: "platforms/cowork/SKILL.md exists with: frontmatter (name, description, model: opus), dispatch table covering all 6 intents (new phase, new loop, next loop, loop status, check execution, model check), and instructions for loading each core skill"
    status: completed
    priority: high

  - id: "loop-008-2"
    content: "Create platforms/cowork/agents/orchestrator-prompt.md as the full self-contained prompt passed to the Agent tool when spawning the orchestrator"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/cowork/agents/orchestrator-prompt.md exists with the complete orchestrator protocol, Cowork-specific path conventions (workspace folder, no .claude/ prefix), and the loop-ready.json write contract"
    status: completed
    priority: high

  - id: "loop-008-3"
    content: "Create platforms/cowork/agents/worker-prompt.md as the full self-contained prompt passed to the Agent tool when spawning the worker, including the targeted skill injection protocol"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/cowork/agents/worker-prompt.md exists with the complete worker protocol, targeted skill injection protocol (load SKILL.md per todo, unload between todos), TodoWrite integration, and snapshot checkpoint steps in place of git commits"
    status: completed
    priority: high

  - id: "loop-008-4"
    content: "Verify routing SKILL.md covers all core skill paths and that agent prompts use workspace-relative paths (not .claude/ prefixed paths)"
    skill: "NA"
    agent: "NA"
    outcome: "Zero occurrences of '.claude/' in any platforms/cowork/ file; all skill paths are workspace-relative; all six routing intents map to a defined action"
    status: completed
    priority: high



prompt: |
  ## Context from prior loop
  Done: Phase 2 complete — Claude Code adapter with 6 commands, 3 agents, settings.json, install.sh, and README fully verified.
  Failed:
  Needed:

  ## Objective
  Build the Cowork adapter's three core files: a routing skill that replaces slash commands, and two agent prompts that are passed directly to Cowork's Agent tool.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-008 cowork routing skill and agents"

  ## Success criteria
  - [ ] platforms/cowork/SKILL.md exists with dispatch table covering all 6 intents
  - [ ] platforms/cowork/agents/orchestrator-prompt.md contains the complete orchestrator protocol
  - [ ] platforms/cowork/agents/worker-prompt.md contains the targeted skill injection protocol
  - [ ] No .claude/ paths anywhere in platforms/cowork/

  ## Required skills
  - skill-creator: Building well-structured routing SKILL.md

  ## Inputs
  - Core agent roles: advanced-planning/core/agents/
  - Existing routing skill pattern: advanced-planning/SKILL.md
  - Phase 3 plan: advanced-planning/plans/phase-3.md

  ## Expected outputs
  - platforms/cowork/SKILL.md
  - platforms/cowork/agents/orchestrator-prompt.md
  - platforms/cowork/agents/worker-prompt.md

  ## Constraints
  - No .claude/ paths — Cowork uses workspace folder paths
  - Agent prompts must be self-contained — they are passed as the full Agent tool prompt
  - Snapshot checkpoint steps replace git commits throughout

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-008 — cowork routing skill and agent prompts"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
```

## Overview

Build the entry point (routing SKILL.md) and the two agent prompts that make the planning system operable in Cowork. The routing skill dispatches user intent to core planning skills; the agent prompts are self-contained instructions passed directly to Cowork's Agent tool.

## Success Criteria

- ✓ `SKILL.md` has broad trigger description and dispatch table covering all planning intents
- ✓ `orchestrator-prompt.md` is a fully self-contained agent prompt with Cowork path conventions
- ✓ `worker-prompt.md` includes the targeted skill injection protocol and snapshot checkpoints
- ✓ Zero `.claude/` path references anywhere in `platforms/cowork/`

## Skills Required

### Broad (from phase plan):
- `skill-creator`: Building the routing SKILL.md with proper dispatch logic

### Specific:
- Pattern from `advanced-planning/SKILL.md` — the existing routing skill is the direct model
- Core agent protocols from `core/agents/orchestrator.md` and `core/agents/worker.md`

## Dependencies
- Phase 1 (core skills and agents) must be complete

## Complexity
**Scope**: Low-Medium — 3 files; agent prompts are the core protocols rewritten for Cowork conventions
**Estimated effort**: 1–2 hours

---

## ralph-loop-009: Snapshot Checkpoints & Testing

```yaml
name: "ralph-loop-009"
task_name: "Snapshot Checkpoints & Testing"
max_iterations: 2
on_max_iterations: checkpoint

handoff_summary:
  done: "Phase 3 complete: checkpoint.sh (POSIX sh, save/restore/list, verified executable), README.md (3-step setup, Agent tool guide, comparison table, 3 troubleshooting entries), and full verification passed (5 files, zero .claude/ references, checkpoint.sh --help clean). PLANS-INDEX.md updated to mark loops 008-009 and Phase 3 as complete."
  failed: ""
  needed: "Begin Phase 4 — Generic + Release (loops 010-012): Python API adapter, documentation, examples, GitHub release packaging."

todos:
  - id: "loop-009-1"
    content: "Create platforms/cowork/checkpoint.sh — a POSIX shell script that snapshots plan and state files to state/snapshots/{timestamp}/"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/cowork/checkpoint.sh is executable, handles 'save [label]', 'restore [timestamp]', and 'list' subcommands, and prints a summary of what was snapshotted"
    status: completed
    priority: high

  - id: "loop-009-2"
    content: "Create platforms/cowork/README.md with Cowork-specific setup, quick-start (3-step setup), Agent tool usage guide, and troubleshooting"
    skill: "NA"
    agent: "NA"
    outcome: "platforms/cowork/README.md exists with: how to add the skill, 3-step quick-start, Agent tool invocation syntax for orchestrator and worker, snapshot checkpoint guide, and troubleshooting for the top 3 Cowork-specific failure modes"
    status: completed
    priority: high

  - id: "loop-009-3"
    content: "Verify complete adapter: all 5 expected files exist, no .claude/ references, checkpoint.sh --help works"
    skill: "NA"
    agent: "NA"
    outcome: "find platforms/cowork/ shows 5 files; grep scan confirms zero .claude/ references; bash checkpoint.sh shows usage without error"
    status: completed
    priority: high

  - id: "loop-009-4"
    content: "Update PLANS-INDEX.md to mark Phase 3 complete and set next action to Phase 4"
    skill: "NA"
    agent: "NA"
    outcome: "PLANS-INDEX.md shows loops 008-009 as complete, Phase 3 status as complete, and next action pointing to Phase 4"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Add snapshot-based checkpointing, the adapter README, and run final verification to declare Phase 3 complete.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-009 snapshot checkpoints and testing"

  ## Success criteria
  - [ ] checkpoint.sh handles save/restore/list subcommands and is executable
  - [ ] README.md has 3-step setup and Agent tool invocation guide
  - [ ] All 5 adapter files present; zero .claude/ references; checkpoint.sh usage works

  ## Required skills
  - None (bash script and README documentation)

  ## Inputs
  - platforms/cowork/SKILL.md (from loop 008)
  - platforms/cowork/agents/ (from loop 008)
  - Phase 3 plan for README content

  ## Expected outputs
  - platforms/cowork/checkpoint.sh
  - platforms/cowork/README.md

  ## Constraints
  - checkpoint.sh must be POSIX sh (not bash-specific) for broad Cowork VM compatibility
  - README must be pitched at non-developer Cowork users — minimal jargon

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-009 — Phase 3 Cowork adapter complete"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
```

## Overview

Complete the Cowork adapter with snapshot-based checkpointing (the git replacement), a user-friendly README, and final verification. The snapshot utility is the structural safety net for non-git Cowork environments.

## Success Criteria

- ✓ `checkpoint.sh` has `save`, `restore`, and `list` subcommands
- ✓ `README.md` is written for non-developer Cowork users
- ✓ Full verification scan passes (5 files, zero `.claude/` references)

## Dependencies
- Loop 008: SKILL.md and agent prompts must exist before README can reference them

## Complexity
**Scope**: Low — 2 files plus verification
**Estimated effort**: 1 hour
