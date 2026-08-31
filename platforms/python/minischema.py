"""Zero-dependency JSON Schema (draft-07 subset) validator.

Supports exactly the keywords used by core/state/*.schema.json. Raises
UnsupportedKeyword for any unknown keyword or unrecognised type value.
"""

import re
from typing import Any, Dict, List, NamedTuple, Optional, Set


class UnsupportedKeyword(Exception):
    """Raised when a schema uses an unsupported keyword."""


class Error(NamedTuple):
    """A single validation error."""
    instance_path: str   # JSON-pointer-ish: "" for root, "/git/base_sha"
    schema_path: str     # e.g. "/allOf/0/then/required"
    keyword: str         # "required", "pattern", "additionalProperties", ...
    message: str         # human-readable


# Keywords this validator supports
SUPPORTED_KEYWORDS = {
    # Assertions
    "type", "enum", "const", "required", "properties", "additionalProperties",
    "items", "contains", "minItems", "minLength", "maxLength", "pattern",
    "allOf", "anyOf", "if", "then", "else", "minimum", "maximum",
    # Annotations (parsed but ignored)
    "$schema", "title", "description", "default", "format",
}

# Valid type values in draft-07
VALID_TYPES = {"string", "number", "integer", "boolean", "array", "object", "null"}


def _check_schema_keywords(schema, path=""):
    # type: (Any, str) -> None
    """Walk a schema and raise UnsupportedKeyword on first unknown keyword."""
    if not isinstance(schema, dict):
        return

    for key, value in schema.items():
        if key not in SUPPORTED_KEYWORDS:
            raise UnsupportedKeyword(f"Unsupported keyword: {key!r} at {path or 'root'}")

        # Recurse into subschemas
        if key in ("properties", "additionalProperties"):
            if isinstance(value, dict):
                for prop_name, prop_schema in value.items():
                    _check_schema_keywords(prop_schema, f"{path}/{key}/{prop_name}")
        elif key == "items":
            _check_schema_keywords(value, f"{path}/{key}")
        elif key in ("allOf", "anyOf"):
            for i, subschema in enumerate(value):
                _check_schema_keywords(subschema, f"{path}/{key}/{i}")
        elif key in ("if", "then", "else"):
            _check_schema_keywords(value, f"{path}/{key}")
        elif key == "contains":
            _check_schema_keywords(value, f"{path}/{key}")


def _json_type(value):
    # type: (Any) -> str
    """Return the JSON type of a Python value.

    Special-case: True/False are booleans, not integers (even though
    isinstance(True, int) is True in Python).
    """
    if value is None:
        return "null"
    if isinstance(value, bool):  # Must check bool before int!
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise ValueError(f"Unknown type: {type(value)}")


def _check_type(value, type_spec):
    # type: (Any, Any) -> bool
    """Check if value matches type specification.

    type_spec may be a string or a list of strings.
    """
    if isinstance(type_spec, str):
        types = [type_spec]
    else:
        types = list(type_spec)

    for t in types:
        if t not in VALID_TYPES:
            raise UnsupportedKeyword(f"Unrecognised type value: {t!r}")

    actual = _json_type(value)

    # Special handling: integer also matches "number" per JSON Schema
    if actual == "integer" and "number" in types:
        return True

    return actual in types


