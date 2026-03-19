"""
AutoGen integration example — Advanced Planning System v8
=========================================================

Shows how to use the planning system's Python API to drive a single ralph loop
using Microsoft AutoGen as the agent orchestration framework.

This is an illustrative skeleton, not a production integration. Framework APIs
evolve rapidly; treat this as a pattern, not working code to copy verbatim.

Framework version at time of writing: autogen ~0.4.x (autogen-agentchat)

Usage:
    python example.py --plans-dir /path/to/plans --state-dir /path/to/state
"""

import argparse
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parents[4]))

from platforms.python.state_manager import write_loop_ready, read_loop_complete, append_history
from platforms.python.plan_io import find_next_loop
from platforms.python.handoff import make_empty_handoff, build_context_block

# ── AutoGen imports (install: pip install autogen-agentchat) ───────────────────
# from autogen_agentchat.agents import AssistantAgent
# from autogen_agentchat.teams import RoundRobinGroupChat
# from autogen_ext.models.anthropic import AnthropicChatCompletionClient


# ── Agent system messages ──────────────────────────────────────────────────────

ORCHESTRATOR_SYSTEM = """\
You are the ralph-orchestrator for this planning session. Your role is to prepare
the next pending ralph loop for execution.

Steps:
1. Read the loop plan file to find pending todos
2. Populate todos if needed (using plan-todos, plan-skill-identification skills)
3. Write loop-ready.json to the state directory
4. Reply TERMINATE when loop-ready.json is written

Do not execute tasks. The worker will handle execution.
"""

WORKER_SYSTEM = """\
You are the ralph-loop-worker. Your role is to execute todos with targeted skill injection.

Steps:
1. Read loop-ready.json from the state directory
2. For each pending todo:
   - Load the assigned SKILL.md immediately before executing (if skill != NA)
   - Execute the todo following the skill's instructions
   - Verify the outcome condition is met
   - Discard the skill before moving to the next todo
3. Write handoff_summary to the loop file
4. Write loop-complete.json to the state directory
5. Reply TERMINATE when loop-complete.json is written

Do not load all skills at startup. One skill per todo, loaded immediately before use.
"""


# ── AutoGen agent definitions (skeleton) ───────────────────────────────────────

def build_orchestrator_agent(state_dir: str, skills_dir: str):
    """
    Build the orchestrator AssistantAgent (Sonnet-tier).

    In a real implementation:

        from autogen_agentchat.agents import AssistantAgent
        from autogen_ext.models.anthropic import AnthropicChatCompletionClient

        client = AnthropicChatCompletionClient(model="claude-sonnet-4-6")
        return AssistantAgent(
            name="orchestrator",
            system_message=ORCHESTRATOR_SYSTEM,
            model_client=client,
            # Add tools for file I/O here
        )
    """
    raise NotImplementedError("Replace with AutoGen AssistantAgent definition")


def build_worker_agent(state_dir: str, skills_dir: str):
    """
    Build the worker AssistantAgent (Haiku-tier).

    In a real implementation:

        client = AnthropicChatCompletionClient(model="claude-haiku-4-5-20251001")
        return AssistantAgent(
            name="worker",
            system_message=WORKER_SYSTEM,
            model_client=client,
            # Add tools for file I/O here
        )
    """
    raise NotImplementedError("Replace with AutoGen AssistantAgent definition")


# ── Main orchestration loop ────────────────────────────────────────────────────

def run_next_loop(plans_dir: str, state_dir: str, skills_dir: str) -> bool:
    """Run the next pending ralph loop using AutoGen."""
    import asyncio

    plans = Path(plans_dir)
    state = Path(state_dir)

    # 1. Find next pending loop
    loop = find_next_loop(plans)
    if not loop:
        print("All loops complete.")
        return False

    print(f"Next loop: {loop['loop_name']} ({loop['task_name']})")

    # 2. Read prior handoff
    prior_complete = read_loop_complete(state)
    handoff = prior_complete["handoff"] if prior_complete else make_empty_handoff()
    context_block = build_context_block(handoff)

    # 3. Initial message to orchestrator
    initial_message = f"""\
{context_block}

Loop to execute: {loop['loop_name']} ({loop['task_name']})
Loop file: {loop['loop_file']}
State directory: {state_dir}
Skills directory: {skills_dir}

Orchestrator: read the loop file, populate todos if needed, write loop-ready.json.
Worker: wait for the orchestrator to finish, then execute todos with targeted skill injection.
    """

    # 4. Build agents and run (AutoGen 0.4.x async pattern)
    #
    # orchestrator = build_orchestrator_agent(state_dir, skills_dir)
    # worker = build_worker_agent(state_dir, skills_dir)
    #
    # For sequential orchestrator → worker (not simultaneous):
    # Option A: Two separate run() calls
    #   await orchestrator.run(task=initial_message)
    #   await worker.run(task="Execute the loop prepared by the orchestrator.")
    #
    # Option B: Use a GroupChat with a custom speaker selection function
    #   team = RoundRobinGroupChat([orchestrator, worker], max_turns=2)
    #   await team.run(task=initial_message)

    print("[Replace this block with AutoGen agent.run() or team.run()]")
    print(f"Initial message: {initial_message[:200]}...")

    # 5. Record completion
    complete = read_loop_complete(state)
    if complete:
        append_history(state, complete)
        print(f"Loop complete: {complete['status']}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the next planning loop via AutoGen")
    parser.add_argument("--plans-dir", default="plans")
    parser.add_argument("--state-dir", default="state")
    parser.add_argument("--skills-dir", default="core/skills")
    args = parser.parse_args()

    import asyncio
    # asyncio.run(run_next_loop(args.plans_dir, args.state_dir, args.skills_dir))
    # Sync wrapper for skeleton demo:
    run_next_loop(args.plans_dir, args.state_dir, args.skills_dir)
