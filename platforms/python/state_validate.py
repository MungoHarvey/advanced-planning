"""
state_validate.py — JSON Schema validation for Advanced Planning state files
=============================================================================

Validates documents against the six canonical state schemas:

- loop-ready.schema.json
- loop-complete.schema.json
- gate-verdict.schema.json
- gate-failure-context.schema.json
- external-task-envelope.schema.json
- collected-evidence.schema.json

CLI usage:
    python ".advanced-plans/bin/ap.py" state_validate <schema-basename> <document-path>

Exit codes:
    0 — valid
    1 — document failed validation
    2 — usage or environment error (bad basename, unreadable file, malformed JSON, missing schema)

Library usage:
    from platforms.python.state_validate import validate_document, ValidationError, SchemaError

    try:
        validate_document("loop-ready", ".advanced-plans/state/loop-ready.json")
    except ValidationError as e:
        print(e.errors)
    except SchemaError as e:
        print(e.message)
"""

import json
import sys
from pathlib import Path
from typing import Any, List, NamedTuple

from platforms.python.minischema import validate, UnsupportedKeyword


# ── Schema registry ────────────────────────────────────────────────────────────

VALID_SCHEMAS = frozenset({
    "loop-ready",
    "loop-complete",
    "gate-verdict",
    "gate-failure-context",
    "external-task-envelope",
    "collected-evidence",
})


# ── Schema resolution ──────────────────────────────────────────────────────────

def _get_schema_dir() -> Path:
    """Resolve the schema directory from the package location.

    This uses the package location (platforms.python.__file__) to derive the
    path to core/state/, not os.getcwd() or sys.argv[0].

    Why not os.getcwd()? An installed project has no core/ directory — that is
    the entire point of Contract 6. Resolution must work from any cwd.

    Why not sys.argv[0]? That points to the launcher script, not the module.
    The package location is the authoritative anchor.
    """
    import platforms.python
    package_dir = Path(platforms.python.__file__).parent
    return package_dir.parent.parent / "core" / "state"


def _load_schema(basename: str) -> dict:
    """Load a schema by basename (without .schema.json suffix).

    Args:
        basename: One of the six valid schema names.

    Returns:
        The schema as a dict.

    Raises:
        SchemaError: If the schema file is missing or invalid.
    """
    schema_dir = _get_schema_dir()
    schema_path = schema_dir / f"{basename}.schema.json"

    if not schema_path.exists():
        raise SchemaError(
            f"Schema file not found: {schema_path}",
            f"Valid schema basenames are: {', '.join(sorted(VALID_SCHEMAS))}"
        )

    try:
        return json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SchemaError(
            f"Schema file is not valid JSON: {schema_path} ({e})",
            "The schema file is corrupted — reinstall from source."
        )


def _load_document(path: str) -> Any:
    """Load a JSON document from disk.

    Args:
        path: Path to the JSON file.

    Returns:
        The parsed JSON value.

    Raises:
        DocumentError: If the file is missing, unreadable, or not valid JSON.
    """
    doc_path = Path(path)

    if not doc_path.exists():
        raise DocumentError(
            f"Document file not found: {path}",
            "Check the path and ensure the file exists."
        )

    try:
        return json.loads(doc_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise DocumentError(
            f"Document is not valid JSON: {path} ({e})",
            "Repair the JSON syntax or regenerate the file."
        )


# ── Exception types ────────────────────────────────────────────────────────────

class SchemaError(Exception):
    """Raised when a schema cannot be loaded or is unknown."""

    def __init__(self, problem: str, fix: str):
        self.problem = problem
        self.fix = fix
        super().__init__(problem)


class DocumentError(Exception):
    """Raised when a document cannot be loaded."""

    def __init__(self, problem: str, fix: str):
        self.problem = problem
        self.fix = fix
        super().__init__(problem)


class ValidationError(NamedTuple):
    """A single validation error."""
    instance_path: str
    schema_path: str
    keyword: str
    message: str

    @classmethod
    def from_minischema(cls, error) -> "ValidationError":
        """Convert a minischema Error to a ValidationError."""
        return cls(
            instance_path=error.instance_path,
            schema_path=error.schema_path,
            keyword=error.keyword,
            message=error.message
        )


# ── Library API ────────────────────────────────────────────────────────────────

def validate_document(basename: str, document_path: str) -> List[ValidationError]:
    """Validate a document against a canonical schema.

    Args:
        basename: One of the six valid schema names (without .schema.json).
        document_path: Path to the JSON document to validate.

    Returns:
        List of ValidationError. Empty list means valid.

    Raises:
        SchemaError: If the schema basename is unknown or the schema file
            cannot be loaded.
        DocumentError: If the document file cannot be loaded.
        UnsupportedKeyword: If the schema uses an unsupported JSON Schema
            keyword (this is a schema defect, not a document error).
    """
    if basename not in VALID_SCHEMAS:
        raise SchemaError(
            f"Unknown schema basename: {basename!r}",
            f"Valid schema basenames are: {', '.join(sorted(VALID_SCHEMAS))}"
        )

    schema = _load_schema(basename)
    instance = _load_document(document_path)

    errors = validate(instance, schema)
    return [ValidationError.from_minischema(e) for e in errors]


def is_valid(basename: str, document_path: str) -> bool:
    """Check if a document is valid against its schema.

    Args:
        basename: One of the six valid schema names.
        document_path: Path to the JSON document.

    Returns:
        True if valid, False if validation errors exist.

    Raises:
        SchemaError: If the schema cannot be loaded.
        DocumentError: If the document cannot be loaded.
        UnsupportedKeyword: If the schema is malformed.
    """
    errors = validate_document(basename, document_path)
    return len(errors) == 0


# ── CLI ────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 (valid), 1 (invalid), 2 (usage/environment error).
    """
    argv = list(sys.argv[1:]) if argv is None else argv

    if len(argv) != 2:
        sys.stderr.write(
            "Usage: python .advanced-plans/bin/ap.py state_validate <schema-basename> <document-path>\n"
        )
        sys.stderr.write(
            f"Valid schema basenames: {', '.join(sorted(VALID_SCHEMAS))}\n"
        )
        return 2

    basename, document_path = argv

    if basename not in VALID_SCHEMAS:
        sys.stderr.write(f"Error: Unknown schema basename: {basename!r}\n")
        sys.stderr.write(
            f"Valid schema basenames: {', '.join(sorted(VALID_SCHEMAS))}\n"
        )
        return 2

    try:
        errors = validate_document(basename, document_path)
    except SchemaError as e:
        sys.stderr.write(f"Error: {e.problem}\n")
        sys.stderr.write(f"Fix: {e.fix}\n")
        return 2
    except DocumentError as e:
        sys.stderr.write(f"Error: {e.problem}\n")
        sys.stderr.write(f"Fix: {e.fix}\n")
        return 2
    except UnsupportedKeyword as e:
        sys.stderr.write(f"Error: Schema uses unsupported keyword: {e}\n")
        sys.stderr.write("Fix: The schema file uses a JSON Schema keyword this validator does not support.\n")
        return 2

    if errors:
        for err in errors:
            sys.stderr.write(
                f"Validation error at {err.instance_path or 'root'}: "
                f"{err.message} (schema: {err.schema_path}, keyword: {err.keyword})\n"
            )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
