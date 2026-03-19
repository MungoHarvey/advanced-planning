# Todo Schema

A todo is an atomic, verifiable unit of work within a ralph loop. Every todo has a concrete `outcome` field that defines what "done" means as an observable condition.

---

## Two-Layer Architecture

Todos exist in two representations that must stay synchronised:

| Layer | Location | Schema | Authority |
|-------|----------|--------|-----------|
| **Frontmatter** (Layer 1) | Ralph loop YAML frontmatter | Extended: `id`, `content`, `skill`, `agent`, `outcome`, `status`, `priority` | **Authoritative** — source of truth |
| **Native TodoWrite** (Layer 2) | Claude Code / Cowork sidebar | Subset: `id`, `content → outcome`, `status`, `priority` | Display — derived from Layer 1 |

If there is ever a conflict, Layer 1 (frontmatter) wins.

---

## Frontmatter Schema (Layer 1)

Fields MUST appear in this canonical order. Agents must maintain this order when editing to prevent schema drift.

```yaml
todos:
  - id: "loop-{NNN}-{N}"          # Globally unique: loop number + todo number
    content: ""                    # Atomic task description (verb-first, specific)
    skill: ""                      # Skill name from skills directory, or "NA"
    agent: ""                      # Subagent ID from agents directory, or "NA"
    outcome: ""                    # Observable completion condition
    status: pending                # pending | in_progress | completed | cancelled
    priority: high                 # high | medium | low
```

### Field Specifications

| Field | Type | Required | Format | Rules |
|-------|------|----------|--------|-------|
| `id` | string | Yes | `loop-{NNN}-{N}` | Globally unique; matches native TodoWrite ID |
| `content` | string | Yes | Verb-first imperative | One atomic action; no compound tasks |
| `skill` | string | Yes | skill-name or `NA` | Must reference an existing skill, or `NA` for general tasks |
| `agent` | string | Yes | agent-id or `NA` | Must reference an existing agent, or `NA` for orchestrator-inline tasks |
| `outcome` | string | Yes | Observable condition | What must exist or pass — not effort description |
| `status` | enum | Yes | See below | Updated in-place during execution |
| `priority` | enum | Yes | `high`, `medium`, `low` | Default: `high` for blocking tasks |

### Status Values

| Status | Meaning | Transitions From |
|--------|---------|------------------|
| `pending` | Not yet started | (initial state) |
| `in_progress` | Currently being executed | `pending` |
| `completed` | Done — outcome verified | `in_progress` |
| `cancelled` | Explicitly skipped with documented reason | `pending`, `in_progress` |

**Rule**: Only ONE todo may be `in_progress` at a time. Set the current todo to `completed` or `cancelled` before starting the next.

---

## Native TodoWrite Schema (Layer 2)

For platforms with a native todo sidebar (Claude Code, Cowork), derive this from Layer 1:

```json
{
  "content": "{content} → outcome: {outcome}",
  "status": "{status}",
  "activeForm": "{content in present continuous}"
}
```

The `outcome` is embedded in `content` using the ` → outcome: ` separator so it remains visible in the sidebar.

### Sync Protocol

1. **Loop start**: Call TodoWrite with all loop todos mapped to native format
2. **During execution**: Update status via TodoWrite immediately when each todo changes
3. **Do not batch**: Update on each transition, not at end of loop
4. **Canonical source**: Frontmatter YAML — native TodoWrite is display-only

---

## Outcome Writing Standards

The `outcome` field answers: **"What must be true in the world for this todo to be done?"**

### Valid Outcomes (observable conditions)

```yaml
# File existence + validation
outcome: "data/normalised.rds exists; dim() matches input; no NA values"

# Test passing
outcome: "pytest exits 0; coverage ≥85%; linter clean with 0 warnings"

# Numeric threshold
outcome: "dir_acc ≥ 0.55 on test fold; documented in analysis/logs/"

# Content requirement
outcome: "reports/qc.md contains sample counts, NA summary, PCA interpretation"

# Schema/format validation
outcome: "loop-ready.json validates against core/state/loop-ready.schema.json"
```

### Invalid Outcomes (effort descriptions)

```yaml
# ❌ These describe effort, not observable conditions:
outcome: "Task complete"
outcome: "Code written"
outcome: "Looked at the data"
outcome: "Done"
outcome: "Run the script"
```

---

## Skill Assignment Levels

Skills are identified at three levels during planning. The `skill:` field in a todo holds the most specific level:

| Level | Assigned By | Example |
|-------|-------------|---------|
| Phase-level (broad) | `@phase-plan-creator` | `statistical-analysis` |
| Loop-level (specific) | `@ralph-loop-planner` | `data-processing`, `output-formatting` |
| Todo-level (precise) | `@plan-skill-identification` | `schema-design`, `docx` |

The todo's `skill:` field holds the **todo-level** assignment. At execution time, the worker agent loads the corresponding `SKILL.md` before executing the todo (see `core/agents/worker.md` for the skill injection protocol).

---

## Agent Assignment Rules

| Delegate to agent when... | Keep as `NA` (orchestrator-inline) when... |
|---------------------------|--------------------------------------------|
| Task is self-contained with clear I/O | Task coordinates or synthesises other tasks |
| Task requires deep domain focus | Task reads/writes plan files |
| Task is long-running (would pollute context) | Task is a simple one-liner (git, file copy) |
| Task is parallelisable with other todos | No suitable agent exists |

---

## In-Place Editing Rules

When agents update todos in the plan file:

1. **Maintain field order**: `id → content → skill → agent → outcome → status → priority`
2. **Only update mutable fields**: `status`, `skill`, `agent` may change; `id`, `content`, `outcome` are immutable after planning
3. **One in_progress at a time**: Set previous to `completed` before starting next
4. **Verify outcome before completing**: Read the output, run the check, confirm the condition

---

## Validation Checklist

Before executing a loop's todos, verify:

- [ ] Every todo has a unique `id` following `loop-{NNN}-{N}` format
- [ ] Every `content` starts with a verb and describes one atomic action
- [ ] Every `outcome` is an observable condition, not an effort description
- [ ] `skill:` values reference existing skills or are `NA`
- [ ] `agent:` values reference existing agents or are `NA`
- [ ] All todos start as `pending`
- [ ] Fields appear in canonical order
