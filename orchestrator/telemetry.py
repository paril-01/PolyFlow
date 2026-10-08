"""
RCIR & Agent Telemetry Architecture (SECTION 8 & 9).

Canonical UsageRecord and Telemetry tracking:
- PROVIDER_NATIVE: native token counts from provider APIs (Ollama prompt_eval_count, OpenAI, Anthropic, Gemini)
- TOKENIZER_EXACT: local tiktoken/cl100k or exact token counter
- ESTIMATED: len(text)//4 fallback when no counter exists
- IDE_EXPORTED / IDE_CREDITS: documented IDE adapter or NOT_MEASURED
- Distinct reporting of:
    1. Representation compression (source vs PolyFlow IR)
    2. Context compression (baseline candidate vs RCIR delivered)
    3. Live model provider token reduction (baseline vs RCIR)
"""

from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class MeasurementSource(str, Enum):
    PROVIDER_NATIVE = "PROVIDER_NATIVE"
    TOKENIZER_EXACT = "TOKENIZER_EXACT"
    ESTIMATED = "ESTIMATED"
    IDE_EXPORTED = "IDE_EXPORTED"


@dataclass
class UsageRecord:
    """
    Canonical usage event for every inference and context retrieval.
    Section 9.2 schema.
    """
    run_id: str
    trial_id: str
    task_id: str
    condition: str
    provider: str
    model: str
    turn: int
    measurement_source: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    context_tokens: int = 0
    tool_result_tokens: int = 0
    latency: float = 0.0
    cached_input_tokens: Optional[int] = None
    provider_cost_usd: Optional[float] = None
    cost_method: str = "NONE"
    ide_credits: Optional[float] = None
    credit_method: str = "NOT_MEASURED"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UsageRecord:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class IDEUsageAdapter:
    """Adapter for IDE credits and documented IDE token interfaces (Section 9.4)."""

    @staticmethod
    def get_ide_credits(env_var: str = "POLYFLOW_IDE_CREDITS") -> tuple[Optional[float], str]:
        """
        Reads documented environment/API export if provided.
        Never scrapes private UI internals.
        """
        import os
        val = os.environ.get(env_var)
        if val is not None:
            try:
                return float(val), "IDE_EXPORTED"
            except ValueError:
                pass
        return None, "NOT_MEASURED"


class TelemetryCollector:
    """
    Aggregates usage records and computes statistical distribution and reductions.
    Section 9.5, 9.6, 9.7 requirements.
    """

    def __init__(self):
        self.records: List[UsageRecord] = []

    def record_usage(self, record: UsageRecord) -> None:
        self.records.append(record)

    def get_trial_records(self, trial_id: str) -> List[UsageRecord]:
        return [r for r in self.records if r.trial_id == trial_id]

    @staticmethod
    def compute_distribution(values: List[float | int]) -> Dict[str, Any]:
        """Computes mean, median, p25, p75, p95 for a list of values."""
        if not values:
            return {"count": 0, "mean": 0.0, "median": 0.0, "p25": 0.0, "p75": 0.0, "p95": 0.0}

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        def percentile(p: float) -> float:
            k = (n - 1) * (p / 100.0)
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return float(sorted_vals[int(k)])
            return float(sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f))

        mean_val = sum(sorted_vals) / n
        median_val = percentile(50)
        p25_val = percentile(25)
        p75_val = percentile(75)
        p95_val = percentile(95)

        return {
            "count": n,
            "mean": round(mean_val, 2),
            "median": round(median_val, 2),
            "p25": round(p25_val, 2),
            "p75": round(p75_val, 2),
            "p95": round(p95_val, 2),
        }

    def aggregate_ab_comparison(
        self,
        baseline_trial_ids: List[str],
        rcir_trial_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Produces rigorous statistical comparison between baseline and RCIR.
        Separates the three reductions (Section 9.5):
        A. Representation compression
        B. Context compression
        C. Live model token reduction
        """
        baseline_records = [r for r in self.records if r.trial_id in baseline_trial_ids]
        rcir_records = [r for r in self.records if r.trial_id in rcir_trial_ids]

        # Group by trial
        def trial_totals(recs: List[UsageRecord]) -> Dict[str, Dict[str, Any]]:
            grouped: Dict[str, Dict[str, Any]] = {}
            for r in recs:
                if r.trial_id not in grouped:
                    grouped[r.trial_id] = {
                        "task_id": r.task_id,
                        "condition": r.condition,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                        "context_tokens": 0,
                        "latency": 0.0,
                    }
                grouped[r.trial_id]["input_tokens"] += r.input_tokens
                grouped[r.trial_id]["output_tokens"] += r.output_tokens
                grouped[r.trial_id]["total_tokens"] += r.total_tokens
                grouped[r.trial_id]["context_tokens"] += r.context_tokens
                grouped[r.trial_id]["latency"] += r.latency
            return grouped

        b_trials = trial_totals(baseline_records)
        r_trials = trial_totals(rcir_records)

        b_totals = [t["total_tokens"] for t in b_trials.values()]
        r_totals = [t["total_tokens"] for t in r_trials.values()]

        b_context = [t["context_tokens"] for t in b_trials.values()]
        r_context = [t["context_tokens"] for t in r_trials.values()]

        b_stats = self.compute_distribution(b_totals)
        r_stats = self.compute_distribution(r_totals)

        mean_delta = b_stats["mean"] - r_stats["mean"]
        mean_reduction_pct = (
            round((mean_delta / b_stats["mean"]) * 100, 2)
            if b_stats["mean"] > 0
            else 0.0
        )

        ctx_b_mean = sum(b_context) / len(b_context) if b_context else 0.0
        ctx_r_mean = sum(r_context) / len(r_context) if r_context else 0.0
        ctx_delta = ctx_b_mean - ctx_r_mean
        ctx_reduction_pct = (
            round((ctx_delta / ctx_b_mean) * 100, 2)
            if ctx_b_mean > 0
            else 0.0
        )

        return {
            "baseline_tokens": b_stats,
            "rcir_tokens": r_stats,
            "live_model_reduction": {
                "absolute_token_delta": round(mean_delta, 2),
                "relative_percentage": mean_reduction_pct,
            },
            "context_compression": {
                "baseline_mean_context_tokens": round(ctx_b_mean, 2),
                "rcir_mean_context_tokens": round(ctx_r_mean, 2),
                "absolute_context_delta": round(ctx_delta, 2),
                "relative_percentage": ctx_reduction_pct,
            },
            "representation_compression": {
                "description": "Repo Source IR vs PolyFlow Semantic Graph",
                "reduction_ratio": "Measured independently per repository",
            },
        }
