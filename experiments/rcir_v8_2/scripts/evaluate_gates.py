#!/usr/bin/env python3
"""
RCIR v8.2 — Machine-Enforced Decision Gate Evaluator.

Takes raw benchmark artifacts and the frozen benchmark contract JSON,
evaluates all primary and secondary gates mechanically, and outputs
the formal recommendation (OPTION A, OPTION B, or OPTION C).

Humans may NOT manually select or override Option A/B/C.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def evaluate_gates(
    dual_plane_data: dict[str, Any],
    contract_data: dict[str, Any],
    agent_ab_data: dict[str, Any] | None = None,
    p0_precision_50: float = 0.052,
) -> dict[str, Any]:
    """Evaluate benchmark outcomes against contract thresholds mechanically."""
    impact_contract = contract_data.get("impact_plane", {})
    context_contract = contract_data.get("context_plane", {})
    agent_contract = contract_data.get("agent", {})

    totals = dual_plane_data.get("totals", {})
    macro = dual_plane_data.get("macro_averages", {})
    per_task = dual_plane_data.get("per_task", [])

    # 1. Impact Plane Gates
    global_recall = totals.get("global_pool_recall", 0.0)
    macro_recall = macro.get("candidate_pool_recall", 0.0)
    silent_misses = totals.get("total_silent_misses", 9999)

    per_task_recalls = [t.get("candidate_pool_recall", 0.0) for t in per_task]
    worst_task_recall = min(per_task_recalls) if per_task_recalls else 0.0

    gate_impact_recall = {
        "name": "Global & Macro Pool Recall",
        "threshold_global": impact_contract.get("global_pool_recall_min", 0.95),
        "measured_global": round(global_recall, 4),
        "threshold_macro": impact_contract.get("macro_pool_recall_min", 0.95),
        "measured_macro": round(macro_recall, 4),
        "worst_task_recall": round(worst_task_recall, 4),
        "per_task_floor": impact_contract.get("per_task_pool_recall_floor", 0.90),
        "passed": (
            global_recall >= impact_contract.get("global_pool_recall_min", 0.95)
            and macro_recall >= impact_contract.get("macro_pool_recall_min", 0.95)
            and worst_task_recall >= impact_contract.get("per_task_pool_recall_floor", 0.90)
        ),
    }

    gate_silent_misses = {
        "name": "Silent Miss Limit",
        "threshold_max": impact_contract.get("max_silent_misses", 15),
        "measured": silent_misses,
        "passed": silent_misses <= impact_contract.get("max_silent_misses", 15),
    }

    # 2. Context Plane Gates (Evaluated on PRIMARY PIPELINE output, not isolated ablations)
    precision_20 = macro.get("precision_at", {}).get("20", macro.get("precision_at_20", 0.0))
    precision_50 = macro.get("precision_at", {}).get("50", macro.get("precision_at_50", 0.0))
    ndcg_50 = macro.get("ndcg_at", {}).get("50", macro.get("ndcg_at_50", 0.0))
    mrr = macro.get("mrr", 0.0)
    critical_budget_recall = macro.get("critical_recall_budget", 0.0)

    gate_context_precision = {
        "name": "Context Precision (P@20 and P@50)",
        "threshold_p20": context_contract.get("precision_at_20_min", 0.35),
        "measured_p20": round(precision_20, 4),
        "threshold_p50": context_contract.get("precision_at_50_min", 0.20),
        "measured_p50": round(precision_50, 4),
        "passed": (
            precision_20 >= context_contract.get("precision_at_20_min", 0.35)
            and precision_50 >= context_contract.get("precision_at_50_min", 0.20)
        ),
    }

    gate_context_ndcg = {
        "name": "Ranking Quality Graded nDCG@50",
        "threshold": context_contract.get("ndcg_at_50_min", 0.50),
        "measured": round(ndcg_50, 4),
        "passed": ndcg_50 >= context_contract.get("ndcg_at_50_min", 0.50),
    }

    gate_context_mrr = {
        "name": "Mean Reciprocal Rank (MRR)",
        "threshold": context_contract.get("mrr_min", 0.70),
        "measured": round(mrr, 4),
        "passed": mrr >= context_contract.get("mrr_min", 0.70),
    }

    gate_critical_budget_recall = {
        "name": "Critical Recall @ 4k Budget",
        "threshold": context_contract.get("critical_recall_budget_min", 0.60),
        "measured": round(critical_budget_recall, 4),
        "passed": critical_budget_recall >= context_contract.get("critical_recall_budget_min", 0.60),
    }

    # 3. Agent Execution Plane Gate
    is_simulated = True
    agent_success_rate = 0.0
    if agent_ab_data:
        cond_a = agent_ab_data.get("condition_a_with_rcir", {})
        is_simulated = cond_a.get("is_simulated", False) or cond_a.get("simulation_fallback", False)
        # Check explicit flag or lack of provenance
        if "model_digest" not in cond_a and not cond_a.get("provenance_verified", False):
            # Flag simulated if historical artifact without provenance
            if cond_a.get("success_rate", 0) == 1.0 and cond_a.get("turns_to_edit", 0) == 2 and not cond_a.get("worktrees"):
                is_simulated = True
        agent_success_rate = cond_a.get("success_rate", 0.0)

    gate_agent_e2e = {
        "name": "Live Verified Agent E2E Execution",
        "requires_real_provider": agent_contract.get("requires_real_provider", True),
        "is_simulated": is_simulated,
        "measured_success_rate": round(agent_success_rate, 4),
        "min_approved_rate": agent_contract.get("min_approved_rate", 0.80),
        "passed": (not is_simulated) and (agent_success_rate >= agent_contract.get("min_approved_rate", 0.80)),
    }

    gates = {
        "impact_recall": gate_impact_recall,
        "silent_miss_limit": gate_silent_misses,
        "context_precision": gate_context_precision,
        "context_ndcg": gate_context_ndcg,
        "context_mrr": gate_context_mrr,
        "critical_budget_recall": gate_critical_budget_recall,
        "real_agent_e2e": gate_agent_e2e,
    }

    # Primary Decision Logic
    all_primary_passed = all(g["passed"] for g in gates.values())

    if all_primary_passed:
        recommendation = "OPTION A — VALIDATED"
        rationale = "All primary Impact, Context, and Agent Execution gates passed against frozen thresholds with zero simulation."
    elif (
        global_recall >= 0.90
        and precision_50 > p0_precision_50
        and (precision_50 - p0_precision_50) >= 0.10
    ):
        recommendation = "OPTION B — PARTIALLY VALIDATED"
        failed_gates = [k for k, v in gates.items() if not v["passed"]]
        rationale = f"Architecture makes material progress over baseline (Recall >= 90%, P@50 > P0), but failed primary gates: {', '.join(failed_gates)}."
    else:
        recommendation = "OPTION C — REJECTED"
        rationale = "Failed to satisfy minimum recall or precision improvement criteria; architectural retreat required."

    return {
        "evaluation_contract_version": contract_data.get("contract_version", "unknown"),
        "gates": gates,
        "all_primary_passed": all_primary_passed,
        "recommendation": recommendation,
        "rationale": rationale,
    }


def main():
    parser = argparse.ArgumentParser(description="Machine-enforced decision gate evaluator for RCIR benchmarks")
    parser.add_argument("--dual-plane", required=True, help="Path to dual_plane JSON artifact")
    parser.add_argument("--contract", required=True, help="Path to benchmark_contract.json")
    parser.add_argument("--agent-ab", help="Path to agent_ab JSON artifact")
    parser.add_argument("--output", help="Optional path to output evaluation JSON")
    args = parser.parse_args()

    with open(args.dual_plane, "r", encoding="utf-8") as f:
        dual_plane = json.load(f)

    with open(args.contract, "r", encoding="utf-8") as f:
        contract = json.load(f)

    agent_ab = None
    if args.agent_ab and Path(args.agent_ab).exists():
        with open(args.agent_ab, "r", encoding="utf-8") as f:
            agent_ab = json.load(f)

    result = evaluate_gates(dual_plane, contract, agent_ab)

    print(json.dumps(result, indent=2))

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\nWritten gate evaluation to {args.output}")

    # Return exit code: 0 if Option A, 1 if Option B, 2 if Option C
    if result["recommendation"].startswith("OPTION A"):
        sys.exit(0)
    elif result["recommendation"].startswith("OPTION B"):
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
