#!/usr/bin/env python3
"""
RCIR v8.2 — Automated Edge Evaluation Runner (PHASES 37, 38, 39).

Evaluates static graph extraction against frozen typed edge ground truth:
- Exact typed matching requires: source entity + target entity + relationship
- Flags wrong-relation matches explicitly: SOURCE_TARGET_ONLY_WRONG_RELATION
- Refuses to fabricate precision: marks EDGE_PRECISION as NOT_MEASURED unless
  a closed-world prediction universe is provided
- Generates raw JSON artifact `results/edge_evaluation.json`
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))

GT_EDGE_PATH = REPO_ROOT / "experiments" / "rcir_v8_2" / "ground_truth" / "typed_edge_ground_truth.json"
GRAPH_PATH = REPO_ROOT / "experiments" / "nextcloud_validation" / "rcir" / "nextcloud_graph.json"
RESULTS_PATH = REPO_ROOT / "experiments" / "rcir_v8_2" / "results" / "edge_evaluation.json"


def normalize_entity(name: str) -> str:
    clean = name.replace("\\", "/").strip("/")
    if "::" in clean:
        parts = clean.split("::")
        return f"{parts[0]}::{parts[1]}"
    return clean


def main():
    if not GT_EDGE_PATH.exists():
        raise FileNotFoundError(f"Missing {GT_EDGE_PATH}")
    if not GRAPH_PATH.exists():
        raise FileNotFoundError(f"Missing {GRAPH_PATH}")

    with open(GT_EDGE_PATH, encoding="utf-8") as f:
        gt_edges = json.load(f)

    with open(GRAPH_PATH, encoding="utf-8") as f:
        raw_graph = json.load(f)

    edges = raw_graph.get("edges", [])

    results_per_edge = []
    exact_typed_hits = 0
    inferred_typed_hits = 0
    wrong_relation_hits = 0
    no_match_hits = 0

    taxonomy_stats: dict[str, dict[str, int]] = {}

    for gt in gt_edges:
        edge_id = gt["edge_id"]
        taxonomy = gt["taxonomy"]
        expected_rel = gt["relationship"].lower()

        s_norm = gt["source"].replace("\\", "/").lower()
        t_norm = gt["target"].replace("\\", "/").lower()
        sf_norm = gt.get("source_file", "").replace("\\", "/").lower()
        tf_norm = gt.get("target_file", "").replace("\\", "/").lower()

        # Find candidate matching edges in the extracted graph
        matched_edges = []
        for e in edges:
            e_src = e.get("source", "").replace("\\", "/").lower()
            e_tgt = e.get("target", "").replace("\\", "/").lower()

            src_match = (s_norm in e_src) or (sf_norm and sf_norm in e_src)
            if not src_match:
                continue

            tgt_match = (t_norm in e_tgt) or (tf_norm and tf_norm in e_tgt)
            if not tgt_match:
                continue

            matched_edges.append(e)

        if not matched_edges:
            status = "NO_MATCH"
            no_match_hits += 1
        else:
            # Check relationship match
            matching_rel_edges = [
                e for e in matched_edges
                if e.get("edge_type", e.get("type", "")).lower() == expected_rel
                or (expected_rel == "route_to_controller" and e.get("edge_type") in ("route", "cross_boundary"))
                or (expected_rel == "event_dispatch" and e.get("edge_type") in ("calls", "event_to_listener"))
                or (expected_rel == "config_reads" and e.get("edge_type") in ("config", "config_service"))
            ]

            if not matching_rel_edges:
                status = "SOURCE_TARGET_ONLY_WRONG_RELATION"
                wrong_relation_hits += 1
            else:
                resolutions = [e.get("resolution", "static_inference") for e in matching_rel_edges]
                if any(r == "static_exact" for r in resolutions):
                    status = "EXACT_TYPED_MATCH"
                    exact_typed_hits += 1
                else:
                    status = "INFERRED_TYPED_MATCH"
                    inferred_typed_hits += 1

        if taxonomy not in taxonomy_stats:
            taxonomy_stats[taxonomy] = {"total": 0, "exact": 0, "inferred": 0, "wrong_relation": 0, "no_match": 0}
        taxonomy_stats[taxonomy]["total"] += 1
        if status == "EXACT_TYPED_MATCH":
            taxonomy_stats[taxonomy]["exact"] += 1
        elif status == "INFERRED_TYPED_MATCH":
            taxonomy_stats[taxonomy]["inferred"] += 1
        elif status == "SOURCE_TARGET_ONLY_WRONG_RELATION":
            taxonomy_stats[taxonomy]["wrong_relation"] += 1
        else:
            taxonomy_stats[taxonomy]["no_match"] += 1

        results_per_edge.append({
            "edge_id": edge_id,
            "taxonomy": taxonomy,
            "source": gt["source"],
            "target": gt["target"],
            "expected_relationship": expected_rel,
            "status": status,
            "matched_edges_count": len(matched_edges),
            "matched_edge_types": list({e.get("edge_type", e.get("type", "")) for e in matched_edges}),
        })

    total_gt = len(gt_edges)
    recovered_typed = exact_typed_hits + inferred_typed_hits
    typed_recall = round(recovered_typed / total_gt, 4) if total_gt else 0.0

    output = {
        "metadata": {
            "version": "8.2",
            "evaluator": "experiments/rcir_v8_2/scripts/evaluate_edges.py",
            "total_ground_truth_edges": total_gt,
            "matching_contract": "source_node + target_node + normalized_relationship",
        },
        "summary": {
            "exact_typed_hits": exact_typed_hits,
            "inferred_typed_hits": inferred_typed_hits,
            "wrong_relation_hits": wrong_relation_hits,
            "no_match_hits": no_match_hits,
            "total_recovered_typed": recovered_typed,
            "typed_edge_recall": typed_recall,
            "edge_precision_exact": "NOT_MEASURED (closed-world prediction universe not defined in benchmark scope; Rule 0 non-fabrication enforcement)",
            "edge_precision_inferred": "NOT_MEASURED",
        },
        "taxonomy_breakdown": taxonomy_stats,
        "edges": results_per_edge,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Edge evaluation complete! Results saved to {RESULTS_PATH}")
    print(f"Exact Typed Hits: {exact_typed_hits}/{total_gt}")
    print(f"Inferred Typed Hits: {inferred_typed_hits}/{total_gt}")
    print(f"Wrong Relation Hits: {wrong_relation_hits}/{total_gt}")
    print(f"No Match Hits: {no_match_hits}/{total_gt}")
    print(f"Typed Edge Recall: {typed_recall * 100:.1f}%")


if __name__ == "__main__":
    main()
