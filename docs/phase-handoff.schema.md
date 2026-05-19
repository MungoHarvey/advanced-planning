# Phase Handoff Digest Schema

> **Status: LOCKED** (2026-05-19). Changes require an explicit decision logged in CLAUDE.md.

**File:** `.advanced-plans/phases/phase-N/handoff.md`
**Purpose:** Resume seed written by `/phase-compact` at each gate pass. A model resuming
after a phase can reload this single digest and be on-task without re-reading any other
file. Phase-level analogue of the loop `done/failed/needed` handoff. Hard token ceiling.

**Design authority:** `.advanced-plans/specs/2026-05-19-phase-compact-context-compaction-design.md`
section "`handoff.md` schema".

---

## Hard Rules (non-negotiable)

1. **Pointers and one-liners only.** Never paste file contents, code blocks, or multi-line
   excerpts into the digest. One line per bullet.
2. **Token ceiling enforced.** Generation fails (non-zero exit) if the total estimated
   token count of the rendered digest exceeds `token_ceiling`. No silent truncation.
3. **Errors & issues is mandatory.** The section must always be present and non-empty.
   Write `- (none)` only if the phase was genuinely clean with zero issues.
4. **Pointers cite paths, SHAs, or named artefacts.** Not prose descriptions of content.
5. **ASCII only.** No em-dashes (use '-'), no curly quotes, no unicode characters outside
   ASCII. Required for Windows cp1252 safety.

---

## Frontmatter Fields

YAML frontmatter block at the top of the file (delimited by `---`).

| Field | Type | Required | Valid Values | Example |
|-------|------|----------|--------------|---------|
| `phase` | integer | Yes | Positive integer | `9` |
| `title` | string | Yes | Phase title from the phase plan | `".advanced-plans/ Restructure"` |
| `status` | string | Yes | `passed` \| `failed_vM` | `passed` |
| `created` | string (ISO 8601) | Yes | Timestamp when the digest was written | `2026-05-19T10:00:00Z` |
| `complete_ref` | string | Yes | Relative path to the phase complete.md artefact | `.advanced-plans/phases/phase-9/complete.md` |
| `plan_ref` | string | Yes | Relative path to the phase plan.md | `.advanced-plans/phases/phase-9/plan.md` |
| `loops_ref` | string | Yes | Relative path to the phase loops.md | `.advanced-plans/phases/phase-9/loops.md` |
| `gate_verdict_refs` | list of strings | Yes | Paths to all gate-verdict JSON files for this phase | `[.advanced-plans/gate-verdicts/phase-9-attempt-2-phase-goals-agent.json]` |
| `token_ceiling` | integer | Yes | Maximum estimated tokens for this digest | `1500` |

### Field Rules

- `phase`: Integer, not a string. Do not quote in YAML.
- `status`: Use `passed` for a gate pass. Use `failed_v1`, `failed_v2`, etc. for a failed
  attempt. The version suffix M must match the attempt number that produced this digest.
- `created`: Written by the generator at artefact creation time, not at gate review time.
- `complete_ref`, `plan_ref`, `loops_ref`: Paths relative to the repo root. Must exist on
  disk at time of generation.
- `gate_verdict_refs`: YAML list. Include all verdict files for all attempts of this phase.
  At minimum one entry. Paths relative to the repo root.
- `token_ceiling`: Default value is `1500`. May be lowered per-phase; must not exceed 2000.
  The generator estimates tokens as `ceil(len(rendered_text) / 4)` and rejects if that
  estimate exceeds this field.

---

## Body Sections

Seven required sections follow the frontmatter, in this order.

### `## What was done & why`

One bullet per material outcome of the phase. Each bullet must:
- Be exactly one line (no wrapping, no sub-bullets)
- Include both the outcome **and** the rationale — the "why"

**Hard rule: no prose paragraphs. One line per outcome.**

### `## Outcomes`

One bullet per observable end-state corresponding to a phase success criterion. Each bullet must:
- Be exactly one line
- Cite a concrete evidence pointer: a file path, a commit SHA, or a named artefact

**Hard rule: one line per outcome. Cite evidence, not descriptions.**

### `## Errors & issues encountered`

What went wrong, how it was resolved, or what remains open. Mandatory section.
- If the phase was genuinely clean, write: `- (none)`
- Otherwise: one bullet per issue; one line; state resolution or open status

**Hard rule: section always present. Never omit. Never leave empty without `- (none)`.**

### `## Files touched (pointers, not contents)`

Files that were created, read, or edited. Each bullet must:
- Be exactly one line
- Follow the format: `TYPE: \`path\` -- brief reason or change`
- TYPE is one of: `read`, `edited`, `created`, `deleted`

**Hard rule: paths only, one line each. Never include file contents.**

### `## Gate review`

A one-paragraph (1-3 sentence) summary of the gate verdict. Must reference the verdict file.
Format: prose sentence ending with `-> full verdict: <path>`.

**Hard rule: one paragraph only. Pointer to full verdict required.**

### `## Skills & methods used`

One bullet per skill or method applied across the phase. Each bullet:
- Format: `` `skill/method-name` -- what it was used for ``
- One line per entry

