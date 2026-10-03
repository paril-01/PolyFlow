"""
RCIR v8 — Ranked Retrieval Evaluation Framework (PHASE 2).

Implements all metrics required by the v8 specification:
- Recall@K (5, 10, 20, 50)
- Precision@K (5, 10, 20, 50)
- MRR (Mean Reciprocal Rank)
- nDCG (normalized Discounted Cumulative Gain)
- candidate_count
- token_budgeted_coverage
- silent_misses
- known_unresolved
- unsupported
- latency_ms
- peak_memory_mb

Reports both macro averages and micro/global aggregates.

Usage:
    python experiments/rcir_v8/scripts/evaluation.py \
        --results results.json \
        --ground-truth ground_truth.json \
        --output report.json
"""

import json
import math
import sys
import time
import tracemalloc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class RetrievalResult:
    """A single ranked retrieval result."""
    entity_id: str
    rank: int
    score: float
    source: str = ""  # which retrieval pass produced this


@dataclass
class TaskEvaluation:
    """Evaluation metrics for a single retrieval task."""
    task_id: str
    ground_truth_files: list[str]
    retrieved_files: list[str]  # ordered by rank
    candidate_count: int = 0
    token_budgeted_coverage: float = 0.0
    silent_misses: list[str] = field(default_factory=list)
    known_unresolved: list[str] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    peak_memory_mb: float = 0.0

    # Computed metrics
    recall_at: dict[int, float] = field(default_factory=dict)
    precision_at: dict[int, float] = field(default_factory=dict)
    mrr: float = 0.0
    ndcg: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "candidate_count": self.candidate_count,
            "ground_truth_count": len(self.ground_truth_files),
            "recall_at": self.recall_at,
            "precision_at": self.precision_at,
            "mrr": round(self.mrr, 4),
            "ndcg": round(self.ndcg, 4),
            "token_budgeted_coverage": round(self.token_budgeted_coverage, 4),
            "silent_misses": self.silent_misses,
            "silent_miss_count": len(self.silent_misses),
            "known_unresolved": self.known_unresolved,
            "known_unresolved_count": len(self.known_unresolved),
            "unsupported": self.unsupported,
            "unsupported_count": len(self.unsupported),
            "latency_ms": round(self.latency_ms, 2),
            "peak_memory_mb": round(self.peak_memory_mb, 2),
        }


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Compute Recall@K.

    Recall@K = |relevant ∩ retrieved[:k]| / |relevant|

    If there are no relevant documents, returns 1.0 (vacuous truth).
    """
    if not relevant:
        return 1.0
    retrieved_at_k = set(retrieved[:k])
    return len(relevant & retrieved_at_k) / len(relevant)


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Compute Precision@K.

    Precision@K = |relevant ∩ retrieved[:k]| / k

    If k is 0, returns 0.0.
    """
    if k == 0:
        return 0.0
    retrieved_at_k = set(retrieved[:k])
    return len(relevant & retrieved_at_k) / k


def mean_reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    """Compute MRR (Mean Reciprocal Rank).

    MRR = 1 / rank_of_first_relevant_document

    If no relevant document is found, returns 0.0.
    """
    for i, doc in enumerate(retrieved):
        if doc in relevant:
            return 1.0 / (i + 1)
    return 0.0


def dcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Compute DCG@K (Discounted Cumulative Gain).

    Uses binary relevance: 1 if relevant, 0 otherwise.
    DCG@K = Σ_{i=1}^{k} rel_i / log2(i + 1)
    """
    score = 0.0
    for i, doc in enumerate(retrieved[:k]):
        if doc in relevant:
            score += 1.0 / math.log2(i + 2)  # i+2 because i is 0-indexed
    return score


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Compute nDCG@K (normalized Discounted Cumulative Gain).

    nDCG@K = DCG@K / IDCG@K

    IDCG@K is the DCG of a perfect ranking where all relevant documents
    are ranked first.
    """
    dcg = dcg_at_k(retrieved, relevant, k)

    # Ideal DCG: all relevant docs ranked first
    n_relevant_in_k = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(n_relevant_in_k))

    if idcg == 0:
        return 0.0
    return dcg / idcg


