# Phase 5 — Ralph Loops

Six loops implementing the Gate Review Sub-Phase & Invocation Improvements.

---

## Ralph Loop 013: Gate State Schemas

```yaml
---
name: "ralph-loop-013"
task_name: "Gate State Schemas"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "Created gate-verdict.schema.json and gate-failure-context.schema.json in core/state/, extended ralph-loop.schema.md with optional gate_failure_context block, and updated core/state/README.md with four new event types and a Gate Review Protocol section; all schemas validate."
  failed: ""
  needed: ""

todos:
  - id: "loop-013-1"
    content: "Create core/state/gate-verdict.schema.json with all required fields following loop-ready.schema.json pattern"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "core/state/gate-verdict.schema.json exists; contains $schema draft-07, required fields (phase, attempt, timestamp, agent, verdict, confidence, findings, loops_to_revert, failure_notes); findings items have severity/location/description/evidence; parses as valid JSON"
    status: completed
    priority: high
  - id: "loop-013-2"
    content: "Create core/state/gate-failure-context.schema.json with failure context fields"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "core/state/gate-failure-context.schema.json exists; contains required fields (attempt, verdict_file, summary, loops_reverted, do_not_repeat); loops_reverted items have loop/reason; parses as valid JSON"
    status: completed
    priority: high
  - id: "loop-013-3"
    content: "Update core/schemas/ralph-loop.schema.md to document optional gate_failure_context frontmatter block"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "core/schemas/ralph-loop.schema.md contains a Gate Failure Context section documenting the optional block with field specs and an example"
    status: completed
    priority: high
  - id: "loop-013-4"
    content: "Update core/state/README.md with gate_pass, gate_fail, phase_retry, and closeout event types and gate review protocol section"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "core/state/README.md contains all four new event types with example JSONL entries and a Gate Review Protocol section"
    status: completed
    priority: high
  - id: "loop-013-5"
    content: "Validate all JSON schemas in core/state/ parse without errors"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "python -c command parsing all core/state/*.json files exits 0 with no exceptions"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Create JSON Schema definitions for gate verdicts and failure context, update the ralph-loop schema to accept optional gate_failure_context, and document new history.jsonl event types.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-013"

  ## Success criteria
  - [ ] core/state/gate-verdict.schema.json exists and validates as JSON Schema draft-07
  - [ ] core/state/gate-failure-context.schema.json exists and validates as JSON Schema draft-07
  - [ ] core/schemas/ralph-loop.schema.md contains optional gate_failure_context block in frontmatter spec
  - [ ] core/state/README.md documents gate_pass, gate_fail, phase_retry, and closeout event types
  - [ ] All JSON schemas in core/state/ parse without errors

  ## Required skills
  - `schema-design`: JSON Schema draft-07 pattern for gate verdict and failure context

  ## Inputs
  - core/state/loop-ready.schema.json: pattern to follow for JSON Schema structure
  - core/state/loop-complete.schema.json: pattern to follow
  - core/schemas/ralph-loop.schema.md: existing schema to extend
  - core/state/README.md: existing protocol doc to extend
  - docs/gate-review-architecture.md: design spec sections 2.3, 2.4, 2.5, 2.9

  ## Expected outputs
  - core/state/gate-verdict.schema.json
  - core/state/gate-failure-context.schema.json
  - Updated core/schemas/ralph-loop.schema.md
  - Updated core/state/README.md

  ## Constraints
  - JSON Schemas must use draft-07 ($schema: http://json-schema.org/draft-07/schema#)
  - Core files must not reference .claude/ paths
  - CI schema-validation job globs core/state/*.json — new files auto-picked up

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-013 — gate verdict and failure context schemas"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---

## Overview
Create the foundational state schemas that gate agents will write to and versioned retry mechanisms will read from. This loop produces the machine-validatable contracts that all subsequent loops depend on.

## Success Criteria
- ✓ gate-verdict.schema.json contains required fields: phase, attempt, timestamp, agent, verdict, confidence, findings[], loops_to_revert[], failure_notes[]
- ✓ gate-failure-context.schema.json contains required fields: attempt, verdict_file, summary, loops_reverted[], do_not_repeat[]
- ✓ ralph-loop.schema.md documents gate_failure_context as optional frontmatter block
- ✓ All core/state/*.json files parse as valid JSON

## Skills Required

### Broad (from phase plan):
- `schema-design`: JSON Schema draft-07 for state bus extensions

### Specific (refined for this loop):
- JSON Schema draft-07 nested object/array definitions
- Markdown schema documentation conventions

### Discovered:
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Existing JSON schemas | core/state/*.schema.json | JSON Schema draft-07 |
| Existing ralph-loop schema | core/schemas/ralph-loop.schema.md | Markdown |
| State bus README | core/state/README.md | Markdown |
| Design spec | docs/gate-review-architecture.md | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Gate verdict schema | core/state/gate-verdict.schema.json | JSON Schema draft-07 |
| Failure context schema | core/state/gate-failure-context.schema.json | JSON Schema draft-07 |
| Updated loop schema | core/schemas/ralph-loop.schema.md | Markdown |
| Updated state README | core/state/README.md | Markdown |

## Dependencies

### Must Complete Before
- None — first loop in Phase 5

### Blocked By
- Nothing

## Complexity
**Scope**: Medium
**Key challenges**:
1. Nested object definitions in JSON Schema (findings array with severity/location/description/evidence)
2. Maintaining consistency with existing schema patterns

---

## Ralph Loop 014: Gate Agent Definitions

```yaml
---
name: "ralph-loop-014"
task_name: "Gate Agent Definitions"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "Created core/agents/gate-reviewer.md (abstract gate role, 6-step protocol, no .claude/ paths) and five concrete gate agents in platforms/claude-code/agents/: code-review-agent.md, phase-goals-agent.md, security-agent.md, test-agent.md, and programme-reporter.md; all have YAML frontmatter with name/description/model/tools/triggers, all reference gate-verdict.schema.json and the [phase]-attempt-[N]-[agent-name].json verdict path, all document confidence ≥80 threshold."
  failed: ""
  needed: ""

