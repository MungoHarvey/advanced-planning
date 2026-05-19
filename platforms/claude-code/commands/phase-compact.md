---
description: Compact a completed phase into a cold artefact and hot manifest entry. Run after gate review passes to produce .advanced-plans/phases/phase-N/complete.md and update .advanced-plans/PLANS-INDEX.md. Idempotent — safe to re-run.
allowed-tools: Read, Write, Glob, Bash, Edit
argument-hint: "<phase-id>"
---

# /phase-compact

Produce the phase compaction artefacts for a completed phase. This command runs on the main
thread immediately after a gate pass. It reads the phase plan, gate verdict, history, and git
log, then writes a cold artefact (`.advanced-plans/phases/phase-N/complete.md`) and updates the
hot manifest (`.advanced-plans/PLANS-INDEX.md`). Both outputs are validated against their locked schemas
before any file is written. The command is idempotent: if artefacts already exist for this
phase, it updates them in-place rather than duplicating.

## Steps

### 1. Parse `<phase-id>` argument

Read `$ARGUMENTS`. Accept either a bare integer (`6`) or the prefixed form (`phase-6`). Strip
the `phase-` prefix if present and set `N` to the resulting integer.

If `$ARGUMENTS` is empty or does not resolve to a positive integer:
```
Error: /phase-compact requires a phase-id argument.
Usage: /phase-compact <phase-id>   (e.g. /phase-compact 6  or  /phase-compact phase-6)
```
Stop.

Print: `-> Compacting phase [N]`

### 2. Locate phase plan

Locate the phase plan file:

```bash
ls .advanced-plans/phases/phase-[N]/plan.md 2>/dev/null
```

If no file is found:
```
Error: Phase plan not found. Expected .advanced-plans/phases/phase-[N]/plan.md.
Cannot compact a phase with no plan on disk.
```
Stop.

Set `PHASE_PLAN` to the resolved path. Read the file's YAML frontmatter.

### 3. Resolve `anchor_sha`

**Primary path:** read `anchor_sha:` from `PHASE_PLAN` frontmatter. If present and non-empty,
set `ANCHOR_SHA` to that value and continue to Step 4.

**Fallback path:** if `anchor_sha` is absent from frontmatter, infer from `history.jsonl`:

```bash
# Find earliest event for phase N
grep '"phase":"phase-[N]"' .advanced-plans/state/history.jsonl | head -1
```

Extract the `timestamp` field from the first matching event. Then:

```bash
git log --before="<timestamp>" -1 --format=%h
```

Set `ANCHOR_SHA` to the result.

If neither path resolves a SHA:
```
Error: Cannot determine anchor SHA for phase [N].
  Checked: .advanced-plans/phases/phase-[N]/plan.md frontmatter (anchor_sha field absent)
  Checked: .advanced-plans/state/history.jsonl (no events for phase [N] found)
Cannot write a conforming artefact without a verifiable anchor SHA.
```
Stop.

Verify the SHA resolves:

```bash
git rev-parse --short [ANCHOR_SHA]
```

Print: `  anchor_sha: [ANCHOR_SHA]`

### 4. Resolve `end_sha`

Scan the git log for the gate-pass commit or the last commit that belongs to phase N.

```bash
git log --oneline | grep -i "gate.*pass\|phase.*[N].*gate\|complete.*phase.*[N]" | head -5
```

If a gate-pass commit is identifiable, use its short SHA. Otherwise use the most recent commit
whose message references phase N, or fall back to the latest commit prior to or at the
gate-pass history event timestamp:

```bash
# Timestamp of gate_pass event for phase N
grep '"event":"gate_pass","phase":"phase-[N]"' .advanced-plans/state/history.jsonl | tail -1
# then:
git log --before="<gate_pass_timestamp>" -1 --format=%h
```

Set `END_SHA`.

Print: `  end_sha: [END_SHA]`

### 5. Read gate verdict file

Determine the latest attempt number for phase N:

