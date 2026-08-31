"""Test run contract fixtures against JSON Schema validators.

This module validates fixture documents against the run contract schemas:
- external-task-envelope.schema.json (the envelope sent to workers)
- collected-evidence.schema.json (evidence collected after execution)

Fixtures live in platforms/python/tests/fixtures/run-contracts/
- valid/ — documents that must validate successfully
- invalid/ — documents that must fail for specific, named reasons

Each invalid fixture is paired with a table entry specifying:
- The expected error schema_path(s)
- A repair operation that makes the document valid

The repair test ensures the fixture is honest: if the wrong field is broken,
repairing the named defect leaves other errors and the test fails.
"""

import json
import os
from pathlib import Path

import pytest

from platforms.python.minischema import validate, UnsupportedKeyword


# Paths to schemas (loaded from disk, not copied)
SCHEMA_DIR = Path(__file__).parent.parent.parent.parent / "core" / "state"
ENVELOPE_SCHEMA_PATH = SCHEMA_DIR / "external-task-envelope.schema.json"
EVIDENCE_SCHEMA_PATH = SCHEMA_DIR / "collected-evidence.schema.json"

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "run-contracts"
VALID_DIR = FIXTURE_DIR / "valid"
INVALID_DIR = FIXTURE_DIR / "invalid"


def load_schema(path):
    """Load a JSON Schema from disk."""
    with open(path) as f:
        return json.load(f)


def load_fixture(path):
    """Load a JSON fixture from disk."""
    with open(path) as f:
        return json.load(f)


def apply_repair(instance, op, pointer, value=None):
    """Apply a repair operation to an instance.

    Args:
        instance: The JSON document (dict)
        op: "set" or "delete"
        pointer: JSON pointer string, e.g. "/allowed_paths" or "/policy/independent_review_passed"
        value: The value to set (for "set" op)

    Returns:
        A new dict with the repair applied.
    """
    import copy
    result = copy.deepcopy(instance)

    # Parse pointer (simple implementation for root-level and one-nested paths)
    parts = [p for p in pointer.split("/") if p]

    # Navigate to parent
    current = result
    for part in parts[:-1]:
        if part.isdigit():
            current = current[int(part)]
        else:
            current = current[part]

    key = parts[-1]

    if op == "set":
        if key.isdigit():
            current[int(key)] = value
        else:
            current[key] = value
    elif op == "delete":
        if key.isdigit():
            del current[int(key)]
        else:
            del current[key]

    return result


# Load schemas once
ENVELOPE_SCHEMA = load_schema(ENVELOPE_SCHEMA_PATH)
EVIDENCE_SCHEMA = load_schema(EVIDENCE_SCHEMA_PATH)


