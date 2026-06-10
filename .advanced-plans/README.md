# .advanced-plans/

This directory is the **data home** for the advanced-planning framework. All programme
artefacts — phase plans, loop files, gate verdicts, design specs, state bus files, and
execution logs — live here. The framework's runtime (commands, agents, skills, schemas,
settings) remains under `.claude/` as a Claude Code platform adapter.

**Live dashboard:** see [PLANNING.md](./PLANNING.md) for the current programme state
(phase, loop, gate status, recommended next action).

---

## Directory Layout

```
.advanced-plans/
├── README.md                    ← this file; static onboarding
├── PLANNING.md                  ← live dashboard (YAML frontmatter + notes)
├── PLANS-INDEX.md               ← programme tracking table (phases + loops)
├── master-plan.md               ← programme overview and objectives
├── phases/
│   ├── phase-1/
│   │   ├── plan.md              ← phase plan (was plans/phase-1.md)
│   │   ├── loops.md             ← ralph loop decomposition
│   │   ├── gate-verdicts/       ← gate review JSON files for this phase
│   │   └── complete.md          ← phase completion artefact (post gate-pass)
│   └── phase-N/
│       └── ...
├── specs/
│   └── YYYY-MM-DD-<topic>-design.md   ← brainstorming and design docs
├── state/
│   ├── loop-ready.json          ← orchestrator → worker handoff
│   ├── loop-complete.json       ← worker → main thread signal
│   └── history.jsonl            ← append-only audit log
└── logs/
    └── execution.log            ← session + agent event log (untracked by git)
```

> **Log rotation note**: `logs/execution.log` is excluded from git (see `.gitignore`)
> because it grows unboundedly during active development. Rotate or truncate freely —
> e.g. `> .advanced-plans/logs/execution.log` to clear, or `cp execution.log
> execution.log.bak && > execution.log` to archive before clearing.
> The file is recreated automatically on the next loop run.

---

## Conventions

### Frontmatter requirements

Every plan file in this directory MUST include YAML frontmatter:

- **`phases/phase-N/plan.md`** — fields: `status`, `phase`, `loops_pending`,
  `loops_complete`, `gate_verdict`
- **`phases/phase-N/loops.md`** — per-loop frontmatter blocks: `name`, `task_name`,
  `handoff_summary`, `todos[]` (fields: `id`/`content`/`skill`/`agent`/`outcome`/
  `status`/`priority`)
- **`PLANNING.md`** — the full 10-field frontmatter schema (see below)
- **`PLANS-INDEX.md`** — pointer field: `dashboard: .advanced-plans/PLANNING.md`

### Path conventions

- Forward slashes in all path references (Windows-safe via pathlib)
- Phase subdirectories are named `phase-N` (no zero-padding for single digits)
- Loop files are named `ralph-loop-NNN` with three-digit zero-padding

### State bus protocol

Three files in `state/` coordinate the two-agent loop cycle:

| File | Writer | Reader | Purpose |
|---|---|---|---|
| `loop-ready.json` | Orchestrator | Worker | Loop preparation handoff |
| `loop-complete.json` | Worker | Main thread | Loop completion signal |
| `history.jsonl` | Main thread | Any | Append-only audit log |

---

## PLANNING.md Frontmatter Schema

```yaml
---
programme: "Programme name"
status: in_progress              # draft | in_progress | complete | blocked
last_updated: YYYY-MM-DD

current_phase: N
current_loop: ralph-loop-NNN     # in flight or next pending
gate_status: not_due             # not_due | pending | passed | failed
next_action: "/next-loop"        # recommended command

active_branches:
  - branch: main
    phase: N
    session: primary

phases:
  complete: [1, 2, ...]
  pending: [N, ...]
  failed: []

state_files:
  ready: .advanced-plans/state/loop-ready.json
  complete: .advanced-plans/state/loop-complete.json
  history: .advanced-plans/state/history.jsonl

notes: |
  Free-text notes about current programme state.
---
```

---

## Workflow Cheat Sheet

### Planning commands

| Command | Purpose |
|---|---|
| `/plan-and-phase` | Explore a new programme; produce a phase plan (Opus) |
| `/new-phase` | Plan the next phase from the current programme state |
| `/decompose-phase` | Decompose a phase plan into ralph loop stubs |

### Execution commands

| Command | Purpose |
|---|---|
| `/next-loop` | Orchestrate + execute the next pending ralph loop |
| `/next-loop --auto` | Chain loops until the phase plan is exhausted |

### Gate and phase transition commands

| Command | Purpose |
|---|---|
| `/run-gate` | Run gate agents to evaluate phase success criteria |
| `/next-phase` | Advance to the next phase (after gate pass) or create a retry version (after gate fail) |
| `/next-phase --auto` | Chain gate review + phase transitions until programme completes |
| `/phase-compact` | Produce a phase-complete.md artefact and update PLANS-INDEX.md |
| `/run-closeout` | Synthesise programme closeout after all phases complete |

### Observation commands

| Command | Purpose |
|---|---|
| `/loop-status` | Current state snapshot: active loop, todo progress, recent log lines |
| `/progress-report` | Historical synthesis: phase completion, loop history, gate outcomes |
| `/check-execution` | Inspect execution.log for errors or stalled agents |
| `/model-check` | Verify agent model assignments across the framework |

---

## Key References

- **Live state:** [PLANNING.md](./PLANNING.md)
- **Programme index:** [PLANS-INDEX.md](./PLANS-INDEX.md)
- **Programme overview:** [master-plan.md](./master-plan.md)
- **Design spec (Phase 9 restructure):** [specs/2026-05-14-advanced-plans-restructure-design.md](./specs/2026-05-14-advanced-plans-restructure-design.md)
- **Framework runtime:** `.claude/` (commands, agents, skills, schemas, settings)
- **CI:** `.github/workflows/ci.yml`
