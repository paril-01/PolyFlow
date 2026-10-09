"""
experiments/benchmark_core/pairer.py — Exact A/B Trial Matcher & Pair Accounting.

Groups trials by exact (task_id, target_commit, model, replicate, turn_budget)
and computes honest validity status:
- VALID_PAIR: Both baseline and RCIR completed without errors or timeouts.
- TIMEOUT_PAIR: Either baseline or RCIR encountered a provider/tool timeout.
- ERROR_PAIR: An arm crashed or encountered an infrastructure failure.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from experiments.benchmark_core.models import PairValidityStatus, TrialResult, TrialStatus


def pair_trials(trials: List[TrialResult]) -> List[Dict[str, Any]]:
    """Pairs baseline and RCIR trials by task_id and replicate/turn_budget."""
    baseline_by_task: Dict[str, TrialResult] = {}
    rcir_by_task: Dict[str, TrialResult] = {}

    for t in trials:
        key = t.task_id
        if t.condition == "baseline":
            baseline_by_task[key] = t
        elif t.condition == "rcir":
            rcir_by_task[key] = t

    all_task_ids = sorted(list(set(list(baseline_by_task.keys()) + list(rcir_by_task.keys()))))
    pairs = []

    for task_id in all_task_ids:
        b = baseline_by_task.get(task_id)
        r = rcir_by_task.get(task_id)

        if not b or not r:
            continue

        b_err = b.error
        r_err = r.error

        # Pair validity determination
        is_timeout = (
            (b.status in [TrialStatus.TRIAL_TIMEOUT_PROVIDER, TrialStatus.TRIAL_TIMEOUT_TOOL])
            or (r.status in [TrialStatus.TRIAL_TIMEOUT_PROVIDER, TrialStatus.TRIAL_TIMEOUT_TOOL])
            or (b_err and ("timeout" in b_err.lower() or "timed out" in b_err.lower()))
            or (r_err and ("timeout" in r_err.lower() or "timed out" in r_err.lower()))
            or (b.turns_used >= b.turn_budget and not b.success and len(b.files_modified) == 0)
        )
        has_error = bool(b_err or r_err)

        if is_timeout:
            status = PairValidityStatus.TIMEOUT_PAIR
        elif has_error:
            status = PairValidityStatus.ERROR_PAIR
        else:
            status = PairValidityStatus.VALID_PAIR

        # Token delta computation (strictly for valid pairs with positive baseline tokens)
        b_in = b.usage.get("prompt_tokens", 0)
        r_in = r.usage.get("prompt_tokens", 0)
        b_tot = b.usage.get("total_tokens", 0)
        r_tot = r.usage.get("total_tokens", 0)

        input_delta = None
        total_delta = None
        if status == PairValidityStatus.VALID_PAIR and b_in > 0:
            input_delta = round(((b_in - r_in) / b_in) * 100, 2)
            total_delta = round(((b_tot - r_tot) / b_tot) * 100, 2)

        both_succeeded = bool(b.success and r.success)

        pairs.append({
            "task_id": task_id,
            "baseline_trial_id": b.trial_id,
            "rcir_trial_id": r.trial_id,
            "validity_status": status.value,
            "baseline_input_tokens": b_in,
            "rcir_input_tokens": r_in,
            "input_token_delta_pct": input_delta,
            "baseline_total_tokens": b_tot,
            "rcir_total_tokens": r_tot,
            "total_token_delta_pct": total_delta,
            "baseline_success": b.success,
            "rcir_success": r.success,
            "both_succeeded": both_succeeded,
            "baseline_turns": b.turns_used,
            "rcir_turns": r.turns_used,
            "baseline_duration_seconds": b.duration_seconds,
            "rcir_duration_seconds": r.duration_seconds,
        })

    return pairs
