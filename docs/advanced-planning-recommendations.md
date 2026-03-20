# Advanced Planning Architecture: Recommendations & Redesign Specification

**Subagent Injection, Ralph Loop Integration & Handoff Protocol**

---

## 1. Executive Summary

This document captures architectural recommendations for the advanced planning pipeline in Claude Code, addressing three interconnected issues identified through this session:

1. **Skill loading in subagents is probabilistic** — a single injection mechanism without enforcement is insufficient
2. **The ralph-loop plugin is not being used** — a first-party Anthropic plugin exists specifically for Claude Code and is entirely absent from the current pipeline
3. **There is no structured handoff protocol** — the orchestrator has no reliable way to evaluate what a coding worker actually accomplished, making stop/go decisions unreliable

Each recommendation is grounded in the specific behaviour and known constraints of Claude Code's subagent system discussed in this session.

---

## 2. The Ralph Loop Plugin — What It Is and Whether It Is Being Used

### 2.1 What the Plugin Actually Is

The ralph-loop plugin is an **official, first-party Anthropic plugin** maintained at `anthropics/claude-plugins-official`. It is not a community tool or third-party implementation — it is part of Anthropic's own plugin catalogue, available via:

```
/plugin install ralph-wiggum@claude-plugins-official
```

It is also listed directly at `claude.com/plugins/ralph-loop`.

The plugin implements the **Ralph Wiggum technique** — named after the Simpsons character, coined by developer Geoffrey Huntley as "Ralph is a Bash loop." The core mechanism:

1. You run `/ralph-loop "your task" --max-iterations 20 --completion-promise "DONE"` once
2. Claude works on the task
3. When Claude tries to exit, a **Stop hook** intercepts the exit attempt
4. The same prompt is fed back, with all modified files and git history preserved from the previous iteration
5. This repeats until Claude outputs the exact completion promise string, or max iterations is reached

The critical property is that each iteration **is not a fresh start** — Claude sees its own prior work, including file modifications and commits, creating a genuine self-correcting feedback loop.

### 2.2 Is It Being Used in the Current Pipeline?

**No.** The ralph-loop plugin is entirely absent from the current Claude Code advanced planning architecture.

What exists instead is a `ralph-loop-planner` **skill file** — a markdown document that describes the ralph loop methodology conceptually and teaches the orchestrator what a loop is. This is not the same thing.

| | Current Pipeline | Ralph Loop Plugin |
|---|---|---|
| **What it is** | A SKILL.md describing the methodology | An official Claude Code plugin with a Stop hook |
| **How loops iterate** | Orchestrator follows skill instructions (probabilistic) | Stop hook mechanically intercepts exit and re-feeds prompt |
| **Retry on failure** | Depends on orchestrator interpreting the skill correctly | Automatic — built into the hook |
| **Completion signal** | Text-based, subject to interpretation | Exact `<promise>` tag string match |
| **Max iterations** | Defined in skill docs, not enforced | Enforced by the hook — terminates hard |
| **State between iterations** | Dependent on context window | Git history + modified files persist reliably |

### 2.3 Why This Gap Matters

The current pipeline describes ralph loop behaviour but does not enforce it. Whether the orchestrator actually retries failed tasks, checks a completion promise, and iterates up to a maximum is entirely dependent on it faithfully following the skill instructions in every session. This is a documentation pattern masquerading as an architecture pattern.

The official plugin turns this into a mechanical guarantee. The Stop hook cannot be argued with or forgotten — it will re-inject the prompt regardless of what the model decides.

### 2.4 Known Limitation: Windows / Git Bash

The plugin has a documented Windows issue: an undocumented `jq` dependency and the bash command may resolve to WSL bash rather than Git Bash, causing the hook to fail silently. The fix is to ensure Git Bash resolves to `Git/bin/bash.exe` (not `Git/usr/bin/bash.exe`) and that `jq` is installed. This is worth resolving before relying on the plugin for autonomous runs.

