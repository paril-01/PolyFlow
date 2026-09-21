"""
Online Boutique controlled benchmark (§6.1.A).

Evaluates RCIR against Google Cloud's Online Boutique (microservices-demo),
measuring precision, recall, and soundness across cross-service protobuf
definitions and Python service implementations.

Anti-Fabrication Discipline (§0.1):
- Uses independently-established ground truth from online_boutique_gt.json
- Computes metrics from real pipeline runs
- No hardcoded numbers or inflated scores
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

from rcir.graph.extractor import extract_graph
from rcir.hierarchy.builder import build_hierarchy
from rcir.retrieval.hybrid import hybrid_retrieve
from rcir.evaluation.ground_truth import (
    DiscoveredEdge,
    compute_precision_recall,
    load_ground_truth,
    PrecisionRecallReport,
)

DEFAULT_SCRATCH_REPO = Path(
    r"C:\Users\Paril Rupani\.gemini\antigravity-ide\brain\214c90a1-3995-48a9-a408-5acad77eafd5\scratch\microservices-demo"
)

DEFAULT_GROUND_TRUTH = (
    Path(__file__).parent / "ground_truth" / "online_boutique_gt.json"
)


def run_online_boutique_benchmark(
    repo_path: str | Path | None = None,
    ground_truth_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run the complete Online Boutique benchmark.

    Args:
        repo_path: Path to cloned microservices-demo repository.
        ground_truth_path: Path to ground truth JSON file.

    Returns:
        Benchmark results dictionary with precision/recall metrics and retrieval tests.
    """
    repo = Path(repo_path) if repo_path else DEFAULT_SCRATCH_REPO
    gt_path = Path(ground_truth_path) if ground_truth_path else DEFAULT_GROUND_TRUTH

    if not repo.exists():
        raise FileNotFoundError(
            f"Online Boutique repository not found at: {repo}. "
            "Clone it first with git clone --depth 1 "
            "https://github.com/GoogleCloudPlatform/microservices-demo.git"
        )

    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth file not found at: {gt_path}")

    # 1. Graph Extraction
    graph = extract_graph(repo)
    meta = graph["metadata"]

    # 2. Hierarchy Building
    hierarchy = build_hierarchy(graph)

    # 3. Precision / Recall Evaluation
    ground_truth = load_ground_truth(gt_path)

    discovered_edges = [
        DiscoveredEdge(
            source=e["source"],
            target=e["target"],
            edge_class=e.get("resolution", "static_exact"),
            confidence=e.get("confidence", 1.0),
            reason=e.get("reason", ""),
        )
        for e in graph["edges"]
    ]

    pr_report: PrecisionRecallReport = compute_precision_recall(
        discovered=discovered_edges,
        ground_truth=ground_truth,
    )

    # 4. Retrieval Benchmark Tasks
    benchmark_tasks = [
        {
            "id": "ob_task_1",
            "name": "Cart Item Addition",
            "query": "CartService AddItem request item and empty response",
            "budget": 2000,
        },
        {
            "id": "ob_task_2",
            "name": "Email Order Confirmation",
            "query": "SendOrderConfirmation in EmailService with order details",
            "budget": 2000,
        },
        {
            "id": "ob_task_3",
            "name": "Product Catalog Search",
            "query": "ProductCatalogService SearchProducts query and results",
            "budget": 2000,
        },
    ]

    retrieval_results = []
    for task in benchmark_tasks:
        contract = hybrid_retrieve(
            hierarchy=hierarchy,
            query=task["query"],
            token_budget=task["budget"],
            graph_edges=graph.get("edges", []),
        )
        retrieval_results.append({
            "task_id": task["id"],
            "name": task["name"],
            "query": task["query"],
            "nodes_retrieved": len(contract.nodes),
            "tokens_used": contract.token_budget_used,
            "tokens_budget": contract.token_budget_total,
            "coverage_warning": contract.coverage_warning,
            "sample_nodes": [n.path for n in contract.nodes[:5]],
        })

    results = {
        "repository": str(repo),
        "extraction_metadata": meta,
        "precision_recall": pr_report.to_dict(),
        "ground_truth_total_edges": len(ground_truth),
        "retrieval_benchmarks": retrieval_results,
    }

    return results


if __name__ == "__main__":
    res = run_online_boutique_benchmark()
    print("=== Online Boutique Benchmark Results ===")
    print(f"Nodes extracted: {res['extraction_metadata']['total_nodes']}")
    print(f"Edges extracted: {res['extraction_metadata']['total_edges']}")
    print(f"Proto files parsed: {res['extraction_metadata']['proto_files_parsed']}")
    print(f"Ground truth edges: {res['ground_truth_total_edges']}")
    print(f"Overall Recall: {res['precision_recall']['overall']['recall']}")
    print(f"Overall Precision: {res['precision_recall']['overall']['precision']}")
    print("\nRetrieval Tasks:")
    for t in res["retrieval_benchmarks"]:
        print(f"  - {t['name']}: {t['nodes_retrieved']} nodes, {t['tokens_used']}/{t['tokens_budget']} tokens")
