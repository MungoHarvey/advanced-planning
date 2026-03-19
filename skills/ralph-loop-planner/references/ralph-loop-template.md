# Ralph Loop Template & Best Practices

## Understanding Ralph Loops

A ralph loop iteration is a self-contained, verifiable unit of work with:
- Explicit todos with `outcome` fields (what "done" actually means per task)
- A concise handoff summary written at completion (done / failed / next)
- Git checkpoints at start and end
- Native TodoWrite sync for real-time sidebar visibility in Claude Code

---

## Schema: Two Layers

### Layer 1 — Frontmatter (Authoritative)
Extended schema stored in the plan file. Contains `skill`, `agent`, `outcome` fields.

### Layer 2 — Native TodoWrite (Session Tracking)
Claude Code's built-in tool. Subset of Layer 1 — omits `skill/agent/outcome`, adds `priority`.
Written at loop start, updated in-place throughout execution.

**Sync rule:** At loop start, call `TodoWrite` with the loop's todos mapped to native format.
Update `status` in both the frontmatter file and via `TodoWrite` as tasks complete.

---

## Full Template

```yaml
---
name: "ralph-loop-NNN"
task_name: "[Human-Readable Task Name]"
max_iterations: 3
on_max_iterations: escalate          # escalate | checkpoint | rollback

# Concise handoff written at loop COMPLETION (not before).
# Next loop injects this as its first context block.
handoff:
  done: ""                           # What was completed
  failed: ""                         # What did not complete and why (NA if none)
  next: ""                           # Exact action needed to reach the outcome

# Authoritative todo list. Each todo has an explicit outcome (done criteria).
# status: pending | in_progress | completed | cancelled
todos:
  - id: loop-NNN-1
    content: "[Atomic task description]"
    skill: "[skill-name or NA]"
    agent: "[subagent-id or NA]"
    outcome: "[What must exist or pass before this todo is complete]"
    status: pending
  - id: loop-NNN-2
    content: "[Atomic task description]"
    skill: "[skill-name or NA]"
    agent: "[subagent-id or NA]"
    outcome: "[What must exist or pass before this todo is complete]"
    status: pending

prompt: |
  # Ralph Loop NNN: [Task Name]

  ## Context from previous loop
  <!-- Paste handoff block from loop NNN-1 here at execution time -->
  done: [what was completed]
  failed: [what failed, or NA]
  next: [what this loop picks up from]

  ## Objective
  [What this loop accomplishes — 1 sentence]

  ## Todos
  [Listed from frontmatter above — agent reads and works through these in order]

  ## Success criteria
  - [ ] [Criterion 1]
  - [ ] [Criterion 2]

  ## Required skills
  - `[skill-1]`: [purpose]

  ## Inputs
  - [Input]: [source, format]

  ## Expected outputs
  - [Output]: [format, location]

  ## Constraints
  - [Constraint 1]

  ## Execution instructions
  1. Read this loop's todos from frontmatter
  2. Call TodoWrite to sync todos to session sidebar (map to native format)
  3. Git checkpoint: `git add -A && git commit -m "checkpoint: before ralph-loop-NNN"`
  4. Work through todos in order; mark each in_progress before starting, completed when done
  5. Verify each todo's outcome before marking completed — do not mark done on effort alone
  6. On completion: write handoff block to frontmatter (done / failed / next)
  7. Git checkpoint: `git add -A && git commit -m "complete: ralph-loop-NNN — [one-line summary]"`
  8. Stop and report results against success criteria
---

## Overview
[1–2 sentences: What this loop accomplishes and why it exists in sequence]

## Success Criteria
- ✓ [Criterion 1]: [How verified]
- ✓ [Criterion 2]: [How verified]

## Skills Required

### Broad (from phase plan):
- `[skill-domain]`: [Purpose]

### Specific (refined for this loop):
- `[specific-skill-1]`: [What you're doing with it]

### Discovered (new, identified during planning):
- `[new-skill]`: [Why needed here]

## Inputs
- `[Input Name]`: [Source, format, size]

## Outputs
- `[Output Name]`: [Format, location, downstream use]

## Dependencies
### Previous Loops:
- ralph-loop-[NNN-1]: [Why blocking]

### External:
- `[External dependency]`: [Status, workaround]

### Can Run in Parallel:
- ralph-loop-[XXX]: [Why safe to parallelise]

## Complexity
- **Scope:** Low / Medium / High
- **Estimated effort:** [e.g., "1–2 days"]
- **Key challenges:**
  1. [Challenge 1]
  2. [Challenge 2]

## Rationale & Design Notes
[Why this structure; alternatives considered; known gotchas]
```

---

## Native TodoWrite Sync

When the loop starts, call `TodoWrite` with this mapping:

```json
[
  {
    "id": "loop-NNN-1",
    "content": "[content from frontmatter] → outcome: [outcome from frontmatter]",
    "status": "pending",
    "priority": "high"
  }
]
```

Include the `outcome` inline in the `content` field so it remains visible in the sidebar.
Update status via `TodoWrite` each time a todo changes — do not batch updates.

---

## Handoff: Concise Three-Field Format

The handoff is written **at loop completion**, not upfront. It must be brief — one line per field:

```yaml
handoff:
  done: "Normalised count matrix written to data/normalised.rds; batch correction applied"
  failed: "UMAP failed on 3 outlier samples (IDs in data/failed_samples.txt)"
  next: "Re-run UMAP with n_neighbors=30 on remaining samples; skip failed IDs"
```

