#!/usr/bin/env python3
"""
RCIR v8.5 — Performance & Resource Benchmark (PHASES 100-101).

Measures real execution performance across:
1. Canonical Graph Loading & Ingestion
2. Multi-Channel Candidate Retrieval & Ranking
3. Context Planning & Compilation
4. Source-Order PHP Type-Flow Analysis
5. Peak Memory Footprint (RSS)

Outputs results/performance_benchmark.json.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Add project roots
SCRIPT_DIR = Path(__file__).resolve().parent
RCIR_V8_5_ROOT = SCRIPT_DIR.parent
POLYFLOW_ROOT = RCIR_V8_5_ROOT.parent.parent
sys.path.insert(0, str(POLYFLOW_ROOT / "rcir" / "src"))
sys.path.insert(0, str(POLYFLOW_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from environment import get_default_environment
from rcir.context.compiler import ContextCompiler
from rcir.context.planner import ContextPlanner
from rcir.context.tokenizer import get_default_token_counter
from rcir.graph.canonical_graph import CanonicalGraph
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.retrieval.ranker import DeterministicRanker, RankerConfig
from rcir.types.php_type_flow import PHPTypeFlowAnalyzer
from retrieval_runner import discover_multi_channel_candidates


def get_current_rss_mb() -> float:
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return round(process.memory_info().rss / (1024 * 1024), 2)
    return 0.0


def run_performance_benchmark():
    print("=" * 80)
    print("RCIR v8.5 — Performance & Resource Benchmark")
    print("=" * 80)

    env = get_default_environment()
    print(f"Target Repo: {env.target_repo_root}")
    print(f"Run ID: {env.run_id}")

    start_rss = get_current_rss_mb()
    print(f"Initial Process RSS: {start_rss} MB")

    # 1. Benchmark Graph Loading & Construction
    print("\n[1/4] Benchmarking Canonical Graph Ingestion...")
    t0 = time.perf_counter()
    with open(env.graph_path, "r", encoding="utf-8") as f:
        raw_graph = json.load(f)
    t_load_json = time.perf_counter() - t0

    t1 = time.perf_counter()
    cg = CanonicalGraph.from_legacy_dict(raw_graph, target_repo_root=env.target_repo_root)
    t_build_cg = time.perf_counter() - t1
    total_graph_time = t_load_json + t_build_cg

    graph_rss = get_current_rss_mb()
    total_edges = sum(len(edges) for edges in cg.outgoing_edges.values())
    print(f"  Nodes: {len(cg.nodes)}, Edges: {total_edges}")
    print(f"  JSON Load Time: {t_load_json:.3f}s, Graph Build Time: {t_build_cg:.3f}s (Total: {total_graph_time:.3f}s)")
    print(f"  Post-Graph RSS: {graph_rss} MB (Delta: {graph_rss - start_rss:.2f} MB)")

    # 2. Benchmark Retrieval Across Ground Truth Tasks
    print("\n[2/4] Benchmarking Semantic Multi-Channel Retrieval & Ranking...")
    with open(env.ground_truth_root / "ground_truth.json", "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    tasks = list(gt_data["tasks"].values()) if isinstance(gt_data["tasks"], dict) else gt_data["tasks"]
    ranker = DeterministicRanker(RankerConfig(use_cascaded_ranking=False, use_diversity=False))

    retrieval_latencies_ms = []
    ranked_results_by_task = {}

    for task in tasks:
        tid = task["task_id"]
        req_sym = task.get("target_symbol") or task.get("requested_symbol", "")
        op_str = task.get("category") or task.get("operation", "behavior_change")
        try:
            op = ChangeOperation(op_str)
        except ValueError:
            op = ChangeOperation.BEHAVIOR_CHANGE

        spec = ChangeSpecification(
            operation=op,
            requested_symbol=req_sym,
            target_file_hint=task["target_file"],
            canonical_target_ids=task.get("canonical_target_ids") or [task.get("target_entity", "")],
            description=task.get("description", ""),
        )

        t_r0 = time.perf_counter()
        res = discover_multi_channel_candidates(spec, cg, cg.registry)
        candidates = list(res.candidates.values())
        ranked = ranker.rank(candidates)
        t_r1 = time.perf_counter()

        latency_ms = (t_r1 - t_r0) * 1000.0
        retrieval_latencies_ms.append(latency_ms)
        ranked_results_by_task[tid] = (spec, ranked)

    mean_retrieval_ms = sum(retrieval_latencies_ms) / len(retrieval_latencies_ms)
    sorted_ret = sorted(retrieval_latencies_ms)
    p95_retrieval_ms = sorted_ret[int(0.95 * len(sorted_ret))]
    total_retrieval_sec = sum(retrieval_latencies_ms) / 1000.0
    retrieval_throughput = len(tasks) / total_retrieval_sec if total_retrieval_sec > 0 else 0

    print(f"  Tasks Processed: {len(tasks)}")
    print(f"  Mean Latency: {mean_retrieval_ms:.2f} ms/task, P95: {p95_retrieval_ms:.2f} ms/task")
    print(f"  Throughput: {retrieval_throughput:.2f} tasks/sec")

    # 3. Benchmark Context Planning & Compilation
    print("\n[3/4] Benchmarking Context Planning & Source-Span Compilation...")
    compiler = ContextCompiler(repo_root=env.target_repo_root, tokenizer=get_default_token_counter())
    context_latencies_ms = []
    compiled_tokens = []

    for task in tasks:
        tid = task["task_id"]
        spec, ranked = ranked_results_by_task[tid]
        pinned = set(spec.canonical_target_ids) if spec.canonical_target_ids else {task["target_file"]}

        t_c0 = time.perf_counter()
        plan = ContextPlanner.create_plan(ranked, token_budget=4000, spec=spec)
        compiled = compiler.compile(ranked, token_budget=4000, pinned_targets=pinned, plan=plan)
        t_c1 = time.perf_counter()

        latency_ms = (t_c1 - t_c0) * 1000.0
        context_latencies_ms.append(latency_ms)
        compiled_tokens.append(compiled.total_estimated_tokens)

    mean_context_ms = sum(context_latencies_ms) / len(context_latencies_ms)
    sorted_ctx = sorted(context_latencies_ms)
    p95_context_ms = sorted_ctx[int(0.95 * len(sorted_ctx))]
    total_context_sec = sum(context_latencies_ms) / 1000.0
    context_throughput = len(tasks) / total_context_sec if total_context_sec > 0 else 0

    print(f"  Contexts Compiled: {len(tasks)}")
    print(f"  Mean Latency: {mean_context_ms:.2f} ms/task, P95: {p95_context_ms:.2f} ms/task")
    print(f"  Throughput: {context_throughput:.2f} tasks/sec")

    # 4. Benchmark PHP Type-Flow Analysis
    print("\n[4/4] Benchmarking PHP Type-Flow Analyzer...")
    analyzer = PHPTypeFlowAnalyzer(repo_root=env.target_repo_root)
    sample_files = [
        "apps/files/lib/Controller/ApiController.php",
        "lib/private/Server.php",
        "lib/private/User/Session.php",
        "apps/dav/lib/Connector/Sabre/FilesPlugin.php",
    ]
    existing_sample_files = [f for f in sample_files if (env.target_repo_root / f).exists()]

    type_flow_latencies_ms = []
    total_callsites_found = 0

    for f_rel in existing_sample_files:
        t_tf0 = time.perf_counter()
        cs = analyzer.analyze_file(f_rel)
        t_tf1 = time.perf_counter()
        lat = (t_tf1 - t_tf0) * 1000.0
        type_flow_latencies_ms.append(lat)
        total_callsites_found += len(cs)

    mean_tf_ms = sum(type_flow_latencies_ms) / len(type_flow_latencies_ms) if type_flow_latencies_ms else 0.0
    print(f"  Sample Files Analyzed: {len(existing_sample_files)}, Call Sites Discovered: {total_callsites_found}")
    print(f"  Mean Latency: {mean_tf_ms:.2f} ms/file")

    peak_rss = get_current_rss_mb()
    print(f"\nFinal Process RSS: {peak_rss} MB (Peak Delta: {peak_rss - start_rss:.2f} MB)")

    benchmark_output = {
        "run_id": env.run_id,
        "polyflow_commit": env.polyflow_commit,
        "target_repo_commit": env.target_repo_commit,
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "validation_status": "MEASURED_PERFORMANCE",
        "graph_ingestion": {
            "node_count": len(cg.nodes),
            "edge_count": total_edges,
            "json_load_seconds": round(t_load_json, 4),
            "graph_build_seconds": round(t_build_cg, 4),
            "total_graph_seconds": round(total_graph_time, 4),
        },
        "retrieval_and_ranking": {
            "tasks_evaluated": len(tasks),
            "mean_latency_ms": round(mean_retrieval_ms, 2),
            "p95_latency_ms": round(p95_retrieval_ms, 2),
            "total_time_seconds": round(total_retrieval_sec, 4),
            "throughput_tasks_per_sec": round(retrieval_throughput, 2),
        },
        "context_compilation": {
            "contexts_compiled": len(tasks),
            "mean_latency_ms": round(mean_context_ms, 2),
            "p95_latency_ms": round(p95_context_ms, 2),
            "total_time_seconds": round(total_context_sec, 4),
            "throughput_tasks_per_sec": round(context_throughput, 2),
            "mean_tokens": round(sum(compiled_tokens) / len(compiled_tokens), 1),
        },
        "type_flow_analysis": {
            "files_analyzed": len(existing_sample_files),
            "call_sites_discovered": total_callsites_found,
            "mean_latency_ms": round(mean_tf_ms, 2),
        },
        "memory_footprint_mb": {
            "initial_rss": start_rss,
            "post_graph_rss": graph_rss,
            "peak_rss": peak_rss,
            "rss_delta": round(peak_rss - start_rss, 2),
        },
    }

    out_file = env.results_root / "performance_benchmark.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_output, f, indent=2)

    print(f"\nSaved performance benchmark to: {out_file}")


if __name__ == "__main__":
    run_performance_benchmark()
