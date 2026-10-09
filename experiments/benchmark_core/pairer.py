"""
experiments/benchmark_core/pairer.py — Exact A/B Trial Matcher & Pair Accounting.

Groups trials by exact (task_id, target_commit, model, replicate, turn_budget)
and computes honest validity status:
- VALID_PAIR: Both baseline and RCIR completed without errors or timeouts.
- TIMEOUT_PAIR: Either baseline or RCIR encountered a provider/tool timeout.
- ERROR_PAIR: An arm crashed or encountered an infrastructure failure.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
from experiments.benchmark_core.models import PairValidityStatus, TrialKey, TrialResult, TrialStatus


def get_trial_key(t: TrialResult) -> Tuple[str, str, str, int, int, int, str]:
    """Extracts the exact 7-tuple comparability key from a TrialResult."""
    if t.key:
        return (
            t.key.task_id,
            t.key.target_commit,
            t.key.model,
            t.key.seed,
            t.key.turn_budget,
            t.key.replicate,
            t.key.experiment_version,
        )
    return (
        t.task_id,
        t.target_commit or "da57df078d0808a7235a0177bd99d23c010b472e",
        t.model,
        getattr(t, "seed", 42),
        t.turn_budget,
        getattr(t, "replicate", 1),
        "3.0.0",
    )


def pair_trials(trials: List[TrialResult]) -> List[Dict[str, Any]]:
    """
    Pairs baseline and RCIR trials by exact 7-tuple:
    (task_id, target_commit, model, seed, turn_budget, replicate, experiment_version).
    Enforces Rule 0: multi-replicates are preserved, duplicate/missing arms flagged.
    """
    baseline_by_key: Dict[Tuple, List[TrialResult]] = defaultdict(list)
    rcir_by_key: Dict[Tuple, List[TrialResult]] = defaultdict(list)

    for t in trials:
        key = get_trial_key(t)
        if t.condition == "baseline":
            baseline_by_key[key].append(t)
        elif t.condition == "rcir":
            rcir_by_key[key].append(t)

    all_keys = sorted(list(set(list(baseline_by_key.keys()) + list(rcir_by_key.keys()))))
    pairs = []

    for key in all_keys:
        task_id, target_commit, model, seed, turn_budget, replicate, exp_ver = key
        b_list = baseline_by_key.get(key, [])
        r_list = rcir_by_key.get(key, [])

        # Check arm multiplicity
        if len(b_list) > 1 or len(r_list) > 1:
            status = PairValidityStatus.DUPLICATE_ARM
            b = b_list[0] if b_list else None
            r = r_list[0] if r_list else None
        elif len(b_list) == 0 or len(r_list) == 0:
            status = PairValidityStatus.INCOMPLETE_PAIR
            b = b_list[0] if b_list else None
            r = r_list[0] if r_list else None
        else:
            b = b_list[0]
            r = r_list[0]

            b_err = b.error
            r_err = r.error

            # True timeout: only provider or tool timeouts
            is_timeout = (
                (b.status in [TrialStatus.TRIAL_TIMEOUT_PROVIDER, TrialStatus.TRIAL_TIMEOUT_TOOL])
                or (r.status in [TrialStatus.TRIAL_TIMEOUT_PROVIDER, TrialStatus.TRIAL_TIMEOUT_TOOL])
                or bool(b_err and ("timeout" in b_err.lower() or "timed out" in b_err.lower()))
                or bool(r_err and ("timeout" in r_err.lower() or "timed out" in r_err.lower()))
            )
            is_invalid_context = (
                b.status == TrialStatus.TRIAL_INVALID_CONTEXT
                or r.status == TrialStatus.TRIAL_INVALID_CONTEXT
            )
            is_invalid_setup = (
                b.status == TrialStatus.TRIAL_INVALID_SETUP
                or r.status == TrialStatus.TRIAL_INVALID_SETUP
            )
            has_error = bool(b_err or r_err)

            if is_timeout:
                status = PairValidityStatus.TIMEOUT_PAIR
            elif is_invalid_context:
                status = PairValidityStatus.INVALID_CONTEXT_PAIR
            elif is_invalid_setup:
                status = PairValidityStatus.INVALID_SETUP_PAIR
            elif has_error:
                status = PairValidityStatus.ERROR_PAIR
            else:
                status = PairValidityStatus.VALID_PAIR

        # Safe attribute extraction
        b_in = b.usage.get("prompt_tokens", 0) if b else 0
        r_in = r.usage.get("prompt_tokens", 0) if r else 0
        b_tot = b.usage.get("total_tokens", 0) if b else 0
        r_tot = r.usage.get("total_tokens", 0) if r else 0

        input_delta = None
        total_delta = None
        if status == PairValidityStatus.VALID_PAIR and b_in > 0:
            input_delta = round(((b_in - r_in) / b_in) * 100, 2)
            total_delta = round(((b_tot - r_tot) / b_tot) * 100, 2)

        both_succeeded = bool(b and r and b.success and r.success)

        pairs.append({
            "task_id": task_id,
            "target_commit": target_commit,
            "model": model,
            "seed": seed,
            "turn_budget": turn_budget,
            "replicate": replicate,
            "experiment_version": exp_ver,
            "baseline_trial_id": b.trial_id if b else None,
            "rcir_trial_id": r.trial_id if r else None,
            "validity_status": status.value,
            "baseline_input_tokens": b_in,
            "rcir_input_tokens": r_in,
            "input_token_delta_pct": input_delta,
            "baseline_total_tokens": b_tot,
            "rcir_total_tokens": r_tot,
            "total_token_delta_pct": total_delta,
            "baseline_success": b.success if b else False,
            "rcir_success": r.success if r else False,
            "both_succeeded": both_succeeded,
            "baseline_turns": b.turns_used if b else 0,
            "rcir_turns": r.turns_used if r else 0,
            "baseline_duration_seconds": b.duration_seconds if b else 0.0,
            "rcir_duration_seconds": r.duration_seconds if r else 0.0,
        })

    return pairs
