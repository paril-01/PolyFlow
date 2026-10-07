"""
RCIR v8.5 — Semantic Multi-Channel Impact Discovery & Validation-Selected Ranker (PHASES 46-63).

Implements 7 Semantic Discovery Channels:
- Channel A: Exact Graph (direct callers, callees, imports, inherits, implements, overrides, constructs, injects)
- Channel B: Type Flow (receiver-resolved call sites, implementation owners, dynamic receivers)
- Channel C: Boundary (route_to_controller, frontend_to_route, service boundaries)
- Channel D: Events (event_dispatch, event_listener, event_payload)
- Channel E: Config / DI (constructor injections, service registration, config_reads, config_writes)
- Channel F: Verification (source_to_test, test fixtures, contract tests)
- Channel G: Lexical Fallback (BM25 symbol matching only when needed, explicitly labeled)

Features:
- Deterministic Evidence Fusion (Phase 54 & 55): deduplicates entities with fused evidence.
- Operation-Aware Traversal (Phase 57).
- Direct exact edges always survive (Phase 59).
- Standard P@K (denominators 20 and 50) and target-exclusion metrics (Phase 47 & 49).
- Graded nDCG@50 (grades 3, 2, 1) and Dependency MRR (Phase 46 & 48).
- Computed Ranker Selection on VALIDATION split (Phase 50, 51, 52).
- One frozen execution on TEST split using selected configuration.
- Generates raw/retrieval/*.json, results/ranker_*.json, and results/selected_ranker_config.json.
"""

from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from environment import get_default_environment

env = get_default_environment()
sys.path.insert(0, str(env.polyflow_root / "rcir" / "src"))

from rcir.adapters.nextcloud import NextcloudSourceDerivedAdapter
from rcir.entities.canonical import CanonicalEntityRegistry, CanonicalEntityID, EntityKind
from rcir.graph.canonical_graph import CanonicalGraph, CanonicalEdge, CanonicalEdgeType, ResolutionClass
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.retrieval.evidence_vector import EvidenceVector
from rcir.retrieval.ranker import (
    DeterministicRanker,
    MultiObjectiveRanker,
    OperationRankerProfile,
    RankedCandidate,
    RankerConfig,
)


@dataclass
class ChannelDiscoveryResult:
    candidates: dict[str, EvidenceVector] = field(default_factory=dict)
    channel_counts: dict[str, int] = field(default_factory=dict)


