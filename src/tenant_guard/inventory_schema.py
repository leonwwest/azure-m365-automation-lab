"""Versioned validation for sanitized Tenant Guard inventories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATH = Path(__file__).parents[2] / "schemas" / "inventory-v1.schema.json"


def validate_inventory(inventory: Any) -> list[str]:
    """Return deterministic field-level validation errors for an inventory."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(inventory), key=lambda error: list(error.absolute_path))
    messages = []
    for error in errors:
        field = ".".join(str(part) for part in error.absolute_path) or "<root>"
        messages.append(f"{field}: {error.message}")
    return messages