todos:
  - id: "loop-014-1"
    content: "Create core/agents/gate-reviewer.md with abstract gate protocol following core/agents/orchestrator.md pattern"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "core/agents/gate-reviewer.md exists; contains model tier, spawned-by, returns-when sections; documents 6-step gate protocol with confidence threshold; zero occurrences of '.claude/' in file"
    status: completed
    priority: high
  - id: "loop-014-2"
    content: "Create platforms/claude-code/agents/code-review-agent.md with YAML frontmatter and code quality evaluation protocol"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "code-review-agent.md exists with name, description, model: sonnet, tools: Read/Glob/Grep/Bash, triggers fields in frontmatter; body documents evaluation criteria, confidence scoring, and verdict output path"
    status: completed
    priority: high
  - id: "loop-014-3"
    content: "Create platforms/claude-code/agents/phase-goals-agent.md with success criteria verification protocol"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "phase-goals-agent.md exists with complete frontmatter (name, description, model, tools, triggers); body documents how to read phase plan success criteria and verify each against actual artifacts"
    status: completed
    priority: high
  - id: "loop-014-4"
    content: "Create platforms/claude-code/agents/security-agent.md with security scanning protocol"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "security-agent.md exists with complete frontmatter; body documents secret detection, credential scanning, and injection pattern checks; marked as optional in description"
    status: completed
    priority: high
  - id: "loop-014-5"
    content: "Create platforms/claude-code/agents/test-agent.md with test verification protocol"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "test-agent.md exists with complete frontmatter (tools: Read, Bash); body documents test suite execution, coverage threshold checking; marked as optional"
    status: completed
    priority: high
  - id: "loop-014-6"
    content: "Create platforms/claude-code/agents/programme-reporter.md with closeout synthesis protocol"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "programme-reporter.md exists with complete frontmatter (tools include Write); body documents how to read complete documentary record and produce closeout narrative"
    status: completed
    priority: high
  - id: "loop-014-7"
    content: "Verify all 6 agent files cross-reference gate-verdict.schema.json and use consistent verdict naming convention"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "All 5 concrete agents reference verdict output path [phase]-attempt-[N]-[agent-name].json; all mention confidence ≥80 threshold"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Create the abstract gate-reviewer role in core/agents/ and five concrete gate agents in platforms/claude-code/agents/, all with standardised frontmatter including the new triggers: field.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-014"

  ## Success criteria
  - [ ] core/agents/gate-reviewer.md exists with abstract gate protocol and no .claude/ paths
  - [ ] All 5 concrete agents exist in platforms/claude-code/agents/ with name, description, model, tools, triggers frontmatter
  - [ ] Each agent references gate-verdict.schema.json for output contract
  - [ ] Confidence scoring (≥80 threshold) documented in each agent's evaluation protocol

  ## Required skills
  - `agent-definition`: Writing abstract and concrete agent roles with frontmatter

  ## Inputs
  - core/agents/orchestrator.md: abstract agent pattern (no YAML frontmatter)
  - platforms/claude-code/agents/ralph-orchestrator.md: concrete agent frontmatter pattern
  - core/state/gate-verdict.schema.json: verdict output contract (from loop 013)
  - docs/gate-review-architecture.md: sections 2.2, 2.8

  ## Expected outputs
  - core/agents/gate-reviewer.md
  - platforms/claude-code/agents/code-review-agent.md
  - platforms/claude-code/agents/phase-goals-agent.md
  - platforms/claude-code/agents/security-agent.md
  - platforms/claude-code/agents/test-agent.md
  - platforms/claude-code/agents/programme-reporter.md

  ## Constraints
  - Abstract gate-reviewer.md must NOT contain .claude/ paths (platform-agnostic core file)
  - Concrete agents must follow existing frontmatter format: name, description, model, tools
  - Add triggers: field (comma-separated keywords) to each concrete agent
  - programme-reporter gets Write in tools (for report output); all other gate agents are read-only

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-014 — 6 gate agent definitions"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---