def discover_multi_channel_candidates(
    spec: ChangeSpecification,
    cg: CanonicalGraph,
    registry: CanonicalEntityRegistry,
) -> ChannelDiscoveryResult:
    """Execute 7-channel semantic discovery (PHASE 53-60)."""
    candidates: dict[str, EvidenceVector] = {}
    channel_counts: dict[str, int] = {
        "channel_a_exact_graph": 0,
        "channel_b_type_flow": 0,
        "channel_c_boundary": 0,
        "channel_d_events": 0,
        "channel_e_config": 0,
        "channel_f_verification": 0,
        "channel_g_lexical": 0,
    }

    # 1. Target resolution
    target_res = registry.resolve(spec.requested_symbol, target_file_hint=spec.target_file_hint)
    resolved_target_id = target_res.canonical_id or (spec.canonical_target_ids[0] if spec.canonical_target_ids else spec.requested_symbol)

    target_fp = spec.target_file_hint or ""
    if not target_fp and resolved_target_id in cg.nodes:
        target_fp = cg.nodes[resolved_target_id].file

    # Target candidate (rank 0 / pinned)
    candidates[resolved_target_id] = EvidenceVector(
        entity_id=resolved_target_id,
        file_path=target_fp,
        entity_match="exact",
        resolution_class="static_exact",
        traversal_score=1.0,
        hop_distance=0,
    )

    # Roots for graph expansion
    roots = [resolved_target_id]
    if "::" in resolved_target_id:
        owner_id = resolved_target_id.split("::")[0]
        owner_res = registry.resolve(owner_id)
        if owner_res.canonical_id and owner_res.canonical_id not in roots:
            roots.append(owner_res.canonical_id)
    if target_fp:
        file_res = registry.resolve(target_fp)
        if file_res.canonical_id and file_res.canonical_id not in roots:
            roots.append(file_res.canonical_id)

    # CHANNEL A — EXACT GRAPH (Phase 53)
    for root_id in roots:
        incoming = cg.get_incoming_edges(root_id)
        outgoing = cg.get_outgoing_edges(root_id)

        # Incoming edges (callers, overrides, implementations)
        for e in incoming:
            src_id = e.source_id
            src_node = cg.nodes.get(src_id)
            if not src_node:
                s_res = registry.resolve(src_id)
                src_node = cg.nodes.get(s_res.canonical_id) if s_res.canonical_id else None
            src_fp = src_node.file if src_node else src_id.split("::")[0].replace("php://", "").replace("ts://", "").replace("external://", "")

            channel_counts["channel_a_exact_graph"] += 1
            if src_id not in candidates:
                candidates[src_id] = EvidenceVector(
                    entity_id=src_id,
                    file_path=src_fp,
                    entity_match="alias" if target_res.canonical_id == src_id else "none",
                    resolution_class=e.resolution_class.value,
                    edge_types=[e.edge_type.value],
                    hop_distance=1,
                    traversal_score=0.85,
                )
            else:
                existing = candidates[src_id]
                if e.edge_type.value not in existing.edge_types:
                    existing.edge_types.append(e.edge_type.value)

        # Outgoing edges (callees, dependencies, inherits)
        for e in outgoing:
            tgt_id = e.target_id
            tgt_node = cg.nodes.get(tgt_id)
            if not tgt_node:
                t_res = registry.resolve(tgt_id)
                tgt_node = cg.nodes.get(t_res.canonical_id) if t_res.canonical_id else None
            tgt_fp = tgt_node.file if tgt_node else tgt_id.split("::")[0].replace("php://", "").replace("ts://", "").replace("external://", "")

            channel_counts["channel_a_exact_graph"] += 1
            if tgt_id not in candidates:
                candidates[tgt_id] = EvidenceVector(
                    entity_id=tgt_id,
                    file_path=tgt_fp,
                    entity_match="none",
                    resolution_class=e.resolution_class.value,
                    edge_types=[e.edge_type.value],
                    hop_distance=1,
                    traversal_score=0.80,
                )
            else:
                existing = candidates[tgt_id]
                if e.edge_type.value not in existing.edge_types:
                    existing.edge_types.append(e.edge_type.value)

    # CHANNEL B — TYPE FLOW & IMPLEMENTATIONS (Phase 53 Channel B)
    # Search actual implementation hierarchy for interfaces / classes
    for root_id in roots:
        for ent_id, ent in cg.nodes.items():
            if ent.kind in (EntityKind.CLASS, EntityKind.INTERFACE):
                # Verify true hierarchy: check implements/inherits in graph edges or verified aliases
                is_hierarchy_match = False
                if root_id in ent.aliases:
                    is_hierarchy_match = True
                else:
                    # Check edges between ent_id and root_id
                    for edge in cg.get_outgoing_edges(ent_id):
                        if edge.target_id == root_id and edge.edge_type.value in ("implements", "inherits"):
                            is_hierarchy_match = True
                            break
                    if not is_hierarchy_match:
                        for edge in cg.get_incoming_edges(root_id):
                            if edge.source_id == ent_id and edge.edge_type.value in ("implements", "inherits"):
                                is_hierarchy_match = True
                                break

                if is_hierarchy_match:
                    channel_counts["channel_b_type_flow"] += 1
                    if ent_id not in candidates:
                        candidates[ent_id] = EvidenceVector(
                            entity_id=ent_id,
                            file_path=ent.file,
                            entity_match="none",
                            resolution_class="static_inference",
                            type_compatibility="compatible",
                            edge_types=["implements"],
                            hop_distance=1,
                            traversal_score=0.82,
                        )

    # CHANNEL C — BOUNDARY (Phase 53 Channel C: source-derived routes parsing)
    route_matches = NextcloudSourceDerivedAdapter.discover_routes(
        env.target_repo_root, target_fp, spec.requested_symbol
    )
    for rm in route_matches:
        channel_counts["channel_c_boundary"] += 1
        if rm.entity_id not in candidates:
            candidates[rm.entity_id] = EvidenceVector(
                entity_id=rm.entity_id,
                file_path=rm.file_path,
                boundary_contract="route",
                resolution_class="static_inference",
                edge_types=[rm.evidence_type],
                hop_distance=1,
                traversal_score=rm.confidence,
            )

    # CHANNEL D — EVENTS (Phase 53 Channel D: source-derived event dispatchers)
    if "Event" in resolved_target_id or spec.operation == ChangeOperation.EVENT_CHANGE:
        event_matches = NextcloudSourceDerivedAdapter.discover_event_dispatchers(
            env.target_repo_root, resolved_target_id, cg.nodes
        )
        for em in event_matches:
            channel_counts["channel_d_events"] += 1
            if em.entity_id not in candidates:
                candidates[em.entity_id] = EvidenceVector(
                    entity_id=em.entity_id,
                    file_path=em.file_path,
                    boundary_contract="event",
                    resolution_class="static_inference",
                    edge_types=[em.evidence_type],
                    hop_distance=1,
                    traversal_score=em.confidence,
                )

    # CHANNEL E — CONFIG / DI (Phase 53 Channel E: source-derived config usage)
    if "Config" in resolved_target_id or spec.operation == ChangeOperation.CONFIG_CHANGE:
        config_matches = NextcloudSourceDerivedAdapter.discover_config_di(
            env.target_repo_root, target_fp, cg.nodes
        )
        for cm in config_matches:
            channel_counts["channel_e_config"] += 1
            if cm.entity_id not in candidates:
                candidates[cm.entity_id] = EvidenceVector(
                    entity_id=cm.entity_id,
                    file_path=cm.file_path,
                    boundary_contract="config",
                    resolution_class="static_inference",
                    edge_types=[cm.evidence_type],
                    hop_distance=1,
                    traversal_score=cm.confidence,
                )

    # CHANNEL F — VERIFICATION (Phase 53 Channel F: source-derived test discovery)
    if target_fp:
        test_matches = NextcloudSourceDerivedAdapter.discover_tests(
            env.target_repo_root, target_fp, spec.requested_symbol
        )
        for tm in test_matches:
            channel_counts["channel_f_verification"] += 1
            if tm.entity_id not in candidates:
                candidates[tm.entity_id] = EvidenceVector(
                    entity_id=tm.entity_id,
                    file_path=tm.file_path,
                    test_relationship="direct_test",
                    resolution_class="static_inference",
                    edge_types=[tm.evidence_type],
                    hop_distance=1,
                    traversal_score=tm.confidence,
                )

    # CHANNEL G — LEXICAL FALLBACK (Phase 53 Channel G)
    # Only if candidate pool is small, search symbol occurrences
    if len(candidates) < 15 and spec.requested_symbol:
        sym_clean = spec.requested_symbol.lower()
        for ent_id, ent in cg.nodes.items():
            if sym_clean in ent.symbol.lower() or sym_clean in ent.file.lower():
                if ent_id not in candidates:
                    channel_counts["channel_g_lexical"] += 1
                    candidates[ent_id] = EvidenceVector(
                        entity_id=ent_id,
                        file_path=ent.file,
                        bm25_score=3.5,
                        resolution_class="not_analyzed",
                        edge_types=["lexical_match"],
                        hop_distance=2,
                        traversal_score=0.45,
                    )
                if len(candidates) >= 30:
                    break

    # Adaptive 2-hop expansion for justified paths (Phase 60)
    # Only expand interface -> implementation -> callers or controller -> routes
    first_hop_keys = [k for k in candidates if candidates[k].hop_distance == 1]
    # Sort deterministically using semantic priority (Phase 58)
    first_hop_keys.sort(key=lambda k: (
        0 if any(et in ("implements", "inherits", "route_to_controller") for et in candidates[k].edge_types) else 1,
        candidates[k].entity_id
    ))

    for hop1_id in first_hop_keys[:25]:
        hop1_vec = candidates[hop1_id]
        # 1. Incoming transitive edges (callers of implementation, etc.)
        if any(et in ("implements", "inherits", "route_to_controller", "injects") for et in hop1_vec.edge_types):
            h2_in = cg.get_incoming_edges(hop1_id)
            for e2 in h2_in[:10]:
                s2_id = e2.source_id
                if s2_id not in candidates:
                    s2_node = cg.nodes.get(s2_id)
                    s2_fp = s2_node.file if s2_node else s2_id.split("::")[0].replace("php://", "").replace("ts://", "")
                    candidates[s2_id] = EvidenceVector(
                        entity_id=s2_id,
                        file_path=s2_fp,
                        resolution_class=e2.resolution_class.value,
                        edge_types=[e2.edge_type.value],
                        hop_distance=2,
                        traversal_score=0.65,
                    )
        # 2. Outgoing transitive dependencies of direct consumers (sibling services, boundary routes)
        if any(et in ("injects", "calls", "route_to_controller", "imports") for et in hop1_vec.edge_types):
            h2_out = cg.get_outgoing_edges(hop1_id)
            for e2 in h2_out[:20]:
                t2_id = e2.target_id
                if t2_id not in candidates:
                    t2_node = cg.nodes.get(t2_id)
                    t2_fp = t2_node.file if t2_node else t2_id.split("::")[0].replace("php://", "").replace("ts://", "")
                    candidates[t2_id] = EvidenceVector(
                        entity_id=t2_id,
                        file_path=t2_fp,
                        resolution_class=e2.resolution_class.value,
                        edge_types=[e2.edge_type.value],
                        hop_distance=2,
                        traversal_score=0.60,
                    )

    return ChannelDiscoveryResult(candidates=candidates, channel_counts=channel_counts)


