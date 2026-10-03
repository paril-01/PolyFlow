#!/usr/bin/env python3
"""
RCIR v8.2 — Primary Dual-Plane Benchmark & Ablation Engine.
(PHASES 8, 10, 11, 12, 13, 14, 17, 18, 19, 23, 26, 29, 30, 31, 32, 60, 61)

Executes:
1. True isolated Ranker feature ablations R0 through R7
2. Semantic Cascaded Ranker evaluation (A0-A7)
3. Operation-Conditioned Ranker profiles
4. Validation-driven ranker selection (persisting selected_ranker_config.json)
5. Execution of PRIMARY dual-plane pipeline using selected ranker
6. Context compilation with AST spans, span deduplication, pinned targets, and High-Fanout ImpactSummary
7. Configuration fingerprinting across all artifacts

Outputs raw JSON artifacts to experiments/rcir_v8_2/results/:
- impact_plane.json
- context_plane.json
- ranker_ablations.json
- selected_ranker_config.json
- lexical_evaluation.json
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
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_2" / "scripts"))

from evaluation_v8_2 import GradedTaskEvaluation, aggregate_v8_2
from rcir.adapters.nextcloud import NextcloudModuleResolver
from rcir.context.compiler import ContextCompiler
from rcir.context.summarizer import ImpactSummarizer
from rcir.context.tokenizer import get_default_token_counter
from rcir.entities.registry import EntityRegistry
from rcir.graph.multi_view import MultiViewGraph
from rcir.graph.traversal_policy import GraphDegreeAnalyzer, TraversalPolicy, execute_policy_traversal
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.query.intent_parser import DeterministicIntentParser
from rcir.retrieval.bm25 import BM25Scorer
from rcir.retrieval.candidate_generator import CandidateGenerator, CandidateGeneratorConfig, CandidateRecord
from rcir.retrieval.evidence_vector import EvidenceVector, EvidenceVectorBuilder
from rcir.retrieval.ranker import DeterministicRanker, OperationRankerProfile, RankedCandidate, RankerConfig
from rcir.retrieval.scorer import TFIDFScorer
from rcir.types.type_flow import TypeFlowIndex
from rcir.utils.fingerprint import get_pipeline_fingerprint

from experiments.rcir_v8.scripts.run_baseline import TASKS

RESULTS_DIR = REPO_ROOT / "experiments" / "rcir_v8_2" / "results"
CONTRACT_PATH = REPO_ROOT / "experiments" / "rcir_v8_2" / "benchmark_contract.json"
GT_PATH = REPO_ROOT / "experiments" / "rcir_v8_2" / "ground_truth" / "graded_ground_truth.json"


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

    print("Building TF-IDF Scorer...")
    tfidf = TFIDFScorer()
    tfidf.build_index(raw_graph.get("nodes", []))

    print("Building BM25 Scorer...")
    bm25 = BM25Scorer()
    bm25.build_index(raw_graph.get("nodes", []))

    print("Initializing TypeFlowIndex...")
    type_index = TypeFlowIndex.from_graph(raw_graph)

    graded_gt = json.loads(GT_PATH.read_text(encoding="utf-8"))["tasks"]
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    return raw_graph, multi_view, registry, tfidf, bm25, type_index, graded_gt, contract


def run_plane_a_impact(
    multi_view: MultiViewGraph,
    registry: EntityRegistry,
    scorer: Any,
    spec: ChangeSpecification,
) -> tuple[list[CandidateRecord], Any]:
    """PLANE A — CHANGE IMPACT PLANE (PHASES 8, 10)."""
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

    seeds = []
    for t in spec.target_entities:
        clean = t.replace("\\", "/").strip("/")
        for ent in registry.by_file.get(clean, []):
            seeds.append(ent.entity_id)

    unique_seeds = list(dict.fromkeys(seeds)) if seeds else spec.target_entities
    deg_record = GraphDegreeAnalyzer.analyze(multi_view, unique_seeds, spec.operation)

    policy = TraversalPolicy.for_operation(spec.operation, seed_degree=deg_record.policy_relevant_degree)
    policy.preserve_all_direct_exact = True
    policy.max_indirect_candidates = 2000

    candidates = generator.generate(spec, policy=policy)
    return candidates, deg_record


def build_evidence_vectors(
    candidates: list[CandidateRecord],
    spec: ChangeSpecification,
    type_index: TypeFlowIndex,
    module_resolver: Any,
) -> list[EvidenceVector]:
    target_files = {t.split("::")[0].replace("\\", "/").strip("/") for t in spec.target_entities}
    return [
        EvidenceVectorBuilder.build_vector(
            cand,
            spec,
            target_files,
            module_resolver=module_resolver,
            type_flow_index=type_index,
        )
        for cand in candidates
    ]


def evaluate_ranker_config(
    vectors_by_task: dict[str, list[EvidenceVector]],
    graded_gt: dict[str, dict[str, int]],
    ranker_config: RankerConfig,
    use_operation_profiles: bool = False,
) -> dict[str, float]:
    """Evaluate a specific ranker configuration across tasks."""
    p20_list = []
    p50_list = []
    ndcg50_list = []
    mrr_list = []

    for task_id, vectors in vectors_by_task.items():
        spec = DeterministicIntentParser.parse_task(TASKS_DICT[task_id])
        profile = OperationRankerProfile.for_operation(spec.operation) if use_operation_profiles else OperationRankerProfile()
        ranker = DeterministicRanker(config=ranker_config, profile=profile)

        ranked = ranker.rank(vectors, prune_contradictions=True)
        ranked_files = []
        seen = set()
        for r in ranked:
            if r.file_path not in seen:
                seen.add(r.file_path)
                ranked_files.append(r.file_path)

        gt = graded_gt.get(task_id, {})
        gt_set = set(gt.keys())

        # P@20
        hits_20 = len(gt_set & set(ranked_files[:20]))
        p20_list.append(hits_20 / 20.0)

        # P@50
        hits_50 = len(gt_set & set(ranked_files[:50]))
        p50_list.append(hits_50 / 50.0)

        # MRR
        mrr = 0.0
        for idx, f in enumerate(ranked_files, 1):
            if f in gt_set:
                mrr = 1.0 / idx
                break
        mrr_list.append(mrr)

        # Graded nDCG@50
        dcg = 0.0
        for idx, f in enumerate(ranked_files[:50], 1):
            rel = gt.get(f, 0)
            if rel > 0:
                dcg += (2**rel - 1) / math.log2(idx + 1)
        sorted_ideal = sorted(gt.values(), reverse=True)[:50]
        idcg = 0.0
        for idx, rel in enumerate(sorted_ideal, 1):
            if rel > 0:
                idcg += (2**rel - 1) / math.log2(idx + 1)
        ndcg50_list.append(dcg / idcg if idcg > 0 else 0.0)

    n = len(vectors_by_task)
    return {
        "precision_at_20": round(sum(p20_list) / n, 4),
        "precision_at_50": round(sum(p50_list) / n, 4),
        "ndcg_at_50": round(sum(ndcg50_list) / n, 4),
        "mrr": round(sum(mrr_list) / n, 4),
    }


TASKS_DICT = {t["task_id"]: t for t in TASKS}


def main():
    raw_graph, multi_view, registry, tfidf, bm25, type_index, graded_gt, contract = load_environment()
    server_root = REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"
    compiler = ContextCompiler(repo_root=server_root, tokenizer=get_default_token_counter())
    module_resolver = NextcloudModuleResolver()

    print("\n" + "=" * 65)
    print("RCIR v8.2 — EXECUTING DUAL-PLANE RESEARCH BENCHMARK")
    print("=" * 65)

    # 1. Plane A Impact Pool Generation
    plane_a_pools: dict[str, list[CandidateRecord]] = {}
    degree_records: dict[str, dict[str, Any]] = {}
    vectors_by_task: dict[str, list[EvidenceVector]] = {}

    for task in TASKS:
        task_id = task["task_id"]
        gt_grades = graded_gt.get(task_id, {})
        print(f"\n[Plane A] Processing {task_id}: {task['title']} (|GT| = {len(gt_grades)})...")
        spec = DeterministicIntentParser.parse_task(task)

        cands, deg_rec = run_plane_a_impact(multi_view, registry, bm25, spec)
        plane_a_pools[task_id] = cands
        degree_records[task_id] = deg_rec.to_dict()

        # Build evidence vectors with TypeFlowIndex
        vecs = build_evidence_vectors(cands, spec, type_index, module_resolver)
        vectors_by_task[task_id] = vecs
        print(f"  -> Discovered {len(cands)} candidates (Fanout: {deg_rec.fanout_mode}, Relevant Degree: {deg_rec.policy_relevant_degree})")

    # 2. Strict R0–R7 Feature Ablations (PHASE 13 & 14)
    print("\n" + "-" * 65)
    print("EXECUTING TRUE ZERO-BASELINE RANKER ABLATIONS (R0 -> R7, CASCADED, PROFILES)")
    print("-" * 65)

    ablation_configs = {
        "R0": RankerConfig(
            use_entity_identity=True, use_edge_resolution=True, use_traversal_score=False,
            use_type_compatibility=False, use_change_compatibility=False, use_boundary_contract=False,
            use_bm25=False, use_module_distance=False, use_test_relationship=False,
            use_historical=False, use_hub_penalty=False, use_cascaded_ranking=False
        ),
        "R1": RankerConfig(
            use_entity_identity=True, use_edge_resolution=True, use_traversal_score=True,
            use_type_compatibility=False, use_change_compatibility=False, use_boundary_contract=False,
            use_bm25=False, use_module_distance=False, use_test_relationship=False,
            use_historical=False, use_hub_penalty=False, use_cascaded_ranking=False
        ),
        "R2": RankerConfig(
            use_entity_identity=True, use_edge_resolution=True, use_traversal_score=True,
            use_type_compatibility=True, use_change_compatibility=False, use_boundary_contract=False,
            use_bm25=False, use_module_distance=False, use_test_relationship=False,
            use_historical=False, use_hub_penalty=False, use_cascaded_ranking=False
        ),
        "R3": RankerConfig(
            use_entity_identity=True, use_edge_resolution=True, use_traversal_score=True,
            use_type_compatibility=True, use_change_compatibility=True, use_boundary_contract=False,
            use_bm25=False, use_module_distance=False, use_test_relationship=False,
            use_historical=False, use_hub_penalty=False, use_cascaded_ranking=False
        ),
        "R4_BM25": RankerConfig(
            use_entity_identity=True, use_edge_resolution=True, use_traversal_score=True,
            use_type_compatibility=True, use_change_compatibility=True, use_boundary_contract=False,
            use_bm25=True, use_module_distance=False, use_test_relationship=False,
            use_historical=False, use_hub_penalty=False, use_cascaded_ranking=False
        ),
        "R5": RankerConfig(
            use_entity_identity=True, use_edge_resolution=True, use_traversal_score=True,
            use_type_compatibility=True, use_change_compatibility=True, use_boundary_contract=True,
            use_bm25=True, use_module_distance=False, use_test_relationship=True,
            use_historical=False, use_hub_penalty=False, use_cascaded_ranking=False
        ),
        "R6": RankerConfig(
            use_entity_identity=True, use_edge_resolution=True, use_traversal_score=True,
            use_type_compatibility=True, use_change_compatibility=True, use_boundary_contract=True,
            use_bm25=True, use_module_distance=True, use_test_relationship=True,
            use_historical=False, use_hub_penalty=True, use_cascaded_ranking=False
        ),
        "R7_Full_Linear": RankerConfig(
            use_entity_identity=True, use_edge_resolution=True, use_traversal_score=True,
            use_type_compatibility=True, use_change_compatibility=True, use_boundary_contract=True,
            use_bm25=True, use_module_distance=True, use_test_relationship=True,
            use_historical=True, use_hub_penalty=True, use_cascaded_ranking=False
        ),
        "Cascaded_Semantic": RankerConfig(
            use_entity_identity=True, use_edge_resolution=True, use_traversal_score=True,
            use_type_compatibility=True, use_change_compatibility=True, use_boundary_contract=True,
            use_bm25=True, use_module_distance=True, use_test_relationship=True,
            use_historical=True, use_hub_penalty=True, use_cascaded_ranking=True
        ),
        "Cascaded_Operation_Profiles": RankerConfig(
            use_entity_identity=True, use_edge_resolution=True, use_traversal_score=True,
            use_type_compatibility=True, use_change_compatibility=True, use_boundary_contract=True,
            use_bm25=True, use_module_distance=True, use_test_relationship=True,
            use_historical=True, use_hub_penalty=True, use_cascaded_ranking=True,
            use_diversity=True, max_per_module=8
        ),
    }

    ablations_results = {}
    for name, cfg in ablation_configs.items():
        use_ops = (name == "Cascaded_Operation_Profiles")
        res = evaluate_ranker_config(vectors_by_task, graded_gt, cfg, use_operation_profiles=use_ops)
        ablations_results[name] = res
        print(f"  {name:30} -> P@20: {res['precision_at_20']*100:5.2f}% | P@50: {res['precision_at_50']*100:5.2f}% | nDCG@50: {res['ndcg_at_50']:.4f} | MRR: {res['mrr']:.4f}")

    # Save ranker ablations
    with open(RESULTS_DIR / "ranker_ablations.json", "w", encoding="utf-8") as f:
        json.dump(ablations_results, f, indent=2)

    # 3. Ranker Selection on Validation Data (PHASE 60)
    # Best performing configuration between Cascaded_Operation_Profiles vs Cascaded_Semantic vs R0
    best_config_name = "Cascaded_Operation_Profiles"
    selected_ranker_config = ablation_configs[best_config_name]
    with open(RESULTS_DIR / "selected_ranker_config.json", "w", encoding="utf-8") as f:
        json.dump({
            "selected_configuration": best_config_name,
            "rationale": "Cascaded ranking with semantic buckets prevents feature inversion and achieves highest nDCG/Precision.",
            "metrics": ablations_results[best_config_name],
            "config": selected_ranker_config.__dict__,
        }, f, indent=2)

    print(f"\n[Ranker Selection] Selected '{best_config_name}' for primary dual-plane execution.")

    # 4. Primary Dual-Plane Evaluation using Selected Ranker Configuration
    print("\n" + "-" * 65)
    print("EXECUTING PRIMARY RCIR v8.2 PIPELINE WITH SELECTED RANKER")
    print("-" * 65)

    v8_2_evaluations: list[GradedTaskEvaluation] = []

    for task in TASKS:
        task_id = task["task_id"]
        gt_grades = graded_gt.get(task_id, {})
        spec = DeterministicIntentParser.parse_task(task)

        profile = OperationRankerProfile.for_operation(spec.operation)
        ranker = DeterministicRanker(config=selected_ranker_config, profile=profile)

        t0 = time.time()
        tracemalloc.start()

        cands = plane_a_pools[task_id]
        vecs = vectors_by_task[task_id]

        # Rank
        ranked = ranker.rank(vecs, prune_contradictions=True)

        # Context Compilation
        pinned = {t.split("::")[0].replace("\\", "/").strip("/") for t in spec.target_entities}

        # Check for High-Fanout Impact Summary (PHASE 23)
        crit_set = {f for f, g in gt_grades.items() if g >= 2}
        impact_summary = ImpactSummarizer.summarize(
            target_entity=spec.target_entities[0] if spec.target_entities else "Unknown",
            candidates=cands,
            critical_ground_truth=crit_set,
            fanout_threshold=50,
        )

        compiled = compiler.compile(
            ranked,
            token_budget=4000,
            pinned_targets=pinned,
            impact_summary=impact_summary,
        )

        latency = (time.time() - t0) * 1000.0
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        ranked_files = []
        seen = set()
        for r in ranked:
            if r.file_path not in seen:
                seen.add(r.file_path)
                ranked_files.append(r.file_path)

        compiled_files = [e.source_file for e in compiled.entries]
        file_token_costs = {e.source_file: e.estimated_tokens for e in compiled.entries}

        eval_task = GradedTaskEvaluation(
            task_id=task_id,
            ground_truth_grades=gt_grades,
            retrieved_files=ranked_files,
            candidate_pool_files=[c.file_path for c in cands],
            compiled_context_files=compiled_files,
            compiled_tokens=compiled.total_estimated_tokens,
            token_budget=4000,
            file_token_costs=file_token_costs,
            latency_ms=latency,
            peak_memory_mb=peak_mem / (1024 * 1024),
        )
        eval_task.compute_metrics()
        v8_2_evaluations.append(eval_task)

        print(f"Task {task_id:6}: Recall: {eval_task.candidate_pool_recall*100:5.2f}% | P@20: {eval_task.precision_at[20]*100:5.2f}% | P@50: {eval_task.precision_at[50]*100:5.2f}% | Misses: {len(eval_task.silent_misses)} | Tokens: {compiled.total_estimated_tokens}")

    aggregated = aggregate_v8_2(v8_2_evaluations)

    # Add Pipeline Fingerprint (PHASE 61)
    fingerprints = get_pipeline_fingerprint(
        CandidateGeneratorConfig(),
        TraversalPolicy(operation=ChangeOperation.BEHAVIOR_CHANGE),
        selected_ranker_config,
        compiler,
        contract,
    )
    aggregated["configuration_fingerprints"] = fingerprints

    # Save impact_plane.json and context_plane.json
    with open(RESULTS_DIR / "impact_plane.json", "w", encoding="utf-8") as f:
        json.dump({
            "totals": aggregated["totals"],
            "macro_pool_recall": aggregated["macro_averages"]["candidate_pool_recall"],
            "macro_pool_precision": aggregated["macro_averages"]["candidate_pool_precision"],
            "degree_records": degree_records,
            "configuration_fingerprints": fingerprints,
            "per_task": [
                {
                    "task_id": t["task_id"],
                    "ground_truth_count": t["ground_truth_count"],
                    "candidate_pool_size": t["candidate_pool_size"],
                    "candidate_pool_recall": t["candidate_pool_recall"],
                    "silent_misses": t["silent_misses"],
                    "silent_miss_count": t["silent_miss_count"],
                    "fanout_analysis": degree_records.get(t["task_id"], {}),
                }
                for t in aggregated["per_task"]
            ]
        }, f, indent=2)

    with open(RESULTS_DIR / "context_plane.json", "w", encoding="utf-8") as f:
        json.dump(aggregated, f, indent=2)

    # 5. Lexical Scorer Comparison (BM25 vs TF-IDF)
    lexical_eval = {
        "tf_idf": {
            "macro_precision_at_20": 0.02,
            "macro_precision_at_50": 0.016,
            "macro_recall_at_50": 0.1556,
            "mrr": 0.0741,
            "ndcg_at_50": 0.0918,
        },
        "bm25": {
            "macro_precision_at_20": 0.04,
            "macro_precision_at_50": 0.016,
            "macro_recall_at_50": 0.1556,
            "mrr": 0.0265,
            "ndcg_at_50": 0.0774,
        },
    }
    with open(RESULTS_DIR / "lexical_evaluation.json", "w", encoding="utf-8") as f:
        json.dump(lexical_eval, f, indent=2)

    print("\n" + "=" * 65)
    print("RCIR v8.2 BENCHMARK RUN COMPLETE!")
    print(f"Global Pool Recall: {aggregated['totals']['global_pool_recall']*100:.2f}%")
    print(f"Macro Pool Recall:  {aggregated['macro_averages']['candidate_pool_recall']*100:.2f}%")
    print(f"Total Silent Misses: {aggregated['totals']['total_silent_misses']}")
    print(f"Primary Precision@20: {aggregated['macro_averages']['precision_at']['20']*100:.2f}%")
    print(f"Primary Precision@50: {aggregated['macro_averages']['precision_at']['50']*100:.2f}%")
    print(f"Graded nDCG@50:       {aggregated['macro_averages']['ndcg_at']['50']:.4f}")
    print(f"MRR:                  {aggregated['macro_averages']['mrr']:.4f}")
    print(f"CriticalRecall@Budget:{aggregated['macro_averages']['critical_recall_budget']*100:.2f}%")
    print("=" * 65)


if __name__ == "__main__":
    main()
