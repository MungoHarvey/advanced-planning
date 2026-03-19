# Todo Schema Reference

## Canonical Frontmatter Schema (Authoritative)

The extended schema lives in ralph loop frontmatter. Field order is enforced — agents must
maintain this order when editing to prevent schema drift and ensure reliable parsing.

```yaml
todos:
  - id: loop-NNN-N          # Format: loop-{loop-number}-{todo-number}
    content: ""             # Atomic task description (one clear action)
    skill: ""               # Skill name from .claude/skills/ — or NA
    agent: ""               # Subagent id from .claude/agents/ — or NA
    outcome: ""             # Concrete done criteria: what must exist or pass
    status: pending         # pending | in_progress | completed | cancelled
```

### Field Rules

| Field | Required | Values | Notes |
|---|---|---|---|
| `id` | Yes | `loop-NNN-N` | Unique; matches native TodoWrite id |
| `content` | Yes | String | One atomic action per todo |
| `skill` | Yes | skill-name or `NA` | From `.claude/skills/` directory |
| `agent` | Yes | agent-id or `NA` | From `.claude/agents/` directory |
| `outcome` | Yes | String | Specific, verifiable — not "done", not "looks right" |
| `status` | Yes | See below | Updated in-place during execution |

### Status Values

| Status | Meaning |
|---|---|
| `pending` | Not yet started |
| `in_progress` | Currently being worked on (max one at a time) |
| `completed` | Done — outcome verified, not just attempted |
| `cancelled` | Explicitly skipped with reason in notes |

**Rule:** Only one todo should be `in_progress` at a time.
Mark `in_progress` **before** starting work. Mark `completed` only after verifying the outcome.

---

## Native TodoWrite Schema (Session Tracking)

Claude Code's built-in tool. Used for real-time sidebar visibility during execution.
This is a **subset** of the frontmatter schema — `skill`, `agent`, `outcome` are not native fields.

```json
{
  "id": "loop-NNN-N",
  "content": "[task description] → [outcome]",
  "status": "pending",
  "priority": "high"
}
```

Embed the `outcome` inline in `content` (after `→`) so it remains visible in the sidebar UI.

### Sync Protocol

1. **Loop start:** Call `TodoWrite` with all loop todos mapped to native format
2. **During execution:** Update `status` via `TodoWrite` as each todo changes
3. **Do not batch:** Update immediately when status changes — not at end of loop
4. **Canonical source:** Frontmatter YAML — if there is any conflict, frontmatter wins

### Priority Mapping

All loop todos default to `high`. Use `medium` only for optional/nice-to-have todos
that are explicitly not blocking the loop's success criteria.

---

## Outcome Writing Standards

The `outcome` field answers: *"What must be true in the world for this todo to be done?"*

### ❌ Invalid Outcomes
```yaml
outcome: "Task complete"
outcome: "Code written"
outcome: "Looks good"
outcome: "Done"
```

### ✅ Valid Outcomes
```yaml
# File existence
outcome: "data/normalised.rds exists at correct path, dim() matches input, no NA values"

# Test passing
outcome: "All unit tests pass; coverage >85%; linter clean with 0 warnings"

# Content requirement
outcome: "reports/qc.md exists; contains sample counts, NA summary, PCA interpretation"

# Numeric threshold
outcome: "UMAP converges; silhouette score >0.6 on validation set"

# Validation confirmation
outcome: "Schema validation passes on output JSON; 0 records rejected"
```

---

## In-Place Editing Rules

When agents update todos in the plan file:

1. **Maintain field order:** `id → content → skill → agent → outcome → status`
2. **Only update `status` and `skill`/`agent` fields** — never rewrite `id`, `content`, or `outcome`
3. **One todo in_progress at a time** — set previous to `completed` before starting next
4. **Verify outcome before completing** — read the output, run the check, confirm the file exists

---

## Example: Complete Loop Todos

```yaml
todos:
  - id: loop-002-1
    content: "Run DESeq2 differential expression for TDP43 vs WT"
    skill: deseq2-analysis
    agent: NA
    outcome: "results/deseq2_tdp43_wt.rds exists; contains LFC and padj columns; 0 NA in padj"
    status: completed

  - id: loop-002-2
    content: "Filter significant hits at padj <0.05 and |LFC| >1"
    skill: NA
    agent: NA
    outcome: "results/sig_hits.csv exists; all rows have padj <0.05 and abs(LFC) >1"
    status: completed

  - id: loop-002-3
    content: "Generate volcano plot"
    skill: visualization-generation
    agent: NA
    outcome: "figures/volcano_tdp43_wt.png exists; significant hits highlighted; axis labels present"
    status: in_progress

  - id: loop-002-4
    content: "Write differential expression summary report"
    skill: NA
    agent: NA
    outcome: "reports/de_summary.md exists; contains hit counts, top 10 genes, volcano interpretation"
    status: pending
```
