"""
RCIR v8 — Deterministic Ranker & Pruner (PHASE 10).

Scores evidence vectors transparently using explicit linear features,
prunes hard contradictions, and produces ordered rankings.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from rcir.retrieval.evidence_vector import EvidenceVector


@dataclass
class ScoreBreakdown:
    """Transparent logging of all scoring components for a candidate."""
    exact_entity_score: float = 0.0
    static_edge_score: float = 0.0
    change_type_compat_score: float = 0.0
    boundary_contract_score: float = 0.0
    test_rel_score: float = 0.0
    lexical_score: float = 0.0
    module_distance_penalty: float = 0.0
    hop_penalty: float = 0.0
    hub_penalty: float = 0.0
    ambiguity_penalty: float = 0.0
    total_score: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "exact_entity": round(self.exact_entity_score, 2),
            "static_edge": round(self.static_edge_score, 2),
            "change_type_compat": round(self.change_type_compat_score, 2),
            "boundary_contract": round(self.boundary_contract_score, 2),
            "test_rel": round(self.test_rel_score, 2),
            "lexical": round(self.lexical_score, 2),
            "module_penalty": round(self.module_distance_penalty, 2),
            "hop_penalty": round(self.hop_penalty, 2),
            "hub_penalty": round(self.hub_penalty, 2),
            "ambiguity_penalty": round(self.ambiguity_penalty, 2),
            "total": round(self.total_score, 2),
        }


@dataclass
class RankedCandidate:
    """A scored and ranked candidate."""
    rank: int
    entity_id: str
    file_path: str
    total_score: float
    evidence: EvidenceVector
    breakdown: ScoreBreakdown

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "entity_id": self.entity_id,
            "file_path": self.file_path,
            "total_score": round(self.total_score, 3),
            "breakdown": self.breakdown.to_dict(),
            "evidence": self.evidence.to_dict(),
        }


class DeterministicRanker:
    """Deterministic, transparent multi-factor ranker and hard contradiction pruner."""

    # Weights
    W_EXACT_ENTITY = 100.0
    W_STATIC_EXACT = 35.0
    W_STATIC_INFERRED = 15.0
    W_CHANGE_COMPAT_HIGH = 30.0
    W_CHANGE_COMPAT_MED = 10.0
    W_BOUNDARY_CONTRACT = 40.0
    W_DIRECT_TEST = 25.0
    W_TEST_UTIL = 5.0
    W_LEXICAL_SCALE = 8.0

    # Penalties
    P_HOP_PER_STEP = 12.0
    P_MODULE_STEP = 15.0
    P_HUB_LOG_SCALE = 3.0
    P_AMBIGUITY = 25.0

    def score_vector(self, vec: EvidenceVector) -> tuple[float, ScoreBreakdown]:
        """Compute transparent total score and component breakdown."""
        sb = ScoreBreakdown()

        # 1. Exact entity match
        if vec.entity_match == "exact":
            sb.exact_entity_score = self.W_EXACT_ENTITY
        elif vec.entity_match == "partial":
            sb.exact_entity_score = self.W_EXACT_ENTITY * 0.3
            sb.ambiguity_penalty = -self.P_AMBIGUITY

        # 2. Static edge / Resolution class
        if vec.resolution_class == "static_exact":
            sb.static_edge_score = self.W_STATIC_EXACT
        elif vec.resolution_class == "static_inference":
            sb.static_edge_score = self.W_STATIC_INFERRED

        # 3. Change-Type Compatibility
        if vec.change_type_compatibility == "high":
            sb.change_type_compat_score = self.W_CHANGE_COMPAT_HIGH
        elif vec.change_type_compatibility == "medium":
            sb.change_type_compat_score = self.W_CHANGE_COMPAT_MED

        # 4. Boundary Contract
        if vec.boundary_contract != "none":
            sb.boundary_contract_score = self.W_BOUNDARY_CONTRACT

        # 5. Test Relationship
        if vec.test_relationship == "direct_test":
            sb.test_rel_score = self.W_DIRECT_TEST
        elif vec.test_relationship == "test_utility":
            sb.test_rel_score = self.W_TEST_UTIL

        # 6. Lexical score
        sb.lexical_score = vec.lexical_score * self.W_LEXICAL_SCALE

        # 7. Hop Distance Penalty
        if vec.hop_distance > 0:
            sb.hop_penalty = - (vec.hop_distance * self.P_HOP_PER_STEP)

        # 8. Module Distance Penalty
        if vec.module_distance > 0:
            sb.module_distance_penalty = - (vec.module_distance * self.P_MODULE_STEP)

        # 9. Hub Penalty (log-damped)
        if vec.hub_degree > 10:
            sb.hub_penalty = - (math.log10(vec.hub_degree) * self.P_HUB_LOG_SCALE)

        sb.total_score = (
            sb.exact_entity_score +
            sb.static_edge_score +
            sb.change_type_compat_score +
            sb.boundary_contract_score +
            sb.test_rel_score +
            sb.lexical_score +
            sb.hop_penalty +
            sb.module_distance_penalty +
            sb.hub_penalty +
            sb.ambiguity_penalty
        )

        return sb.total_score, sb

    def rank(
        self,
        vectors: list[EvidenceVector],
        prune_contradictions: bool = True,
    ) -> list[RankedCandidate]:
        """Filter contradictions and rank candidates by descending score."""
        scored: list[tuple[float, EvidenceVector, ScoreBreakdown]] = []

        for vec in vectors:
            # Hard contradiction pruning
            if prune_contradictions and vec.contradictions:
                continue

            score, breakdown = self.score_vector(vec)
            scored.append((score, vec, breakdown))

        # Sort descending by score; tie-break deterministically by entity_id
        scored.sort(key=lambda item: (-item[0], item[1].entity_id))

        ranked: list[RankedCandidate] = []
        for idx, (score, vec, breakdown) in enumerate(scored, 1):
            ranked.append(RankedCandidate(
                rank=idx,
                entity_id=vec.entity_id,
                file_path=vec.file_path,
                total_score=score,
                evidence=vec,
                breakdown=breakdown,
            ))

        return ranked
