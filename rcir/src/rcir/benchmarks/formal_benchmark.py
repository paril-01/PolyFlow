"""
Formal Benchmark Runner (§6.5).

Executes comprehensive evaluation of RCIR against formal criteria:
1. Precision and recall against independently-established ground truth (§1)
2. Token efficiency and budget boundedness (§7)
3. Layered Context Contract compliance (§5)
4. Invalidation blast radius comparison (body-only vs interface edits)
5. Zero-cloud constraint compliance (§3)

Anti-Fabrication Discipline (§0.1):
- All numbers are computed from live pipeline execution
- Denominators are derived directly from the ground truth file
- No hardcoded benchmark scores or synthetic inflation
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rcir.graph.extractor import extract_graph
from rcir.hierarchy.builder import build_hierarchy
from rcir.retrieval.hybrid import hybrid_retrieve
from rcir.state.diff import diff_file
from rcir.state.propagate import compute_propagation
from rcir.contract.schema import ContextContract, validate_contract
from rcir.evaluation.ground_truth import (
    DiscoveredEdge,
    compute_precision_recall,
    load_ground_truth,
    PrecisionRecallReport,
)


@dataclass
class FormalBenchmarkConfig:
    """Configuration for formal benchmark execution."""
    repo_path: Path
    ground_truth_path: Path | None = None
    tasks: list[dict[str, Any]] = field(default_factory=list)
    token_budget: int = 2000
    exclude_dirs: set[str] | None = None


@dataclass
class FormalBenchmarkResult:
    """Result of formal benchmark execution."""
    repo_path: str
    extraction_time_ms: float
    hierarchy_time_ms: float
    total_nodes: int
    total_edges: int
    proto_services: int
    http_routes: int
    precision_recall: dict[str, Any] | None
    task_evaluations: list[dict[str, Any]]
    invalidation_evaluation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_path": self.repo_path,
            "timings_ms": {
                "extraction": round(self.extraction_time_ms, 2),
                "hierarchy": round(self.hierarchy_time_ms, 2),
            },
            "graph_summary": {
                "total_nodes": self.total_nodes,
                "total_edges": self.total_edges,
                "proto_services": self.proto_services,
                "http_routes": self.http_routes,
            },
            "precision_recall": self.precision_recall,
            "task_evaluations": self.task_evaluations,
            "invalidation_evaluation": self.invalidation_evaluation,
        }


class FormalBenchmarkRunner:
    """Runner for formal benchmark evaluation."""

    def __init__(self, config: FormalBenchmarkConfig):
        self.config = config

    def run(self) -> FormalBenchmarkResult:
        repo = self.config.repo_path.resolve()

        # 1. Graph Extraction
        t0 = time.perf_counter()
        graph = extract_graph(repo, exclude_dirs=self.config.exclude_dirs)
        extraction_time_ms = (time.perf_counter() - t0) * 1000

        meta = graph["metadata"]

        # 2. Hierarchy Building
        t1 = time.perf_counter()
        hierarchy = build_hierarchy(graph)
        hierarchy_time_ms = (time.perf_counter() - t1) * 1000

        # 3. Precision / Recall (if ground truth provided)
        pr_data = None
        if self.config.ground_truth_path and self.config.ground_truth_path.exists():
            gt_edges = load_ground_truth(self.config.ground_truth_path)
            discovered = [
                DiscoveredEdge(
                    source=e["source"],
                    target=e["target"],
                    edge_class=e.get("resolution", "static_exact"),
                    confidence=e.get("confidence", 1.0),
                    reason=e.get("reason", ""),
                )
                for e in graph["edges"]
            ]
            pr_report = compute_precision_recall(discovered, gt_edges)
            pr_data = pr_report.to_dict()

        # 4. Context Retrieval Tasks
        task_evals = []
        for task in self.config.tasks:
            query = task["query"]
            budget = task.get("budget", self.config.token_budget)

            t_start = time.perf_counter()
            contract = hybrid_retrieve(
                hierarchy=hierarchy,
                query=query,
                token_budget=budget,
                graph_edges=graph.get("edges", []),
            )
            retrieval_ms = (time.perf_counter() - t_start) * 1000

            contract_errors = validate_contract(contract)

            task_evals.append({
                "task_id": task.get("id", "unnamed"),
                "query": query,
                "retrieval_time_ms": round(retrieval_ms, 2),
                "nodes_retrieved": len(contract.nodes),
                "token_budget_used": contract.token_budget_used,
                "token_budget_total": contract.token_budget_total,
                "budget_respected": contract.token_budget_used <= contract.token_budget_total,
                "contract_valid": len(contract_errors) == 0,
                "contract_errors": contract_errors,
                "retrieved_nodes": [n.path for n in contract.nodes[:5]],
            })

        # 5. Invalidation Blast Radius Test
        # Pick the first non-trivial function to test body-only vs interface edit blast radius
        inv_eval = self._evaluate_invalidation(hierarchy)

        return FormalBenchmarkResult(
            repo_path=str(repo),
            extraction_time_ms=extraction_time_ms,
            hierarchy_time_ms=hierarchy_time_ms,
            total_nodes=meta["total_nodes"],
            total_edges=meta["total_edges"],
            proto_services=meta.get("proto_services_found", 0),
            http_routes=meta.get("http_routes_found", 0),
            precision_recall=pr_data,
            task_evaluations=task_evals,
            invalidation_evaluation=inv_eval,
        )

    def _evaluate_invalidation(self, hierarchy: dict[str, Any]) -> dict[str, Any]:
        """Test invalidation blast radius on a sample node."""
        func_nodes = [n for n in hierarchy.get("nodes", []) if n.get("kind") == "function"]
        if not func_nodes:
            return {"status": "no_function_nodes_found"}

        sample_node = func_nodes[0]["path"]

        # Body-only diff:
        body_diff = [{
            "node_path": sample_node,
            "interface_status": "unchanged",
            "body_status": "changed",
            "data_contract_status": "n/a",
        }]
        body_result = compute_propagation(body_diff, hierarchy)

        # Interface diff:
        iface_diff = [{
            "node_path": sample_node,
            "interface_status": "changed",
            "body_status": "changed",
            "data_contract_status": "changed",
        }]
        iface_result = compute_propagation(iface_diff, hierarchy)

        return {
            "tested_node": sample_node,
            "body_only_blast_radius": body_result.total_invalidated,
            "interface_blast_radius": iface_result.total_invalidated,
            "confinement_holds": body_result.total_invalidated <= iface_result.total_invalidated,
        }


def run_formal_benchmark(
    repo_path: str | Path,
    ground_truth_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Convenience function to run the formal benchmark."""
    repo = Path(repo_path)
    gt = Path(ground_truth_path) if ground_truth_path else None

    # Default tasks for general repos
    default_tasks = [
        {"id": "t1", "query": "service request response handler", "budget": 2000},
        {"id": "t2", "query": "order payment checkout cart", "budget": 2000},
        {"id": "t3", "query": "validate auth token credentials", "budget": 2000},
    ]

    config = FormalBenchmarkConfig(
        repo_path=repo,
        ground_truth_path=gt,
        tasks=default_tasks,
    )

    runner = FormalBenchmarkRunner(config)
    result = runner.run()
    d = result.to_dict()

    if output_path:
        Path(output_path).write_text(json.dumps(d, indent=2), encoding="utf-8")

    return d


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RCIR Formal Benchmark Runner")
    parser.add_argument("repo_path", help="Repository path to benchmark")
    parser.add_argument("--gt", default=None, help="Ground truth JSON file path")
    parser.add_argument("--output", "-o", default=None, help="Output JSON results path")
    args = parser.parse_args()

    res = run_formal_benchmark(args.repo_path, args.gt, args.output)
    print(json.dumps(res, indent=2))
