"""
PolyFlow @schema Data Validation and Type Conversion.

Validates data payloads against language-agnostic @schema definitions.
"""

import re
import uuid
from typing import Dict, Any, Tuple, Optional
from polyflow.parser import SchemaBlock

class SchemaValidationError(Exception):
    def __init__(self, message: str, errors: Optional[Dict[str, str]] = None):
        super().__init__(message)
        self.errors = errors or {}

class PolySchemaValidator:
    TYPE_REGEX = re.compile(r"^([a-zA-Z0-9_|]+)(?:<(.+)>)?$")

    def validate(self, schema: SchemaBlock, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        errors = {}

        for field_name, spec in schema.fields.items():
            value = payload.get(field_name)
            is_valid, err_msg = self._validate_field(field_name, spec, value)
            if not is_valid:
                errors[field_name] = err_msg

        if errors:
            return False, errors
        return True, {}

    def _validate_field(self, field_name: str, spec: str, value: Any) -> Tuple[bool, str]:
        # Handle union with null (e.g. string | null)
        allows_null = "| null" in spec or "|null" in spec
        clean_spec = spec.replace("| null", "").replace("|null", "").strip()

        if value is None:
            if allows_null:
                return True, ""
            return False, f"Field '{field_name}' is required and cannot be null."

        match = self.TYPE_REGEX.match(clean_spec)
        if not match:
            return True, ""  # Untyped or unparsed constraint passes

        base_type = match.group(1).lower()
        constraint_str = match.group(2)

        # Base Type Validation
        if base_type == "string":
            if not isinstance(value, str):
                return False, f"Expected string for '{field_name}', got {type(value).__name__}."
        elif base_type in ("number", "int", "float"):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False, f"Expected number for '{field_name}', got {type(value).__name__}."
        elif base_type in ("boolean", "bool"):
            if not isinstance(value, bool):
                return False, f"Expected boolean for '{field_name}', got {type(value).__name__}."
        elif base_type == "uuid":
            try:
                uuid.UUID(str(value))
            except ValueError:
                return False, f"Expected valid UUID for '{field_name}', got '{value}'."

        # Constraint Validation
        if constraint_str:
            constraints = self._parse_constraints(constraint_str)
            if base_type == "string" and isinstance(value, str):
                if "min" in constraints and len(value) < constraints["min"]:
                    return False, f"String '{field_name}' is shorter than min length {constraints['min']}."
                if "max" in constraints and len(value) > constraints["max"]:
                    return False, f"String '{field_name}' exceeds max length {constraints['max']}."
                if "format" in constraints and constraints["format"] == "email":
                    if "@" not in value or "." not in value:
                        return False, f"Field '{field_name}' is not a valid email address."
                if "regex" in constraints:
                    if not re.search(constraints["regex"], value):
                        return False, f"Field '{field_name}' does not match regex '{constraints['regex']}'."

            elif base_type in ("number", "int", "float") and isinstance(value, (int, float)):
                if "min" in constraints and value < constraints["min"]:
                    return False, f"Number '{field_name}' is less than min value {constraints['min']}."
                if "max" in constraints and value > constraints["max"]:
                    return False, f"Number '{field_name}' exceeds max value {constraints['max']}."

        return True, ""

    def _parse_constraints(self, constraint_str: str) -> Dict[str, Any]:
        result = {}
        parts = constraint_str.split(",")
        for part in parts:
            part = part.strip()
            if ":" in part:
                k, v = part.split(":", 1)
                k = k.strip()
                v = v.strip().strip("\"'")
                if v.isdigit():
                    result[k] = int(v)
                elif re.match(r"^\d+\.\d+$", v):
                    result[k] = float(v)
                else:
                    result[k] = v
        return result
