"""
RCIR v8 — Multi-View Graph Layers (PHASE 6).

Organizes the repository dependency graph into explicit layer views:
- Symbol View (calls, imports, inherits, implements, overrides, constructs, defines)
- Boundary View (route_to_controller, frontend_to_route, event_to_listener, grpc_to_rpc)
- State / Config View (config_service, db_table, env_var, migration, serializer)
- Verification View (source_to_test, test_to_source)
- Historical View (cochange_file, cochange_symbol)
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


SYMBOL_EDGE_TYPES = {
    "calls", "imports", "inherits", "implements", "overrides",
    "constructs", "defines", "reads", "writes"
}

BOUNDARY_EDGE_TYPES = {
    "route_to_controller", "frontend_to_route", "grpc_client_to_rpc",
    "event_to_listener", "queue_producer_to_consumer", "spec_to_generated_client",
    "http_route", "route"
}

CONFIG_EDGE_TYPES = {
    "config_key", "env_var", "db_table", "db_field", "migration",
    "serializer", "feature_flag", "config_service"
}

VERIFICATION_EDGE_TYPES = {
    "source_to_test", "test_to_source", "module_to_build_target",
    "generated_source", "integration_test", "lint_target"
}

HISTORICAL_EDGE_TYPES = {
    "cochange_file", "cochange_symbol", "production_test_cochange"
}


class MultiViewGraph:
    """Multi-view layered index over a raw dependency graph."""

    def __init__(self, raw_graph: dict[str, Any]):
        self.raw_graph = raw_graph
        self.nodes = raw_graph.get("nodes", [])
        self.edges = raw_graph.get("edges", [])

        # Forward and backward adjacency by view
        self.symbol_fwd: dict[str, list[dict]] = defaultdict(list)
        self.symbol_bwd: dict[str, list[dict]] = defaultdict(list)

        self.boundary_fwd: dict[str, list[dict]] = defaultdict(list)
        self.boundary_bwd: dict[str, list[dict]] = defaultdict(list)

        self.config_fwd: dict[str, list[dict]] = defaultdict(list)
        self.config_bwd: dict[str, list[dict]] = defaultdict(list)

        self.verification_fwd: dict[str, list[dict]] = defaultdict(list)
        self.verification_bwd: dict[str, list[dict]] = defaultdict(list)

        self.historical_fwd: dict[str, list[dict]] = defaultdict(list)
        self.historical_bwd: dict[str, list[dict]] = defaultdict(list)

        self.unsupported_fwd: dict[str, list[dict]] = defaultdict(list)
        self.unsupported_bwd: dict[str, list[dict]] = defaultdict(list)

        # Node index
        self.node_by_path: dict[str, dict] = {n.get("path", ""): n for n in self.nodes}

        self._build_views()

    def _build_views(self) -> None:
        for edge in self.edges:
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            etype = edge.get("edge_type", edge.get("type", "calls"))

            # Primary classification based on normalized taxonomy
            if etype in SYMBOL_EDGE_TYPES:
                self.symbol_fwd[src].append(edge)
                self.symbol_bwd[tgt].append(edge)
            elif etype in BOUNDARY_EDGE_TYPES or etype in {"cross_boundary", "route"}:
                self.boundary_fwd[src].append(edge)
                self.boundary_bwd[tgt].append(edge)
            elif etype in CONFIG_EDGE_TYPES or etype == "config":
                self.config_fwd[src].append(edge)
                self.config_bwd[tgt].append(edge)
            elif etype in VERIFICATION_EDGE_TYPES:
                self.verification_fwd[src].append(edge)
                self.verification_bwd[tgt].append(edge)
            elif etype in HISTORICAL_EDGE_TYPES:
                self.historical_fwd[src].append(edge)
                self.historical_bwd[tgt].append(edge)
            else:
                self.unsupported_fwd[src].append(edge)
                self.unsupported_bwd[tgt].append(edge)

    def get_callers(self, target_entity: str) -> list[dict]:
        """Find nodes that call this entity (incoming calls edges)."""
        callers = []
        for edge in self.symbol_bwd.get(target_entity, []):
            if edge.get("edge_type") == "calls":
                callers.append(edge)
        return callers

    def get_callees(self, source_entity: str) -> list[dict]:
        """Find nodes called by this entity (outgoing calls edges)."""
        callees = []
        for edge in self.symbol_fwd.get(source_entity, []):
            if edge.get("edge_type") == "calls":
                callees.append(edge)
        return callees

    def get_importers(self, target_entity: str) -> list[dict]:
        """Find nodes that import this entity."""
        return [e for e in self.symbol_bwd.get(target_entity, []) if e.get("edge_type") == "imports"]

    def get_routes_for_controller(self, controller_symbol: str) -> list[dict]:
        """Find route declarations targeting this controller/method."""
        routes = []
        clean = controller_symbol.split("\\")[-1]
        for src, edges in self.boundary_fwd.items():
            for e in edges:
                tgt = e.get("target", "")
                if clean in tgt or clean in src:
                    routes.append(e)
        return routes

    def get_tests_for_entity(self, entity_id: str) -> list[dict]:
        """Find test files associated with this entity."""
        return self.verification_bwd.get(entity_id, [])
