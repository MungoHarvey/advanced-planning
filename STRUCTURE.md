# Repository Structure

Canonical folder layout for the Advanced Planning System. Every file has one home; adapters reference the core, never duplicate it.

```
planning-system/
│
├── README.md                           ← Quick-start, what this is, how to install
├── CONTRIBUTING.md                     ← How to contribute
├── LICENCE                             ← Apache 2.0
├── STRUCTURE.md                        ← This file
│
├── core/                               ← Platform-independent planning logic
│   │
│   ├── schemas/                        ← Formal definitions of every artefact type
│   │   ├── phase-plan.schema.md        ← Phase plan: fields, types, examples
│   │   ├── ralph-loop.schema.md        ← Ralph loop: frontmatter + markdown body
│   │   ├── todo.schema.md              ← Todo item: canonical field order + rules
│   │   └── handoff.schema.md           ← Handoff summary: 3-field protocol
│   │
│   ├── skills/                         ← 5 planning skills (run by Opus at plan time)
│   │   ├── phase-plan-creator/
│   │   │   ├── SKILL.md               ← Generate structured phase plans
│   │   │   └── references/
│   │   │       └── phase-plan-template.md
│   │   ├── ralph-loop-planner/
│   │   │   ├── SKILL.md               ← Decompose phases into bounded loops
│   │   │   └── references/
│   │   │       └── ralph-loop-template.md
│   │   ├── plan-todos/
│   │   │   ├── SKILL.md               ← Derive atomic todos from loop descriptions
│   │   │   └── references/
│   │   │       └── todo-schema.md      ← (symlink → core/schemas/todo.schema.md)
│   │   ├── plan-skill-identification/
│   │   │   └── SKILL.md               ← Assign skills to todos
│   │   └── plan-subagent-identification/
│   │       └── SKILL.md               ← Assign agents to todos
│   │
│   ├── agents/                         ← Abstract agent role definitions
│   │   ├── orchestrator.md             ← Prepares loops, assigns skills/agents
│   │   └── worker.md                   ← Executes loops, includes skill injection protocol
│   │
│   └── state/                          ← Filesystem state bus protocol
│       ├── README.md                   ← Protocol specification
│       ├── loop-ready.schema.json      ← JSON Schema for loop-ready.json
│       └── loop-complete.schema.json   ← JSON Schema for loop-complete.json
│
├── platforms/                           ← Platform-specific wrappers
│   │
│   ├── claude-code/                    ← Claude Code CLI integration
│   │   ├── README.md                   ← Install + usage for Claude Code
│   │   ├── install.sh                  ← Copies/symlinks into .claude/
│   │   ├── commands/                   ← Slash commands
│   │   │   ├── new-phase.md            ← /new-phase [description]
│   │   │   ├── new-loop.md             ← /new-loop [phase-N]
│   │   │   ├── next-loop.md            ← /next-loop (two-agent pattern)
│   │   │   ├── loop-status.md          ← /loop-status
│   │   │   ├── check-execution.md      ← /check-execution (6-area diagnostic)
│   │   │   └── model-check.md          ← /model-check
│   │   ├── agents/                     ← Agent files with Claude Code frontmatter
│   │   │   ├── ralph-orchestrator.md   ← Sonnet: prepare loops
│   │   │   ├── ralph-loop-worker.md    ← Haiku: execute loops
│   │   │   └── analysis-worker.md      ← Haiku: computational tasks
│   │   ├── settings.json               ← Permissions + hooks
│   │   └── claude-md-template.md       ← ## Planning State section template
│   │
│   ├── cowork/                         ← Cowork desktop integration
│   │   ├── README.md                   ← Setup for Cowork users
│   │   ├── SKILL.md                    ← Routing skill (entry point)
│   │   ├── agents/                     ← Agent prompts for Cowork Agent tool
│   │   │   ├── orchestrator-prompt.md
│   │   │   └── worker-prompt.md
│   │   └── checkpoint.sh               ← File-based snapshot utility
│   │
│   └── generic/                        ← Framework-agnostic Python API
│       ├── README.md
│       ├── __init__.py
│       ├── state_manager.py            ← Filesystem state bus implementation
│       ├── plan_io.py                  ← Plan file reading/writing
│       ├── handoff.py                  ← Handoff injection utility
│       ├── tests/
│       │   ├── test_state_manager.py
│       │   ├── test_plan_io.py
│       │   └── test_handoff.py
│       └── examples/
│           ├── langgraph/
│           ├── crewai/
│           └── autogen/
│
├── docs/                               ← Documentation suite
│   ├── architecture.md                 ← System design, tier model, why it works
│   ├── getting-started.md              ← Install → first loop in 10 minutes
│   ├── concepts.md                     ← Phase plans, ralph loops, handoffs, outcomes
│   ├── model-tier-strategy.md          ← Opus/Sonnet/Haiku assignment rationale
│   ├── skill-injection.md              ← Per-todo skill loading protocol
│   ├── decisions.md                    ← Architectural decisions log (from DECISIONS.md)
│   └── adapting-to-new-platforms.md    ← How to write a new adapter
│
├── examples/                           ← Worked examples with real plan files
│   ├── multi-phase-project/            ← Worked example of a multi-phase programme
│   │   ├── README.md
│   │   └── plans/                      ← Sample plan files
│   └── planning-system-restructure/    ← This repo's own plans (dogfood example)
│       ├── README.md
│       └── plans/                      ← These phase plans and ralph loops
│
└── plans/                              ← Active plans for THIS project's development
    ├── PLANS-INDEX.md                  ← Master tracker: all phases, loops, status
    ├── master-plan.md                  ← Programme overview
    ├── phase-1.md                      ← Core Architecture Design
    ├── phase-1-ralph-loops.md          ← Loops 001–004
    ├── phase-2.md                      ← Claude Code Adapter
    ├── phase-2-ralph-loops.md          ← Loops 005–007
    ├── phase-3.md                      ← Cowork Adapter
    ├── phase-3-ralph-loops.md          ← Loops 008–009
    ├── phase-4.md                      ← Generic + Release
    └── phase-4-ralph-loops.md          ← Loops 010–012
```

---

## Naming Conventions

| Artefact | Pattern | Example |
|----------|---------|---------|
| Phase plan | `phase-{N}.md` | `phase-1.md` |
| Ralph loops (single file) | `phase-{N}-ralph-loops.md` | `phase-1-ralph-loops.md` |
| Ralph loops (individual) | `ralph-loop-{NNN}.md` | `ralph-loop-001.md` |
| Plans index | `PLANS-INDEX.md` | Always at `plans/PLANS-INDEX.md` |
| Master plan | `master-plan.md` | One per programme |
| State files | `loop-ready.json`, `loop-complete.json` | In `.claude/state/` at runtime |
| Execution log | `execution.log` | In `.claude/logs/` at runtime |

## Runtime Directory (created by adapters, not in repo)

```
.claude/                                ← Created in target project by install.sh
├── CLAUDE.md                           ← Project conventions + ## Planning State
├── plans/                              ← Phase plans + ralph loops (runtime)
├── skills/                             ← Symlinks → core/skills/
├── commands/                           ← Copied from adapter
├── agents/                             ← Copied from adapter
├── settings.json                       ← Copied from adapter
├── state/                              ← Filesystem state bus (runtime)
│   ├── loop-ready.json
│   ├── loop-complete.json
│   └── history.jsonl                   ← Append-only audit log
├── logs/
│   └── execution.log
└── snapshots/                          ← File-based checkpoints (Cowork adapter)
    └── {ISO-timestamp}/
```
