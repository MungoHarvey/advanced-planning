# Architectural Decisions

A curated log of the key decisions made during the v8 Advanced Planning System design and implementation. Each decision includes the context in which it was made, the alternatives considered, and the rationale chosen.

---

## Decision 1 — Targeted Skill Injection (not preloading)

**Context**: The worker agent must apply specialist knowledge to diverse tasks within a single loop. Decisions about how to make skills available at execution time shape both output quality and context efficiency.

**Alternatives considered**:
1. Load all assigned skills at worker startup
2. Load no skills; rely on model baseline capability
3. Load the assigned skill per-todo, immediately before execution, then discard

**Decision**: Option 3 — targeted per-todo injection.

**Rationale**: Option 1 floods the context with potentially contradictory instructions from multiple skills simultaneously, and the volume of instruction degrades attention to the actual task. Option 2 produces generic output for specialist tasks — adequate for simple file creation, inadequate for schema design, statistical methods, or domain-specific patterns. Option 3 gives each task exactly the specialist instruction it needs, at the moment it needs it, without carrying it forward to contaminate the next task.

**Consequence**: The worker's 7-step per-todo protocol (read → mark in_progress → load skill → execute → verify → unload skill → mark complete) is more complex than alternatives but produces meaningfully better outputs, particularly for specialist tasks.

---

## Decision 2 — Two-Agent Pattern (orchestrator + worker, not one agent)

**Context**: Designing how agents are structured for loop execution. One agent could do everything — plan, populate todos, execute, and complete. Or responsibilities could be split.

**Alternatives considered**:
1. Single agent handles planning and execution in sequence
2. Orchestrator handles planning; worker handles execution; both spawned by main thread

**Decision**: Option 2 — two separate agents, both spawned by the main thread.

**Rationale**: A single agent executing a long loop degrades in quality as context fills. Separating the planning phase (orchestrator) from the execution phase (worker) gives each agent a clean, focused context. The orchestrator uses Sonnet (reasoning-appropriate for planning); the worker uses Haiku (execution-appropriate). Neither agent spawns the other — the main thread sequences them — because in Claude Code, subagents cannot spawn further subagents.

**Consequence**: The main thread must explicitly read `loop-ready.json` between spawning the orchestrator and the worker. This is a small overhead but ensures the coordination protocol is explicit and debuggable.

---

## Decision 3 — Filesystem State Bus (not a queue or API)

**Context**: The orchestrator and worker must exchange structured data. Several coordination mechanisms were considered.

**Alternatives considered**:
1. In-memory state passed as arguments
2. Database (SQLite, Redis)
3. Message queue (RabbitMQ, Kafka)
4. Filesystem files (JSON)

**Decision**: Option 4 — filesystem files.

**Rationale**: Agents in sandboxed environments (Claude Code, Cowork VMs) cannot share in-memory state across spawning boundaries. Databases and queues require installation and services. Filesystem files require nothing — they work in every environment, are human-readable for debugging, can be snapshotted for rollback, and are trivially inspected with standard tools. The performance overhead is negligible for the invocation frequency involved.

**Consequence**: Three files (`loop-ready.json`, `loop-complete.json`, `history.jsonl`) constitute the entire state bus. This simplicity is a feature — there is nothing to fail, configure, or maintain.

---

## Decision 4 — Handoff Summary with Three Fields (not full output)

**Context**: After each loop completes, the next loop's orchestrator needs context about what was done. How much context to carry, and in what format, was a design question.

**Alternatives considered**:
1. Pass the full loop-complete.json as context
2. Pass a structured summary with many fields (files created, commands run, errors encountered, etc.)
3. Pass three fields — done (one sentence), failed (one sentence), needed (one sentence)

**Decision**: Option 3 — three fields, one sentence each.

**Rationale**: Context grows unboundedly if each loop carries the full output of all prior loops. A rich structured summary adds fields that are rarely read and always generated. Three sentences — what was done, what failed, what is needed next — are sufficient for an agent to orient itself and precisely calibrate the start of the next loop. The one-sentence constraint also improves quality: an agent forced to summarise in one sentence cannot be vague.

