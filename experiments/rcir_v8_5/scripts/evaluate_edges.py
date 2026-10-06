"""
RCIR v8.5 — Typed Edge Ground Truth Evaluator (PHASES 15-20, 85).

Features:
- Replaces substring matching with strict exact canonical endpoint equality:
  canonical_source_id == expected_source and canonical_target_id == expected_target.
- Distinctly evaluates implements, inherits, calls, injects, route_to_controller, event_dispatch, config_reads, source_to_test.
- Tests hard negative edges (verifying non-existence of invalid edges).
- Implements formal precision logic or explicit NOT_MEASURED status.
- Generates results/edge_evaluation.json and raw/edge_eval/predicted_edges.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from environment import get_default_environment

env = get_default_environment()
sys.path.insert(0, str(env.polyflow_root / "rcir" / "src"))

from rcir.graph.canonical_graph import CanonicalGraph, CanonicalEdgeType


def evaluate_edges():
    print("=" * 80)
    print("RCIR v8.5 — Typed Edge Ground Truth Evaluation (PHASES 15-20, 85)")
    print("=" * 80)

    edge_gt_path = env.edge_ground_truth_root / "ground_truth_edges.json"
    if not edge_gt_path.exists():
        raise FileNotFoundError(f"Missing edge ground truth at {edge_gt_path}")

    gt_data = json.loads(edge_gt_path.read_text(encoding="utf-8"))
    gt_edges = gt_data["edges"]
    print(f"Loaded {len(gt_edges)} verified ground truth edge specifications.")

    print(f"Loading CanonicalGraph from {env.graph_path}...")
    raw_graph = json.loads(env.graph_path.read_text(encoding="utf-8"))
    cg = CanonicalGraph.from_legacy_dict(raw_graph, target_repo_root=env.target_repo_root)

    # Positive and negative edge evaluation
    pos_exact = 0
    pos_relaxed = 0
    pos_wrong_relation = 0
    pos_missing = 0
    neg_correct = 0
    neg_violated = 0

    edge_eval_records = []
    predicted_edges_dump = []

    for gt_e in gt_edges:
        src = gt_e["source"]
        tgt = gt_e["target"]
        expected_et = gt_e["edge_type"]
        is_pos = gt_e.get("is_positive", True)

        # Look for exact outgoing edges
        out_edges = cg.get_outgoing_edges(src)
        for oe in out_edges:
            predicted_edges_dump.append({
                "source": oe.source_id,
                "target": oe.target_id,
                "edge_type": oe.edge_type.value if hasattr(oe.edge_type, "value") else str(oe.edge_type),
                "resolution": oe.resolution_class.value if hasattr(oe.resolution_class, "value") else str(oe.resolution_class),
            })

        # STRICT EXACT MATCHING (PHASE 18)
        # Check if any outgoing edge matches exact canonical endpoints
        matched_exact_typed = False
        matched_relaxed_endpoint = False
        found_wrong_rel = None

        for oe in out_edges:
            oe_target = oe.target_id
            oe_type = oe.edge_type.value if hasattr(oe.edge_type, "value") else str(oe.edge_type)

            # Strict canonical equality
            if oe_target == tgt:
                matched_relaxed_endpoint = True
                if oe_type == expected_et:
                    matched_exact_typed = True
                    break
                else:
                    found_wrong_rel = oe_type

        # Also check incoming edges from target if applicable
        if not matched_exact_typed:
            in_edges = cg.get_incoming_edges(tgt)
            for ie in in_edges:
                ie_source = ie.source_id
                ie_type = ie.edge_type.value if hasattr(ie.edge_type, "value") else str(ie.edge_type)
                if ie_source == src:
                    matched_relaxed_endpoint = True
                    if ie_type == expected_et:
                        matched_exact_typed = True
                        break
                    else:
                        found_wrong_rel = ie_type

        if is_pos:
            if matched_exact_typed:
                pos_exact += 1
                pos_relaxed += 1
                status = "CORRECT_EXACT_TYPED"
            elif matched_relaxed_endpoint:
                pos_relaxed += 1
                pos_wrong_relation += 1
                status = f"CORRECT_ENDPOINT_WRONG_RELATION ({found_wrong_rel} vs {expected_et})"
            else:
                pos_missing += 1
                status = "MISSING_IN_GRAPH"
        else:
            # Hard negative test: must NOT exist with that relation
            if matched_exact_typed:
                neg_violated += 1
                status = "NEGATIVE_VIOLATED (Found unexpected edge!)"
            else:
                neg_correct += 1
                status = "CORRECT_NEGATIVE_REJECTION"

        edge_eval_records.append({
            "edge_id": gt_e.get("edge_id"),
            "source": src,
            "target": tgt,
            "expected_edge_type": expected_et,
            "is_positive": is_pos,
            "matched_exact_typed": matched_exact_typed,
            "matched_relaxed_endpoint": matched_relaxed_endpoint,
            "status": status,
        })
        print(f"  [{status}] {src} -> {tgt} ({expected_et})")

    pos_total = sum(1 for e in gt_edges if e.get("is_positive", True))
    neg_total = sum(1 for e in gt_edges if not e.get("is_positive", True))

    exact_recall = pos_exact / max(1, pos_total)
    relaxed_recall = pos_relaxed / max(1, pos_total)
    neg_accuracy = neg_correct / max(1, neg_total)

    # Save raw predictions
    raw_dump = {
        "run_id": env.run_id,
        "total_predicted_dumped": len(predicted_edges_dump),
        "predictions": predicted_edges_dump[:500],
    }
    raw_file = env.raw_root / "edge_eval" / "predicted_edges.json"
    raw_file.write_text(json.dumps(raw_dump, indent=2), encoding="utf-8")
    print(f"Saved predicted edges raw dump to {raw_file}")

    # Save results/edge_evaluation.json
    result_payload = {
        "run_id": env.run_id,
        "status": "ADVISORY_ONLY",
        "target_commit": env.target_repo_commit,
        "positive_edges_total": pos_total,
        "positive_exact_typed_matches": pos_exact,
        "positive_relaxed_endpoint_matches": pos_relaxed,
        "positive_wrong_relation_matches": pos_wrong_relation,
        "positive_missing_edges": pos_missing,
        "exact_typed_edge_recall": round(exact_recall, 4),
        "relaxed_endpoint_recall": round(relaxed_recall, 4),
        "hard_negative_edges_total": neg_total,
        "hard_negative_correct_rejections": neg_correct,
        "hard_negative_violations": neg_violated,
        "hard_negative_rejection_rate": round(neg_accuracy, 4),
        "precision_methodology": "NOT_MEASURED (Requires full open-world edge adjudication corpus)",
        "eval_records": edge_eval_records,
    }

    res_file = env.results_root / "edge_evaluation.json"
    res_file.write_text(json.dumps(result_payload, indent=2), encoding="utf-8")
    print(f"Saved edge evaluation result to {res_file}")
    print(f"Exact Recall: {exact_recall*100:.1f}%, Relaxed Recall: {relaxed_recall*100:.1f}%, Negative Rejection: {neg_accuracy*100:.1f}%")


if __name__ == "__main__":
    evaluate_edges()
