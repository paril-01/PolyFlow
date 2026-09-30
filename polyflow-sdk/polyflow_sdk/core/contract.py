"""
PolyFlow Contract and Schema Validation Engine.

Enforces schema types, constraints, and organizational compliance for .poly files.
"""

import re
from typing import Dict, Any, List, Tuple
from polyflow_sdk.core.interpreter import PolyFile, PolySchema


class ContractValidationError(Exception):
    pass


class ContractValidator:
    """Validates contract schemas and payloads against .poly definitions."""

    @staticmethod
    def validate_payload(schema: PolySchema, payload: Dict[str, Any]) -> List[str]:
        """Validate input payload dictionary against schema fields and constraints."""
        errors = []
        for fname, field in schema.fields.items():
            if fname not in payload:
                errors.append(f"Missing required field '{fname}' for schema '{schema.name}'")
                continue

            val = payload[fname]
            expected_type = field.type_str.lower()

            if expected_type == "string" and not isinstance(val, str):
                errors.append(f"Field '{fname}' must be string, got {type(val).__name__}")
            elif expected_type in ("int", "integer") and not isinstance(val, int):
                errors.append(f"Field '{fname}' must be integer, got {type(val).__name__}")
            elif expected_type in ("bool", "boolean") and not isinstance(val, bool):
                errors.append(f"Field '{fname}' must be boolean, got {type(val).__name__}")
            elif expected_type in ("list", "array") and not isinstance(val, list):
                errors.append(f"Field '{fname}' must be list, got {type(val).__name__}")
            elif expected_type in ("dict", "map") and not isinstance(val, dict):
                errors.append(f"Field '{fname}' must be dict, got {type(val).__name__}")

            # Check constraints
            if isinstance(val, str):
                if "min" in field.constraints and len(val) < int(field.constraints["min"]):
                    errors.append(f"Field '{fname}' length {len(val)} < min {field.constraints['min']}")
                if "max" in field.constraints and len(val) > int(field.constraints["max"]):
                    errors.append(f"Field '{fname}' length {len(val)} > max {field.constraints['max']}")
                if field.constraints.get("format") == "email" and "@" not in val:
                    errors.append(f"Field '{fname}' is not a valid email format: '{val}'")

            elif isinstance(val, (int, float)):
                if "min" in field.constraints and val < float(field.constraints["min"]):
                    errors.append(f"Field '{fname}' value {val} < min {field.constraints['min']}")
                if "max" in field.constraints and val > float(field.constraints["max"]):
                    errors.append(f"Field '{fname}' value {val} > max {field.constraints['max']}")

        return errors

    @staticmethod
    def audit_contract_compliance(poly_file: PolyFile) -> Dict[str, Any]:
        """Audit organizational compliance of .poly file contracts."""
        issues = []
        if not poly_file.contracts:
            issues.append("File lacks @contract definition block.")
        else:
            c = poly_file.contracts[0]
            if not c.feature_id or c.feature_id == "UNKNOWN":
                issues.append("Contract missing unique feature_id.")
            if not c.owner:
                issues.append("Contract missing owner assignment.")

        return {
            "compliant": len(issues) == 0,
            "contracts_found": len(poly_file.contracts),
            "schemas_found": len(poly_file.schemas),
            "decisions_found": len(poly_file.decisions),
            "issues": issues
        }