def _validate_impl(instance, schema, instance_path, schema_path):
    # type: (Any, Any, str, str) -> List[Error]
    """Internal validation implementation.

    Returns a list of errors. Empty list means valid.
    """
    if not isinstance(schema, dict):
        return []

    errors = []  # type: List[Error]

    # Handle type keyword
    if "type" in schema:
        type_spec = schema["type"]
        if not _check_type(value=instance, type_spec=type_spec):
            errors.append(Error(
                instance_path=instance_path,
                schema_path=f"{schema_path}/type",
                keyword="type",
                message=f"Expected type {type_spec!r}, got {_json_type(instance)!r}"
            ))

    # Handle enum keyword
    if "enum" in schema:
        enum_values = schema["enum"]
        # Use JSON equality: True != 1, False != 0
        if not any(_json_equals(instance, v) for v in enum_values):
            errors.append(Error(
                instance_path=instance_path,
                schema_path=f"{schema_path}/enum",
                keyword="enum",
                message=f"Value {instance!r} not in enum {enum_values}"
            ))

    # Handle const keyword
    if "const" in schema:
        const_value = schema["const"]
        if not _json_equals(instance, const_value):
            errors.append(Error(
                instance_path=instance_path,
                schema_path=f"{schema_path}/const",
                keyword="const",
                message=f"Value {instance!r} is not const {const_value!r}"
            ))

    # Handle required keyword (objects only)
    if "required" in schema:
        if isinstance(instance, dict):
            for prop in schema["required"]:
                if prop not in instance:
                    errors.append(Error(
                        instance_path=instance_path,
                        schema_path=f"{schema_path}/required",
                        keyword="required",
                        message=f"Missing required property: {prop!r}"
                    ))

    # Handle properties keyword
    if "properties" in schema:
        if isinstance(instance, dict):
            for prop_name, prop_schema in schema["properties"].items():
                if prop_name in instance:
                    prop_errors = _validate_impl(
                        instance[prop_name], prop_schema,
                        f"{instance_path}/{prop_name}",
                        f"{schema_path}/properties/{prop_name}"
                    )
                    errors.extend(prop_errors)

    # Handle additionalProperties: false
    if schema.get("additionalProperties") is False:
        if isinstance(instance, dict):
            allowed = set(schema.get("properties", {}).keys())
            for key in instance.keys():
                if key not in allowed:
                    errors.append(Error(
                        instance_path=f"{instance_path}/{key}",
                        schema_path=f"{schema_path}/additionalProperties",
                        keyword="additionalProperties",
                        message=f"Additional property {key!r} not allowed"
                    ))

    # Handle items keyword (arrays)
    if "items" in schema:
        if isinstance(instance, list):
            items_schema = schema["items"]
            for i, item in enumerate(instance):
                item_errors = _validate_impl(
                    item, items_schema,
                    f"{instance_path}/{i}",
                    f"{schema_path}/items"
                )
                errors.extend(item_errors)

    # Handle contains keyword (arrays)
    if "contains" in schema:
        if isinstance(instance, list):
            contains_schema = schema["contains"]
            found = False
            for item in instance:
                item_errors = _validate_impl(item, contains_schema, "", "")
                if not item_errors:
                    found = True
                    break
            if not found:
                errors.append(Error(
                    instance_path=instance_path,
                    schema_path=f"{schema_path}/contains",
                    keyword="contains",
                    message="No item matches 'contains' schema"
                ))

    # Handle minItems
    if "minItems" in schema:
        if isinstance(instance, list):
            if len(instance) < schema["minItems"]:
                errors.append(Error(
                    instance_path=instance_path,
                    schema_path=f"{schema_path}/minItems",
                    keyword="minItems",
                    message=f"Array has {len(instance)} items, minimum is {schema['minItems']}"
                ))

    # Handle minLength
    if "minLength" in schema:
        if isinstance(instance, str):
            if len(instance) < schema["minLength"]:
                errors.append(Error(
                    instance_path=instance_path,
                    schema_path=f"{schema_path}/minLength",
                    keyword="minLength",
                    message=f"String length {len(instance)}, minimum is {schema['minLength']}"
                ))

    # Handle maxLength
    if "maxLength" in schema:
        if isinstance(instance, str):
            if len(instance) > schema["maxLength"]:
                errors.append(Error(
                    instance_path=instance_path,
                    schema_path=f"{schema_path}/maxLength",
                    keyword="maxLength",
                    message=f"String length {len(instance)}, maximum is {schema['maxLength']}"
                ))

    # Handle minimum (numbers only)
    if "minimum" in schema:
        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if instance < schema["minimum"]:
                errors.append(Error(
                    instance_path=instance_path,
                    schema_path=f"{schema_path}/minimum",
                    keyword="minimum",
                    message=f"Value {instance} is less than minimum {schema['minimum']}"
                ))

    # Handle maximum (numbers only)
    if "maximum" in schema:
        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if instance > schema["maximum"]:
                errors.append(Error(
                    instance_path=instance_path,
                    schema_path=f"{schema_path}/maximum",
                    keyword="maximum",
                    message=f"Value {instance} is greater than maximum {schema['maximum']}"
                ))

    # Handle pattern (uses re.search, not re.match - draft-07 unanchored)
    if "pattern" in schema:
        if isinstance(instance, str):
            pattern = schema["pattern"]
            if not re.search(pattern, instance):
                errors.append(Error(
                    instance_path=instance_path,
                    schema_path=f"{schema_path}/pattern",
                    keyword="pattern",
                    message=f"String does not match pattern {pattern!r}"
                ))

    # Handle allOf
    if "allOf" in schema:
        for i, subschema in enumerate(schema["allOf"]):
            sub_errors = _validate_impl(
                instance, subschema,
                instance_path,
                f"{schema_path}/allOf/{i}"
            )
            errors.extend(sub_errors)

    # Handle anyOf
    if "anyOf" in schema:
        any_valid = False
        for i, subschema in enumerate(schema["anyOf"]):
            sub_errors = _validate_impl(
                instance, subschema,
                instance_path,
                f"{schema_path}/anyOf/{i}"
            )
            if not sub_errors:
                any_valid = True
                break
        if not any_valid:
            errors.append(Error(
                instance_path=instance_path,
                schema_path=f"{schema_path}/anyOf",
                keyword="anyOf",
                message="No subschema in 'anyOf' matches"
            ))

    # Handle if/then/else
    if "if" in schema:
        if_schema = schema["if"]
        if_errors = _validate_impl(instance, if_schema, instance_path, f"{schema_path}/if")

        if not if_errors:
            # if passed, apply then
            if "then" in schema:
                then_errors = _validate_impl(
                    instance, schema["then"],
                    instance_path,
                    f"{schema_path}/then"
                )
                errors.extend(then_errors)
        else:
            # if failed, apply else if present
            if "else" in schema:
                else_errors = _validate_impl(
                    instance, schema["else"],
                    instance_path,
                    f"{schema_path}/else"
                )
                errors.extend(else_errors)
        # Note: if_errors are NEVER reported - if is a condition, not assertion

    return errors


def _json_equals(a, b):
    # type: (Any, Any) -> bool
    """JSON equality: True != 1, False != 0."""
    # Check types first using JSON types
    if _json_type(a) != _json_type(b):
        return False
    return a == b


def validate(instance, schema):
    # type: (Any, Any) -> List[Error]
    """Validate an instance against a JSON Schema (draft-07 subset).

    Returns ALL errors. Empty list means valid.
    Raises UnsupportedKeyword for unknown keywords or unrecognised type values.

    Args:
        instance: The JSON value to validate.
        schema: The JSON Schema (as a dict).

    Returns:
        List of Error namedtuples. Empty if valid.

    Raises:
        UnsupportedKeyword: If schema uses unsupported keywords.
    """
    # First, check for unsupported keywords
    _check_schema_keywords(schema)

    # Then validate
    return _validate_impl(instance, schema, "", "")
