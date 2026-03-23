# Advanced Planning — Generic Python API

A framework-agnostic Python library for driving the v8 hierarchical planning system. Import three modules to coordinate orchestrator and worker agents in any framework — LangGraph, CrewAI, AutoGen, or your own.

**No external dependencies.** Standard library only (`pathlib`, `json`, `re`, `datetime`).

---

## Install

Copy the `platforms/python/` directory into your project, or install directly from GitHub:

```bash
# Direct copy
cp -r advanced-planning/platforms/python/ your_project/planning/

# Or add to your project as a submodule
git submodule add https://github.com/your-org/advanced-planning
```

Then import:

```python
from platforms.python.state_manager import write_loop_ready, read_loop_complete
from platforms.python.plan_io import find_next_loop, get_pending_todos
from platforms.python.handoff import inject_handoff, make_empty_handoff
from platforms.python.versioning import create_retry_version, inject_failure_context
```

---

## Modules

### `state_manager.py` — Filesystem state bus

Manages the three coordination files between orchestrator and worker.

#### `write_loop_ready(state_dir, *, loop_name, loop_file, task_name, todos_count, handoff_done="", handoff_failed="", handoff_needed="")`

Write `loop-ready.json` to signal the worker that a loop is prepared.

```python
from platforms.python.state_manager import write_loop_ready

write_loop_ready(
    "state",
    loop_name="ralph-loop-001",
    loop_file="plans/phase-1-ralph-loops.md",
    task_name="Schema Definitions",
    todos_count=4,
    handoff_done="Phase plan created.",
    handoff_needed="Derive todos for loop-001.",
)
```

#### `read_loop_complete(state_dir) → dict | None`

Read `loop-complete.json` written by the worker. Returns `None` if the file doesn't exist yet.

```python
from platforms.python.state_manager import read_loop_complete

result = read_loop_complete("state")
if result and result["status"] == "completed":
    print(result["handoff"]["done"])
```

#### `append_history(state_dir, record)` / `read_history(state_dir) → list`

Append a completion record to `history.jsonl` and read all records back.

#### `get_status(state_dir) → dict`

Summary snapshot of the state bus: `has_loop_ready`, `has_loop_complete`, `history_count`.

---

### `plan_io.py` — Plan file reading and writing

Parses loop plan Markdown files and their YAML frontmatter blocks.

#### `find_next_loop(plans_dir) → dict | None`

Scan all plan files and return metadata for the first loop with pending todos.

```python
from platforms.python.plan_io import find_next_loop

loop = find_next_loop("plans")
if loop:
    print(loop["loop_name"])     # "ralph-loop-002"
    print(loop["todos_count"])   # 3
    print(loop["loop_file"])     # "plans/phase-1-ralph-loops.md"
```

#### `get_pending_todos(loop_file, loop_name) → list`

Return all todos with `status: pending` for a named loop.

```python
from platforms.python.plan_io import get_pending_todos

todos = get_pending_todos("plans/phase-1-ralph-loops.md", "ralph-loop-002")
for todo in todos:
    print(todo["id"], todo["content"], todo["skill"])
```

#### `update_todo_status(loop_file, loop_name, todo_id, new_status) → bool`

Update a todo's `status` field in-place within the plan file.

```python
from platforms.python.plan_io import update_todo_status

update_todo_status("plans/phase-1-ralph-loops.md", "ralph-loop-002", "loop-002-1", "completed")
```

#### `parse_loop_frontmatter(loop_file, loop_name) → dict | None`

Return the full parsed frontmatter for a named loop, including `todos[]`, `handoff_summary`, and metadata fields.

#### `get_loop_handoff(loop_file, loop_name) → dict`

Return the `handoff_summary` dict (`done`, `failed`, `needed`) for a named loop.

---

### `versioning.py` — Versioned retry files

Creates and manages versioned loop files for gate-review retry cycles.

#### `create_retry_version(loop_file, *, attempt_number)`

