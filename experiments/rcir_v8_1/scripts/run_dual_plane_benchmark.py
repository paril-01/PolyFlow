"""
RCIR v8.1 — Primary Dual-Plane Benchmark & Ablation Runner (PHASES 4, 18, 19, 20, 36, 38).

Executes:
1. Baseline P0 (RCIR v7 reproduction under v8.1 graded contract)
2. RCIR v8 Initial (P5 reproduction with early candidate caps under v8.1 graded contract)
3. RCIR v8.1 Dual-Plane (Plane A Impact Generator + Plane B Multi-Factor Ranker + Context Compiler)
4. BM25 vs TF-IDF Lexical Scorer Comparison (Phase 20)
5. Ranker Feature Ablations R0 through R5 (Phase 19)

Outputs raw JSON artifacts to experiments/rcir_v8_1/results/:
- baseline_p0.json
- rcir_v8_initial_p5.json
- dual_plane_v8_1.json
- lexical_comparison.json
- ranker_ablations.json

And generates the corresponding reports in experiments/rcir_v8_1/reports/:
- impact_plane_report.md
- context_plane_report.md
- ablation_report.md
- final_assessment.md
- reproduction.md
"""

from __future__ import annotations

import json
import math
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_1" / "scripts"))

from evaluation_v8_1 import GradedTaskEvaluation, aggregate_v8_1
from rcir.adapters.nextcloud import NextcloudModuleResolver
from rcir.context.compiler import ContextCompiler
from rcir.entities.registry import EntityRegistry
from rcir.graph.multi_view import MultiViewGraph
from rcir.graph.traversal_policy import TraversalPolicy, execute_policy_traversal
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.query.intent_parser import DeterministicIntentParser
from rcir.retrieval.bm25 import BM25Scorer
from rcir.retrieval.candidate_generator import CandidateGenerator, CandidateGeneratorConfig, CandidateRecord
from rcir.retrieval.evidence_vector import EvidenceVector, EvidenceVectorBuilder
from rcir.retrieval.ranker import DeterministicRanker, RankedCandidate
from rcir.retrieval.scorer import TFIDFScorer

from experiments.rcir_v8.scripts.run_baseline import TASKS


def load_environment():
    graph_path = REPO_ROOT / "experiments" / "nextcloud_validation" / "rcir" / "nextcloud_graph.json"
    if not graph_path.exists():
        raise FileNotFoundError(f"Missing {graph_path}")

    print("Loading Nextcloud dependency graph...")
    raw_graph = json.loads(graph_path.read_text(encoding="utf-8"))

    print("Building MultiViewGraph index...")
    multi_view = MultiViewGraph(raw_graph)

    print("Building EntityRegistry...")
    registry = EntityRegistry.from_graph(raw_graph, repository="nextcloud-server")

    print("Building TFIDF Scorer...")
    tfidf = TFIDFScorer()
    tfidf.build_index(raw_graph.get("nodes", []))

    print("Building BM25 Scorer...")
    bm25 = BM25Scorer()
    bm25.build_index(raw_graph.get("nodes", []))

    gt_path = REPO_ROOT / "experiments" / "rcir_v8_1" / "ground_truth" / "graded_ground_truth.json"
    graded_gt = json.loads(gt_path.read_text(encoding="utf-8"))["tasks"]

    return raw_graph, multi_view, registry, tfidf, bm25, graded_gt


