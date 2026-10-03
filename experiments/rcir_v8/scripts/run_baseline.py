"""
RCIR v8 — Baseline Evaluation Runner (PHASE 2 / P0).

Runs the current RCIR v7 retrieval system against the 5 benchmark tasks
from the Nextcloud validation and evaluates using the v8 evaluation framework.

Produces:
    experiments/rcir_v8/results/policy_p0.json

This establishes the P0 baseline that all subsequent policies are compared against.

Usage:
    python experiments/rcir_v8/scripts/run_baseline.py \
        --nextcloud-path <path_to_nextcloud_server> \
        --output experiments/rcir_v8/results/policy_p0.json

If --nextcloud-path is not available (repo not cloned), produces a
measurement from the existing committed benchmark artifacts instead.
"""

import json
import os
import sys
import time
import tracemalloc
from pathlib import Path

# Setup paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8" / "scripts"))

from evaluation import evaluate_task, aggregate_evaluations, K_VALUES


# --- Benchmark Task Definitions (from agent_harness.py) ---

TASKS = [
    {
        "task_id": "TASK-1",
        "title": "Refactor Controller Endpoint",
        "target_symbol": "getThumbnail",
        "target_file": "apps/files/lib/Controller/ApiController.php",
        "category": "controller_route",
        "query": "ApiController getThumbnail thumbnail generation preview",
        "description": "Refactor ApiController thumbnail endpoint and update all affected callers and routes",
        "ground_truth_grep": "getThumbnail",
        "semantic_filter": None,
    },
    {
        "task_id": "TASK-2",
        "title": "Filesystem Node Contract Evolution",
        "target_symbol": "getId",
        "target_file": "lib/public/Files/Node.php",
        "category": "interface_method",
        "query": "Node getId filesystem node identifier",
        "description": "Refactor Node::getId() method contract and identify affected consumers",
        "ground_truth_grep": "->getId\\(\\)",
        "semantic_filter": "node_scope",
    },
    {
        "task_id": "TASK-3",
        "title": "Event Contract Evolution",
        "target_symbol": "NodeDeletedEvent",
        "target_file": "lib/public/Files/Events/Node/NodeDeletedEvent.php",
        "category": "event_contract",
        "query": "NodeDeletedEvent delete node event dispatcher listener",
        "description": "Evolve NodeDeletedEvent contract and ensure all dispatchers and listeners are updated",
        "ground_truth_grep": "NodeDeletedEvent",
        "semantic_filter": None,
    },
    {
        "task_id": "TASK-4",
        "title": "Dependency Injection Service Resolution",
        "target_symbol": "IConfig",
        "target_file": "lib/public/IConfig.php",
        "category": "dependency_injection",
        "query": "IConfig get config service container",
        "description": "Refactor IConfig interface and update all container lookups and consumers",
        "ground_truth_grep": "get\\(IConfig::class\\)|get\\(['\"]IConfig['\"]\\)|IConfig \\$",
        "semantic_filter": None,
    },
    {
        "task_id": "TASK-5",
        "title": "Cross-Stack API Contract Boundary",
        "target_symbol": "Recent.ts",
        "target_file": "apps/files/src/services/Recent.ts",
        "category": "cross_stack",
        "query": "Recent getRecentSearch getContents dav endpoint",
        "description": "Trace recent files frontend client call across language boundary to backend DAV / files endpoint",
        "ground_truth_grep": "getRecentSearch|services/Recent\\.ts|views/recent\\.ts",
        "semantic_filter": None,
    },
]


def extract_ground_truth_files(repo_path: Path) -> dict[str, list[str]]:
    """Extract ground truth files for all benchmark tasks from Nextcloud repo."""
    sys.path.insert(0, str(REPO_ROOT / "experiments" / "nextcloud_validation" / "scripts"))
    from agent_harness import get_ground_truth_files

    gt_by_task = {}
    for task in TASKS:
        files = get_ground_truth_files(
            repo_path,
            task["ground_truth_grep"],
            task.get("semantic_filter"),
        )
        gt_by_task[task["task_id"]] = files
    return gt_by_task


