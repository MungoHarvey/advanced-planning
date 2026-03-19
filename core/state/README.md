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
