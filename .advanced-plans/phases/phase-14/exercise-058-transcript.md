# Witnessed self-heal exercise — ralph-loop-058

Run: 2026-06-09T13:46:47Z   worktree=C:/Users/mharvey2/Documents/Coding/ap-ex-058   branch=exercise/phase-058   induced phase=phase-exercise
Purpose: observe the installed self-correcting gate remediate a deliberately-induced,
isolated gate fail and re-gate to pass — entirely inside a discarded git worktree.

Main history.jsonl pre-exercise: 20 lines (must be unchanged at end).

## 1. Throwaway worktree created from HEAD

## 2. Induced gate fail (localized + fixable)
- defect: platforms/python/demo_remediation_target.py now contains a FIXME marker (violates frozen criterion C1)
- criteria frozen; sha256=49ede93700c4e3cf48bc54e7f4c6dadad9544fafd88c70615c74a1345c95004b
- gate_fail event appended (worktree history); cycles counted = 1 (bound = 2)

## 3. Triage (platforms.python.remediate.triage_findings)
```
{"structural": 0, "localized": 1, "unfixable": 0, "conflict": 0}
LOCALIZED_LOC=platforms/python/demo_remediation_target.py:3
```
-> classified as LOCALIZED (actionable location) => a bounded in-place fix is attempted.

## 4. Diff allowlist safety check (validate_diff_allowlist)
```
fix-only diff      -> ok=True violations=[]
+never-touch path  -> ok=False violations=['.advanced-plans/phases/phase-9/plan.md']
```
-> the fix touches only an allowlisted path; a NEVER-TOUCH path would be rejected.

## 5. Bounded fix applied
- platforms/python/demo_remediation_target.py rewritten with the FIXME removed; retry-context.json sidecar written

## 6. Remediation committed; gate_remediation event emitted

## 7. Re-gate
- frozen-criteria hash before=49ede93700c4e3cf48bc54e7f4c6dadad9544fafd88c70615c74a1345c95004b
- frozen-criteria hash after =49ede93700c4e3cf48bc54e7f4c6dadad9544fafd88c70615c74a1345c95004b
- HASH_VERIFIED=True  (criteria were NOT altered during remediation)
- criterion C1 now satisfied (no FIXME in target): true
- => gate_pass with passed_after_remediation=true emitted

## 8. Captured event trail (worktree history.jsonl tail)
```json
{"event":"gate_fail","phase":"phase-exercise","attempt":1,"timestamp":"2026-06-09T13:46:47Z","agent":"phase-goals-agent","verdict_file":".advanced-plans/gate-verdicts/phase-exercise-attempt-1-phase-goals-agent.json","loops_to_revert":[]}
{"event":"gate_remediation","phase":"phase-exercise","cycle":1,"timestamp":"2026-06-09T13:46:47Z","structural_count":0,"localized_count":1}
{"event":"gate_pass","phase":"phase-exercise","attempt":2,"timestamp":"2026-06-09T13:46:47Z","agents":["code-review-agent","phase-goals-agent"],"passed_after_remediation":true,"cycles":1,"verdict_files":[]}
```

