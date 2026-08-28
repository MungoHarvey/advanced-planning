"""Unit tests for the zero-dependency minischema validator.

Tests cover:
1. Per-keyword accepting and rejecting cases
2. UnsupportedKeyword for unknown keywords and type values
3. Vacuous properties (properties does not require)
4. Boolean vs integer distinction
5. if/then semantics (if errors not reported)
6. anyOf failure produces exactly one error
7. Real schemas load without UnsupportedKeyword
"""

import json
from pathlib import Path

import pytest

from platforms.python.tests.minischema import (
    UnsupportedKeyword,
    Error,
    validate,
)


# ── Helper ─────────────────────────────────────────────────────────────────────

def _error_keywords(errors: list[Error]) -> set[str]:
    """Return set of keywords that produced errors."""
    return {e.keyword for e in errors}


# ── Type keyword ───────────────────────────────────────────────────────────────

class TestType:
    def test_string_accepts_string(self):
        errors = validate("hello", {"type": "string"})
        assert errors == []

    def test_string_rejects_number(self):
        errors = validate(42, {"type": "string"})
        assert len(errors) == 1
        assert errors[0].keyword == "type"
        assert errors[0].instance_path == ""

    def test_integer_accepts_integer(self):
        errors = validate(42, {"type": "integer"})
        assert errors == []

    def test_integer_rejects_string(self):
        errors = validate("42", {"type": "integer"})
        assert len(errors) == 1
        assert errors[0].keyword == "type"

    def test_boolean_accepts_true(self):
        errors = validate(True, {"type": "boolean"})
        assert errors == []

    def test_boolean_rejects_integer(self):
        """Boolean type must reject 1 (Python bool is subclass of int)."""
        errors = validate(1, {"type": "boolean"})
        assert len(errors) == 1
        assert errors[0].keyword == "type"

    def test_integer_rejects_true(self):
        """Integer type must reject True (Python bool is subclass of int)."""
        errors = validate(True, {"type": "integer"})
        assert len(errors) == 1
        assert errors[0].keyword == "type"

    def test_number_accepts_float(self):
        errors = validate(3.14, {"type": "number"})
        assert errors == []

    def test_number_accepts_integer(self):
        """Per JSON Schema, integer is also a number."""
        errors = validate(42, {"type": "number"})
        assert errors == []

    def test_array_accepts_array(self):
        errors = validate([1, 2, 3], {"type": "array"})
        assert errors == []

    def test_object_accepts_object(self):
        errors = validate({"a": 1}, {"type": "object"})
        assert errors == []

    def test_null_accepts_none(self):
        errors = validate(None, {"type": "null"})
        assert errors == []

    def test_type_array_accepts_any_matching(self):
        errors = validate("hello", {"type": ["string", "number"]})
        assert errors == []

    def test_type_array_rejects_none_matching(self):
        errors = validate(True, {"type": ["string", "number"]})
        assert len(errors) == 1
        assert errors[0].keyword == "type"


# ── Enum keyword ───────────────────────────────────────────────────────────────

class TestEnum:
    def test_enum_accepts_member(self):
        errors = validate("red", {"enum": ["red", "green", "blue"]})
        assert errors == []

    def test_enum_rejects_non_member(self):
        errors = validate("yellow", {"enum": ["red", "green", "blue"]})
        assert len(errors) == 1
        assert errors[0].keyword == "enum"

    def test_enum_with_numbers(self):
        errors = validate(1, {"enum": [1, 2, 3]})
        assert errors == []

    def test_enum_distinguishes_true_from_1(self):
        """JSON equality: True != 1."""
        errors = validate(True, {"enum": [1, 2, 3]})
        assert len(errors) == 1
        assert errors[0].keyword == "enum"


# ── Const keyword ──────────────────────────────────────────────────────────────

class TestConst:
    def test_const_accepts_exact_value(self):
        errors = validate(42, {"const": 42})
        assert errors == []

    def test_const_rejects_different_value(self):
        errors = validate(43, {"const": 42})
        assert len(errors) == 1
        assert errors[0].keyword == "const"

    def test_const_with_string(self):
        errors = validate("hello", {"const": "hello"})
        assert errors == []

    def test_const_distinguishes_true_from_1(self):
        """const: 1 must not accept true."""
        errors = validate(True, {"const": 1})
        assert len(errors) == 1
        assert errors[0].keyword == "const"

    def test_const_with_true_boolean(self):
        errors = validate(True, {"const": True})
        assert errors == []

    def test_const_with_false_boolean(self):
        errors = validate(False, {"const": False})
        assert errors == []


