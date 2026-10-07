#!/usr/bin/env python3
"""
RCIR v8.5.1 — Contract Feasibility and Theoretical Metric Ceiling Validator.

Calculates the theoretical ceiling for ranking and retrieval metrics given the ground-truth labels.
For fixed-denominator Precision@K:
    max_precision_at_k = min(len(relevant_dependencies), k) / k
Aggregates theoretical ceilings using the exact benchmark aggregation (macro mean).
If contract threshold > theoretical ceiling, marks contract INVALID_CONTRACT.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def calculate_ranking_ceilings(
    tasks: Any,
    k_values: Tuple[int, ...] = (20, 50),
    ground_truth_dict: Optional[Dict[str, Any]] = None,
) -> Dict[str, float]:
    """
    Compute theoretical maximum macro-average Precision@K for a task split.
    Relevant dependencies are calculated excluding target file.
    """
    if isinstance(tasks, dict) and "tasks" in tasks:
        tasks = tasks["tasks"]

    if isinstance(tasks, dict):
        task_list = list(tasks.values())
    elif isinstance(tasks, list):
        task_list = tasks
    else:
        task_list = []

    if not task_list:
        return {f"precision_at_{k}_excluding_target": 0.0 for k in k_values}

    ceilings: Dict[int, List[float]] = {k: [] for k in k_values}

    for task in task_list:
        tid = task.get("task_id", "")
        # If task does not have expected_files, look it up in ground_truth_dict if provided
        if "expected_files" not in task and ground_truth_dict and tid in ground_truth_dict:
            task = ground_truth_dict[tid]

        target_file = (task.get("target_file") or task.get("spec", {}).get("target_file_hint") or "").replace("\\", "/")
        expected_files = [f.replace("\\", "/") for f in task.get("expected_files", [])]
        # Exclude target file
        relevant_dependencies = [f for f in expected_files if f != target_file]
        n_rel = len(relevant_dependencies)

        for k in k_values:
            max_p_k = min(n_rel, k) / float(k)
            ceilings[k].append(max_p_k)

    result = {}
    for k in k_values:
        result[f"precision_at_{k}_excluding_target"] = (sum(ceilings[k]) / len(ceilings[k])) if ceilings[k] else 0.0
    return result


def validate_contract_feasibility(
    contract_data: Dict[str, Any],
    ground_truth_tasks: List[Dict[str, Any]] | Dict[str, Dict[str, Any]],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate whether the contract ranking thresholds are mathematically possible.
    Returns (is_feasible, details_dict).
    """
    ceilings = calculate_ranking_ceilings(ground_truth_tasks, k_values=(20, 50))
    ranking_cfg = contract_data.get("ranking_plane", {})

    violations = []
    threshold_p20 = ranking_cfg.get("precision_at_20_excluding_target_min")
    ceil_p20 = ceilings.get("precision_at_20_excluding_target")
    if threshold_p20 is not None and ceil_p20 is not None and threshold_p20 > ceil_p20:
        violations.append(
            f"precision_at_20_excluding_target_min threshold ({threshold_p20:.4f}) exceeds "
            f"theoretical maximum ceiling ({ceil_p20:.4f})"
        )

    threshold_p50 = ranking_cfg.get("precision_at_50_excluding_target_min")
    ceil_p50 = ceilings.get("precision_at_50_excluding_target")
    if threshold_p50 is not None and ceil_p50 is not None and threshold_p50 > ceil_p50:
        violations.append(
            f"precision_at_50_excluding_target_min threshold ({threshold_p50:.4f}) exceeds "
            f"theoretical maximum ceiling ({ceil_p50:.4f})"
        )

    # Check blocking metrics ceilings (<= 1.0)
    blocking_cfg = ranking_cfg.get("blocking_metrics", {})
    for metric_name, thresh in blocking_cfg.items():
        if thresh is not None and thresh > 1.0:
            violations.append(f"{metric_name} threshold ({thresh}) exceeds theoretical maximum ceiling (1.0)")

    is_feasible = len(violations) == 0
    return is_feasible, {
        "status": "VALID_CONTRACT" if is_feasible else "INVALID_CONTRACT",
        "theoretical_ceilings": ceilings,
        "contract_thresholds": {
            "precision_at_20_excluding_target_min": threshold_p20,
            "precision_at_50_excluding_target_min": threshold_p50,
            "blocking_metrics": blocking_cfg,
        },
        "violations": violations,
    }

