# Human Gate Review

## Purpose

This document defines the manual human review gate that blocks phase progression until explicit approval is received.

## Gate Instruction

After a phase plan is produced at `.advanced-plans/phases/phase-N/plan.md`, print exactly:

```text
REVIEW .advanced-plans/phases/phase-N/plan.md

Reply with exactly one:
APPROVE phase-N
REVISE phase-N: <instructions>
STOP phase-N
```

## Response Semantics

| Response | Action |
|----------|--------|
| `APPROVE phase-N` | Continue to loop decomposition, todo population, skill assignment, and agent assignment. |
| `REVISE phase-N: <instructions>` | Rerun phase planning with the supplied instructions. Present the revised plan for review. |
| `STOP phase-N` | Preserve the plan and exit. No further action. |

## Blocking Rules

Until one of the three responses is received:

1. **Loop decomposition must not begin.**
2. **No approval event may be recorded.**
3. **`resume` must return to the outstanding review.**
4. **Auto mode must remain stopped.**

## Rationale

Manual review is the baseline, not an optional fallback. No absent hook may silently approve or skip the gate. This ensures human oversight of phase boundaries and prevents uncontrolled scope expansion.