# ── Required keyword ───────────────────────────────────────────────────────────

class TestRequired:
    def test_required_all_present(self):
        errors = validate({"a": 1, "b": 2}, {"required": ["a", "b"]})
        assert errors == []

    def test_required_missing_one(self):
        errors = validate({"a": 1}, {"required": ["a", "b"]})
        assert len(errors) == 1
        assert errors[0].keyword == "required"
        assert "b" in errors[0].message

    def test_required_missing_multiple(self):
        errors = validate({}, {"required": ["a", "b", "c"]})
        assert len(errors) == 3  # One error per missing property

    def test_required_ignores_extra(self):
        errors = validate({"a": 1, "b": 2, "c": 3}, {"required": ["a"]})
        assert errors == []


# ── Properties keyword ─────────────────────────────────────────────────────────

class TestProperties:
    def test_properties_validates_present(self):
        schema = {"properties": {"a": {"type": "integer"}}}
        errors = validate({"a": 1}, schema)
        assert errors == []

    def test_properties_rejects_wrong_type(self):
        schema = {"properties": {"a": {"type": "integer"}}}
        errors = validate({"a": "not an int"}, schema)
        assert len(errors) == 1
        assert errors[0].keyword == "type"
        assert errors[0].instance_path == "/a"

    def test_properties_vacuous_on_absent(self):
        """properties does NOT require - {} is valid even with constraints."""
        schema = {"properties": {"x": {"const": True}}}
        errors = validate({}, schema)
        assert errors == []  # This is correct draft-07 behaviour


# ── AdditionalProperties keyword ───────────────────────────────────────────────

class TestAdditionalProperties:
    def test_additional_false_all_known(self):
        schema = {
            "properties": {"a": {"type": "integer"}},
            "additionalProperties": False
        }
        errors = validate({"a": 1}, schema)
        assert errors == []

    def test_additional_false_one_extra(self):
        schema = {
            "properties": {"a": {"type": "integer"}},
            "additionalProperties": False
        }
        errors = validate({"a": 1, "b": 2}, schema)
        assert len(errors) == 1
        assert errors[0].keyword == "additionalProperties"
        assert errors[0].instance_path == "/b"

    def test_additional_false_multiple_extra(self):
        schema = {
            "properties": {"a": {"type": "integer"}},
            "additionalProperties": False
        }
        errors = validate({"a": 1, "b": 2, "c": 3}, schema)
        assert len(errors) == 2  # One error per extra key


# ── Items keyword ──────────────────────────────────────────────────────────────

class TestItems:
    def test_items_all_valid(self):
        schema = {"items": {"type": "integer"}}
        errors = validate([1, 2, 3], schema)
        assert errors == []

    def test_items_one_invalid(self):
        schema = {"items": {"type": "integer"}}
        errors = validate([1, "two", 3], schema)
        assert len(errors) == 1
        assert errors[0].keyword == "type"
        assert errors[0].instance_path == "/1"

    def test_items_all_invalid(self):
        schema = {"items": {"type": "integer"}}
        errors = validate(["a", "b"], schema)
        assert len(errors) == 2


# ── Contains keyword ───────────────────────────────────────────────────────────

class TestContains:
    def test_contains_found(self):
        schema = {"contains": {"const": 42}}
        errors = validate([1, 42, 3], schema)
        assert errors == []

    def test_contains_not_found(self):
        schema = {"contains": {"const": 42}}
        errors = validate([1, 2, 3], schema)
        assert len(errors) == 1
        assert errors[0].keyword == "contains"

    def test_contains_empty_array(self):
        schema = {"contains": {"type": "integer"}}
        errors = validate([], schema)
        assert len(errors) == 1
        assert errors[0].keyword == "contains"


# ── minItems keyword ───────────────────────────────────────────────────────────