def compute_split_metrics(
    ranked_results: dict[str, list[RankedCandidate]],
    gt_tasks: dict[str, Any],
) -> dict[str, Any]:
    """Compute formal metrics adhering to Phases 46-49."""
    task_recalls = []
    task_p20_excl = []
    task_p50_excl = []
    task_dep_mrr = []
    task_ndcg = []
    silent_misses = 0

    for tid, ranked_cands in ranked_results.items():
        task = gt_tasks.get(tid)
        if not task:
            continue

        target_file = task.get("target_file", "")
        expected_files = set(task.get("expected_files", []))
        critical_files = set(task.get("critical_files", []))
        must_change = set(task.get("must_change", []))
        must_inspect = set(task.get("must_inspect", []))

        # Retrieved files pool
        retrieved_files = {c.file_path for c in ranked_cands if c.file_path}

        # Per-task recall
        matched_expected = expected_files.intersection(retrieved_files)
        recall = len(matched_expected) / max(1, len(expected_files))
        task_recalls.append(recall)

        misses = len(expected_files - retrieved_files)
        silent_misses += misses

        # Target-exclusion ranking (PHASE 49)
        cands_excl_target = [c for c in ranked_cands if c.file_path != target_file]

        # File-level deduplication (F03): deduplicate ranked candidates by file path (first occurrence)
        seen_files = set()
        deduped_cands = []
        for c in cands_excl_target:
            if c.file_path and c.file_path not in seen_files:
                seen_files.add(c.file_path)
                deduped_cands.append(c)

        # P@20 excluding target (PHASE 47: Denominator is 20)
        top_20 = deduped_cands[:20]
        rel_20 = [c for c in top_20 if c.file_path in expected_files]
        p_at_20 = len(rel_20) / 20.0
        task_p20_excl.append(p_at_20)

        # P@50 excluding target (PHASE 47: Denominator is 50)
        top_50 = deduped_cands[:50]
        rel_50 = [c for c in top_50 if c.file_path in expected_files]
        p_at_50 = len(rel_50) / 50.0
        task_p50_excl.append(p_at_50)

        # Dependency MRR (PHASE 46: Excludes target entity)
        dep_mrr = 0.0
        for rank_idx, c in enumerate(deduped_cands[:100], 1):
            if c.file_path in expected_files:
                dep_mrr = 1.0 / rank_idx
                break
        task_dep_mrr.append(dep_mrr)

        # Graded nDCG@50 (PHASE 48: 3 for MUST_CHANGE, 2 for MUST_INSPECT, 1 for SUPPORTING)
        dcg = 0.0
        for r_idx, c in enumerate(top_50, 1):
            fp = c.file_path
            if fp in must_change:
                grade = 3
            elif fp in must_inspect:
                grade = 2
            elif fp in expected_files:
                grade = 1
            else:
                grade = 0
            if grade > 0:
                dcg += (2**grade - 1) / math.log2(r_idx + 1)

        # Ideal DCG@50
        ideal_grades = []
        for fp in expected_files:
            if fp == target_file:
                continue
            if fp in must_change:
                ideal_grades.append(3)
            elif fp in must_inspect:
                ideal_grades.append(2)
            else:
                ideal_grades.append(1)
        ideal_grades.sort(reverse=True)
        ideal_grades = ideal_grades[:50]

        idcg = sum((2**g - 1) / math.log2(idx + 1) for idx, g in enumerate(ideal_grades, 1))
        ndcg_50 = (dcg / idcg) if idcg > 0 else 0.0
        task_ndcg.append(ndcg_50)

    n_tasks = max(1, len(task_recalls))
    macro_recall = sum(task_recalls) / n_tasks
    worst_task_recall = min(task_recalls) if task_recalls else 0.0
    mean_p20 = sum(task_p20_excl) / n_tasks
    mean_p50 = sum(task_p50_excl) / n_tasks
    mean_dep_mrr = sum(task_dep_mrr) / n_tasks
    mean_ndcg = sum(task_ndcg) / n_tasks

    # Frozen Multi-Objective Optimization Score (PHASE 52)
    multi_objective_score = (
        0.25 * macro_recall
        + 0.25 * worst_task_recall
        + 0.20 * mean_p20
        + 0.15 * mean_ndcg
        + 0.15 * mean_dep_mrr
    )

    return {
        "macro_pool_recall": round(macro_recall, 4),
        "worst_task_pool_recall": round(worst_task_recall, 4),
        "precision_at_20_excluding_target": round(mean_p20, 4),
        "precision_at_50_excluding_target": round(mean_p50, 4),
        "dependency_mrr": round(mean_dep_mrr, 4),
        "graded_ndcg_at_50": round(mean_ndcg, 4),
        "multi_objective_score": round(multi_objective_score, 4),
        "silent_misses": silent_misses,
        "total_tasks_evaluated": len(task_recalls),
    }