## Overview
Create the agent definitions that the gate commands will spawn. One abstract role for the core, five concrete agents for the Claude Code adapter.

## Success Criteria
- ✓ Abstract gate-reviewer.md contains no platform-specific references
- ✓ All 5 concrete agents have valid YAML frontmatter with name, description, model, tools, triggers
- ✓ Verdict output naming convention documented: [phase]-attempt-[N]-[agent-name].json

## Skills Required

### Broad (from phase plan):
- `agent-definition`: Writing agent roles with frontmatter

### Specific:
- Confidence scoring protocol design
- Verdict file naming conventions

### Discovered:
- None

## Inputs
| Input | Source | Format |
|-------|--------|--------|
| Abstract agent pattern | core/agents/orchestrator.md | Markdown |
| Concrete agent pattern | platforms/claude-code/agents/ralph-orchestrator.md | Markdown (YAML frontmatter) |
| Gate verdict schema | core/state/gate-verdict.schema.json | JSON Schema |
| Design spec | docs/gate-review-architecture.md | Markdown |

## Outputs
| Output | Location | Format |
|--------|----------|--------|
| Abstract gate role | core/agents/gate-reviewer.md | Markdown |
| Code review agent | platforms/claude-code/agents/code-review-agent.md | Markdown (YAML frontmatter) |
| Phase goals agent | platforms/claude-code/agents/phase-goals-agent.md | Markdown (YAML frontmatter) |
| Security agent | platforms/claude-code/agents/security-agent.md | Markdown (YAML frontmatter) |
| Test agent | platforms/claude-code/agents/test-agent.md | Markdown (YAML frontmatter) |
| Programme reporter | platforms/claude-code/agents/programme-reporter.md | Markdown (YAML frontmatter) |

## Dependencies

### Must Complete Before
- ralph-loop-013: gate-verdict.schema.json must exist for agent output contracts

## Complexity
**Scope**: Medium
**Key challenges**:
1. Balancing specificity of review criteria with generality across project types
2. Designing the confidence scoring protocol

---

## Ralph Loop 015: Invocation & Catalogue Updates

