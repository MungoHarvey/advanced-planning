# Schemas Index

Schema documents for the advanced-planning framework. Platform-agnostic; referenced by all adapters.

---

## Core Schemas (`core/schemas/`)

| Schema | Description |
|--------|-------------|
| [handoff.schema.md](handoff.schema.md) | Three-field handoff summary (`done`/`failed`/`needed`) carried between loops |
| [phase-plan.schema.md](phase-plan.schema.md) | Phase plan frontmatter and body structure; defines phase metadata and success criteria |
| [ralph-loop.schema.md](ralph-loop.schema.md) | Ralph loop YAML frontmatter, todos array, prompt structure, and handoff fields |
| [todo.schema.md](todo.schema.md) | Individual todo item fields, canonical field order, and outcome writing rules |

---

## Compaction Schemas (`docs/`)

Produced in Phase 6. These are the contracts for the phase-compactor agent and `/phase-compact` command.

| Schema | Description |
|--------|-------------|
| [docs/phase-complete.schema.md](../../docs/phase-complete.schema.md) | Cold artefact schema for `plans/phase-completes/phase-N-complete.md`; defines frontmatter fields, body section rules, anchor SHA mechanism, and validation checklist |
| [docs/phase-manifest-entry.schema.md](../../docs/phase-manifest-entry.schema.md) | Hot manifest entry schema for `PLANS-INDEX.md`; enforces the ≤8-line hard ceiling per phase entry and max 2 highlights |
