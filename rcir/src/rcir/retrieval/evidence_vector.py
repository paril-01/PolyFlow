"""
RCIR v8.1 — Evidence Vector Model (PHASES 8, 12, 13, 14, 15, 16).

Builds multi-source evidence vectors for each retrieved candidate:
- Separates entity identity resolution from dependency relationship resolution (PHASE 13)
- Implements real type compatibility (PHASE 14)
- Uses pluggable ModuleResolver eliminating repository-specific hardcoding (PHASE 15 & 16)
- Preserves traversal scores and edge provenance for ranker consumption (PHASE 8 & 12)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from rcir.entities.module import ModuleResolver
from rcir.adapters.nextcloud import NextcloudModuleResolver
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.retrieval.candidate_generator import CandidateRecord


@dataclass
class EvidenceVector:
    """Rich evidence vector representing all signals for a candidate."""
    entity_id: str
    file_path: str
    entity_match: str = "none"           # exact | partial | none
    resolution_class: str = "unknown"    # static_exact | static_inference | dynamic_unresolved | unsupported | unknown
    edge_types: list[str] = field(default_factory=list)
    type_compatibility: str = "unknown"  # exact | compatible | incompatible | unknown
    change_type_compatibility: str = "medium"  # high | medium | low | contradiction
    boundary_contract: str = "none"      # route_matched | event_registered | cross_stack | none
    lexical_score: float = 0.0
    traversal_score: float = 0.0
    module_distance: int = 0             # 0: same module, 1: sibling, 2: cross-module/distant
    hop_distance: int = 0
    historical_cochange: float = 0.0
    test_relationship: str = "none"      # direct_test | test_utility | none
    runtime_evidence: bool = False
    hub_degree: int = 0
    contradictions: list[str] = field(default_factory=list)
    source_evidence_records: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_match": self.entity_match,
            "resolution_class": self.resolution_class,
            "edge_types": list(self.edge_types),
            "type_compatibility": self.type_compatibility,
            "change_type_compatibility": self.change_type_compatibility,
            "boundary_contract": self.boundary_contract,
            "lexical_score": round(self.lexical_score, 4),
            "traversal_score": round(self.traversal_score, 4),
            "module_distance": self.module_distance,
            "hop_distance": self.hop_distance,
            "historical_cochange": round(self.historical_cochange, 4),
            "test_relationship": self.test_relationship,
            "runtime_evidence": self.runtime_evidence,
            "contradictions": list(self.contradictions),
            "source_evidence_records": list(self.source_evidence_records),
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
        module_resolver: ModuleResolver | None = None,
        type_flow_index: Any | None = None,
    ) -> EvidenceVector:
        resolver = module_resolver or ModuleResolver()

        vec = EvidenceVector(
            entity_id=candidate.entity_id,
            file_path=candidate.file_path,
            hop_distance=candidate.best_hop_distance,
            edge_types=list(candidate.edge_types_seen),
            lexical_score=candidate.raw_lexical_score,
            traversal_score=candidate.best_traversal_score,
            source_evidence_records=list(getattr(candidate, "source_evidence_records", [])),
        )

        # 1. Entity Match (Identity only)
        if "exact_entity_lookup" in candidate.candidate_sources or "exact_file_lookup" in candidate.candidate_sources:
            vec.entity_match = "exact"
        elif "ambiguous_entity_lookup" in candidate.candidate_sources:
            vec.entity_match = "partial"

        for tf in target_files:
            tf_norm = tf.replace("\\", "/").strip("/")
            if tf_norm == candidate.file_path or tf_norm in candidate.entity_id:
                vec.entity_match = "exact"
                break

        # 2. Resolution Class (PHASE 13: derived strictly from dependency edge evidence)
        if "static_exact" in candidate.resolution_classes:
            vec.resolution_class = "static_exact"
        elif "static_inference" in candidate.resolution_classes:
            vec.resolution_class = "static_inference"
        elif "dynamic_unresolved" in candidate.resolution_classes:
            vec.resolution_class = "dynamic_unresolved"
        elif "unsupported" in candidate.resolution_classes:
            vec.resolution_class = "unsupported"
        elif "boundary_graph" in candidate.candidate_sources:
            vec.resolution_class = "static_inference"
        else:
            vec.resolution_class = "unknown"

        # 3. Type Compatibility (PHASES 20 & 25)
        # Derived strictly from type-system signals, NEVER from filename/path substrings.
        if vec.entity_match == "exact":
            vec.type_compatibility = "exact"
        elif any(et in ("inherits", "implements", "overrides") for et in candidate.edge_types_seen):
            vec.type_compatibility = "compatible"
        elif type_flow_index:
            vec.type_compatibility = type_flow_index.check_compatibility(spec.target_entities, candidate.entity_id)
        else:
            vec.type_compatibility = "unknown"

        # 4. Boundary Contract
        if "boundary_graph" in candidate.candidate_sources or "route" in candidate.edge_types_seen:
            vec.boundary_contract = "route_matched"
        elif "cross_boundary" in candidate.edge_types_seen:
            vec.boundary_contract = "cross_stack"

        # 5. Test Relationship
        file_lower = candidate.file_path.lower()
        if "test" in file_lower or "tests/" in file_lower:
            for target in spec.target_entities:
                target_base = target.split("::")[-1].replace(".php", "").replace(".ts", "")
                if target_base.lower() in file_lower:
                    vec.test_relationship = "direct_test"
                    break
            if vec.test_relationship == "none":
                vec.test_relationship = "test_utility"

        # 6. Module Distance (PHASE 16: generic resolver)
        if target_files:
            distances = [resolver.compute_module_distance(tf, candidate.file_path) for tf in target_files]
            vec.module_distance = min(distances) if distances else 0
        else:
            vec.module_distance = 0

        # 7. Change-Type Compatibility
        op = spec.operation
        if op == ChangeOperation.ROUTE_CHANGE:
            if "route" in candidate.file_path.lower() or vec.boundary_contract != "none" or vec.entity_match == "exact":
                vec.change_type_compatibility = "high"
            elif vec.test_relationship == "direct_test":
                vec.change_type_compatibility = "high"
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
            if vec.boundary_contract != "none" or "service" in file_lower or "api" in file_lower:
                vec.change_type_compatibility = "high"
            else:
                vec.change_type_compatibility = "low"

        # 8. Hub Degree
        if hub_scores and candidate.entity_id in hub_scores:
            vec.hub_degree = int(hub_scores[candidate.entity_id])

        # 9. Contradiction Detection
        if "vendor/" in candidate.file_path or "3rdparty/" in candidate.file_path:
            vec.contradictions.append("vendor_external_code")

        return vec
