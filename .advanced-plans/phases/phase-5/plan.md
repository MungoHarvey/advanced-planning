# Phase 5: Gate Review Sub-Phase & Invocation Improvements

## Objective

Extend the Advanced Planning System with inter-phase quality gates that verify outputs before advancement, versioned retry mechanisms for failed phases, and standardised invocation patterns so that any model tier (main thread, orchestrator, worker) can discover, load, and invoke agents, skills, and commands consistently.

## Scope

### Included:

- State schemas: `gate-verdict.schema.json`, `gate-failure-context.schema.json`
- Updated `ralph-loop.schema.md` to support optional `gate_failure_context` frontmatter block
- Abstract gate reviewer role definition (`core/agents/gate-reviewer.md`)
- Five concrete gate agents for Claude Code: code-review-agent, phase-goals-agent, security-agent, test-agent, programme-reporter
- Three new commands: `/run-gate`, `/run-closeout`, `/next-phase` (with gate integration)
- Python versioning utilities: `platforms/python/versioning.py` with full test suite
- Invocation standardisation: consistent agent frontmatter with `triggers:` field, updated skill and agent catalogues, discoverable path resolution
- Updated `PLANS-INDEX.md` schema to track versioned retry files and gate verdicts
- Four new `history.jsonl` event types: `gate_pass`, `gate_fail`, `phase_retry`, `closeout`
- Integration verification: gate-pass and gate-fail end-to-end scenarios
- Updated `core/state/README.md` with gate protocol documentation

### Explicitly NOT included:

- Plugin packaging and marketplace distribution (future Phase 6)
- Cowork adapter gate integration (future — Claude Code first, then port)
- Nested subagent orchestration (tracked separately as a future capability)
- Changes to existing planning skills (phase-plan-creator, ralph-loop-planner, etc.) beyond catalogue updates

## Key Deliverables

| Deliverable | Format | Location |
|-------------|--------|----------|
| Gate verdict schema | JSON Schema draft-07 | `core/state/gate-verdict.schema.json` |
| Gate failure context schema | JSON Schema draft-07 | `core/state/gate-failure-context.schema.json` |
| Updated ralph-loop schema | Markdown | `core/schemas/ralph-loop.schema.md` |
| Abstract gate reviewer | Markdown | `core/agents/gate-reviewer.md` |
| Code review agent | Markdown (YAML frontmatter) | `platforms/claude-code/agents/code-review-agent.md` |
| Phase goals agent | Markdown (YAML frontmatter) | `platforms/claude-code/agents/phase-goals-agent.md` |
| Security agent | Markdown (YAML frontmatter) | `platforms/claude-code/agents/security-agent.md` |
| Test agent | Markdown (YAML frontmatter) | `platforms/claude-code/agents/test-agent.md` |
| Programme reporter | Markdown (YAML frontmatter) | `platforms/claude-code/agents/programme-reporter.md` |
| /run-gate command | Markdown | `platforms/claude-code/commands/run-gate.md` |
| /run-closeout command | Markdown | `platforms/claude-code/commands/run-closeout.md` |
| /next-phase command | Markdown | `platforms/claude-code/commands/next-phase.md` |
| Versioning utilities | Python (stdlib only) | `platforms/python/versioning.py` |
| Versioning tests | Python (pytest) | `platforms/python/tests/test_versioning.py` |
| Updated agent catalogue | Markdown | `core/skills/plan-subagent-identification/references/agent-catalogue.md` |
| Updated skill catalogue | Markdown | `core/skills/plan-skill-identification/references/skill-catalogue.md` |
| Updated state README | Markdown | `core/state/README.md` |

## Success Criteria

- ✓ `gate-verdict.schema.json` validates against JSON Schema draft-07; contains required fields: phase, attempt, timestamp, agent, verdict, confidence, findings[], loops_to_revert[], failure_notes[]
- ✓ `gate-failure-context.schema.json` validates against draft-07; contains fields: attempt, verdict_file, summary, loops_reverted[], do_not_repeat[]
- ✓ All six agent files (1 abstract + 5 concrete) exist with correct frontmatter format (name, model, description, tools) and a `triggers:` field for invocation discovery
- ✓ `/run-gate` command spawns gate agents sequentially, reads verdicts, and writes pass/fail status to `history.jsonl`
- ✓ `/next-phase` command calls `/run-gate` before advancing; on gate failure, creates versioned retry files (`phase-N-ralph-loops-v2.md`) with injected `gate_failure_context`
- ✓ `versioning.py` passes all tests with standard library only; functions: `create_retry_version()`, `inject_failure_context()`, `get_active_version()`, `freeze_loop_file()`
- ✓ Agent catalogue lists all agents (existing + new gate agents) with consistent frontmatter descriptions
- ✓ Skill catalogue includes entry for any new gate-review skill
- ✓ Any agent can discover all available skills and agents by globbing `.claude/skills/*/SKILL.md` and `.claude/agents/*.md` and reading frontmatter
- ✓ All Python source files in `platforms/python/` pass the AST import checker (standard library only)
- ✓ `python -m pytest platforms/python/tests/ -v` passes with zero failures

