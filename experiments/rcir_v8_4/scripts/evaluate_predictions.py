#!/usr/bin/env python3
"""
RCIR v8.4 — Independent Benchmark Evaluator (PHASE 76).

Architectural Rule:
This evaluator reads raw retrieval predictions, compiled contexts, and authoritative ground truth.
It computes mathematical metrics with zero hardcoding:
- Impact Plane: macro candidate recall, micro recall, worst-task recall, silent miss catalog.
- Ranking Plane: P@20, P@50, nDCG@50, MRR.
- Context Plane: CriticalRecall@2k, CriticalRecall@4k, CriticalRecall@8k.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT))

GT_PATH = REPO_ROOT / "experiments" / "rcir_v8_4" / "ground_truth" / "ground_truth.json"
RAW_RETRIEVAL_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "raw" / "retrieval"
RAW_CONTEXT_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "raw" / "context"
RESULTS_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "results"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def compute_ndcg_at_k(ranked_files: list[str], relevant_files: set[str], k: int = 50) -> float:
    dcg = 0.0
    for idx, f in enumerate(ranked_files[:k]):
        if f in relevant_files:
            rel = 1.0
            dcg += rel / math.log2(idx + 2)

    # Ideal DCG
    idcg = 0.0
    for idx in range(min(len(relevant_files), k)):
        idcg += 1.0 / math.log2(idx + 2)

    return (dcg / idcg) if idcg > 0.0 else 0.0


def compute_mrr(ranked_files: list[str], relevant_files: set[str]) -> float:
    for idx, f in enumerate(ranked_files):
        if f in relevant_files:
            return 1.0 / (idx + 1)
    return 0.0


def evaluate_split(split: str) -> None:
    pred_path = RAW_RETRIEVAL_DIR / f"{split}_predictions.json"
    ctx_path = RAW_CONTEXT_DIR / f"{split}_contexts.json"

    if not pred_path.exists() or not ctx_path.exists():
        raise FileNotFoundError(f"Raw artifacts missing for {split}. Run retrieval_runner.py and context_runner.py first.")

    pred_data = json.loads(pred_path.read_text(encoding="utf-8"))
    ctx_data = json.loads(ctx_path.read_text(encoding="utf-8"))
    gt_data = json.loads(GT_PATH.read_text(encoding="utf-8")).get("tasks", {})

    print(f"Evaluating split '{split}' against independent ground truth...")

    impact_tasks = []
    ranker_tasks = []
    context_tasks = []
    silent_misses = []

    macro_recalls = []
    worst_task_recall = 1.0
    worst_task_id = ""

    total_gt_files = 0
    total_recalled_files = 0

    total_critical_gt_files = 0
    total_critical_recalled_files = 0

    p20_list = []
    p50_list = []
    ndcg50_list = []
    mrr_list = []

    crit_recall_2k_list = []
    crit_recall_4k_list = []
    crit_recall_8k_list = []

    for task_id, p_info in pred_data.get("task_predictions", {}).items():
        if task_id not in gt_data:
            print(f"Warning: task {task_id} not found in ground truth. Skipping.")
            continue

        gt = gt_data[task_id]
        expected_files = set(gt.get("expected_files", []))
        critical_files = set(gt.get("critical_files", []))

        predicted_files = set(p_info.get("predicted_files", []))
        ranked_files = []
        seen_rf = set()
        for cand in p_info.get("ranked_candidates", []):
            fp = cand.get("file_path", "")
            if fp and fp not in seen_rf:
                seen_rf.add(fp)
                ranked_files.append(fp)

        # 1. Impact Recall Metrics
        recalled = predicted_files.intersection(expected_files)
        critical_recalled = predicted_files.intersection(critical_files)

        task_recall = (len(recalled) / len(expected_files)) if expected_files else 1.0
        task_crit_recall = (len(critical_recalled) / len(critical_files)) if critical_files else 1.0

        macro_recalls.append(task_recall)
        if task_recall < worst_task_recall:
            worst_task_recall = task_recall
            worst_task_id = task_id

        total_gt_files += len(expected_files)
        total_recalled_files += len(recalled)
        total_critical_gt_files += len(critical_files)
        total_critical_recalled_files += len(critical_recalled)

        # Diagnose silent misses (Phase 84)
        missed = expected_files - predicted_files
        for m in missed:
            stage = "TRAVERSAL_POLICY" if "test" in m.lower() else "EDGE_EXTRACTION"
            silent_misses.append({
                "task_id": task_id,
                "missed_file": m,
                "is_critical": m in critical_files,
                "miss_stage": stage,
                "reason": f"Expected dependency {m} not in candidate pool",
            })

        impact_tasks.append({
            "task_id": task_id,
            "target_entity": gt.get("target_entity"),
            "expected_files_count": len(expected_files),
            "recalled_files_count": len(recalled),
            "candidate_recall": round(task_recall, 4),
            "critical_recall": round(task_crit_recall, 4),
            "missed_files": sorted(list(missed)),
        })

        # 2. Ranking Metrics
        p20 = len(set(ranked_files[:20]).intersection(expected_files)) / min(20, max(1, len(expected_files)))
        p50 = len(set(ranked_files[:50]).intersection(expected_files)) / min(50, max(1, len(expected_files)))
        ndcg50 = compute_ndcg_at_k(ranked_files, expected_files, k=50)
        mrr = compute_mrr(ranked_files, expected_files)

        p20_list.append(p20)
        p50_list.append(p50)
        ndcg50_list.append(ndcg50)
        mrr_list.append(mrr)

        ranker_tasks.append({
            "task_id": task_id,
            "p_at_20": round(p20, 4),
            "p_at_50": round(p50, 4),
            "ndcg_at_50": round(ndcg50, 4),
            "mrr": round(mrr, 4),
        })

        # 3. Context Metrics across budgets
        ctx_budgets = ctx_data.get("task_contexts", {}).get(task_id, {}).get("budgets", {})
        task_ctx_eval = {"task_id": task_id, "budgets": {}}

        for b_str in ["2000", "4000", "8000"]:
            b_info = ctx_budgets.get(b_str, {})
            inc_files = set(b_info.get("included_files", []))
            crit_cov = len(inc_files.intersection(critical_files)) / len(critical_files) if critical_files else 1.0
            task_ctx_eval["budgets"][b_str] = {
                "budget": int(b_str),
                "tokens_consumed": b_info.get("tokens_consumed", 0),
                "critical_recall": round(crit_cov, 4),
                "included_files_count": len(inc_files),
            }
            if b_str == "2000":
                crit_recall_2k_list.append(crit_cov)
            elif b_str == "4000":
                crit_recall_4k_list.append(crit_cov)
            elif b_str == "8000":
                crit_recall_8k_list.append(crit_cov)

        context_tasks.append(task_ctx_eval)

    # Aggregations (Phase 44)
    macro_recall = sum(macro_recalls) / len(macro_recalls) if macro_recalls else 0.0
    micro_recall = (total_recalled_files / total_gt_files) if total_gt_files else 0.0
    critical_micro_recall = (total_critical_recalled_files / total_critical_gt_files) if total_critical_gt_files else 0.0

    mean_p20 = sum(p20_list) / len(p20_list) if p20_list else 0.0
    mean_p50 = sum(p50_list) / len(p50_list) if p50_list else 0.0
    mean_ndcg50 = sum(ndcg50_list) / len(ndcg50_list) if ndcg50_list else 0.0
    mean_mrr = sum(mrr_list) / len(mrr_list) if mrr_list else 0.0

    mean_crit_2k = sum(crit_recall_2k_list) / len(crit_recall_2k_list) if crit_recall_2k_list else 0.0
    mean_crit_4k = sum(crit_recall_4k_list) / len(crit_recall_4k_list) if crit_recall_4k_list else 0.0
    mean_crit_8k = sum(crit_recall_8k_list) / len(crit_recall_8k_list) if crit_recall_8k_list else 0.0

    # Save Impact results
    impact_output = {
        "split": split,
        "version": "8.4",
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "tasks_count": len(macro_recalls),
            "macro_candidate_recall": round(macro_recall, 4),
            "micro_candidate_recall": round(micro_recall, 4),
            "critical_micro_recall": round(critical_micro_recall, 4),
            "worst_task_recall": round(worst_task_recall, 4),
            "worst_task_id": worst_task_id,
            "silent_misses_count": len(silent_misses),
        },
        "tasks": impact_tasks,
        "silent_miss_catalog": silent_misses,
    }
    (RESULTS_DIR / f"impact_{split}.json").write_text(json.dumps(impact_output, indent=2), encoding="utf-8")

    # Save Ranker results
    ranker_output = {
        "split": split,
        "version": "8.4",
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "p_at_20": round(mean_p20, 4),
            "p_at_50": round(mean_p50, 4),
            "ndcg_at_50": round(mean_ndcg50, 4),
            "mrr": round(mean_mrr, 4),
        },
        "tasks": ranker_tasks,
    }
    (RESULTS_DIR / f"ranker_{split}.json").write_text(json.dumps(ranker_output, indent=2), encoding="utf-8")

    # Save Context results
    context_output = {
        "split": split,
        "version": "8.4",
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "critical_recall_2k": round(mean_crit_2k, 4),
            "critical_recall_4k": round(mean_crit_4k, 4),
            "critical_recall_8k": round(mean_crit_8k, 4),
        },
        "tasks": context_tasks,
    }
    (RESULTS_DIR / f"context_{split}.json").write_text(json.dumps(context_output, indent=2), encoding="utf-8")

    # If test split, save context_budget_curve_test.json
    if split == "test":
        budget_curve = {
            "version": "8.4",
            "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "budgets": {
                "2000": {"critical_recall": round(mean_crit_2k, 4)},
                "4000": {"critical_recall": round(mean_crit_4k, 4)},
                "8000": {"critical_recall": round(mean_crit_8k, 4)},
            },
        }
        (RESULTS_DIR / "context_budget_curve_test.json").write_text(json.dumps(budget_curve, indent=2), encoding="utf-8")

    print(f"Completed evaluation for '{split}': Macro Recall = {macro_recall:.2%}, Worst Task = {worst_task_recall:.2%}, P@20 = {mean_p20:.2%}, CritRecall@4k = {mean_crit_4k:.2%}")


def main():
    parser = argparse.ArgumentParser(description="RCIR v8.4 Independent Evaluator")
    parser.add_argument("--split", choices=["dev", "validation", "test", "all"], default="all")
    args = parser.parse_args()

    splits = ["dev", "validation", "test"] if args.split == "all" else [args.split]
    for s in splits:
        evaluate_split(s)


if __name__ == "__main__":
    main()
