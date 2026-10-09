"""
experiments/benchmark_core — Canonical Benchmark Harness & Integrity Infrastructure.
"""

from experiments.benchmark_core.models import (
    RunManifest,
    TrialKey,
    TrialResult,
    VerificationResult,
    UsageRecord,
    TrialStatus,
    PairValidityStatus,
)
from experiments.benchmark_core.isolation import WorktreeManager, BenchmarkSetupError
from experiments.benchmark_core.evaluator import EvaluatorOracle
from experiments.benchmark_core.pairer import pair_trials
from experiments.benchmark_core.metrics import compute_benchmark_metrics
from experiments.benchmark_core.hashes import sha256_file, sha256_text

__all__ = [
    "RunManifest",
    "TrialKey",
    "TrialResult",
    "VerificationResult",
    "UsageRecord",
    "TrialStatus",
    "PairValidityStatus",
    "WorktreeManager",
    "BenchmarkSetupError",
    "EvaluatorOracle",
    "pair_trials",
    "compute_benchmark_metrics",
    "sha256_file",
    "sha256_text",
]