Create a versioned copy of a loop file for a gate-review retry attempt (e.g. `phase-1-ralph-loops-v2.md`).

#### `inject_failure_context(loop_file, *, verdict)`

Inject a `gate_failure_context` YAML block into a loop file, carrying forward structured gate verdict information so the retry starts with full failure context.

#### `get_active_version(plans_index, *, phase)`

Read `PLANS-INDEX.md` to determine the currently active loop file version for a given phase.

#### `freeze_loop_file(loop_file)`

Freeze all todo statuses in a superseded loop file, marking it as a historical record that should not be re-executed.

---

### `handoff.py` — Handoff injection

Reads and injects the three-field handoff summary into prompt templates.

#### `inject_handoff(template, handoff) → str`

Replace `[inject prior.handoff_summary.*]` placeholders in a template string.

```python
from platforms.python.handoff import inject_handoff

template = """
## Context from prior loop
Done: [inject prior.handoff_summary.done]
Failed: [inject prior.handoff_summary.failed]
Needed: [inject prior.handoff_summary.needed]
"""

handoff = {"done": "4 schemas created.", "failed": "", "needed": "Plan loop-002 todos."}
prompt = inject_handoff(template, handoff)
```

#### `read_handoff(loop_complete_path) → dict`

Read the handoff block directly from a `loop-complete.json` file.

#### `inject_handoff_from_file(template, loop_complete_path) → str`

Convenience: read handoff from file and inject into template in one call.

#### `build_context_block(handoff, prefix="## Context from prior loop") → str`

Build the standard Done/Failed/Needed context block ready to prepend to a prompt.

#### `make_empty_handoff() → dict`

Return `{"done": "", "failed": "", "needed": ""}` — for the first loop in a programme.

---

## Full Workflow Example

```python
from pathlib import Path
from platforms.python.state_manager import write_loop_ready, read_loop_complete, append_history
from platforms.python.plan_io import find_next_loop, get_loop_handoff
from platforms.python.handoff import inject_handoff, make_empty_handoff

STATE = Path("state")
PLANS = Path("plans")
ORCHESTRATOR_TEMPLATE = Path("agents/orchestrator-prompt.md").read_text()
WORKER_TEMPLATE = Path("agents/worker-prompt.md").read_text()

# --- 1. Find next pending loop ---
loop = find_next_loop(PLANS)
if not loop:
    print("All loops complete.")
    exit()

# --- 2. Read prior handoff ---
prior_complete = read_loop_complete(STATE)
if prior_complete:
    handoff = prior_complete["handoff"]
else:
    handoff = make_empty_handoff()

# --- 3. Write loop-ready.json (orchestrator output) ---
write_loop_ready(
    STATE,
    loop_name=loop["loop_name"],
    loop_file=loop["loop_file"],
    task_name=loop["task_name"],
    todos_count=loop["todos_count"],
    handoff_done=handoff["done"],
    handoff_failed=handoff["failed"],
    handoff_needed=handoff["needed"],
)

# --- 4. Spawn orchestrator (framework-specific) ---
orchestrator_prompt = inject_handoff(ORCHESTRATOR_TEMPLATE, handoff)
# orchestrator_result = your_framework.run_agent(model="sonnet", prompt=orchestrator_prompt)

# --- 5. Spawn worker (framework-specific) ---
worker_prompt = inject_handoff(WORKER_TEMPLATE, handoff)
# worker_result = your_framework.run_agent(model="haiku", prompt=worker_prompt)

# --- 6. Read completion ---
complete = read_loop_complete(STATE)
if complete:
    append_history(STATE, complete)
    print(f"Loop {complete['loop_name']} finished: {complete['status']}")
    print(f"Done: {complete['handoff']['done']}")
```

See `examples/` for framework-specific integrations with LangGraph, CrewAI, and AutoGen.

---

## Running Tests

```bash
cd advanced-planning
python -m pytest platforms/python/tests/ -v
```

All 70 tests cover state manager round-trips, plan file parsing, todo extraction, status updates, handoff injection, and versioned retry file management.
