"""
RCIR v8.1 — Traversal Policy Engine (PHASES 5, 6, 7, 8, 9).

Replaces destructive candidate caps with:
- Strict resolution rank enforcement (min_resolution: static_exact > static_inference > dynamic_unresolved > unsupported)
- Adaptive Fanout Control (FanoutPolicy: LOW, MEDIUM, HIGH)
- Protection of ALL direct exact relationships from candidate count pruning
- Exact shortest-hop distance tracking (best_hop_distance = min(hops))
- Complete edge evidence retention per candidate
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from rcir.graph.multi_view import MultiViewGraph
from rcir.query.change_spec import ChangeOperation, ChangeSpecification


RESOLUTION_RANKS = {
    "unsupported": 1,
    "dynamic_unresolved": 2,
    "static_inference": 3,
    "static_exact": 4,
}


class TraversalDirection(str, Enum):
    FORWARD = "forward"      # Follow outgoing dependencies
    BACKWARD = "backward"    # Follow incoming dependencies (consumers/callers)
    BIDIRECTIONAL = "both"   # Follow both


class FanoutMode(str, Enum):
    LOW_DEGREE = "low_degree"        # <= 10 connections
    MEDIUM_DEGREE = "medium_degree"  # 11-50 connections
    HIGH_DEGREE = "high_degree"      # > 50 connections


@dataclass
class FanoutPolicy:
    """Adaptive fanout control based on target branching factor."""
    mode: FanoutMode
    allow_recursive_expansion: bool = True
    max_indirect_candidates: int = 1000

    @classmethod
    def evaluate(cls, degree: int, operation: ChangeOperation) -> FanoutPolicy:
        if degree > 50:
            # High-degree: Include all direct exact consumers, do NOT recursively expand
            return cls(
                mode=FanoutMode.HIGH_DEGREE,
                allow_recursive_expansion=False,
                max_indirect_candidates=200,
            )
        elif degree <= 10:
            # Low-degree: Allow full contract-specific 2-hop expansion
            return cls(
                mode=FanoutMode.LOW_DEGREE,
                allow_recursive_expansion=True,
                max_indirect_candidates=1000,
            )
        else:
            return cls(
                mode=FanoutMode.MEDIUM_DEGREE,
                allow_recursive_expansion=True,
                max_indirect_candidates=500,
            )


@dataclass
class TraversalRule:
    """A rule defining how an edge type should be traversed."""
    edge_type: str
    direction: TraversalDirection
    max_hops: int = 1
    min_resolution: str = "static_inference"
    weight_multiplier: float = 1.0


@dataclass
class EdgeEvidence:
    """Auditable evidence for a single traversed edge."""
    source: str
    target: str
    edge_type: str
    resolution: str
    direction: str
    hop: int
    policy_weight: float
    path_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type,
            "resolution": self.resolution,
            "direction": self.direction,
            "hop": self.hop,
            "policy_weight": round(self.policy_weight, 2),
            "path_score": round(self.path_score, 4),
        }


@dataclass
class TraversalHit:
    """A node discovered via traversal with full provenance and minimum hop distance."""
    node_id: str
    best_hop_distance: int
    best_traversal_score: float
    paths: list[list[str]] = field(default_factory=list)
    edge_evidence: list[EdgeEvidence] = field(default_factory=list)
    resolution_classes: list[str] = field(default_factory=list)
    edge_types: list[str] = field(default_factory=list)

    # Backward compatibility properties
    @property
    def hop_distance(self) -> int:
        return self.best_hop_distance

    @property
    def score(self) -> float:
        return self.best_traversal_score

    @property
    def path(self) -> list[str]:
        return self.paths[0] if self.paths else []

    @property
    def edge_type(self) -> str:
        return self.edge_types[0] if self.edge_types else "calls"

    @property
    def resolution(self) -> str:
        return self.resolution_classes[0] if self.resolution_classes else "static_inference"

    @property
    def direction(self) -> str:
        return self.edge_evidence[0].direction if self.edge_evidence else "forward"


@dataclass
class TraversalPolicy:
    """Complete traversal policy tailored to a ChangeOperation and FanoutPolicy."""
    operation: ChangeOperation
    rules: list[TraversalRule] = field(default_factory=list)
    max_hops: int = 1
    preserve_all_direct_exact: bool = True
    max_indirect_candidates: int = 1000
    allow_cross_module: bool = True
    module_boundary_penalty: float = 0.7
    fanout_policy: Optional[FanoutPolicy] = None

    @classmethod
    def for_operation(
        cls,
        operation: ChangeOperation | str,
        seed_degree: int = 0,
    ) -> TraversalPolicy:
        """Construct deterministic policy tailored to the specific change operation."""
        if isinstance(operation, str):
            try:
                operation = ChangeOperation(operation)
            except ValueError:
                operation = ChangeOperation.BEHAVIOR_CHANGE

        fanout = FanoutPolicy.evaluate(seed_degree, operation)

        if operation == ChangeOperation.RENAME:
            return cls(
                operation=operation,
                rules=[
                    TraversalRule("calls", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.2, min_resolution="static_inference"),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.0, min_resolution="static_inference"),
                    TraversalRule("inherits", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.1, min_resolution="static_exact"),
                    TraversalRule("implements", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.1, min_resolution="static_exact"),
                    TraversalRule("overrides", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.1, min_resolution="static_exact"),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.9, min_resolution="static_inference"),
                ],
                max_hops=1,
                fanout_policy=fanout,
            )

        elif operation == ChangeOperation.SIGNATURE_CHANGE:
            return cls(
                operation=operation,
                rules=[
                    TraversalRule("calls", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.3, min_resolution="static_inference"),
                    TraversalRule("implements", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.2, min_resolution="static_exact"),
                    TraversalRule("inherits", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.1, min_resolution="static_exact"),
                    TraversalRule("overrides", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.2, min_resolution="static_exact"),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=0.8, min_resolution="static_inference"),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.9, min_resolution="static_inference"),
                ],
                max_hops=1,
                fanout_policy=fanout,
            )

        elif operation == ChangeOperation.ROUTE_CHANGE:
            return cls(
                operation=operation,
                rules=[
                    TraversalRule("route_to_controller", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.5, min_resolution="static_inference"),
                    TraversalRule("route", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.5, min_resolution="static_exact"),
                    TraversalRule("cross_boundary", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.4, min_resolution="static_inference"),
                    TraversalRule("frontend_to_route", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=1.4, min_resolution="static_inference"),
                    TraversalRule("calls", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.0, min_resolution="static_inference"),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=0.7, min_resolution="static_inference"),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.9, min_resolution="static_inference"),
                ],
                max_hops=2,
                fanout_policy=fanout,
            )

        elif operation == ChangeOperation.EVENT_CHANGE:
            return cls(
                operation=operation,
                rules=[
                    TraversalRule("calls", TraversalDirection.BACKWARD, max_hops=2, weight_multiplier=1.4, min_resolution="static_inference"),
                    TraversalRule("event_to_listener", TraversalDirection.FORWARD, max_hops=2, weight_multiplier=1.4, min_resolution="static_inference"),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=2, weight_multiplier=1.0, min_resolution="static_inference"),
                    TraversalRule("inherits", TraversalDirection.BIDIRECTIONAL, max_hops=2, weight_multiplier=1.0, min_resolution="static_exact"),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.9, min_resolution="static_inference"),
                ],
                max_hops=2,
                fanout_policy=fanout,
            )

        elif operation == ChangeOperation.CONFIG_CHANGE:
            return cls(
                operation=operation,
                rules=[
                    TraversalRule("config_service", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.3, min_resolution="static_exact"),
                    TraversalRule("config", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.3, min_resolution="static_exact"),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.1, min_resolution="static_inference"),
                    TraversalRule("calls", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=1.0, min_resolution="static_inference"),
                    TraversalRule("inherits", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=0.8, min_resolution="static_exact"),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.8, min_resolution="static_inference"),
                ],
                max_hops=1,
                fanout_policy=fanout,
            )

        elif operation == ChangeOperation.SERVICE_BOUNDARY_CHANGE:
            return cls(
                operation=operation,
                rules=[
                    TraversalRule("frontend_to_route", TraversalDirection.BIDIRECTIONAL, max_hops=2, weight_multiplier=1.5, min_resolution="static_inference"),
                    TraversalRule("cross_boundary", TraversalDirection.BIDIRECTIONAL, max_hops=2, weight_multiplier=1.5, min_resolution="static_inference"),
                    TraversalRule("route_to_controller", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.4, min_resolution="static_inference"),
                    TraversalRule("route", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.4, min_resolution="static_exact"),
                    TraversalRule("calls", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.1, min_resolution="static_inference"),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=2, weight_multiplier=1.2, min_resolution="static_inference"),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.9, min_resolution="static_inference"),
                ],
                max_hops=2,
                fanout_policy=fanout,
            )

        else:
            return cls(
                operation=ChangeOperation.BEHAVIOR_CHANGE,
                rules=[
                    TraversalRule("calls", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=1.0, min_resolution="static_inference"),
                    TraversalRule("imports", TraversalDirection.BACKWARD, max_hops=1, weight_multiplier=0.8, min_resolution="static_inference"),
                    TraversalRule("inherits", TraversalDirection.BIDIRECTIONAL, max_hops=1, weight_multiplier=0.9, min_resolution="static_exact"),
                    TraversalRule("source_to_test", TraversalDirection.FORWARD, max_hops=1, weight_multiplier=0.9, min_resolution="static_inference"),
                ],
                max_hops=1,
                fanout_policy=fanout,
            )


def execute_policy_traversal(
    multi_view: MultiViewGraph,
    seed_nodes: list[str],
    policy: TraversalPolicy,
) -> list[TraversalHit]:
    """
    Execute targeted traversal strictly governed by TraversalPolicy.
    - Enforces rule.min_resolution.
    - Never discards direct exact relationships due to candidate limits.
    - Computes best_hop_distance as minimum supported path distance.
    - Retains rich EdgeEvidence.
    """
    rule_map: dict[str, list[TraversalRule]] = {}
    for r in policy.rules:
        rule_map.setdefault(r.edge_type, []).append(r)

    hits_map: dict[str, TraversalHit] = {}
    seed_set = set(seed_nodes)
    current_frontier = list(seed_nodes)

    fanout = policy.fanout_policy or FanoutPolicy.evaluate(len(seed_nodes), policy.operation)
    max_hops = policy.max_hops
    if not fanout.allow_recursive_expansion and max_hops > 1:
        max_hops = 1

    for hop in range(1, max_hops + 1):
        next_frontier = []

        for curr_node in current_frontier:
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
                if not target_node or target_node in seed_set:
                    continue

                etype = edge.get("edge_type", edge.get("type", "calls"))
                matching_rules = rule_map.get(etype, [])

                # Match rule and check min_resolution
                permitted = False
                multiplier = 1.0
                edge_res = edge.get("resolution", "static_inference")
                edge_rank = RESOLUTION_RANKS.get(edge_res, 3)

                for rule in matching_rules:
                    if rule.max_hops >= hop:
                        if rule.direction in (direction, TraversalDirection.BIDIRECTIONAL):
                            # PHASE 7: Enforce min_resolution ordering
                            min_rank = RESOLUTION_RANKS.get(rule.min_resolution, 3)
                            if edge_rank >= min_rank:
                                permitted = True
                                multiplier = rule.weight_multiplier
                                break

                if not permitted:
                    continue

                # Score calculation
                base_score = 1.0 if edge_res == "static_exact" else 0.7
                hop_decay = 0.6 ** hop
                final_score = base_score * multiplier * hop_decay

                # Build EdgeEvidence (PHASE 8)
                evidence = EdgeEvidence(
                    source=curr_node,
                    target=target_node,
                    edge_type=etype,
                    resolution=edge_res,
                    direction=direction.value,
                    hop=hop,
                    policy_weight=multiplier,
                    path_score=final_score,
                )

                # Check candidate limits (PHASE 5):
                # Direct exact relationships must NEVER be discarded due to candidate counts
                is_direct_exact = (hop == 1 and edge_res == "static_exact")
                if not is_direct_exact:
                    if len(hits_map) >= fanout.max_indirect_candidates:
                        continue

                # PHASE 9: best_hop_distance = minimum supported path distance
                if target_node in hits_map:
                    hit = hits_map[target_node]
                    if hop < hit.best_hop_distance:
                        hit.best_hop_distance = hop
                    if final_score > hit.best_traversal_score:
                        hit.best_traversal_score = final_score
                    hit.paths.append([curr_node, target_node])
                    hit.edge_evidence.append(evidence)
                    if edge_res not in hit.resolution_classes:
                        hit.resolution_classes.append(edge_res)
                    if etype not in hit.edge_types:
                        hit.edge_types.append(etype)
                else:
                    hit = TraversalHit(
                        node_id=target_node,
                        best_hop_distance=hop,
                        best_traversal_score=final_score,
                        paths=[[curr_node, target_node]],
                        edge_evidence=[evidence],
                        resolution_classes=[edge_res],
                        edge_types=[etype],
                    )
                    hits_map[target_node] = hit
                    next_frontier.append(target_node)

        current_frontier = next_frontier
        if not current_frontier:
            break

    return list(hits_map.values())
