"""
RCIR v8.2 — Semantic Cascaded Ranker & Operation Profiles (PHASES 11, 12, 13, 14, 17, 18, 19).

Features:
- Explicit boolean RankerConfig switches (isolated zero-baseline R0-R7 ablations)
- Strict BM25 isolation (zero lexical score when use_bm25=False)
- OperationRankerProfile tailoring weights to change operations
- Cascaded Ranking: semantic buckets (A0-A7) ensuring verified callers outrank lexical matches
- Diversity-aware reranking constraining module concentration in Plane B
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional

from rcir.query.change_spec import ChangeOperation
from rcir.retrieval.evidence_vector import EvidenceVector


@dataclass
class RankerConfig:
    """Explicit configuration switches for ablation control and feature gating."""
    use_entity_identity: bool = True
    use_edge_resolution: bool = True
    use_traversal_score: bool = True
    use_type_compatibility: bool = True
    use_change_compatibility: bool = True
    use_boundary_contract: bool = True
    use_bm25: bool = True
    use_module_distance: bool = True
    use_test_relationship: bool = True
    use_historical: bool = True
    use_hub_penalty: bool = True
    use_cascaded_ranking: bool = True
    use_diversity: bool = False
    max_per_module: int = 5


@dataclass
class OperationRankerProfile:
    """Weight profile tailored to a specific change operation (PHASE 17 & 44)."""
    operation: str = ""
    w_exact_entity: float = 100.0
    w_static_exact: float = 40.0
    w_static_inferred: float = 15.0
    w_type_exact: float = 25.0
    w_type_compat: float = 12.0
    w_change_compat_high: float = 30.0
    w_change_compat_med: float = 10.0
    w_boundary_contract: float = 40.0
    w_direct_test: float = 30.0
    w_test_util: float = 5.0
    w_traversal: float = 20.0
    w_lexical_scale: float = 8.0
    w_historical: float = 15.0
    p_hop_per_step: float = 10.0
    p_module_step: float = 2.0  # Calibrated to avoid penalizing valid cross-module consumers
    p_hub_log_scale: float = 3.0
    p_ambiguity: float = 25.0
    p_type_incompat: float = 50.0

    @classmethod
    def for_operation(cls, operation: ChangeOperation | str | None) -> OperationRankerProfile:
        if not operation:
            return cls(operation="default")
        op_str = operation.value if hasattr(operation, "value") else str(operation).lower()

        if op_str == "route_change":
            return cls(
                operation=op_str,
                w_boundary_contract=50.0,
                w_static_exact=35.0,
                w_direct_test=25.0,
                w_lexical_scale=3.0,
                p_module_step=1.0,
            )
        elif op_str == "signature_change":
            return cls(
                operation=op_str,
                w_static_exact=50.0,
                w_type_exact=35.0,
                w_type_compat=20.0,
                w_direct_test=35.0,
                p_module_step=0.0,  # Zero cross-module penalty for signature changes
            )
        elif op_str == "event_change":
            return cls(
                operation=op_str,
                w_boundary_contract=45.0,
                w_static_exact=40.0,
                w_change_compat_high=35.0,
                p_module_step=1.0,
            )
        elif op_str == "config_change":
            return cls(
                operation=op_str,
                w_boundary_contract=45.0,
                w_static_exact=35.0,
                p_module_step=0.5,
            )
        elif op_str == "service_boundary_change":
            return cls(
                operation=op_str,
                w_boundary_contract=55.0,
                w_static_exact=40.0,
                p_module_step=0.0,
            )
        return cls(operation=op_str)


@dataclass
class ScoreBreakdown:
    """Transparent logging of all scoring components for a candidate."""
    exact_entity_score: float = 0.0
    static_edge_score: float = 0.0
    type_compat_score: float = 0.0
    change_type_compat_score: float = 0.0
    boundary_contract_score: float = 0.0
    test_rel_score: float = 0.0
    traversal_score: float = 0.0
    lexical_score: float = 0.0
    historical_score: float = 0.0
    module_distance_penalty: float = 0.0
    hop_penalty: float = 0.0
    hub_penalty: float = 0.0
    ambiguity_penalty: float = 0.0
    semantic_bucket: str = "A7"
    total_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "exact_entity": round(self.exact_entity_score, 2),
            "static_edge": round(self.static_edge_score, 2),
            "type_compat": round(self.type_compat_score, 2),
            "change_type_compat": round(self.change_type_compat_score, 2),
            "boundary_contract": round(self.boundary_contract_score, 2),
            "test_rel": round(self.test_rel_score, 2),
            "traversal": round(self.traversal_score, 2),
            "lexical": round(self.lexical_score, 2),
            "historical": round(self.historical_score, 2),
            "module_penalty": round(self.module_distance_penalty, 2),
            "hop_penalty": round(self.hop_penalty, 2),
            "hub_penalty": round(self.hub_penalty, 2),
            "ambiguity_penalty": round(self.ambiguity_penalty, 2),
            "semantic_bucket": self.semantic_bucket,
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

    # Backward compatibility class weights
    W_EXACT_ENTITY = 100.0
    W_STATIC_EXACT = 40.0
    W_STATIC_INFERRED = 15.0
    W_TYPE_EXACT = 25.0
    W_TYPE_COMPAT = 12.0
    W_CHANGE_COMPAT_HIGH = 30.0
    W_CHANGE_COMPAT_MED = 10.0
    W_BOUNDARY_CONTRACT = 40.0
    W_DIRECT_TEST = 30.0
    W_TEST_UTIL = 5.0
    W_TRAVERSAL = 20.0
    W_LEXICAL_SCALE = 8.0
    W_HISTORICAL = 15.0

    def __init__(
        self,
        config: RankerConfig | None = None,
        profile: OperationRankerProfile | None = None,
    ):
        self.config = config or RankerConfig()
        self.profile = profile or OperationRankerProfile()

    def classify_bucket(self, vec: EvidenceVector) -> str:
        """Assign candidate to semantic priority bucket A0-A7 (PHASE 18)."""
        # A0: Explicit target
        if vec.entity_match == "exact":
            return "A0"

        # A2: Typed interface/implementation/override (Section 6.4: prioritized for contract/signature impact)
        if any(et in ("implements", "inherits", "overrides") for et in vec.edge_types):
            return "A2"

        # A1: Direct static-exact dependency
        if vec.resolution_class == "static_exact" and vec.hop_distance <= 1:
            return "A1"

        # A3: Direct boundary contract
        if vec.boundary_contract != "none":
            return "A3"

        # A4: Direct verification/test relation
        if vec.test_relationship == "direct_test":
            return "A4"

        # A5: Static inferred relationship
        if vec.resolution_class == "static_inference" and vec.hop_distance <= 1:
            return "A5"

        # A6: Indirect relation
        if vec.hop_distance > 1:
            return "A6"

        # A7: Lexical-only or peripheral candidate
        return "A7"

    def score_vector(self, vec: EvidenceVector) -> tuple[float, ScoreBreakdown]:
        """Compute transparent total score and component breakdown obeying explicit config."""
        sb = ScoreBreakdown()
        p = self.profile
        cfg = self.config

        sb.semantic_bucket = self.classify_bucket(vec)

        # 1. Exact entity match (Identity)
        if cfg.use_entity_identity:
            if vec.entity_match == "exact":
                sb.exact_entity_score = p.w_exact_entity
            elif vec.entity_match == "partial":
                sb.exact_entity_score = p.w_exact_entity * 0.3
                sb.ambiguity_penalty = -p.p_ambiguity

        # 2. Static edge / Resolution class (Relationship)
        if cfg.use_edge_resolution:
            if vec.resolution_class == "static_exact":
                sb.static_edge_score = p.w_static_exact
            elif vec.resolution_class == "static_inference":
                sb.static_edge_score = p.w_static_inferred

        # 3. Type Compatibility (PHASE 14 & 20)
        if cfg.use_type_compatibility:
            if vec.type_compatibility == "exact":
                sb.type_compat_score = p.w_type_exact
            elif vec.type_compatibility == "compatible":
                sb.type_compat_score = p.w_type_compat
            elif vec.type_compatibility == "incompatible":
                sb.type_compat_score = -p.p_type_incompat

        # 4. Change-Type Compatibility
        if cfg.use_change_compatibility:
            if vec.change_type_compatibility == "high":
                sb.change_type_compat_score = p.w_change_compat_high
            elif vec.change_type_compatibility == "medium":
                sb.change_type_compat_score = p.w_change_compat_med

        # 5. Boundary Contract
        if cfg.use_boundary_contract:
            if vec.boundary_contract != "none":
                sb.boundary_contract_score = p.w_boundary_contract

        # 6. Test Relationship
        if cfg.use_test_relationship:
            if vec.test_relationship == "direct_test":
                sb.test_rel_score = p.w_direct_test
            elif vec.test_relationship == "test_utility":
                sb.test_rel_score = p.w_test_util

        # 7. Traversal Evidence (PHASE 12)
        if cfg.use_traversal_score:
            sb.traversal_score = vec.traversal_score * p.w_traversal

        # 8. Lexical score (PHASE 12: strictly zero when BM25 disabled)
        if cfg.use_bm25:
            sb.lexical_score = vec.lexical_score * p.w_lexical_scale
        else:
            sb.lexical_score = 0.0

        # 9. Historical co-change
        if cfg.use_historical and vec.historical_cochange > 0:
            sb.historical_score = vec.historical_cochange * p.w_historical

        # 10. Hop Distance Penalty
        if vec.hop_distance > 0:
            sb.hop_penalty = - (vec.hop_distance * p.p_hop_per_step)

        # 11. Module Distance Penalty
        if cfg.use_module_distance and vec.module_distance > 0:
            sb.module_distance_penalty = - (vec.module_distance * p.p_module_step)

        # 12. Hub Penalty (log-damped, Section 6.5: damp generic hubs unless direct exact/typed evidence)
        if cfg.use_hub_penalty and vec.hub_degree > 10:
            is_direct_exact = (vec.resolution_class == "static_exact" and vec.hop_distance <= 1)
            is_typed = any(et in ("implements", "inherits", "overrides") for et in vec.edge_types)
            if not is_direct_exact and not is_typed:
                sb.hub_penalty = - (math.log10(vec.hub_degree) * p.p_hub_log_scale)

        sb.total_score = (
            sb.exact_entity_score +
            sb.static_edge_score +
            sb.type_compat_score +
            sb.change_type_compat_score +
            sb.boundary_contract_score +
            sb.test_rel_score +
            sb.traversal_score +
            sb.lexical_score +
            sb.historical_score +
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
        """Rank candidates using cascaded semantic buckets or linear score."""
        scored: list[tuple[float, EvidenceVector, ScoreBreakdown]] = []

        for vec in vectors:
            if prune_contradictions and vec.contradictions:
                continue

            score, breakdown = self.score_vector(vec)
            scored.append((score, vec, breakdown))

        if self.config.use_cascaded_ranking:
            # PHASE 44: Operation-specific Cascaded Ranking across semantic buckets
            op = getattr(self.profile, "operation", "")
            if op == "signature_change":
                bucket_order = ["A0", "A2", "A1", "A4", "A5", "A6", "A3", "A7"]
            elif op == "route_change":
                bucket_order = ["A0", "A3", "A1", "A4", "A5", "A2", "A6", "A7"]
            elif op in ("event_change", "service_boundary_change"):
                bucket_order = ["A0", "A3", "A1", "A4", "A2", "A5", "A6", "A7"]
            elif op == "config_change":
                bucket_order = ["A0", "A3", "A1", "A4", "A5", "A6", "A2", "A7"]
            else:
                bucket_order = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7"]

            buckets: dict[str, list[tuple[float, EvidenceVector, ScoreBreakdown]]] = {b: [] for b in bucket_order}

            for item in scored:
                b = item[2].semantic_bucket
                buckets.setdefault(b, []).append(item)

            ordered: list[tuple[float, EvidenceVector, ScoreBreakdown]] = []
            for b in bucket_order:
                b_items = buckets.get(b, [])
                # Rank within bucket by descending score, tie-break by entity_id
                b_items.sort(key=lambda x: (-x[0], x[1].entity_id))
                ordered.extend(b_items)
            scored = ordered
        else:
            # Flat linear sort
            scored.sort(key=lambda item: (-item[0], item[1].entity_id))

        if self.config.use_diversity:
            # PHASE 19: Diversity-aware reranking (max entries per module)
            module_counts: dict[str, int] = {}
            primary_pool = []
            deferred_pool = []
            for item in scored:
                file_path = item[1].file_path
                mod = file_path.split("/")[0] if "/" in file_path else "root"
                cnt = module_counts.get(mod, 0)
                if cnt < self.config.max_per_module:
                    module_counts[mod] = cnt + 1
                    primary_pool.append(item)
                else:
                    deferred_pool.append(item)
            scored = primary_pool + deferred_pool

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


class MultiObjectiveRanker:
    """
    Multi-objective deterministic ranker combining:
    - Anchor Quality: First-hit precision & MRR via cascaded operation profile
    - Coverage Quality: Broad structural coverage & nDCG via linear ranker
    Fuses objectives using deterministic Reciprocal Rank Fusion (RRF) (PHASE 43).
    """

    def __init__(self, operation: ChangeOperation | str | None = None):
        self.anchor_ranker = DeterministicRanker(
            RankerConfig(use_cascaded_ranking=True, use_diversity=False),
            profile=OperationRankerProfile.for_operation(operation),
        )
        self.coverage_ranker = DeterministicRanker(
            RankerConfig(use_cascaded_ranking=False, use_diversity=True, max_per_module=6),
            profile=OperationRankerProfile.for_operation(operation),
        )

    def rank(
        self,
        vectors: list[EvidenceVector],
        prune_contradictions: bool = True,
    ) -> list[RankedCandidate]:
        if not vectors:
            return []

        anchor_ranked = self.anchor_ranker.rank(vectors, prune_contradictions=prune_contradictions)
        coverage_ranked = self.coverage_ranker.rank(vectors, prune_contradictions=prune_contradictions)

        anchor_ranks = {cand.entity_id: cand.rank for cand in anchor_ranked}
        coverage_ranks = {cand.entity_id: cand.rank for cand in coverage_ranked}

        vec_map = {v.entity_id: v for v in vectors}
        breakdown_map = {cand.entity_id: cand.breakdown for cand in anchor_ranked}

        # Compute RRF score
        rrf_scores: list[tuple[float, str]] = []
        k = 60.0
        for eid in anchor_ranks:
            r_a = anchor_ranks[eid]
            r_c = coverage_ranks.get(eid, len(vectors) + 1)
            score = (1.0 / (k + r_a)) + (1.0 / (k + r_c))
            rrf_scores.append((score, eid))

        rrf_scores.sort(key=lambda item: (-item[0], item[1]))

        fused: list[RankedCandidate] = []
        for idx, (fused_score, eid) in enumerate(rrf_scores, 1):
            vec = vec_map[eid]
            fused.append(RankedCandidate(
                rank=idx,
                entity_id=eid,
                file_path=vec.file_path,
                total_score=round(fused_score, 5),
                evidence=vec,
                breakdown=breakdown_map.get(eid, ScoreBreakdown()),
            ))

        return fused
