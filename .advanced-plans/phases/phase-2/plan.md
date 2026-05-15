# Phase 2: Claude Code Adapter

## Objective

Build the Claude Code-specific adapter that wraps the core planning system into slash commands, agent files with Claude Code frontmatter, and settings.json hooks — producing a clean, installable package that colleagues can add to any Claude Code project.

---

## Scope

### Included

- **Slash commands** (6): /new-phase, /new-loop, /next-loop, /loop-status, /check-execution, /model-check — wrapping core skills into Claude Code command format
- **Agent files** (3): ralph-orchestrator (Sonnet), ralph-loop-worker (Haiku), analysis-worker (Haiku) — with Claude Code frontmatter (`name`, `description`, `model`, `tools`, `skills`)
- **settings.json**: Permissions whitelist + hooks for session/subagent/tool events logging to execution.log
- **Install script**: `install.sh` supporting three modes: `--project` (copy to .claude/), `--global` (commands to ~/.claude/), and skill-mode (no install, reference via @)
- **CLAUDE.md template**: Planning State section template that projects add to their CLAUDE.md
- **End-to-end verification**: Run a complete cycle (new-phase → new-loop → next-loop) to confirm the adapter works

### Explicitly NOT included

- Cowork-specific integration (Phase 3)
- Python API (Phase 4)
- New features beyond what v7+v8 already demonstrated
- Modifications to the core schemas or skills (those are locked in Phase 1)

---

## Key Deliverables

| Deliverable | Format | Location |
|-------------|--------|----------|
| /new-phase command | Markdown | `platforms/claude-code/commands/new-phase.md` |
| /new-loop command | Markdown | `platforms/claude-code/commands/new-loop.md` |
| /next-loop command | Markdown (v8 two-agent pattern) | `platforms/claude-code/commands/next-loop.md` |
| /loop-status command | Markdown | `platforms/claude-code/commands/loop-status.md` |
| /check-execution command | Markdown (6-area diagnostic) | `platforms/claude-code/commands/check-execution.md` |
| /model-check command | Markdown | `platforms/claude-code/commands/model-check.md` |
| ralph-orchestrator agent | Markdown with frontmatter | `platforms/claude-code/agents/ralph-orchestrator.md` |
| ralph-loop-worker agent | Markdown with frontmatter | `platforms/claude-code/agents/ralph-loop-worker.md` |
| analysis-worker agent | Markdown with frontmatter | `platforms/claude-code/agents/analysis-worker.md` |
| settings.json | JSON | `platforms/claude-code/settings.json` |
| install.sh | Bash | `platforms/claude-code/install.sh` |
| CLAUDE.md template | Markdown | `platforms/claude-code/claude-md-template.md` |
| Adapter README | Markdown | `platforms/claude-code/README.md` |

---

## Success Criteria

- ✓ **Install works**: `install.sh --project /tmp/test-project` creates a complete `.claude/` directory with all commands, skills (symlinked from core), agents, and settings
- ✓ **Commands reference core**: Slash commands import/reference core skill definitions rather than duplicating content
- ✓ **Two-agent pattern functional**: `/next-loop` spawns ralph-orchestrator then ralph-loop-worker sequentially; loop-ready.json and loop-complete.json are written and consumed correctly
- ✓ **Hooks fire**: session start/end, subagent start/stop, and tool use events are logged to `.claude/logs/execution.log`
- ✓ **End-to-end cycle completes**: A test phase plan → ralph loops → execution cycle runs without errors
- ✓ **Colleague-ready**: A developer unfamiliar with the system can install and run `/loop-status` within 5 minutes using only the adapter README

---

## Dependencies

### Must Complete Before

- Phase 1: Core Architecture Design — schemas, skills, agent roles, and state bus must be finalised

### Blocked By

- Nothing external — Claude Code is the existing platform

---

## Skills Required (Broad Categories)

- `skill-creator`: Adapting core skills into Claude Code command format
- `systematic-debugging`: Diagnosing any issues with the two-agent spawn pattern
- `verification-before-completion`: End-to-end testing before declaring the adapter complete

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Subagent-cannot-spawn-subagent constraint breaks the two-agent pattern | Low (already solved in v8 design) | High | The pattern is: main thread spawns orchestrator, waits, then spawns worker. Neither spawns the other. Verified in v8 design. |
| install.sh symlinks break across OS | Medium | Medium | Test on macOS and Linux; fall back to file copy if symlinks fail |
| Hook environment variables still unresolved | Medium | Low | Document the workaround (read agent frontmatter directly); add to /check-execution diagnostic |

---

## Assumptions

- `Claude Code agent frontmatter stable`: The `model:`, `tools:`, `skills:` frontmatter fields work as documented. Validated by: v8 agent definitions use these fields.
- `Slash command format unchanged`: The command markdown format with `---` frontmatter is stable. Validated by: v7 commands currently work.

---

## Notes / Design Decisions

- **Why commands reference core rather than embed**: Avoids content duplication. When a core skill is updated, all adapters benefit without manual sync. The command file's job is to map the platform's invocation pattern to the core skill, not to redefine the skill.
- **Why install.sh supports three modes**: Different teams have different preferences. Some want everything local to one project, some want commands global, some want to try it without installing anything. All three were requested during the original design.
- **Why the deprecated loop-orchestrator is excluded**: The v8 two-agent pattern (ralph-orchestrator + ralph-loop-worker) supersedes it. Including the deprecated agent would confuse colleagues.

---

## Ralph Loops (3)

| Loop | Name | Type | Key Outputs |
|------|------|------|-------------|
| 005 | Commands & Install | Implementation | 6 command files + install.sh + CLAUDE.md template |
| 006 | Agents & Settings | Implementation | 3 agent files + settings.json + adapter README |
| 007 | End-to-End Test | Verification | Test cycle run; issues documented and resolved; adapter declared ready |
