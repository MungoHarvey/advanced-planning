# OpenCode Advanced Planning Adapter

This adapter brings the Advanced Planning framework to OpenCode. It provides a host-neutral routing skill and OpenCode-specific integration.

## Project Setup

1. Clone the advanced-planning repository to a known location.
2. Run the project installer from the OpenCode project root:

```powershell
# PowerShell
& setup/opencode/install.ps1 -Project <path-to-your-project>
```

This installs:

- The shared routing skill to `.agents/skills/advanced-planning/SKILL.md`
- Approved core planning skills to `.agents/skills/<name>/SKILL.md`
- The Python runtime launcher to `.advanced-plans/bin/ap.py`
- The runtime manifest to `.advanced-plans/runtime.json`

## Global Setup

For use across all projects:

```powershell
# PowerShell
& setup/opencode/install.ps1 -Global
```

This installs the shared skill and runtime to your profile directory (`$env:USERPROFILE/.agents/skills/` and `$env:USERPROFILE/.advanced-plans/`).

## Quick Start

Once installed, use the five planning actions in OpenCode:

| Action | OpenCode Trigger |
|--------|---------------|
| Create phase | `$advanced-planning phase <goal>` |
| Execute loop | `$advanced-planning loop next` |
| Gate review | `$advanced-planning gate current` |
| Resume session | `$advanced-planning resume` |
| Compact artefacts | `$advanced-planning compact current` |

### Example: Create a Phase

```
$advanced-planning phase Build schema validation for state documents
```

This creates `.advanced-plans/phases/phase-N/plan.md` and presents a human review gate. Reply with one of:

```
APPROVE phase-N
REVISE phase-N: <instructions>
STOP phase-N
```

### Example: Execute a Loop

```
$advanced-planning loop next
```

This performs one orchestrator → worker cycle. For auto-chaining through all pending loops, use `loop next --auto` (stage C).

## Shared Skill Behavior

The routing skill (`advanced-planning`) is shared between Codex and OpenCode adapters. When both are installed in one project:

- Both install the **same byte-identical copy** to `.agents/skills/advanced-planning/SKILL.md`
- Installing one after the other checks for divergence
- If the files differ, installation fails with both SHA-256 digests
- If identical, installation reports `shared; unchanged`

This ensures consistent behavior across hosts and prevents silent overwrites.

## Checkpoint Ownership

**OpenCode can commit.** Unlike Codex, OpenCode subagents have full git access and can commit directly from within a linked worktree. The checkpoint flow is:

1. **Opening checkpoint**: The loop receives the current HEAD as context (no empty commit required)
2. **Closing checkpoint**: OpenCode commits approved changes directly within the worktree
3. **Worker**: Stages the paths it changed — never a blanket `git add -A` — and commits them carrying `Agent: worker/opencode` and `Loop: <loop_name>` trailers, so every change is traceable to the agent that made it

For linked git worktrees, OpenCode's native git access means no external controller is required for commit sequencing.

## Failure Modes

### 1. Skill Not Discovered

**Symptom**: OpenCode does not recognize `$advanced-planning` or reports "skill not found".

**Cause**: The skill is not installed or not in a discovered location.

**Fix**:

```powershell
# Reinstall the skill
& setup/opencode/install.ps1 -Project <path-to-your-project>

# Restart the OpenCode session to refresh skill discovery
```

OpenCode discovers skills under `.agents/skills/` from the current directory to the repository root. Ensure the skill exists at `.agents/skills/advanced-planning/SKILL.md`.

### 2. Runtime Source Unreachable

**Symptom**: `python ".advanced-plans/bin/ap.py"` fails with `ModuleNotFoundError` or exit code 3.

**Cause**: The shared Python runtime checkout has been moved, renamed, or deleted.

**Fix**:

```powershell
# Re-run the installer from the checkout's new location
& setup/opencode/install.ps1 -Project <path-to-your-project>
```

The installer writes `.advanced-plans/runtime.json` with the absolute path to the checkout. If the checkout moves, the manifest becomes stale.

### 3. Human Gate Blocking

**Symptom**: Phase planning completes but loop decomposition does not begin.

**Cause**: Awaiting human review response.

**Fix**: Reply with one of the three valid responses:

```
APPROVE phase-N
REVISE phase-N: <instructions>
STOP phase-N
```

The gate blocks until an explicit response is received. This is the designed behavior.

### 4. Access Dialog (Worktree Outside Checkout)

**Symptom**: OpenCode worker settles `blocked` on an "Access external directory" prompt when pointed at a worktree outside its checkout.

**Cause**: OpenCode gates directory access outside its worktree. This is not a trust dialog but an access boundary.

**Fix**:

- Deliver envelope files inline in the `agent prompt` text
- Or write them inside the worktree rather than referencing external paths
- Pre-authorize the directory if using herdr: `herdr-trust.py <worktree> --apply`

## Architecture

```
OpenCode main thread
├── advanced-planning skill (router)
├── Orchestrator subagent (prepares loop)
│   └── Writes loop-ready.json
└── Worker subagent (executes loop)
    ├── Writes loop-complete.json
    └── Commits changes directly (git worktree access)
```

## Constraints

- **State directory**: `.advanced-plans/state/` — never a host-private directory
- **Skills directory**: `.agents/skills/` — shared discovery location
- **Python runtime**: All Python calls go through `.advanced-plans/bin/ap.py`
- **Human gate**: Manual review is the baseline; no automatic approval
- **No Plannotator**: The deprecated review companion is not installed or invoked
- **Worktree access**: OpenCode workers must stay inside their worktree or use inline envelopes

## See Also

- `platforms/shared/agent-skills/advanced-planning/SKILL.md` — The shared routing skill
- `core/agents/orchestrator.md` — Orchestrator role specification
- `core/agents/worker.md` — Worker role specification
- `core/agents/gate-reviewer.md` — Gate reviewer role specification
- `docs/adapting-to-new-platforms.md` — Adapter contract and constraints