## Dependencies

### Must Complete Before This Phase:

- Phase 4 (Generic + Release): Complete — Python API, docs, and state bus all in place
- Design specification: `docs/gate-review-architecture.md` — reviewed and approved

### Blocked By:

- Nothing — all prerequisites are met

### Optional:

- Anthropic's official code-review plugin patterns: useful reference for confidence scoring and parallel agent patterns, but not blocking

## Skills Required (Broad Categories)

- `schema-design`: JSON Schema draft-07 for gate verdict and failure context schemas
- `agent-definition`: Writing abstract and concrete agent roles with frontmatter
- `command-authoring`: Creating slash commands with agent spawning patterns
- `python-development`: Standard library Python for versioning utilities
- `integration-testing`: End-to-end scenario verification (gate-pass, gate-fail)
- `catalogue-maintenance`: Updating skill and agent catalogues for discoverability

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Gate agents produce inconsistent verdicts | Medium | High | Define strict verdict schema with required fields; use confidence threshold (≥80) to filter low-confidence findings |
| Versioned retry files accumulate and confuse orchestrator | Low | Medium | PLANS-INDEX.md tracks active version; orchestrator reads index first, not raw directory listing |
| Sequential gate execution is too slow | Low | Low | Start sequential (consistent with two-agent pattern); parallel can be added later as an optimisation |
| New commands conflict with existing command flows | Medium | Medium | `/next-phase` is new (doesn't exist yet); `/run-gate` and `/run-closeout` are additive; no existing commands modified |
| Invocation frontmatter changes break existing agent loading | Low | High | `triggers:` field is additive (optional); existing `name`, `model`, `description`, `tools` fields unchanged |
| Python versioning utilities introduce external dependencies | Low | High | CI AST checker enforces stdlib-only; write tests that verify import compliance |

## Assumptions

- `Sequential gate execution is sufficient`: Gate agents run one at a time via main thread, consistent with the existing two-agent pattern — validated by the architecture review
- `Confidence scoring at ≥80 threshold`: Borrowed from Anthropic's code-review plugin pattern — will validate empirically during integration testing
- `Existing state bus needs minimal changes`: Adding four event types to `history.jsonl` is append-only and non-breaking — validated by reviewing the schema
- `Agent frontmatter is extensible`: Adding `triggers:` as an optional field does not break existing agent loading — validated by reading how commands parse agent files

## Notes / Design Decisions

- **Sequential over parallel gate execution**: The current architecture enforces main-thread sequencing. Parallel gate agents would require architectural changes to the spawning model. Sequential is consistent, simpler, and sufficient for the initial implementation.
- **Versioned files over in-place editing**: Following the immutability principle from the design spec. Original loop files are frozen; retry files carry failure context. This preserves the complete documentary record.
- **`triggers:` field as invocation improvement**: Currently agents are discovered only by name matching in `plan-subagent-identification`. Adding a `triggers:` field (similar to skill `description`) enables any model to discover agents by intent, not just by name.
- **`/next-phase` is new, not updated**: The design doc says "Updated `/next-phase`" but no such command exists. It will be created from scratch with gate integration built in from the start.
- **Gate agents are optional per-phase**: The `/run-gate` command reads a phase config to determine which gate agents to spawn. Security and test agents are marked optional — phases can opt in or out.

## Ralph Loops (6)

| Loop | Name | Type | Key Outputs |
|------|------|------|-------------|
| 013 | Gate State Schemas | Design | `gate-verdict.schema.json`, `gate-failure-context.schema.json`, updated `ralph-loop.schema.md`, updated `core/state/README.md` |
| 014 | Gate Agent Definitions | Design | `gate-reviewer.md` (abstract), 5 concrete agents with standardised frontmatter |
| 015 | Invocation & Catalogue Updates | Implementation | Updated agent-catalogue, skill-catalogue, standardised `triggers:` field across all agents |
| 016 | Gate Commands | Implementation | `/run-gate`, `/run-closeout`, `/next-phase` commands |
| 017 | Python Versioning Utilities | Implementation | `versioning.py`, `test_versioning.py`, CI validation |
| 018 | Integration Verification | Testing | Gate-pass scenario, gate-fail scenario, PLANS-INDEX versioning, history.jsonl event verification |
