# Phase Manifest Entry Schema

> **Status: LOCKED** (2026-05-13). Changes require an explicit decision logged in CLAUDE.md.

**Location:** `PLANS-INDEX.md` (one entry per phase, appended to the hot manifest)
**Status:** LOCKED (2026-05-13)
**Purpose:** Hot tier entry for a completed phase. Kept in `PLANS-INDEX.md` so the main thread loads one file and gets navigable per-phase summaries for all completed phases. Size is strictly bounded so the hot manifest stays compact across a long programme.

---

## YAML Field Spec

Each entry is a YAML mapping in a list. Fields in canonical order:

| Field | Type | Required | Valid Values | Example |
|-------|------|----------|--------------|---------|
| `phase` | integer | Yes | Positive integer | `5` |
| `title` | string | Yes | Phase title from the phase plan | `"Compaction Schema Audit & Lock"` |
| `status` | string | Yes | `passed` \| `failed_v<M>` | `passed` |
| `commits` | string | Yes | `<anchor_sha>..<end_sha>` | `a1b2c3d..e4f5a6b` |
| `detail` | string | Yes | Relative path to the cold artefact | `plans/phase-completes/phase-5-complete.md` |
| `highlights` | list of strings | Yes | 1–2 one-line bullets; max 2 items | see example |

### Field Rules

- `phase`: Unquoted integer.
- `status`: Mirrors the cold artefact's `status` field. `failed_v<M>` entries persist in the manifest until superseded by a passing attempt.
- `commits`: Formatted as `<anchor_sha>..<end_sha>`. Both SHAs must be short-form (7 chars). Readable as a `git diff` range.
- `detail`: Path relative to repo root. The cold artefact must exist at this path before the manifest entry is written.
- `highlights`: Exactly 1 or 2 items. Each item is one line. If the phase produced more notable outcomes, they live in the cold artefact only — do not exceed 2 highlights to fit the 8-line ceiling.

---

## Hard Rules

These are non-negotiable. The 8-line ceiling is a hard constraint, not a guideline.

1. **≤8 lines per entry.** Count every line in the YAML block, including `- phase:`, `  highlights:`, and each `    - <bullet>`. The entry must fit within 8 lines. This is the load-budget constraint that keeps the hot manifest readable after 20+ phases.
2. **Maximum 2 highlights.** Two `highlights` bullets consume 3 lines (`highlights:` line + 2 bullets). Adding a third highlight pushes a 7-line entry to 8 and leaves no room for future fields. Cap strictly at 2.
3. **One line per bullet.** No multi-line strings, no YAML block scalars, no `|` or `>` indicators in highlight values.
4. **No prose fields.** Every field is a scalar or a bounded list. No free-text description fields are permitted in the entry.
5. **No invented fields.** Only the six fields in the spec above are permitted. Additional metadata belongs in the cold artefact.

---

## Validation Checklist

Run before appending the entry to `PLANS-INDEX.md`:

- [ ] Entry contains exactly the six fields specified: `phase`, `title`, `status`, `commits`, `detail`, `highlights`
- [ ] No additional fields are present
- [ ] Total line count of the YAML block is ≤8 lines (count manually or with `wc -l`)
- [ ] `highlights` contains no more than 2 items
- [ ] Each highlight is a single line (no newlines embedded in the string)
- [ ] `phase` is an unquoted integer
- [ ] `status` is exactly `passed` or `failed_v<M>`
- [ ] `commits` is in `<sha>..<sha>` format with 7-character SHAs
- [ ] `detail` path exists on disk before the entry is written
- [ ] **If validating in-place within `PLANS-INDEX.md`:** entry appears in ascending phase order relative to neighbouring entries. **If validating a standalone `.yaml` snippet (e.g. during schema testing or pre-append review):** skip this item — ordering cannot be verified without the surrounding file.

---

## Worked Example

```yaml
- phase: 5
  title: "Documentation and Architecture Decisions"
  status: passed
  commits: a1b2c3d..e4f5a6b
  detail: plans/phase-completes/phase-5-complete.md
  highlights:
    - Published docs/getting-started.md and docs/decisions.md
    - Gate passed first attempt; model-tier benchmarking deferred to phase-7
```

Line count: 8 lines. This is the maximum permitted structure. Removing one highlight drops to 7 lines.
