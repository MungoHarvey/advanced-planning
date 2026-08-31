---
description: Reconcile the PLANS-INDEX.md Phases table row and loop-status rows for a phase against the phase plan and loops file. Reports every drift corrected. Run after editing a phase plan or loops file to keep the index in sync.
allowed-tools: Read, Write, Edit, Glob, Bash
argument-hint: "<phase-id>"
---

# /sync-plans

Re-render the PLANS-INDEX.md entries for a given phase from the authoritative source
(`.advanced-plans/phases/phase-N/plan.md` frontmatter and
`.advanced-plans/phases/phase-N/loops.md`) so the index stays in sync without
manual editing. The command **only propagates from plan → index** — it does not
invent content. Every change it makes is a drift correction that is reported.

## Steps

### 1. Parse `<phase-id>` argument

Read `$ARGUMENTS`. Accept either a bare integer (`15`) or the prefixed form
(`phase-15`). Strip the `phase-` prefix if present and set `N` to the resulting
integer.

If `$ARGUMENTS` is empty or does not resolve to a positive integer:

```
Error: /sync-plans requires a phase-id argument.
Usage: /sync-plans <phase-id>   (e.g. /sync-plans 15  or  /sync-plans phase-15)
```

Stop.

Print: `-> Syncing phase [N]`

### 2. Locate and read the phase plan

Locate the phase plan:

```
.advanced-plans/phases/phase-[N]/plan.md
```

If the file does not exist:

```
Error: Phase plan not found. Expected .advanced-plans/phases/phase-[N]/plan.md.
Cannot sync a phase with no plan on disk.
```

Stop.

Read the YAML frontmatter of the plan. Extract:

- `name:` — the phase title (e.g. `"Automation-Surface Audit"`)
- `status:` — the phase status (e.g. `draft`, `complete`)
- `loops:` — the loop-number list (e.g. `[059, 060, 061, 062, 063]`)

Compute the loop range string from the `loops:` list:

- If the list has exactly one element, the range is that element zero-padded to 3 digits.
- If the list has 2+ elements, the range is `[first]..[last]` (e.g. `059–063`).
- If `loops:` is absent or empty, set range to `—`.

### 3. Locate and read the loops file

Locate the loops file:

```
.advanced-plans/phases/phase-[N]/loops.md
```

If the file does not exist, proceed without it (loop rows cannot be synced; note
this in the drift report).

If the file exists, extract each loop block's frontmatter:

- `name:` — the loop identifier (e.g. `ralph-loop-059`)
- `task_name:` — the loop title (e.g. `Doc-Hygiene + Wire State-Archiving`)
- `handoff_summary.done` — non-empty string means the loop has completed
- todo counts: count `status: completed` and `status: pending` todos

Derive the loop status for each loop:

- All todos `completed` OR `handoff_summary.done` non-empty → `**complete**`
- Any todo `in_progress` → `**in_progress**`
- Otherwise → `**pending**`

### 4. Read PLANS-INDEX.md

Read `.advanced-plans/PLANS-INDEX.md` in full.

If the file does not exist:

```
Error: .advanced-plans/PLANS-INDEX.md not found. Cannot sync index.
```

Stop.

### 5. Reconcile the Phases table row

Locate the Phases table in PLANS-INDEX.md. The table header is:

```
| Phase | Name | File | Status | Loops | Outcome |
```

Find the row for phase N. It matches the pattern `| [N] |` at the start of a
table row.

**If no row is found for phase N:** append a new row at the end of the Phases
table in ascending phase-number order. Construct the row:

```
| [N] | [name] | [`phase-[N]/plan.md`](phases/phase-[N]/plan.md) | **[status]** | [loop-range] | [name] |
```

Set `Outcome` to the phase name (a placeholder — the operator should enrich it
after the phase completes). Record as a drift correction: `Phases table — row
for phase [N] was missing; added`.

**If a row exists for phase N:** compare its fields against the plan frontmatter:

