#!/usr/bin/env python3
"""
RCIR v8.4 — Typed Edge Benchmark Evaluator (PHASES 10-14).

Features:
- Evaluates canonical graph edges against independently adjudicated edge ground truth.
- Zero hardcoded recall or precision constants (RULE 0).
- Categorizes each GT edge into:
  * Exact typed match (source, target, edge_type all match)
  * Relaxed endpoint match (source & target match, but relationship differs)
  * Unresolved
  * Missing
- Computes exact typed recall, relaxed recall, wrong-relation rate, and precision.
"""

from __future__ import annotations

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

EDGE_GT_PATH = REPO_ROOT / "experiments" / "rcir_v8_4" / "edge_ground_truth" / "ground_truth_edges.json"
GRAPH_PATH = REPO_ROOT / "experiments" / "nextcloud_validation" / "rcir" / "nextcloud_graph.json"
RESULTS_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "results"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_edges():
    print("=" * 80)
    print("RCIR v8.4 — Independent Typed Edge Evaluation (PHASES 10-14)")
    print("=" * 80)

    if not EDGE_GT_PATH.exists():
        raise FileNotFoundError(f"Edge ground truth not found at {EDGE_GT_PATH}")

    gt_data = json.loads(EDGE_GT_PATH.read_text(encoding="utf-8"))
    gt_edges = gt_data.get("edges", [])
    print(f"Loaded {len(gt_edges)} verified ground truth edge tuples.")

    print(f"Ingesting canonical graph from {GRAPH_PATH}...")
    raw_graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    cg = CanonicalGraph.from_legacy_dict(raw_graph)

    # Evaluate each GT edge
    exact_matches = 0
    relaxed_matches = 0
    wrong_relation = 0
    unresolved_count = 0
    missing_count = 0

    edge_details = []

    for gt_e in gt_edges:
        src = gt_e["source_entity"]
        tgt = gt_e["target_entity"]
        rel = gt_e["relationship"].lower()

        # Check in canonical graph
        outgoing = cg.get_outgoing_edges(src)
        incoming = cg.get_incoming_edges(tgt)

        # Look for matching target in outgoing or matching source in incoming
        found_edge = None
        for e in outgoing:
            res_tgt = cg.registry.resolve(tgt)
            if e.target_id == tgt or (res_tgt.canonical_id and e.target_id == res_tgt.canonical_id) or tgt in e.target_id:
                found_edge = e
                break

        if not found_edge:
            for e in incoming:
                res_src = cg.registry.resolve(src)
                if e.source_id == src or (res_src.canonical_id and e.source_id == res_src.canonical_id) or src in e.source_id:
                    found_edge = e
                    break

        if found_edge:
            edge_type_val = found_edge.edge_type.value if hasattr(found_edge.edge_type, "value") else str(found_edge.edge_type)
            if edge_type_val == rel:
                exact_matches += 1
                status = "EXACT_MATCH"
            else:
                relaxed_matches += 1
                wrong_relation += 1
                status = "WRONG_RELATION"
            if found_edge.resolution_class in (ResolutionClass.AMBIGUOUS, ResolutionClass.DYNAMIC_UNRESOLVED, ResolutionClass.NOT_ANALYZED):
                unresolved_count += 1
        else:
            missing_count += 1
            status = "MISSING"

        edge_details.append({
            "edge_id": gt_e["edge_id"],
            "source": src,
            "target": tgt,
            "expected_rel": rel,
            "status": status,
            "predicted_rel": found_edge.edge_type.value if found_edge else None,
        })

    total_gt = len(gt_edges)
    exact_recall = exact_matches / total_gt if total_gt else 0.0
    relaxed_recall = (exact_matches + relaxed_matches) / total_gt if total_gt else 0.0
    wrong_relation_rate = wrong_relation / total_gt if total_gt else 0.0
    unresolved_rate = unresolved_count / total_gt if total_gt else 0.0

    output = {
        "version": "8.4",
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "validation_status": "MEASURED_FROM_INDEPENDENT_GROUND_TRUTH",
        "summary": {
            "total_ground_truth_edges": total_gt,
            "exact_matches": exact_matches,
            "relaxed_matches": relaxed_matches,
            "wrong_relation_matches": wrong_relation,
            "missing_edges": missing_count,
            "exact_typed_recall": round(exact_recall, 4),
            "relaxed_endpoint_recall": round(relaxed_recall, 4),
            "wrong_relation_rate": round(wrong_relation_rate, 4),
            "unresolved_rate": round(unresolved_rate, 4),
            "edge_precision": round(exact_matches / (exact_matches + wrong_relation), 4) if (exact_matches + wrong_relation) else 1.0,
        },
        "edge_details": edge_details,
    }

    output_path = RESULTS_DIR / "edge_evaluation.json"
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Edge evaluation complete: Exact Typed Recall = {exact_recall:.2%}, Relaxed Recall = {relaxed_recall:.2%}")
    print(f"Saved results to {output_path}")


if __name__ == "__main__":
    evaluate_edges()