```yaml
---
name: "ralph-loop-015"
task_name: "Invocation & Catalogue Updates"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "Added triggers: field to 3 existing platform agents; updated agent-catalogue.md with ## Gate Review Agents section (6 new agents with model tier, spawned-by, purpose, when-to-assign) and updated quick-reference/model-tier tables; updated skill-catalogue.md with NA entries for gate review and programme closeout; fixed install.sh and install.ps1 to copy platforms/claude-code/agents/*.md in both project and global modes; created platforms/claude-code/.claude-plugin/plugin.json; created platforms/claude-code/hooks/hooks.json with planning-mode and gate-review-mode guards and AGENT START/STOP subagent logging; updated settings.json with gate-review-mode PreToolUse hooks and renamed WORKER to AGENT in SubagentStart/Stop; mirrored all 6 gate agent files (gate-reviewer + 5 concrete) to .claude/agents/."
  failed: ""
  needed: ""

todos:
  - id: "loop-015-1"
    content: "Add triggers: field to ralph-orchestrator.md, ralph-loop-worker.md, and analysis-worker.md frontmatter"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "All 3 existing platform agents in platforms/claude-code/agents/ contain a triggers: field with comma-separated discovery keywords"
    status: completed
    priority: high
  - id: "loop-015-2"
    content: "Update agent-catalogue.md with Gate Review Agents section listing all 6 new agents"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "core/skills/plan-subagent-identification/references/agent-catalogue.md contains ## Gate Review Agents section with entries for gate-reviewer, code-review-agent, phase-goals-agent, security-agent, test-agent, programme-reporter; quick-reference and model tier tables updated"
    status: completed
    priority: high
  - id: "loop-015-3"
    content: "Update skill-catalogue.md to note gate review = NA (handled by agents, not skills)"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "core/skills/plan-skill-identification/references/skill-catalogue.md contains entries noting gate review evaluation and programme closeout are NA (done by agents)"
    status: completed
    priority: high
  - id: "loop-015-4"
    content: "Fix install.sh to copy platform agents from platforms/claude-code/agents/ in addition to core/agents/"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "setup/claude-code/install.sh contains a loop copying platforms/claude-code/agents/*.md to target; --dry-run shows both core and platform agents"
    status: completed
    priority: high
  - id: "loop-015-5"
    content: "Fix install.ps1 with equivalent platform agent copy logic"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "setup/claude-code/install.ps1 contains equivalent PowerShell loop for platform agents"
    status: completed
    priority: high
  - id: "loop-015-6"
    content: "Create platforms/claude-code/.claude-plugin/plugin.json manifest following ralph-loop plugin pattern"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "platforms/claude-code/.claude-plugin/plugin.json exists with name, description, version, author fields"
    status: completed
    priority: high
  - id: "loop-015-7"
    content: "Create platforms/claude-code/hooks/hooks.json with planning-mode and gate-review-mode guards and subagent logging"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "platforms/claude-code/hooks/hooks.json exists with PreToolUse hooks for both sentinel files and SubagentStart/SubagentStop logging"
    status: completed
    priority: high
  - id: "loop-015-8"
    content: "Update platforms/claude-code/settings.json with gate-review-mode PreToolUse hooks and rename WORKER to AGENT in SubagentStart/Stop"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "settings.json PreToolUse hooks block writes when gate-review-mode sentinel exists (allowing plans/gate-verdicts/ only); SubagentStart/Stop log AGENT START/STOP instead of WORKER"
    status: completed
    priority: high
  - id: "loop-015-9"
    content: "Mirror all new gate agent files to .claude/agents/ for project-local use"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "All 6 new agent files (gate-reviewer + 5 concrete) exist in .claude/agents/ matching their source copies"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Add triggers: field to all existing agents, update agent and skill catalogues with gate agents, fix install scripts to copy platform agents, create plugin-ready scaffold, add gate-review-mode hooks, and mirror new agents to .claude/agents/.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-015"

  ## Success criteria
  - [ ] All 3 existing platform agents (ralph-orchestrator, ralph-loop-worker, analysis-worker) have triggers: field
  - [ ] agent-catalogue.md lists all gate agents with delegation criteria
  - [ ] skill-catalogue.md notes gate review = NA (handled by agents, not skills)
  - [ ] install.sh copies both core/agents/ AND platforms/claude-code/agents/ to target
  - [ ] install.ps1 has equivalent fix
  - [ ] platforms/claude-code/.claude-plugin/plugin.json exists with manifest
  - [ ] platforms/claude-code/hooks/hooks.json exists with extracted hooks
  - [ ] settings.json has gate-review-mode PreToolUse hooks and updated SubagentStart/Stop logging
  - [ ] All new agents mirrored to .claude/agents/

  ## Required skills
  - `catalogue-maintenance`: Updating skill and agent catalogues

  ## Inputs
  - platforms/claude-code/agents/*.md: existing agents to add triggers: to
  - core/skills/plan-subagent-identification/references/agent-catalogue.md: catalogue to update
  - core/skills/plan-skill-identification/references/skill-catalogue.md: catalogue to update
  - setup/claude-code/install.sh: install script to fix
  - setup/claude-code/install.ps1: install script to fix
  - platforms/claude-code/settings.json: hooks to update
  - ~/.claude/plugins/cache/claude-plugins-official/ralph-loop/*: plugin structure pattern

  ## Expected outputs
  - Updated agent frontmatter (3 existing agents)
  - Updated agent-catalogue.md and skill-catalogue.md
  - Fixed install.sh and install.ps1
  - platforms/claude-code/.claude-plugin/plugin.json
  - platforms/claude-code/hooks/hooks.json
  - Updated platforms/claude-code/settings.json
  - Mirrored agents in .claude/agents/

  ## Constraints
  - triggers: field is additive and optional — must not break existing agent loading
  - Install script fix must work for both --project and --global modes
  - Plugin scaffold follows ralph-loop plugin's exact directory structure
  - Gate-review-mode hooks follow planning-mode sentinel pattern

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-015 — invocation improvements, catalogues, plugin scaffold"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---

## Overview
The invocation loop that makes all new agents discoverable, fixes the install script bug, and creates the plugin-ready structure.

## Success Criteria
- ✓ All agents (existing + new) discoverable via glob + frontmatter parsing
- ✓ Install scripts copy all agent files to target projects
- ✓ Plugin scaffold follows ralph-loop plugin pattern

## Skills Required

### Broad (from phase plan):
- `catalogue-maintenance`: Agent and skill catalogue updates

### Specific:
- Shell script editing (POSIX sh)
- PowerShell script editing
- JSON hooks configuration

### Discovered:
- Plugin manifest authoring (borrowed from ralph-loop plugin pattern)

## Dependencies

### Must Complete Before
- ralph-loop-014: new gate agents must exist before catalogues can list them

## Complexity
**Scope**: High (many files touched across multiple directories)
**Key challenges**:
1. Install script fix must handle both --project and --global modes
2. Gate-review-mode hooks must allow verdict writes but block everything else

---

## Ralph Loop 016: Gate Commands

```yaml
---
name: "ralph-loop-016"
task_name: "Gate Commands"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "Created run-gate.md (10 numbered steps: phase resolution, loop-complete check, agent list, sentinel management, sequential agent spawning, verdict aggregation, history.jsonl append), run-closeout.md (6 steps: completion check, documentary record gather, programme-reporter spawn, report verification, closeout event), and next-phase.md (7 steps: gate review inline, pass/fail branching, versioned retry file creation, failure context injection, loop file freezing, PLANS-INDEX.md update, phase_retry event); all 3 copied to .claude/commands/ and verified identical to source."
  failed: ""
  needed: ""

