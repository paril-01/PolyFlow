"""
RCIR v8.3 — Change Specification Model (PHASE 4).

Represents a formal, structured specification of a code modification,
separating requested symbol from target file hints and resolving canonical target IDs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChangeOperation(str, Enum):
    """Permitted change operation types as defined in RCIR v8.3 specification."""
    RENAME = "rename"
    SIGNATURE_CHANGE = "signature_change"
    BEHAVIOR_CHANGE = "behavior_change"
    ROUTE_CHANGE = "route_change"
    SCHEMA_CHANGE = "schema_change"
    EVENT_CHANGE = "event_change"
    CONFIG_CHANGE = "config_change"
    PERMISSION_CHANGE = "permission_change"
    SERVICE_BOUNDARY_CHANGE = "service_boundary_change"
    DEPENDENCY_CHANGE = "dependency_change"


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
    requested_symbol: str = ""
    target_file_hint: str = ""
    canonical_target_ids: list[str] = field(default_factory=list)
    changed_facets: list[str] = field(default_factory=list)
    requested_scope: RequestedScope = RequestedScope.CROSS_MODULE
    language: str | None = None
    risk_hints: list[str] = field(default_factory=list)
    description: str = ""
    
    # Backwards compatibility field
    target_entities: list[str] = field(default_factory=list)

    def __post_init__(self):
        # Sync requested_symbol and target_file_hint with target_entities if provided
        if not self.requested_symbol and self.target_entities:
            # First item may be symbol or file
            self.requested_symbol = self.target_entities[0]
        if self.requested_symbol and self.requested_symbol not in self.target_entities:
            self.target_entities.append(self.requested_symbol)

    @property
    def target_symbol(self) -> str:
        return self.requested_symbol

    @property
    def target_file(self) -> str:
        return self.target_file_hint

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation.value if isinstance(self.operation, ChangeOperation) else str(self.operation),
            "requested_symbol": self.requested_symbol,
            "target_file_hint": self.target_file_hint,
            "canonical_target_ids": list(self.canonical_target_ids),
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

        req_sym = data.get("requested_symbol", data.get("target_symbol", ""))
        file_hint = data.get("target_file_hint", data.get("target_file", ""))
        target_ents = list(data.get("target_entities", []))
        if not req_sym and target_ents:
            req_sym = target_ents[0]

        return cls(
            operation=op,
            requested_symbol=req_sym,
            target_file_hint=file_hint,
            canonical_target_ids=data.get("canonical_target_ids", []),
            target_entities=target_ents,
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


# Backwards compatibility alias
ChangeSpec = ChangeSpecification
