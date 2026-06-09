# Fixture: Stub Loop for --full Demo

This file is a throwaway fixture used by loop-062-3 to demonstrate
that applying plan-todos → plan-skill-identification → plan-subagent-identification
in sequence on an unpopulated stub loop produces a fully-populated loop,
equivalent to the --full one-pass chain in /next-loop.

---

```yaml
---
name: "ralph-loop-fixture-full"
task_name: "Add schema validation helper to state_manager"
max_iterations: 3
on_max_iterations: escalate

handoff_summary:
  done: ""
  failed: ""
  needed: ""

todos:
  - id: "loop-fixture-full-1"
    content: "Add validate_state_file(path, schema_name) to platforms/python/state_manager.py: reads core/state/<schema_name>.json, validates the JSON at path against it using stdlib json module, raises ValueError with a descriptive message on mismatch"
    skill: "NA"
    agent: "NA"
    outcome: "validate_state_file function exists in state_manager.py; raises ValueError on schema mismatch; uses only stdlib (json, pathlib)"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-fixture-full-2"
    content: "Write pytest tests for validate_state_file in platforms/python/tests/: a happy-path test with a valid state file, an error-path test with an invalid file that asserts ValueError is raised with a non-empty message"
    skill: "verification-before-completion"
    agent: "NA"
    outcome: "At least two tests exist; all pass under pytest; no new external imports"
    status: pending
    complexity: medium
    priority: high
  - id: "loop-fixture-full-3"
    content: "Run python -m platforms.python.ast_check platforms/python/ --exclude tests/ --exclude examples/ and confirm it exits 0 (NONE)"
    skill: "NA"
    agent: "NA"
    outcome: "AST check exits 0 with NONE output; no forbidden imports detected"
    status: pending
    complexity: low
    priority: medium

prompt: |
  ## Objective
  Add a `validate_state_file(path, schema_name)` helper to platforms/python/state_manager.py
  that reads the JSON schema from core/state/<schema_name>.json and validates the state file,
  raising ValueError with a descriptive message on failure.

  ## Success Criteria
  - [ ] validate_state_file function exists in state_manager.py
  - [ ] Function raises ValueError with clear message when file does not match schema
  - [ ] At least one pytest test covers the happy path and one covers the error path
  - [ ] Zero external dependencies (stdlib only); AST check NONE

  ## Inputs
  - platforms/python/state_manager.py
  - core/state/*.json (JSON schema files)
  - platforms/python/tests/

  ## Constraints
  - stdlib only (json, pathlib, re, typing allowed)
  - No new files outside platforms/python/
```