---

## 3. Current Architecture Problems

### 3.1 Subagents Cannot Spawn Subagents

**Status: RESOLVED** — The main thread now spawns both the orchestrator and worker agents directly. The orchestrator no longer attempts to spawn subagents.

The current execution chain is:

```
/next-loop  (main thread)
  └─ spawns loop-orchestrator  (subagent)          ✓ works
       └─ tries to spawn coding-worker  (subagent)  ✗ silently ignored
```

Claude Code explicitly prohibits subagents from spawning their own subagents. The loop-orchestrator, being itself a subagent, cannot call the Agent tool successfully. All work ends up executed by the orchestrator directly — as Sonnet — without the intended task isolation or context management. This failure is **silent**: no error is thrown, making it easy to miss.

### 3.2 Skill Loading Is a Loading Guarantee, Not a Compliance Guarantee

The `skills:` frontmatter field in agent definitions injects skill content into a subagent's context at spawn time — this part works. However, a subagent in a fresh context window may treat injected skill content as reference material rather than operative instructions unless explicitly told otherwise. A single injection mechanism with no fallback is insufficient for critical pipeline knowledge.

### 3.3 No Structured Handoff Protocol

**Status: RESOLVED** — Implemented via `loop-ready.json` / `loop-complete.json` filesystem state bus with structured `handoff_summary` (done/failed/needed) in both the loop file frontmatter and the completion JSON.

When a coding worker completes a loop, there is no enforced structure for communicating back to the orchestrator what happened. The orchestrator receives whatever text the subagent produced last. Consequently:

- The main agent cannot reliably parse success vs partial success vs failure
- The stop/go decision for the next loop is based on unstructured text interpretation
- Retry logic has no structured basis for what to retry
- The `handoff_summary` field exists in the loop schema but is populated inconsistently

### 3.4 The Ralph Loop Methodology Is Described, Not Enforced

As established in section 2, the `ralph-loop-planner` skill teaches the orchestrator what a ralph loop is — it does not drive one. The mechanical iteration, retry-on-failure, and completion promise behaviour that the skill describes is simply not present.

---

## 4. Recommended Architecture

### 4.1 Install and Integrate the Ralph Loop Plugin

The first and most impactful change is installing the official plugin:

```bash
/plugin install ralph-wiggum@claude-plugins-official
```

Once installed, the mechanic is available as `/ralph-loop:ralph-loop`. The integration sits alongside the existing `/next-loop` command as a second mode of operation:

| Mode | Command | Use case |
|---|---|---|
| Interactive, loop-by-loop | `/next-loop` | Normal development — review between loops, human in the loop |
| Autonomous, unattended | `/ralph-loop:ralph-loop` with task and completion promise | Overnight runs, batch mechanical tasks, clear success criteria |

The `/next-loop` command should also incorporate the **completion promise mechanic** in its own logic, giving interactive sessions the same iteration guarantees without requiring fully autonomous mode.

### 4.2 Flatten the Execution Chain

**Status: IMPLEMENTED** — `/next-loop` acts as the main thread orchestrator, spawning both agents directly in sequence.

Move all orchestration logic into the main thread. The `/next-loop` and `/next-phase` commands should themselves act as the orchestrator — reading skills, managing state, and spawning coding workers directly.

```
Before:
/next-loop (main thread)
  └─ spawns loop-orchestrator (subagent) → cannot spawn workers

After:
/next-loop (main thread IS the orchestrator)
  └─ spawns coding-worker (subagent)  ✓ works correctly
```

The `loop-orchestrator` agent is retained but repurposed as a **top-level agent for unattended autonomous runs**, not as a subagent. It should be launched directly with `claude --agent loop-orchestrator`, never spawned by `/next-loop`.

### 4.3 Dual-Injection Skill Loading (Belt and Braces)

**Status: PARTIALLY ADDRESSED** — Frontmatter `skills:` injection works at spawn time; targeted per-todo injection is implemented in the worker protocol. Explicit preflight read instruction could be added for additional robustness.