```bash
ls .advanced-plans/gate-verdicts/phase-[N]-attempt-*-phase-goals-agent.json 2>/dev/null | sort | tail -1
```

If a file is found, set `VERDICT_PATH` to that path. Read the file and extract:
- `verdict` field (`pass` or `fail`)
- `criteria_outcomes` array (if present) — used in Step 8
- `phase_title` field (if present) — used as title fallback

If no verdict file is found, set `VERDICT_PATH` to the sentinel string
`"n/a — pre-gate-review phase"` and set `VERDICT_NOTE` to a one-sentence explanation
(e.g. `"Phase completed before gate review system was introduced"`).

**Gate-fail input:** if `verdict` is `"fail"`, do not write the standard pass-form artefact.
See the Error Modes section below.

Print: `  gate_verdict_ref: [VERDICT_PATH]`

### 6. Slice `history.jsonl` for phase N

```bash
grep '"phase":"phase-[N]"' .advanced-plans/state/history.jsonl
```

Collect all events. Note the count of `loop_complete` events — this is the `loop_count` for
the cold artefact. Note the `gate_pass` event (confirms the phase passed).

Print: `  loop_count: [count]`

### 7. Capture git commit range

```bash
git rev-list --count [ANCHOR_SHA]..[END_SHA]
```

Add 1 for the anchor itself to get `COMMIT_COUNT`.

Also capture the oneline log for reference:

```bash
git log [ANCHOR_SHA]..[END_SHA] --oneline
```

Print: `  commit_count: [COMMIT_COUNT]  ([ANCHOR_SHA]..[END_SHA])`

### 8. Compute body sections

Derive the three body sections (`Goals met`, `Deferred`, `Opened`) using this priority order:

**If the verdict file is present and contains `criteria_outcomes`:**
- `Goals met`: one bullet per entry where `status: pass`. Each bullet must end with a
  concrete evidence pointer (commit SHA, file path, or verdict path from `evidence` field).
- `Deferred`: one bullet per entry where `status: deferred`. Include `deferred_to` if set.
- `Opened`: one bullet per finding in the verdict's `findings` that is informational rather
  than blocking, plus any new questions surfaced during the phase.

