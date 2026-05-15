# Phase 4 — Ralph Loops: Generic Adapter, Documentation & Release

Loops 010–012 complete the open-source release: a framework-agnostic Python API, a full documentation suite with worked examples, and release packaging.

---

## ralph-loop-010: Python API

```yaml
name: "ralph-loop-010"
task_name: "Python API"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: "Python API complete: state_manager.py (write_loop_ready, read_loop_complete, append_history, get_status), plan_io.py (find_next_loop, parse_loop_frontmatter, get_pending_todos, update_todo_status, get_loop_handoff), handoff.py (read_handoff, inject_handoff, build_context_block, make_empty_handoff). 40 unit tests — all passing. platforms/python/README.md with full API reference."
  failed: ""
  needed: "Begin loop-011: create docs/ suite starting with concepts.md, then architecture.md, getting-started.md, model-tier-strategy.md, adapting-to-new-platforms.md, decisions.md; create worked examples and framework skeletons."

todos:
  - id: "loop-010-1"
    content: "Create platforms/python/__init__.py and platforms/python/tests/__init__.py to make the package importable"
    skill: "NA"
    agent: "NA"
    outcome: "Both __init__.py files exist; platforms/python/ is a valid Python package"
    status: completed
    priority: high

  - id: "loop-010-2"
    content: "Create platforms/python/state_manager.py — functions to write loop-ready.json, read loop-complete.json, append to history.jsonl, and query current loop status"
    skill: "NA"
    agent: "NA"
    outcome: "state_manager.py exists with write_loop_ready(), read_loop_complete(), append_history(), and get_status() functions; type hints and docstrings throughout"
    status: completed
    priority: high

  - id: "loop-010-3"
    content: "Create platforms/python/plan_io.py — functions to find the next pending loop across plan files, parse a loop's YAML frontmatter, extract todos, and write updated frontmatter back"
    skill: "NA"
    agent: "NA"
    outcome: "plan_io.py exists with find_next_loop(), parse_loop_frontmatter(), get_pending_todos(), and update_todo_status() functions; handles missing fields gracefully"
    status: completed
    priority: high

  - id: "loop-010-4"
    content: "Create platforms/python/handoff.py — functions to read a prior loop's handoff_summary and inject done/failed/needed into a prompt template string"
    skill: "NA"
    agent: "NA"
    outcome: "handoff.py exists with read_handoff() and inject_handoff() functions; inject_handoff() replaces [inject prior.handoff_summary.X] placeholders in template strings"
    status: completed
    priority: high

  - id: "loop-010-5"
    content: "Create platforms/python/tests/test_state_manager.py — unit tests covering write/read round-trip for loop-ready.json, loop-complete.json, and history.jsonl append"
    skill: "NA"
    agent: "NA"
    outcome: "test_state_manager.py exists with at least 5 tests; all pass with python -m pytest platforms/python/tests/test_state_manager.py"
    status: completed
    priority: high

  - id: "loop-010-6"
    content: "Create platforms/python/tests/test_plan_io.py and platforms/python/tests/test_handoff.py — unit tests for YAML parsing, todo extraction, and handoff injection"
    skill: "NA"
    agent: "NA"
    outcome: "Both test files exist with at least 4 tests each; all pass with python -m pytest platforms/python/tests/"
    status: completed
    priority: high

  - id: "loop-010-7"
    content: "Run full test suite and confirm all tests pass; create platforms/python/README.md with install instructions and API reference"
    skill: "NA"
    agent: "NA"
    outcome: "python -m pytest platforms/python/tests/ shows all tests passing; platforms/python/README.md documents each module's public API with usage examples"
    status: completed
    priority: high
```

## Overview

Build the minimal Python library that framework developers can import to integrate the planning system into LangGraph, CrewAI, AutoGen, or any other agent framework. The API wraps the filesystem state bus (loop-ready.json / loop-complete.json / history.jsonl) and plan file I/O into clean, typed Python functions — no knowledge of the raw file formats required.

The library is intentionally minimal: three modules, one file each, no dependencies beyond the standard library (pathlib, json, re, datetime). Framework integration is shown in examples (loop 011), not in the library itself.

## Success Criteria

- ✓ `state_manager.py`, `plan_io.py`, and `handoff.py` exist with documented public APIs
- ✓ All unit tests pass (`python -m pytest platforms/python/tests/`)
- ✓ No external dependencies (standard library only)
- ✓ `platforms/python/README.md` covers install and API reference

## Skills Required

- Standard Python — type hints, docstrings, pathlib, json, re

## Dependencies
- Phase 1 state schemas must be finalised (they are)

## Complexity
**Scope**: Medium — 7 files; the API is small but tests require fixtures
**Estimated effort**: 2–3 hours

---

## ralph-loop-011: Documentation & Examples

