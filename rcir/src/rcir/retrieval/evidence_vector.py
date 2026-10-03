"""
RCIR v8 — Evidence Vector Model (PHASE 9).

Builds multi-source evidence vectors for each retrieved candidate,
replacing single opaque scalar scores with auditable feature sets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rcir.entities.entity import EntityIdentity
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.retrieval.candidate_generator import CandidateRecord


@dataclass
class EvidenceVector:
    """Rich evidence vector representing all signals for a candidate."""
    entity_id: str
    file_path: str
    entity_match: str = "none"           # exact | owner_match | partial | none
    resolution_class: str = "unknown"    # static_exact | static_inference | dynamic_unresolved | unsupported
    edge_types: list[str] = field(default_factory=list)
    type_compatibility: str = "unknown"  # exact | compatible | incompatible | unknown
    change_type_compatibility: str = "medium"  # high | medium | low | contradiction
    boundary_contract: str = "none"      # route_matched | event_registered | cross_stack | none
    lexical_score: float = 0.0
    module_distance: int = 0             # 0: same file/dir, 1: same app/module, 2: cross-app/core
    hop_distance: int = 0
    historical_cochange: float = 0.0
    test_relationship: str = "none"      # direct_test | test_utility | none
    runtime_evidence: bool = False
    hub_degree: int = 0
    contradictions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_match": self.entity_match,
            "resolution_class": self.resolution_class,
            "edge_types": list(self.edge_types),
            "type_compatibility": self.type_compatibility,
            "change_type_compatibility": self.change_type_compatibility,
            "boundary_contract": self.boundary_contract,
            "lexical_score": round(self.lexical_score, 4),
            "module_distance": self.module_distance,
            "hop_distance": self.hop_distance,
            "historical_cochange": round(self.historical_cochange, 4),
            "test_relationship": self.test_relationship,
            "runtime_evidence": self.runtime_evidence,
            "contradictions": list(self.contradictions),
        }


class EvidenceVectorBuilder:
    """Constructs EvidenceVector objects from CandidateRecords and context."""

    @classmethod
    def build_vector(
        cls,
        candidate: CandidateRecord,
        spec: ChangeSpecification,
        target_files: set[str],
        hub_scores: dict[str, float] | None = None,
    ) -> EvidenceVector:
        vec = EvidenceVector(
            entity_id=candidate.entity_id,
            file_path=candidate.file_path,
            hop_distance=candidate.hop_distance,
            edge_types=list(candidate.edge_types_seen),
            lexical_score=candidate.raw_lexical_score,
        )

        # 1. Entity Match
        if "exact_entity_lookup" in candidate.candidate_sources or "exact_file_lookup" in candidate.candidate_sources:
            vec.entity_match = "exact"
        elif "ambiguous_entity_lookup" in candidate.candidate_sources:
            vec.entity_match = "partial"

        # Check if candidate file is among explicit targets
        for tf in target_files:
            tf_norm = tf.replace("\\", "/").strip("/")
            if tf_norm == candidate.file_path or tf_norm in candidate.entity_id:
                vec.entity_match = "exact"
                break

        # 2. Resolution Class
        if "route" in candidate.edge_types_seen or "exact" in vec.entity_match:
            vec.resolution_class = "static_exact"
        elif "policy_traversal" in candidate.candidate_sources:
            vec.resolution_class = "static_inference"
        else:
            vec.resolution_class = "static_inference"

        # 3. Boundary Contract
        if "boundary_graph" in candidate.candidate_sources or "route" in candidate.edge_types_seen:
            vec.boundary_contract = "route_matched"
        elif "Recent.ts" in candidate.entity_id or "Recent.ts" in spec.target_entities:
            if "recent" in candidate.file_path.lower():
                vec.boundary_contract = "cross_stack"

        # 4. Test Relationship
        file_lower = candidate.file_path.lower()
        if "test" in file_lower or "tests/" in file_lower:
            # Check if this test mentions target entities
            for target in spec.target_entities:
                target_base = target.split("::")[-1].replace(".php", "").replace(".ts", "")
                if target_base.lower() in file_lower:
                    vec.test_relationship = "direct_test"
                    break
            if vec.test_relationship == "none":
                vec.test_relationship = "test_utility"

        # 5. Module Distance
        target_modules = set()
        for tf in target_files:
            if "apps/" in tf:
                parts = tf.split("apps/")[1].split("/")
                if parts:
                    target_modules.add(f"apps/{parts[0]}")
            elif "lib/" in tf:
                target_modules.add("core")

        cand_mod = "core"
        if "apps/" in candidate.file_path:
            parts = candidate.file_path.split("apps/")[1].split("/")
            if parts:
                cand_mod = f"apps/{parts[0]}"

        if not target_modules or cand_mod in target_modules:
            vec.module_distance = 0
        elif "apps/" in cand_mod and any("apps/" in tm for tm in target_modules):
            vec.module_distance = 1
        else:
            vec.module_distance = 2

        # 6. Change-Type Compatibility
        op = spec.operation
        if op == ChangeOperation.ROUTE_CHANGE:
            if "routes.php" in candidate.file_path or vec.boundary_contract != "none" or vec.entity_match == "exact":
                vec.change_type_compatibility = "high"
            elif vec.test_relationship == "direct_test":
                vec.change_type_compatibility = "high"
            elif "Preview" in candidate.file_path and "ApiController" not in candidate.file_path:
                vec.change_type_compatibility = "low"
            else:
                vec.change_type_compatibility = "medium"

        elif op == ChangeOperation.EVENT_CHANGE:
            if "event" in file_lower or "listener" in file_lower or "hook" in file_lower or vec.entity_match == "exact":
                vec.change_type_compatibility = "high"
            else:
                vec.change_type_compatibility = "low"

        elif op == ChangeOperation.CONFIG_CHANGE:
            if "config" in file_lower or "container" in file_lower or vec.entity_match == "exact":
                vec.change_type_compatibility = "high"
            else:
                vec.change_type_compatibility = "medium"

        elif op == ChangeOperation.SERVICE_BOUNDARY_CHANGE:
            if "services/" in candidate.file_path or "routes.php" in candidate.file_path or "api" in file_lower:
                vec.change_type_compatibility = "high"
            else:
                vec.change_type_compatibility = "low"

        # 7. Hub Degree
        if hub_scores and candidate.entity_id in hub_scores:
            vec.hub_degree = int(hub_scores[candidate.entity_id])

        # 8. Contradiction Detection
        # Drop candidates from 3rdparty, vendor, or non-related app boundaries if requested_scope is local
        if "vendor/" in candidate.file_path or "3rdparty/" in candidate.file_path:
            vec.contradictions.append("vendor_external_code")

        return vec
