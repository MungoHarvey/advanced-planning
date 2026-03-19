# AutoGen Integration Example

Illustrative skeleton showing how to use the planning system's Python API with Microsoft AutoGen.

## What This Shows

- How to define two `AssistantAgent` instances (orchestrator at Sonnet, worker at Haiku)
- How to structure an initial message with handoff context injected
- Two options for sequencing agents: separate `run()` calls, or `RoundRobinGroupChat`
- How to fit the planning API lifecycle around AutoGen's async run pattern

## Prerequisites

```bash
pip install autogen-agentchat autogen-ext
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

**`build_orchestrator_agent`**: Create an `AssistantAgent` with `model="claude-sonnet-4-6"` using `AnthropicChatCompletionClient`. The system message is already defined in `ORCHESTRATOR_SYSTEM`. Add file read/write tools so the agent can interact with plan files and the state directory.

**`build_worker_agent`**: Create an `AssistantAgent` with `model="claude-haiku-4-5-20251001"`. The `WORKER_SYSTEM` message emphasises targeted skill injection — loading one `SKILL.md` per todo.

**Sequencing the agents**: The orchestrator must complete before the worker starts (the worker reads `loop-ready.json` which the orchestrator writes). Two approaches:

```python
# Option A: Sequential separate runs (simplest)
await orchestrator.run(task=initial_message)
worker_task = f"Execute the loop prepared. State dir: {state_dir}"
await worker.run(task=worker_task)

# Option B: GroupChat with max_turns=2 (one turn each)
from autogen_agentchat.teams import RoundRobinGroupChat
team = RoundRobinGroupChat([orchestrator, worker], max_turns=2)
await team.run(task=initial_message)
```

Option A is recommended for clarity — the planning system's two-agent pattern maps naturally to two sequential agent calls, not a group chat.

## AutoGen-Specific Notes

AutoGen 0.4.x uses an async API. Wrap calls in `asyncio.run()` for synchronous usage. The `TERMINATE` keyword in agent replies is the standard AutoGen termination signal — include it in the system messages so agents know when to stop.

File I/O tools are critical: both agents need to read and write files in the plans and state directories. Look at `autogen_ext.tools.filesystem` or implement simple read/write tools using AutoGen's `@tool` decorator.
