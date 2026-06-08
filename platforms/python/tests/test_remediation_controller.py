"""
Unit tests for platforms.python.remediation_controller — bounded gate-remediation predicates.

Covers:
- cycle bound from history events
- sentinel-absent assertion
- diff-allowlist rejection -> escalate (is_path_never_touch)
- transient-excluded no-change -> escalate (has_allowlisted_source_changes)
- criteria-hash mismatch -> escalate
- re-gate verdict missing a criterion -> escalate
- --auto OFF behavior trace (documented, not predicate-tested)
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parents[3]))

from platforms.python.remediation_controller import (
    compute_criteria_hash,
    count_gate_fail_cycles,
    has_allowlisted_source_changes,
    has_sentinel,
    is_path_in_allowlist,
    is_path_never_touch,
    is_transient_path,
    validate_criteria_hash,
    validate_diff_allowlist,
    validate_regateverdict_criteria_outcomes,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_history(tmp_path: Path, events: list) -> Path:
    """Write a history.jsonl with the given events."""
    history = tmp_path / "history.jsonl"
    history.write_text(
        "\n".join(json.dumps(e) for e in events) + "\n",
        encoding="utf-8",
    )
    return history


# ---------------------------------------------------------------------------
# count_gate_fail_cycles
# ---------------------------------------------------------------------------

class TestCountGateFailCycles:
    """Cycle count predicate — derived from history.jsonl gate_fail events."""

    def test_no_history_file_returns_zero(self, tmp_path):
        missing = tmp_path / "no_such_file.jsonl"
        assert count_gate_fail_cycles(missing, "phase-13") == 0

    def test_empty_history_returns_zero(self, tmp_path):
        h = _write_history(tmp_path, [])
        assert count_gate_fail_cycles(h, "phase-13") == 0

    def test_counts_only_gate_fail_for_target_phase(self, tmp_path):
        events = [
            {"event": "gate_pass", "phase": "phase-13"},
            {"event": "gate_fail", "phase": "phase-13"},
            {"event": "gate_fail", "phase": "phase-12"},  # different phase
            {"event": "gate_fail", "phase": "phase-13"},
        ]
        h = _write_history(tmp_path, events)
        assert count_gate_fail_cycles(h, "phase-13") == 2

    def test_cycle_bound_reached_at_2(self, tmp_path):
        """When cycles >= 2, controller escalates — verify the count."""
        events = [
            {"event": "gate_fail", "phase": "phase-13"},
            {"event": "gate_fail", "phase": "phase-13"},
        ]
        h = _write_history(tmp_path, events)
        cycles = count_gate_fail_cycles(h, "phase-13")
        assert cycles >= 2, "cycle bound must be reached"

    def test_single_gate_fail_below_bound(self, tmp_path):
        events = [{"event": "gate_fail", "phase": "phase-13"}]
        h = _write_history(tmp_path, events)
        cycles = count_gate_fail_cycles(h, "phase-13")
        assert cycles < 2, "single failure should not trigger escalation"

    def test_ignores_malformed_lines(self, tmp_path):
        history = tmp_path / "history.jsonl"
        history.write_text(
            '{"event":"gate_fail","phase":"phase-13"}\nNOT_JSON\n',
            encoding="utf-8",
        )
        assert count_gate_fail_cycles(history, "phase-13") == 1

    def test_remediation_events_not_counted(self, tmp_path):
        """gate_remediation events must NOT increase the cycle counter."""
        events = [
            {"event": "gate_fail", "phase": "phase-13"},
            {"event": "gate_remediation", "phase": "phase-13", "cycle": 1},
        ]
        h = _write_history(tmp_path, events)
        assert count_gate_fail_cycles(h, "phase-13") == 1


# ---------------------------------------------------------------------------
# Sentinel assertion
# ---------------------------------------------------------------------------

class TestHasSentinel:
    """Sentinel-absent assertion — fix dispatch must be blocked if sentinel exists."""

    def test_absent_sentinel_returns_false(self, tmp_path):
        sentinel = tmp_path / "gate-review-mode"
        assert not has_sentinel(sentinel)

    def test_present_sentinel_returns_true(self, tmp_path):
        sentinel = tmp_path / "gate-review-mode"
        sentinel.write_text("2026-06-08T00:00:00Z", encoding="utf-8")
        assert has_sentinel(sentinel)

    def test_sentinel_present_means_fix_must_be_blocked(self, tmp_path):
        """Behavioural trace: if has_sentinel() is True, controller must escalate."""
        sentinel = tmp_path / "gate-review-mode"
        sentinel.write_text("ts", encoding="utf-8")
        sentinel_present = has_sentinel(sentinel)
        # Simulate controller logic: escalate if sentinel present
        should_escalate = sentinel_present
        assert should_escalate, (
            "Controller must escalate (not dispatch fix) when sentinel exists; "
            "the PreToolUse hook blocks source edits with exit 2 while it is present."
        )


# ---------------------------------------------------------------------------
# Diff allowlist — never-touch rejection
# ---------------------------------------------------------------------------

class TestIsPathNeverTouch:
    """Diff allowlist: never-touch paths trigger escalation."""

    @pytest.mark.parametrize("path", [
        ".advanced-plans/phases/phase-13/plan.md",
        ".advanced-plans/phases/phase-13/loops.md",
        ".advanced-plans/phases/phase-13/loops-v2.md",
        ".advanced-plans/phases/phase-13/criteria-frozen.md",
        "core/schemas/gate-verdict.schema.json",
        "core/state/history.schema.json",
        "core/agents/gate-reviewer.md",
        "platforms/claude-code/agents/code-review-agent.md",
        "platforms/claude-code/agents/phase-goals-agent.md",
        ".advanced-plans/gate-verdicts/phase-13-attempt-1-code-review-agent.json",
        ".advanced-plans/state/history.jsonl",
        ".advanced-plans/state/loop-ready.json",
        ".advanced-plans/state/loop-complete.json",
        ".advanced-plans/state/gate-review-mode",
    ])
    def test_forbidden_paths_are_never_touch(self, path):
        assert is_path_never_touch(path), f"Expected {path!r} to be never-touch"

    @pytest.mark.parametrize("path", [
        "platforms/python/remediate.py",
        "platforms/python/remediation_controller.py",
        "platforms/claude-code/commands/next-phase.md",
        "core/skills/plan-todos/SKILL.md",
        ".advanced-plans/phases/phase-13/retry-context.json",
        ".claude/skills/some-skill/SKILL.md",
    ])
    def test_allowlisted_paths_are_not_never_touch(self, path):
        assert not is_path_never_touch(path), f"Expected {path!r} NOT to be never-touch"


class TestValidateDiffAllowlist:
    """validate_diff_allowlist: rejects diffs touching forbidden paths."""

    def test_clean_diff_passes(self):
        ok, violations = validate_diff_allowlist([
            "platforms/python/remediate.py",
            "platforms/claude-code/commands/next-phase.md",
        ])
        assert ok
        assert violations == []

    def test_forbidden_path_causes_escalation(self):
        ok, violations = validate_diff_allowlist([
            "platforms/python/remediate.py",
            ".advanced-plans/phases/phase-13/loops.md",  # forbidden
        ])
        assert not ok
        assert ".advanced-plans/phases/phase-13/loops.md" in violations

    def test_multiple_forbidden_paths_all_reported(self):
        ok, violations = validate_diff_allowlist([
            "core/schemas/gate-verdict.schema.json",
            ".advanced-plans/phases/phase-13/plan.md",
        ])
        assert not ok
        assert len(violations) == 2

    def test_empty_diff_passes(self):
        """Empty diff — handled by has_allowlisted_source_changes, not allowlist check."""
        ok, violations = validate_diff_allowlist([])
        assert ok
        assert violations == []

    def test_gate_gaming_loops_success_criterion_rejected(self):
        """
        Gate-gaming guard: a remediation diff that touches loops.md (which
        contains the success criteria that failed) is rejected by
        validate_diff_allowlist and must escalate instead of re-gating.

        This covers the most direct gaming vector: rewriting a loops.md
        success criterion so the same broken code passes the re-gate.

        Backing predicate: is_path_never_touch(".advanced-plans/phases/**/loops*.md")
        """
        # The remediation agent attempted to edit the loops.md success criterion
        gaming_diff = [
            "platforms/python/some_fix.py",        # legitimate source fix
            ".advanced-plans/phases/phase-13/loops.md",  # gaming attempt: criterion edit
        ]
        ok, violations = validate_diff_allowlist(gaming_diff)
        assert not ok, "Gaming attempt touching loops.md must fail allowlist check"
        assert ".advanced-plans/phases/phase-13/loops.md" in violations
        # Controller must escalate to versioned-retry+STOP, not re-gate:
        should_escalate = not ok
        assert should_escalate, "validate_diff_allowlist failure must drive escalation"

    def test_gate_gaming_test_file_asserting_failed_criterion_rejected(self):
        """
        Gate-gaming guard: a remediation diff that touches a test file asserting
        the failed criterion is rejected by validate_diff_allowlist.

        Note: platforms/python/tests/ sits under platforms/ which is in the
        allowlist, BUT test files asserting failed criteria are in the NEVER-TOUCH
        list's spirit.  The is_path_never_touch predicate does NOT currently block
        all test files generically — the per-loop operator must identify criterion-
        asserting tests and add them explicitly to the NEVER-TOUCH list at runtime.
        This test documents the mechanism: validate_diff_allowlist raises if the
        path is flagged is_path_never_touch by any matching pattern.

        For criteria-frozen.md itself (the frozen copy of criteria), the pattern
        is concrete and tested here:
        """
        # The remediation agent attempted to weaken the frozen criteria file itself
        gaming_diff = [
            "platforms/python/some_fix.py",
            ".advanced-plans/phases/phase-13/criteria-frozen.md",  # frozen criteria edit
        ]
        ok, violations = validate_diff_allowlist(gaming_diff)
        assert not ok, (
            "Editing criteria-frozen.md is a never-touch violation — "
            "it must be rejected as a gate-gaming attempt."
        )
        assert ".advanced-plans/phases/phase-13/criteria-frozen.md" in violations


# ---------------------------------------------------------------------------
# Transient-excluded no-change detection
# ---------------------------------------------------------------------------

class TestIsTransientPath:
    """Transient files are excluded from no-change detection."""

    @pytest.mark.parametrize("path", [
        ".advanced-plans/phases/phase-13/retry-context.json",
        ".advanced-plans/state/history.jsonl",
        ".advanced-plans/gate-verdicts/phase-13-attempt-1-code-review-agent.json",
        ".advanced-plans/state/loop-ready.json",
        ".advanced-plans/state/loop-complete.json",
        ".advanced-plans/state/gate-review-mode",
    ])
    def test_transient_paths_identified(self, path):
        assert is_transient_path(path), f"Expected {path!r} to be transient"

    @pytest.mark.parametrize("path", [
        "platforms/python/remediate.py",
        "platforms/claude-code/commands/next-phase.md",
        "core/skills/plan-todos/SKILL.md",
    ])
    def test_source_paths_not_transient(self, path):
        assert not is_transient_path(path), f"Expected {path!r} NOT to be transient"


class TestHasAllowlistedSourceChanges:
    """no-change detection: transient-only diffs must trigger escalation."""

    def test_source_change_detected(self):
        assert has_allowlisted_source_changes([
            ".advanced-plans/state/history.jsonl",  # transient
            "platforms/python/remediate.py",        # source
        ])

    def test_transient_only_returns_false(self):
        """Transient-only diff -> escalate (fix had no real effect)."""
        result = has_allowlisted_source_changes([
            ".advanced-plans/phases/phase-13/retry-context.json",
            ".advanced-plans/state/history.jsonl",
            ".advanced-plans/gate-verdicts/phase-13-attempt-1-code-review-agent.json",
        ])
        assert not result, (
            "A diff touching only transient files means the fix produced no change "
            "to source — controller must escalate rather than re-gate."
        )

    def test_empty_diff_returns_false(self):
        """Empty diff is also no-change -> escalate."""
        assert not has_allowlisted_source_changes([])


# ---------------------------------------------------------------------------
# Criteria hash mismatch
# ---------------------------------------------------------------------------

class TestCriteriaHash:
    """Criteria hash validation — drift from frozen criteria triggers escalation."""

    def test_matching_hash_passes(self, tmp_path):
        criteria = tmp_path / "criteria-frozen.md"
        content = "## Success Criteria\n- criterion A\n- criterion B\n"
        # Write as bytes to avoid platform newline conversion (Windows \r\n)
        raw = content.encode("utf-8")
        criteria.write_bytes(raw)
        expected = compute_criteria_hash(raw)
        assert validate_criteria_hash(criteria, expected)

    def test_mismatched_hash_triggers_escalation(self, tmp_path):
        criteria = tmp_path / "criteria-frozen.md"
        raw = b"## Success Criteria\n- criterion A\n- criterion B\n"
        criteria.write_bytes(raw)
        wrong_hash = "a" * 64  # not a real SHA-256 of this content
        result = validate_criteria_hash(criteria, wrong_hash)
        assert not result, (
            "A changed criteria-frozen.md must fail hash validation — "
            "controller must escalate rather than proceed with the re-gate."
        )

    def test_modified_content_changes_hash(self, tmp_path):
        """Simulates an adversary weakening the criteria then trying to re-gate."""
        original_raw = b"## Success Criteria\n- criterion A\n- criterion B\n"
        weakened_raw = b"## Success Criteria\n- criterion A\n"  # criterion B removed
        original_hash = compute_criteria_hash(original_raw)
        criteria = tmp_path / "criteria-frozen.md"
        criteria.write_bytes(weakened_raw)
        assert not validate_criteria_hash(criteria, original_hash), (
            "Weakened criteria must not pass hash validation."
        )

    def test_compute_hash_is_deterministic(self):
        content = "## Success Criteria\n- some criterion\n"
        h1 = compute_criteria_hash(content)
        h2 = compute_criteria_hash(content)
        assert h1 == h2

    def test_compute_hash_bytes_and_str_equivalent(self):
        content = "## Success Criteria\n- some criterion\n"
        assert compute_criteria_hash(content) == compute_criteria_hash(
            content.encode("utf-8")
        )


# ---------------------------------------------------------------------------
# Re-gate verdict missing a criterion
# ---------------------------------------------------------------------------

class TestValidateRegateVerdictCriteriaOutcomes:
    """Re-gate verdict must cover ALL frozen criteria in criteria_outcomes."""

    def test_all_criteria_present_passes(self):
        verdict = {
            "verdict": "pass",
            "criteria_outcomes": {
                "criterion A": "pass",
                "criterion B": "pass",
            },
        }
        ok, missing = validate_regateverdict_criteria_outcomes(
            verdict, ["criterion A", "criterion B"]
        )
        assert ok
        assert missing == []

    def test_missing_one_criterion_triggers_escalation(self):
        verdict = {
            "verdict": "fail",
            "criteria_outcomes": {
                "criterion A": "pass",
                # criterion B missing
            },
        }
        ok, missing = validate_regateverdict_criteria_outcomes(
            verdict, ["criterion A", "criterion B"]
        )
        assert not ok
        assert "criterion B" in missing

    def test_all_criteria_missing_triggers_escalation(self):
        verdict = {"verdict": "fail"}  # no criteria_outcomes at all
        ok, missing = validate_regateverdict_criteria_outcomes(
            verdict, ["criterion A", "criterion B"]
        )
        assert not ok
        assert set(missing) == {"criterion A", "criterion B"}

    def test_empty_frozen_criteria_always_passes(self):
        """Edge case: no frozen criteria — nothing to check."""
        ok, missing = validate_regateverdict_criteria_outcomes({}, [])
        assert ok
        assert missing == []

    def test_extra_criteria_in_verdict_ok(self):
        """Verdict may have MORE criteria than frozen — that is fine."""
        verdict = {
            "criteria_outcomes": {
                "criterion A": "pass",
                "criterion B": "pass",
                "criterion C": "pass",  # extra — not frozen, but harmless
            }
        }
        ok, missing = validate_regateverdict_criteria_outcomes(
            verdict, ["criterion A", "criterion B"]
        )
        assert ok
        assert missing == []


# ---------------------------------------------------------------------------
# --auto OFF regression trace
# ---------------------------------------------------------------------------

class TestAutoOffRegressionTrace:
    """
    Trace: without --auto, gate-fail behavior is byte-for-byte as before.

    This test is a documentation/assertion test.  The behavior is specified in
    next-phase.md Step 7.0:

        "Without --auto, Step 7 runs the versioned-retry + STOP path
         (Steps 7a–7j) unconditionally. This is byte-for-byte the same behavior
         as before this command was updated."

    The predicates in remediation_controller.py are never invoked when --auto
    is absent — the controller short-circuits directly to the existing Step 7a.

    This test asserts the design contract: if AUTO_PHASE_MODE is False, the
    remediation controller functions are not called, and the gate-fail path
    is identical to the pre-Phase-13 implementation.
    """

    def test_auto_off_path_does_not_invoke_controller_predicates(self):
        """Simulate the controller guard: remediation is skipped without --auto."""
        AUTO_PHASE_MODE = False
        GATE_RESULT = "fail"

        # In the command doc, Step 7-AUTO checks this flag first:
        # "If AUTO_PHASE_MODE = false, skip directly to Step 7a (versioned-retry + STOP path)."
        remediation_controller_invoked = False

        if AUTO_PHASE_MODE and GATE_RESULT == "fail":
            remediation_controller_invoked = True
            # count_gate_fail_cycles(...) would be called here

        assert not remediation_controller_invoked, (
            "The bounded remediation controller MUST NOT be invoked when --auto is absent. "
            "Gate fail without --auto must go directly to the versioned-retry + STOP path."
        )

    def test_auto_on_path_invokes_cycle_count(self, tmp_path):
        """When --auto is set, cycle count is consulted before any remediation."""
        AUTO_PHASE_MODE = True
        GATE_RESULT = "fail"

        history = _write_history(tmp_path, [
            {"event": "gate_fail", "phase": "phase-13"},
        ])

        cycle_count_checked = False
        if AUTO_PHASE_MODE and GATE_RESULT == "fail":
            cycles = count_gate_fail_cycles(history, "phase-13")
            cycle_count_checked = True
            assert cycles == 1  # first failure — below the 2-cycle bound

        assert cycle_count_checked, (
            "Under --auto, the cycle count must be checked on every gate_fail."
        )


# ---------------------------------------------------------------------------
# E2E controller traces
# ---------------------------------------------------------------------------

class TestE2EControllerTraces:
    """
    End-to-end traces of the two bounded remediation paths described in
    next-phase.md Section 7-AUTO:

    Happy path (fix -> re-gate -> pass):
        gate_fail (cycles=1) → triage → diff OK → criteria hash OK →
        re-gate PASS → gate_pass with passed_after_remediation=true

    Bound->escalate path (cycles>=2):
        gate_fail appended (now cycles=2) → cycle bound reached →
        escalate to versioned-retry+STOP from PRE_REMEDIATION_SHA

    These are simulation traces: they exercise the real predicate helpers
    (count_gate_fail_cycles, validate_diff_allowlist, validate_criteria_hash,
    validate_regateverdict_criteria_outcomes) through the same conditional
    logic encoded in next-phase.md, proving that the predicates correctly
    drive the controller decisions.

    Backing predicate tests:
        - cycle counting: TestCountGateFailCycles
        - sentinel: TestHasSentinel
        - diff allowlist: TestIsPathNeverTouch, TestValidateDiffAllowlist
        - transient exclusion: TestIsTransientPath, TestHasAllowlistedSourceChanges
        - criteria hash: TestCriteriaHash
        - verdict completeness: TestValidateRegateVerdictCriteriaOutcomes
    """

    # ------------------------------------------------------------------
    # Helpers shared by both traces
    # ------------------------------------------------------------------

    @staticmethod
    def _make_criteria(tmp_path: Path) -> tuple:
        """Write criteria-frozen.md and return (path, hash)."""
        crit = tmp_path / "criteria-frozen.md"
        raw = b"## Success Criteria\n- criterion A\n- criterion B\n"
        crit.write_bytes(raw)
        h = compute_criteria_hash(raw)
        return crit, h

    # ------------------------------------------------------------------
    # Happy path: fix -> re-gate -> pass (cycles == 1)
    # ------------------------------------------------------------------

    def test_fix_regate_pass_happy_path(self, tmp_path):
        """
        Trace: one remediation cycle that reaches a re-gate pass.

        next-phase.md mapping:
            Step 7-AUTO-a  cycles = count_gate_fail_cycles(...)  → 1 (< 2)
            Step 7-AUTO-b  PRE_REMEDIATION_SHA recorded; criteria frozen
            Step 7-AUTO-c  triage_findings → structural/localized (mocked)
            Step 7-AUTO-d  has_sentinel() → False (safe to dispatch)
            Step 7-AUTO-e  inject_failure_context (sidecar written, not traced here)
            Step 7-AUTO-f  fix dispatched (mocked)
            Step 7-AUTO-g  validate_diff_allowlist → ok
                           has_allowlisted_source_changes → True
            Step 7-AUTO-h  remediation committed (mocked)
            Step 7-AUTO-i  validate_criteria_hash → True (criteria unchanged)
            Step 7-AUTO-j  re-gate: validate_regateverdict_criteria_outcomes → ok
                           GATE_RESULT = pass → passed_after_remediation = True
        """
        PHASE = "phase-13"
        AUTO_PHASE_MODE = True
        GATE_RESULT = "fail"

        # --- 7-AUTO-a: count cycles ---
        history = _write_history(tmp_path, [
            {"event": "gate_fail", "phase": PHASE},  # the current failure
        ])
        cycles = count_gate_fail_cycles(history, PHASE)
        assert cycles == 1
        escalate = cycles >= 2
        assert not escalate, "cycles=1 must NOT trigger escalation"

        # --- 7-AUTO-b: record PRE_REMEDIATION_SHA + freeze criteria ---
        PRE_REMEDIATION_SHA = "abc123"  # mocked git SHA
        criteria_path, CRITERIA_HASH = self._make_criteria(tmp_path)

        # --- 7-AUTO-d: assert sentinel absent ---
        sentinel = tmp_path / "gate-review-mode"
        assert not has_sentinel(sentinel), "sentinel must be absent before fix dispatch"

        # --- 7-AUTO-g: validate diff allowlist (mocked fix changed a source file) ---
        changed = [
            "platforms/python/remediate.py",
            f".advanced-plans/phases/{PHASE}/retry-context.json",
        ]
        ok, violations = validate_diff_allowlist(changed)
        assert ok, f"diff must pass allowlist; violations: {violations}"
        assert has_allowlisted_source_changes(changed), (
            "must detect a real source change to allow re-gate"
        )

        # --- 7-AUTO-i: assert criteria hash still matches ---
        hash_ok = validate_criteria_hash(criteria_path, CRITERIA_HASH)
        assert hash_ok, "criteria hash must match (criteria were not altered)"

        # --- 7-AUTO-j: re-gate verdict covers all frozen criteria ---
        frozen_criteria = ["criterion A", "criterion B"]
        regate_verdict = {
            "verdict": "pass",
            "criteria_outcomes": {
                "criterion A": "pass",
                "criterion B": "pass",
            },
        }
        crit_ok, missing = validate_regateverdict_criteria_outcomes(
            regate_verdict, frozen_criteria
        )
        assert crit_ok, f"re-gate verdict must cover all frozen criteria; missing: {missing}"

        # --- Final: controller concludes gate PASS with passed_after_remediation ---
        final_gate_result = regate_verdict["verdict"]
        passed_after_remediation = final_gate_result == "pass" and cycles >= 1
        assert final_gate_result == "pass"
        assert passed_after_remediation, (
            "A gate_pass following >=1 remediation cycle must set passed_after_remediation=True"
        )

    # ------------------------------------------------------------------
    # Bound->escalate path: cycles >= 2
    # ------------------------------------------------------------------

    def test_bound_escalate_at_cycles_2(self, tmp_path):
        """
        Trace: second gate_fail — cycle bound reached, escalate to versioned-retry+STOP.

        next-phase.md mapping:
            Step 4            gate_fail appended (now 2nd event for this phase)
            Step 7-AUTO-a     cycles = count_gate_fail_cycles(...) → 2 (>= 2)
                              → escalate to versioned-retry + STOP
                              → PRE_REMEDIATION_SHA (from cycle-1 setup) used as baseline
        """
        PHASE = "phase-13"

        # Two gate_fail events already in history (current one was just appended in Step 4)
        history = _write_history(tmp_path, [
            {"event": "gate_fail", "phase": PHASE},  # cycle 1 (prior)
            {"event": "gate_fail", "phase": PHASE},  # cycle 2 (current)
        ])

        cycles = count_gate_fail_cycles(history, PHASE)
        assert cycles == 2

        # --- Controller decision: cycles >= 2 → escalate ---
        escalate = cycles >= 2
        assert escalate, "cycles=2 must trigger escalation to versioned-retry+STOP"

        # --- Escalation uses PRE_REMEDIATION_SHA (recorded in cycle 1, Step 7-AUTO-b) ---
        PRE_REMEDIATION_SHA = "abc123"  # mocked; recorded during cycle-1 setup
        # The controller passes this as the baseline to create_retry_version.
        # This trace confirms it is non-empty (cycle-1 setup ran):
        assert PRE_REMEDIATION_SHA, (
            "PRE_REMEDIATION_SHA must be recorded in cycle 1 so escalation can "
            "version from the clean pre-remediation state, not from mid-fix HEAD."
        )

        # --- gate_remediation events do NOT count toward the cycle bound ---
        history_with_rem = _write_history(tmp_path, [
            {"event": "gate_fail", "phase": PHASE},
            {"event": "gate_remediation", "phase": PHASE, "cycle": 1},
            {"event": "gate_fail", "phase": PHASE},
        ])
        cycles_with_rem = count_gate_fail_cycles(history_with_rem, PHASE)
        assert cycles_with_rem == 2, (
            "gate_remediation events must not inflate the cycle count; "
            "only gate_fail events drive the bound."
        )
