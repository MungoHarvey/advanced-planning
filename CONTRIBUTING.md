# Contributing to Advanced Planning System

Thank you for your interest in contributing. This project welcomes improvements to adapters, core skills, documentation, and the Python API.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Development Setup](#development-setup)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Adding a New Adapter](#adding-a-new-adapter)
- [Adding a Core Skill](#adding-a-core-skill)
- [Code Style](#code-style)
- [Repository Map](#repository-map)

---

## Code of Conduct

Be constructive, be kind. Criticism of ideas is welcome; criticism of people is not. Issues and PRs that are rude or dismissive will be closed.

---

## How to Contribute

**Small fixes** (typos, broken links, clarifications) — open a PR directly, no issue needed.

**Larger changes** (new adapters, new skills, API changes, architectural decisions) — open an issue first to discuss the approach before investing time in an implementation. This avoids duplicate effort and ensures the change fits the project's direction.

---

## Reporting Bugs

Open a [GitHub issue](https://github.com/MungoHarvey/advanced-planning/issues) with:

1. **What you were doing** — which command, which adapter, which loop step
2. **What you expected** — the intended behaviour
3. **What actually happened** — exact error message, unexpected output, or failure mode
4. **Environment** — Claude Code / Cowork / Python API; Claude model version if relevant

---

## Suggesting Features

Open a [GitHub issue](https://github.com/MungoHarvey/advanced-planning/issues) with the label `enhancement`. Describe:

- The use case driving the request (not just the feature itself)
- How it fits the existing three-tier architecture
- Whether it requires core changes or could be a platform adapter

---

## Development Setup

**Python API and tests:**

```bash
git clone https://github.com/MungoHarvey/advanced-planning.git
cd advanced-planning
python -m pytest platforms/python/tests/ -v
```

No external dependencies — standard library only. Python 3.10+ required.

**Claude Code adapter** — follow `setup/claude-code/README.md`.

**Cowork adapter** — follow `setup/cowork/README.md`.

---

## Submitting a Pull Request

1. Fork the repository and create a branch from `main`
2. Make your changes
3. Run the test suite: `python -m pytest platforms/python/tests/ -v`
4. Check all items in the PR checklist below
5. Open a PR with a clear title and description of what changed and why

**PR title format:**
- `fix: [description]` — bug fix
- `feat: [description]` — new feature or adapter
- `docs: [description]` — documentation only
- `refactor: [description]` — structural change with no behaviour change
- `test: [description]` — tests only

### PR Checklist

Before opening a PR, confirm all items:

- [ ] **Portability scan clean** — no absolute local paths or session IDs in committed files
- [ ] **No secrets** — no API keys, tokens, passwords, or credentials anywhere
- [ ] **Tests pass** — `python -m pytest platforms/python/tests/ -v` returns green
- [ ] **No new external dependencies** — `platforms/python/*.py` must import standard library only
- [ ] **Schema valid** — if modifying `core/state/*.schema.json`, run `python -m json.tool` to validate
- [ ] **Docs updated** — if adding a concept or changing behaviour, update `docs/concepts.md` or the relevant doc
- [ ] **Adapter README current** — if modifying an adapter, README reflects the change

---

## Adding a New Adapter

An adapter wraps the platform-agnostic core in the conventions of a specific execution environment. The minimum required files:

1. `platforms/[platform]/README.md` — setup guide and quick-start
2. `platforms/[platform]/agents/orchestrator-prompt.md` — self-contained orchestrator prompt
3. `platforms/[platform]/agents/worker-prompt.md` — self-contained worker prompt with targeted skill injection
4. One entry-point file (slash command, routing skill, Python module, etc.)

**Before submitting:**
- Zero references to other platforms' internal paths (e.g. no `.claude/` in a Cowork adapter)
- Skills directory path in the worker prompt matches the actual skills location
- Run the adapter through at least one loop end-to-end
- Troubleshooting section in the README covering the top three failure modes

See `docs/adapting-to-new-platforms.md` for the full five-contract adapter specification.

---

## Adding a Core Skill

Core skills live in `core/skills/[skill-name]/SKILL.md`. A skill is a self-contained instruction set loaded by the worker agent immediately before executing a matching todo.

**Required frontmatter:**

```yaml
---
name: my-skill
model: opus        # or sonnet, haiku
description: "One sentence: what this skill does and when to load it."
---
```

**Required sections in the skill body:**

- `## When to Use` — trigger conditions
- `## Process` — step-by-step instructions
- `## Output Format` — what a correct output looks like

**Recommended additions:**

- `references/` subdirectory — templates, schemas, worked examples
- `## Anti-patterns` — common mistakes to avoid
- Entry in `core/skills/plan-skill-identification/references/skill-catalogue.md` — so the orchestrator can assign it automatically

---

## Code Style

**Python** (`platforms/python/`):
- Type hints on all public function signatures
- Docstrings on all public functions (NumPy style)
- Standard library only — no external dependencies in core API modules
- Tests in `platforms/python/tests/` using pytest; one class per function group

**Markdown** (everything else):
- ATX-style headers (`##`, not underline style)
- Fenced code blocks with language tag
- Tables for structured comparisons; prose for explanations
- No trailing whitespace

**Shell scripts** (`checkpoint.sh`, `install.sh`):
- POSIX sh (`#!/bin/sh`, not `#!/bin/bash`)
- `set -e` at the top
- Quoted variables throughout (`"$VAR"`)
- `--help` or no-args usage block

---

## Repository Map

```
advanced-planning/
├── core/                     <- Platform-agnostic. Shared by all adapters.
│   ├── schemas/              <- Markdown schema docs for plan file types
│   ├── skills/               <- Planning skills (loaded per-todo by the worker)
│   │   └── [skill-name]/
│   │       ├── SKILL.md
│   │       └── references/   <- Templates, worked examples, reference catalogues
│   ├── agents/               <- Orchestrator and worker role definitions
│   └── state/                <- JSON schemas for state bus files
│
├── platforms/                <- Platform-specific wrappers
│   ├── claude-code/          <- Slash commands, hooks, settings.json
│   ├── cowork/               <- Routing SKILL.md, agent prompts, checkpoint.sh
│   └── python/               <- Python API + unit tests + framework examples
│
├── setup/                    <- Installation guides and scripts
│   ├── claude-code/          <- install.sh + setup guide
│   └── cowork/               <- create-zip.sh + setup guide
│
├── docs/                     <- User-facing documentation
├── examples/                 <- Worked programme examples
└── plans/                    <- The plan files used to build this repository
```

---

## Licence

By contributing, you agree that your contributions will be released under the [MIT Licence](LICENCE).
