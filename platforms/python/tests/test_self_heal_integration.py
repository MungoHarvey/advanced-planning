"""
Integration test for the Phase 13 self-correcting gate (self-heal) pipeline.

This module drives the remediation flow end-to-end on SYNTHETIC inputs:
  1. Construct a synthetic gate-fail verdict.
  2. Run triage_findings to classify findings into triage buckets.
  3. Simulate the controller decision logic (validate_diff_allowlist, cycle count,
     sentinel check, criteria hash, re-gate verdict coverage).
  4. Assert that a diff touching a NEVER-TOUCH path ESCALATES rather than proceeding.
  5. Assert that happy-path inputs route correctly to a re-gate pass conclusion.

SAFETY GUARANTEE
----------------
This test makes NO real file edits and NO git commits to the working tree.
All file operations use tempfile.TemporaryDirectory() or in-memory fixtures.
Git is never invoked.  The controller predicate helpers are pure functions
(no I/O side effects) and the git-sha / diff inputs are string fixtures.

The test proves the DECISION LOGIC is correct — the same logic encoded in
the /next-phase --auto command.
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure project root is on sys.path regardless of working directory
sys.path.insert(0, str(Path(__file__).parents[3]))

from platforms.python.remediate import triage_findings
from platforms.python.remediation_controller import (
    compute_criteria_hash,
    count_gate_fail_cycles,
    has_allowlisted_source_changes,
    has_sentinel,
    is_path_never_touch,
    validate_criteria_hash,
    validate_diff_allowlist,
    validate_regateverdict_criteria_outcomes,
)


# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

def _gate_fail_verdict(
    phase: str = "phase-14",
    findings: list = None,
    loops_to_revert: list = None,
    criteria_outcomes: list = None,
) -> dict:
    """Construct a minimal schema-compliant gate-fail verdict dict."""
    if findings is None:
        findings = []
    if loops_to_revert is None:
        loops_to_revert = []
    if criteria_outcomes is None:
        criteria_outcomes = []
    return {
        "phase": phase,
        "attempt": 1,
        "timestamp": "2026-06-09T00:00:00Z",
        "agent": "code-review-agent",
        "verdict": "fail",
        "confidence": 85,
        "findings": findings,
        "loops_to_revert": loops_to_revert,
        "failure_notes": ["Synthetic test failure — sandboxed, no real edits"],
        "criteria_outcomes": criteria_outcomes,
    }


def _write_history(tmp_path: Path, events: list) -> Path:
    """Write a history.jsonl with the given events and return its path."""
    history = tmp_path / "history.jsonl"
    lines = "\n".join(json.dumps(e) for e in events)
    history.write_text(lines + "\n", encoding="utf-8")
    return history


def _write_criteria(tmp_path: Path, content: str = None) -> tuple:
    """Write a criteria-frozen.md to tmp_path; return (path, sha256_hex)."""
    if content is None:
        content = (
            "## Success Criteria\n"
            "- criterion A: codex gate proven\n"
            "- criterion B: self-heal proven\n"
        )
    raw = content.encode("utf-8")
    path = tmp_path / "criteria-frozen.md"
    path.write_bytes(raw)
    return path, compute_criteria_hash(raw)


# ---------------------------------------------------------------------------
# TestSyntheticTriageRouting
# ---------------------------------------------------------------------------

class TestSyntheticTriageRouting:
    """
    Verify triage_findings routes a synthetic gate-fail verdict correctly.

    These tests drive the triage step (Step 7-AUTO-c in next-phase.md) with
    synthetic data and confirm each bucket receives the right findings.
    """

    def test_localized_finding_goes_to_localized_bucket(self):
        """Critical finding with an actionable file path -> localized bucket."""
        verdict = _gate_fail_verdict(
            findings=[
                {
                    "severity": "critical",
                    "location": "platforms/python/state_manager.py:42",
                    "description": "Synthetic localized finding for integration test",
                    "evidence": "sandboxed evidence",
                }
            ]
        )
        result = triage_findings(verdict)
        assert len(result["localized"]) == 1
        assert result["structural"] == []
        assert result["unfixable"] == []
        assert result["conflict"] == []

    def test_never_touch_path_in_finding_does_not_suppress_allowlist_check(self):
        """
        A finding whose location is a NEVER-TOUCH path means the 'fix' the controller
        would attempt touches a forbidden file.  The diff-allowlist check must reject
        it and escalate.

        This test verifies the integration between triage_findings (which surfaces the
        finding as localized) and validate_diff_allowlist (which rejects the diff).
        The controller's correct response is ESCALATE, not commit.
        """
        never_touch_path = ".advanced-plans/phases/phase-14/loops.md"
        verdict = _gate_fail_verdict(
            findings=[
                {
                    "severity": "critical",
                    "location": never_touch_path,
                    "description": "Synthetic finding targeting a NEVER-TOUCH path",
                    "evidence": "test evidence",
                }
            ]
        )
        # Triage routes the finding as localized (has an actionable location)
        triage = triage_findings(verdict)
        assert len(triage["localized"]) == 1
        assert triage["localized"][0]["location"] == never_touch_path

        # Simulate: the controller tries to dispatch a fix that modifies the
        # finding's location file.  The diff produced would include the NEVER-TOUCH path.
        simulated_diff = [never_touch_path]
        ok, violations = validate_diff_allowlist(simulated_diff)

        # The allowlist check MUST reject this diff
        assert not ok, (
            "A diff touching a NEVER-TOUCH path must fail the allowlist check."
        )
        assert never_touch_path in violations, (
            f"{never_touch_path!r} must appear in the violations list."
        )

    def test_unfixable_finding_forces_escalation(self):
        """
        A critical finding with no actionable location and no loops_to_revert
        goes to the unfixable bucket, which the controller treats as escalate.
        """
        verdict = _gate_fail_verdict(
            findings=[
                {
                    "severity": "critical",
                    "location": "",
                    "description": "Unfixable design issue — no actionable location",
                    "evidence": "none",
                }
            ],
            loops_to_revert=[],
        )
        triage = triage_findings(verdict)
        assert len(triage["unfixable"]) == 1
        # Controller decision: unfixable bucket non-empty -> escalate
        should_escalate = len(triage["unfixable"]) > 0
        assert should_escalate, (
            "Unfixable finding must drive controller escalation."
        )


# ---------------------------------------------------------------------------
# TestDiffAllowlistBreachEscalation  (the heart of the loop-057 requirement)
# ---------------------------------------------------------------------------

class TestDiffAllowlistBreachEscalation:
    """
    The core integration assertion: a diff that breaches the NEVER-TOUCH list
    must ESCALATE rather than proceed to commit/re-gate.

    This mirrors the controller guard at Step 7-AUTO-g in next-phase.md:
        "Run validate_diff_allowlist(changed_paths).  If not ok -> escalate."
    """

    # NEVER-TOUCH paths that a corrupt/gaming remediation might try to edit
    NEVER_TOUCH_PATHS = [
        ".advanced-plans/phases/phase-14/loops.md",
        ".advanced-plans/phases/phase-14/plan.md",
        ".advanced-plans/phases/phase-14/criteria-frozen.md",
        "core/schemas/gate-verdict.schema.json",
        "core/state/gate-verdict.schema.json",
        "core/agents/gate-reviewer.md",
        ".advanced-plans/state/history.jsonl",
        ".advanced-plans/state/loop-ready.json",
        ".advanced-plans/state/loop-complete.json",
        ".advanced-plans/state/gate-review-mode",
    ]

    @pytest.mark.parametrize("forbidden_path", NEVER_TOUCH_PATHS)
    def test_never_touch_path_in_diff_triggers_escalation(self, forbidden_path):
        """Any diff touching a NEVER-TOUCH path must reject and escalate."""
        # Mix in a legitimate source file to confirm the check is not pass-through
        diff = ["platforms/python/remediate.py", forbidden_path]
        ok, violations = validate_diff_allowlist(diff)
        assert not ok, (
            f"Diff touching {forbidden_path!r} must fail allowlist check."
        )
        assert forbidden_path in violations

    def test_allowlist_breach_escalation_no_commit(self):
        """
        End-to-end escalation trace: a synthetic gate-fail remediation produces
        a diff that touches a NEVER-TOUCH path.  The controller must ESCALATE
        and NO commit must be made.

        This test proves the decision path without invoking git.
        The 'commit' flag starts False and must remain False after the controller
        evaluates the diff — simulating the guard that prevents git commit.
        """
        # Synthetic scenario: remediation tried to edit loops.md (gate-gaming attempt)
        simulated_remediation_diff = [
            "platforms/python/remediation_controller.py",      # legit source change
            ".advanced-plans/phases/phase-14/loops.md",        # NEVER-TOUCH violation
        ]

        # Controller Step 7-AUTO-g check
        ok, violations = validate_diff_allowlist(simulated_remediation_diff)

        # Decision: breach -> escalate, no commit
        commit_would_proceed = ok
        escalate = not ok

        assert escalate, (
            "Controller must escalate when diff allowlist is breached; "
            "commit must not proceed."
        )
        assert not commit_would_proceed, (
            "commit_would_proceed must be False when a NEVER-TOUCH violation is found."
        )
        assert ".advanced-plans/phases/phase-14/loops.md" in violations

    def test_clean_diff_allows_regate(self):
        """
        Contrast case: a clean diff (no NEVER-TOUCH paths) passes the allowlist
        check and has real source changes, allowing the re-gate to proceed.
        """
        clean_diff = [
            "platforms/python/remediate.py",
            ".advanced-plans/phases/phase-14/retry-context.json",  # transient, not never-touch
        ]
        ok, violations = validate_diff_allowlist(clean_diff)
        assert ok, f"Clean diff must pass allowlist; violations: {violations}"
        assert has_allowlisted_source_changes(clean_diff), (
            "Clean diff with a real source file must have allowlisted source changes."
        )

    def test_transient_only_diff_escalates_no_change(self):
        """
        A 'fix' that changes ONLY transient files (no real source change) is
        treated as 'no change' and must escalate.

        Note: retry-context.json is the primary transient-but-not-never-touch path.
        history.jsonl, gate-verdict files, loop-ready/complete, and gate-review-mode
        are ALL in both the transient list AND the never-touch list, so they fail
        validate_diff_allowlist before reaching the no-change check.
        """
        # retry-context.json is transient AND NOT never-touch — the only such path.
        # Use two variants (different phase directories) to create a transient-only diff.
        transient_only_diff = [
            ".advanced-plans/phases/phase-14/retry-context.json",
            ".advanced-plans/phases/phase-13/retry-context.json",
        ]
        # Step 1: Allowlist check passes (retry-context.json is NOT never-touch)
        ok, violations = validate_diff_allowlist(transient_only_diff)
        assert ok, (
            "retry-context.json is transient but NOT never-touch; "
            f"allowlist check should pass; violations: {violations}"
        )

        # Step 2: But no-change detection triggers escalation — only transient files changed
        has_real_change = has_allowlisted_source_changes(transient_only_diff)
        assert not has_real_change, (
            "Transient-only diff must fail no-change detection and trigger escalation."
        )


# ---------------------------------------------------------------------------
# TestSentinelBlocksFix
# ---------------------------------------------------------------------------

class TestSentinelBlocksFix:
    """
    Verify the sentinel check (Step 7-AUTO-d): if gate-review-mode sentinel
    exists, the controller must escalate rather than dispatch a fix.

    This is tested with a tmp dir sentinel — no real sentinel is written/read.
    """

    def test_sentinel_present_escalates(self, tmp_path):
        sentinel = tmp_path / "gate-review-mode"
        sentinel.write_text("2026-06-09T00:00:00Z", encoding="utf-8")
        assert has_sentinel(sentinel), "Sentinel file must be detected."
        # Controller decision: if sentinel -> escalate
        should_escalate = has_sentinel(sentinel)
        assert should_escalate, (
            "Controller must escalate (not dispatch fix) when sentinel exists."
        )

    def test_sentinel_absent_allows_fix(self, tmp_path):
        sentinel = tmp_path / "gate-review-mode"
        assert not has_sentinel(sentinel), "Absent sentinel must return False."
        should_escalate = has_sentinel(sentinel)
        assert not should_escalate


# ---------------------------------------------------------------------------
# TestCriteriaHashGuard
# ---------------------------------------------------------------------------

class TestCriteriaHashGuard:
    """
    Verify that a tampered criteria-frozen.md (different content from what was
    hashed at freeze-time) forces escalation.

    Files are written to a tmp dir — no real criteria-frozen.md is touched.
    """

    def test_tampered_criteria_escalates(self, tmp_path):
        """If criteria-frozen.md changes between cycle start and re-gate, escalate."""
        original_raw = b"## Success Criteria\n- criterion A\n- criterion B\n"
        tampered_raw = b"## Success Criteria\n- criterion A\n"  # B removed (gaming)
        original_hash = compute_criteria_hash(original_raw)

        criteria = tmp_path / "criteria-frozen.md"
        criteria.write_bytes(tampered_raw)

        hash_ok = validate_criteria_hash(criteria, original_hash)
        assert not hash_ok, (
            "Tampered criteria-frozen.md must fail hash validation -> escalate."
        )
        should_escalate = not hash_ok
        assert should_escalate

    def test_unchanged_criteria_passes(self, tmp_path):
        crit_path, expected_hash = _write_criteria(tmp_path)
        assert validate_criteria_hash(crit_path, expected_hash)


# ---------------------------------------------------------------------------
# TestCycleBoundEscalation
# ---------------------------------------------------------------------------

class TestCycleBoundEscalation:
    """
    Verify that reaching the 2-cycle bound in history.jsonl forces escalation
    without any attempt to remediate further.

    History is written to a tmp dir — the real repo's history.jsonl is not touched.
    """

    def test_two_gate_fails_triggers_escalation(self, tmp_path):
        history = _write_history(tmp_path, [
            {"event": "gate_fail", "phase": "phase-14"},
            {"event": "gate_fail", "phase": "phase-14"},
        ])
        cycles = count_gate_fail_cycles(history, "phase-14")
        assert cycles == 2
        escalate = cycles >= 2
        assert escalate, "cycles >= 2 must trigger escalation."

    def test_one_gate_fail_below_bound(self, tmp_path):
        history = _write_history(tmp_path, [
            {"event": "gate_fail", "phase": "phase-14"},
        ])
        cycles = count_gate_fail_cycles(history, "phase-14")
        assert cycles == 1
        assert cycles < 2, "Single gate_fail must NOT trigger escalation."

    def test_history_in_sandbox_does_not_touch_real_repo(self, tmp_path):
        """Sanity: the history written above is in tmp_path, not the real repo."""
        real_history = Path(".advanced-plans/state/history.jsonl")
        sandbox_history = _write_history(tmp_path, [
            {"event": "gate_fail", "phase": "phase-14"},
        ])
        # The sandbox history path must not equal the real repo path
        assert not sandbox_history.samefile(real_history) if real_history.exists() else True
        # Count from sandbox only — real history untouched
        cycles = count_gate_fail_cycles(sandbox_history, "phase-14")
        assert cycles == 1


# ---------------------------------------------------------------------------
# TestFullSyntheticRemediationTrace
# ---------------------------------------------------------------------------

class TestFullSyntheticRemediationTrace:
    """
    End-to-end controller trace exercising the allowlist-breach escalation path.

    This is the primary integration test required by loop-057.  It:
    1. Constructs a synthetic gate-fail with a NEVER-TOUCH-path finding.
    2. Runs triage_findings.
    3. Simulates the controller decision logic through all guards.
    4. Asserts the ESCALATE outcome and NO commit.
    5. Leaves the real working tree and git history completely untouched.
    """

    def test_allowlist_breach_full_escalation_trace(self, tmp_path):
        """
        Synthetic gate-fail -> triage -> allowlist breach detected -> ESCALATE.

        next-phase.md step mapping:
            Step 4:           gate_fail appended (mocked in sandbox)
            Step 7-AUTO-a:    cycle count = 1 (below bound)
            Step 7-AUTO-b:    PRE_REMEDIATION_SHA = "synthetic_sha_abc"
            Step 7-AUTO-c:    triage_findings -> localized (NEVER-TOUCH path)
            Step 7-AUTO-d:    sentinel absent -> fix dispatch permitted so far
            Step 7-AUTO-g:    validate_diff_allowlist -> BREACH -> ESCALATE
            Outcome:          escalate=True, commit_proceeded=False
        """
        PHASE = "phase-14"

        # Step 4: Gate fail appended (sandbox history)
        history = _write_history(tmp_path, [
            {"event": "gate_fail", "phase": PHASE},
        ])

        # Step 7-AUTO-a: cycle count
        cycles = count_gate_fail_cycles(history, PHASE)
        assert cycles == 1
        cycle_escalate = cycles >= 2
        assert not cycle_escalate, "One cycle must not trigger bound escalation."

        # Step 7-AUTO-b: record PRE_REMEDIATION_SHA (mocked — no real git)
        PRE_REMEDIATION_SHA = "synthetic_sha_abc123"
        assert PRE_REMEDIATION_SHA  # non-empty

        # Record criteria hash from sandbox criteria file
        crit_path, CRITERIA_HASH = _write_criteria(tmp_path)

        # Step 7-AUTO-c: triage_findings on the synthetic gate-fail
        never_touch_path = ".advanced-plans/phases/phase-14/loops.md"
        verdict = _gate_fail_verdict(
            phase=PHASE,
            findings=[
                {
                    "severity": "critical",
                    "location": never_touch_path,
                    "description": "Synthetic: remediator tried to edit loops.md criterion",
                    "evidence": "sandboxed test",
                }
            ],
        )
        triage = triage_findings(verdict)
        assert len(triage["localized"]) == 1, (
            "Finding with NEVER-TOUCH location must be classified as localized."
        )

        # Step 7-AUTO-d: sentinel check (sandbox sentinel — absent)
        sentinel = tmp_path / "gate-review-mode"
        assert not has_sentinel(sentinel), "Sandbox sentinel must be absent."

        # Step 7-AUTO-g: the remediator tried to fix the finding by editing loops.md
        # Simulate the resulting diff
        simulated_diff = [
            never_touch_path,  # The NEVER-TOUCH violation
        ]
        allowlist_ok, violations = validate_diff_allowlist(simulated_diff)

        # Decision gate: breach -> ESCALATE, no commit
        commit_proceeded = False  # tracks whether we would have committed
        if not allowlist_ok:
            escalate = True
            # Controller would call create_retry_version from PRE_REMEDIATION_SHA
            # and halt — we do NOT call it here (no real file I/O needed)
        else:
            escalate = False
            commit_proceeded = True  # would have committed — must NOT reach this

        # Assertions
        assert escalate, (
            "NEVER-TOUCH breach must set escalate=True; controller halts without commit."
        )
        assert not commit_proceeded, (
            "commit_proceeded must remain False when allowlist is breached."
        )
        assert never_touch_path in violations
        assert allowlist_ok is False

    def test_clean_remediation_proceeds_to_regate(self, tmp_path):
        """
        Contrast: a synthetic gate-fail where the remediation diff is clean
        proceeds through all guards to a re-gate pass.

        This proves the escalation is specific to the allowlist breach, not
        a blanket failure of the controller logic.
        """
        PHASE = "phase-14"
        FROZEN_CRITERIA = ["criterion A: codex gate proven", "criterion B: self-heal proven"]

        # Setup
        history = _write_history(tmp_path, [
            {"event": "gate_fail", "phase": PHASE},
        ])
        crit_path, CRITERIA_HASH = _write_criteria(tmp_path)
        sentinel = tmp_path / "gate-review-mode"

        # Step 7-AUTO-a
        cycles = count_gate_fail_cycles(history, PHASE)
        assert cycles < 2

        # Step 7-AUTO-d
        assert not has_sentinel(sentinel)

        # Step 7-AUTO-g: clean diff
        clean_diff = [
            "platforms/python/remediate.py",
            f".advanced-plans/phases/{PHASE}/retry-context.json",
        ]
        ok, violations = validate_diff_allowlist(clean_diff)
        assert ok, f"Clean diff must pass; violations: {violations}"
        assert has_allowlisted_source_changes(clean_diff)

        # Step 7-AUTO-i: criteria hash unchanged
        assert validate_criteria_hash(crit_path, CRITERIA_HASH)

        # Step 7-AUTO-j: re-gate verdict covers all frozen criteria
        regate_verdict = {
            "verdict": "pass",
            "criteria_outcomes": [
                {"criterion": c, "status": "met", "evidence": "sandbox proof"}
                for c in FROZEN_CRITERIA
            ],
        }
        crit_ok, missing = validate_regateverdict_criteria_outcomes(
            regate_verdict, FROZEN_CRITERIA
        )
        assert crit_ok, f"Re-gate verdict must cover all frozen criteria; missing: {missing}"

        # Outcome: pass
        final = regate_verdict["verdict"]
        assert final == "pass"
        passed_after_remediation = final == "pass" and cycles >= 1
        assert passed_after_remediation

    def test_sandbox_leaves_real_working_tree_untouched(self, tmp_path):
        """
        Meta-test: all file operations in this module use tmp_path.
        The real working tree's critical files are not modified.

        We verify this by checking that key real files still exist at their
        expected paths (they would be missing or empty if we accidentally
        wrote/deleted them).
        """
        real_loops_md = Path(
            "C:/Users/mharvey2/Documents/Coding/advanced-planning"
            "/.advanced-plans/phases/phase-14/loops.md"
        )
        real_state_dir = Path(
            "C:/Users/mharvey2/Documents/Coding/advanced-planning"
            "/.advanced-plans/state"
        )

        # Real loops.md must still exist (we never touched it in these tests)
        assert real_loops_md.exists(), (
            "loops.md was unexpectedly missing — sandbox tests must not modify real files."
        )

        # Real state directory must still exist
        assert real_state_dir.is_dir(), (
            "State directory was unexpectedly missing."
        )

        # The tmp_path files we created must be DIFFERENT from real files
        sandbox_file = tmp_path / "criteria-frozen.md"
        _write_criteria(tmp_path)
        assert sandbox_file.parent == tmp_path, (
            "Sandbox file must be under tmp_path, not the real repo."
        )