todos:
  - id: "loop-016-1"
    content: "Create platforms/claude-code/commands/run-gate.md with sequential agent spawning, verdict aggregation, and sentinel management"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "run-gate.md exists with frontmatter (description, allowed-tools, argument-hint); numbered steps covering phase resolution, loop completion check, sentinel creation, agent spawning, sentinel removal, verdict aggregation, history.jsonl append, and summary output"
    status: completed
    priority: high
  - id: "loop-016-2"
    content: "Create platforms/claude-code/commands/run-closeout.md with programme-reporter spawning"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "run-closeout.md exists with correct frontmatter; steps spawn programme-reporter agent, write closeout-report.md, append closeout event to history.jsonl"
    status: completed
    priority: high
  - id: "loop-016-3"
    content: "Create platforms/claude-code/commands/next-phase.md with gate integration and versioned retry on failure"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "next-phase.md exists with frontmatter; steps include gate review, on-pass advancement (gate_pass event, CLAUDE.md update), on-fail retry (create_retry_version, inject_failure_context, freeze_loop_file, PLANS-INDEX.md update, phase_retry event)"
    status: completed
    priority: high
  - id: "loop-016-4"
    content: "Copy all 3 new commands to .claude/commands/"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "run-gate.md, run-closeout.md, and next-phase.md all exist in .claude/commands/ matching their source copies"
    status: completed
    priority: high
  - id: "loop-016-5"
    content: "Verify all commands have consistent frontmatter and follow the next-loop.md pattern"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "All 3 commands have description, allowed-tools, argument-hint fields; steps are numbered with markdown code blocks for shell commands"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Create the /run-gate, /run-closeout, and /next-phase slash commands that drive the gate review workflow. Copy to .claude/commands/.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-016"

  ## Success criteria
  - [ ] platforms/claude-code/commands/run-gate.md exists with numbered steps, agent spawning, verdict aggregation, and gate-review-mode sentinel management
  - [ ] platforms/claude-code/commands/run-closeout.md exists with programme-reporter spawning
  - [ ] platforms/claude-code/commands/next-phase.md exists with gate integration, versioned retry on fail, and PLANS-INDEX.md update
  - [ ] All 3 commands have correct frontmatter (description, allowed-tools, argument-hint)
  - [ ] Commands copied to .claude/commands/

  ## Required skills
  - `command-authoring`: Slash command creation with agent spawning patterns

  ## Inputs
  - platforms/claude-code/commands/next-loop.md: command pattern to follow
  - platforms/claude-code/agents/code-review-agent.md: agent to spawn
  - platforms/claude-code/agents/phase-goals-agent.md: agent to spawn
  - core/state/gate-verdict.schema.json: verdict format to read
  - docs/gate-review-architecture.md: sections 2.6, 2.4

  ## Expected outputs
  - platforms/claude-code/commands/run-gate.md
  - platforms/claude-code/commands/run-closeout.md
  - platforms/claude-code/commands/next-phase.md
  - Copies in .claude/commands/

  ## Constraints
  - Sequential agent spawning (main thread controls, consistent with two-agent pattern)
  - Gate-review-mode sentinel created before spawning, removed after
  - /next-phase is a NEW command (does not exist yet)
  - Verdict file naming: [phase]-attempt-[N]-[agent-name].json

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-016 — gate commands"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---