def execute_retrieval_suite():
    print("=" * 80)
    print("RCIR v8.5 — Semantic Multi-Channel Retrieval & Validation Selection")
    print("=" * 80)

    # 1. Load full Canonical Graph
    t0 = time.time()
    with open(env.graph_path, "r", encoding="utf-8") as f:
        raw_graph = json.load(f)
    cg = CanonicalGraph.from_legacy_dict(raw_graph, target_repo_root=env.target_repo_root)
    registry = cg.registry
    print(f"Loaded graph in {time.time() - t0:.2f}s with {len(registry.entities)} registry entities.")

    # 2. Load Ground Truth
    gt_data = json.loads((env.ground_truth_root / "ground_truth.json").read_text(encoding="utf-8"))
    gt_tasks = gt_data["tasks"]

    # 3. Candidate generation for each split
    splits_candidates: dict[str, dict[str, list[EvidenceVector]]] = {}
    splits_channel_stats: dict[str, dict[str, int]] = {}

    for split in ("dev", "validation", "test"):
        dataset = json.loads((env.dataset_root / f"{split}.json").read_text(encoding="utf-8"))
        tasks = dataset["tasks"]
        print(f"Discovering multi-channel candidates for {split.upper()} ({len(tasks)} tasks)...")

        split_cands: dict[str, list[EvidenceVector]] = {}
        split_stats: dict[str, int] = {}

        for task in tasks:
            tid = task["task_id"]
            spec_data = task["spec"]
            op_str = spec_data.get("operation", "behavior_change")
            try:
                op = ChangeOperation(op_str)
            except ValueError:
                op = ChangeOperation.BEHAVIOR_CHANGE

            spec = ChangeSpecification(
                operation=op,
                requested_symbol=spec_data.get("requested_symbol", ""),
                target_file_hint=spec_data.get("target_file_hint"),
                canonical_target_ids=spec_data.get("canonical_target_ids", []),
                description=task.get("description", ""),
            )

            res = discover_multi_channel_candidates(spec, cg, registry)
            split_cands[tid] = list(res.candidates.values())

            for ch, cnt in res.channel_counts.items():
                split_stats[ch] = split_stats.get(ch, 0) + cnt

        splits_candidates[split] = split_cands
        splits_channel_stats[split] = split_stats

    # 4. VALIDATION-BASED RANKER SELECTION (PHASE 50, 51, 52)
    # Define candidate ranker configurations
    ranker_candidate_configs = {
        "R0": {
            "name": "R0_GraphDistanceBaseline",
            "type": "linear",
            "config": RankerConfig(use_cascaded_ranking=False, use_diversity=False),
        },
        "ExactFirst": {
            "name": "ExactFirstCascaded",
            "type": "cascaded",
            "config": RankerConfig(use_cascaded_ranking=True, use_diversity=False),
        },
        "OperationCascade": {
            "name": "OperationAwareCascade",
            "type": "operation_cascaded",
            "config": RankerConfig(use_cascaded_ranking=True, use_diversity=False),
        },
        "Coverage": {
            "name": "CoverageDiversityRanker",
            "type": "diversity",
            "config": RankerConfig(use_cascaded_ranking=False, use_diversity=True, max_per_module=5),
        },
        "AnchorCoverageRRF": {
            "name": "AnchorCoverageRRF_MultiObjective",
            "type": "multi_objective_rrf",
            "config": None,
        },
    }

