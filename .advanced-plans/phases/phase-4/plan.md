# Phase 4: Generic Adapter, Documentation & Open-Source Release

## Objective

Create a framework-agnostic Python API for the planning system, write comprehensive documentation, prepare worked examples, and package everything for publication as an open-source GitHub repository that colleagues and the broader AI agent community can use.

---

## Scope

### Included

- **Python API**: `state_manager.py` (filesystem state bus), `plan_io.py` (plan file reading/writing), `handoff.py` (handoff injection) — a minimal library that any framework can import
- **Framework examples**: Skeleton integrations showing how to use the API with LangGraph, CrewAI, and AutoGen
- **Documentation suite**: Architecture guide, getting-started tutorial, concepts reference, model-tier strategy guide, and platform adaptation guide
- **Worked examples**: The forex trading system (extracted from plans-in-practice-reporting) and this restructure plan itself
- **Repository packaging**: README, CONTRIBUTING.md, LICENCE, .gitignore, basic CI (markdown linting, JSON schema validation)

### Explicitly NOT included

- Full production integrations with LangGraph/CrewAI/AutoGen (examples only, not maintained adapters)
- A web UI or dashboard
- A package manager distribution (PyPI/npm) — direct GitHub installation for now
- Hosting or SaaS features

---

## Key Deliverables

| Deliverable | Format | Location |
|-------------|--------|----------|
| State manager | Python module | `platforms/python/state_manager.py` |
| Plan I/O | Python module | `platforms/python/plan_io.py` |
| Handoff injection | Python module | `platforms/python/handoff.py` |
| LangGraph example | Python + README | `platforms/python/examples/langgraph/` |
| CrewAI example | Python + README | `platforms/python/examples/crewai/` |
| AutoGen example | Python + README | `platforms/python/examples/autogen/` |
| Architecture guide | Markdown | `docs/architecture.md` |
| Getting started | Markdown | `docs/getting-started.md` |
| Concepts reference | Markdown | `docs/concepts.md` |
| Model tier strategy | Markdown | `docs/model-tier-strategy.md` |
| Platform adaptation guide | Markdown | `docs/adapting-to-new-platforms.md` |
| Decisions log | Markdown (migrated from DECISIONS.md) | `docs/decisions.md` |
| Forex trading example | Plan files + README | `examples/trading-system/` |
| Restructure example | Plan files (this plan) + README | `examples/planning-system-restructure/` |
| Root README | Markdown | `README.md` |
| Contributing guide | Markdown | `CONTRIBUTING.md` |
| Licence | Text | `LICENCE` |

---

## Success Criteria

- ✓ **Python API functional**: `state_manager.py` can create, read, and advance loop state; `plan_io.py` can parse a ralph loop's frontmatter and extract todos; `handoff.py` can inject a prior loop's handoff into a prompt template. All with unit tests.
- ✓ **Framework examples run**: Each example directory has a README that a developer can follow to see the planning system coordinating agents in their framework of choice
- ✓ **Documentation complete**: A developer who has never seen the system can understand the architecture, install an adapter, and run their first loop using only the documentation — no external guidance needed
- ✓ **Worked examples navigable**: Both examples include a README explaining what the plan achieved, how to read the loop files, and what patterns to look for
- ✓ **Repository publishable**: Clean git history, no secrets, no internal paths, no deprecated files, clear licence, CI passing
- ✓ **Colleague feedback**: At least one colleague has reviewed the repository structure and documentation before public release

---

## Dependencies

### Must Complete Before

- Phase 1: Core Architecture Design — schemas and skills must be finalised
- Phase 2: Claude Code Adapter — must be working (validates the core)
- Phase 3: Cowork Adapter — should be working (provides second adapter example)

### Blocked By

- GitHub repository creation (can be done at any point; not blocking design work)
- Licence decision (recommend Apache 2.0 for maximum reuse)

### Optional

- Review by Anthropic colleagues familiar with Claude Code internals
- Community feedback from early testers

---

## Skills Required (Broad Categories)

- `python-development`: Clean API design with type hints and docstrings
- `documentation`: Technical writing for diverse audiences (developers, researchers, AI practitioners)
- `verification-before-completion`: Testing all examples end-to-end
- `repository-management`: Git hygiene, CI setup, release preparation

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Framework APIs change (LangGraph/CrewAI/AutoGen) | Medium | Low | Examples are labelled with framework version; README notes they are illustrative, not maintained integrations |
| Documentation becomes stale as system evolves | Medium | Medium | Keep docs co-located with code; add "last verified" dates; CI checks for broken internal links |
| Forex example contains sensitive data | Low | High | Scrub all API keys, credentials, account IDs before extraction; review every file manually |
| Scope creep into building full framework integrations | Medium | Medium | Explicitly scope as "examples" not "platforms"; the generic adapter is the Python API, not framework-specific code |

---

## Assumptions

- `Apache 2.0 is appropriate`: Permissive licence allowing commercial use and modification. Validated by: standard for developer tools and AI agent frameworks.
- `GitHub is the right platform`: Industry standard for open-source AI tooling. Validated by: target audience (AI developers, researchers) is concentrated on GitHub.
- `Markdown-first documentation works`: Developers in this space prefer reading markdown in-repo to external documentation sites. Validated by: convention in the Claude Code ecosystem.

---

## Notes / Design Decisions

- **Why a Python API not a CLI**: The generic adapter's users are developers integrating with frameworks. They want to `import planning_system` and call functions, not shell out to a CLI. The CLI already exists as the Claude Code adapter.
- **Why framework examples not full integrations**: Maintaining production integrations with three rapidly-evolving frameworks would be unsustainable. Examples show the pattern; developers adapt to their specific framework version.
- **Why two worked examples**: The forex system shows a complex, real-world, multi-month programme. This restructure plan shows a focused, well-scoped project. Together they demonstrate the system's range.
- **Why colleague review before public release**: Fresh eyes catch assumptions that are obvious to the author but opaque to newcomers. At minimum, one person should be able to install and run a loop using only the documentation.

---

## Ralph Loops (3)

| Loop | Name | Type | Key Outputs |
|------|------|------|-------------|
| 010 | Python API | Implementation | 3 Python modules + unit tests in `platforms/python/` |
| 011 | Documentation & Examples | Writing + Extraction | 6 doc files + 2 worked examples + 3 framework examples |
| 012 | Package & Release | Packaging + Verification | README, CONTRIBUTING, LICENCE, CI, clean git history, colleague review |
