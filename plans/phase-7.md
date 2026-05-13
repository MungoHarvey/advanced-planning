# Phase 7: `/phase-compact` Slash Command — End-to-End

## Objective
Implement `/phase-compact <phase-id>` as a slash command that reads phase plan + gate verdict + history.jsonl + git log, produces a cold artefact and hot manifest entry conforming to the locked schemas, and validates end-to-end against a real completed phase (Phase 6).

## Scope

### Included:
- Extension of `core/state/gate-verdict.schema.json` with two optional fields: `criteria_outcomes` (array) and `phase_title` (string) — per loop 019's extension spec
- Extension of `phase-goals-agent` definition so it populates `criteria_outcomes` and `phase_title` when writing verdicts
- Fix `phase-goals-agent` tool allowlist to include `Write` scoped to `plans/gate-verdicts/`
- New slash command at `platforms/claude-code/commands/phase-compact.md` taking `<phase-id>` as argument
- End-to-end execution against Phase 6 producing `plans/phase-completes/phase-6-complete.md` + hot manifest entry
- Validation against the locked schemas using their checklists
- Pre-emptive: prepare an agent-permission template that Phase 8's `phase-compactor` will use (Write scoped to `plans/phase-completes/` and `PLANS-INDEX.md`)

### Explicitly NOT included:
- Promotion to `phase-compactor` subagent (Phase 8)
- Automatic trigger via `gate_pass` polling (Phase 9)
- `/clear` and reload sequencing (Phase 9)
- `/load-phase-context` retrieval helper (Phase 10)

## Key Deliverables

| Deliverable | Format | Location |
|-------------|--------|----------|
| Extended verdict schema | JSON Schema | `core/state/gate-verdict.schema.json` |
| Updated phase-goals-agent definition | Markdown | `platforms/claude-code/agents/phase-goals-agent.md` |
| `/phase-compact` slash command | Markdown | `platforms/claude-code/commands/phase-compact.md` |
| Phase 6 cold artefact (produced by the command) | Markdown | `plans/phase-completes/phase-6-complete.md` |
| Phase 6 hot manifest entry | YAML in `PLANS-INDEX.md` | `plans/PLANS-INDEX.md` (Compaction Programme block or new section) |
| Agent permission template note | Markdown section | within `platforms/claude-code/agents/phase-goals-agent.md` or new doc |

## Success Criteria

- ✓ `core/state/gate-verdict.schema.json` validates as JSON Schema draft-07 and includes `criteria_outcomes` and `phase_title` as optional fields with the spec from `docs/phase-goals-verdict-audit.md`
- ✓ `phase-goals-agent` definition has `Write` in its tool allowlist scoped to `plans/gate-verdicts/`
- ✓ `phase-goals-agent` definition's prompt instructs it to populate `criteria_outcomes` (one entry per phase success criterion) and `phase_title` (copied from phase plan)
- ✓ `/phase-compact 6` produces `plans/phase-completes/phase-6-complete.md` that passes every item in `docs/phase-complete.schema.md` Validation Checklist
- ✓ `/phase-compact 6` appends or updates a hot manifest entry in `PLANS-INDEX.md` that passes every item in `docs/phase-manifest-entry.schema.md` Validation Checklist (≤8 lines confirmed)
- ✓ Running `/phase-compact 6` is idempotent — running it twice does not duplicate the manifest entry or corrupt the cold artefact
- ✓ The command's behaviour is documented in its own markdown file (inputs, outputs, error modes, exit conditions)

## Dependencies

### Must Complete Before This Phase:
- Phase 6 (LOCKED): schemas at `docs/phase-complete.schema.md` and `docs/phase-manifest-entry.schema.md` are the contract this phase implements against
- Phase 6 worked example at `plans/phase-completes/phase-5-complete.md` — serves as the format reference for the command's output

### Blocked By:
- Nothing

### Optional:
- Reading `core/skills/` for existing slash command patterns

## Skills Required (Broad Categories)