## Overview
Create the command layer that orchestrates gate review execution. These commands spawn gate agents, aggregate verdicts, and manage phase advancement with versioned retry on failure.

## Success Criteria
- ✓ /run-gate can run independently of /next-phase
- ✓ /next-phase calls gate review before advancing
- ✓ Versioned retry files created on gate failure with injected failure context

## Skills Required

### Broad (from phase plan):
- `command-authoring`: Slash command creation

### Specific:
- Agent spawning via Agent tool
- Verdict file aggregation logic
- Gate-review-mode sentinel management

### Discovered:
- None

## Dependencies

### Must Complete Before
- ralph-loop-014: agents must exist to be spawned
- ralph-loop-015: install scripts must copy commands; hooks must be in place

## Complexity
**Scope**: High
**Key challenges**:
1. /next-phase is the most complex command — handles gate pass, gate fail with versioned retry, PLANS-INDEX update
2. Gate-review-mode sentinel lifecycle must be robust (create before, remove after, even on error)

---

## Ralph Loop 017: Python Versioning Utilities

```yaml
---
name: "ralph-loop-017"
task_name: "Python Versioning Utilities"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "Created platforms/python/versioning.py with four functions (create_retry_version, inject_failure_context, get_active_version, freeze_loop_file), platforms/python/tests/test_versioning.py with 30 test methods across 4 classes all passing; updated platforms/python/__init__.py to add versioning to __all__; full test suite 70/70 passed, zero external imports."
  failed: ""
  needed: ""

todos:
  - id: "loop-017-1"
    content: "Create platforms/python/versioning.py with create_retry_version function"
    skill: "NA"
    agent: "analysis-worker"
    outcome: "versioning.py exists; create_retry_version(loop_file, *, attempt_number) creates phase-N-ralph-loops-v{attempt}.md; strips existing -v\\d+ suffix; raises FileNotFoundError and ValueError appropriately"
    status: completed
    priority: high
  - id: "loop-017-2"
    content: "Add inject_failure_context function to versioning.py"
    skill: "NA"
    agent: "analysis-worker"
    outcome: "inject_failure_context(loop_file, *, verdict) writes gate_failure_context YAML block into frontmatter; handles both --- and ```yaml delimiters"
    status: completed
    priority: high
  - id: "loop-017-3"
    content: "Add get_active_version function to versioning.py"
    skill: "NA"
    agent: "analysis-worker"
    outcome: "get_active_version(plans_index, *, phase) reads PLANS-INDEX.md markdown table and returns active loop file path for the phase; returns None if phase not found"
    status: completed
    priority: high
  - id: "loop-017-4"
    content: "Add freeze_loop_file function to versioning.py"
    skill: "NA"
    agent: "analysis-worker"
    outcome: "freeze_loop_file(loop_file) replaces all status: completed and status: in_progress with status: frozen via regex; leaves completed and cancelled unchanged"
    status: pending
    priority: high
  - id: "loop-017-5"
    content: "Create platforms/python/tests/test_versioning.py with comprehensive test suite"
    skill: "NA"
    agent: "analysis-worker"
    outcome: "test_versioning.py exists with ≥16 test methods across 4 test classes (TestCreateRetryVersion, TestInjectFailureContext, TestGetActiveVersion, TestFreezeLoopFile); covers happy paths, edge cases, and error conditions"
    status: completed
    priority: high
  - id: "loop-017-6"
    content: "Update platforms/python/__init__.py to add versioning to __all__"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "platforms/python/__init__.py __all__ list includes 'versioning'"
    status: completed
    priority: high
  - id: "loop-017-7"
    content: "Run full test suite and verify zero external imports"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "python -m pytest platforms/python/tests/ -v exits 0 with all tests passing; versioning.py uses only allowed stdlib imports"
    status: completed
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Create versioning.py with four functions (create_retry_version, inject_failure_context, get_active_version, freeze_loop_file) and comprehensive tests.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-017"

  ## Success criteria
  - [ ] platforms/python/versioning.py exists with 4 public functions
  - [ ] platforms/python/tests/test_versioning.py exists with ≥16 test methods
  - [ ] python -m pytest platforms/python/tests/test_versioning.py -v passes with 0 failures
  - [ ] python -m pytest platforms/python/tests/ -v (full suite) passes with 0 failures
  - [ ] CI AST import checker would pass (standard library imports only)
  - [ ] platforms/python/__init__.py updated with versioning in __all__

  ## Required skills
  - `python-development`: Standard library Python following existing API conventions

  ## Inputs
  - platforms/python/state_manager.py: API pattern to follow
  - platforms/python/plan_io.py: regex patterns for frontmatter parsing
  - platforms/python/tests/test_state_manager.py: test pattern to follow
  - core/state/gate-verdict.schema.json: verdict structure for inject_failure_context
  - core/state/gate-failure-context.schema.json: failure context structure

  ## Expected outputs
  - platforms/python/versioning.py
  - platforms/python/tests/test_versioning.py
  - Updated platforms/python/__init__.py

  ## Constraints
  - Standard library only: json, pathlib, re, datetime, typing (CI enforces)
  - Keyword-only args after *, Path | str for paths, NumPy-style docstrings
  - freeze_loop_file uses direct regex, NOT plan_io.update_todo_status()
  - inject_failure_context must handle both --- and ```yaml frontmatter delimiters

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-017 — versioning utilities and tests"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---

## Overview
Build the Python API for versioned retry file creation and failure context injection. These utilities are called by /next-phase when a gate fails.

## Success Criteria
- ✓ create_retry_version creates phase-N-ralph-loops-v{attempt}.md from source
- ✓ inject_failure_context writes gate_failure_context YAML block
- ✓ get_active_version reads PLANS-INDEX.md for active loop file
- ✓ freeze_loop_file replaces pending/in_progress with frozen
- ✓ All tests pass with zero external dependencies

## Skills Required

### Broad (from phase plan):
- `python-development`: Standard library Python API

### Specific:
- Regex for YAML frontmatter manipulation
- pytest fixture patterns

### Discovered:
- None

## Dependencies

### Must Complete Before
- ralph-loop-013: schemas define the structures versioning operates on

### Parallelisable
- Can run in parallel with loops 014-016 (no shared file dependencies)

## Complexity
**Scope**: Medium
**Key challenges**:
1. Handling both --- and ```yaml frontmatter formats
2. Robust version suffix stripping in create_retry_version

