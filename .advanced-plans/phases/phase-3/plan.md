# Phase 3: Cowork Adapter

## Objective

Build an adapter that makes the advanced planning system fully functional in Cowork mode, using a routing SKILL.md as the entry point and Cowork's Agent tool for orchestrator/worker spawning — enabling the same hierarchical planning workflow without slash commands or git.

---

## Scope

### Included

- **Routing SKILL.md**: Entry point that dispatches to core planning skills based on user intent (replaces slash commands)
- **Agent integration**: Map ralph-orchestrator and ralph-loop-worker to Cowork's Agent tool with explicit `model` parameter for tier control
- **Snapshot-based checkpoints**: File-based state snapshots replacing git checkpoints for environments without git
- **TodoWrite integration**: Identical to Claude Code — Cowork uses the same native TodoWrite tool
- **Adapter README**: Setup instructions specific to Cowork users

### Explicitly NOT included

- Slash commands (Cowork doesn't support them)
- Git hooks or settings.json (Cowork doesn't use these)
- New planning capabilities beyond what the core provides
- Python API (Phase 4)

---

## Key Deliverables

| Deliverable | Format | Location |
|-------------|--------|----------|
| Routing SKILL.md | Markdown with frontmatter | `platforms/cowork/SKILL.md` |
| Orchestrator agent prompt | Markdown | `platforms/cowork/agents/orchestrator-prompt.md` |
| Worker agent prompt | Markdown | `platforms/cowork/agents/worker-prompt.md` |
| Snapshot checkpoint utility | Bash/Python script | `platforms/cowork/checkpoint.sh` |
| Adapter README | Markdown | `platforms/cowork/README.md` |

---

## Success Criteria

- ✓ **Routing works**: A user saying "plan a new phase" in Cowork triggers the phase-plan-creator skill via the routing SKILL.md
- ✓ **Agent spawning works**: The orchestrator is spawned with `model: sonnet` and the worker with `model: haiku` via Cowork's Agent tool
- ✓ **Skill injection works**: The worker loads per-todo SKILL.md files as defined in the core worker protocol
- ✓ **State bus works**: loop-ready.json and loop-complete.json are written and consumed correctly in Cowork's sandboxed VM
- ✓ **Checkpoints without git**: File-based snapshots capture plan state at loop boundaries; recoverable from snapshot if a loop corrupts state
- ✓ **Colleague-ready**: A Cowork user can start using the planning system by adding the skill to their session — no install script needed

---

## Dependencies

### Must Complete Before

- Phase 1: Core Architecture Design — core skills and state bus must be finalised
- Phase 2: Claude Code Adapter — validates the two-agent pattern works end-to-end (learnings inform Cowork implementation)

### Blocked By

- Cowork's Agent tool must support the `model` parameter for tier control (currently supported)

---

## Skills Required (Broad Categories)

- `skill-creator`: Building the routing SKILL.md with proper dispatch logic
- `verification-before-completion`: Testing in actual Cowork environment

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Cowork Agent tool doesn't pass skill context to spawned agents | Medium | High | Test early in loop 008; if skills can't be passed, include skill content inline in the agent prompt |
| Cowork VM filesystem resets between sessions | Low (workspace folder persists) | Medium | Store all plan files and state in the workspace folder, not the session's temporary directory |
| No git means no rollback | Expected | Medium | Snapshot checkpoints provide equivalent functionality for the planning use case |

---

## Assumptions

- `Cowork Agent tool supports model selection`: The `model` parameter on Cowork's Agent tool allows specifying sonnet/haiku per agent spawn. Validated by: Cowork documentation confirms this.
- `Workspace folder persists`: Files saved to the Cowork workspace folder survive between sessions. Validated by: this is a core Cowork feature.
- `TodoWrite identical`: Cowork's TodoWrite tool has the same schema as Claude Code's. Validated by: both use the same underlying implementation.

---

## Notes / Design Decisions

- **Why a routing SKILL.md instead of commands**: Cowork doesn't support slash commands. The routing skill acts as a dispatcher — the user describes what they want ("plan a new phase", "what's the loop status", "run the next loop") and the skill routes to the appropriate core skill. This is actually more natural for non-developer users.
- **Why snapshot checkpoints instead of git**: Many Cowork users won't have git initialised in their workspace. File-based snapshots (copy plan files to `state/snapshots/{timestamp}/`) provide the same rollback capability without requiring git. The core state bus protocol already supports this — the state files are the coordination mechanism, not git.
- **Why this phase is smaller**: The core does the heavy lifting. The Cowork adapter is primarily about mapping the core's platform-independent definitions to Cowork's specific invocation patterns.

---

## Ralph Loops (2)

| Loop | Name | Type | Key Outputs |
|------|------|------|-------------|
| 008 | Routing SKILL & Agent Integration | Implementation | SKILL.md + agent prompts + checkpoint utility |
| 009 | Snapshot Checkpoints & Testing | Implementation + Verification | Snapshot system + end-to-end test in Cowork |