For the coding-worker subagent, combine both available mechanisms so skill content is guaranteed to be present and acted upon:

**Layer 1 — Frontmatter injection (loaded at spawn):**
```yaml
---
name: coding-worker
skills:
  - relevant-domain-skill   # injected into context at spawn
---
```

**Layer 2 — Explicit preflight read instruction in agent body:**
```markdown
## Mandatory Preflight
Before starting any task, read the skill file path provided in your task brief.
Confirm you have read it before proceeding.
```

**Layer 3 — Orchestrator passes skill path explicitly in the task brief:**

The main orchestrator, informed by `plan-skill-identification`, includes the relevant skill file path in the prompt string passed to the coding-worker. Even if frontmatter injection is the only reliable mechanism, the agent has been explicitly told what to read and where.

### 4.4 Structured Handoff Protocol

**Status: PARTIALLY ADDRESSED** — Structured handoff exists via `handoff_summary` (done/failed/needed) written to loop frontmatter and `loop-complete.json`. Validation logic for `loop-ready.json` has been added to `/next-loop`. Full handoff block validation (absent/malformed detection) to be added.

Every coding-worker must return a structured handoff block as its final output. The orchestrator validates this block before making a stop/go decision. An absent or malformed block is itself a failure state.

**Handoff block format (returned by worker):**
```yaml
## Handoff
status: complete | partial | failed
done:
  - [description of what was accomplished]
failed:
  - [description of what was not completed, or "none"]
needed:
  - [what the next loop needs to know, or "none"]
files_modified:
  - [list of files changed]
acceptance_met: true | false
```

**Orchestrator stop/go decision logic:**

| Handoff State | Orchestrator Action |
|---|---|
| `acceptance_met: true`, `status: complete` | Loop closed. Advance to next loop. Commit checkpoint. |
| `acceptance_met: false`, `status: partial` | Retry loop with failed items injected as prior context. Increment iteration counter. |
| `status: failed` | Escalate. Do not auto-retry. Print handoff and pause for user review. |
| Handoff block absent | Request explicitly before proceeding. Treat as failure if not produced. |

### 4.5 Command-Activated Skill Loading

The slash commands are the most reliable activation point for skill loading because they run in the main thread. Each command must begin with mandatory skill reads before any other action.

**`/next-loop` activation sequence:**
```
1. Read .claude/skills/ralph-loop-planner/SKILL.md
2. Read .claude/skills/plan-todos/SKILL.md
3. Confirm reads complete
4. Act as ralph-orchestrator from this point
```

**`/next-phase` activation sequence:**
```
1. Read .claude/skills/ralph-loop-planner/SKILL.md
2. Read .claude/skills/phase-plan-creator/SKILL.md
3. Read .claude/skills/plan-todos/SKILL.md
4. Read .claude/skills/plan-skill-identification/SKILL.md
5. Confirm reads complete
6. Act as ralph-orchestrator in phase-transition mode
```

The key principle: the command body forces the main agent to ingest the orchestrator methodology before it does anything else. **The agent becomes the orchestrator by reading the skill — it is not spawned as one.**

### 4.6 Ralph Loop Iteration Mechanic in `/next-loop`

**Status: PARTIALLY ADDRESSED** — Basic retry logic exists in the worker protocol (`max_iterations`, `on_max_iterations`). The completion promise mechanic from the ralph-loop plugin is not yet integrated; deferred pending Windows/jq compatibility resolution.

Incorporating the completion promise mechanic from the plugin into the interactive command gives it the same guarantees without requiring autonomous mode:

```
1. Spawn coding-worker with task brief and acceptance criteria
2. Receive and parse handoff block
3. Evaluate acceptance_met against stated criteria
4. If false and iterations < max_iterations (default 3):
     Re-spawn coding-worker with failed items and handoff context as prior context
5. If true or max_iterations reached:
     Close loop, write handoff_summary to frontmatter, commit checkpoint
```

