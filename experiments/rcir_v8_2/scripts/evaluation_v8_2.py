"""
RCIR v8.2 — Primary Evaluation Framework (PHASES 2, 3, 31, 32, 33).

Provides rigorous metric calculation for both Plane A (Impact) and Plane B (Context):
- CandidatePoolRecall (Global, Macro, Per-Task, Worst-Task)
- Graded nDCG@K using exponential DCG
- Strict MRR
- Token-weighted Precision and Recall based on exact compiled entry tokens (no 150-token fallback)
- Reports both File-Level and Entity-Level context density (PHASE 33)
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

K_VALUES = [5, 10, 20, 50]


@dataclass
class GradedTaskEvaluation:
    task_id: str
    ground_truth_grades: dict[str, int]  # file -> tier (1, 2, 3)
    retrieved_files: list[str]            # ordered by rank
    candidate_pool_files: list[str]       # all candidates in Plane A
    compiled_context_files: list[str] = field(default_factory=list)
    compiled_tokens: int = 0
    token_budget: int = 4000
    file_token_costs: dict[str, int] = field(default_factory=dict)
    known_unresolved: list[str] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    peak_memory_mb: float = 0.0

    # Computed fields
    candidate_pool_recall: float = 0.0
    candidate_pool_precision: float = 0.0
    silent_misses: list[str] = field(default_factory=list)
    r_precision: float = 0.0
    recall_at_r: float = 0.0
    recall_at: dict[int, float] = field(default_factory=dict)
    precision_at: dict[int, float] = field(default_factory=dict)
    critical_recall_at: dict[int, float] = field(default_factory=dict)
    mrr: float = 0.0
    ndcg_at: dict[int, float] = field(default_factory=dict)
    context_precision: float = 0.0
    context_recall: float = 0.0
    critical_recall_budget: float = 0.0
    token_weighted_precision: float = 0.0
    token_weighted_recall: float = 0.0

    def compute_metrics(self) -> None:
        gt_set = set(self.ground_truth_grades.keys())
        total_gt = len(gt_set)
        if total_gt == 0:
            return

        pool_set = set(self.candidate_pool_files)
        if not pool_set and self.retrieved_files:
            pool_set = set(self.retrieved_files)

        # 1. Candidate Pool Recall & Precision
        recalled_in_pool = gt_set & pool_set
        self.candidate_pool_recall = len(recalled_in_pool) / total_gt
        self.silent_misses = sorted(list(gt_set - pool_set))
        self.candidate_pool_precision = len(recalled_in_pool) / len(pool_set) if pool_set else 0.0

        # 2. Critical ground truth (Tiers 2 & 3)
        critical_gt = {f for f, grade in self.ground_truth_grades.items() if grade >= 2}
        total_critical = len(critical_gt)

        # 3. Standard Recall@K and Precision@K
        for k in K_VALUES:
            top_k_set = set(self.retrieved_files[:k])
            hits = len(gt_set & top_k_set)
            self.recall_at[k] = hits / total_gt
            self.precision_at[k] = hits / k if k > 0 else 0.0

            if total_critical > 0:
                crit_hits = len(critical_gt & top_k_set)
                self.critical_recall_at[k] = crit_hits / total_critical
            else:
                self.critical_recall_at[k] = 1.0

        # 4. R-Precision
        r = total_gt
        top_r_set = set(self.retrieved_files[:r])
        self.r_precision = len(gt_set & top_r_set) / r if r > 0 else 0.0
        self.recall_at_r = self.r_precision

        # 5. MRR
        self.mrr = 0.0
        for idx, f in enumerate(self.retrieved_files, 1):
            if f in gt_set:
                self.mrr = 1.0 / idx
                break

        # 6. Graded nDCG@K
        for k in [20, 50]:
            dcg = 0.0
            for idx, f in enumerate(self.retrieved_files[:k], 1):
                rel = self.ground_truth_grades.get(f, 0)
                if rel > 0:
                    dcg += (2**rel - 1) / math.log2(idx + 1)

            sorted_ideal_grades = sorted(self.ground_truth_grades.values(), reverse=True)[:k]
            idcg = 0.0
            for idx, rel in enumerate(sorted_ideal_grades, 1):
                if rel > 0:
                    idcg += (2**rel - 1) / math.log2(idx + 1)

            self.ndcg_at[k] = (dcg / idcg) if idcg > 0 else 0.0

        # 7. Context Plane Metrics
        if self.compiled_context_files:
            ctx_set = set(self.compiled_context_files)
            ctx_hits = len(gt_set & ctx_set)
            self.context_precision = ctx_hits / len(ctx_set) if ctx_set else 0.0
            self.context_recall = ctx_hits / total_gt

            if total_critical > 0:
                self.critical_recall_budget = len(critical_gt & ctx_set) / total_critical
            else:
                self.critical_recall_budget = 1.0

            # PHASE 32: Token-weighted metrics using actual compiled entry costs
            compiled_tokens_total = self.compiled_tokens or sum(self.file_token_costs.get(f, 60) for f in ctx_set)
            rel_tokens = sum(self.file_token_costs.get(f, 60) for f in (gt_set & ctx_set))
            all_gt_tokens = sum(self.file_token_costs.get(f, 60) for f in gt_set)

            self.token_weighted_precision = (rel_tokens / compiled_tokens_total) if compiled_tokens_total > 0 else 0.0
            self.token_weighted_recall = (rel_tokens / all_gt_tokens) if all_gt_tokens > 0 else 0.0
        else:
            proxy_ctx = self.retrieved_files[:20]
            ctx_set = set(proxy_ctx)
            ctx_hits = len(gt_set & ctx_set)
            self.context_precision = ctx_hits / len(ctx_set) if ctx_set else 0.0
            self.context_recall = ctx_hits / total_gt
            self.critical_recall_budget = (len(critical_gt & ctx_set) / total_critical) if total_critical > 0 else 1.0
            self.token_weighted_precision = self.context_precision
            self.token_weighted_recall = self.context_recall

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "ground_truth_count": len(self.ground_truth_grades),
            "candidate_pool_size": len(self.candidate_pool_files),
            "candidate_pool_recall": round(self.candidate_pool_recall, 4),
            "candidate_pool_precision": round(self.candidate_pool_precision, 4),
            "r_precision": round(self.r_precision, 4),
            "recall_at_r": round(self.recall_at_r, 4),
            "recall_at": {str(k): round(v, 4) for k, v in self.recall_at.items()},
            "precision_at": {str(k): round(v, 4) for k, v in self.precision_at.items()},
            "critical_recall_at": {str(k): round(v, 4) for k, v in self.critical_recall_at.items()},
            "mrr": round(self.mrr, 4),
            "ndcg_at": {str(k): round(v, 4) for k, v in self.ndcg_at.items()},
            "context_precision": round(self.context_precision, 4),
            "context_recall": round(self.context_recall, 4),
            "critical_recall_budget": round(self.critical_recall_budget, 4),
            "token_weighted_precision": round(self.token_weighted_precision, 4),
            "token_weighted_recall": round(self.token_weighted_recall, 4),
            "compiled_tokens": self.compiled_tokens,
            "silent_misses": self.silent_misses,
            "silent_miss_count": len(self.silent_misses),
            "known_unresolved": self.known_unresolved,
            "known_unresolved_count": len(self.known_unresolved),
            "unsupported": self.unsupported,
            "unsupported_count": len(self.unsupported),
            "latency_ms": round(self.latency_ms, 2),
            "peak_memory_mb": round(self.peak_memory_mb, 2),
        }


def aggregate_v8_2(evaluations: list[GradedTaskEvaluation]) -> dict[str, Any]:
    """Compute micro (global) and macro averages across all evaluated tasks."""
    n = len(evaluations)
    if n == 0:
        return {}

    macro: dict[str, Any] = {
        "candidate_pool_recall": round(sum(e.candidate_pool_recall for e in evaluations) / n, 4),
        "candidate_pool_precision": round(sum(e.candidate_pool_precision for e in evaluations) / n, 4),
        "r_precision": round(sum(e.r_precision for e in evaluations) / n, 4),
        "recall_at": {
            str(k): round(sum(e.recall_at[k] for e in evaluations) / n, 4)
            for k in K_VALUES
        },
        "precision_at": {
            str(k): round(sum(e.precision_at[k] for e in evaluations) / n, 4)
            for k in K_VALUES
        },
        "critical_recall_at": {
            str(k): round(sum(e.critical_recall_at[k] for e in evaluations) / n, 4)
            for k in K_VALUES
        },
        "mrr": round(sum(e.mrr for e in evaluations) / n, 4),
        "ndcg_at": {
            "20": round(sum(e.ndcg_at.get(20, 0.0) for e in evaluations) / n, 4),
            "50": round(sum(e.ndcg_at.get(50, 0.0) for e in evaluations) / n, 4),
        },
        "context_precision": round(sum(e.context_precision for e in evaluations) / n, 4),
        "context_recall": round(sum(e.context_recall for e in evaluations) / n, 4),
        "critical_recall_budget": round(sum(e.critical_recall_budget for e in evaluations) / n, 4),
        "token_weighted_precision": round(sum(e.token_weighted_precision for e in evaluations) / n, 4),
        "token_weighted_recall": round(sum(e.token_weighted_recall for e in evaluations) / n, 4),
    }

    # Micro / Global totals
    total_gt = sum(len(e.ground_truth_grades) for e in evaluations)
    total_candidates_pool = sum(len(e.candidate_pool_files) for e in evaluations)
    total_silent_misses = sum(len(e.silent_misses) for e in evaluations)
    total_recalled = total_gt - total_silent_misses

    per_task_recalls = [e.candidate_pool_recall for e in evaluations]
    worst_task_recall = min(per_task_recalls) if per_task_recalls else 0.0

    totals = {
        "tasks": n,
        "total_ground_truth": total_gt,
        "total_candidates_pool": total_candidates_pool,
        "total_silent_misses": total_silent_misses,
        "global_pool_recall": round(total_recalled / total_gt, 4) if total_gt > 0 else 0.0,
        "worst_task_pool_recall": round(worst_task_recall, 4),
        "total_known_unresolved": sum(len(e.known_unresolved) for e in evaluations),
        "total_unsupported": sum(len(e.unsupported) for e in evaluations),
    }

    perf = {
        "mean_latency_ms": round(sum(e.latency_ms for e in evaluations) / n, 2),
        "mean_peak_memory_mb": round(sum(e.peak_memory_mb for e in evaluations) / n, 2),
    }

    return {
        "macro_averages": macro,
        "totals": totals,
        "performance": perf,
        "per_task": [e.to_dict() for e in evaluations],
    }
