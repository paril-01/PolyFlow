"""
RCIR v8 — Intent Parser (PHASE 4).

Converts natural language change descriptions or benchmark tasks into
deterministic ChangeSpecification objects without LLM non-determinism.
"""

from __future__ import annotations

import re
from typing import Any

from rcir.query.change_spec import ChangeOperation, ChangeSpecification, RequestedScope


class DeterministicIntentParser:
    """Deterministic parser converting text or task metadata into ChangeSpecification."""

    OPERATION_PATTERNS = [
        (ChangeOperation.ROUTE_CHANGE, re.compile(r"\b(route|endpoint|controller|api|url|rest|dav|http)\b", re.IGNORECASE)),
        (ChangeOperation.EVENT_CHANGE, re.compile(r"\b(event|listener|dispatcher|notify|subscribe|publish)\b", re.IGNORECASE)),
        (ChangeOperation.CONFIG_CHANGE, re.compile(r"\b(config|setting|preference|container|dependency injection|di|service resolution)\b", re.IGNORECASE)),
        (ChangeOperation.SCHEMA_CHANGE, re.compile(r"\b(schema|migration|database|table|column|entity|model|db)\b", re.IGNORECASE)),
        (ChangeOperation.RENAME, re.compile(r"\b(rename|move|relocate)\b", re.IGNORECASE)),
        (ChangeOperation.SIGNATURE_CHANGE, re.compile(r"\b(signature|parameter|argument|return type|interface method|contract evolution)\b", re.IGNORECASE)),
        (ChangeOperation.SERVICE_BOUNDARY_CHANGE, re.compile(r"\b(cross-stack|cross-service|grpc|protobuf|rpc|boundary)\b", re.IGNORECASE)),
        (ChangeOperation.PERMISSION_CHANGE, re.compile(r"\b(permission|auth|role|acl|access control)\b", re.IGNORECASE)),
    ]

    @classmethod
    def parse_task(cls, task_dict: dict[str, Any]) -> ChangeSpecification:
        """Construct a ChangeSpecification directly from benchmark task metadata."""
        category = task_dict.get("category", "")
        title = task_dict.get("title", "")
        desc = task_dict.get("description", "")
        target_symbol = task_dict.get("target_symbol", "")
        target_file = task_dict.get("target_file", "")
        query = task_dict.get("query", "")

        # 1. Deterministic category mapping
        op = cls._map_category_to_operation(category)
        if op is None:
            op = cls.infer_operation(f"{title} {desc} {query}")

        targets = []
        if target_symbol:
            targets.append(target_symbol)
        if target_file and target_file not in targets:
            targets.append(target_file)

        facets = []
        if "method" in category or "endpoint" in title.lower():
            facets.append("callable")
        if "interface" in category or "contract" in title.lower():
            facets.append("type_contract")
        if "event" in category:
            facets.append("event_payload")
        if "service" in category or "config" in title.lower():
            facets.append("di_container")

        scope = RequestedScope.CROSS_MODULE
        if category in ("cross_stack", "service_boundary"):
            scope = RequestedScope.REPOSITORY
        elif category in ("controller_route", "interface_method"):
            scope = RequestedScope.CROSS_MODULE

        language = None
        if target_file:
            if target_file.endswith(".php"):
                language = "php"
            elif target_file.endswith((".ts", ".tsx", ".js")):
                language = "typescript"
            elif target_file.endswith(".py"):
                language = "python"
            elif target_file.endswith(".go"):
                language = "go"

        return ChangeSpecification(
            operation=op,
            target_entities=targets,
            changed_facets=facets,
            requested_scope=scope,
            language=language,
            risk_hints=[category] if category else [],
            description=desc or title or query,
        )

    @classmethod
    def _map_category_to_operation(cls, category: str) -> ChangeOperation | None:
        cat_lower = category.lower()
        if cat_lower in ("controller_route", "route", "routes"):
            return ChangeOperation.ROUTE_CHANGE
        if cat_lower in ("interface_method", "signature", "signature_change"):
            return ChangeOperation.SIGNATURE_CHANGE
        if cat_lower in ("event_contract", "event", "events"):
            return ChangeOperation.EVENT_CHANGE
        if cat_lower in ("dependency_injection", "config", "config_change"):
            return ChangeOperation.CONFIG_CHANGE
        if cat_lower in ("cross_stack", "cross_service", "boundary"):
            return ChangeOperation.SERVICE_BOUNDARY_CHANGE
        if cat_lower in ("schema", "database", "migration"):
            return ChangeOperation.SCHEMA_CHANGE
        return None

    @classmethod
    def infer_operation(cls, text: str) -> ChangeOperation:
        """Infer ChangeOperation from query or description text using deterministic rules."""
        for op, pattern in cls.OPERATION_PATTERNS:
            if pattern.search(text):
                return op
        return ChangeOperation.BEHAVIOR_CHANGE

    @classmethod
    def parse_query(cls, query: str, target_symbol: str | None = None) -> ChangeSpecification:
        """Parse raw query string into ChangeSpecification."""
        op = cls.infer_operation(query)
        targets = [target_symbol] if target_symbol else []
        return ChangeSpecification(
            operation=op,
            target_entities=targets,
            requested_scope=RequestedScope.CROSS_MODULE,
            description=query,
        )