**Hard rule: one line per skill. No explanatory paragraphs.**

### `## Resume pointers`

A single bullet (or two at most) with the key references for resuming work. Must include
plan_ref, loops_ref, and the next action.
- Format: `Plans: <plan_ref> / <loops_ref> - Spec: <spec path> - Next: <next action>`

**Hard rule: maximum two lines. Sufficient to get a model back on-task from cold start.**

---

## Token Ceiling Enforcement

The generator estimates token count as `ceil(len(rendered_digest_text) / 4)`.

If this estimate exceeds `token_ceiling`:
- Generation exits with a non-zero error code
- The error message MUST list each section name and its estimated token count
- No partial or truncated digest is written
- No silent failure

The operator must tighten the digest (shorter bullets, fewer entries) until it fits.
Token ceiling is a quality gate, not a suggestion.

---

## Generation Decision

The generation logic lives in `platforms/python/handoff_digest.py` (zero-dependency helper
module). This is intentional: a standalone module is testable in isolation, importable by
the `/phase-compact` command and by pytest, and keeps command logic thin. The command
calls `generate_handoff_digest(phase_dir, output_path)` and handles the non-zero exit
on ceiling violation.

---

## Validation Checklist

Run before marking the artefact complete:

- [ ] File exists at `.advanced-plans/phases/phase-N/handoff.md` where N matches `phase`
- [ ] All required frontmatter fields present and non-empty (`phase`, `title`, `status`,
      `created`, `complete_ref`, `plan_ref`, `loops_ref`, `gate_verdict_refs`,
      `token_ceiling`)
- [ ] `phase` is an unquoted integer
- [ ] `status` is exactly `passed` or `failed_vM` with no trailing whitespace
- [ ] `complete_ref`, `plan_ref`, `loops_ref` are paths that exist on disk
- [ ] `gate_verdict_refs` is a non-empty YAML list; each path exists on disk
- [ ] `token_ceiling` is an integer <= 2000
- [ ] `created` is valid ISO 8601
- [ ] All seven body sections present in the required order:
      `## What was done & why`, `## Outcomes`, `## Errors & issues encountered`,
      `## Files touched (pointers, not contents)`, `## Gate review`,
      `## Skills & methods used`, `## Resume pointers`
- [ ] `## Errors & issues encountered` is non-empty (contains bullets or `- (none)`)
- [ ] No bullet in any section spans more than one line
- [ ] No prose paragraphs appear anywhere in the body (exception: `## Gate review`
      allows one paragraph)
- [ ] No file contents pasted anywhere in the digest
- [ ] Estimated token count `ceil(len(text) / 4)` <= `token_ceiling`
- [ ] All text is ASCII-only (no em-dashes, no Unicode outside ASCII range)

---

## Worked Example Skeleton

```markdown
---
phase: 9
title: ".advanced-plans/ Restructure"
status: passed
created: 2026-05-19T10:00:00Z
complete_ref: .advanced-plans/phases/phase-9/complete.md
plan_ref: .advanced-plans/phases/phase-9/plan.md
loops_ref: .advanced-plans/phases/phase-9/loops.md
gate_verdict_refs:
  - .advanced-plans/gate-verdicts/phase-9-attempt-1-phase-goals-agent.json
  - .advanced-plans/gate-verdicts/phase-9-attempt-2-phase-goals-agent.json
token_ceiling: 1500
---

## What was done & why
- Migrated all planning data from plans/ to .advanced-plans/ to isolate planning from Claude runtime -- keeps .claude/ runtime-only
- Rewrote all slash commands to target new paths -- prerequisite for any Phase 10+ work

## Outcomes
- .advanced-plans/ tree verified present with full subtree -- ls output; attempt-2 gate pass
- Old plans/, .claude/state/, .claude/logs/ confirmed deleted -- all three ls return no such dir
- pytest 72 passed -- platforms/python/tests/

## Errors & issues encountered
- Attempt-1 gate: code-review-agent found 9 double-prefix corruptions across 4 command files -- fixed in loop-036 remediation; attempt-2 passed

## Files touched (pointers, not contents)
- created: `.advanced-plans/` -- new planning data home (full tree)
- edited: `platforms/claude-code/commands/*.md` -- path updates to new layout
- edited: `CLAUDE.md` -- architecture section rewritten for new layout

## Gate review
Attempt-1 failed (double-prefix corruption in command files); attempt-2 passed at 95 confidence with all 12 criteria met and two info-level findings (stale spec ref in plan.md; install README outdated). -> full verdict: .advanced-plans/gate-verdicts/phase-9-attempt-2-phase-goals-agent.json

## Skills & methods used
- `file-migration` -- batch git mv for all planning artefacts with history preservation
- `command-rewriting` -- slash command path updates and /new-loop -> /decompose-phase rename
- `permission-config` -- hook allowlists and settings.json allow rules

## Resume pointers
- Plans: .advanced-plans/phases/phase-9/plan.md / loops.md - Spec: .advanced-plans/specs/2026-05-14-advanced-plans-restructure-design.md - Next: Phase 10 phase-compact reframe
```
