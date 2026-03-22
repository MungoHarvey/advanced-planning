# State Bus Protocol

Filesystem-based coordination between the orchestrator, worker, and main thread. No databases, no message queues — just JSON files written and read sequentially.

---

## Design Principles

1. **Sequential, not concurrent.** Files are written by one process and read by another. There is never concurrent write access.
2. **Human-readable.** Every state file is a JSON document you can inspect with `cat`.
3. **Platform-agnostic.** Any environment with a filesystem can implement this protocol.
4. **Ephemeral coordination, authoritative plan files.** State files represent current loop state. The plan file frontmatter is the permanent record.

---

## Files

| File | Written By | Read By | Lifecycle |
|------|-----------|---------|-----------|
| `loop-ready.json` | Orchestrator | Main thread + Worker | Overwritten each loop cycle |
| `loop-complete.json` | Worker | Main thread | Overwritten each loop cycle |
| `history.jsonl` | Main thread | Diagnostics / analytics | Append-only (optional) |

---

## Protocol Sequence

```
Main Thread          Orchestrator (Sonnet)       Worker (Haiku)
    │
    ├─ Spawn ────────►│
    │                 ├─ Find next pending loop
    │                 ├─ Populate todos/skills/agents
    │                 ├─ Write loop-ready.json
    │                 ├─ Return
    │◄────────────────┘
    │
    ├─ Read loop-ready.json
    ├─ Print loop summary
    │
    ├─ Spawn ──────────────────────────────────►│
    │                                           ├─ Read loop-ready.json
    │                                           ├─ Execute todos
    │                                           ├─ Write loop-complete.json
    │                                           ├─ Return
    │◄──────────────────────────────────────────┘
    │
    ├─ Read loop-complete.json
    ├─ Update CLAUDE.md Planning State
    ├─ Append to history.jsonl (optional)
    ├─ Git commit
    └─ Print cycle summary
```

---

## File Schemas

### loop-ready.json

See `loop-ready.schema.json` for the full JSON Schema.

```json
{
  "loop_name": "ralph-loop-001",
  "loop_file": "plans/phase-1-ralph-loops.md",
  "task_name": "Schema Definitions",
  "todos_count": 5,
  "prepared_at": "2026-03-19T10:00:00Z",
  "status": "ready",
  "handoff_injected": {
    "done": "Phase plan approved; repository skeleton created.",
    "failed": "",
    "needed": ""
  }
}
```

When all loops are complete, the orchestrator writes:
```json
{
  "status": "all_complete"
}
```

### loop-complete.json

See `loop-complete.schema.json` for the full JSON Schema.

```json
{
  "loop_name": "ralph-loop-001",
  "loop_file": "plans/phase-1-ralph-loops.md",
  "status": "completed",
  "todos_done": 5,
  "todos_failed": 0,
  "completed_at": "2026-03-19T11:30:00Z",
  "handoff": {
    "done": "All 4 schema documents created in core/schemas/ with field specs, examples, and validation checklists.",
    "failed": "",
    "needed": ""
  },
  "duration_seconds": 5400
}
```

### history.jsonl (optional)

Append-only log. Each line is a JSON object recording one state transition:

```jsonl
{"event": "loop_ready", "loop_name": "ralph-loop-001", "timestamp": "2026-03-19T10:00:00Z", "todos_count": 5}
{"event": "loop_complete", "loop_name": "ralph-loop-001", "timestamp": "2026-03-19T11:30:00Z", "status": "completed", "todos_done": 5, "todos_failed": 0}
{"event": "loop_ready", "loop_name": "ralph-loop-002", "timestamp": "2026-03-19T11:35:00Z", "todos_count": 6}
```

This provides a timeline of all loop executions without modifying the ephemeral state files.

#### Gate Review Event Types

Four additional event types are appended by the main thread when gate review runs. These events are immutable — once written they are never updated or removed.

| Event Type | Trigger |
|------------|---------|
| `gate_pass` | All configured gate agents return `pass` verdicts; phase can advance |
| `gate_fail` | Any gate agent returns a `fail` verdict; versioned retry files are created |
| `phase_retry` | New versioned loop files created after gate failure; retry loop begins |
| `closeout` | Programme closeout synthesis completed by the programme-reporter agent |

