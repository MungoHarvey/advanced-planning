# LangGraph Integration Example

Illustrative skeleton showing how to use the planning system's Python API with LangGraph.

## What This Shows

- How to find the next pending loop using `find_next_loop()`
- How to build orchestrator and worker prompts with handoff context injected
- How to structure a LangGraph `StateGraph` with two nodes (orchestrator → worker)
- How to read `loop-complete.json` and record to `history.jsonl` after execution

## Prerequisites

```bash
pip install langgraph langchain-anthropic
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

The `build_planning_graph()` function is a commented-out skeleton. To make it runnable:

1. Define a `TypedDict` for graph state
2. Create `ChatAnthropic` instances — `claude-sonnet-4-6` for orchestrator, `claude-haiku-4-5-20251001` for worker
3. Add file read/write tools as `ToolNode` instances (the agents need to read plan files and write state files)
4. Wire the graph: orchestrator → worker → END

The orchestrator's job (from `core/agents/orchestrator.md`): read plans, populate todos if needed, write `state/loop-ready.json`.

The worker's job (from `core/agents/worker.md`): read `loop-ready.json`, execute todos with targeted skill injection, write `state/loop-complete.json`.

## Important: Targeted Skill Injection

The worker must implement the targeted skill injection protocol — loading the assigned `SKILL.md` per-todo, not all at once. In a LangGraph implementation, this means the worker node must:

1. Read the todo's `skill` field
2. Read `skills/[skill]/SKILL.md` before executing the todo
3. Pass the skill content as part of the tool context or system prompt for that specific step
4. Clear it before the next todo

This is the highest-value behaviour to preserve in any framework integration.