| Field | Source of truth | PLANS-INDEX column |
|-------|-----------------|--------------------|
| Name | `plan.md` `name:` | Name column |
| Status | `plan.md` `status:` (formatted as `**[status]**`) | Status column |
| Loop range | Derived from `plan.md` `loops:` | Loops column |

For each field that differs, record the drift and update the index cell. The
`File` and `Outcome` columns are not overwritten — they may contain enriched
content the operator added. If Name is the same as the current Name column,
leave it unchanged.

Print for each corrected field:

```
  Phases row [N]: [field] "[old]" → "[new]"
```

If no fields differ, print:

```
  Phases row [N]: no drift
```

### 6. Reconcile the Ralph Loops table rows

Locate the Ralph Loops table in PLANS-INDEX.md. The table header is:

```
| Loop | Phase | Name | File | Status | Active File | Attempt |
```

For each loop in the loops file:

Extract the loop number from the `name:` field (e.g. `ralph-loop-059` → `059`).

Find the matching row in the Ralph Loops table (`| 059 |`). Compare:

| Field | Source of truth | PLANS-INDEX column |
|-------|-----------------|--------------------|
| Name | `task_name:` from loops.md | Name column |
| Status | Derived in Step 3 | Status column |

For each field that differs, record the drift and update the row cell. The
`File`, `Active File`, and `Attempt` columns are not overwritten.

**If no row is found for a loop in the loops file:** append a new row for that
loop at the end of the Ralph Loops table in ascending loop-number order:

```
| [NNN] | [N] | [task_name] | `phases/phase-[N]/loops.md` | [status] | — | 1 |
```

Record as a drift correction.

Print for each loop that had drift:

```
  Loop [NNN]: [field] "[old]" → "[new]"
```

For loops with no drift, print a summary count at the end (not per-loop).

### 7. Write the updated PLANS-INDEX.md

If any drift was detected in Steps 5 or 6, write the corrected PLANS-INDEX.md
using the Edit tool to apply each cell replacement in-place.

Print:

```
  PLANS-INDEX.md updated ([N] drift corrections applied)
```

If no drift was detected:

```
  PLANS-INDEX.md already in sync — no changes made
```

### 8. Print drift report

```
/sync-plans phase [N] complete
-------------------------------
Phase plan:   .advanced-plans/phases/phase-[N]/plan.md
Loops file:   .advanced-plans/phases/phase-[N]/loops.md
Index:        .advanced-plans/PLANS-INDEX.md

Drift corrections:
  [list each corrected field, or "(none)" if none]

No content was invented. All corrections propagated from plan → index.
```

## Usage

```
/sync-plans 15
/sync-plans phase-15
```

Run after editing a phase plan, changing a loop's task_name, or marking a phase
complete — any time the plan frontmatter or loops file changes and the index may
have drifted.

Also useful as a post-gate-pass hygiene step before running `/phase-compact`.

## Error Modes

| Condition | Behaviour |
|-----------|-----------|
| Missing `<phase-id>` argument | Print usage error and stop immediately |
| Phase plan not found | Print error with expected path and stop |
| PLANS-INDEX.md not found | Print error and stop |
| Loops file not found | Note in report; sync Phases table only; continue |
| Loop in PLANS-INDEX has no matching entry in loops.md | Skip — do not delete existing rows |
| `loops:` field absent from plan frontmatter | Set loop range to `—`; note in report |

## Notes

**Scope is narrow by design.** `/sync-plans` reconciles only: (a) the Phases
table row for the given phase, and (b) the Ralph Loops table rows for that
phase's loops. It does not rewrite phase plan content, loop body text, gate
verdicts, handoff digests, or any artefact outside PLANS-INDEX.md.

**The Outcome column is not overwritten.** Outcome cells may contain curator-
enriched summaries written at gate pass. `/sync-plans` leaves them intact and
only updates Name, Status, and Loops-range columns.

**Idempotent.** Running `/sync-plans [N]` twice produces the same result. If
the index already matches the plan, the second run reports zero drift and makes
no writes.

**Does not commit.** Changes are left in the working tree for the operator to
review and commit.