---

## Ralph Loop 018: Integration Verification

```yaml
---
name: "ralph-loop-018"
task_name: "Integration Verification"
max_iterations: 3
on_max_iterations: checkpoint

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-018-1"
    content: "Trace gate-pass scenario end-to-end and document the state transitions"
    skill: "NA"
    agent: "analysis-worker"
    outcome: "Gate-pass trace documented showing: all loops complete → /run-gate creates sentinel → agents write pass verdicts → sentinel removed → gate_pass event in history.jsonl → /next-phase advances"
    status: pending
    priority: high
  - id: "loop-018-2"
    content: "Trace gate-fail + versioned retry scenario and document state transitions"
    skill: "NA"
    agent: "analysis-worker"
    outcome: "Gate-fail trace documented showing: fail verdict → gate_fail event → versioned retry file created with failure context → original frozen → PLANS-INDEX updated → phase_retry event → /next-loop executes retry"
    status: pending
    priority: high
  - id: "loop-018-3"
    content: "Verify gate-review-mode hooks block non-verdict writes and allow verdict writes"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Hook behaviour confirmed: with sentinel present, Write to non-verdict path is blocked; Write to plans/gate-verdicts/ is allowed; removing sentinel unblocks all writes"
    status: pending
    priority: high
  - id: "loop-018-4"
    content: "Verify ralph-loop plugin compatibility — no file conflicts with our state files"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "Confirmed: .claude/state/ files do not conflict with .claude/ralph-loop.local.md; both /next-loop --auto and /ralph-loop can be available simultaneously"
    status: pending
    priority: medium
  - id: "loop-018-5"
    content: "Update CLAUDE.md with gate review protocol, updated model tiers, commands list, runtime directory, and ralph-loop compatibility note"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "CLAUDE.md contains Gate Review Protocol subsection; Model Tiers table includes gate review (Sonnet) and closeout (Sonnet); commands table includes /run-gate, /run-closeout, /next-phase; runtime directory tree includes plans/gate-verdicts/"
    status: pending
    priority: high
  - id: "loop-018-6"
    content: "Update core/schemas/todo.schema.md with frozen as valid terminal status"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "todo.schema.md Status Values table includes frozen with description: set by versioning system when loop file is superseded by retry version"
    status: pending
    priority: high
  - id: "loop-018-7"
    content: "Update plans/PLANS-INDEX.md with Phase 5 entry and version tracking columns"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "PLANS-INDEX.md Phases table includes Phase 5; Ralph Loops table includes loops 013-018; version tracking columns (Active File, Attempt) added"
    status: pending
    priority: high
  - id: "loop-018-8"
    content: "Run final validation: all JSON schemas valid, all Python tests pass"
    skill: "NA"
    agent: "ralph-loop-worker"
    outcome: "JSON schema validation exits 0; python -m pytest platforms/python/tests/ -v exits 0 with all tests passing"
    status: pending
    priority: medium

prompt: |
  ## Context from prior loop
  Done: [inject prior.handoff_summary.done]
  Failed: [inject prior.handoff_summary.failed]
  Needed: [inject prior.handoff_summary.needed]

  ## Objective
  Verify end-to-end scenarios (gate-pass, gate-fail with retry, hooks, plugin compatibility), update CLAUDE.md, PLANS-INDEX.md, and todo.schema.md documentation.

  ## Git checkpoint (run first)
  git add -A && git commit -m "checkpoint: before ralph-loop-018"

  ## Success criteria
  - [ ] Gate-pass scenario traced and documented
  - [ ] Gate-fail + versioned retry scenario traced and documented
  - [ ] Gate-review-mode hooks verified (blocks non-verdict writes, allows verdict writes)
  - [ ] Ralph-loop plugin compatibility confirmed (no file conflicts)
  - [ ] CLAUDE.md updated with gate review protocol, model tiers, commands, runtime directory
  - [ ] core/schemas/todo.schema.md updated with frozen status
  - [ ] plans/PLANS-INDEX.md updated with Phase 5 entry and version tracking columns
  - [ ] All JSON schemas valid; all Python tests pass

  ## Required skills
  - `integration-testing`: End-to-end verification
  - `documentation`: CLAUDE.md and schema updates

  ## Inputs
  - All files created in loops 013-017
  - CLAUDE.md: documentation to update
  - core/schemas/todo.schema.md: schema to update
  - plans/PLANS-INDEX.md: index to update

  ## Expected outputs
  - Updated CLAUDE.md
  - Updated core/schemas/todo.schema.md
  - Updated plans/PLANS-INDEX.md
  - Verification evidence (scenario traces)

  ## Constraints
  - CLAUDE.md updates must be accurate and concise
  - frozen status is a new terminal state — document clearly

  ## On completion
  1. git add -A && git commit -m "complete: ralph-loop-018 — integration verification and documentation"
  2. Update handoff_summary
  3. Mark all todos completed

  Begin. Mark todos in_progress before starting each task. One in_progress at a time.
---

## Overview
Final verification loop. Traces both success and failure scenarios end-to-end, verifies hook behaviour, confirms plugin compatibility, and updates all documentation.

## Success Criteria
- ✓ Both gate-pass and gate-fail scenarios produce correct state transitions
- ✓ Documentary record is intact (verdicts, history.jsonl events, versioned files)
- ✓ All documentation reflects the new capabilities

## Skills Required

### Broad (from phase plan):
- `integration-testing`: Scenario verification
- `documentation`: Reference doc updates

### Specific:
- State transition tracing
- CLAUDE.md conventions

### Discovered:
- None

## Dependencies

### Must Complete Before
- ralph-loop-013 through ralph-loop-017: all components must exist

## Complexity
**Scope**: Medium
**Key challenges**:
1. Ensuring all documentation updates are consistent and accurate
2. Verifying hook behaviour without running a full gate review (may need to simulate)
