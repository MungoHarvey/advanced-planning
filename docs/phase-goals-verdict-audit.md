# Phase Goals Verdict Audit

**Purpose:** Audit the verdict file format written by `phase-goals-agent` and determine whether it is sufficient for `phase-compactor` to consume, or whether a minimal extension is required.

**Agent definition source:** `platforms/claude-code/agents/phase-goals-agent.md`
**Schema source:** `core/state/gate-verdict.schema.json`
**Design doc:** `~/.gstack/projects/MungoHarvey-advanced-planning/mharvey2-main-design-20260513-103520.md`
**Verdict write path:** `plans/gate-verdicts/[phase]-attempt-[N]-phase-goals-agent.json`

---

## Current Format

The agent's write-path instruction (verbatim from `platforms/claude-code/agents/phase-goals-agent.md`):

> Write the verdict to:
> `plans/gate-verdicts/[phase]-attempt-[N]-phase-goals-agent.json`
> Example: `plans/gate-verdicts/phase-2-attempt-1-phase-goals-agent.json`
> The file must conform to `core/state/gate-verdict.schema.json`.
> Set `"agent": "phase-goals-agent"` in the verdict.
> The file is immutable once written. Each attempt produces a new file with an incremented attempt number.

The JSON schema (`core/state/gate-verdict.schema.json`) defines the following required fields:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `phase` | string | required | Phase identifier, e.g. `"phase-2"` |
| `attempt` | integer | required, min 1 | Attempt number; increments on retry |
| `timestamp` | string (date-time) | required | ISO 8601 timestamp of verdict write |
| `agent` | string | required | Agent identifier, e.g. `"phase-goals-agent"` |
| `verdict` | string | required, enum: `"pass"` \| `"fail"` | Gate outcome |
| `confidence` | integer | required, 0–100 | Overall confidence score |
| `findings` | array | required | List of issues; empty array on pass |
| `loops_to_revert` | array | required | Loop IDs to re-execute on retry; empty on pass |
| `failure_notes` | array | required | Actionable constraints for retry; empty on pass |

Each item in `findings` is an object with four required fields:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `severity` | string | enum: `"critical"` \| `"warning"` \| `"info"` | `critical` blocks pass |
| `location` | string | required | File path, function, or loop identifier |
| `description` | string | required | Human-readable issue description |
| `evidence` | string | required | Concrete evidence (file path, line, value observed) |

`additionalProperties: false` is enforced at the top level and within findings items — the schema rejects any field not listed above.

---

## Concrete Example

No verdict files exist under `plans/gate-verdicts/` at the time of this audit. The directory does not yet exist in the repository — the framework has not yet run a gate review for any phase in the current programme.

The current format is therefore drawn entirely from `core/state/gate-verdict.schema.json` and the agent definition. The worked example below is a synthetic illustration of what a passing verdict would look like, strictly conforming to the schema:

```json
{
  "phase": "phase-5",
  "attempt": 1,
  "timestamp": "2026-05-13T10:00:00Z",
  "agent": "phase-goals-agent",
  "verdict": "pass",
  "confidence": 92,
  "findings": [],
  "loops_to_revert": [],
  "failure_notes": []
}
```

**Field-by-field annotation:**

- `phase`: Matches the phase plan filename stem (`phase-5`), not a display name.
- `attempt`: `1` for a first-run pass. Increments to `2` if a retry is needed and passes.
- `timestamp`: Written at the moment the verdict file is created — not the gate review start time.
- `agent`: Hardcoded to `"phase-goals-agent"` by the agent definition. Other gate agents (e.g. `code-review-agent`) write their own verdict files with their own identifier.
- `verdict`: `"pass"` — all success criteria met, all expected outputs present.
- `confidence`: The agent's aggregate confidence across all criterion checks. Below-80 findings are demoted to `severity: "info"` and do not affect verdict.
- `findings`: Empty on a clean pass. On fail, each entry names the criterion that failed, the file path expected, and the evidence of absence or mismatch.
- `loops_to_revert`: Empty on pass. On fail, lists loop IDs whose outputs are invalid and must be re-executed.
- `failure_notes`: Empty on pass. On fail, actionable constraints injected into the retry loop file as `do_not_repeat`.

---

## Gap Analysis

The design doc (Recommended Approach, Agent contract / Inputs section) specifies that the `phase-compactor` requires four inputs:

1. The phase plan file (path passed by main thread — not from the verdict file)
2. The gate-verdict JSON written by `phase-goals-agent` for this phase
3. The slice of `history.jsonl` covering this phase's events (not from the verdict file)
4. The phase-start anchor SHA (mechanism per design doc §Open Questions — not from the verdict file)

Of these, only input 2 is sourced from the verdict file. The compactor does not need the verdict file to carry inputs 1, 3, or 4 — those are passed by the main thread separately.

The table below maps every field the compactor needs from the verdict file against what the current schema provides:

| Field needed by compactor | Present in current schema | Notes |
|--------------------------|--------------------------|-------|
| Phase identifier (`phase`) | Yes — `phase` field | Used to match verdict to phase plan |
| Attempt number (`attempt`) | Yes — `attempt` field | Needed to name cold artefact correctly (`phase-N-complete.md` vs `phase-N-complete-v1-failed.md`) |
| Gate outcome (`verdict`) | Yes — `verdict` field | `"pass"` triggers cold artefact; `"fail"` triggers failed variant |
| Timestamp of gate completion | Yes — `timestamp` field | Used as `created` field in cold artefact |
| Agent that produced verdict | Yes — `agent` field | Used as `gate_verdict_ref` in cold artefact frontmatter |
| Goals that passed (structured) | **No** | `findings` records failures only; passing criteria are implicit (absence of critical finding) |
| Deferred goals (structured) | **No** | Not recorded in verdict at all |
| Failure reasons for cold artefact | Partial — `failure_notes` | `failure_notes` is a flat string array; not keyed by criterion |
| Loops reviewed | Partial — `loops_to_revert` | Only loops flagged for revert; silent on loops that passed cleanly |

**Gap summary:** Two structural gaps exist.

**Gap 1 — Passed criteria not enumerated.** The compactor's cold artefact (`phase-N-complete.md`) requires a `## Goals met` section listing each satisfied success criterion with a commit-range or file reference. The current verdict schema has no field for this — it records only failures. The compactor would need to re-read the phase plan and re-derive which criteria passed, undermining Premise 4 of the design doc ("The phase-compactor consumes `phase-goals-agent`'s gate-verdict file as input rather than re-judging goal completion").

**Gap 2 — Deferred goals not captured.** The cold artefact's `## Deferred` section requires goals explicitly punted to a later phase. The verdict schema has no field for deferrals — `failure_notes` records retry constraints, not strategic deferrals. A deferred goal is distinct from a failed criterion: it is a conscious decision to exclude scope, not an oversight.

---

## Extension Spec

Two new optional fields are required on the verdict schema. Both are `additionalProperties: false`, so they must be added to the schema explicitly.

### Field 1: `criteria_outcomes`

| Attribute | Value |
|-----------|-------|
| **Name** | `criteria_outcomes` |
| **Type** | array of objects |
| **Required** | No (optional; defaults to `[]` for backward compatibility) |
| **Location in schema** | Top-level, alongside `findings` |

Each item:

| Sub-field | Type | Required | Description |
|-----------|------|----------|-------------|
| `criterion` | string | yes | Verbatim text of the success criterion from the phase plan |
| `status` | string (enum) | yes | `"met"` \| `"deferred"` \| `"failed"` |
| `evidence` | string | yes | File path, commit SHA, or Glob result confirming status |
| `deferred_to` | string | no | Target phase identifier if `status: "deferred"` (e.g. `"phase-7"`) |

**Semantics:** The compactor reads `criteria_outcomes` to populate `## Goals met` (items where `status: "met"`) and `## Deferred` (items where `status: "deferred"`). Items with `status: "failed"` are already covered by `findings`. This eliminates the need for the compactor to re-read or re-evaluate the phase plan.

**Default:** `[]` — existing verdict files written before this extension remain valid. The compactor falls back to the re-read path if `criteria_outcomes` is absent or empty, with a logged warning.

**Worked example (pass case):**

```json
"criteria_outcomes": [
  {
    "criterion": "docs/phase-goals-verdict-audit.md exists with all four sections",
    "status": "met",
    "evidence": "plans/phase-6-ralph-loops.md handoff_summary.done confirms artefact produced"
  },
  {
    "criterion": "Gap Analysis table covers every compactor input",
    "status": "met",
    "evidence": "docs/phase-goals-verdict-audit.md line 67–89"
  }
]
```

### Field 2: `phase_title`

| Attribute | Value |
|-----------|-------|
| **Name** | `phase_title` |
| **Type** | string |
| **Required** | No (optional) |
| **Location in schema** | Top-level |

**Semantics:** The display title of the phase (e.g. `"Compaction Schema Audit & Lock"`), sourced from the phase plan's `title` field. The compactor needs this for the cold artefact's `title` frontmatter field and the hot manifest entry's `title` field. Without it, the compactor must read the phase plan to extract the title — a minor redundancy but an unnecessary coupling.

**Default:** Absent — compactor reads the phase plan for the title if not present. This field is a convenience extension, not required for correctness.

**Worked example:**

```json
"phase_title": "Compaction Schema Audit & Lock"
```

### Schema change summary

Two fields added to `core/state/gate-verdict.schema.json` under `properties`, both optional:

```json
"criteria_outcomes": {
  "type": "array",
  "description": "Outcome of each success criterion. Used by phase-compactor to populate goals_met and deferred sections without re-reading the phase plan.",
  "items": {
    "type": "object",
    "required": ["criterion", "status", "evidence"],
    "properties": {
      "criterion": { "type": "string" },
      "status": { "type": "string", "enum": ["met", "deferred", "failed"] },
      "evidence": { "type": "string" },
      "deferred_to": { "type": "string" }
    },
    "additionalProperties": false
  }
},
"phase_title": {
  "type": "string",
  "description": "Display title of the phase from the phase plan. Convenience field for the compactor."
}
```

`additionalProperties: false` at the top level must be updated to permit these two new fields.

The `phase-goals-agent` definition (`platforms/claude-code/agents/phase-goals-agent.md`) must be extended with instructions to populate `criteria_outcomes` during Step 3 (Verify each success criterion) and to write `phase_title` from the phase plan's title field. **This extension is out of scope for Phase 6 — it is Phase 7 implementation work.**

Phase 6's deliverable is this audit and spec. Phase 7 implements the extension on the agent and schema.