class TestMinItems:
    def test_minitems_met(self):
        schema = {"minItems": 2}
        errors = validate([1, 2], schema)
        assert errors == []

    def test_minitems_not_met(self):
        schema = {"minItems": 3}
        errors = validate([1, 2], schema)
        assert len(errors) == 1
        assert errors[0].keyword == "minItems"


# ── minLength keyword ──────────────────────────────────────────────────────────

class TestMinLength:
    def test_minlength_met(self):
        schema = {"minLength": 3}
        errors = validate("hello", schema)
        assert errors == []

    def test_minlength_not_met(self):
        schema = {"minLength": 5}
        errors = validate("hi", schema)
        assert len(errors) == 1
        assert errors[0].keyword == "minLength"


# ── maxLength keyword ──────────────────────────────────────────────────────────

class TestMaxLength:
    def test_maxlength_met(self):
        schema = {"maxLength": 5}
        errors = validate("hi", schema)
        assert errors == []

    def test_maxlength_not_met(self):
        schema = {"maxLength": 2}
        errors = validate("hello", schema)
        assert len(errors) == 1
        assert errors[0].keyword == "maxLength"


# ── Minimum keyword ────────────────────────────────────────────────────────────

class TestMinimum:
    def test_minimum_met(self):
        schema = {"minimum": 0}
        errors = validate(5, schema)
        assert errors == []

    def test_minimum_exact(self):
        schema = {"minimum": 5}
        errors = validate(5, schema)
        assert errors == []

    def test_minimum_not_met(self):
        schema = {"minimum": 10}
        errors = validate(5, schema)
        assert len(errors) == 1
        assert errors[0].keyword == "minimum"

    def test_minimum_with_float(self):
        schema = {"minimum": 0.5}
        errors = validate(0.3, schema)
        assert len(errors) == 1
        assert errors[0].keyword == "minimum"

    def test_minimum_ignores_non_numbers(self):
        """Minimum only applies to numbers."""
        schema = {"minimum": 0}
        errors = validate("hello", schema)
        assert errors == []  # Not a number, so minimum doesn't apply


# ── Maximum keyword ────────────────────────────────────────────────────────────

class TestMaximum:
    def test_maximum_met(self):
        schema = {"maximum": 10}
        errors = validate(5, schema)
        assert errors == []

    def test_maximum_exact(self):
        schema = {"maximum": 5}
        errors = validate(5, schema)
        assert errors == []

    def test_maximum_not_met(self):
        schema = {"maximum": 5}
        errors = validate(10, schema)
        assert len(errors) == 1
        assert errors[0].keyword == "maximum"

    def test_maximum_ignores_non_numbers(self):
        """Maximum only applies to numbers."""
        schema = {"maximum": 10}
        errors = validate("hello", schema)
        assert errors == []  # Not a number, so maximum doesn't apply


# ── Pattern keyword ────────────────────────────────────────────────────────────

class TestPattern:
    def test_pattern_matches(self):
        schema = {"pattern": "^[0-9a-f]{40}$"}
        errors = validate("a" * 40, schema)
        assert errors == []

    def test_pattern_no_match(self):
        schema = {"pattern": "^[0-9a-f]{40}$"}
        errors = validate("short", schema)
        assert len(errors) == 1
        assert errors[0].keyword == "pattern"

    def test_pattern_uses_search(self):
        """Draft-07 uses re.search, not re.match - unanchored."""
        schema = {"pattern": "hello"}  # No anchors
        errors = validate("say hello world", schema)
        assert errors == []  # search finds "hello" in the middle


# ── AllOf keyword ──────────────────────────────────────────────────────────────

class TestAllOf:
    def test_allof_all_pass(self):
        schema = {
            "allOf": [
                {"type": "integer"},
                {"minimum": 0}
            ]
        }
        errors = validate(42, schema)
        assert errors == []

    def test_allof_one_fails(self):
        schema = {
            "allOf": [
                {"type": "integer"},
                {"type": "string"}
            ]
        }
        errors = validate(42, schema)
        assert len(errors) == 1  # One branch fails

    def test_allof_reports_each_branch_errors(self):
        schema = {
            "allOf": [
                {"type": "integer"},
                {"type": "string"}
            ]
        }
        errors = validate(True, schema)
        # Both branches fail (True is boolean, not int or string)
        assert len(errors) == 2