def run_live_baseline(nextcloud_path: Path, precomputed_graph_path: Path | None = None) -> tuple[dict, dict]:
    """Run live RCIR v7 retrieval against a Nextcloud clone using hybrid retrieval + change impact report.

    Returns:
        (results_dict, ground_truth_dict)
    """
    from rcir.graph.extractor import extract_graph
    from rcir.hierarchy.builder import build_hierarchy
    from rcir.retrieval.hybrid import hybrid_retrieve
    from rcir.impact import generate_change_impact_report

    # Load pre-extracted graph if available to save 5+ minutes
    graph = None
    if precomputed_graph_path and precomputed_graph_path.exists():
        print(f"Loading precomputed graph from {precomputed_graph_path}...")
        t0 = time.perf_counter()
        graph = json.loads(precomputed_graph_path.read_text(encoding="utf-8"))
        print(f"  Loaded graph ({len(graph.get('nodes', []))} nodes, {len(graph.get('edges', []))} edges) in {(time.perf_counter() - t0):.2f}s")
    else:
        print(f"Extracting graph from {nextcloud_path}...")
        t0 = time.perf_counter()
        graph = extract_graph(nextcloud_path)
        print(f"  Extracted in {(time.perf_counter() - t0):.2f}s")

    print("Building hierarchy...")
    t0 = time.perf_counter()
    hierarchy = build_hierarchy(graph)
    print(f"  Hierarchy built in {(time.perf_counter() - t0):.2f}s")

    # Extract ground truth files
    print("Extracting ground-truth files from repository...")
    gt_map = extract_ground_truth_files(nextcloud_path)
    for tid, files in gt_map.items():
        print(f"  {tid}: {len(files)} ground-truth files")

    # Save ground truth to file for reproducibility
    gt_cache_path = REPO_ROOT / "experiments" / "rcir_v8" / "ground_truth" / "ground_truth_files_v7.json"
    gt_cache_path.parent.mkdir(parents=True, exist_ok=True)
    gt_cache_path.write_text(json.dumps(gt_map, indent=2), encoding="utf-8")

    results = {"tasks": []}
    gt_dict = {"tasks": []}

    for task in TASKS:
        task_id = task["task_id"]
        print(f"\nRunning {task_id}: {task['title']}...")
        tracemalloc.start()
        t0 = time.perf_counter()

        # 1. Bounded hybrid retrieval contract
        contract = hybrid_retrieve(
            hierarchy=hierarchy,
            query=task["query"],
            token_budget=4000,
            graph_edges=graph.get("edges", []),
        )

        # 2. Change impact report (2-hop blast radius expansion)
        impact_report = generate_change_impact_report(
            repo_path=nextcloud_path,
            target_symbol=task["target_symbol"],
            graph=graph,
        )

        latency_ms = (time.perf_counter() - t0) * 1000
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Build ranked retrieved file list:
        # Priority 1: Target file
        # Priority 2: Files in contract nodes (hybrid retrieval score order)
        # Priority 3: Affected edges from impact report (1-hop then 2-hop)
        retrieved_files = []
        seen = set()

        def add_file(f: str):
            f_norm = f.replace("\\", "/").strip("/")
            if "::" in f_norm:
                f_norm = f_norm.split("::")[0]
            if f_norm and f_norm not in seen:
                seen.add(f_norm)
                retrieved_files.append(f_norm)

        if task.get("target_file"):
            add_file(task["target_file"])

        for node in contract.nodes:
            add_file(node.path)

        for edge in impact_report.affected_edges:
            for ep in (edge.get("source", ""), edge.get("target", "")):
                add_file(ep)

        task_gt = gt_map.get(task_id, [])
        gt_set = set(task_gt)
        retrieved_set = set(retrieved_files)
        silent_misses = sorted(list(gt_set - retrieved_set))

        tb_coverage = 0.0
        contract_files = set()
        for node in contract.nodes:
            p = node.path.split("::")[0].replace("\\", "/").strip("/")
            if p:
                contract_files.add(p)
        if gt_set:
            tb_coverage = len(contract_files & gt_set) / len(gt_set)

        results["tasks"].append({
            "task_id": task_id,
            "retrieved_files": retrieved_files,
            "candidate_count": len(retrieved_files),
            "token_budgeted_coverage": tb_coverage,
            "latency_ms": latency_ms,
            "peak_memory_mb": peak_mem / 1024 / 1024,
            "unresolved_count": impact_report.unresolved_count,
        })

        gt_dict["tasks"].append({
            "task_id": task_id,
            "ground_truth_files": task_gt,
            "ground_truth_count": len(task_gt),
            "silent_misses": silent_misses,
            "silent_miss_count": len(silent_misses),
            "known_unresolved": [u.location for u in impact_report.unresolved_locations],
            "unsupported": [],
        })

        print(f"  Retrieved: {len(retrieved_files)} candidates (Top-50 evaluated for ranking)")
        print(f"  Ground truth: {len(task_gt)}, Silent misses: {len(silent_misses)}")
        print(f"  Latency: {latency_ms:.1f}ms, Memory: {peak_mem / 1024 / 1024:.1f}MB")

    return results, gt_dict