K_VALUES = [5, 10, 20, 50]


def evaluate_task(
    task_id: str,
    ground_truth_files: list[str],
    retrieved_files: list[str],
    candidate_count: int = 0,
    token_budgeted_coverage: float = 0.0,
    silent_misses: list[str] | None = None,
    known_unresolved: list[str] | None = None,
    unsupported: list[str] | None = None,
    latency_ms: float = 0.0,
    peak_memory_mb: float = 0.0,
) -> TaskEvaluation:
    """Evaluate a single retrieval task against ground truth.

    Args:
        task_id: Unique task identifier.
        ground_truth_files: List of files that should have been retrieved.
        retrieved_files: Ranked list of files that were actually retrieved.
        candidate_count: Total number of candidates before ranking.
        token_budgeted_coverage: Fraction of ground truth covered within token budget.
        silent_misses: Files completely missed (not even in candidate set).
        known_unresolved: Files flagged as unresolvable.
        unsupported: Files in ground truth that are outside analysis scope.
        latency_ms: Wall-clock time for retrieval.
        peak_memory_mb: Peak memory usage during retrieval.

    Returns:
        TaskEvaluation with all computed metrics.
    """
    relevant = set(ground_truth_files)

    eval_result = TaskEvaluation(
        task_id=task_id,
        ground_truth_files=ground_truth_files,
        retrieved_files=retrieved_files,
        candidate_count=candidate_count,
        token_budgeted_coverage=token_budgeted_coverage,
        silent_misses=silent_misses or [],
        known_unresolved=known_unresolved or [],
        unsupported=unsupported or [],
        latency_ms=latency_ms,
        peak_memory_mb=peak_memory_mb,
    )

    # Compute Recall@K and Precision@K for each K
    for k in K_VALUES:
        eval_result.recall_at[k] = round(recall_at_k(retrieved_files, relevant, k), 4)
        eval_result.precision_at[k] = round(precision_at_k(retrieved_files, relevant, k), 4)

    # MRR
    eval_result.mrr = mean_reciprocal_rank(retrieved_files, relevant)

    # nDCG (at the largest K value, 50)
    eval_result.ndcg = ndcg_at_k(retrieved_files, relevant, max(K_VALUES))

    return eval_result


@dataclass
class AggregateEvaluation:
    """Aggregated evaluation across multiple tasks."""
    task_count: int = 0
    macro_recall_at: dict[int, float] = field(default_factory=dict)
    macro_precision_at: dict[int, float] = field(default_factory=dict)
    macro_mrr: float = 0.0
    macro_ndcg: float = 0.0
    micro_recall_at: dict[int, float] = field(default_factory=dict)
    micro_precision_at: dict[int, float] = field(default_factory=dict)
    total_candidates: int = 0
    total_ground_truth: int = 0
    total_silent_misses: int = 0
    total_known_unresolved: int = 0
    total_unsupported: int = 0
    mean_latency_ms: float = 0.0
    mean_peak_memory_mb: float = 0.0
    per_task: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_count": self.task_count,
            "macro_averages": {
                "recall_at": self.macro_recall_at,
                "precision_at": self.macro_precision_at,
                "mrr": round(self.macro_mrr, 4),
                "ndcg": round(self.macro_ndcg, 4),
            },
            "micro_aggregates": {
                "recall_at": self.micro_recall_at,
                "precision_at": self.micro_precision_at,
            },
            "totals": {
                "candidates": self.total_candidates,
                "ground_truth": self.total_ground_truth,
                "silent_misses": self.total_silent_misses,
                "known_unresolved": self.total_known_unresolved,
                "unsupported": self.total_unsupported,
            },
            "performance": {
                "mean_latency_ms": round(self.mean_latency_ms, 2),
                "mean_peak_memory_mb": round(self.mean_peak_memory_mb, 2),
            },
            "per_task": self.per_task,
        }


