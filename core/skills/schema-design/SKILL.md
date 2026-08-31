---
name: schema-design
description: "Produce schema documents for framework artefacts: YAML frontmatter definition, ordered body sections, field rules, a validation checklist, and a worked skeleton. Mirrors the style of docs/phase-handoff.schema.md. Triggers: design schema, create schema, schema document, frontmatter spec, artefact schema."
---

# Schema Design

Produces schema documentation for a framework artefact. A schema doc is a Markdown file
that defines the frontmatter fields, required body sections, hard rules, and a validation
checklist for any file type the framework reads or writes. Consumers use the checklist to
confirm their output is correct before committing.

## When to Use

- Defining the structure of a new framework file type (state bus files, digest artefacts,
  planning documents, skill stubs)
- Updating an existing schema to add or remove fields
- Verifying that an existing artefact conforms to its schema during a gate review
- Bootstrapping a new skill, agent, or schema document that must fit a standard template

Do NOT produce a schema doc when a simple inline comment or a JSON Schema file is
sufficient. Use this skill when the artefact is Markdown with YAML frontmatter.

## Process

### 1. Identify the artefact

Determine:

- The file name pattern and canonical path (e.g. `.advanced-plans/phases/phase-N/handoff.md`)
- The purpose of the artefact (who writes it, who reads it, when)
- Any existing style reference to mirror (check `docs/` for existing schemas)

### 2. Define frontmatter fields

For each field:

- Name: lowercase, underscore-separated
- Type: `string`, `integer`, `boolean`, `list of strings`
- Required: Yes / No
- Valid values or format (ISO 8601, positive integer, enum)
- Example value

Lay out as a Markdown table with columns: `Field | Type | Required | Valid Values | Example`.

Write field rules immediately below the table:

- One rule per bullet; reference the field name in backticks
- State the rule as a constraint, not an aspiration ("must not exceed 2000" not "should be short")

### 3. Define body sections

For each required section:

- Use ATX heading level 2 (`## Section Name`)
- State in one sentence what the section contains
- List the hard rule for that section (one-liners only, single-line bullets, etc.)
- Give the exact format each bullet or entry must follow

Order sections as they must appear in the document.

### 4. Write a validation checklist

A checklist of observable conditions that can be checked programmatically or by eye.
Format:

```text
- [ ] condition (what to check, how)
```

Cover: file path, all required frontmatter fields present and non-empty, field type
constraints, all body sections present in order, hard rules per section, no prohibited
content.

### 5. Write a worked example skeleton

A fenced Markdown code block showing a minimal valid artefact:

- All required frontmatter fields with example values
- All required body sections with one-line placeholder bullets
- Shows the exact format without real content

### 6. State design authority

One sentence citing the design spec or decision record that governs this schema.
If a schema is LOCKED, state that explicitly with the lock date.

## Output Format

A single Markdown file structured as follows:

```text
# [Artefact Type] Schema

> [Status line if LOCKED; omit if not locked]

**File:** [canonical path pattern]
**Purpose:** [one sentence — who writes it, who reads it, when]

**Design authority:** [spec or decision record path]

---

## Hard Rules (non-negotiable)

[numbered list of global constraints that apply across all sections]

---

## Frontmatter Fields

[Markdown table: Field | Type | Required | Valid Values | Example]

### Field Rules

[bulleted list — one rule per field that needs one]

---

## Body Sections

[one subsection per required section, with hard rule]

---

## Validation Checklist

[checkboxes — observable conditions]

---

## Worked Example Skeleton

[fenced markdown code block with minimal valid artefact]
```

Rules:

- ASCII only: no em-dashes (use `-`), no curly quotes, no Unicode outside ASCII
- No trailing whitespace on any line
- Fenced code blocks must carry a language tag (`markdown`, `yaml`, `json`)
- LOCKED schemas must state the lock date in the status line and in CLAUDE.md decision log