```jsonl
{"event": "gate_pass", "phase": "phase-2", "attempt": 1, "timestamp": "2026-03-22T12:00:00Z", "agents": ["code-review-agent", "phase-goals-agent"], "verdict_files": ["gate-verdicts/phase-2-attempt-1-code-review.json", "gate-verdicts/phase-2-attempt-1-phase-goals.json"]}
{"event": "gate_fail", "phase": "phase-2", "attempt": 1, "timestamp": "2026-03-22T12:05:00Z", "agent": "code-review-agent", "verdict_file": "gate-verdicts/phase-2-attempt-1-code-review.json", "loops_to_revert": ["ralph-loop-002", "ralph-loop-003"]}
{"event": "phase_retry", "phase": "phase-2", "attempt": 2, "timestamp": "2026-03-22T12:10:00Z", "new_loop_file": "plans/phase-2-ralph-loops-v2.md", "original_loop_file": "plans/phase-2-ralph-loops.md"}
{"event": "closeout", "timestamp": "2026-03-22T18:00:00Z", "phases_completed": 5, "total_loops": 28, "total_retries": 2, "report_file": "docs/programme-closeout.md"}
```

---

## Runtime Directory

```
.claude/state/                  ← or equivalent for non-Claude Code platforms
├── loop-ready.json             ← Current assignment (overwritten each cycle)
├── loop-complete.json          ← Current result (overwritten each cycle)
└── history.jsonl               ← Audit log (append-only, optional)
```

---

## Adapter Responsibilities

| Responsibility | Claude Code | Cowork | Generic |
|---------------|-------------|--------|---------|
| Write loop-ready.json | ralph-orchestrator agent | Orchestrator via Agent tool | `state_manager.write_ready()` |
| Write loop-complete.json | ralph-loop-worker agent | Worker via Agent tool | `state_manager.write_complete()` |
| Read state files | /next-loop command | Routing SKILL.md | `state_manager.read_ready()` |
| Append to history.jsonl | /next-loop command | Routing SKILL.md | `state_manager.append_history()` |
| State directory location | `.claude/state/` | Workspace folder | Configurable |

---

## Gate Review Protocol

The gate review sub-phase runs between phase completion and phase advancement. Gate agents coordinate via a dedicated `gate-verdicts/` directory alongside the standard state bus files.

### Gate Verdict Files

Each gate agent writes a verdict to `gate-verdicts/` when it completes its review. Verdict files are immutable — one file per agent per attempt, never overwritten. File naming convention:

```
gate-verdicts/{phase}-attempt-{N}-{agent}.json
```

Example: `gate-verdicts/phase-2-attempt-1-code-review.json`

See `gate-verdict.schema.json` for the full JSON Schema.

### Gate Review Sequence

```
Main Thread          Gate Agent(s)
    │
    ├─ Spawn ────────►│
    │                 ├─ Read phase plan + all loop files
    │                 ├─ Read all produced outputs
    │                 ├─ Evaluate against phase success criteria
    │                 ├─ Write gate-verdicts/{phase}-attempt-{N}-{agent}.json
    │                 └─ Return
    │◄────────────────┘
    │
    ├─ Read all verdict files for this phase + attempt
    ├─ If ALL verdicts = pass:
    │   ├─ Append gate_pass to history.jsonl
    │   └─ Advance to next phase
    │
    └─ If ANY verdict = fail:
        ├─ Append gate_fail to history.jsonl
        ├─ Create versioned retry files (phase-N-ralph-loops-v{attempt+1}.md)
        ├─ Inject gate_failure_context into new loop files
        ├─ Update PLANS-INDEX.md active pointer
        ├─ Append phase_retry to history.jsonl
        └─ Begin retry cycle
```

### Gate Failure Context Injection

When a gate fails, the structured failure context is injected into every new versioned loop file as a `gate_failure_context` frontmatter block. This gives the retry attempt full context without requiring it to re-read the verdict file.

See `gate-failure-context.schema.json` for the full JSON Schema and `core/schemas/ralph-loop.schema.md` for how this block appears in loop frontmatter.

### Immutability Constraints

| Artefact | Constraint |
|----------|-----------|
| Gate verdict files | Written once per agent per attempt; never overwritten |
| Original loop files | Frozen after gate failure; status fields not updated on retry |
| history.jsonl | Append-only; gate events are never removed or modified |
| Failure notes | Preserved in `gate_failure_context.do_not_repeat` across all retries |