---

## 5. Updated File Structure

```
.claude/
├── commands/
│   ├── next-loop.md          # Main orchestrator. Reads ralph skills, drives
│   │                         # iteration loop, spawns coding-worker, evaluates handoff.
│   ├── next-phase.md         # Phase transition. Reads all planning skills,
│   │                         # evaluates completion, creates next phase plan.
│   └── new-phase.md          # Unchanged — full planning pipeline.
│
├── agents/
│   ├── coding-worker.md      # Pure execution subagent. No pipeline knowledge.
│   │                         # Dual-injection skill loading. Returns structured handoff.
│   └── loop-orchestrator.md  # Top-level autonomous agent. NOT a subagent.
│                             # For unattended runs only. Launch directly.
│
└── skills/
    ├── ralph-loop-planner/   # Orchestrator methodology + handoff protocol +
    │   └── SKILL.md          # iteration mechanic. Read by /next-loop at activation.
    ├── phase-plan-creator/SKILL.md
    ├── plan-todos/SKILL.md
    ├── plan-skill-identification/SKILL.md
    └── plan-subagent-identification/SKILL.md
```

---

## 6. Required Updates to `ralph-loop-planner` SKILL.md

The skill needs three new sections to reflect the redesigned architecture:

### 6.1 The Iteration Mechanic (new section)

A ralph loop is not a single execution pass. It is an iterative cycle with a completion promise. The orchestrator must:

- Spawn a coding-worker with a precise task brief including acceptance criteria
- Receive the structured handoff block
- Evaluate `acceptance_met` against the stated criteria
- If false and `iterations < max_iterations`: re-spawn with the failed items and handoff context injected as prior context
- If true or `max_iterations` reached: close the loop

### 6.2 Coding-Worker Brief Format (new section)

When spawning a coding-worker, the orchestrator passes a complete, self-contained brief. This is the only channel from orchestrator to worker and must contain everything the worker needs:

```markdown
## Task Brief
Task: [one-sentence description]

Acceptance criteria:
  - [specific, verifiable criterion]

Relevant files:
  - [path] (modify | read only)

Skill to read: .claude/skills/[name]/SKILL.md

Prior context (if retry):
  - Failed: [what the last iteration did not complete]
  - Needed: [what was flagged as required]

Return a ## Handoff block as your final output.
```

### 6.3 Handoff Evaluation Rules (new section)

The orchestrator must not proceed to the next loop until it has validated the handoff block:

- All required fields must be present: `status`, `done`, `failed`, `needed`, `files_modified`, `acceptance_met`
- `acceptance_met` must be an explicit boolean, not inferred from prose
- If block is absent: request it explicitly before proceeding
- Write validated `handoff_summary` to loop frontmatter before any other action

---

## 7. Implementation Task List

Ordered by dependency — complete in sequence:

1. **Install ralph-loop plugin** — `/plugin install ralph-wiggum@claude-plugins-official`. Resolve Windows/jq dependency. Verify Stop hook fires correctly in a test session.

2. **Update `/next-loop.md`** — flatten execution chain; add ralph iteration loop with `max_iterations`; add handoff evaluation and stop/go decision logic.

3. **Update `/next-phase.md`** — add mandatory skill read sequence at the top of the command.

4. **Create/update `coding-worker.md`** — add `skills:` frontmatter, mandatory preflight read instruction, and structured handoff output requirement.

5. **Update `ralph-loop-planner` SKILL.md** — add iteration mechanic, task brief format, and handoff evaluation rules as new sections (section 6 above).

6. **Update `loop-orchestrator.md`** — clarify it is a top-level agent, not a subagent. Add the same iteration mechanic for unattended autonomous use.

7. **Verify `handoff_summary` schema** in the ralph-loops template matches the new handoff block format exactly.

---

*Advanced Planning Architecture — Internal Design Document*
