---
phase: 3
title: "Cowork Adapter"
status: passed
gate_verdict_ref: "n/a — pre-gate-review phase"
gate_verdict_note: "Phase 3 predates gate review system; delivered in the initial repository release commit"
anchor_sha: 5ec7168
end_sha: 5ec7168
commit_count: 1
loop_count: 2
created: 2026-06-10T22:40:00Z
---

## Goals met

- platforms/cowork/SKILL.md routing skill created with dispatch table covering all 6 planning intents; zero .claude/ references — commit 5ec7168
- platforms/cowork/agents/orchestrator-prompt.md (self-contained Sonnet prompt with loop-ready.json write contract) created with Cowork-relative paths — commit 5ec7168
- platforms/cowork/agents/worker-prompt.md (targeted skill injection protocol + snapshot checkpoints) created — commit 5ec7168
- platforms/cowork/checkpoint.sh (POSIX sh, save/restore/list subcommands) created and verified executable — commit 5ec7168
- platforms/cowork/README.md with 3-step setup, Agent tool guide, and troubleshooting created — commit 5ec7168

## Deferred

- Cowork adapter gate integration → future phase (Claude Code gate reviewed first)

## Opened

- (none)
