"""
RCIR v8 — Traversal Policy Engine (PHASE 7).

Replaces generic 2-hop bidirectional BFS with typed, directional,
operation-specific graph traversal policies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from rcir.graph.multi_view import MultiViewGraph
from rcir.query.change_spec import ChangeOperation, ChangeSpecification


class TraversalDirection(str, Enum):
    FORWARD = "forward"      # Follow outgoing dependencies (dependencies of target)
    BACKWARD = "backward"    # Follow incoming dependencies (consumers/callers of target)
    BIDIRECTIONAL = "both"   # Follow both


@dataclass
class TraversalRule:
    """A single rule defining how an edge type should be traversed."""
    edge_type: str
    direction: TraversalDirection
    max_hops: int = 1
    min_resolution: str = "static_inference"
    weight_multiplier: float = 1.0


@dataclass
class TraversalHit:
    """A node discovered via traversal with provenance."""
    node_id: str
    hop_distance: int
    edge_type: str
    direction: str
    resolution: str
    score: float
    path: list[str] = field(default_factory=list)


@dataclass
class TraversalPolicy:
    """Complete traversal policy tailored to a ChangeOperation."""
    operation: ChangeOperation
    rules: list[TraversalRule] = field(default_factory=list)
    max_hops: int = 1
    max_candidates: int = 150
    allow_cross_module: bool = True
    module_boundary_penalty: float = 0.7

    @classmethod
    def for_operation(cls, operation: ChangeOperation | str) -> TraversalPolicy:
        """Construct deterministic policy tailored to the specific change operation."""
        if isinstance(operation, str):
            try:
                operation = ChangeOperation(operation)
            except ValueError:
                operation = ChangeOperation.BEHAVIOR_CHANGE

        if operation == ChangeOperation.RENAME:
            # Rename: Only callers, importers, overrides, and tests need to change
            return cls(
                operation=operation,
                rules=[
                    TraversalRule("calls", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.2),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.0),
                    TraversalRule("inherits", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.1),
                    TraversalRule("implements", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.1),
                    TraversalRule("overrides", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.1),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.9),
                ],
                max_hops=1,
                max_candidates=100,
            )

        elif operation == ChangeOperation.SIGNATURE_CHANGE:
            # Signature Change: Direct callers, interface declarations, overrides, implementations, tests
            return cls(
                operation=operation,
                rules=[
                    TraversalRule("calls", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.3),
                    TraversalRule("implements", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.2),
                    TraversalRule("inherits", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.1),
                    TraversalRule("overrides", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.2),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=0.8),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.9),
                ],
                max_hops=1,
                max_candidates=120,
            )

        elif operation == ChangeOperation.ROUTE_CHANGE:
            # Route Change: Route declaration, controller, frontend client calls, route tests
            return cls(
                operation=operation,
                rules=[
                    TraversalRule("route_to_controller", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.5),
                    TraversalRule("frontend_to_route", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=1.4),
                    TraversalRule("calls", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.0),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=0.7),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.9),
                ],
                max_hops=2,
                max_candidates=80,
            )

        elif operation == ChangeOperation.EVENT_CHANGE:
            # Event Change: Event dispatchers, listeners, event registration
            return cls(
                operation=operation,
                rules=[
                    TraversalRule("calls", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.4),  # Dispatchers
                    TraversalRule("event_to_listener", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=1.4),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=0.9),
                    TraversalRule("inherits", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=1.0),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.9),
                ],
                max_hops=1,
                max_candidates=60,
            )

        elif operation == ChangeOperation.CONFIG_CHANGE:
            # DI / Config: Service container registration, direct consumers
            return cls(
                operation=operation,
                rules=[
                    TraversalRule("config_service", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.3),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.1),
                    TraversalRule("calls", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.0),
                    TraversalRule("inherits", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=0.8),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.8),
                ],
                max_hops=1,
                max_candidates=150,
            )

        elif operation == ChangeOperation.SERVICE_BOUNDARY_CHANGE:
            # Cross-stack / cross-service: HTTP routes, RPCs, frontend clients
            return cls(
                operation=operation,
                rules=[
                    TraversalRule("frontend_to_route", TraversalDirection.BIDIRECTIONAL, max_hops=2, weight_multiplier=1.5),
                    TraversalRule("route_to_controller", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.4),
                    TraversalRule("calls", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.1),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.9),
                ],
                max_hops=2,
                max_candidates=100,
            )

        else:
            # Default / Behavior Change: 1-hop callers and callees, tests
            return cls(
                operation=ChangeOperation.BEHAVIOR_CHANGE,
                rules=[
                    TraversalRule("calls", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.0),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=0.8),
                    TraversalRule("inherits", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=0.9),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.9),
                ],
                max_hops=1,
                max_candidates=100,
            )


def execute_policy_traversal(
    multi_view: MultiViewGraph,
    seed_nodes: list[str],
    policy: TraversalPolicy,
) -> list[TraversalHit]:
    """Execute targeted traversal strictly governed by TraversalPolicy."""
    rule_map: dict[str, list[TraversalRule]] = {}
    for r in policy.rules:
        rule_map.setdefault(r.edge_type, []).append(r)

    hits: list[TraversalHit] = []
    seen: set[str] = set(seed_nodes)

    current_frontier = list(seed_nodes)

    for hop in range(1, policy.max_hops + 1):
        next_frontier = []

        for curr_node in current_frontier:
            # Check all views for edges touching curr_node
            candidate_edges = []

            # 1. Forward edges
            fwd_edges = (
                multi_view.symbol_fwd.get(curr_node, []) +
                multi_view.boundary_fwd.get(curr_node, []) +
                multi_view.config_fwd.get(curr_node, []) +
                multi_view.verification_fwd.get(curr_node, [])
            )
            for e in fwd_edges:
                candidate_edges.append((e, TraversalDirection.FORWARD, e.get("target", "")))

            # 2. Backward edges
            bwd_edges = (
                multi_view.symbol_bwd.get(curr_node, []) +
                multi_view.boundary_bwd.get(curr_node, []) +
                multi_view.config_bwd.get(curr_node, []) +
                multi_view.verification_bwd.get(curr_node, [])
            )
            for e in bwd_edges:
                candidate_edges.append((e, TraversalDirection.BACKWARD, e.get("source", "")))

            for edge, direction, target_node in candidate_edges:
                if not target_node or target_node in seen:
                    continue

                etype = edge.get("edge_type", "calls")
                matching_rules = rule_map.get(etype, [])

                # Check if this edge is permitted by policy
                permitted = False
                multiplier = 1.0
                for rule in matching_rules:
                    if rule.max_hops >= hop:
                        if rule.direction in (direction, TraversalDirection.BIDIRECTIONAL):
                            permitted = True
                            multiplier = rule.weight_multiplier
                            break

                if not permitted:
                    continue

                resolution = edge.get("resolution", "static_inference")
                base_score = 1.0 if resolution == "static_exact" else 0.7
                hop_decay = 0.6 ** hop
                final_score = base_score * multiplier * hop_decay

                seen.add(target_node)
                hit = TraversalHit(
                    node_id=target_node,
                    hop_distance=hop,
                    edge_type=etype,
                    direction=direction.value,
                    resolution=resolution,
                    score=final_score,
                    path=[curr_node, target_node],
                )
                hits.append(hit)
                next_frontier.append(target_node)

                if len(hits) >= policy.max_candidates:
                    return hits

        current_frontier = next_frontier
        if not current_frontier:
            break

    return hits
