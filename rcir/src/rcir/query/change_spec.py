"""
RCIR v8 — Change Specification Model (PHASE 4).

Represents a formal, structured specification of a code modification,
replacing raw unstructured natural language queries with typed engineering intent.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChangeOperation(str, Enum):
    """Permitted change operation types as defined in RCIR v8 specification."""
    RENAME = "rename"
    SIGNATURE_CHANGE = "signature_change"
    BEHAVIOR_CHANGE = "behavior_change"
    ROUTE_CHANGE = "route_change"
    SCHEMA_CHANGE = "schema_change"
    EVENT_CHANGE = "event_change"
    CONFIG_CHANGE = "config_change"
    PERMISSION_CHANGE = "permission_change"
    SERVICE_BOUNDARY_CHANGE = "service_boundary_change"


class RequestedScope(str, Enum):
    """Scope boundary for change impact analysis."""
    LOCAL = "local"
    MODULE = "module"
    CROSS_MODULE = "cross_module"
    REPOSITORY = "repository"


@dataclass
class ChangeSpecification:
    """Formal representation of an engineering change intent."""
    operation: ChangeOperation
    target_entities: list[str] = field(default_factory=list)
    changed_facets: list[str] = field(default_factory=list)
    requested_scope: RequestedScope = RequestedScope.CROSS_MODULE
    language: str | None = None
    risk_hints: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation.value if isinstance(self.operation, ChangeOperation) else str(self.operation),
            "target_entities": list(self.target_entities),
            "changed_facets": list(self.changed_facets),
            "requested_scope": self.requested_scope.value if isinstance(self.requested_scope, RequestedScope) else str(self.requested_scope),
            "language": self.language,
            "risk_hints": list(self.risk_hints),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChangeSpecification:
        op_str = data.get("operation", "behavior_change")
        try:
            op = ChangeOperation(op_str)
        except ValueError:
            op = ChangeOperation.BEHAVIOR_CHANGE

        scope_str = data.get("requested_scope", "cross_module")
        try:
            scope = RequestedScope(scope_str)
        except ValueError:
            scope = RequestedScope.CROSS_MODULE

        return cls(
            operation=op,
            target_entities=data.get("target_entities", []),
            changed_facets=data.get("changed_facets", []),
            requested_scope=scope,
            language=data.get("language"),
            risk_hints=data.get("risk_hints", []),
            description=data.get("description", ""),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> ChangeSpecification:
        return cls.from_dict(json.loads(json_str))
