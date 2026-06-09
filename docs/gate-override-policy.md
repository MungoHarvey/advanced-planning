# Gate-Override Policy

This document defines the conditions under which a **gate-pass-with-dissent** override is
permitted — that is, when the main thread may record `override: true` on a `gate_pass`
event in `history.jsonl` even though one reviewer returned `verdict: fail`.

Cross-reference: see the Gate Review Protocol section of `CLAUDE.md` for the normal
gate-pass and gate-fail flows.

---

## 1. When a Gate-Pass-with-Dissent Override Is Permitted

An override is permitted **only** when all of the following are true:

1. **The failing verdict is a verifiable environment/isolation false-negative.**
   The reviewer's fail is caused by a constraint of its review environment — not by an
   actual deliverable defect. The failing reviewer was structurally unable to verify the
   criterion it raised (e.g. its sandbox blocks `pytest`, or the isolation rule forbids
   it from reading the directory that would have confirmed the criterion).

2. **No deliverable defect has been identified.**
   After examining the specific finding raised by the failing reviewer, the main thread
   (with the help of the two in-house agents) can confirm that the work product is correct
   and the criterion is actually met.

3. **The two in-house agents both returned `verdict: pass`.**
   A minimum of two independent evaluators must agree the criteria are met before an
   override is applied. A single in-house pass is not sufficient.

4. **The failing reviewer's specific findings have been addressed or explained.**
   Each `critical` or `warning` finding must be traced to an environmental cause and
   documented in the `override_reason`.

### Phase 14 Precedent

The first invocation of this policy was at the Phase 14 gate (2026-06-09, `history.jsonl`).
The codex reviewer returned `fail` for two reasons:

- Its read-only sandbox blocked `python`/`pytest`, so it could not run the test criteria
  it was asked to verify.
- The isolation rule (`gate-review-mode` sentinel) forbids codex from reading
  `.advanced-plans/gate-verdicts/`, so it could not self-verify a criterion asking whether
  a `backend: codex` verdict file existed.

Both in-house agents passed with confidence 95/93. The main thread independently re-verified
all criteria (343 tests, AST NONE, LOCKED schema docs unchanged, byte-identity, v0.14.0).
No deliverable defect was identified. The override was recorded with a full `override_reason`
string in the `gate_pass` event.

---

## 2. What Must Be Recorded

When an override is applied, the `gate_pass` event appended to
`.advanced-plans/state/history.jsonl` **must** carry:

```json
{
  "event": "gate_pass",
  "phase": "<phase-id>",
  "attempt": <n>,
  "timestamp": "<ISO-8601>",
  "agents": ["<agent-1>", "<agent-2>"],
  "override": true,
  "override_reason": "<detailed explanation of why the dissenting fail is a false-negative; cite the environmental constraint(s), the criterion affected, the independent verification performed, and confirm no deliverable defect was found>"
}
```

The `override_reason` must be concrete enough that a future reader can audit the decision
without access to the original conversation. Include:

- Which reviewer returned `fail` and why it was structurally unable to verify the criterion.
- What independent verification the main thread performed instead.
- Explicit confirmation that no deliverable defect was identified.

**Schema note:** The override fields (`override`, `override_reason`) live on the
`history.jsonl` `gate_pass` event — not on the per-agent `gate-verdict.schema.json` file.
The gate-verdict schema records what the agent concluded; the history event records the
main-thread decision. No change to `gate-verdict.schema.json` is needed or made (see
Section 5).

---

## 3. Who May Authorise an Override

**Only the human operator on the main thread may authorise an override.**

No agent may self-authorise an override. This includes:

- The orchestrator agent — may not grant an override while preparing a loop.
- The worker agent — may not grant an override while executing todos.
- Any gate reviewer — may not mark its own dissenting verdict as overridable.
- The self-heal / remediation controller — may not treat an overridable fail as a re-gate
  trigger; overrides are reserved for environmental false-negatives, not fixable defects.

The main thread is the only thread with full visibility of the review environment, the
delivered artefacts, and the programme state. Override authority must not be delegated
down the agent hierarchy.

---

## 4. What Is NOT a Valid Override

The following situations do **not** qualify for an override and must result in a gate fail:

- **A genuine deliverable defect.** If a reviewer identifies a concrete defect in a file,
  test, or artefact — regardless of which reviewer raised it — the defect must be fixed and
  the phase re-gated. It may not be overridden.
- **A low-confidence hunch.** An override requires positive confirmation that the failing
  criterion is actually met, verified by an independent means. "Probably fine" is not
  sufficient.
- **Reviewer disagreement on a genuinely ambiguous criterion.** If two evaluators reach
  different verdicts on a criterion where both had full access to the evidence, the
  disagreement must be resolved (by fixing the criterion or re-examining the evidence), not
  overridden.
- **Convenience.** An override is not a shortcut to avoid fixing a failing criterion. The
  bar is environmental impossibility, not inconvenience.

---

## 5. Schema Decision

The override record lives on the `history.jsonl` `gate_pass` event (as shown in Section 2),
not on the per-agent verdict files. The `gate-verdict.schema.json` schema covers what the
reviewing agent concluded; the `gate_pass` event in `history.jsonl` is where the
main-thread decision (including any override) is recorded.

**Decision: no change to `core/state/gate-verdict.schema.json` is needed.** The existing
schema is sufficient. The `override` and `override_reason` fields are free-form extensions
on the history event, which is an append-only JSONL log without a formal JSON Schema
constraint. This was confirmed during Phase 14 and is documented in the CLAUDE.md decision
log.

---

## 6. Checklist for Applying an Override

Before writing the overriding `gate_pass` event, the main thread should be able to check
all boxes:

- [ ] Both in-house agents returned `verdict: pass`.
- [ ] The dissenting reviewer's findings are each traceable to an environmental constraint
      (sandbox, isolation rule, auth limit), not to a deliverable defect.
- [ ] The main thread has independently verified the affected criteria by an alternative
      means (e.g. running the test suite directly, reading the file in question, checking
      git diff).
- [ ] No `critical` finding from any reviewer remains unexplained.
- [ ] `override: true` and a full `override_reason` will be written to the `gate_pass` event.
- [ ] The override will not be applied by an agent on behalf of the main thread.
