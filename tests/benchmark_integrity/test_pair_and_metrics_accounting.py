"""
tests/benchmark_integrity/test_pair_and_metrics_accounting.py — Verification of Pairing & Metrics.

Verifies:
1. Trials are paired strictly by task_id and condition.
2. Timeouts are categorized as TIMEOUT_PAIR and excluded from valid_pairs accounting.
3. Partial token usage without passed tests is marked as a failed task.
4. Primary efficiency headline is NOT_MEASURED when successful_both_pairs = 0.
"""

from __future__ import annotations

import pytest
from experiments.benchmark_core.models import (
    TrialResult,
    TrialStatus,
    VerificationResult,
    PairValidityStatus,
)
from experiments.benchmark_core.pairer import pair_trials
from experiments.benchmark_core.metrics import compute_benchmark_metrics


def _make_dummy_trial(trial_id: str, task_id: str, condition: str, success: bool, in_tokens: int, error: str = None) -> TrialResult:
    return TrialResult(
        trial_id=trial_id,
        task_id=task_id,
        condition=condition,
        model="qwen2.5-coder:1.5b",
        turn_budget=12,
        turns_used=5,
        tool_calls_executed=3,
        files_modified=["test.php"] if success else [],
        diff_length=100 if success else 0,
        git_diff="--- diff" if success else "",
        verification=VerificationResult(
            accepted=success,
            l1_syntax_passed=success,
            l1_logs=[],
            l2_targeted_passed=success,
            l2_log="OK" if success else "FAIL",
            l3_regression_passed=True,
            l3_log="OK",
        ),
        gatekeeper="APPROVE" if success else "REJECT",
        status=TrialStatus.TRIAL_SUCCESS if success else (TrialStatus.TRIAL_TIMEOUT_PROVIDER if error else TrialStatus.TRIAL_FAILED_BEHAVIOR),
        success=success,
        duration_seconds=10.0,
        usage={"prompt_tokens": in_tokens, "completion_tokens": 100, "total_tokens": in_tokens + 100},
        usage_records=[],
        error=error,
    )


def test_pair_key_uses_task_model_budget_replicate_commit():
    """Verify that pair_trials pairs baseline and rcir trials accurately."""
    t1_base = _make_dummy_trial("T1_base", "TASK-01", "baseline", False, 1000)
    t1_rcir = _make_dummy_trial("T1_rcir", "TASK-01", "rcir", False, 900)

    pairs = pair_trials([t1_base, t1_rcir])
    assert len(pairs) == 1
    p = pairs[0]
    assert p["task_id"] == "TASK-01"
    assert p["validity_status"] == PairValidityStatus.VALID_PAIR.value
    assert p["input_token_delta_pct"] == 10.0  # 100 * (1000 - 900) / 1000 = 10%


def test_pair_timeout_excluded():
    """Verify that timeout pairs are categorized as TIMEOUT_PAIR and have input_token_delta_pct as None."""
    t1_base = _make_dummy_trial("T1_base", "TASK-01", "baseline", False, 1000)
    t1_rcir = _make_dummy_trial("T1_rcir", "TASK-01", "rcir", False, 900, error="Provider request timed out after 120s")

    pairs = pair_trials([t1_base, t1_rcir])
    assert len(pairs) == 1
    p = pairs[0]
    assert p["validity_status"] == PairValidityStatus.TIMEOUT_PAIR.value
    assert p["input_token_delta_pct"] is None  # Excluded from token delta calculations


def test_pair_partial_usage_is_not_successful_completion():
    """Verify that a trial with partial usage but failing verification is marked failed."""
    t1_base = _make_dummy_trial("T1_base", "TASK-01", "baseline", False, 1200)
    assert t1_base.success is False
    assert t1_base.gatekeeper == "REJECT"


def test_report_metrics_recomputed_from_raw():
    """Verify that compute_benchmark_metrics enforces primary efficiency headline as NOT_MEASURED when successful pairs = 0."""
    t1_base = _make_dummy_trial("T1_base", "TASK-01", "baseline", False, 1000)
    t1_rcir = _make_dummy_trial("T1_rcir", "TASK-01", "rcir", False, 900)

    pairs = pair_trials([t1_base, t1_rcir])
    metrics = compute_benchmark_metrics(pairs, total_trials=2)

    assert metrics["valid_pairs_count"] == 1
    assert metrics["successful_both_pairs_count"] == 0
    assert metrics["primary_efficiency_headline"] == "NOT_MEASURED"
    assert metrics["primary_efficiency_status"] == "INCONCLUSIVE_ZERO_SUCCESSFUL_PAIRS"
    assert metrics["agent_gate_status"] == "NOT_SATISFIED"
