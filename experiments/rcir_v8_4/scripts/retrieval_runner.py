#!/usr/bin/env python3
"""
RCIR v8.4 — Decoupled Retrieval Runner (PHASE 76).

Architectural Rule:
This process has NO access to ground truth data or paths.
It strictly ingests the ChangeSpecification from the dataset, searches the CanonicalGraph,
scores candidates via MultiObjectiveRanker, and outputs raw predictions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT))

from rcir.entities.canonical import CanonicalEntityRegistry, CanonicalEntityID, EntityKind
from rcir.graph.canonical_graph import CanonicalGraph, CanonicalEdge, CanonicalEdgeType, ResolutionClass
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.retrieval.evidence_vector import EvidenceVector
from rcir.retrieval.ranker import MultiObjectiveRanker, OperationRankerProfile, RankerConfig, RankedCandidate

DATASETS_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "datasets"
GRAPH_PATH = REPO_ROOT / "experiments" / "nextcloud_validation" / "rcir" / "nextcloud_graph.json"
RAW_RETRIEVAL_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "raw" / "retrieval"

RAW_RETRIEVAL_DIR.mkdir(parents=True, exist_ok=True)


def load_canonical_graph() -> tuple[CanonicalGraph, CanonicalEntityRegistry]:
    print(f"Loading Nextcloud raw dependency graph from {GRAPH_PATH}...")
    t0 = time.time()
    raw_graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    cg = CanonicalGraph.from_legacy_dict(raw_graph)
    print(f"CanonicalGraph built in {time.time() - t0:.2f}s: {len(cg.nodes)} nodes, {cg.ledger.to_dict()['total_evaluated']} evaluated edges.")
    return cg, cg.registry


def run_retrieval(split: str, cg: CanonicalGraph, registry: CanonicalEntityRegistry) -> dict[str, Any]:
    dataset_file = DATASETS_DIR / f"{split}.json"
    if not dataset_file.exists():
        raise FileNotFoundError(f"Dataset split not found: {dataset_file}")

    dataset = json.loads(dataset_file.read_text(encoding="utf-8"))
    tasks = dataset.get("tasks", [])
    print(f"Running decoupled retrieval for split: '{split}' ({len(tasks)} tasks)...")

    predictions: dict[str, Any] = {
        "split": split,
        "version": "8.4",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "task_predictions": {},
    }

    for t_idx, task in enumerate(tasks, 1):
        task_id = task["task_id"]
        spec_data = task["spec"]
        operation_str = spec_data.get("operation", "behavior_change")
        try:
            op = ChangeOperation(operation_str)
        except ValueError:
            op = ChangeOperation.BEHAVIOR_CHANGE

        spec = ChangeSpecification(
            operation=op,
            requested_symbol=spec_data.get("requested_symbol", ""),
            target_file_hint=spec_data.get("target_file_hint"),
            canonical_target_ids=spec_data.get("canonical_target_ids", []),
            description=task.get("description", ""),
        )

        # 1. Target resolution
        target_res = registry.resolve(spec.requested_symbol, target_file_hint=spec.target_file_hint)
        resolved_target_id = target_res.canonical_id or (spec.canonical_target_ids[0] if spec.canonical_target_ids else spec.requested_symbol)

        # 2. Candidate generation
        candidates: dict[str, EvidenceVector] = {}

        # Target candidate
        target_fp = spec.target_file_hint or ""
        if not target_fp and resolved_target_id in cg.nodes:
            target_fp = cg.nodes[resolved_target_id].file

        candidates[resolved_target_id] = EvidenceVector(
            entity_id=resolved_target_id,
            file_path=target_fp,
            entity_match="exact",
            resolution_class="static_exact",
            traversal_score=1.0,
            hop_distance=0,
        )

        # 1-hop incoming and outgoing edges for target and its structural ancestors (file, enclosing class)
        roots = [resolved_target_id]
        if "::" in resolved_target_id:
            owner_id = resolved_target_id.split("::")[0]
            owner_res = registry.resolve(owner_id)
            if owner_res.canonical_id and owner_res.canonical_id not in roots:
                roots.append(owner_res.canonical_id)
        if target_fp:
            file_res = registry.resolve(target_fp)
            if file_res.canonical_id and file_res.canonical_id not in roots:
                roots.append(file_res.canonical_id)

        for root_id in roots:
            incoming = cg.get_incoming_edges(root_id)
            outgoing = cg.get_outgoing_edges(root_id)

            # Direct 1-hop exact relationships are never pruned (Phase 83)
            for e in incoming:
                src_id = e.source_id
                src_node = cg.nodes.get(src_id)
                if not src_node:
                    s_res = registry.resolve(src_id)
                    src_node = cg.nodes.get(s_res.canonical_id) if s_res.canonical_id else None
                src_fp = src_node.file if src_node else src_id.split("::")[0].replace("php://", "").replace("ts://", "").replace("external://", "")

                candidates[src_id] = EvidenceVector(
                    entity_id=src_id,
                    file_path=src_fp,
                    entity_match="alias" if target_res.canonical_id == src_id else "none",
                    resolution_class=e.resolution_class.value,
                    edge_types=[e.edge_type.value],
                    hop_distance=1,
                    traversal_score=0.85,
                )

            for e in outgoing:
                tgt_id = e.target_id
                tgt_node = cg.nodes.get(tgt_id)
                if not tgt_node:
                    t_res = registry.resolve(tgt_id)
                    tgt_node = cg.nodes.get(t_res.canonical_id) if t_res.canonical_id else None
                tgt_fp = tgt_node.file if tgt_node else tgt_id.split("::")[0].replace("php://", "").replace("ts://", "").replace("external://", "")

                if tgt_id not in candidates:
                    candidates[tgt_id] = EvidenceVector(
                        entity_id=tgt_id,
                        file_path=tgt_fp,
                        resolution_class=e.resolution_class.value,
                        edge_types=[e.edge_type.value],
                        hop_distance=1,
                        traversal_score=0.75,
                    )

        # 2-hop bounded expansion (incoming callers and outgoing callee dependencies)
        for direct_cand_id in list(candidates.keys())[:50]:
            for e2 in cg.get_incoming_edges(direct_cand_id)[:15]:
                if e2.source_id not in candidates and len(candidates) < 250:
                    s2_node = cg.nodes.get(e2.source_id)
                    if not s2_node:
                        s2_res = registry.resolve(e2.source_id)
                        s2_node = cg.nodes.get(s2_res.canonical_id) if s2_res.canonical_id else None
                    s2_fp = s2_node.file if s2_node else e2.source_id.split("::")[0].replace("php://", "").replace("ts://", "").replace("external://", "")
                    candidates[e2.source_id] = EvidenceVector(
                        entity_id=e2.source_id,
                        file_path=s2_fp,
                        resolution_class=e2.resolution_class.value,
                        edge_types=[e2.edge_type.value],
                        hop_distance=2,
                        traversal_score=0.45,
                    )
            for e2 in cg.get_outgoing_edges(direct_cand_id)[:10]:
                if e2.target_id not in candidates and len(candidates) < 250:
                    t2_node = cg.nodes.get(e2.target_id)
                    if not t2_node:
                        t2_res = registry.resolve(e2.target_id)
                        t2_node = cg.nodes.get(t2_res.canonical_id) if t2_res.canonical_id else None
                    t2_fp = t2_node.file if t2_node else e2.target_id.split("::")[0].replace("php://", "").replace("ts://", "").replace("external://", "")
                    candidates[e2.target_id] = EvidenceVector(
                        entity_id=e2.target_id,
                        file_path=t2_fp,
                        resolution_class=e2.resolution_class.value,
                        edge_types=[e2.edge_type.value],
                        hop_distance=2,
                        traversal_score=0.40,
                    )

        # 3. Score and Rank candidates
        cand_list = list(candidates.values())
        ranker = MultiObjectiveRanker(operation=op)
        ranked = ranker.rank(cand_list)

        # Record raw prediction record
        predictions["task_predictions"][task_id] = {
            "task_id": task_id,
            "target_entity": resolved_target_id,
            "candidates_count": len(ranked),
            "ranked_candidates": [c.to_dict() for c in ranked],
            "predicted_files": sorted(list({c.file_path for c in ranked if c.file_path})),
        }

    output_path = RAW_RETRIEVAL_DIR / f"{split}_predictions.json"
    output_path.write_text(json.dumps(predictions, indent=2), encoding="utf-8")
    print(f"Saved {len(tasks)} task predictions to {output_path}")
    return predictions


def main():
    parser = argparse.ArgumentParser(description="RCIR v8.4 Decoupled Retrieval Runner")
    parser.add_argument("--split", choices=["dev", "validation", "test", "all"], default="all")
    args = parser.parse_args()

    cg, registry = load_canonical_graph()

    splits = ["dev", "validation", "test"] if args.split == "all" else [args.split]
    for s in splits:
        run_retrieval(s, cg, registry)

    print("All retrieval predictions successfully generated.")


if __name__ == "__main__":
    main()
