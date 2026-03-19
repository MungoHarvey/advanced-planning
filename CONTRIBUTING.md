# Contributing

Contributions to the Advanced Planning System are welcome. This document covers how the repository is structured, how to add new adapters and skills, and what the PR checklist requires.

---

## Repository Map

```
advanced-planning/
│
├── core/                     ← Platform-agnostic. Shared by all adapters.
│   ├── schemas/              ← Markdown schema docs for plan file types
│   ├── skills/               ← Opus-tier planning skills
│   │   └── [skill-name]/
│   │       ├── SKILL.md      ← The skill itself (frontmatter + instructions)
│   │       └── references/   ← Templates and worked examples
│   ├── agents/               ← Orchestrator and worker role definitions
│   └── state/                ← JSON schemas for state bus files
│
├── platforms/                 ← Platform-specific wrappers
│   ├── claude-code/          ← Slash commands, hooks, settings.json, install.sh
│   ├── cowork/               ← Routing SKILL.md, agent prompts, checkpoint.sh
│   └── python/               ← Python API + unit tests + framework examples
│
├── docs/                     ← User-facing documentation
├── examples/                 ← Worked programme examples
└── plans/                    ← The plan files used to build this repository
```

---

## How to Add a New Adapter

An adapter wraps the core in a new execution environment. The minimum files required:

1. `platforms/[platform]/README.md` — setup guide and quick-start
2. `platforms/[platform]/agents/orchestrator-prompt.md` — self-contained orchestrator prompt with platform path conventions
3. `platforms/[platform]/agents/worker-prompt.md` — self-contained worker prompt with targeted skill injection protocol
4. One entry-point file (slash command, routing skill, Python module, etc.)

Before submitting:
- Confirm zero references to other platforms' internal paths (e.g. no `.claude/` in a Cowork adapter)
- Confirm skills directory path in the worker prompt matches the actual skills location
- Run the adapter through at least one loop end-to-end
- Add a troubleshooting section to the README covering the top 3 failure modes

See `docs/adapting-to-new-platforms.md` for the full five-contract adapter specification.

---

## How to Add a New Core Skill

Core skills live in `core/skills/[skill-name]/SKILL.md`. A skill is a self-contained instruction set loaded by the worker agent per-todo.

Skill frontmatter:
```yaml
---
name: my-skill
description: "One-line description of when to load this skill"
model: opus   # or sonnet, haiku — the tier this skill is designed for
version: 1.0
---
```

Skill content should include:
- **Purpose** — what tasks this skill is designed to assist with
- **Instructions** — specific guidance for executing those tasks
- **Output standards** — what a well-formed output looks like
- **Anti-patterns** — what to avoid

After adding a skill:
- Add it to the `plan-skill-identification` skill's reference list so the orchestrator can assign it
- Test it by including it in a loop's todo and verifying the output quality improvement

---

## How to Add Documentation

Documentation lives in `docs/`. All files are Markdown.

- Keep docs co-located with the code they describe
- Add a "last verified" date to docs that reference specific file paths or commands
- Run a link check before submitting (`markdownlint-cli2` or equivalent)

---

## Pull Request Checklist

Before opening a PR, confirm all items:

- [ ] **Portability scan clean**: no internal paths (session IDs, absolute local paths) in committed files
- [ ] **No secrets**: no API keys, tokens, passwords, or credentials in any file
- [ ] **JSON schema valid**: if modifying `core/state/*.schema.json`, validate with `python -m json.tool`
- [ ] **Tests pass**: `python -m pytest platforms/python/tests/ -v` returns green
- [ ] **Adapter README updated**: if modifying an adapter, README reflects the change
- [ ] **Docs cross-checked**: if adding a new concept or changing behaviour, `docs/concepts.md` or the relevant doc is updated

---

## Code Style Notes

**Python** (`platforms/python/`):
- Type hints on all public function signatures
- Docstrings on all public functions (NumPy style)
- Standard library only — no external dependencies in the core API modules
- Tests in `platforms/python/tests/` using pytest; one test class per function group

**Markdown** (everything else):
- ATX-style headers (`##`, not underlines)
- Fenced code blocks with language tag (` ```bash `, ` ```yaml `, etc.)
- Tables for structured comparisons; prose for explanations
- No trailing whitespace

**Shell scripts** (`checkpoint.sh`, `install.sh`):
- POSIX sh, not bash-specific (`#!/bin/sh`)
- `set -e` at the top
- Quoted variables throughout (`"$VAR"`)
- `--help` or no-args usage block required