def build_from_committed_artifacts() -> dict:
    """Build evaluation from committed benchmark artifacts.

    Uses the agent_benchmark_results.json which contains per-task
    RCIR retrieval results from the original Nextcloud benchmark run.
    """
    artifacts_dir = REPO_ROOT / "experiments" / "nextcloud_validation" / "reports"
    agent_results_path = artifacts_dir / "agent_benchmark_results.json"
    if not agent_results_path.exists():
        print(f"ERROR: Cannot find {agent_results_path}")
        sys.exit(1)

    agent_results = json.loads(agent_results_path.read_text(encoding="utf-8"))
    results = {"tasks": []}

    for task_bench in agent_results.get("algorithmic_retrieval_benchmarks", []):
        task_id = task_bench.get("task_id", "")
        rcir = task_bench.get("rcir", {})

        discovered_files = rcir.get("discovered_files", [])
        files_identified = rcir.get("files_identified", len(discovered_files))

        results["tasks"].append({
            "task_id": task_id,
            "retrieved_files": discovered_files,
            "candidate_count": files_identified,
            "true_positives": rcir.get("true_positives", 0),
            "false_positives": rcir.get("false_positives", 0),
            "full_recall": rcir.get("recall", 0.0),
            "full_precision": rcir.get("precision", 0.0),
            "token_budgeted_coverage": 0.0,
            "latency_ms": 0.0,
            "peak_memory_mb": 0.0,
            "note": "Top-10 discovered_files from committed artifact.",
        })

    return results


