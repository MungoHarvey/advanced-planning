# Model Tier Strategy

The v8 planning system assigns AI models by role and frequency of invocation, not by task difficulty alone. This keeps planning costs predictable and ensures expensive model capacity is spent where strategic reasoning is genuinely required.

---

## Default Tier Assignments

| Role | Default Model | Invoked | Per Programme Cost Profile |
|------|--------------|---------|---------------------------|
| Phase plan authoring | Opus | Once per phase | High unit cost, low frequency |
| Loop planning / orchestration | Sonnet | Once per loop | Medium unit cost, medium frequency |
| Progress report synthesis | Sonnet | On demand | Medium unit cost, low frequency |
| Todo execution (worker) | Haiku | Many times per loop | Low unit cost, high frequency |

The model tier economics table: Opus is the most capable but most expensive; Haiku is fast and cheap. The system exploits this by matching model to role based on where reasoning quality matters most.

---

## Why This Allocation Works

**Opus at the strategic tier**: Phase plans require genuine strategic reasoning — scoping a 4-phase programme, identifying dependencies, estimating complexity, writing success criteria that will hold up across months of work. This is a one-time investment per phase. Opus's reasoning quality is worth the cost here.

**Sonnet at the tactical tier**: The orchestrator reads a loop plan, evaluates whether todos need population, invokes planning skills, and writes `loop-ready.json`. This is medium-complexity reasoning — more than Haiku can handle reliably for the population step, but not requiring Opus. Sonnet hits the right point on the cost/quality curve. The `progress-report` skill also runs at Sonnet tier — it reads and synthesises existing artefacts rather than reasoning strategically, so Opus is not justified.

**Haiku at the execution tier**: The worker's job is execution, not reasoning. The skill injected per-todo provides the specialist instructions; Haiku's job is to follow them accurately and efficiently. At high loop counts (a 4-phase programme might have 40–80 todos), the worker cost dominates — Haiku keeps this tractable.

---

## Worked Cost Estimate

For a typical 4-phase programme with 3 loops per phase and 5 todos per loop:

| Model | Invocations | Reason |
|-------|------------|--------|
| Opus | 4 | Phase plan authoring (once per phase) |
| Sonnet | 12 | Orchestrator (once per loop) |
| Haiku | ~60 | Worker todos (avg 5 per loop, 12 loops) |

At approximate 2024 API pricing:
- Opus: ~$0.40–1.20 per invocation → **$2–5 for the programme**
- Sonnet: ~$0.10–0.30 per invocation → **$1–4 for the programme**
- Haiku: ~$0.01–0.05 per invocation → **$0.60–3 for the programme**

Total programme cost: roughly **$4–12** for a well-scoped 4-phase programme.

*These are illustrative estimates. Actual costs depend on context length, output length, and provider pricing at the time of use.*

---

## Overriding Default Tiers

The model assignment is specified in the frontmatter of each skill and agent file. To override:

**In a skill file** (`core/skills/my-skill/SKILL.md`):
```yaml
---
name: my-skill
model: opus   # or sonnet, haiku
---
```

**In an adapter's agent file** (`platforms/claude-code/agents/ralph-loop-worker.md`):
```yaml
---
model: sonnet  # override default haiku for this deployment
tools: [Read, Write, Edit, Glob, Bash, TodoWrite]
---
```

**Verify assignments** with the `/model-check` command (Claude Code) or by reading the `model:` field across all skill/agent frontmatter.

### When to upgrade a tier

- **Haiku → Sonnet for the worker**: If execution quality is consistently poor and the task requires compositional reasoning (not just instruction-following), upgrading the worker to Sonnet can help. Cost increases ~5–10x per todo.
- **Sonnet → Opus for orchestration**: If the orchestrator is failing to populate todos correctly for complex loops, upgrading to Opus for specific phases is reasonable. Cost increases ~3–5x per loop.
- **Keep Opus at strategic tier**: Phase plan authoring is where Opus earns its cost. Downgrading to Sonnet for phase planning typically produces weaker scope definitions and looser success criteria.

### When to downgrade a tier

- **Opus → Sonnet for simple phases**: If a phase is straightforward and well-understood (e.g. "add a README and licence to an existing repo"), Sonnet can author the phase plan acceptably at lower cost.
- **Sonnet → Haiku for orchestration**: Only if todos are pre-populated and the orchestrator's role is purely writing `loop-ready.json` with no population step. Not generally recommended.

---

## The Targeted Skill Injection Factor

Model tier and skill injection interact. A Haiku-tier worker with a well-written skill injected per-todo often produces better output than a Sonnet-tier worker with no skill guidance. The skill sets the quality bar; the model follows it.

This means:

1. **Invest in skills before upgrading models.** If execution quality is poor, check whether the right skill is being injected. A missing or weak skill is usually the culprit.
2. **Haiku + strong skill > Sonnet + no skill** for specialist tasks.
3. **Model upgrades are a last resort** after skill quality is confirmed adequate.

See `docs/concepts.md` → Targeted Skill Injection for the full explanation.
