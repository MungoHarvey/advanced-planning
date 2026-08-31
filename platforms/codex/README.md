# Codex Advanced Planning Adapter

This adapter brings the Advanced Planning framework to OpenAI Codex. It provides a host-neutral routing skill and Codex-specific integration.

## Project Setup

1. Clone the advanced-planning repository to a known location.
2. Run the project installer from the Codex project root:

```powershell
# PowerShell
& setup/codex/install.ps1 -Project <path-to-your-project>
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
& setup/codex/install.ps1 -Global
```

This installs the shared skill and runtime to your profile directory (`$env:USERPROFILE/.agents/skills/` and `$env:USERPROFILE/.advanced-plans/`).

## Quick Start

Once installed, use the five planning actions in Codex:

| Action | Codex Trigger |
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

**Codex cannot commit.** This is a sandbox limit, not a policy choice: Codex subagents inherit the parent sandbox and cannot reach a linked worktree's git metadata, which lives in the parent repo's `.git/worktrees/`. Workers on runtimes that *can* reach git commit their own work under the shared worker contract; Codex instead hands the change to the external controller (Herdr/AAW), which owns git sequencing here:

1. **Opening checkpoint**: External controller records or creates the opening commit before spawning the orchestrator
2. **Closing checkpoint**: Codex returns a structured checkpoint request; the external controller validates the diff, commits it outside the Codex sandbox, and returns the full SHA
3. **Worker**: Receives opening SHA as immutable context; reports the paths it changed instead of staging them, and the controller commits with the same `Agent: worker/codex` and `Loop: <loop_name>` trailers a self-committing worker would have used

For linked git worktrees (the standard pattern), this is the only permitted flow. A clean opening tree uses the existing HEAD SHA; no empty commit is required.

## Failure Modes

### 1. Skill Not Discovered

**Symptom**: Codex does not recognize `$advanced-planning` or reports "skill not found".

**Cause**: The skill is not installed or not in a discovered location.

**Fix**:

```powershell
# Reinstall the skill
& setup/codex/install.ps1 -Project <path-to-your-project>

# Restart the Codex session to refresh skill discovery
```

Codex discovers skills under `.agents/skills/` from the current directory to the repository root. Ensure the skill exists at `.agents/skills/advanced-planning/SKILL.md`.

### 2. Runtime Source Unreachable

**Symptom**: `python ".advanced-plans/bin/ap.py"` fails with `ModuleNotFoundError` or exit code 3.

**Cause**: The shared Python runtime checkout has been moved, renamed, or deleted.

**Fix**:

```powershell
# Re-run the installer from the checkout's new location
& setup/codex/install.ps1 -Project <path-to-your-project>
```

The installer writes `.advanced-plans/runtime.json` with the absolute path to the checkout. If the checkout moves, the manifest becomes stale.

### 3. Delegation Unavailable

**Symptom**: `loop next` fails with "native delegation unavailable" or similar.

**Cause**: Codex subagents are disabled or the external Herdr/AAW integration is not available.

**Fix**:

- Ensure Codex subagents are enabled in your Codex configuration
- For Herdr/AAW fallback, ensure the herdr daemon is running and the integration is configured
- If neither is available, the action is unsupported

### 4. Human Gate Blocking

**Symptom**: Phase planning completes but loop decomposition does not begin.

**Cause**: Awaiting human review response.

**Fix**: Reply with one of the three valid responses:

```
APPROVE phase-N
REVISE phase-N: <instructions>
STOP phase-N
```

The gate blocks until an explicit response is received. This is the designed behavior.

### 5. Checkpoint Unavailable

**Symptom**: Loop execution fails at the checkpoint step.

**Cause**: External controller cannot access the worktree's git metadata.

**Fix**:

- Ensure the worktree is properly linked (`git worktree list` shows it)
- Ensure the external controller (Herdr/AAW) has access to the parent repository
- For shared checkouts, ensure the controller has write access

## Architecture

```
Codex main thread
├── advanced-planning skill (router)
├── Orchestrator subagent (prepares loop)
│   └── Writes loop-ready.json
└── Worker subagent (executes loop)
    └── Writes loop-complete.json

External controller (Herdr/AAW)
├── Records opening checkpoint
├── Validates closing diff
└── Commits approved changes
```

## Constraints

- **State directory**: `.advanced-plans/state/` — never a host-private directory
- **Skills directory**: `.agents/skills/` — shared discovery location
- **Python runtime**: All Python calls go through `.advanced-plans/bin/ap.py`
- **Human gate**: Manual review is the baseline; no automatic approval
- **No Plannotator**: The deprecated review companion is not installed or invoked

## See Also

- `platforms/shared/agent-skills/advanced-planning/SKILL.md` — The shared routing skill
- `core/agents/orchestrator.md` — Orchestrator role specification
- `core/agents/worker.md` — Worker role specification
- `core/agents/gate-reviewer.md` — Gate reviewer role specification
- `docs/adapting-to-new-platforms.md` — Adapter contract and constraints