# ── AnyOf keyword ──────────────────────────────────────────────────────────────

class TestAnyOf:
    def test_anyof_one_passes(self):
        schema = {
            "anyOf": [
                {"type": "integer"},
                {"type": "string"}
            ]
        }
        errors = validate(42, schema)
        assert errors == []

    def test_anyof_all_fail_one_error(self):
        """anyOf failure produces exactly ONE error."""
        schema = {
            "anyOf": [
                {"type": "integer"},
                {"type": "string"}
            ]
        }
        errors = validate(True, schema)
        assert len(errors) == 1  # Exactly one error, not two
        assert errors[0].keyword == "anyOf"


# ── If/Then/Else keyword ───────────────────────────────────────────────────────

class TestIfThenElse:
    def test_if_passes_then_applied(self):
        schema = {
            "if": {"type": "integer"},
            "then": {"minimum": 10}
        }
        errors = validate(5, schema)
        assert len(errors) == 1  # 5 < 10
        assert errors[0].keyword == "minimum"

    def test_if_fails_then_not_applied(self):
        """When if fails, then is not applied - result is valid."""
        schema = {
            "if": {"type": "integer"},
            "then": {"minimum": 10}
        }
        errors = validate("hello", schema)
        assert errors == []  # Valid - if failed, then not applied

    def test_if_errors_not_reported(self):
        """Errors from evaluating if are NEVER reported."""
        schema = {
            "if": {"type": "integer"},
            "then": {"type": "string"}
        }
        errors = validate("hello", schema)
        assert errors == []
        # No error about "hello" not being integer (that was the if check)

    def test_else_applied_when_if_fails(self):
        schema = {
            "if": {"type": "integer"},
            "then": {"type": "string"},
            "else": {"type": "boolean"}
        }
        errors = validate("hello", schema)
        assert len(errors) == 1  # "hello" is not boolean
        assert errors[0].keyword == "type"


# ── UnsupportedKeyword ─────────────────────────────────────────────────────────

class TestUnsupportedKeyword:
    def test_typo_in_required(self):
        schema = {"requried": ["a"]}  # Typo
        with pytest.raises(UnsupportedKeyword) as exc_info:
            validate({"a": 1}, schema)
        assert "requried" in str(exc_info.value)

    def test_unrecognised_type_value(self):
        schema = {"type": "objekt"}  # Typo
        with pytest.raises(UnsupportedKeyword) as exc_info:
            validate({}, schema)
        assert "objekt" in str(exc_info.value)

    def test_oneof_not_supported(self):
        """oneOf is deliberately NOT supported."""
        schema = {"oneOf": [{"type": "integer"}, {"type": "string"}]}
        with pytest.raises(UnsupportedKeyword) as exc_info:
            validate(42, schema)
        assert "oneOf" in str(exc_info.value)

    def test_unknown_keyword_nested(self):
        schema = {"properties": {"a": {"unknownKeyword": True}}}
        with pytest.raises(UnsupportedKeyword) as exc_info:
            validate({"a": 1}, schema)
        assert "unknownKeyword" in str(exc_info.value)


# ── Real schemas load ──────────────────────────────────────────────────────────

class TestRealSchemas:
    """Guard: real schemas must load without UnsupportedKeyword."""

    def test_external_task_envelope_schema_loads(self):
        """external-task-envelope.schema.json uses only supported keywords."""
        schema_path = Path(__file__).parent.parent.parent.parent / "core" / "state" / "external-task-envelope.schema.json"
        with open(schema_path) as f:
            schema = json.load(f)
        # Should not raise
        from platforms.python.tests.minischema import _check_schema_keywords
        _check_schema_keywords(schema)

    def test_collected_evidence_schema_loads(self):
        """collected-evidence.schema.json uses only supported keywords."""
        schema_path = Path(__file__).parent.parent.parent.parent / "core" / "state" / "collected-evidence.schema.json"
        with open(schema_path) as f:
            schema = json.load(f)
        # Should not raise
        from platforms.python.tests.minischema import _check_schema_keywords
        _check_schema_keywords(schema)
