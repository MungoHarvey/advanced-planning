# Phase Complete Schema

> **Status: LOCKED** (2026-05-13). Changes require an explicit decision logged in CLAUDE.md.

**File:** `plans/phase-completes/phase-N-complete.md`
**Status:** LOCKED (2026-05-13)
**Purpose:** Cold artefact produced by `phase-compactor` at each gate pass. Serves as a structured index into git for a completed phase. Loaded on demand via `/load-phase-context N`. Never a substitute for git diffs — pointers only.

---

## Frontmatter Fields

YAML frontmatter block at the top of the file (delimited by `---`).

| Field | Type | Required | Valid Values | Example |
|-------|------|----------|--------------|---------|
| `phase` | integer | Yes | Positive integer | `5` |
| `title` | string | Yes | Phase title from the phase plan | `"Compaction Schema Audit & Lock"` |
| `status` | string | Yes | `passed` \| `failed_v<M>` | `passed` |
| `gate_verdict_ref` | string | Yes | Relative path to the gate-verdict JSON for this phase, OR the sentinel value `"n/a — pre-gate-review phase"` if no verdict file exists | `plans/gate-verdicts/phase-5-attempt-1-phase-goals-agent.json` |
| `gate_verdict_note` | string | No | One-line explanation when `gate_verdict_ref` is the sentinel value | `"Phase predates gate review system"` |
| `anchor_sha` | string | Yes | Short SHA of the first commit in this phase | `e199cca` |
| `end_sha` | string | Yes | Short SHA of the last commit in this phase (gate-pass commit) | `34ea21f` |
| `commit_count` | integer | Yes | Number of commits between anchor and end (inclusive) | `12` |
| `loop_count` | integer | Yes | Number of ralph loops executed in this phase | `6` |
| `created` | string (ISO 8601) | Yes | Timestamp when the compactor wrote this file | `2026-05-13T10:00:00Z` |

### Field Rules

- `phase`: Integer, not a string. Do not quote in YAML.
- `status`: Use `passed` for a gate pass. Use `failed_v1`, `failed_v2`, etc. for failed attempts. The superseded file retains its version suffix; the passing attempt's artefact uses `passed`.
- `gate_verdict_ref`: Path relative to the repo root. Points to the `phase-goals-agent` verdict file. If multiple gate agents ran, reference the `phase-goals-agent` verdict only — it is the compactor's primary input. For phases that completed before the gate review system existed (or that were not run through gate review), use the sentinel value `"n/a — pre-gate-review phase"` and supply a `gate_verdict_note` explaining why no verdict file exists.
- `gate_verdict_note`: Optional. Required when `gate_verdict_ref` is the sentinel value. One sentence only. Omit entirely when a real verdict path is present.
- `anchor_sha` and `end_sha`: Short SHAs (7 characters). Must be verifiable via `git log --oneline`.
- `commit_count`: Count from anchor to end inclusive. Computed via `git rev-list --count <anchor_sha>..<end_sha>` plus one for the anchor itself, or equivalent.
- `created`: Written by the compactor at artefact creation time, not at gate review time.

---

## Body Sections

Three required sections follow the frontmatter, in this order.

### `## Goals met`

One bullet per success criterion that was satisfied during this phase. Each bullet must:
- Be exactly one line (no wrapping, no sub-bullets)
- Reference a concrete evidence pointer: a file path, a commit SHA, or a commit range

**Hard rule: no prose paragraphs. One line per goal.**

### `## Deferred`

One bullet per goal explicitly deferred to a later phase. A deferral is a conscious scope decision, not a failure. Each bullet must:
- Be exactly one line
- Name the target phase if known (e.g. `→ phase-7`)
- Include a one-phrase reason why it was deferred

If nothing was deferred, write: `- (none)`

**Hard rule: one line per deferral. No explanatory paragraphs.**

### `## Opened`

One bullet per new question, known issue, or follow-up surfaced during the phase that was not in the original success criteria. Each bullet must:
- Be exactly one line
- Be actionable or attributable (not vague observations)

If nothing was opened, write: `- (none)`

**Hard rule: one line per item. No prose.**

---

## Anchor SHA Decision

