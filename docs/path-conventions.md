# Path Conventions

**File:** `docs/path-conventions.md`
**Purpose:** Canonical reference for every directory path used by the advanced-planning
framework - both in the source repository and in an installed target project.

**Design authority:** `.advanced-plans/specs/2026-05-20-phase-11-friction-remediation-design.md`
(scope item S7).

---

## Hard Rules (non-negotiable)

1. Source-repo paths and installed-project paths are distinct namespaces. Never conflate them.
2. The planning data home is `.advanced-plans/` in the target project. It is portable across
   agentic platforms and must never be renamed or moved.
3. Claude Code runtime adapters (commands, skills, agents, schemas) live under `.claude/` in
   the target project. They are NOT the data home.
4. Deprecated tokens listed below MUST NOT appear in new code, commands, or agent definitions.
   Existing occurrences must be rewritten on encounter.
5. **Host-neutrality under `core/`:** Files under `core/` must contain no host-specific
   directories, tool names, or permission syntax. The CI path audit enforces this.
   See §7.3 below.

---

## Source Repository Layout

The source repository for the framework itself:

```
advanced-planning/
|
|-- core/                          <- Platform-agnostic definitions
|   |-- skills/                    <- Canonical skill SKILL.md files
|   |   `-- <skill-name>/SKILL.md
|   |-- schemas/                   <- Artefact schema documents
|   |-- agents/                    <- Abstract agent role definitions
|   `-- state/                     <- JSON schemas for state bus files
|
|-- platforms/
|   |-- claude-code/               <- Claude Code adapter
|   |   |-- commands/              <- Slash command .md files
|   |   |-- agents/                <- Runtime agent definitions (mirrors core/agents/)
|   |   `-- hooks/                 <- PreToolUse / PreCompact hook scripts
|   |-- python/                    <- Python API
|   |   |-- state_manager.py
|   |   |-- plan_io.py
|   |   |-- handoff.py
|   |   `-- tests/
|   `-- cowork/                    <- Cowork routing adapter
|
|-- setup/
|   `-- claude-code/               <- Install scripts for Claude Code adapter
|       |-- install.sh
|       `-- install.ps1
|
|-- docs/                          <- Human-readable framework docs
|-- .advanced-plans/               <- Planning data home (used when developing the framework)
`-- .github/workflows/             <- CI
```

---

## Installed-Project Runtime Layout

What `install.sh` / `install.ps1` creates in the target project:

```
<target-project>/
|
|-- .claude/                       <- Claude Code runtime adapters (NOT data)
|   |-- commands/                  <- Copied from platforms/claude-code/commands/
|   |-- skills/                    <- Copied/symlinked from core/skills/
|   |-- agents/                    <- Copied from platforms/claude-code/agents/
|   |-- schemas/                   <- Copied from core/schemas/
|   `-- settings.json              <- Hook configuration
|
`-- .advanced-plans/               <- Planning data home (portable across platforms)
    |-- PLANNING.md                <- Live programme dashboard (YAML frontmatter)
    |-- README.md                  <- Directory map + conventions
    |-- PLANS-INDEX.md             <- Index of all phases and loops
    |-- phases/
    |   `-- phase-N/               <- plan.md + loops.md (+ complete.md at gate pass)
    |-- specs/                     <- Design specs (brainstorming output)
    |-- gate-verdicts/             <- Verdict JSON written by gate agents during /run-gate
    |-- state/                     <- Filesystem state bus
    |   |-- loop-ready.json        <- Written by orchestrator; read by worker
    |   |-- loop-complete.json     <- Written by worker; read by main thread
    |   |-- history.jsonl          <- Append-only audit log
    |   `-- archive/               <- Cross-phase stale state (auto-archived by orchestrator)
    `-- logs/
        `-- execution.log          <- Session hook output
```

---

## Where to Find What

