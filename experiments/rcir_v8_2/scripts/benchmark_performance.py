#!/usr/bin/env python3
"""
RCIR v8.2 — Performance Benchmarking Suite (PHASE 59).

Measures latency and memory consumption across the retrieval & compilation pipeline:
- Warm-up execution to prime caches
- Multiple repetitions (N=5)
- Percentile metrics: median, p95, min, max
- Stage breakdown: graph hydration, candidate generation, ranking, context compilation
- Memory breakdown: Python heap peak (tracemalloc) + process RSS (psutil)
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List

import psutil

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_2" / "scripts"))

from rcir.adapters.nextcloud import NextcloudModuleResolver
from rcir.context.compiler import ContextCompiler
from rcir.context.summarizer import ImpactSummarizer
from rcir.context.tokenizer import get_default_token_counter
from rcir.entities.registry import EntityRegistry
from rcir.graph.multi_view import MultiViewGraph
from rcir.graph.traversal_policy import GraphDegreeAnalyzer, TraversalPolicy
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.query.intent_parser import DeterministicIntentParser
from rcir.retrieval.bm25 import BM25Scorer
from rcir.retrieval.candidate_generator import CandidateGenerator, CandidateGeneratorConfig
from rcir.retrieval.evidence_vector import EvidenceVector, EvidenceVectorBuilder
from rcir.retrieval.ranker import DeterministicRanker, OperationRankerProfile, RankerConfig
from rcir.retrieval.scorer import TFIDFScorer
from rcir.types.type_flow import TypeFlowIndex

from experiments.rcir_v8.scripts.run_baseline import TASKS

RESULTS_DIR = REPO_ROOT / "experiments" / "rcir_v8_2" / "results"
NEXTCLOUD_GRAPH_PATH = REPO_ROOT / "experiments" / "nextcloud_validation" / "rcir" / "nextcloud_graph.json"
GROUND_TRUTH_DIR = REPO_ROOT / "experiments" / "rcir_v8_2" / "ground_truth"
TASKS_DICT = {t["task_id"]: t for t in TASKS}


def run_performance_benchmarks() -> Dict[str, Any]:
    process = psutil.Process()
    rss_start_mb = process.memory_info().rss / (1024 * 1024)

    # 1. Graph Loading Benchmark
    load_times: List[float] = []
    raw_graph = None
    for _ in range(3):
        t0 = time.perf_counter()
        raw_graph = json.loads(NEXTCLOUD_GRAPH_PATH.read_text(encoding="utf-8"))
        multi_view = MultiViewGraph(raw_graph)
        load_times.append((time.perf_counter() - t0) * 1000.0)

    node_count = len(raw_graph.get("nodes", []))
    edge_count = len(raw_graph.get("edges", []))

    registry = EntityRegistry.from_graph(raw_graph, repository="nextcloud-server")
    tfidf = TFIDFScorer()
    tfidf.build_index(raw_graph.get("nodes", []))
    bm25 = BM25Scorer()
    bm25.build_index(raw_graph.get("nodes", []))
    type_index = TypeFlowIndex.from_graph(raw_graph)
    module_resolver = NextcloudModuleResolver()

    with open(GROUND_TRUTH_DIR / "graded_ground_truth.json", "r", encoding="utf-8") as f:
        graded_gt = json.load(f)["tasks"]

    generator = CandidateGenerator(
        multi_view=multi_view,
        registry=registry,
        scorer=bm25,
        config=CandidateGeneratorConfig(
            use_entity_resolution=True,
            use_boundary_graph=True,
            use_test_graph=True,
            use_lexical=True,
            use_traversal=True,
            use_historical=False,
            lexical_top_k=50,
        ),
    )

    ranker_config = RankerConfig(use_cascaded_ranking=True)
    server_root = REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"
    compiler = ContextCompiler(repo_root=server_root, tokenizer=get_default_token_counter())

    def execute_task(task_dict: dict):
        spec = DeterministicIntentParser.parse_task(task_dict)
        profile = OperationRankerProfile.for_operation(spec.operation)
        ranker = DeterministicRanker(config=ranker_config, profile=profile)

        seeds = []
        for t in spec.target_entities:
            clean = t.replace("\\", "/").strip("/")
            for ent in registry.by_file.get(clean, []):
                seeds.append(ent.entity_id)
        unique_seeds = list(dict.fromkeys(seeds)) if seeds else spec.target_entities
        deg = GraphDegreeAnalyzer.analyze(multi_view, unique_seeds, spec.operation)
        policy = TraversalPolicy.for_operation(spec.operation, seed_degree=deg.policy_relevant_degree)
        policy.preserve_all_direct_exact = True
        policy.max_indirect_candidates = 2000

        # Candidate generation
        t_q0 = time.perf_counter()
        candidates = generator.generate(spec, policy=policy)
        t_q = (time.perf_counter() - t_q0) * 1000.0

        target_files = {t.split("::")[0].replace("\\", "/").strip("/") for t in spec.target_entities}
        evs = [
            EvidenceVectorBuilder.build_vector(
                c, spec, target_files,
                module_resolver=module_resolver,
                type_flow_index=type_index,
            )
            for c in candidates
        ]

        # Ranking
        t_r0 = time.perf_counter()
        ranked = ranker.rank(evs, prune_contradictions=True)
        t_r = (time.perf_counter() - t_r0) * 1000.0

        pinned = [
            t.split("::")[0].replace("\\", "/").strip("/")
            for t in task_dict.get("seed_entities", task_dict.get("target_files", []))
            if t.endswith(".php")
        ]

        # Compilation
        t_c0 = time.perf_counter()
        _ = compiler.compile(ranked, token_budget=4000, pinned_targets=pinned)
        t_c = (time.perf_counter() - t_c0) * 1000.0

        return t_q, t_r, t_c

    # Warm-up run
    print("Running warm-up pass...")
    for task in TASKS:
        execute_task(task)

    # Measured Repetitions
    query_times: List[float] = []
    ranking_times: List[float] = []
    compilation_times: List[float] = []
    total_pipeline_times: List[float] = []
    heap_peaks: List[float] = []

    N_REPS = 5
    print(f"Running {N_REPS} measured repetitions across {len(TASKS)} tasks...")
    for rep in range(N_REPS):
        for task in TASKS:
            tracemalloc.start()
            t_start = time.perf_counter()

            t_q, t_r, t_c = execute_task(task)

            t_tot = (time.perf_counter() - t_start) * 1000.0
            _, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            query_times.append(t_q)
            ranking_times.append(t_r)
            compilation_times.append(t_c)
            total_pipeline_times.append(t_tot)
            heap_peaks.append(peak_bytes / (1024 * 1024))
        print(f"  Repetition {rep + 1}/{N_REPS} complete.")

    rss_end_mb = process.memory_info().rss / (1024 * 1024)

    def stats(data: List[float]) -> Dict[str, float]:
        sorted_d = sorted(data)
        p95_idx = int(len(sorted_d) * 0.95)
        return {
            "mean": round(statistics.mean(data), 2),
            "median": round(statistics.median(data), 2),
            "p95": round(sorted_d[min(p95_idx, len(sorted_d) - 1)], 2),
            "min": round(min(data), 2),
            "max": round(max(data), 2),
        }

    return {
        "metadata": {
            "version": "8.2.0",
            "repetitions": N_REPS,
            "tasks_evaluated": len(TASKS),
            "graph_nodes": node_count,
            "graph_edges": edge_count,
        },
        "latency_ms": {
            "graph_index_hydration": stats(load_times),
            "candidate_generation": stats(query_times),
            "cascaded_ranking": stats(ranking_times),
            "context_compilation": stats(compilation_times),
            "total_pipeline": stats(total_pipeline_times),
        },
        "memory": {
            "python_heap_peak_mb": stats(heap_peaks),
            "process_rss_start_mb": round(rss_start_mb, 2),
            "process_rss_end_mb": round(rss_end_mb, 2),
            "process_rss_delta_mb": round(rss_end_mb - rss_start_mb, 2),
        },
    }


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    bench_data = run_performance_benchmarks()
    out_file = RESULTS_DIR / "performance_benchmark.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(bench_data, f, indent=2)

    print(f"\nPerformance benchmark saved to: {out_file}")
    lat = bench_data["latency_ms"]
    mem = bench_data["memory"]
    print(f"  Graph Hydration Median:  {lat['graph_index_hydration']['median']} ms")
    print(f"  Cand Generation Median:  {lat['candidate_generation']['median']} ms")
    print(f"  Cascaded Ranking Median: {lat['cascaded_ranking']['median']} ms")
    print(f"  Compilation Median:      {lat['context_compilation']['median']} ms")
    print(f"  Pipeline Median Latency: {lat['total_pipeline']['median']} ms")
    print(f"  Pipeline P95 Latency:    {lat['total_pipeline']['p95']} ms")
    print(f"  Heap Peak Median:        {mem['python_heap_peak_mb']['median']} MB")
    print(f"  Process RSS Final:       {mem['process_rss_end_mb']} MB")


if __name__ == "__main__":
    main()