def build_ground_truth_from_harness() -> dict:
    """Build ground truth from committed agent_benchmark_results.json."""
    artifacts_dir = REPO_ROOT / "experiments" / "nextcloud_validation" / "reports"
    agent_results_path = artifacts_dir / "agent_benchmark_results.json"

    if not agent_results_path.exists():
        print(f"ERROR: Cannot find {agent_results_path}")
        sys.exit(1)

    agent_results = json.loads(agent_results_path.read_text(encoding="utf-8"))
    ground_truth = {"tasks": []}

    for task_bench in agent_results.get("algorithmic_retrieval_benchmarks", []):
        task_id = task_bench.get("task_id", "")
        gt_count = task_bench.get("ground_truth_files", 0)
        rcir = task_bench.get("rcir", {})
        baseline = task_bench.get("baseline", {})
        silent_misses_count = rcir.get("dependency_misses", 0)

        ground_truth["tasks"].append({
            "task_id": task_id,
            "ground_truth_files": [],
            "ground_truth_count": gt_count,
            "rcir_recall": rcir.get("recall", 0.0),
            "rcir_precision": rcir.get("precision", 0.0),
            "rcir_true_positives": rcir.get("true_positives", 0),
            "baseline_recall": baseline.get("recall", 0.0),
            "silent_misses": [],
            "silent_miss_count": silent_misses_count,
            "known_unresolved": [],
            "unsupported": [],
        })

    return ground_truth


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="RCIR v8 Baseline (P0) Evaluation Runner"
    )
    default_nc = REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"
    parser.add_argument(
        "--nextcloud-path",
        default=str(default_nc) if default_nc.is_dir() else None,
        help="Path to Nextcloud server clone (for live evaluation)"
    )
    default_graph = REPO_ROOT / "experiments" / "nextcloud_validation" / "rcir" / "nextcloud_graph.json"
    parser.add_argument(
        "--graph-path",
        default=str(default_graph) if default_graph.exists() else None,
        help="Path to precomputed graph.json to avoid re-extraction"
    )
    parser.add_argument(
        "--output", "-o",
        default=str(REPO_ROOT / "experiments" / "rcir_v8" / "results" / "policy_p0.json"),
        help="Output JSON path"
    )
    args = parser.parse_args()

    # Determine mode: live or from artifacts
    if args.nextcloud_path and Path(args.nextcloud_path).is_dir():
        print("MODE: Live evaluation against Nextcloud repository")
        graph_p = Path(args.graph_path) if args.graph_path else None
        results, ground_truth = run_live_baseline(Path(args.nextcloud_path), graph_p)
    else:
        print("MODE: Evaluation from committed benchmark artifacts")
        print("  (Provide --nextcloud-path for live evaluation)")
        results = build_from_committed_artifacts()
        ground_truth = build_ground_truth_from_harness()

    # Run evaluation
    evaluations = []
    gt_by_task = {t["task_id"]: t for t in ground_truth.get("tasks", [])}
    aggregate_from_artifacts = []

    for task_result in results.get("tasks", []):
        task_id = task_result["task_id"]
        gt = gt_by_task.get(task_id, {})
        gt_files = gt.get("ground_truth_files", [])

        if not gt_files:
            aggregate_from_artifacts.append({
                "task_id": task_id,
                "ground_truth_count": gt.get("ground_truth_count", 0),
                "rcir_recall_full_set": gt.get("rcir_recall", 0.0),
                "rcir_precision_full_set": gt.get("rcir_precision", 0.0),
                "rcir_true_positives": gt.get("rcir_true_positives", 0),
                "rcir_false_positives": task_result.get("false_positives", 0),
                "rcir_candidate_count": task_result.get("candidate_count", 0),
                "baseline_recall": gt.get("baseline_recall", 0.0),
                "silent_miss_count": gt.get("silent_miss_count", 0),
                "discovered_files_truncated": task_result.get("retrieved_files", []),
                "note": "Ranked metrics NOT available — ground truth file list not in committed artifacts",
            })
        else:
            evaluation = evaluate_task(
                task_id=task_id,
                ground_truth_files=gt_files,
                retrieved_files=task_result.get("retrieved_files", []),
                candidate_count=task_result.get("candidate_count", 0),
                token_budgeted_coverage=task_result.get("token_budgeted_coverage", 0.0),
                silent_misses=gt.get("silent_misses", []),
                known_unresolved=gt.get("known_unresolved", []),
                unsupported=gt.get("unsupported", []),
                latency_ms=task_result.get("latency_ms", 0.0),
                peak_memory_mb=task_result.get("peak_memory_mb", 0.0),
            )
            evaluations.append(evaluation)

    # Build output
    aggregate = None
    if evaluations:
        aggregate = aggregate_evaluations(evaluations)
        eval_dict = aggregate.to_dict()
    else:
        eval_dict = {"task_count": 0, "note": "No full ground truth file lists available for ranked evaluation"}

    output = {
        "policy": "P0",
        "description": "Current RCIR v7 — 2-hop undirected BFS + TF-IDF + symbol match",
        "baseline_commit": "226cfc6b3b8663f98dd97f0327529f765ac36284",
        "evaluation": eval_dict,
        "aggregate_from_committed_artifacts": aggregate_from_artifacts if aggregate_from_artifacts else None,
        "data_limitations": {
            "ranked_metrics_available": len(evaluations) > 0,
            "aggregate_recall_precision_available": len(aggregate_from_artifacts) > 0,
            "note": (
                "Ranked metrics (Recall@K, Precision@K, MRR, nDCG) computed against real ground truth files. "
                "Candidate set reflects full RCIR v7 candidate expansion."
            ),
        },
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nP0 baseline evaluation written to {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("P0 BASELINE SUMMARY")
    print("=" * 60)
    if aggregate:
        macro = aggregate.to_dict()["macro_averages"]
        print(f"  Tasks:         {aggregate.task_count}")
        for k in K_VALUES:
            print(f"  Recall@{k:<2}:     {macro['recall_at'].get(k, 'N/A')}")
        for k in K_VALUES:
            print(f"  Precision@{k:<2}:  {macro['precision_at'].get(k, 'N/A')}")
        print(f"  MRR:           {macro['mrr']}")
        print(f"  nDCG@50:       {macro['ndcg']}")
        totals = aggregate.to_dict()["totals"]
        print(f"  Candidates:    {totals['candidates']}")
        print(f"  Silent misses: {totals['silent_misses']}")
    elif aggregate_from_artifacts:
        print(f"  Tasks: {len(aggregate_from_artifacts)}")
        print("  Ranked metrics not computed (file lists unavailable in artifacts mode)")
        for t in aggregate_from_artifacts:
            print(f"  {t['task_id']}: Recall={t['rcir_recall_full_set']}, Precision={t['rcir_precision_full_set']}, Misses={t['silent_miss_count']}")
    print("=" * 60)


if __name__ == "__main__":
    main()