See [Anchor SHA Decision](#anchor-sha-decision-1) section below.

---

## Validation Checklist

Run before marking the artefact complete:

- [ ] File exists at `plans/phase-completes/phase-N-complete.md` where N matches the `phase` field
- [ ] All required frontmatter fields are present and non-empty (`phase`, `title`, `status`, `gate_verdict_ref`, `anchor_sha`, `end_sha`, `commit_count`, `loop_count`, `created`); `gate_verdict_note` is optional and only required when `gate_verdict_ref` is the sentinel value
- [ ] `phase` is an unquoted integer
- [ ] `status` is exactly `passed` or `failed_v<M>` with no trailing whitespace
- [ ] `gate_verdict_ref` is either a path that exists on disk OR the exact sentinel value `"n/a — pre-gate-review phase"`; if sentinel, `gate_verdict_note` is present and non-empty
- [ ] `anchor_sha` and `end_sha` resolve via `git rev-parse --short <sha>` without error
- [ ] `commit_count` matches `git rev-list --count <anchor_sha>..<end_sha>` output (allowing ±1 for boundary inclusion)
- [ ] `loop_count` matches the number of loops marked `completed` in the phase's ralph-loops file
- [ ] `created` is valid ISO 8601
- [ ] `## Goals met` section is present; each bullet is one line with a concrete evidence pointer
- [ ] `## Deferred` section is present; contains bullets or `- (none)`
- [ ] `## Opened` section is present; contains bullets or `- (none)`
- [ ] No bullet in any body section spans more than one line
- [ ] No prose paragraphs appear anywhere in the body

---

## Anchor SHA Decision

**Chosen mechanism:** Frontmatter field `anchor_sha` on the phase plan file, written by `phase-plan-creator` when the phase is created.

**Who writes it:** `phase-plan-creator` — the agent or command that scaffolds the phase plan. It records the SHA of the HEAD commit at plan-creation time. This SHA becomes the phase's start boundary.

**When it is written:** At phase plan creation, before any loops execute.

**How the compactor reads it:** The compactor receives the phase plan file path as an input. It reads `anchor_sha` from the plan's frontmatter. If the field is absent, the compactor falls back to the inference path (see below).

**Fallback (inference):** If `anchor_sha` is missing from the phase plan frontmatter, the compactor cross-references `history.jsonl` for the earliest event with a matching phase identifier, extracts its timestamp, and runs `git log --before=<timestamp> -1 --format=%h` to infer the SHA. Inference is the safety net, not the primary path — it will be less precise if events were logged with clock skew.

**Alternative considered and rejected — git tags:** Writing a git tag at phase start (e.g. `phase-5-start`) was considered. Tags are highly durable across rebases and branch operations. The approach was rejected for two reasons: (1) tag proliferation across a 20+ phase programme produces noise in `git tag` output with no cleanup path defined by the framework, and (2) the framework's existing convention is to carry metadata in plan frontmatter — `anchor_sha` follows that pattern at zero additional tool surface. Frontmatter is co-located with the plan and readable without git commands.

---

## Worked Example Skeleton

```markdown
---
phase: 5
title: "Documentation and Architecture Decisions"
status: passed
gate_verdict_ref: plans/gate-verdicts/phase-5-attempt-1-phase-goals-agent.json
anchor_sha: a1b2c3d
end_sha: e4f5a6b
commit_count: 14
loop_count: 6
created: 2026-05-13T09:00:00Z
---

# Alternative: pre-gate-review phase (gate_verdict_ref as sentinel)
---
phase: 4
title: "Some Earlier Phase"
status: passed
gate_verdict_ref: "n/a — pre-gate-review phase"
gate_verdict_note: "Phase completed before gate review system was introduced"
anchor_sha: a1b2c3d
end_sha: e4f5a6b
commit_count: 8
loop_count: 4
created: 2026-05-01T09:00:00Z
---

## Goals met
- Documented architecture decisions in docs/decisions.md — commits a1b2c3d..c3d4e5f
- Published getting-started guide at docs/getting-started.md — e199cca
- Gate review passed on first attempt with confidence 91 — plans/gate-verdicts/phase-5-attempt-1-phase-goals-agent.json

## Deferred
- Model-tier benchmarking → phase-7 (out of scope for documentation phase)

## Opened
- docs/release-checklist.md needs a Windows-specific section — surfaced during loop 018 review
```