```yaml
name: "ralph-loop-011"
task_name: "Documentation & Examples"
max_iterations: 3
on_max_iterations: checkpoint

handoff_summary:
  done: "Documentation suite complete: docs/concepts.md (9 definitions), docs/architecture.md (5 architectural decisions, ASCII diagrams), docs/getting-started.md (5-step Claude Code tutorial), docs/model-tier-strategy.md (cost table, override guidance), docs/adapting-to-new-platforms.md (5-contract checklist, Cowork walkthrough), docs/decisions.md (8 decisions with rationale), examples/planning-system-restructure/README.md, and three framework skeletons (langgraph, crewai, autogen) each with README."
  failed: ""
  needed: "Begin loop-012: create root README.md, CONTRIBUTING.md, LICENCE (Apache 2.0), .gitignore, .github/workflows/ci.yml, and run final portability scan."

todos:
  - id: "loop-011-1"
    content: "Create docs/concepts.md — authoritative glossary covering: ralph loop, handoff summary, targeted skill injection, state bus, phase plan, model tier, on_max_iterations"
    skill: "NA"
    agent: "NA"
    outcome: "docs/concepts.md exists; every term used in other docs is defined here; each definition includes a one-sentence explanation and a concrete example"
    status: completed
    priority: high

  - id: "loop-011-2"
    content: "Create docs/architecture.md — full system architecture: three-tier hierarchy diagram (ASCII), two-agent pattern, state bus flow, targeted skill injection explanation, platform adapter model"
    skill: "NA"
    agent: "NA"
    outcome: "docs/architecture.md exists with ASCII sequence diagram, state bus diagram, and prose explanation of all five architectural decisions"
    status: completed
    priority: high

  - id: "loop-011-3"
    content: "Create docs/getting-started.md — tutorial for a developer's first loop using the Claude Code adapter: install, CLAUDE.md setup, /new-phase, /new-loop, /next-loop, verify outputs"
    skill: "NA"
    agent: "NA"
    outcome: "docs/getting-started.md leads a developer from zero to a completed first loop in under 30 minutes; every command is shown verbatim; expected outputs are described"
    status: completed
    priority: high

  - id: "loop-011-4"
    content: "Create docs/model-tier-strategy.md — guide to model selection: Opus/Sonnet/Haiku economics table, when to override defaults, cost estimation, and the rationale for targeted skill injection at the Haiku tier"
    skill: "NA"
    agent: "NA"
    outcome: "docs/model-tier-strategy.md exists with cost/capability table, worked cost estimate for a 4-phase programme, and guidance on overriding the defaults"
    status: completed
    priority: medium

  - id: "loop-011-5"
    content: "Create docs/adapting-to-new-platforms.md — guide for building a new platform adapter: what the five adapter contracts are, a minimal adapter checklist, and the Cowork adapter as a worked example"
    skill: "NA"
    agent: "NA"
    outcome: "docs/adapting-to-new-platforms.md exists with 5-contract adapter checklist, annotated Cowork adapter walkthrough, and a template for a minimal adapter README"
    status: completed
    priority: medium

  - id: "loop-011-6"
    content: "Create examples/planning-system-restructure/README.md — a guide to reading this repository's own planning files as a worked example of the system"
    skill: "NA"
    agent: "NA"
    outcome: "examples/planning-system-restructure/README.md explains what the example shows, how to navigate the 4 phase plans, what patterns to look for in the loop files, and links to the key decisions"
    status: completed
    priority: high

  - id: "loop-011-7"
    content: "Create platforms/python/examples/ with three framework skeletons: langgraph/example.py, crewai/example.py, autogen/example.py — each showing how to use the Python API to drive a single loop"
    skill: "NA"
    agent: "NA"
    outcome: "Three example files exist; each imports from platforms/python and shows write_loop_ready(), read_loop_complete(), and inject_handoff() being called in the framework's agent invocation pattern; each has a companion README.md"
    status: completed
    priority: medium

  - id: "loop-011-8"
    content: "Create docs/decisions.md — a curated log of the key architectural decisions made during this restructure, with context and rationale for each"
    skill: "NA"
    agent: "NA"
    outcome: "docs/decisions.md exists with at least 8 decisions documented (targeted skill injection, two-agent pattern, state bus design, handoff_summary fields, model tier assignments, snapshot vs git, routing SKILL vs slash commands, Apache 2.0 licence)"
    status: completed
    priority: medium
```

## Overview

Write the documentation suite and worked examples that make the repository self-contained for a developer who has never seen the system. The goal is a developer can clone the repo, read the docs, and run their first loop — with no external guidance.

This loop is writing-heavy. Each doc should be written for its specific audience: getting-started.md targets a developer skimming for quick-start steps; architecture.md targets someone who wants to understand the design before using it; concepts.md is a reference to look terms up in.

## Success Criteria

- ✓ All 5 docs in `docs/` cover their stated scope
- ✓ Framework examples each have a runnable (or near-runnable) skeleton and a README
- ✓ `examples/planning-system-restructure/README.md` helps a newcomer navigate this project's own plan files
- ✓ `docs/decisions.md` has at least 8 decisions with rationale

## Skills Required

- Technical writing — clarity, structure, audience awareness
- No code execution required (examples are skeletons, not end-to-end runnable)

## Dependencies
- Loop 010 must be complete (docs reference the Python API)

