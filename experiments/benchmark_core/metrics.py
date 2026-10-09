"""
experiments/benchmark_core/metrics.py — Statistical Metrics and Gate Computation.

Computes:
- Valid pair counts, timeout counts, both-successful pair counts.
- Median input token delta and total token delta over valid pairs.
- Primary efficiency headline: marked NOT_MEASURED if both-successful pairs = 0.
- Micro and macro task success rates for baseline and RCIR.
"""

from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional
from experiments.benchmark_core.models import PairValidityStatus


def compute_benchmark_metrics(pairs: List[Dict[str, Any]], total_trials: int) -> Dict[str, Any]:
    valid_pairs = [p for p in pairs if p.get("validity_status") == PairValidityStatus.VALID_PAIR.value]
    timeout_pairs = [p for p in pairs if p.get("validity_status") == PairValidityStatus.TIMEOUT_PAIR.value]
    successful_pairs = [p for p in valid_pairs if p.get("both_succeeded", False)]

    # Input token deltas over valid pairs
    valid_input_deltas = [
        p["input_token_delta_pct"] for p in valid_pairs if p.get("input_token_delta_pct") is not None
    ]
    median_input_delta = round(statistics.median(valid_input_deltas), 2) if valid_input_deltas else None

    # Total token deltas over valid pairs
    valid_total_deltas = [
        p["total_token_delta_pct"] for p in valid_pairs if p.get("total_token_delta_pct") is not None
    ]
    median_total_delta = round(statistics.median(valid_total_deltas), 2) if valid_total_deltas else None

    # Success counts
    baseline_successes = sum(1 for p in pairs if p.get("baseline_success"))
    rcir_successes = sum(1 for p in pairs if p.get("rcir_success"))

    # Primary efficiency metric: requires both-successful pairs
    if len(successful_pairs) > 0:
        both_succ_deltas = [
            p["input_token_delta_pct"] for p in successful_pairs if p.get("input_token_delta_pct") is not None
        ]
        primary_efficiency_headline = (
            f"{statistics.median(both_succ_deltas):.2f}%" if both_succ_deltas else "NOT_MEASURED"
        )
        primary_efficiency_status = "MEASURED"
    else:
        primary_efficiency_headline = "NOT_MEASURED"
        primary_efficiency_status = "INCONCLUSIVE_ZERO_SUCCESSFUL_PAIRS"

    # Agent success gate status
    agent_gate_status = "SATISFIED" if rcir_successes > 0 and len(successful_pairs) > 0 else "NOT_SATISFIED"

    return {
        "total_trials": total_trials,
        "total_pairs": len(pairs),
        "valid_pairs_count": len(valid_pairs),
        "timeout_pairs_count": len(timeout_pairs),
        "successful_both_pairs_count": len(successful_pairs),
        "baseline_success_count": baseline_successes,
        "rcir_success_count": rcir_successes,
        "exploratory_median_input_token_delta_pct": median_input_delta,
        "exploratory_median_total_token_delta_pct": median_total_delta,
        "primary_efficiency_headline": primary_efficiency_headline,
        "primary_efficiency_status": primary_efficiency_status,
        "agent_gate_status": agent_gate_status,
    }