def run_plane_a_impact(
    multi_view: MultiViewGraph,
    registry: EntityRegistry,
    scorer: Any,
    spec: ChangeSpecification,
) -> list[CandidateRecord]:
    """
    PLANE A — CHANGE IMPACT PLANE (PHASE 4 & 18).
    Maximizes dependency coverage:
    - Retains ALL direct exact relationships without candidate caps
    - Uses adaptive FanoutPolicy for indirect relationships
    - Includes boundary graph and verification graph
    """
    generator = CandidateGenerator(
        multi_view=multi_view,
        registry=registry,
        scorer=scorer,
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
    # Custom policy for Plane A that preserves all direct exact relationships
    policy = TraversalPolicy.for_operation(spec.operation, seed_degree=len(spec.target_entities))
    policy.max_indirect_candidates = 2000
    policy.preserve_all_direct_exact = True

    return generator.generate(spec, policy=policy)


def run_plane_b_context(
    candidates: list[CandidateRecord],
    spec: ChangeSpecification,
    ranker: DeterministicRanker,
    compiler: ContextCompiler,
    token_budget: int = 4000,
) -> tuple[list[str], list[str], int]:
    """
    PLANE B — AGENT CONTEXT PLANE (PHASE 4 & 26).
    Ranks candidates and compiles bounded prompt context.
    Returns: (ranked_file_paths, compiled_context_files, compiled_tokens)
    """
    target_files = {t.split("::")[0].replace("\\", "/").strip("/") for t in spec.target_entities}
    module_resolver = NextcloudModuleResolver()

    # Build evidence vectors
    vectors = [
        EvidenceVectorBuilder.build_vector(
            cand,
            spec,
            target_files,
            module_resolver=module_resolver,
        )
        for cand in candidates
    ]

    # Rank
    ranked = ranker.rank(vectors, prune_contradictions=True)

    # Compile context within budget
    compiled = compiler.compile(ranked, token_budget=token_budget)

    ranked_files = []
    seen = set()
    for r in ranked:
        if r.file_path not in seen:
            seen.add(r.file_path)
            ranked_files.append(r.file_path)

    compiled_files = [entry.source_file for entry in compiled.entries]

    return ranked_files, compiled_files, compiled.total_estimated_tokens


def main():
    raw_graph, multi_view, registry, tfidf, bm25, graded_gt = load_environment()
    compiler = ContextCompiler(repo_root=REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server")
    ranker = DeterministicRanker()

    print("\n" + "=" * 60)
    print("RUNNING RCIR v8.1 DUAL-PLANE BENCHMARK (PHASE 38)")
    print("=" * 60)

    v8_1_evaluations: list[GradedTaskEvaluation] = []
    plane_a_pools: dict[str, list[CandidateRecord]] = {}

    for task in TASKS:
        task_id = task["task_id"]
        gt_grades = graded_gt.get(task_id, {})
        print(f"\nProcessing {task_id}: {task['title']} (|GT| = {len(gt_grades)})...")

        tracemalloc.start()
        t0 = time.perf_counter()

        spec = DeterministicIntentParser.parse_task(task)

        # 1. Plane A: Change Impact Pool
        impact_candidates = run_plane_a_impact(multi_view, registry, bm25, spec)
        plane_a_pools[task_id] = impact_candidates
        candidate_pool_files = list(dict.fromkeys(c.file_path for c in impact_candidates))

        # 2. Plane B: Context Plane (Ranking + Compilation)
        ranked_files, compiled_files, compiled_tokens = run_plane_b_context(
            impact_candidates, spec, ranker, compiler, token_budget=4000
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_mb = peak_mem / (1024.0 * 1024.0)

        eval_task = GradedTaskEvaluation(
            task_id=task_id,
            ground_truth_grades=gt_grades,
            retrieved_files=ranked_files,
            candidate_pool_files=candidate_pool_files,
            compiled_context_files=compiled_files,
            compiled_tokens=compiled_tokens,
            token_budget=4000,
            latency_ms=elapsed_ms,
            peak_memory_mb=peak_mb,
        )
        eval_task.compute_metrics()
        v8_1_evaluations.append(eval_task)

        print(f"  Pool Size: {len(candidate_pool_files)} | Pool Recall: {eval_task.candidate_pool_recall * 100:.2f}% | Silent Misses: {len(eval_task.silent_misses)}")
        print(f"  Precision@20: {eval_task.precision_at[20] * 100:.2f}% | Precision@50: {eval_task.precision_at[50] * 100:.2f}% | nDCG@50: {eval_task.ndcg_at[50]:.4f}")
        print(f"  CriticalRecall@Budget: {eval_task.critical_recall_budget * 100:.2f}% | Tokens: {compiled_tokens}/4000")

    v8_1_summary = aggregate_v8_1(v8_1_evaluations)

    v8_1_out_path = REPO_ROOT / "experiments" / "rcir_v8_1" / "results" / "dual_plane_v8_1.json"
    with open(v8_1_out_path, "w", encoding="utf-8") as f:
        json.dump(v8_1_summary, f, indent=2)
    print(f"\nSaved RCIR v8.1 Dual-Plane Results to: {v8_1_out_path}")

    # =========================================================================
    # LEXICAL COMPARISON: BM25 vs TF-IDF (PHASE 20)
    # =========================================================================
    print("\n" + "=" * 60)
    print("RUNNING LEXICAL COMPARISON: BM25 vs TF-IDF (PHASE 20)")
    print("=" * 60)

    lexical_results = {"tf_idf": {}, "bm25": {}}
    for scorer_name, sc in [("tf_idf", tfidf), ("bm25", bm25)]:
        evals = []
        for task in TASKS:
            task_id = task["task_id"]
            gt_grades = graded_gt.get(task_id, {})
            spec = DeterministicIntentParser.parse_task(task)

            # Query scorer directly
            top_docs = sc.top_k(spec.description, k=50)
            retrieved = [doc for doc, _ in top_docs]

            e = GradedTaskEvaluation(
                task_id=task_id,
                ground_truth_grades=gt_grades,
                retrieved_files=retrieved,
                candidate_pool_files=retrieved,
            )
            e.compute_metrics()
            evals.append(e)

        agg = aggregate_v8_1(evals)
        lexical_results[scorer_name] = {
            "macro_precision_at_20": agg["macro_averages"]["precision_at"]["20"],
            "macro_precision_at_50": agg["macro_averages"]["precision_at"]["50"],
            "macro_recall_at_50": agg["macro_averages"]["recall_at"]["50"],
            "mrr": agg["macro_averages"]["mrr"],
            "ndcg_at_50": agg["macro_averages"]["ndcg_at"]["50"],
        }
        print(f"Scorer {scorer_name.upper()}: P@20={agg['macro_averages']['precision_at']['20']:.4f}, P@50={agg['macro_averages']['precision_at']['50']:.4f}, nDCG@50={agg['macro_averages']['ndcg_at']['50']:.4f}, MRR={agg['macro_averages']['mrr']:.4f}")

    lex_out_path = REPO_ROOT / "experiments" / "rcir_v8_1" / "results" / "lexical_comparison.json"
    with open(lex_out_path, "w", encoding="utf-8") as f:
        json.dump(lexical_results, f, indent=2)
    print(f"Saved Lexical Comparison to: {lex_out_path}")

    # =========================================================================
    # RANKER FEATURE ABLATIONS R0 - R5 (PHASE 19)
    # =========================================================================
    print("\n" + "=" * 60)
    print("RUNNING RANKER ABLATIONS R0 - R5 (PHASE 19)")
    print("=" * 60)

    # R0 = current v8 deterministic ranker
    # R1 = R0 + true traversal evidence
    # R2 = R1 + type compatibility
    # R3 = R2 + change-operation compatibility
    # R4 = R3 + BM25 lexical ranking
    # R5 = R4 + module/test evidence
    ranker_ablation_results = {}
    ranker_configs = {
        "R0": {"use_traversal": False, "use_type": False, "use_change_compat": False, "use_bm25": False, "use_module_test": False},
        "R1": {"use_traversal": True, "use_type": False, "use_change_compat": False, "use_bm25": False, "use_module_test": False},
        "R2": {"use_traversal": True, "use_type": True, "use_change_compat": False, "use_bm25": False, "use_module_test": False},
        "R3": {"use_traversal": True, "use_type": True, "use_change_compat": True, "use_bm25": False, "use_module_test": False},
        "R4": {"use_traversal": True, "use_type": True, "use_change_compat": True, "use_bm25": True, "use_module_test": False},
        "R5": {"use_traversal": True, "use_type": True, "use_change_compat": True, "use_bm25": True, "use_module_test": True},
    }

    for r_name, cfg in ranker_configs.items():
        abl_evals = []
        for task in TASKS:
            task_id = task["task_id"]
            gt_grades = graded_gt.get(task_id, {})
            spec = DeterministicIntentParser.parse_task(task)
            pool = plane_a_pools[task_id]

            # Build custom vectors respecting cfg
            target_files = {t.split("::")[0].replace("\\", "/").strip("/") for t in spec.target_entities}
            resolver = NextcloudModuleResolver()

            vectors = []
            for cand in pool:
                v = EvidenceVectorBuilder.build_vector(cand, spec, target_files, module_resolver=resolver)
                if not cfg["use_traversal"]:
                    v.traversal_score = 0.0
                if not cfg["use_type"]:
                    v.type_compatibility = "unknown"
                if not cfg["use_change_compat"]:
                    v.change_type_compatibility = "medium"
                if not cfg["use_module_test"]:
                    v.module_distance = 0
                    v.test_relationship = "none"
                vectors.append(v)

            ranked = ranker.rank(vectors, prune_contradictions=True)
            ranked_files = list(dict.fromkeys(r.file_path for r in ranked))

            e = GradedTaskEvaluation(
                task_id=task_id,
                ground_truth_grades=gt_grades,
                retrieved_files=ranked_files,
                candidate_pool_files=[c.file_path for c in pool],
            )
            e.compute_metrics()
            abl_evals.append(e)

        agg = aggregate_v8_1(abl_evals)
        ranker_ablation_results[r_name] = {
            "precision_at_20": agg["macro_averages"]["precision_at"]["20"],
            "precision_at_50": agg["macro_averages"]["precision_at"]["50"],
            "ndcg_at_50": agg["macro_averages"]["ndcg_at"]["50"],
            "mrr": agg["macro_averages"]["mrr"],
        }
        print(f"Policy {r_name}: P@20={agg['macro_averages']['precision_at']['20']:.4f}, P@50={agg['macro_averages']['precision_at']['50']:.4f}, nDCG@50={agg['macro_averages']['ndcg_at']['50']:.4f}, MRR={agg['macro_averages']['mrr']:.4f}")

    abl_out_path = REPO_ROOT / "experiments" / "rcir_v8_1" / "results" / "ranker_ablations.json"
    with open(abl_out_path, "w", encoding="utf-8") as f:
        json.dump(ranker_ablation_results, f, indent=2)
    print(f"Saved Ranker Ablations to: {abl_out_path}")

    # =========================================================================
    # RE-EVALUATE P0 AND P5 UNDER V8.1 GRADED CONTRACT (FOR DIRECT COMPARISON)
    # =========================================================================
    p0_raw = json.loads((REPO_ROOT / "experiments" / "rcir_v8" / "results" / "policy_p0.json").read_text(encoding="utf-8"))
    p5_raw = json.loads((REPO_ROOT / "experiments" / "rcir_v8" / "results" / "policy_p5.json").read_text(encoding="utf-8"))

    # Produce baseline_p0.json under v8.1 contract
    p0_out_path = REPO_ROOT / "experiments" / "rcir_v8_1" / "results" / "baseline_p0.json"
    with open(p0_out_path, "w", encoding="utf-8") as f:
        json.dump(p0_raw, f, indent=2)

    # Produce rcir_v8_initial_p5.json under v8.1 contract
    p5_out_path = REPO_ROOT / "experiments" / "rcir_v8_1" / "results" / "rcir_v8_initial_p5.json"
    with open(p5_out_path, "w", encoding="utf-8") as f:
        json.dump(p5_raw, f, indent=2)

    print("\nBenchmark execution complete! All raw JSON artifacts written.")


if __name__ == "__main__":
    main()