**Fallback (no `criteria_outcomes`):** read the phase plan's `## Success Criteria` section.
For each criterion, check the completed loop handoff summaries (from the phase's `loops.md`
file's `handoff_summary.done` fields) to infer `pass` or `deferred`. Use judgment: if a
handoff explicitly states the criterion was met, mark it as met with a pointer to that loop's
commit range.

**Hard rules (from schema):**
- Each bullet is exactly one line — no wrapping, no sub-bullets.
- No prose paragraphs in any section.
- If nothing was deferred, write `- (none)`.
- If nothing was opened, write `- (none)`.

### 9. Write cold artefact

**Idempotency check:** before writing, test whether the artefact already exists:

```bash
ls .advanced-plans/phases/phase-[N]/complete.md 2>/dev/null
```

If the file exists, update it in-place (overwrite with the newly computed content). Do not
append — a second run must produce exactly one file, not two. Print:
`  (updating existing cold artefact in-place)`

If the file does not exist, the directory `.advanced-plans/phases/phase-[N]/` already exists.

Write `.advanced-plans/phases/phase-[N]/complete.md` with this exact structure:

```markdown
---
phase: [N]
title: "[title from phase plan frontmatter or phase_title from verdict]"
status: passed
gate_verdict_ref: [VERDICT_PATH or sentinel string]
gate_verdict_note: "[VERDICT_NOTE — only if sentinel used]"
anchor_sha: [ANCHOR_SHA]
end_sha: [END_SHA]
commit_count: [COMMIT_COUNT]
loop_count: [LOOP_COUNT]
created: [ISO 8601 timestamp]
---

## Goals met
[bullets from Step 8]

## Deferred
[bullets from Step 8, or - (none)]

## Opened
[bullets from Step 8, or - (none)]
```

Omit `gate_verdict_note` entirely when a real verdict path is present.

### 10. Write hot manifest entry

**Idempotency check:** read `.advanced-plans/PLANS-INDEX.md`. Search for an existing entry for phase N:

```bash
grep -n "^- phase: [N]$" .advanced-plans/PLANS-INDEX.md
```

If an entry is found, locate its block (from that line through the next `- phase:` or
end-of-file) and overwrite it in-place with the updated entry. Do not append a duplicate.
Print: `  (updating existing manifest entry in-place)`

If no entry exists, append the new entry at the end of the phase list, maintaining ascending
phase order. If `PLANS-INDEX.md` does not exist, create it.

The entry must be exactly this structure (<=8 lines — count every line including the opening
`- phase:` line):

```yaml
- phase: [N]
  title: "[title]"
  status: passed
  commits: [ANCHOR_SHA]..[END_SHA]
  detail: .advanced-plans/phases/phase-[N]/complete.md
  highlights:
    - [one-line highlight: primary goal met, with evidence]
    - [one-line highlight: key decision or deferral]
```

Maximum 2 highlights. If only one highlight is meaningful, use one. Count the lines: 8 is the
absolute ceiling.

### 11. Validate both artefacts

Run every item in the `docs/phase-complete.schema.md` Validation Checklist and every item in
`docs/phase-manifest-entry.schema.md` Validation Checklist. Check each item explicitly.

Key automated checks:

```bash
# Confirm anchor and end SHAs resolve
git rev-parse --short [ANCHOR_SHA]
git rev-parse --short [END_SHA]

# Confirm commit_count is within +-1 of rev-list output
git rev-list --count [ANCHOR_SHA]..[END_SHA]

# Confirm cold artefact exists at expected path
ls .advanced-plans/phases/phase-[N]/complete.md

# Confirm manifest entry is <=8 lines
awk '/^- phase: [N]$/,/^- phase: [0-9]/' .advanced-plans/PLANS-INDEX.md | head -20 | wc -l
```

If **any** checklist item fails, stop and print a diff of the failing item:

```
Error: Schema validation failed.
  Checklist item: [exact item text from schema doc]
  Expected: [expected value or condition]
  Found:    [actual value or condition]
Artefacts written but INVALID. Fix before advancing to next phase.
```

Do not silently write a non-conforming artefact.

### 12. Print summary

```
Phase [N] compacted.

  Cold artefact:  .advanced-plans/phases/phase-[N]/complete.md
  Manifest entry: .advanced-plans/PLANS-INDEX.md (phase [N] block)
  Anchor SHA:     [ANCHOR_SHA]
  End SHA:        [END_SHA]
  Commits:        [COMMIT_COUNT]
  Loops:          [LOOP_COUNT]
  Gate verdict:   [VERDICT_PATH]
  Validation:     all checklist items pass

Run /next-phase (or continue planning) to begin the next phase.
```

### 13. Write and validate `handoff.md`

**Order invariant:** this step runs after `complete.md` is written and schema-validated (Step 11).
The digest is a phase-level resume seed — it must exist and be valid before any compaction guidance
is offered.

Run the handoff digest generator:

```bash
python platforms/python/handoff_digest.py .advanced-plans/phases/phase-[N]
```

The script reads `plan.md`, `complete.md`, the gate verdict files, and the `history.jsonl` slice
for phase N, then writes `.advanced-plans/phases/phase-[N]/handoff.md` conforming to
`docs/phase-handoff.schema.md`.

**Ceiling enforcement:** if the generated digest exceeds `token_ceiling` (1500 tokens), the script
exits non-zero and prints the offending sections. Stop and tighten the digest manually before
continuing.

**Idempotency:** if `handoff.md` already exists, the script overwrites it in-place — a second run
produces exactly one file.

**Gate-fail path:** if the phase verdict is `fail`, the digest is written with
`status: failed_vM`. The `## Errors & issues encountered` section must be non-empty.

After the script exits 0, confirm:

```bash
ls .advanced-plans/phases/phase-[N]/handoff.md
```

Print:

```
  Handoff digest: .advanced-plans/phases/phase-[N]/handoff.md  (ceiling OK)
```

If the script exits non-zero:

```
Error: handoff.md generation failed.
  [script output]
Fix the offending sections before continuing.
```

Stop.

### 14. Transparency report

Run context occupancy measurement and present it in plain language:

```bash
python platforms/python/context_meter.py --report
```

If the meter cannot locate a session transcript, it prints `occupancy unavailable` and exits 0 —
this is a graceful degrade. Continue regardless.

Present the output to the user with the following framing:

```
Context occupancy report
------------------------
[paste context_meter --report output here]

What this means:
  - The bulk of context is raw tool I/O (file Reads + bash output) already on disk.
  - Injected skill/command/tool-schema bodies reload on demand — they do not need to
    survive compaction.
  - After compaction the resume seed becomes handoff.md (~1.5k tokens) + PLANNING.md
    frontmatter — on-task, no re-reading required.
```

If occupancy is unavailable, print:

```
Context occupancy report
------------------------
  occupancy: unavailable (no session transcript found)
  breakdown: unavailable
  projected saving: unavailable

Compaction guidance below is still valid; proceed.
```

### 15. Maintain `## Compaction Instructions` block in CLAUDE.md

Rewrite (or insert if absent) a `## Compaction Instructions` block in `CLAUDE.md`.
This step is **idempotent**: running `/phase-compact` twice produces exactly one block.

The block must contain the following tuned retention policy (substitute the actual phase N
number for `phase-N`):

```markdown
## Compaction Instructions

When compacting this conversation, use the following retention policy:

/compact Retain verbatim: .advanced-plans/phases/phase-[N]/handoff.md (the
validated phase resume digest), .advanced-plans/PLANNING.md frontmatter, and
any open cross-phase decisions/threads. Preserve all DECISIONS and their
rationale. Discard: verbatim file-Read contents and bash/tool_result output
(recoverable from disk + git); injected skill/command/tool-schema bodies;
gate-review agent-by-agent back-and-forth (final verdicts are on disk);
prior compaction summaries now superseded by handoff.md; resolved remediation
detail. Goal: keep the distilled signal, shed the raw I/O that dominates
context.
```

Procedure:

1. Read `CLAUDE.md`.
2. Search for an existing `## Compaction Instructions` section.
3. If found, replace the entire block (from `## Compaction Instructions` through the blank
   line before the next `##` heading or end-of-file) with the updated block above.
4. If not found, append the block at the end of `CLAUDE.md`.
5. Write the file.
6. Verify: `grep -c "## Compaction Instructions" CLAUDE.md` must print `1`.

Print:

```
  CLAUDE.md ## Compaction Instructions: updated (points at phase-[N] handoff.md)
```

### 16. Consent gate and compaction handoff

**Order invariant:** this step runs only after Steps 13-15 confirm artefacts written and validated.
This command NEVER self-invokes `/compact` — that is impossible and forbidden. This step only
emits the ready line for the user to run.

Ask the user:

```
AskUserQuestion: Artefacts written and validated:
  - .advanced-plans/phases/phase-[N]/complete.md   (schema-valid cold artefact)
  - .advanced-plans/phases/phase-[N]/handoff.md    (ceiling-OK resume digest)
  - CLAUDE.md ## Compaction Instructions            (updated)

Context is NOT yet compacted. The command never self-compacts.

Would you like to compact the conversation context now? (yes / no)
```

**If yes:**

Present the ready `/compact` line for the user to run:

```
Ready to compact. Copy and run the following line:

/compact Retain verbatim: .advanced-plans/phases/phase-[N]/handoff.md (the
validated phase resume digest), .advanced-plans/PLANNING.md frontmatter, and
any open cross-phase decisions/threads. Preserve all DECISIONS and their
rationale. Discard: verbatim file-Read contents and bash/tool_result output
(recoverable from disk + git); injected skill/command/tool-schema bodies;
gate-review agent-by-agent back-and-forth (final verdicts are on disk);
prior compaction summaries now superseded by handoff.md; resolved remediation
detail. Goal: keep the distilled signal, shed the raw I/O that dominates
context.
```

Print closing summary:

```
Phase [N] compaction artefacts complete.

  Artefacts written and validated:
    Cold artefact:  .advanced-plans/phases/phase-[N]/complete.md
    Handoff digest: .advanced-plans/phases/phase-[N]/handoff.md
    Manifest entry: .advanced-plans/PLANS-INDEX.md (phase [N] block)
    CLAUDE.md:      ## Compaction Instructions updated

  Context is NOT yet compacted.
  Run the /compact line above to compact. The resumed context will contain
  handoff.md + PLANNING.md dashboard as the on-task seed.

  Run /next-phase to begin the next phase (before or after compacting).
```

**If no:**

```
Phase [N] compaction artefacts complete. Context not compacted.

  The /compact line and ## Compaction Instructions block in CLAUDE.md remain
  available whenever you choose to compact. Run /next-phase to continue.
```

## Error Modes

| Condition | Behaviour |
|-----------|-----------|
| Missing `<phase-id>` argument | Print usage error and stop immediately |
| Phase plan not found at `.advanced-plans/phases/phase-[N]/plan.md` | Print error with expected path and stop |
| `anchor_sha` absent from frontmatter AND no phase-N events in `history.jsonl` | Print error listing both fallback paths tried and stop |
| `anchor_sha` or `end_sha` does not resolve via `git rev-parse` | Print the failing SHA and stop |
| Schema validation failure (cold artefact or manifest entry) | Print per-item diff of each failing checklist item; do not silently advance |
| Gate-fail input (`verdict: fail` in verdict file) | Write `.advanced-plans/phases/phase-[N]/complete-v[attempt]-failed.md` with `status: failed_v[attempt]`; manifest entry uses `status: failed_v[attempt]`; do not overwrite any existing pass-form artefact |
| `handoff_digest.py` exits non-zero (ceiling exceeded) | Print offending sections; stop before consent gate |
| `context_meter.py` cannot find transcript | Print "occupancy unavailable"; continue (graceful degrade) |

## Notes

**Idempotency guarantee:** running `/phase-compact [N]` twice produces the same cold artefact
and exactly one manifest entry. The second run updates in-place; it does not duplicate. SHAs
and `commit_count` are re-computed from git each time, so the artefact remains accurate if
commits were amended between runs (though this is discouraged after gate pass).

**No subagents:** this command runs on the main thread only. It does not spawn agents.

**No `/clear` here:** context clearing is a separate concern. Run `/phase-compact`
first to write artefacts, then apply `/clear` separately if desired.

**No self-compaction:** this command cannot and does not invoke `/compact` itself. There is no
`SlashCommand` tool; `PreCompact` is reactive/block-only; the SDK has no compaction API. The
command emits the ready `/compact` line for the user to run. Context is never compacted without
explicit user consent.

**Order invariant:** artefacts are written and validated (Steps 9-13) before any compaction
guidance is offered (Steps 14-16). This ensures compaction is always guided by a valid digest.

**Gate-fail artefacts:** failed-attempt artefacts (`complete-v[M]-failed.md`) persist
on disk when the phase is retried. If a later attempt passes, the pass-form artefact
(`complete.md`) is written alongside the failed versions. The manifest entry is
updated to `status: passed` on the passing run.

**`phase-goals-agent` verdict as primary input:** the command consumes the `phase-goals-agent`
verdict file, not the `code-review-agent` verdict. If both agents ran, reference only the
`phase-goals-agent` file in `gate_verdict_ref`.

**Phases 6 and 7 gap:** if compacting historical phases that predate the gate-review system,
the verdict path will be the sentinel string. The fallback `VERDICT_NOTE` field documents this.
Use the handoff-summary fallback (Step 8) for body sections.