- `slash-command-authoring`: Writing a new `.md` command file with correct frontmatter and step protocol
- `json-schema`: Extending the verdict schema while preserving backward compatibility
- `agent-definition`: Updating `phase-goals-agent`'s tools and prompt
- `verification-before-completion`: Running the validation checklists end-to-end against generated output
- `writing-skills`: Tight prose for the command's documentation

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Verdict schema extension breaks backward compatibility | Low | High | Both new fields are OPTIONAL with safe defaults; `additionalProperties: false` stays on; existing verdicts (none on disk yet) would parse fine |
| Slash command produces output that doesn't match locked schema | Medium | High | Run the schema's Validation Checklist against the output as part of execution success criteria; do not mark loops complete unless validation passes |
| Idempotency violated — second run duplicates manifest entry | Medium | Medium | Command must detect existing entry for the same phase and update-in-place rather than append; include a explicit idempotency check step |
| Anchor SHA inference fallback (when frontmatter is absent) gives wrong commit | Low | Medium | Phase 6 plan was created before `anchor_sha` frontmatter existed — must inference-derive it; cross-check against the SHA recorded in `phase-5-complete.md` for sanity |
| Command bloat — tries to be the compactor agent already | Medium | Medium | Strict scope discipline: this is a one-shot slash command, NOT a generalised compactor. Agent promotion is Phase 8. |

## Assumptions

- `Slash command pattern exists`: `platforms/claude-code/commands/` already has command files for `/run-gate`, `/next-phase` etc. — pattern is established. Validated by listing existing commands.
- `phase-goals-agent definition is editable`: It lives at a known path under `platforms/claude-code/agents/`. Validated during loop 023 (locate it).
- `Phase 6 has enough commits in git to produce a meaningful compaction`: 4 loops × ~2 commits each = ~8 commits, plus the gate-pass commit. Sufficient for testing.
- `History.jsonl has Phase 6 events`: gate_pass event was written during /run-gate. Loop completion events should also be present (or absent, in which case the command handles the inference fallback).

## Notes / Design Decisions

- **Why extend the verdict schema in this phase, not separately:** Loop 019's audit identified the extension as a prerequisite for the compactor to produce well-formed `goals_met` / `deferred` sections without re-judging. Implementing it now means Phase 7's command can consume real extended verdicts from Phase 7 onward.
- **Why Phase 6 is the test target:** It just completed with a real gate-pass and verdict files. Phase 5's worked example was reconstructed retrospectively; Phase 6 is the first phase that can be compacted using the real production path.
- **Why fix `phase-goals-agent`'s Write permission here:** Surfaced during Phase 6 gate review — the agent wrote a valid verdict but the main thread had to persist it. Phase 9's automatic trigger will not have a human to fall back on. Fix now.
- **Why prepare the agent-permission template:** Phase 8 will promote the slash command to an agent. That agent needs Write scoped to `plans/phase-completes/` and `PLANS-INDEX.md`. Documenting the pattern now means Phase 8 just copies it.
- **Idempotency requirement:** The command will eventually be invoked automatically on every `gate_pass`. Running twice (manual retry, automation race) must not corrupt state. Detect-and-update, not blind-append.

## Ralph Loops (4)

| Loop | Name | Type | Key Outputs |
|------|------|------|-------------|
| 023 | Verdict Schema Extension + Agent Fix | Implementation | Extended `gate-verdict.schema.json`; updated `phase-goals-agent` definition with Write permission and new field population instructions |
| 024 | `/phase-compact` Command Implementation | Implementation | `platforms/claude-code/commands/phase-compact.md` with full step protocol, idempotency, and validation |
| 025 | End-to-End Run Against Phase 6 | Validation | `plans/phase-completes/phase-6-complete.md` + manifest entry in `PLANS-INDEX.md`; both validated against locked schemas |
| 026 | Agent Permission Template + Phase 7 Closeout | Documentation | Permission template documented; CLAUDE.md updated; PLANS-INDEX.md reflects Phase 7 complete and Phase 8 ready |