**Rules:**
- `done` — completed work that persists (files written, tests passing, decisions made)
- `failed` — what didn't complete and why; reference exact file/location if relevant; `NA` if none
- `next` — the precise action the next loop should start with; not a restatement of the phase goal

The next loop **injects this handoff block** at the top of its execution prompt before the objective.
This keeps incoming context clean while preserving continuity — no need to drag forward the full prior session.

---

## Git Checkpointing

Every loop bookends with two commits:

```bash
# Before starting work
git add -A && git commit -m "checkpoint: before ralph-loop-NNN"

# After completing work
git add -A && git commit -m "complete: ralph-loop-NNN — [one-line summary of what changed]"
```

This gives rollback points if a loop corrupts state, and a clean audit trail of what each loop produced.

---

## Error Recovery

Defined by `on_max_iterations` in frontmatter:

| Value | Behaviour |
|---|---|
| `escalate` | Stop, write partial handoff (`failed` field), surface to human |
| `checkpoint` | Commit current state, write handoff, pause — resumable later |
| `rollback` | `git reset` to the pre-loop checkpoint commit, restore previous state |

Default is `escalate`. Use `checkpoint` for long research loops where partial progress has value.

---

## Success Criteria Quality Standards

### ❌ Vague
- "Tests pass" / "Code is clean" / "Results look right"

### ✅ Specific & Verifiable
- "All [test suite] passes; linter clean with 0 warnings"
- "[Metric] matches reference within [tolerance]%; documented in [file]"
- "[Output file] exists at [path], non-empty, schema validated"

---

## Full Example

```yaml
---
name: "ralph-loop-001"
task_name: "DESeq2 normalisation and QC"
max_iterations: 3
on_max_iterations: checkpoint

handoff:
  done: ""
  failed: ""
  next: ""

todos:
  - id: loop-001-1
    content: "Run multiBatchNorm on raw count matrix"
    skill: deseq2-normalisation
    agent: NA
    outcome: "data/normalised.rds exists; dim() matches input; no NA values"
    status: pending
  - id: loop-001-2
    content: "Generate PCA plot pre/post normalisation"
    skill: visualization-generation
    agent: NA
    outcome: "figures/pca_normalisation.png exists; batch clusters visibly reduced"
    status: pending
  - id: loop-001-3
    content: "Write QC report"
    skill: NA
    agent: NA
    outcome: "reports/qc_normalisation.md exists; contains sample counts, NA summary, PCA interpretation"
    status: pending

prompt: |
  # Ralph Loop 001: DESeq2 Normalisation and QC

  ## Context from previous loop
  done: Phase plan complete; raw counts at data/raw_counts.rds; sample metadata at data/metadata.csv
  failed: NA
  next: Run normalisation pipeline from scratch

  ## Objective
  Normalise raw DRUGseq count matrix across batches and produce QC report confirming correction.

  ## Todos
  Work through todos in frontmatter in order: loop-001-1, loop-001-2, loop-001-3.
  Mark each in_progress before starting. Verify outcome before marking completed.

  ## Success criteria
  - [ ] data/normalised.rds exists, no NA values, dims match input
  - [ ] figures/pca_normalisation.png shows visible batch reduction
  - [ ] reports/qc_normalisation.md complete with counts, NA summary, PCA notes

  ## Required skills
  - `deseq2-normalisation`: multiBatchNorm across batches
  - `visualization-generation`: PCA plots

  ## Inputs
  - Raw counts: data/raw_counts.rds
  - Metadata: data/metadata.csv

  ## Expected outputs
  - Normalised matrix: data/normalised.rds
  - PCA figure: figures/pca_normalisation.png
  - QC report: reports/qc_normalisation.md

  ## Constraints
  - Use multiBatchNorm, not simple TMM, to preserve batch structure for downstream Harmony

  ## Execution instructions
  1. Read todos from frontmatter
  2. Call TodoWrite to sync to session sidebar
  3. git add -A && git commit -m "checkpoint: before ralph-loop-001"
  4. Work through todos; verify outcome before marking completed
  5. Write handoff block to frontmatter
  6. git add -A && git commit -m "complete: ralph-loop-001 — normalisation and QC done"
  7. Report against success criteria
---

## Overview
Establishes normalised count matrix as the foundation for all downstream DESeq2 analysis.
Must complete before loop-002 (differential expression) can begin.

## Success Criteria
- ✓ data/normalised.rds: exists, no NA values, correct dimensions
- ✓ figures/pca_normalisation.png: batch separation visibly reduced
- ✓ reports/qc_normalisation.md: sample counts, NA summary, PCA interpretation

## Skills Required
### Broad: `bioinformatics-analysis`
### Specific:
- `deseq2-normalisation`: multiBatchNorm
- `visualization-generation`: ggplot2 PCA

## Dependencies
- None (loop 1)

## Complexity
- **Scope:** Medium
- **Effort:** 4–6 hours
- **Challenges:**
  1. Batch metadata must align exactly with count matrix column names
  2. multiBatchNorm requires minimum sample counts per batch
```

---

## Execution Workflow

```
1. Generate ralph loops (@ralph-loop-planner)
2. Review structure, dependencies, skills
3. For each loop:
   a. Read todos from frontmatter
   b. Call TodoWrite to sync to sidebar
   c. Git checkpoint (before)
   d. Execute, marking todos in_progress → completed with outcome verified
   e. Write handoff (done / failed / next)
   f. Git checkpoint (complete)
   g. Review against success criteria
   h. If failed: up to max_iterations — then on_max_iterations behaviour
4. Inject handoff into next loop's prompt context block
5. After all loops: review phase outcomes; log learnings to CLAUDE.md
```