| Artefact | Canonical path |
|----------|---------------|
| State bus (live loop files) | `.advanced-plans/state/` |
| Gate verdicts | `.advanced-plans/gate-verdicts/` |
| Audit history | `.advanced-plans/state/history.jsonl` |
| Phase plans + loops | `.advanced-plans/phases/phase-N/` |
| Design specs | `.advanced-plans/specs/` |
| Slash commands (source) | `platforms/claude-code/commands/` |
| Slash commands (runtime) | `.claude/commands/` |
| Skills (source) | `core/skills/<skill-name>/SKILL.md` |
| Skills (runtime) | `.claude/skills/<skill-name>/SKILL.md` |
| Agent definitions (source) | `core/agents/` and `platforms/claude-code/agents/` |
| Agent definitions (runtime) | `.claude/agents/` |
| Schema documents (source) | `core/schemas/` |
| Schema documents (runtime) | `.claude/schemas/` |
| Execution log | `.advanced-plans/logs/execution.log` |
| Python API | `platforms/python/` |
| Install scripts | `setup/claude-code/` |

---

## Deprecated Path Tokens

These tokens MUST NOT appear in new code, command files, agent definitions, or skills.
Rewrite any occurrence on encounter.

| Deprecated token | Reason deprecated | Canonical replacement |
|-----------------|------------------|-----------------------|
| `plans/` (top-level) | Pre-restructure location; replaced during Phase 9 migration | `.advanced-plans/` |
| `.claude/plans/` | Confused the Claude Code runtime dir with the data home | `.advanced-plans/` |
| `.claude/state/` | State bus was moved out of .claude/ to avoid platform coupling | `.advanced-plans/state/` |
| `plans/gate-verdicts/` | Old path for verdict JSON files | `.advanced-plans/gate-verdicts/` |
| `/new-loop` | Command renamed to avoid ambiguity | `/decompose-phase` |

### Identifying a stale reference

A reference is stale if it directs an agent or script to store or read planning data from
any of the deprecated paths above. It is NOT stale if it:

- Describes the `.claude/` directory as a runtime Adapter location (commands, skills, agents)
- Appears inside an install script explaining what it creates at `.claude/`
- Appears in a test fixture or migration artefact that explicitly labels it as legacy

---

## Host-Neutrality Rule (§7.3)

**Design authority:** Design §7.3 (envelope loop-003-hostneutral).

**Rule:** Core files must contain no `.claude/`, `.cursor/`, `.opencode/`, `.codex/`,
`.agents/`, `.gemini/`, Claude-only tool names, or host-specific permission syntax.

**Rationale:** The `core/` directory contains platform-agnostic definitions that must remain
usable by any agentic host (Claude Code, Cursor, Codex, opencode, etc.). Host-specific
references couple the core to a single platform and violate the architecture.

**Enforcement:** The CI path audit (`platforms/python/path_audit.py`) scans `core/agents/`
and `core/skills/` for host-specific tokens. Violations cause CI failure.

**What is forbidden under `core/`:**

| Category | Tokens | Example |
|----------|--------|---------|
| Host directories | `.claude/`, `.cursor/`, `.opencode/`, `.codex/`, `.agents/`, `.gemini/` | "Load from `.claude/skills/`" |
| Host-only tool names | `Claude Code`, `Cowork`, `Agent tool`, `Task tool`, `TodoWrite`, `subagent_type` | "Use the Agent tool" |
| Host permission syntax | `settings.json`, `opencode.json`, `.cursor/rules` | "permissions.defaultMode" |

**Note:** Bare English words like "task" and "agent" in ordinary prose are NOT flagged.
The rule matches qualified tool names and identifiers (e.g., "Agent tool", "TodoWrite"),
not common nouns. A markdown table header "| Loop | Task | Todos |" is legitimate.

**What is allowed under `platforms/claude-code/`:**

The same tokens are **legitimate** under `platforms/claude-code/` because that directory
contains Claude Code-specific adapter code. For example:

- `platforms/claude-code/commands/install.md` may document installing to `.claude/commands/`
- `platforms/claude-code/agents/orchestrator.md` may reference the Agent tool

The path audit enforces this boundary: `core/` = host-neutral, `platforms/` = host-specific
allowed.

---

## Validation Checklist

- [ ] `docs/path-conventions.md` exists at the repository root under `docs/`
- [ ] CLAUDE.md `## Architecture > ### Runtime Directory` section links to this file
- [ ] No file under `platforms/`, `core/`, or `docs/` contains any deprecated token listed above
  in a data-directive context (state bus reads/writes, file creation, path references)
- [ ] `.advanced-plans/state/` is used (not `.claude/state/`) wherever state bus files are referenced
- [ ] `.advanced-plans/gate-verdicts/` is used (not `plans/gate-verdicts/`) for verdict JSON
- [ ] `/decompose-phase` is used (not `/new-loop`) in all command references
