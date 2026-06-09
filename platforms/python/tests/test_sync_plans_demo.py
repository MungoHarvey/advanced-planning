"""
Demonstration test: /sync-plans reconciles a seeded drift in PLANS-INDEX.md.

This test:
1. Seeds deliberate mismatches in a TEMP copy of PLANS-INDEX.md for phase 15:
   - Ralph Loops table: loop 059 and 060 have wrong task_name and wrong status
2. Runs the sync_plans reconciliation logic against the seeded copy using the real
   phase-15 loops.md as the source of truth
3. Asserts all drift is corrected
4. Verifies idempotency (second run produces zero corrections)
5. Leaves the REAL PLANS-INDEX.md untouched at all times
"""
import re
import pathlib
import sys


# ---------------------------------------------------------------------------
# Inline sync-plans reconciliation logic (mirrors /sync-plans command steps)
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter fields from a markdown file."""
    m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    block = m.group(1)
    for line in block.splitlines():
        kv = re.match(r'^(\w+):\s+(.*)', line.strip())
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip('"')
    loops_m = re.search(r'^loops:\s*\[([^\]]*)\]', block, re.MULTILINE)
    if loops_m:
        nums = [x.strip() for x in loops_m.group(1).split(',')]
        fm['loops_list'] = nums
    return fm


def derive_loop_range(loops_list: list) -> str:
    if not loops_list:
        return "—"
    if len(loops_list) == 1:
        return loops_list[0].zfill(3)
    first = loops_list[0].strip().zfill(3)
    last = loops_list[-1].strip().zfill(3)
    return f"{first}–{last}"


def parse_loops_file(text: str) -> list:
    """
    Extract loop metadata from a loops.md file.
    Returns list of dicts: name, task_name, status_derived.
    """
    loops = []
    for block in re.findall(r'```yaml\n---(.*?)```', text, re.DOTALL):
        name_m = re.search(r'^name:\s+"?(ralph-loop-\d+)"?', block, re.MULTILINE)
        task_m = re.search(r'^task_name:\s+"?(.+?)"?\s*$', block, re.MULTILINE)
        done_m = re.search(r'^\s+done:\s+"?(.*?)"?\s*$', block, re.MULTILINE)
        if not name_m:
            continue
        name = name_m.group(1)
        task_name = task_m.group(1).strip() if task_m else ""
        done_val = done_m.group(1).strip() if done_m else ""
        completed_count = len(re.findall(r'status:\s+completed', block))
        pending_count = len(re.findall(r'status:\s+pending', block))
        in_progress_count = len(re.findall(r'status:\s+in_progress', block))
        if done_val or (pending_count == 0 and in_progress_count == 0 and completed_count > 0):
            status = "**complete**"
        elif in_progress_count > 0:
            status = "**in_progress**"
        else:
            status = "**pending**"
        loops.append({"name": name, "task_name": task_name, "status": status})
    return loops


def reconcile_loop_rows(index_text: str, loops: list) -> tuple:
    """
    Update Ralph Loops table rows for each loop.
    Pattern: | NNN | PHASE | task_name | file | status | active | attempt |
    Only updates Name and Status columns; leaves File, Active File, Attempt intact.
    Returns (updated_text, list_of_corrections).
    """
    corrections = []
    for loop in loops:
        loop_num_m = re.search(r'ralph-loop-(\d+)', loop['name'])
        if not loop_num_m:
            continue
        num_str = loop_num_m.group(1)
        num_padded = num_str.zfill(3)
        task_name = loop['task_name']
        status = loop['status']

        # Match exactly the loop row: | NNN | PHASE_N | NAME | FILE | STATUS | ...
        # Use line-anchored pattern to avoid matching inside other content
        row_pattern = re.compile(
            r'^(\| ' + re.escape(num_padded) + r' \| \d+ \| )([^|\n]+?)( \| [^|\n]+? \| )([^|\n]+?)( \| [^|\n]+ \|[^\n]*)$',
            re.MULTILINE
        )
        m = row_pattern.search(index_text)
        if not m:
            corrections.append(f"Loop {num_padded}: row not found (would append new row)")
            continue

        current_task = m.group(2).strip()
        current_status = m.group(4).strip()

        if current_task == task_name and current_status == status:
            continue  # no drift

        new_row = m.group(0)
        if current_task != task_name:
            corrections.append(f'Loop {num_padded}: Name "{current_task}" -> "{task_name}"')
            # Replace group(2) in new_row
            new_row = (
                m.group(1) + task_name + m.group(3) + m.group(4) + m.group(5)
            )
        if current_status != status:
            corrections.append(f'Loop {num_padded}: Status "{current_status}" -> "{status}"')
            # Rebuild with updated status
            new_row = (
                m.group(1) + (task_name if current_task != task_name else m.group(2))
                + m.group(3) + status + m.group(5)
            )

        index_text = index_text[:m.start()] + new_row + index_text[m.end():]

    return index_text, corrections


def run_sync_plans_loops_only(loops_md_path: pathlib.Path,
                               loops_list: list,
                               index_path: pathlib.Path) -> tuple:
    """
    Sync only the Ralph Loops table rows (not Phases table).
    Used when no Phases table row exists for the phase yet.
    Returns (updated_index_text, all_corrections).
    """
    loops_text = loops_md_path.read_text(encoding='utf-8')
    all_loops = parse_loops_file(loops_text)
    # Filter to only loops in the provided list
    loop_names = {f"ralph-loop-{n.strip().zfill(3)}" for n in loops_list}
    phase_loops = [l for l in all_loops if l['name'] in loop_names]

    index_text = index_path.read_text(encoding='utf-8')
    updated, corrections = reconcile_loop_rows(index_text, phase_loops)
    return updated, corrections


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

REPO = pathlib.Path(__file__).parents[3]


def test_sync_plans_corrects_seeded_drift(tmp_path):
    """
    Seed drift in a temp copy of PLANS-INDEX.md for phase-15 loop rows
    and assert /sync-plans logic fixes it. Real PLANS-INDEX.md is untouched.
    """
    real_index = REPO / ".advanced-plans" / "PLANS-INDEX.md"
    loops_md = REPO / ".advanced-plans" / "phases" / "phase-15" / "loops.md"

    assert real_index.exists(), f"PLANS-INDEX.md not found at {real_index}"
    assert loops_md.exists(), f"phase-15/loops.md not found at {loops_md}"

    original_index = real_index.read_text(encoding='utf-8')

    # Seed drift: wrong task name and wrong status for loops 059 and 060
    seeded = original_index
    seeded = seeded.replace(
        '| 059 | 15 | Doc-Hygiene + Wire State-Archiving |',
        '| 059 | 15 | WRONG TASK NAME |'
    )
    seeded = seeded.replace(
        '| 060 | 15 | CI Path-Convention Audit |',
        '| 060 | 15 | WRONG TASK 060 |'
    )
    # Also flip the status of loop 059 from **complete** to **DRIFTED**
    seeded = re.sub(
        r'(\| 059 \| 15 \| WRONG TASK NAME \| `phases/phase-15/loops\.md` \| )\*\*\w+\*\*',
        r'\1**DRIFTED**',
        seeded
    )

    seeded_index = tmp_path / "PLANS-INDEX.md"
    seeded_index.write_text(seeded, encoding='utf-8')

    print("\n--- BEFORE (seeded drift) ---")
    for line in seeded.splitlines():
        if '| 059 |' in line or '| 060 |' in line:
            print(f"  {line}")

    # Run sync_plans logic against seeded copy
    updated_text, corrections = run_sync_plans_loops_only(
        loops_md_path=loops_md,
        loops_list=['059', '060', '061', '062', '063'],
        index_path=seeded_index,
    )

    print("\n--- CORRECTIONS APPLIED ---")
    for c in corrections:
        print(f"  {c}")
    print(f"\nTotal corrections: {len(corrections)}")

    print("\n--- AFTER (reconciled) ---")
    for line in updated_text.splitlines():
        if '| 059 |' in line or '| 060 |' in line:
            print(f"  {line}")

    # Verification (per verification-before-completion skill: assertions before claims)
    assert len(corrections) >= 3, \
        f"Expected >=3 corrections (2 task names + 1 status) but got {len(corrections)}: {corrections}"

    assert 'WRONG TASK NAME' not in updated_text, "Loop 059 task name was not corrected"
    assert 'WRONG TASK 060' not in updated_text, "Loop 060 task name was not corrected"
    assert 'DRIFTED' not in updated_text, "Loop 059 status was not corrected"

    assert 'Doc-Hygiene + Wire State-Archiving' in updated_text, \
        "Loop 059 correct task name not present after sync"
    assert 'CI Path-Convention Audit' in updated_text, \
        "Loop 060 correct task name not present after sync"

    # Critically: real PLANS-INDEX.md must be untouched
    assert real_index.read_text(encoding='utf-8') == original_index, \
        "Real PLANS-INDEX.md was modified — it must remain untouched"

    print("\nAll assertions pass. Real PLANS-INDEX.md confirmed untouched.")


def test_sync_plans_is_idempotent(tmp_path):
    """Running sync_plans twice produces zero corrections on the second run."""
    real_index = REPO / ".advanced-plans" / "PLANS-INDEX.md"
    loops_md = REPO / ".advanced-plans" / "phases" / "phase-15" / "loops.md"

    seeded_index = tmp_path / "PLANS-INDEX.md"
    original = real_index.read_text(encoding='utf-8')
    # Seed one drift
    seeded = original.replace(
        '| 059 | 15 | Doc-Hygiene + Wire State-Archiving |',
        '| 059 | 15 | IDEMPOTENT DRIFT |'
    )
    seeded_index.write_text(seeded, encoding='utf-8')

    # First run — should correct the drift
    updated1, corrections1 = run_sync_plans_loops_only(
        loops_md, ['059', '060', '061', '062', '063'], seeded_index
    )
    seeded_index.write_text(updated1, encoding='utf-8')

    # Second run on corrected content — should produce zero corrections
    updated2, corrections2 = run_sync_plans_loops_only(
        loops_md, ['059', '060', '061', '062', '063'], seeded_index
    )

    assert len(corrections1) >= 1, "First run should have at least one correction"
    assert len(corrections2) == 0, \
        f"Second run (idempotency check) should have zero corrections; got: {corrections2}"
    assert updated1 == updated2, "Idempotency: second run changed the output"

    print(f"\nIdempotency confirmed: first run made {len(corrections1)} corrections; "
          f"second run made 0 corrections.")


def test_sync_plans_no_drift_is_noop():
    """When Ralph Loops rows already match loops.md, sync makes zero corrections."""
    real_index = REPO / ".advanced-plans" / "PLANS-INDEX.md"
    loops_md = REPO / ".advanced-plans" / "phases" / "phase-15" / "loops.md"

    # Run on a COPY of the real index (which may already be in sync)
    # First sync to ensure it's in sync, then run again and check zero corrections
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False,
                                     encoding='utf-8') as f:
        f.write(real_index.read_text(encoding='utf-8'))
        tmp_name = f.name
    try:
        tmp_path = pathlib.Path(tmp_name)
        # First run: bring it in sync
        updated1, _ = run_sync_plans_loops_only(
            loops_md, ['059', '060', '061', '062', '063'], tmp_path
        )
        tmp_path.write_text(updated1, encoding='utf-8')

        # Second run: must be zero corrections
        _, corrections2 = run_sync_plans_loops_only(
            loops_md, ['059', '060', '061', '062', '063'], tmp_path
        )
        assert len(corrections2) == 0, \
            f"Expected zero corrections after sync; got: {corrections2}"
        print("\nNo-drift no-op confirmed.")
    finally:
        os.unlink(tmp_name)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "-s"]))
