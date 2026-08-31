# Test Fixtures

## codex_stdout_sample.txt

**Type**: Real codex CLI stdout (NOT synthesized)

**Produced by**:

```bash
cd <repo-root>
codex exec review --ephemeral -m gpt-5.5 \
  "Emit EXACTLY ONE fenced json block ..." \
  > platforms/python/tests/fixtures/codex_stdout_sample.txt 2>&1
```

**codex-cli version**: 0.124.0 (ChatGPT account auth, gpt-5.5 model)

**Captured**: 2026-06-09 (Phase 14, Loop 056)

**Known behavior**: The codex `exec` and `exec review` subcommands in
non-interactive mode emit the response twice in stdout — once as part of the
conversation transcript and once as the final standalone message. This fixture
therefore contains TWO identical fenced JSON blocks.

**Consequence for extract_and_validate**: `extract_verdict_json` returns
`None` for multiple fenced blocks (the ambiguity guard). Feeding this fixture
to `extract_and_validate` produces `ok=False` — which triggers the
`gate_codex_skipped` degrade path in `run-gate.md`. This is documented as
a friction finding in `docs/tool-friction-log.md` (2026-06-09 entry).

**Tests that use this fixture**:

- `test_codex_gate_live.py::TestCodexRealStdout::test_real_fixture_double_block_triggers_degrade`
  — asserts the double-block behavior returns ok=False (degrade, not happy path)

## codex_stdout_single_block.txt

**Type**: Contract-compliant single-fenced-block stdout (synthesized for happy-path tests)

**Rationale**: The codex-reviewer contract (core/agents/codex-reviewer.md) specifies
that codex should emit exactly ONE fenced JSON block. The real CLI wrapper adds a
second copy (see above). This fixture represents the contract-compliant output that
run-gate expects when the codex-reviewer follows its output contract. It is used
for happy-path testing of `extract_and_validate`.

**Tests that use this fixture**:

- `test_codex_gate_live.py::TestHappyPath::test_single_block_extract_and_validate`