def aggregate_evaluations(evaluations: list[TaskEvaluation]) -> AggregateEvaluation:
    """Compute macro averages and micro/global aggregates across tasks.

    Macro: average of per-task metrics (each task weighted equally).
    Micro: pool all ground-truth and retrieved items, compute globally.
    """
    if not evaluations:
        return AggregateEvaluation()

    n = len(evaluations)
    agg = AggregateEvaluation(task_count=n)

    # Macro averages
    for k in K_VALUES:
        agg.macro_recall_at[k] = round(
            sum(e.recall_at.get(k, 0) for e in evaluations) / n, 4
        )
        agg.macro_precision_at[k] = round(
            sum(e.precision_at.get(k, 0) for e in evaluations) / n, 4
        )

    agg.macro_mrr = sum(e.mrr for e in evaluations) / n
    agg.macro_ndcg = sum(e.ndcg for e in evaluations) / n

    # Micro aggregates: pool all ground truth and retrieved
    for k in K_VALUES:
        total_relevant = 0
        total_retrieved_relevant = 0
        total_retrieved = 0

        for e in evaluations:
            relevant = set(e.ground_truth_files)
            retrieved_at_k = set(e.retrieved_files[:k])
            total_relevant += len(relevant)
            total_retrieved_relevant += len(relevant & retrieved_at_k)
            total_retrieved += min(k, len(e.retrieved_files))

        agg.micro_recall_at[k] = round(
            total_retrieved_relevant / total_relevant if total_relevant > 0 else 0.0, 4
        )
        agg.micro_precision_at[k] = round(
            total_retrieved_relevant / total_retrieved if total_retrieved > 0 else 0.0, 4
        )

    # Totals
    agg.total_candidates = sum(e.candidate_count for e in evaluations)
    agg.total_ground_truth = sum(len(e.ground_truth_files) for e in evaluations)
    agg.total_silent_misses = sum(len(e.silent_misses) for e in evaluations)
    agg.total_known_unresolved = sum(len(e.known_unresolved) for e in evaluations)
    agg.total_unsupported = sum(len(e.unsupported) for e in evaluations)

    # Performance
    agg.mean_latency_ms = sum(e.latency_ms for e in evaluations) / n
    agg.mean_peak_memory_mb = sum(e.peak_memory_mb for e in evaluations) / n

    # Per-task details
    agg.per_task = [e.to_dict() for e in evaluations]

    return agg


def evaluate_from_json(
    results_path: str | Path,
    ground_truth_path: str | Path,
) -> AggregateEvaluation:
    """Load results and ground truth from JSON files and evaluate.

    Expected results format:
    {
        "tasks": [
            {
                "task_id": "TASK-1",
                "retrieved_files": ["file1.py", "file2.py", ...],
                "candidate_count": 100,
                "latency_ms": 50.0,
                "peak_memory_mb": 12.0
            },
            ...
        ]
    }

    Expected ground truth format:
    {
        "tasks": [
            {
                "task_id": "TASK-1",
                "ground_truth_files": ["file1.py", "file3.py", ...],
                "silent_misses": [],
                "known_unresolved": [],
                "unsupported": []
            },
            ...
        ]
    }
    """
    results = json.loads(Path(results_path).read_text(encoding="utf-8"))
    ground_truth = json.loads(Path(ground_truth_path).read_text(encoding="utf-8"))

    # Build ground truth lookup
    gt_by_task = {t["task_id"]: t for t in ground_truth.get("tasks", [])}

    evaluations = []
    for task_result in results.get("tasks", []):
        task_id = task_result["task_id"]
        gt = gt_by_task.get(task_id, {})

        evaluation = evaluate_task(
            task_id=task_id,
            ground_truth_files=gt.get("ground_truth_files", []),
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

    return aggregate_evaluations(evaluations)


def main():
    """CLI: evaluate retrieval results against ground truth."""
    import argparse

    parser = argparse.ArgumentParser(
        description="RCIR v8 Ranked Retrieval Evaluation"
    )
    parser.add_argument(
        "--results", "-r", required=True,
        help="Path to retrieval results JSON"
    )
    parser.add_argument(
        "--ground-truth", "-g", required=True,
        help="Path to ground truth JSON"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output JSON file path (default: stdout)"
    )
    args = parser.parse_args()

    aggregate = evaluate_from_json(args.results, args.ground_truth)
    output_json = json.dumps(aggregate.to_dict(), indent=2)

    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"Evaluation written to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
