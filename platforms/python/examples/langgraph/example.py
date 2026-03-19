"""
LangGraph integration example — Advanced Planning System v8
===========================================================

Shows how to use the planning system's Python API to drive a single ralph loop
using LangGraph as the agent orchestration framework.

This is an illustrative skeleton, not a production integration. Framework APIs
evolve rapidly; treat this as a pattern, not working code to copy verbatim.

Framework version at time of writing: langgraph ~0.2.x

Usage:
    python example.py --plans-dir /path/to/plans --state-dir /path/to/state
"""

import argparse
from pathlib import Path

# ── Planning system API ────────────────────────────────────────────────────────
# Adjust the import path to match where you've installed platforms/python/
import sys
sys.path.insert(0, str(Path(__file__).parents[4]))

from platforms.python.state_manager import write_loop_ready, read_loop_complete, append_history
from platforms.python.plan_io import find_next_loop, get_loop_handoff
from platforms.python.handoff import inject_handoff, make_empty_handoff, build_context_block

# ── LangGraph imports (install: pip install langgraph) ─────────────────────────
# from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolNode
# from langchain_anthropic import ChatAnthropic


# ── Agent prompt templates ─────────────────────────────────────────────────────

ORCHESTRATOR_TEMPLATE = """\
You are the ralph-orchestrator for this planning session.

{context_block}

Your job: prepare the next pending loop and write loop-ready.json.

Plans directory: {plans_dir}
State directory: {state_dir}
Skills directory: {skills_dir}

Read the next pending loop, populate its todos if needed, then write
{state_dir}/loop-ready.json with the required fields.

See core/agents/orchestrator.md for the full protocol.
"""

WORKER_TEMPLATE = """\
You are the ralph-loop-worker for this planning session.

{context_block}

Your job: execute the loop specified in loop-ready.json using targeted skill injection.

State directory: {state_dir}
Skills directory: {skills_dir}

Read {state_dir}/loop-ready.json, execute each todo by loading its assigned
SKILL.md immediately before execution (then unloading it), verify outcomes,
write handoff_summary, then write {state_dir}/loop-complete.json.

See core/agents/worker.md for the full protocol.
"""


# ── LangGraph graph definition (skeleton) ─────────────────────────────────────

def build_planning_graph(plans_dir: str, state_dir: str, skills_dir: str):
    """
    Build a LangGraph StateGraph for a single planning loop cycle.

    The graph has two nodes:
      orchestrator_node → worker_node → END

    In a real implementation, you would:
    1. Define a TypedDict for the graph state
    2. Create ChatAnthropic instances with the right models
    3. Add tools (file read/write) as ToolNodes
    4. Wire up the graph with conditional edges

    Example (requires langgraph and langchain_anthropic installed):

        from langgraph.graph import StateGraph, END
        from langchain_anthropic import ChatAnthropic
        from typing import TypedDict

        class PlanState(TypedDict):
            loop_ready: dict
            loop_complete: dict

        orchestrator_llm = ChatAnthropic(model="claude-sonnet-4-6")
        worker_llm = ChatAnthropic(model="claude-haiku-4-5-20251001")

        def orchestrator_node(state: PlanState) -> PlanState:
            # Build the orchestrator prompt
            prompt = ORCHESTRATOR_TEMPLATE.format(...)
            response = orchestrator_llm.invoke(prompt)
            # In practice: agent reads files, writes loop-ready.json
            loop_ready = read_loop_ready(state_dir)
            return {**state, "loop_ready": loop_ready}

        def worker_node(state: PlanState) -> PlanState:
            # Build the worker prompt
            prompt = WORKER_TEMPLATE.format(...)
            response = worker_llm.invoke(prompt)
            loop_complete = read_loop_complete(state_dir)
            return {**state, "loop_complete": loop_complete}

        graph = StateGraph(PlanState)
        graph.add_node("orchestrator", orchestrator_node)
        graph.add_node("worker", worker_node)
        graph.add_edge("orchestrator", "worker")
        graph.add_edge("worker", END)
        graph.set_entry_point("orchestrator")
        return graph.compile()
    """
    # Placeholder — replace with real LangGraph implementation
    raise NotImplementedError("Replace this with your LangGraph graph definition")


# ── Main orchestration loop ────────────────────────────────────────────────────

def run_next_loop(plans_dir: str, state_dir: str, skills_dir: str) -> bool:
    """
    Run the next pending ralph loop using LangGraph.

    Returns True if a loop was executed, False if all loops are complete.
    """
    plans = Path(plans_dir)
    state = Path(state_dir)

    # 1. Find the next pending loop
    loop = find_next_loop(plans)
    if not loop:
        print("All loops complete.")
        return False

    print(f"Next loop: {loop['loop_name']} ({loop['task_name']})")

    # 2. Read prior handoff
    prior_complete = read_loop_complete(state)
    if prior_complete:
        handoff = prior_complete["handoff"]
    else:
        handoff = make_empty_handoff()

    # 3. Build context block for agent prompts
    context_block = build_context_block(handoff)

    # 4. Build agent prompts
    orchestrator_prompt = ORCHESTRATOR_TEMPLATE.format(
        context_block=context_block,
        plans_dir=plans_dir,
        state_dir=state_dir,
        skills_dir=skills_dir,
    )
    worker_prompt = WORKER_TEMPLATE.format(
        context_block=context_block,
        state_dir=state_dir,
        skills_dir=skills_dir,
    )

    # 5. Build and run the LangGraph graph
    # In a real implementation:
    #   graph = build_planning_graph(plans_dir, state_dir, skills_dir)
    #   result = graph.invoke({"orchestrator_prompt": orchestrator_prompt,
    #                          "worker_prompt": worker_prompt})
    print(f"Orchestrator prompt (first 200 chars): {orchestrator_prompt[:200]}...")
    print(f"Worker prompt (first 200 chars): {worker_prompt[:200]}...")
    print("[Replace this with: graph.invoke(...)]")

    # 6. Read loop completion and record to history
    complete = read_loop_complete(state)
    if complete:
        append_history(state, complete)
        print(f"Loop complete: {complete['status']}")
        print(f"Done: {complete['handoff']['done']}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the next planning loop via LangGraph")
    parser.add_argument("--plans-dir", default="plans", help="Directory containing plan files")
    parser.add_argument("--state-dir", default="state", help="Directory for state bus files")
    parser.add_argument("--skills-dir", default="core/skills", help="Directory containing skills")
    args = parser.parse_args()

    run_next_loop(args.plans_dir, args.state_dir, args.skills_dir)