**Consequence**: The `handoff_summary` (and its representation in `loop-complete.json`) has exactly three required fields. Downstream agents (orchestrator) are instructed to read these three fields and no more.

---

## Decision 5 — Model Tier by Frequency, not Task Difficulty

**Context**: Assigning AI models to roles in the planning system. Several assignment strategies were considered.

**Alternatives considered**:
1. Use the most capable model (Opus) for everything
2. Assign by task difficulty (strategic = Opus, complex execution = Sonnet, simple execution = Haiku)
3. Assign by invocation frequency (phase = Opus, loop = Sonnet, todo = Haiku)

**Decision**: Option 3 — frequency-based assignment.

**Rationale**: Task difficulty is subjective and variable. Frequency is objective and predictable. A 4-phase programme with 3 loops per phase and 5 todos per loop invokes: Opus 4×, Sonnet 12×, Haiku 60×. Cost is dominated by the most frequent tier. Making Haiku the execution tier — even if some individual todos are complex — keeps the programme economically predictable. The targeted skill injection mechanism compensates for Haiku's lower baseline capability on specialist tasks.

**Consequence**: A Haiku worker with an excellent skill produces better output than a Sonnet worker with no skill guidance. This shifts the quality investment from model tier to skill quality — a more leverageable investment.

---

## Decision 6 — Snapshot Checkpoints for Non-Git Environments

**Context**: The Claude Code adapter uses git commits as checkpoints. Cowork and other sandboxed environments may not have git available.

**Alternatives considered**:
1. Require git in all environments
2. Use a database or cache layer for state preservation
3. File-based snapshots (copy `plans/` and `state/` to a timestamped archive)

**Decision**: Option 3 — file-based snapshots via `checkpoint.sh`.

**Rationale**: Requiring git excludes valid deployment environments. A database adds a dependency. File copies are universally available, require no configuration, produce human-readable archives, and can be restored with standard shell commands. The `checkpoint.sh` script handles `save`, `restore`, and `list` with a minimal POSIX sh implementation.

**Consequence**: The Cowork adapter has no git dependency. Restoration is a `sh checkpoint.sh restore [timestamp]` command. The snapshot overhead is negligible for the file sizes involved (plan files are typically <100KB each).

---

## Decision 7 — Routing SKILL.md (not slash commands) for Cowork

**Context**: The Claude Code adapter uses slash commands as entry points. Cowork has no equivalent — it uses natural language via an LLM session.

**Alternatives considered**:
1. Port slash commands to Cowork (not possible — feature not available)
2. Require users to type structured commands
3. A routing `SKILL.md` with a dispatch table mapping natural language to planning actions

**Decision**: Option 3 — routing skill with intent dispatch.

**Rationale**: Cowork's strength is natural language interaction. A routing skill with a broad trigger description and a dispatch table maps user intent to planning actions without requiring structured syntax. The same routing skill also serves as the entry point for Agent tool spawning, making it the single file a Cowork user needs to install.

**Consequence**: The Cowork adapter's entry point is more flexible than slash commands but less predictable. Users can express planning intent in many ways; the routing skill must cover enough trigger phrases to catch the common ones.

---

## Decision 8 — MIT Licence

**Context**: Choosing a licence for the open-source release.

**Alternatives considered**:
1. MIT — permissive, minimal friction, universally understood
2. Apache 2.0 — permissive with explicit patent clause
3. AGPL — copyleft, requires open-sourcing modifications
4. CC BY 4.0 — appropriate for content, not software

**Decision**: MIT.

**Rationale**: This is a planning framework primarily made up of Markdown documents, prompt templates, and a small Python utility library. The primary goal is maximum adoption and minimum friction. MIT is the most universally understood permissive licence, imposes no conditions beyond attribution, and is the default expectation in the broader open-source community. The patent protections offered by Apache 2.0 are not a material concern for a project of this nature.

**Consequence**: Commercial use, modification, and distribution are all permitted. The only requirement is that the copyright notice and licence text are included in copies. No contributor licence agreement is required.
