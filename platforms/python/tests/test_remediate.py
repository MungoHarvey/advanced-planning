"""Unit tests for platforms.python.remediate — triage_findings."""

import sys
from pathlib import Path

import pytest

# Adjust path so we can import from the package root when running from repo root
sys.path.insert(0, str(Path(__file__).parents[3]))

from platforms.python.remediate import triage_findings


# ── Helpers ────────────────────────────────────────────────────────────────────

def _verdict(**kwargs):
    """Build a minimal verdict dict. Only keys provided are set."""
    base = {
        "phase": "phase-13",
        "attempt": 1,
        "timestamp": "2026-06-08T00:00:00Z",
        "agent": "code-review-agent",
        "verdict": "fail",
        "confidence": 80,
        "findings": [],
        "loops_to_revert": [],
        "failure_notes": [],
    }
    base.update(kwargs)
    return base


# ── TestTriageFindings ─────────────────────────────────────────────────────────

class TestTriageFindings:

    # ── Return shape ──────────────────────────────────────────────────────────

    def test_returns_dict_with_required_keys(self):
        result = triage_findings(_verdict())
        assert set(result.keys()) == {"structural", "localized", "unfixable", "conflict"}

    def test_empty_verdict_returns_empty_lists(self):
        result = triage_findings(_verdict())
        assert result["structural"] == []
        assert result["localized"] == []
        assert result["unfixable"] == []
        assert result["conflict"] == []

    # ── Structural route ──────────────────────────────────────────────────────

    def test_loops_to_revert_go_to_structural(self):
        verdict = _verdict(loops_to_revert=["ralph-loop-001", "ralph-loop-002"])
        result = triage_findings(verdict)
        assert result["structural"] == ["ralph-loop-001", "ralph-loop-002"]

    def test_structural_does_not_include_empty_loops_to_revert(self):
        result = triage_findings(_verdict(loops_to_revert=[]))
        assert result["structural"] == []

    # ── Localized route ───────────────────────────────────────────────────────

    def test_critical_finding_with_location_goes_to_localized(self):
        findings = [
            {
                "severity": "critical",
                "location": "platforms/python/versioning.py:42",
                "description": "inject_failure_context still writes frontmatter",
                "evidence": "line 176 writes to loops.md",
            }
        ]
        result = triage_findings(_verdict(findings=findings))
        assert len(result["localized"]) == 1
        assert result["localized"][0]["location"] == "platforms/python/versioning.py:42"

    def test_localized_preserves_finding_fields(self):
        findings = [
            {
                "severity": "critical",
                "location": "core/state/gate-failure-context.schema.json",
                "description": "Schema description is wrong",
                "evidence": "description says frontmatter",
            }
        ]
        result = triage_findings(_verdict(findings=findings))
        f = result["localized"][0]
        assert f["severity"] == "critical"
        assert f["description"] == "Schema description is wrong"
        assert f["evidence"] == "description says frontmatter"

    def test_multiple_critical_with_locations_all_localized(self):
        findings = [
            {
                "severity": "critical",
                "location": "platforms/python/foo.py:10",
                "description": "Issue A",
                "evidence": "ev A",
            },
            {
                "severity": "critical",
                "location": "platforms/python/bar.py:20",
                "description": "Issue B",
                "evidence": "ev B",
            },
        ]
        result = triage_findings(_verdict(findings=findings))
        assert len(result["localized"]) == 2

    # ── Unfixable route ───────────────────────────────────────────────────────

    def test_critical_finding_without_location_goes_to_unfixable(self):
        findings = [
            {
                "severity": "critical",
                "location": "",
                "description": "Design flaw with no actionable location",
                "evidence": "see overall architecture",
            }
        ]
        result = triage_findings(_verdict(findings=findings))
        assert len(result["unfixable"]) == 1

    def test_critical_finding_in_reverted_loop_not_unfixable(self):
        """A critical finding whose location is covered by a loops_to_revert entry
        is NOT routed to unfixable — the structural re-run will address it."""
        findings = [
            {
                "severity": "critical",
                "location": "",
                "description": "Issue in ralph-loop-001 output",
                "evidence": "loop output invalid",
            }
        ]
        # The loop is in loops_to_revert, so the critical no-location finding
        # that references it is covered by structural — not unfixable.
        # NOTE: per spec, a critical finding with no actionable location AND not
        # covered by a reverted loop -> unfixable. Here loops_to_revert covers it,
        # so the finding should NOT be in unfixable.
        verdict = _verdict(
            findings=findings,
            loops_to_revert=["ralph-loop-001"],
        )
        result = triage_findings(verdict)
        # structural gets the loop
        assert "ralph-loop-001" in result["structural"]
        # unfixable is empty because loops_to_revert covers the phase
        assert len(result["unfixable"]) == 0

    def test_critical_no_location_no_reverted_loop_is_unfixable(self):
        findings = [
            {
                "severity": "critical",
                "location": "",
                "description": "No actionable location, no reverted loop",
                "evidence": "none",
            }
        ]
        result = triage_findings(_verdict(findings=findings, loops_to_revert=[]))
        assert len(result["unfixable"]) == 1

    # ── Warning/info ignored ──────────────────────────────────────────────────

    def test_warning_finding_ignored(self):
        findings = [
            {
                "severity": "warning",
                "location": "platforms/python/foo.py",
                "description": "Minor style issue",
                "evidence": "line 5",
            }
        ]
        result = triage_findings(_verdict(findings=findings))
        assert result["localized"] == []
        assert result["unfixable"] == []
        assert result["structural"] == []
        assert result["conflict"] == []

    def test_info_finding_ignored(self):
        findings = [
            {
                "severity": "info",
                "location": "README.md",
                "description": "Informational note",
                "evidence": "line 1",
            }
        ]
        result = triage_findings(_verdict(findings=findings))
        assert result["localized"] == []
        assert result["unfixable"] == []
        assert result["structural"] == []
        assert result["conflict"] == []

    def test_mixed_severities_only_critical_routed(self):
        findings = [
            {
                "severity": "critical",
                "location": "platforms/python/foo.py:1",
                "description": "Critical",
                "evidence": "ev",
            },
            {
                "severity": "warning",
                "location": "platforms/python/bar.py:2",
                "description": "Warning",
                "evidence": "ev",
            },
            {
                "severity": "info",
                "location": "docs/readme.md:3",
                "description": "Info",
                "evidence": "ev",
            },
        ]
        result = triage_findings(_verdict(findings=findings))
        assert len(result["localized"]) == 1
        assert result["localized"][0]["description"] == "Critical"

    # ── Multi-agent union ─────────────────────────────────────────────────────

    def test_multi_agent_union_merges_loops_to_revert(self):
        """Passing a list of verdicts unions their loops_to_revert into structural."""
        v1 = _verdict(loops_to_revert=["ralph-loop-001"], findings=[])
        v2 = _verdict(loops_to_revert=["ralph-loop-002"], findings=[])
        result = triage_findings([v1, v2])
        assert set(result["structural"]) == {"ralph-loop-001", "ralph-loop-002"}

    def test_multi_agent_union_deduplicates_loops(self):
        v1 = _verdict(loops_to_revert=["ralph-loop-001"], findings=[])
        v2 = _verdict(loops_to_revert=["ralph-loop-001"], findings=[])
        result = triage_findings([v1, v2])
        assert result["structural"].count("ralph-loop-001") == 1

    def test_multi_agent_union_merges_findings(self):
        f1 = {
            "severity": "critical",
            "location": "platforms/python/a.py:1",
            "description": "Agent 1 finding",
            "evidence": "ev1",
        }
        f2 = {
            "severity": "critical",
            "location": "platforms/python/b.py:2",
            "description": "Agent 2 finding",
            "evidence": "ev2",
        }
        v1 = _verdict(findings=[f1])
        v2 = _verdict(findings=[f2])
        result = triage_findings([v1, v2])
        assert len(result["localized"]) == 2

    # ── Contradictory-location conflict ──────────────────────────────────────

    def test_contradictory_same_location_goes_to_conflict(self):
        """Two critical findings at the same location are contradictory -> conflict."""
        findings = [
            {
                "severity": "critical",
                "location": "platforms/python/foo.py:42",
                "description": "Should use single quotes",
                "evidence": "ev A",
            },
            {
                "severity": "critical",
                "location": "platforms/python/foo.py:42",
                "description": "Should use double quotes",
                "evidence": "ev B",
            },
        ]
        result = triage_findings(_verdict(findings=findings))
        assert len(result["conflict"]) > 0
        # Conflicting findings should NOT also appear in localized
        locations_in_localized = [f["location"] for f in result["localized"]]
        assert "platforms/python/foo.py:42" not in locations_in_localized

    def test_non_contradictory_same_location_unique_findings_not_conflict(self):
        """Same location from same finding is not a conflict."""
        findings = [
            {
                "severity": "critical",
                "location": "platforms/python/foo.py:42",
                "description": "Only one finding here",
                "evidence": "ev",
            }
        ]
        result = triage_findings(_verdict(findings=findings))
        assert result["conflict"] == []
        assert len(result["localized"]) == 1

    def test_multi_agent_contradictory_location_conflict(self):
        """Contradictory findings from two different agents (same location, different
        descriptions) -> conflict."""
        f1 = {
            "severity": "critical",
            "location": "platforms/python/foo.py:10",
            "description": "Add type hints",
            "evidence": "ev1",
        }
        f2 = {
            "severity": "critical",
            "location": "platforms/python/foo.py:10",
            "description": "Remove type hints",
            "evidence": "ev2",
        }
        v1 = _verdict(findings=[f1])
        v2 = _verdict(findings=[f2])
        result = triage_findings([v1, v2])
        assert len(result["conflict"]) > 0