## Complexity
**Scope**: Medium-High — 8 files, all substantial writing
**Estimated effort**: 3–4 hours

---

## ralph-loop-012: Package & Release

```yaml
name: "ralph-loop-012"
task_name: "Package & Release"
max_iterations: 2
on_max_iterations: checkpoint

handoff_summary:
  done: "Release packaging complete: README.md (elevator pitch, quick-start, adapter table, docs index), CONTRIBUTING.md (repo map, 3-section guide, 6-item PR checklist), LICENCE (Apache 2.0, 2025 Mungo Harvey), .gitignore (Python, OS, .claude/, snapshots, secrets), .github/workflows/ci.yml (3 jobs: markdown-lint, schema-validation, python-tests on 3.10/3.11/3.12), docs/release-checklist.md (12-item checklist), and final portability scan clean (78 files, zero session paths, zero secrets, zero deprecated stubs)."
  failed: ""
  needed: ""

todos:
  - id: "loop-012-1"
    content: "Create root README.md — the repository's front page: what the system is, why it exists, quick-start (5 steps), links to all adapters, link to docs, badge placeholders"
    skill: "NA"
    agent: "NA"
    outcome: "README.md exists at repo root with: elevator pitch (2 sentences), architecture diagram (ASCII), quick-start steps, adapter comparison table, docs index, and licence/contributing links"
    status: completed
    priority: high

  - id: "loop-012-2"
    content: "Create CONTRIBUTING.md — how to contribute: repo structure walkthrough, how to add a new adapter, how to add a new core skill, PR checklist, code style notes"
    skill: "NA"
    agent: "NA"
    outcome: "CONTRIBUTING.md exists with repo map, 3-section contribution guide (platforms/skills/docs), PR checklist with 6 items, and style notes"
    status: completed
    priority: medium

  - id: "loop-012-3"
    content: "Create LICENCE (Apache 2.0 full text) and .gitignore (Python, node_modules, OS files, .claude/ directory, state/snapshots/)"
    skill: "NA"
    agent: "NA"
    outcome: "LICENCE contains full Apache 2.0 text with correct year and author; .gitignore excludes .claude/, state/snapshots/, __pycache__, .DS_Store, *.pyc, and common secrets patterns"
    status: completed
    priority: high

  - id: "loop-012-4"
    content: "Create .github/workflows/ci.yml — CI pipeline: markdown link check, JSON schema validation for loop-ready/loop-complete schemas, Python test run for platforms/python/tests/"
    skill: "NA"
    agent: "NA"
    outcome: ".github/workflows/ci.yml is valid YAML; defines 3 jobs (markdown-lint, schema-validation, python-tests); triggers on push and pull_request to main"
    status: completed
    priority: medium

  - id: "loop-012-5"
    content: "Run final portability scan: verify no internal paths, no secrets patterns, no deprecated directory names across the entire repo"
    skill: "NA"
    agent: "NA"
    outcome: "grep scans confirm: zero occurrences of internal paths (gifted-awesome-heisenberg, /sessions/); zero occurrences of secret patterns (api_key=, token=, password=); no deprecated stubs (phase-plan-creator-mh/, phase-plan-creator-claude/)"
    status: completed
    priority: high

  - id: "loop-012-6"
    content: "Create docs/release-checklist.md — a pre-publication checklist covering: portability scan, colleague review, CI green, all docs cross-checked, example READMEs accurate, LICENCE and CONTRIBUTING present"
    skill: "NA"
    agent: "NA"
    outcome: "docs/release-checklist.md exists with a 12-item markdown checklist; each item is a verifiable checkbox with the command or action that confirms it"
    status: completed
    priority: medium

  - id: "loop-012-7"
    content: "Verify repository structure: run find to confirm all expected directories and key files exist; produce a final file tree summary"
    skill: "NA"
    agent: "NA"
    outcome: "find output confirms: core/{schemas,skills,agents,state}, platforms/{claude-code,cowork,generic}, docs/, examples/, plans/ all exist with their expected files; summary written to docs/release-checklist.md verification section"
    status: completed
    priority: high
```

## Overview

Prepare the repository for public release. This loop is about packaging, polish, and verification — not new functionality. Every file created here makes the repository usable by someone who has never seen it before.

The portability scan (loop-012-5) is the critical gate: any internal paths or secrets that leak into the public repository would be a serious problem. Run it last, after all other files are in place.

## Success Criteria

- ✓ `README.md` at repo root passes the "30-second test" (what it is and how to start are immediately clear)
- ✓ CI workflow covers markdown linting, JSON schema validation, and Python tests
- ✓ Portability scan returns clean across the full repo
- ✓ `LICENCE`, `CONTRIBUTING.md`, and `.gitignore` all present and complete

## Skills Required

- Repository management — CI YAML, .gitignore patterns, Apache 2.0 licence text
- Technical writing — README, CONTRIBUTING

## Dependencies
- Loops 010 and 011 must be complete (README references them; portability scan covers all files)

## Complexity
**Scope**: Low-Medium — 6 files, mostly templated or formulaic; portability scan is the most critical step
**Estimated effort**: 1.5–2 hours
