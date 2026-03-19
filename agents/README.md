# Agents Directory

Subagent definitions for multi-agent loop execution.

Each file defines a specialised Claude Code subagent that the orchestrator can
delegate todos to via the `agent:` field in loop frontmatter.

---

## What Subagents Are For

Subagents run in isolated context windows. Use them to:
- Keep long analysis tasks out of the orchestrator's context
- Run domain-specific work with focused instructions
- Parallelise independent todos across multiple agents

The orchestrator reads results from the agent's outputs (files, logs) rather than
carrying the full execution history forward.

---

## File Structure

```
.claude/agents/
├── README.md              ← This file
├── analysis-worker.md     ← Example: runs R/Python analysis tasks
├── code-reviewer.md       ← Example: reviews code against standards
└── [your-agent].md
```

---

## Agent File Format

```yaml
---
name: [agent-id]
description: "[What this agent does; when to assign todos to it]"
tools: [Bash, Read, Write, Edit]   ← Tools this agent is allowed to use
model: claude-sonnet-4-6           ← Optional: override model per agent
---

# [Agent Name]

## Role
[One sentence: what this agent is]

## Responsibilities
- [What it does]
- [What it produces]
- [What it does NOT do — important for scope control]

## Input Convention
Always receive inputs as:
- File paths to read (never raw data in prompt)
- Explicit output paths to write results to
- Handoff context from orchestrator (done / failed / needed)

## Output Convention
Always produce:
- Results written to specified output paths
- A brief completion note: what was done, any issues, output locations
- Never modify the plan file directly (orchestrator's responsibility)

## Instructions
[Detailed instructions for this agent type]
```

---

## Starter Template

Copy this to create a new agent:

```yaml
---
name: [agent-name]
description: "[What this agent does and when to assign todos to it]"
tools: [Bash, Read, Write, Edit]
---

# [Agent Name]

## Role
[One sentence]

## Responsibilities
- [Task type 1]
- [Task type 2]
- Does NOT: modify plan files, update todo status, or call other agents

## Input Convention
Receive from orchestrator:
- `input_path`: file(s) to operate on
- `output_path`: where to write results
- `context`: brief handoff note (what's done, what's needed)

## Output Convention
On completion, write a brief note to stdout:
```
DONE: [what was produced]
OUTPUT: [path(s)]
ISSUES: [any problems encountered, or "none"]
```

## Instructions
[Your agent-specific instructions here]
```

---

## Assigning Agents to Todos

Agents are assigned by `@plan-subagent-identification` during loop planning.
The `agent:` field in each todo references the agent's `name` from frontmatter.

```yaml
todos:
  - id: loop-003-1
    content: "Run PCA on corrected expression matrix"
    skill: dimensionality-reduction
    agent: analysis-worker        ← references .claude/agents/analysis-worker.md
    outcome: "plots/pca.pdf saved, top 10 PCs explain >60% variance"
    status: pending
    priority: high
```

During `/next-loop` execution, the orchestrator spawns the subagent using Claude Code's
`Task` tool with the agent file's instructions as the system prompt.
