"""
CrewAI integration example — Advanced Planning System v8
=========================================================

Shows how to use the planning system's Python API to drive a single ralph loop
using CrewAI as the agent orchestration framework.

This is an illustrative skeleton, not a production integration. Framework APIs
evolve rapidly; treat this as a pattern, not working code to copy verbatim.

Framework version at time of writing: crewai ~0.80.x

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

# ── CrewAI imports (install: pip install crewai) ───────────────────────────────
# from crewai import Agent, Task, Crew, Process
# from crewai_tools import FileReadTool, FileWriteTool


# ── Agent definitions (skeleton) ───────────────────────────────────────────────

def build_orchestrator_agent(skills_dir: str):
    """
    Build the orchestrator agent (Sonnet-tier).

    In a real implementation:

        from crewai import Agent
        from crewai_tools import FileReadTool, FileWriteTool

        return Agent(
            role="Ralph Orchestrator",
            goal="Prepare the next pending ralph loop for execution",
            backstory=(
                "You are a tactical planning agent. You read plan files, "
                "populate todos if needed, and write loop-ready.json."
            ),
            tools=[FileReadTool(), FileWriteTool()],
            llm="claude-sonnet-4-6",
            verbose=True,
        )
    """
    raise NotImplementedError("Replace with CrewAI Agent definition")


def build_worker_agent(skills_dir: str):
    """
    Build the worker agent (Haiku-tier).

    In a real implementation:

        return Agent(
            role="Ralph Loop Worker",
            goal="Execute todos with targeted skill injection; write loop-complete.json",
            backstory=(
                "You are an execution agent. For each todo, you load the assigned "
                "SKILL.md, execute the task following its instructions, verify the "
                "outcome, then discard the skill before the next todo."
            ),
            tools=[FileReadTool(), FileWriteTool()],
            llm="claude-haiku-4-5-20251001",
            verbose=True,
        )
    """
    raise NotImplementedError("Replace with CrewAI Agent definition")


# ── Task definitions (skeleton) ────────────────────────────────────────────────

def build_orchestrator_task(agent, loop_info: dict, state_dir: str, context_block: str):
    """
    Build the orchestrator's Task.

    In a real implementation:

        from crewai import Task

        return Task(
            description=f'''
                {context_block}

                Loop to prepare: {loop_info["loop_name"]} ({loop_info["task_name"]})
                Loop file: {loop_info["loop_file"]}
                State directory: {state_dir}

                1. Read the loop file and check if todos need population
                2. If needed: load plan-todos, plan-skill-identification, plan-subagent-identification
                3. Write {state_dir}/loop-ready.json with the required fields
                4. Return when loop-ready.json is written
            ''',
            expected_output=f"loop-ready.json written to {state_dir}/",
            agent=agent,
        )
    """
    raise NotImplementedError("Replace with CrewAI Task definition")


def build_worker_task(agent, state_dir: str, skills_dir: str, context_block: str, orchestrator_task=None):
    """
    Build the worker's Task.

    In a real implementation, pass orchestrator_task as context= to create a dependency:

        return Task(
            description=f'''
                {context_block}

                State directory: {state_dir}
                Skills directory: {skills_dir}

                1. Read {state_dir}/loop-ready.json
                2. For each pending todo:
                   a. Read skills/{todo.skill}/SKILL.md (if skill != NA)
                   b. Execute the todo following the skill's instructions
                   c. Verify the outcome condition
                   d. Discard the skill context
                3. Write handoff_summary to the loop file
                4. Write {state_dir}/loop-complete.json
            ''',
            expected_output=f"loop-complete.json written to {state_dir}/",
            agent=agent,
            context=[orchestrator_task],  # depends on orchestrator completing first
        )
    """
    raise NotImplementedError("Replace with CrewAI Task definition")


# ── Main orchestration loop ────────────────────────────────────────────────────

def run_next_loop(plans_dir: str, state_dir: str, skills_dir: str) -> bool:
    """Run the next pending ralph loop using CrewAI."""
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

    # 3. Build agents and tasks
    # orchestrator = build_orchestrator_agent(skills_dir)
    # worker = build_worker_agent(skills_dir)
    # orch_task = build_orchestrator_task(orchestrator, loop, state_dir, context_block)
    # work_task = build_worker_task(worker, state_dir, skills_dir, context_block, orch_task)

    # 4. Create and run the Crew (sequential process: orchestrator → worker)
    # crew = Crew(
    #     agents=[orchestrator, worker],
    #     tasks=[orch_task, work_task],
    #     process=Process.sequential,
    #     verbose=True,
    # )
    # crew.kickoff()

    print("[Replace this block with crew.kickoff()]")

    # 5. Record completion
    complete = read_loop_complete(state)
    if complete:
        append_history(state, complete)
        print(f"Loop complete: {complete['status']}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the next planning loop via CrewAI")
    parser.add_argument("--plans-dir", default="plans")
    parser.add_argument("--state-dir", default="state")
    parser.add_argument("--skills-dir", default="core/skills")
    args = parser.parse_args()
    run_next_loop(args.plans_dir, args.state_dir, args.skills_dir)
