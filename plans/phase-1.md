# Phase 1: Core Architecture Design

## Objective

Design and implement the platform-independent core of the advanced planning system — schemas, planning skills, agent role definitions, and the filesystem state bus — as a clean, documented foundation that adapters for Claude Code, Cowork, and generic frameworks can build upon.

---

## Scope

### Included

- **Schema definitions** (4): Phase plan, ralph loop, todo, and handoff schemas as standalone markdown reference documents with JSON Schema validation where appropriate
- **Planning skills** (5): phase-plan-creator, ralph-loop-planner, plan-todos, plan-skill-identification, plan-subagent-identification — migrated from v8, refined based on practical evidence, stripped of platform-specific assumptions
- **Agent role definitions** (2): Abstract orchestrator and worker roles with the targeted skill injection protocol documented as part of the worker specification
- **State bus protocol**: Filesystem-based coordination (loop-ready.json / loop-complete.json / history.jsonl) with formal schemas and a protocol specification document
- **Repository skeleton**: Top-level directory structure (`core/`, `platforms/`, `docs/`, `examples/`) with placeholder READMEs

### Explicitly NOT included

- Claude Code-specific commands, agents, or settings (Phase 2)
- Cowork-specific routing or Agent tool integration (Phase 3)
- Python API or framework examples (Phase 4)
- Installation scripts (Phase 2 — platform-specific)

---

## Key Deliverables

| Deliverable | Format | Location |
|-------------|--------|----------|
| Phase plan schema | Markdown + YAML spec | `core/schemas/phase-plan.schema.md` |
| Ralph loop schema | Markdown + YAML spec | `core/schemas/ralph-loop.schema.md` |
| Todo schema | Markdown + YAML spec | `core/schemas/todo.schema.md` |
| Handoff schema | Markdown + YAML spec | `core/schemas/handoff.schema.md` |
| Phase plan creator skill | SKILL.md + references/ | `core/skills/phase-plan-creator/` |
| Ralph loop planner skill | SKILL.md + references/ | `core/skills/ralph-loop-planner/` |
| Plan todos skill | SKILL.md + references/ | `core/skills/plan-todos/` |
| Plan skill identification skill | SKILL.md | `core/skills/plan-skill-identification/` |
| Plan subagent identification skill | SKILL.md | `core/skills/plan-subagent-identification/` |
| Orchestrator role definition | Markdown | `core/agents/orchestrator.md` |
| Worker role definition | Markdown (includes skill injection protocol) | `core/agents/worker.md` |
| State bus protocol | Markdown + JSON schemas | `core/state/README.md` |
| Repository skeleton | Directory structure + READMEs | Root level |

---

## Success Criteria

- ✓ **Schema completeness**: All four schemas define every field with type, requirement level, valid values, and one worked example
- ✓ **Skill portability**: All five planning skills contain zero platform-specific references (no mention of Claude Code, Cowork, slash commands, or specific tool names)
- ✓ **Skill injection documented**: Worker role definition includes a step-by-step protocol for loading SKILL.md per-todo based on the `skill:` field, with clear entry/exit points
- ✓ **State bus testable**: loop-ready.json and loop-complete.json schemas can be validated programmatically; a colleague could write a state bus implementation from the protocol document alone
- ✓ **Repository structure navigable**: A new contributor can find any component within 2 clicks from the root README
- ✓ **Multi-level skill identification documented**: The phase → loop → todo skill cascade is formally described with examples showing how skills refine at each level

---

## Dependencies

### Must Complete Before

- Analysis document (`ANALYSIS-AND-OPTIMISATION.md`): COMPLETE — provides the evidence base and design rationale

### Blocked By

- Nothing — this is the first phase

### Optional

- Reviewing the open questions from DECISIONS.md (can inform schema design but not blocking)

---

## Skills Required (Broad Categories)

- `skill-creator`: Crafting well-structured SKILL.md files with proper frontmatter and reference documents
- `schema-design`: Defining clear, validatable schemas from practical evidence
- `documentation`: Writing reference documents that colleagues can use without additional context
- `verification-before-completion`: Ensuring each schema and skill works as specified before moving on

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Over-abstracting the schemas beyond what practice supports | Medium | High | Constrain every schema field to something that was actually used in the 56+ loop evidence; flag aspirational fields explicitly |
| Skill definitions too tightly coupled to the forex domain examples | Low | Medium | Use generic examples in skill bodies; forex-specific examples go in `examples/` only |
| State bus protocol too complex for simple use cases | Low | Medium | Define a minimal protocol (loop-ready + loop-complete only) and an extended protocol (+ history.jsonl); adapters choose which to implement |

---

## Assumptions

- `Schema stability`: The four schema types (phase plan, ralph loop, todo, handoff) are sufficient for the planning hierarchy — no additional schema types are needed. Validated by: 56+ loops successfully executed with these four types.
- `Skill portability is achievable`: Planning skills can be written without platform-specific tool references. Validated by: the v8 skills already avoid tool-specific syntax in their core logic.
- `Filesystem state bus is universal`: Any platform that can read/write JSON files can implement the state bus. Validated by: both Claude Code and Cowork have filesystem access.

---

## Notes / Design Decisions

- **Why four schemas not more**: The three-tier hierarchy (phase → loop → todo) plus the handoff protocol covers every planning artefact observed in practice. Adding schemas for "projects" or "programmes" above phases would add complexity without evidence of need.
- **Why skills are in `core/` not `platforms/`**: Planning skills are the same regardless of platform — the logic of "decompose a phase into loops" doesn't change based on whether you're in Claude Code or Cowork. Only the execution mechanism differs.
- **Why the worker role includes skill injection**: This is the highest-value optimisation identified in the analysis. Making it part of the core worker definition ensures all adapters implement it, rather than leaving it as an optional enhancement.

---

## Ralph Loops (4)

| Loop | Name | Type | Key Outputs |
|------|------|------|-------------|
| 001 | Schema Definitions | Design | 4 schema documents in `core/schemas/` |
| 002 | Planning Skills | Migration + Refinement | 5 skill directories in `core/skills/` |
| 003 | Agent Role Definitions | Design | 2 role documents in `core/agents/` with skill injection protocol |
| 004 | State Bus Protocol | Design + Specification | Protocol document + JSON schemas in `core/state/` |
