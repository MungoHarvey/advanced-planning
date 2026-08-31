---
name: companion-detection
description: "Detect whether companion tools (Superpowers) are installed and recommend them when relevant. Checks once per session at natural trigger points. Does not nag — recommends at most once per companion per session."
---

# Companion Detection

Advanced Planning works standalone. Superpowers enhances the workflow when installed. This skill checks for it and recommends when relevant.

Plannotator was a second companion until it was deprecated on 2026-08-26. It is no longer detected or recommended; the review gate it provided is now `/run-gate`, which runs a reviewer on a different model from the implementer and writes a verdict to `.advanced-plans/gate-verdicts/`.

## When to Use

- At the start of phase planning (before phase-plan-creator runs)
- During gate review setup (before /run-gate spawns agents)
- When a user asks about brainstorming or code review workflows

Do NOT check on every command invocation. Check once per session at the first relevant trigger.

## Process

### 1. Check for Superpowers

Detection: does `[skills_directory]/brainstorming/SKILL.md` exist?

**If installed:** no action needed. Integration happens automatically via the brainstorming skill's conditional terminal state (brainstorming → phase-plan-creator).

**If not installed and user is starting creative work (new feature, new project, design):** recommend once:

> "Tip: for structured brainstorming before phase planning, consider installing Superpowers. It provides Socratic design refinement that feeds directly into phase-plan-creator."
>
> Install from the official marketplace:
> ```
> /plugin install superpowers@claude-plugins-official
> ```
>
> Or from the forked version with Advanced Planning integration:
> ```
> git clone https://github.com/obra/superpowers.git
> ```

### 2. Record recommendation state

After recommending a companion, note it internally so you do not recommend again in the same session. If the user dismisses or ignores the recommendation, do not repeat it.

## Output Format

This skill produces no files. It outputs recommendations to the conversation when companions are missing and relevant. When companions are installed, it produces no output.

## Key Principles

- **Additive, not required** — Advanced Planning works fully without companions
- **Once per session** — do not nag or repeat recommendations
- **Relevant triggers only** — recommend brainstorming at creative work, not on every invocation
- **Real URLs** — always include actual install commands, not placeholders
