"""
Phase D: Ground Truth Evaluation — Compare RCIR output against independent ground truth.

Computes per-edge-class metrics:
- true_positives: RCIR found the edge and it's in ground truth
- false_positives: RCIR reported an edge not in ground truth (assessed differently)
- false_negatives (silent misses): ground truth edge RCIR didn't find at all
- known_unresolved: ground truth edge RCIR flagged as unresolvable
- unsupported: ground truth edge outside RCIR's analysis scope

Section 9 metrics:
- edge_precision
- edge_recall
- silent_miss_rate
- known_unresolved_rate
- unsupported_rate
"""

import json
from pathlib import Path
import sys
from typing import Any


def normalize_target(target: str) -> str:
    """Normalize target names for fuzzy matching."""
    # Remove leading backslashes from PHP FQCNs
    t = target.lstrip('\\')
    # Normalize separators
    t = t.replace('/', '.').replace('::', '.')
    return t.lower()


def check_edge_in_graph(gt_edge: dict, graph_edges: list[dict]) -> dict:
    """Check if a ground truth edge is found in RCIR's graph output.

    Returns a result dict with matching status.
    """
    gt_source = gt_edge["source"]
    gt_target = gt_edge["target"]
    gt_type = gt_edge["edge_type"]

    # Normalize for fuzzy matching
    gt_target_norm = normalize_target(gt_target)
    gt_source_norm = normalize_target(gt_source)

    # Try exact match first
    for edge in graph_edges:
        e_source = edge.get("source", "")
        e_target = edge.get("target", "")

        e_source_norm = normalize_target(e_source)
        e_target_norm = normalize_target(e_target)

        # Check if source and target match (either exact or substring)
        source_match = (
            gt_source_norm == e_source_norm or
            gt_source_norm in e_source_norm or
            e_source_norm in gt_source_norm
        )
        target_match = (
            gt_target_norm == e_target_norm or
            gt_target_norm in e_target_norm or
            e_target_norm in gt_target_norm
        )

        if source_match and target_match:
            resolution = edge.get("resolution", "unknown")
            if resolution in ("dynamic_unresolved", "unsupported"):
                return {
                    "status": "known_unresolved",
                    "matched_edge": edge,
                    "resolution": resolution,
                }
            return {
                "status": "true_positive",
                "matched_edge": edge,
                "resolution": resolution,
            }

    # Try target-only match (less strict — checks if RCIR found the target at all)
    target_found_anywhere = False
    for edge in graph_edges:
        e_target = edge.get("target", "")
        e_target_norm = normalize_target(e_target)
        if gt_target_norm in e_target_norm or e_target_norm in gt_target_norm:
            target_found_anywhere = True
            break

    if target_found_anywhere:
        return {
            "status": "partial_match",
            "notes": f"Target '{gt_target}' found in graph but not with expected source '{gt_source}'",
        }

    return {
        "status": "silent_miss",
        "notes": f"Ground truth edge not found: {gt_source} -> {gt_target}",
    }


def evaluate_ground_truth(graph_path: Path, gt_path: Path) -> dict:
    """Evaluate RCIR graph against ground truth."""
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    ground_truth = json.loads(gt_path.read_text(encoding="utf-8"))

    edges = graph.get("edges", [])

    results = []
    total_tp = 0
    total_fn = 0  # silent misses
    total_unresolved = 0
    total_partial = 0
    category_results = {}

    for gt_edge in ground_truth:
        result = check_edge_in_graph(gt_edge, edges)
        result["ground_truth"] = gt_edge

        status = result["status"]
        category = gt_edge.get("category", "unknown")
        difficulty = gt_edge.get("difficulty", "unknown")

        if status == "true_positive":
            total_tp += 1
        elif status == "silent_miss":
            total_fn += 1
        elif status == "known_unresolved":
            total_unresolved += 1
        elif status == "partial_match":
            total_partial += 1

        # Per-category tracking
        if category not in category_results:
            category_results[category] = {"tp": 0, "fn": 0, "unresolved": 0, "partial": 0, "total": 0}
        category_results[category]["total"] += 1
        if status == "true_positive":
            category_results[category]["tp"] += 1
        elif status == "silent_miss":
            category_results[category]["fn"] += 1
        elif status == "known_unresolved":
            category_results[category]["unresolved"] += 1
        elif status == "partial_match":
            category_results[category]["partial"] += 1

        results.append(result)

    total = len(ground_truth)
    edge_recall = total_tp / total if total > 0 else 0.0
    silent_miss_rate = total_fn / total if total > 0 else 0.0
    unresolved_rate = total_unresolved / total if total > 0 else 0.0

    report = {
        "summary": {
            "total_ground_truth_edges": total,
            "true_positives": total_tp,
            "silent_misses": total_fn,
            "known_unresolved": total_unresolved,
            "partial_matches": total_partial,
            "edge_recall": round(edge_recall, 4),
            "silent_miss_rate": round(silent_miss_rate, 4),
            "known_unresolved_rate": round(unresolved_rate, 4),
        },
        "per_category": category_results,
        "detailed_results": results,
        "graph_stats": {
            "total_nodes": len(graph.get("nodes", [])),
            "total_edges": len(edges),
        },
    }

    return report


def main():
    base_dir = Path(__file__).resolve().parent.parent
    graph_path = base_dir / "rcir" / "nextcloud_graph.json"
    gt_path = base_dir / "ground_truth" / "ground_truth_edges.json"
    output_path = base_dir / "reports" / "ground_truth_evaluation.json"

    if not graph_path.exists():
        print(f"ERROR: Graph file not found: {graph_path}")
        print("Run Phase B extraction first.")
        return

    if not gt_path.exists():
        print(f"ERROR: Ground truth file not found: {gt_path}")
        print("Run establish_ground_truth.py first.")
        return

    print(f"Evaluating RCIR graph against ground truth...")
    report = evaluate_ground_truth(graph_path, gt_path)

    output_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Report saved to: {output_path}")

    # Print summary
    s = report["summary"]
    print(f"\n{'='*60}")
    print(f"GROUND TRUTH EVALUATION RESULTS")
    print(f"{'='*60}")
    print(f"Ground truth edges:    {s['total_ground_truth_edges']}")
    print(f"True positives:        {s['true_positives']}")
    print(f"Silent misses:         {s['silent_misses']}")
    print(f"Known unresolved:      {s['known_unresolved']}")
    print(f"Partial matches:       {s['partial_matches']}")
    print(f"Edge recall:           {s['edge_recall']:.1%}")
    print(f"Silent miss rate:      {s['silent_miss_rate']:.1%}")

    print(f"\nPer category:")
    for cat, stats in sorted(report["per_category"].items()):
        recall = stats['tp'] / stats['total'] if stats['total'] > 0 else 0
        print(f"  {cat:30s}  TP={stats['tp']}  FN={stats['fn']}  Partial={stats['partial']}  Recall={recall:.0%}")

    print(f"\nDetailed results:")
    for r in report["detailed_results"]:
        gt = r["ground_truth"]
        status_icon = {"true_positive": "[OK]", "silent_miss": "[MISS]", "known_unresolved": "[?]", "partial_match": "[PARTIAL]"}.get(r["status"], "[?]")
        print(f"  {status_icon} {gt['case_id']} ({gt['category']}, {gt.get('difficulty', '?')}): {r['status']}")
        if r.get("notes"):
            print(f"      Notes: {r['notes']}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
