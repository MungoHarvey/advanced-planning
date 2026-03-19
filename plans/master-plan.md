# Master Plan: Advanced Planning System — Open-Source Restructure

## Context

The advanced planning system has been proven across 9 phases and 56+ ralph loops in a real-world forex trading prediction pipeline. It solves four failure modes in long-running AI agent sessions: context drift, unverifiable progress, no resumption path, and scope creep. The system uses hierarchical planning (Opus), loop orchestration (Sonnet), and bounded task execution (Haiku/Sonnet) to maintain quality across weeks of multi-session work.

The current codebase is functional but has accumulated artefacts from iterative development (deprecated stubs, duplicate skill variants, a v8 proposal directory with structural improvements not yet merged). The goal is to restructure the system from the ground up, producing a clean open-source package that works across Claude Code, Cowork, and generic agent frameworks.

**Meta-note**: This plan uses the planning system itself (dogfooding). The plan documents serve as both execution guide and worked example for the open-source repository's `examples/` directory.

---

## Phase Overview

```
Phase 1: Core Architecture Design
    ↓
Phase 2: Claude Code Adapter
    ↓
Phase 3: Cowork Adapter
    ↓
Phase 4: Generic Adapter, Documentation & Open-Source Release
```

Each phase produces artefacts that become part of the final repository. Phase plans and ralph loop files will be preserved in `examples/planning-system-restructure/` as a real-world worked example.

---

## Phase 1: Core Architecture Design

**Objective**: Design and implement the platform-independent core of the planning system — schemas, planning skills, agent role definitions, and the filesystem state bus protocol.

**Why**: Everything downstream (adapters, documentation, examples) depends on the core being clean and well-defined. The core must capture the proven patterns from 56+ loops of practical use without platform-specific coupling.

**Ralph Loops (4)**:
1. **Schema Definitions** — Define phase-plan, ralph-loop, todo, and handoff schemas as standalone reference documents
2. **Planning Skills (5)** — Migrate and refine phase-plan-creator, ralph-loop-planner, plan-todos, plan-skill-identification, plan-subagent-identification
3. **Agent Role Definitions** — Define abstract orchestrator and worker roles with the targeted skill injection protocol
4. **State Bus Protocol** — Implement the filesystem coordination pattern (loop-ready.json / loop-complete.json / history.jsonl)

**Skills**: `skill-creator`, `verification-before-completion`

---

## Phase 2: Claude Code Adapter

**Objective**: Build the Claude Code-specific adapter that wraps the core into slash commands, agent files with frontmatter, and settings.json hooks — producing a working system identical in capability to the current v7+v8 but structurally clean.

**Why**: Claude Code is the primary execution environment and the most mature integration point. This adapter must work end-to-end before we build others.

**Ralph Loops (3)**:
5. **Commands & Install** — Create /new-phase, /new-loop, /next-loop, /loop-status, /check-execution commands plus install.sh
6. **Agents & Settings** — Create ralph-orchestrator.md, ralph-loop-worker.md, analysis-worker.md agent files with Claude Code frontmatter; settings.json with hooks
7. **End-to-End Test** — Run a complete phase plan → ralph loops → execution cycle using the new package, verify against the practical evidence from the forex system

**Skills**: `systematic-debugging`, `verification-before-completion`

---

## Phase 3: Cowork Adapter

**Objective**: Build an adapter that makes the planning system work in Cowork mode, using routing SKILLs and the Agent tool rather than slash commands and subagent spawning.

**Why**: Cowork is a growing platform with a different execution model. The planning system's value proposition (long-running structured work) is highly relevant to Cowork users, but the integration patterns differ from Claude Code.

**Ralph Loops (2)**:
8. **Routing SKILL & Agent Integration** — Create entry-point SKILL.md, map orchestrator/worker to Cowork's Agent tool with model parameter control
9. **Snapshot Checkpoints & Testing** — Replace git-based checkpoints with file-based snapshots for environments without git; end-to-end test in Cowork

**Skills**: `skill-creator`, `verification-before-completion`

---

## Phase 4: Generic Adapter, Documentation & Open-Source Release

**Objective**: Create a framework-agnostic Python API, comprehensive documentation, worked examples, and package the whole system for open-source release.

**Why**: The planning system's patterns are general — they work with any agent framework that supports hierarchical task decomposition and bounded context windows. Open-sourcing makes these patterns available to the broader AI agent community.

**Ralph Loops (3)**:
10. **Python API** — Create state_manager.py, plan file I/O, handoff injection, with a clean API for external frameworks
11. **Documentation & Examples** — Write architecture guide, getting-started, concepts doc; extract forex system as worked example; include this restructure as second example
12. **Package & Release** — Repository structure, README, contributing guide, licence, CI (linting/validation), initial release

**Skills**: `documentation`, `verification-before-completion`

---

## Cross-Phase Principles

- **Every phase produces usable artefacts** — no phase is purely preparatory
- **The core is the single source of truth** — adapters reference core schemas, never redefine them
- **Proven patterns first** — prefer patterns validated by the 56+ loop practical evidence over theoretical improvements
- **Skill injection is woven through** — the targeted skill loading protocol is part of the core, not an adapter-specific feature
- **This plan is itself an example** — all plan files are preserved for the repository's `examples/` directory