def build_ranker(config_name: str, operation: Optional[str] = None) -> Any:
    """Centralized ranker factory used across retrieval runner, validation selection, TEST execution, and determinism evaluation (v8.5.1)."""
    cfg = (config_name or "").strip()
    if cfg in ("R0", "R0_GraphDistanceBaseline", "linear"):
        return DeterministicRanker(RankerConfig(use_cascaded_ranking=False, use_diversity=False))
    elif cfg in ("ExactFirst", "ExactFirstCascaded", "cascaded"):
        return DeterministicRanker(RankerConfig(use_cascaded_ranking=True, use_diversity=False))
    elif cfg in ("OperationCascade", "OperationAwareCascade", "operation_cascaded"):
        profile = OperationRankerProfile.for_operation(operation) if operation else None
        return DeterministicRanker(RankerConfig(use_cascaded_ranking=True, use_diversity=False), profile=profile)
    elif cfg in ("Coverage", "CoverageDiversityRanker", "diversity"):
        return DeterministicRanker(RankerConfig(use_cascaded_ranking=False, use_diversity=True, max_per_module=5))
    elif cfg in ("AnchorCoverageRRF", "AnchorCoverageRRF_MultiObjective", "multi_objective_rrf"):
        return MultiObjectiveRanker(operation=operation or "behavior_change")
    else:
        return DeterministicRanker(RankerConfig(use_cascaded_ranking=False, use_diversity=False))


    # 4. VALIDATION-BASED RANKER SELECTION (PHASE 50, 51, 52)
    # Define candidate ranker configurations
    ranker_candidate_configs = {
        "R0": {
            "name": "R0_GraphDistanceBaseline",
            "type": "linear",
            "config": RankerConfig(use_cascaded_ranking=False, use_diversity=False),
        },
        "ExactFirst": {
            "name": "ExactFirstCascaded",
            "type": "cascaded",
            "config": RankerConfig(use_cascaded_ranking=True, use_diversity=False),
        },
        "OperationCascade": {
            "name": "OperationAwareCascade",
            "type": "operation_cascaded",
            "config": RankerConfig(use_cascaded_ranking=True, use_diversity=False),
        },
        "Coverage": {
            "name": "CoverageDiversityRanker",
            "type": "diversity",
            "config": RankerConfig(use_cascaded_ranking=False, use_diversity=True, max_per_module=5),
        },
        "AnchorCoverageRRF": {
            "name": "AnchorCoverageRRF_MultiObjective",
            "type": "multi_objective_rrf",
            "config": None,
        },
    }

    print("\n--- Evaluating Ranker Configurations on VALIDATION split (PHASE 50) ---")
    val_cands = splits_candidates["validation"]
    validation_results = {}
    best_config_name = None
    best_objective_score = -1.0

    for cfg_key, cfg_info in ranker_candidate_configs.items():
        val_ranked: dict[str, list[RankedCandidate]] = {}
        for tid, vectors in val_cands.items():
            task_op = gt_tasks[tid]["category"]
            r = build_ranker(cfg_key, operation=task_op)
            val_ranked[tid] = r.rank(vectors)

        metrics = compute_split_metrics(val_ranked, gt_tasks)
        metrics["config_key"] = cfg_key
        metrics["config_name"] = cfg_info["name"]
        validation_results[cfg_key] = metrics

        obj = metrics["multi_objective_score"]
        print(f"  [{cfg_key}] {cfg_info['name']} -> Macro Recall: {metrics['macro_pool_recall']*100:.1f}%, Worst: {metrics['worst_task_pool_recall']*100:.1f}%, P@20: {metrics['precision_at_20_excluding_target']*100:.1f}%, MRR: {metrics['dependency_mrr']:.4f} => Objective Score: {obj:.4f}")

        if obj > best_objective_score:
            best_objective_score = obj
            best_config_name = cfg_key

    print(f"\nWinning Validation Configuration: '{best_config_name}' ({ranker_candidate_configs[best_config_name]['name']}) with score {best_objective_score:.4f}")

    # Build provenance envelope
    env.derive_run_id()
    from provenance import build_provenance_envelope
    envelope = build_provenance_envelope(env)

    # Produce selected_ranker_config.json (PHASE 51)
    selected_artifact = {
        **envelope,
        "selected_configuration": best_config_name,
        "config_description": ranker_candidate_configs[best_config_name]["name"],
        "validation_objective_score": best_objective_score,
        "validation_metrics": validation_results[best_config_name],
        "selection_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_visibility": False,
        "all_candidate_configurations_evaluated": list(ranker_candidate_configs.keys()),
        "all_candidate_results": validation_results,
        "selection_objective": "0.25*Macro_Recall + 0.25*Worst_Recall + 0.20*P@20_excl + 0.15*nDCG@50 + 0.15*Dep_MRR",
    }
    (env.results_root / "selected_ranker_config.json").write_text(json.dumps(selected_artifact, indent=2), encoding="utf-8")
    print("Saved selected_ranker_config.json")

    # Evaluate and write baseline R0 on TEST split for Option B comparative contract evaluation
    r0_test_ranked: dict[str, list[RankedCandidate]] = {}
    for tid, vectors in splits_candidates["test"].items():
        task_op = gt_tasks[tid]["category"]
        r0 = build_ranker("R0", operation=task_op)
        r0_test_ranked[tid] = r0.rank(vectors)
    r0_test_metrics = compute_split_metrics(r0_test_ranked, gt_tasks)
    r0_baseline_artifact = {
        **envelope,
        "split": "test",
        "ranker_configuration": "R0_GraphDistanceBaseline",
        "metrics": r0_test_metrics,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (env.results_root / "ranker_baseline_r0.json").write_text(json.dumps(r0_baseline_artifact, indent=2), encoding="utf-8")
    print(f"Saved ranker_baseline_r0.json (Baseline R0 P@50 excl: {r0_test_metrics['precision_at_50_excluding_target']:.4f})")

    # 5. Run winning configuration across DEV, VALIDATION, and TEST
    split_final_predictions: dict[str, dict[str, Any]] = {}
    split_final_metrics: dict[str, Any] = {}

    for split in ("dev", "validation", "test"):
        cands_map = splits_candidates[split]
        ranked_map: dict[str, list[RankedCandidate]] = {}
        dump_tasks: dict[str, Any] = {}

        for tid, vectors in cands_map.items():
            task_op = gt_tasks[tid]["category"]
            r = build_ranker(best_config_name, operation=task_op)
            ranked = r.rank(vectors)

            ranked_map[tid] = ranked
            dump_tasks[tid] = {
                "task_id": tid,
                "total_candidates": len(ranked),
                "ranked_candidates": [
                    {
                        "rank": c.rank,
                        "entity_id": c.entity_id,
                        "file_path": c.file_path,
                        "score": round(c.total_score, 4),
                        "hop_distance": c.evidence.hop_distance,
                        "edge_types": c.evidence.edge_types,
                        "resolution_class": c.evidence.resolution_class,
                    }
                    for c in ranked
                ],
            }

        split_metrics = compute_split_metrics(ranked_map, gt_tasks)
        split_final_metrics[split] = split_metrics

        # Write raw prediction dump
        raw_pred_payload = {
            **envelope,
            "split": split,
            "selected_config": best_config_name,
            "channel_counts": splits_channel_stats[split],
            "total_tasks": len(ranked_map),
            "tasks": dump_tasks,
        }
        raw_pred_file = env.raw_root / "retrieval" / f"{split}_predictions.json"
        raw_pred_file.write_text(json.dumps(raw_pred_payload, indent=2), encoding="utf-8")
        print(f"Saved raw predictions to {raw_pred_file}")

        # Write result metrics
        result_payload = {
            **envelope,
            "split": split,
            "selected_ranker_config": best_config_name,
            "metrics": split_metrics,
            "channel_discovery_stats": splits_channel_stats[split],
            "gate_compliance": {
                "macro_recall_passed": split_metrics["macro_pool_recall"] >= 0.90,
                "worst_task_recall_passed": split_metrics["worst_task_pool_recall"] >= 0.80,
                "silent_misses_passed": split_metrics["silent_misses"] <= 20,
            }
        }
        res_file = env.results_root / f"ranker_{split}.json"
        res_file.write_text(json.dumps(result_payload, indent=2), encoding="utf-8")
        print(f"Saved ranker metrics to {res_file}")

        # Also write impact plane results (impact_{split}.json)
        impact_payload = {
            **envelope,
            "split": split,
            "macro_pool_recall": split_metrics["macro_pool_recall"],
            "worst_task_pool_recall": split_metrics["worst_task_pool_recall"],
            "silent_misses": split_metrics["silent_misses"],
            "total_candidates_pooled": sum(len(c) for c in cands_map.values()),
            "channel_discovery_stats": splits_channel_stats[split],
        }
        (env.results_root / f"impact_{split}.json").write_text(json.dumps(impact_payload, indent=2), encoding="utf-8")

        print(f"[{split.upper()}] Macro Recall: {split_metrics['macro_pool_recall']*100:.1f}%, Worst: {split_metrics['worst_task_pool_recall']*100:.1f}%, P@20(excl): {split_metrics['precision_at_20_excluding_target']*100:.1f}%, Dep MRR: {split_metrics['dependency_mrr']:.4f}, Silent Misses: {split_metrics['silent_misses']}")

    # Holdout hygiene: semantic and file-overlap analysis across splits (Section 17)
    dev_tasks = json.loads((env.dataset_root / "dev.json").read_text(encoding="utf-8"))["tasks"]
    val_tasks = json.loads((env.dataset_root / "validation.json").read_text(encoding="utf-8"))["tasks"]
    test_tasks = json.loads((env.dataset_root / "test.json").read_text(encoding="utf-8"))["tasks"]

    def extract_meta(ts):
        target_f = set()
        target_s = set()
        expected_f = set()
        for t in ts:
            sp = t.get("spec", {})
            tf = t.get("target_file") or sp.get("target_file_hint") or ""
            tsym = t.get("target_symbol") or sp.get("requested_symbol") or ""
            if tf:
                target_f.add(tf)
            if tsym:
                target_s.add(tsym)
            for ef in gt_tasks.get(t["task_id"], {}).get("expected_files", []):
                target_f.add(ef)
        return {"target_files": target_f, "target_symbols": target_s, "expected_files": expected_f}

    d_m = extract_meta(dev_tasks)
    v_m = extract_meta(val_tasks)
    t_m = extract_meta(test_tasks)

    overlap_artifact = {
        **envelope,
        "dev_vs_test": {
            "overlapping_target_files": sorted(list(d_m["target_files"].intersection(t_m["target_files"]))),
            "overlapping_target_symbols": sorted(list(d_m["target_symbols"].intersection(t_m["target_symbols"]))),
        },
        "validation_vs_test": {
            "overlapping_target_files": sorted(list(v_m["target_files"].intersection(t_m["target_files"]))),
            "overlapping_target_symbols": sorted(list(v_m["target_symbols"].intersection(t_m["target_symbols"]))),
        },
    }
    (env.results_root / "dataset_split_overlap.json").write_text(json.dumps(overlap_artifact, indent=2), encoding="utf-8")

    print("\nRetrieval execution COMPLETE.")


if __name__ == "__main__":
    execute_retrieval_suite()
