"""
Phase D: Controlled Mutation Suite for RCIR on Nextcloud.

Evaluates RCIR's blast radius and impact analysis on 7 controlled mutations
affecting real Nextcloud core classes, methods, events, interfaces, and routes:

1. MUT-001: Rename method OCA\\Files\\Controller\\ApiController::getThumbnail
2. MUT-002: Rename service class OC\\Files\\Node\\Node
3. MUT-003: Rename interface OCP\\Files\\Node
4. MUT-004: Rename event class OCP\\Files\\Events\\Node\\NodeDeletedEvent
5. MUT-005: Change DI container lookup for OCP\\IConfig
6. MUT-006: Rename method OCP\\Files\\Node::getId
7. MUT-007: Rename static method OCP\\Util::isLoaded

For each mutation:
- Runs RCIR impact analysis (generate_change_impact_report) using the full extracted graph
- Performs independent grep-based verification across the Nextcloud codebase to find all true references
- Computes Precision, Recall, and Silent Miss count
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))

from rcir.impact import generate_change_impact_report


MUTATIONS = [
    {
        "id": "MUT-001",
        "name": "Rename Controller Method",
        "entity": "ApiController::getThumbnail",
        "symbol": "getThumbnail",
        "category": "controller_method",
        "target_file": "apps/files/lib/Controller/ApiController.php",
        "grep_pattern": "getThumbnail",
        "description": "Rename thumbnail generation method on ApiController",
    },
    {
        "id": "MUT-002",
        "name": "Rename Core Service Class",
        "entity": "OC\\Files\\Node\\Node",
        "symbol": "Node",
        "category": "service_class",
        "target_file": "lib/private/Files/Node/Node.php",
        "grep_pattern": "\\bNode\\b",
        "description": "Rename core filesystem Node class",
    },
    {
        "id": "MUT-003",
        "name": "Rename Interface",
        "entity": "OCP\\Files\\Node",
        "symbol": "Node",
        "category": "interface",
        "target_file": "lib/public/Files/Node.php",
        "grep_pattern": "implements.*Node|interface Node",
        "description": "Rename public API Node interface",
    },
    {
        "id": "MUT-004",
        "name": "Rename Event Class",
        "entity": "OCP\\Files\\Events\\Node\\NodeDeletedEvent",
        "symbol": "NodeDeletedEvent",
        "category": "event",
        "target_file": "lib/public/Files/Events/Node/NodeDeletedEvent.php",
        "grep_pattern": "NodeDeletedEvent",
        "description": "Rename NodeDeletedEvent dispatched when a file/folder is deleted",
    },
    {
        "id": "MUT-005",
        "name": "Change DI Service Lookup",
        "entity": "OCP\\IConfig",
        "symbol": "IConfig",
        "category": "dependency_injection",
        "target_file": "lib/public/IConfig.php",
        "grep_pattern": "get\\(IConfig::class\\)|get\\(['\"]IConfig['\"]\\)|IConfig \\$",
        "description": "Change DI container resolution of IConfig service",
    },
    {
        "id": "MUT-006",
        "name": "Rename Interface Method",
        "entity": "OCP\\Files\\Node::getId",
        "symbol": "getId",
        "category": "interface_method",
        "target_file": "lib/public/Files/Node.php",
        "grep_pattern": "->getId\\(\\)",
        "semantic_filter": "node_scope",
        "description": "Rename getId() method on Node interface and implementations (semantically scoped to OCP\\Files\\Node)",
    },
    {
        "id": "MUT-007",
        "name": "Rename Public Util Static Method",
        "entity": "OCP\\Util::isLoaded",
        "symbol": "isLoaded",
        "category": "static_method",
        "target_file": "lib/public/Util.php",
        "grep_pattern": "Util::isLoaded",
        "description": "Rename Util::isLoaded() static check method",
    },
]

NODE_SCOPE_RE = re.compile(
    r"use\s+OCP\\Files\\(Node|File|Folder)|use\s+OC\\Files\\Node|"
    r"Node\s+\$|File\s+\$|Folder\s+\$|@(?:param|return|var)\s+(?:\\?[A-Za-z0-9_\\]*\\)?(Node|File|Folder)"
)


def find_ground_truth_references(
    repo_path: Path,
    grep_pattern: str,
    semantic_filter: str | None = None,
    file_ext: str = "*.php",
) -> list[str]:
    """Find actual references in codebase using regex search with semantic scope verification."""
    matched_files = set()
    regex = re.compile(grep_pattern)

    for root, _, files in os.walk(repo_path):
        # Skip vendor and 3rdparty
        if any(skip in root for skip in [".git", "vendor", "3rdparty", "node_modules"]):
            continue
        for f in files:
            if f.endswith((".php", ".ts", ".js")):
                fp = Path(root) / f
                try:
                    content = fp.read_text(encoding="utf-8", errors="ignore")
                    if regex.search(content):
                        # Apply semantic verification if required
                        if semantic_filter == "node_scope":
                            rel_posix = fp.relative_to(repo_path).as_posix()
                            has_node_context = (
                                bool(NODE_SCOPE_RE.search(content))
                                or "Files/Node" in rel_posix
                                or "lib/public/Files" in rel_posix
                            )
                            if not has_node_context:
                                continue
                        rel = fp.relative_to(repo_path).as_posix()
                        matched_files.add(rel)
                except Exception:
                    pass
    return sorted(matched_files)


def evaluate_mutation(mutation: dict[str, Any], full_graph: dict[str, Any], repo_path: Path) -> dict[str, Any]:
    """Evaluate a single mutation against RCIR impact analysis and ground truth."""
    m_id = mutation["id"]
    symbol = mutation["symbol"]
    entity = mutation["entity"]
    print(f"\nEvaluating {m_id}: {mutation['name']} (symbol: '{symbol}')...")

    # 1. Run RCIR Change Impact Report
    t0 = time.perf_counter()
    report = generate_change_impact_report(
        repo_path=repo_path,
        target_symbol=symbol,
        graph=full_graph,
    )
    rcir_latency_ms = (time.perf_counter() - t0) * 1000

    # Collect files identified by RCIR as affected
    rcir_affected_files = set()
    for edge in report.affected_edges:
        src = edge.get("source", "")
        # Extract file from source path
        if "::" in src:
            src_file = src.split("::")[0]
        else:
            src_file = src
        # Normalize relative path
        src_file = src_file.replace("\\", "/").strip("/")
        if src_file:
            rcir_affected_files.add(src_file)

    # 2. Independent ground truth search (semantically verified)
    t_gt0 = time.perf_counter()
    gt_files = set(
        find_ground_truth_references(
            repo_path,
            mutation["grep_pattern"],
            semantic_filter=mutation.get("semantic_filter"),
        )
    )
    gt_time_s = time.perf_counter() - t_gt0

    # Normalize target file
    norm_target = mutation["target_file"].replace("\\", "/")

    # Intersect and compute metrics
    true_positives = rcir_affected_files & gt_files
    false_positives = rcir_affected_files - gt_files
    false_negatives = gt_files - rcir_affected_files

    precision = len(true_positives) / len(rcir_affected_files) if rcir_affected_files else (1.0 if not gt_files else 0.0)
    recall = len(true_positives) / len(gt_files) if gt_files else 1.0

    print(f"  RCIR: {report.total_affected_call_sites} call sites across {len(rcir_affected_files)} files ({rcir_latency_ms:.1f}ms)")
    print(f"  Exact: {report.exact_call_sites}, Inferred: {report.inferred_call_sites}, Confidence: {report.confidence:.1%}")
    print(f"  Ground Truth: {len(gt_files)} referencing files found via grep ({gt_time_s:.2f}s)")
    print(f"  TP: {len(true_positives)} | FP: {len(false_positives)} | FN (missed): {len(false_negatives)}")
    print(f"  Precision: {precision:.1%} | Recall: {recall:.1%}")

    return {
        "mutation_id": m_id,
        "name": mutation["name"],
        "entity": entity,
        "symbol": symbol,
        "category": mutation["category"],
        "target_file": norm_target,
        "rcir_latency_ms": round(rcir_latency_ms, 2),
        "rcir_total_affected_call_sites": report.total_affected_call_sites,
        "rcir_exact_call_sites": report.exact_call_sites,
        "rcir_inferred_call_sites": report.inferred_call_sites,
        "rcir_affected_files_count": len(rcir_affected_files),
        "rcir_confidence": round(report.confidence, 3),
        "ground_truth_files_count": len(gt_files),
        "true_positives_count": len(true_positives),
        "false_positives_count": len(false_positives),
        "false_negatives_count": len(false_negatives),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "sample_missed_files": sorted(list(false_negatives))[:5],
        "sample_detected_files": sorted(list(true_positives))[:5],
    }


def main():
    print("=" * 60)
    print("PHASE D: CONTROLLED MUTATION SUITE FOR RCIR")
    print("=" * 60)

    repo_path = REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"
    graph_path = REPO_ROOT / "experiments" / "nextcloud_validation" / "rcir" / "nextcloud_graph.json"

    if not graph_path.exists():
        print(f"Error: Nextcloud graph not found at {graph_path}")
        sys.exit(1)

    print(f"Loading Nextcloud dependency graph from {graph_path}...")
    t0 = time.perf_counter()
    with open(graph_path, "r", encoding="utf-8") as f:
        graph = json.load(f)
    print(f"Graph loaded in {time.perf_counter() - t0:.2f}s ({len(graph.get('nodes', [])):,} nodes, {len(graph.get('edges', [])):,} edges)")

    results = []
    for mutation in MUTATIONS:
        res = evaluate_mutation(mutation, graph, repo_path)
        results.append(res)

    # Compute overall summary
    total_tp = sum(r["true_positives_count"] for r in results)
    total_fp = sum(r["false_positives_count"] for r in results)
    total_fn = sum(r["false_negatives_count"] for r in results)
    total_gt = sum(r["ground_truth_files_count"] for r in results)

    macro_precision = sum(r["precision"] for r in results) / len(results)
    macro_recall = sum(r["recall"] for r in results) / len(results)
    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    micro_recall = total_tp / total_gt if total_gt > 0 else 0

    summary = {
        "total_mutations": len(results),
        "macro_precision": round(macro_precision, 3),
        "macro_recall": round(macro_recall, 3),
        "micro_precision": round(micro_precision, 3),
        "micro_recall": round(micro_recall, 3),
        "total_true_positives": total_tp,
        "total_false_positives": total_fp,
        "total_false_negatives": total_fn,
        "total_ground_truth_references": total_gt,
        "average_impact_latency_ms": round(sum(r["rcir_latency_ms"] for r in results) / len(results), 2),
    }

    output = {
        "summary": summary,
        "mutations": results,
    }

    report_path = REPO_ROOT / "experiments" / "nextcloud_validation" / "reports" / "mutation_suite_results.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\n[OK] Mutation suite report saved to: {report_path}")

    print("\n" + "=" * 80)
    print("MUTATION SUITE SUMMARY")
    print("=" * 80)
    print(f"{'ID':<10} {'Name':<28} {'GT':>6} {'RCIR':>6} {'TP':>6} {'FN':>6} {'Prec':>8} {'Recall':>8}")
    print("-" * 80)
    for r in results:
        print(f"{r['mutation_id']:<10} {r['name']:<28} {r['ground_truth_files_count']:>6} {r['rcir_affected_files_count']:>6} {r['true_positives_count']:>6} {r['false_negatives_count']:>6} {r['precision']:>7.1%} {r['recall']:>7.1%}")
    print("-" * 80)
    print(f"{'OVERALL':<39} {total_gt:>6} {total_tp + total_fp:>6} {total_tp:>6} {total_fn:>6} {micro_precision:>7.1%} {micro_recall:>7.1%}")
    print("=" * 80)


if __name__ == "__main__":
    main()
