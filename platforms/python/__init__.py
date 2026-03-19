"""
advanced-planning — Generic Python API
=======================================

A framework-agnostic library for driving the v8 hierarchical planning system.
Import the three modules directly:

    from platforms.python.state_manager import write_loop_ready, read_loop_complete
    from platforms.python.plan_io import find_next_loop, get_pending_todos
    from platforms.python.handoff import read_handoff, inject_handoff

No external dependencies — standard library only (pathlib, json, re, datetime).
"""

__version__ = "0.8.0"
__all__ = ["state_manager", "plan_io", "handoff"]
