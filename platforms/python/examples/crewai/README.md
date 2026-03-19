# CrewAI Integration Example

Illustrative skeleton showing how to use the planning system's Python API with CrewAI.

## What This Shows

- How to define two CrewAI Agents (orchestrator at Sonnet, worker at Haiku)
- How to structure Tasks with a dependency: worker Task takes orchestrator Task as context
- How to wire a sequential `Process` so orchestrator runs before worker
- How the planning API (`find_next_loop`, `read_loop_complete`, `append_history`) fits into the CrewAI lifecycle

## Prerequisites

```bash
pip install crewai crewai-tools
```

Set your API key:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

## Usage

```bash
python example.py --plans-dir /path/to/plans --state-dir /path/to/state
```

## What to Implement

The skeleton raises `NotImplementedError` in four functions. To make it runnable:

**`build_orchestrator_agent`**: Create a `crewai.Agent` with `llm="claude-sonnet-4-6"`, file read/write tools, and the orchestrator's goal and backstory. See `core/agents/orchestrator.md` for the role description.

**`build_worker_agent`**: Create a `crewai.Agent` with `llm="claude-haiku-4-5-20251001"`, file read/write tools, and the worker's goal. The backstory should emphasise targeted skill injection — loading one `SKILL.md` per todo.

**`build_orchestrator_task`**: A `crewai.Task` describing how to read the loop plan, populate todos if needed, and write `loop-ready.json`. The `expected_output` should be "loop-ready.json written to {state_dir}/".

**`build_worker_task`**: A `crewai.Task` with `context=[orchestrator_task]` so CrewAI ensures the orchestrator finishes first. The description should include the full targeted skill injection protocol.

## CrewAI-Specific Notes

CrewAI's `Process.sequential` runs tasks in order, which maps well to the orchestrator → worker pattern. The `context=` parameter in Task is the CrewAI equivalent of the state bus `loop-ready.json` wait — it ensures the worker task doesn't start until the orchestrator task completes.

For multi-loop programmes, wrap `run_next_loop()` in a `while` loop that continues until it returns `False`.