# Table of invalid fixtures with expected errors and repairs
INVALID_FIXTURES = [
    {
        "file": "envelope-sync-allowed-paths-missing.json",
        "schema": "envelope",
        "reason": "a sync task with no allowed_paths (rule 3: required for sync/release)",
        "expect": ["/required", "/allOf/1/then/required"],  # Two errors: root required + conditional
        "repair": {"op": "set", "pointer": "/allowed_paths", "value": ["skills/"]},
    },
    {
        "file": "envelope-implementation-shared-isolation.json",
        "schema": "envelope",
        "reason": "implementation task with isolation=shared and no override (rule 2)",
        "expect": ["/allOf/0/then/anyOf"],
        "repair": {"op": "set", "pointer": "/isolation", "value": "worktree"},
    },
    {
        "file": "envelope-credential-field.json",
        "schema": "envelope",
        "reason": "credential-shaped extra field api_key at root (rule 5)",
        "expect": ["/additionalProperties"],
        "repair": {"op": "delete", "pointer": "/api_key"},
    },
    {
        "file": "envelope-base-ref-without-sha.json",
        "schema": "envelope",
        "reason": "base_ref present but base_sha missing entirely (rule 6)",
        "expect": ["/required"],
        "repair": {"op": "set", "pointer": "/base_sha", "value": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
    },
    {
        "file": "evidence-policy-omits-gate.json",
        "schema": "evidence",
        "reason": "policy present but missing independent_review_passed (rule 4)",
        "expect": ["/properties/policy/required"],
        "repair": {"op": "set", "pointer": "/policy/independent_review_passed", "value": False},
    },
    {
        "file": "envelope-release-allowed-paths-empty.json",
        "schema": "envelope",
        "reason": "release task with allowed_paths=[] (rule 3: minItems=1 isolates the conditional)",
        "expect": ["/allOf/1/then/properties/allowed_paths/minItems"],
        "repair": {"op": "set", "pointer": "/allowed_paths", "value": ["release/"]},
    },
    {
        "file": "envelope-base-sha-abbreviated.json",
        "schema": "envelope",
        "reason": "base_sha is only 7 characters, not 40 (rule 6)",
        "expect": ["/properties/base_sha/minLength", "/properties/base_sha/pattern"],
        "repair": {"op": "set", "pointer": "/base_sha", "value": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
    },
    {
        "file": "envelope-forbidden-paths-missing-state.json",
        "schema": "envelope",
        "reason": "forbidden_paths does not contain .advanced-plans/state/ (rule 4)",
        "expect": ["/properties/forbidden_paths/contains"],
        "repair": {"op": "set", "pointer": "/forbidden_paths", "value": [".advanced-plans/state/"]},
    },
    {
        "file": "evidence-status-review-required.json",
        "schema": "evidence",
        "reason": "status=review_required is not in §10 lifecycle; kept as a regression case after the §9.3 example was corrected to 'review'",
        "expect": ["/properties/status/enum"],
        "repair": {"op": "set", "pointer": "/status", "value": "review"},
    },
    {
        "file": "evidence-exit-code-string.json",
        "schema": "evidence",
        "reason": "checks[0].exit_code is string '0' not integer 0",
        "expect": ["/properties/checks/items/properties/exit_code/type"],
        "repair": {"op": "set", "pointer": "/checks/0/exit_code", "value": 0},
    },
    {
        "file": "evidence-credential-in-agent.json",
        "schema": "evidence",
        "reason": "api_key smuggled inside agent object (rule 5, nested)",
        "expect": ["/properties/agent/additionalProperties"],
        "repair": {"op": "delete", "pointer": "/agent/api_key"},
    },
]


# ── Valid fixtures tests ───────────────────────────────────────────────────────

@pytest.fixture(params=[f for f in os.listdir(VALID_DIR) if f.endswith(".json")])
def valid_fixture_file(request):
    """Parametrize over valid fixture files."""
    return request.param


def test_valid_fixtures_validate(valid_fixture_file):
    """Every file in valid/ must produce zero errors."""
    path = VALID_DIR / valid_fixture_file
    instance = load_fixture(path)

    # Determine schema by filename
    if "envelope" in valid_fixture_file:
        schema = ENVELOPE_SCHEMA
    elif "evidence" in valid_fixture_file:
        schema = EVIDENCE_SCHEMA
    else:
        pytest.fail(f"Cannot determine schema for {valid_fixture_file}")

    errors = validate(instance, schema)
    assert errors == [], f"Valid fixture {valid_fixture_file} should have no errors, got: {errors}"


# ── Invalid fixtures tests ─────────────────────────────────────────────────────

@pytest.fixture(params=INVALID_FIXTURES, ids=lambda x: x["file"])
def invalid_fixture_entry(request):
    """Parametrize over invalid fixture table entries."""
    return request.param


def test_invalid_fixture_reports_its_named_error(invalid_fixture_entry):
    """Each invalid fixture must produce the specific error(s) its table entry names."""
    file_name = invalid_fixture_entry["file"]
    schema_name = invalid_fixture_entry["schema"]
    reason = invalid_fixture_entry["reason"]
    expect_paths = invalid_fixture_entry["expect"]

    path = INVALID_DIR / file_name
    instance = load_fixture(path)
    schema = ENVELOPE_SCHEMA if schema_name == "envelope" else EVIDENCE_SCHEMA

    errors = validate(instance, schema)

    # Assert the fixture actually fails
    assert len(errors) > 0, f"Invalid fixture {file_name} ({reason}) should fail validation"

    # Assert each expected path is among the errors
    error_paths = {e.schema_path for e in errors}
    for expect_path in expect_paths:
        assert expect_path in error_paths, (
            f"Fixture {file_name} ({reason}) missing expected error at {expect_path}. "
            f"Got errors at: {error_paths}"
        )


def test_invalid_fixture_is_valid_once_repaired(invalid_fixture_entry):
    """After applying the named repair, each invalid fixture must be fully valid."""
    file_name = invalid_fixture_entry["file"]
    schema_name = invalid_fixture_entry["schema"]
    reason = invalid_fixture_entry["reason"]
    repair = invalid_fixture_entry["repair"]

    path = INVALID_DIR / file_name
    instance = load_fixture(path)
    schema = ENVELOPE_SCHEMA if schema_name == "envelope" else EVIDENCE_SCHEMA

    # Apply repair
    repaired = apply_repair(instance, repair["op"], repair["pointer"], repair.get("value"))

    # Validate repaired instance
    errors = validate(repaired, schema)
    assert errors == [], (
        f"After repairing {repair['op']} {repair['pointer']}, fixture {file_name} ({reason}) "
        f"should be valid. Got errors: {errors}"
    )


# ── Completeness tests ─────────────────────────────────────────────────────────

def test_every_invalid_file_is_in_the_table():
    """Every .json file in invalid/ must have a corresponding table entry."""
    actual_files = {f for f in os.listdir(INVALID_DIR) if f.endswith(".json")}
    table_files = {entry["file"] for entry in INVALID_FIXTURES}

    missing = actual_files - table_files
    assert not missing, (
        f"These invalid/ files have no table entry: {missing}. "
        "Add them to INVALID_FIXTURES or remove them."
    )

    extra = table_files - actual_files
    assert not extra, (
        f"These table entries have no corresponding file: {extra}. "
        "Create the file or remove the entry."
    )


def test_fixture_ids_are_unique_and_named_for_their_reason():
    """Fixture IDs (filenames) should be unique and descriptive."""
    files = [entry["file"] for entry in INVALID_FIXTURES]
    assert len(files) == len(set(files)), "Duplicate fixture filenames found"

    # Each filename should be descriptive (at least 3 parts separated by -)
    for f in files:
        parts = f.replace(".json", "").split("-")
        assert len(parts) >= 3, (
            f"Fixture filename '{f}' is not descriptive enough. "
            "Use format: <schema>-<rule>-<detail>.json"
        )
