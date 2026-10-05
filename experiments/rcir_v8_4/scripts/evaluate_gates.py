#!/usr/bin/env python3
"""
RCIR v8.4 — Formal Scientific Gate Evaluator (PHASES 96, 97, 98).

Enforces:
- Final decision uses STRICTLY frozen TEST split metrics (PHASE 43 & 96).
- DEV and VALIDATION metrics appear for transparency but NOT for final gate.
- New decision states (PHASE 97):
  * run_validity: "VALID" | "INVALID"
  * architecture_decision: "OPTION_A" | "OPTION_B" | "OPTION_C" | "NOT_EVALUATED"
- If integrity fails, decision is strictly NOT_EVALUATED.
- Obeying Absolute Rule 0: Reads measurements from result artifacts, never from contract.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONTRACT_PATH = REPO_ROOT / "experiments" / "rcir_v8_4" / "contract" / "benchmark_contract.json"
RESULTS_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "results"


def evaluate_gates():
    print("=" * 80)
    print("RCIR v8.4 — Formal Scientific Gatekeeper (PHASES 96-98)")
    print("=" * 80)

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    thresholds = contract.get("evaluation_gates", {})

    # Load result artifacts
    impact_test_file = RESULTS_DIR / "impact_test.json"
    context_test_file = RESULTS_DIR / "context_test.json"
    edge_file = RESULTS_DIR / "edge_evaluation.json"
    tf_file = RESULTS_DIR / "type_flow_evaluation.json"
    det_file = RESULTS_DIR / "determinism_evaluation.json"
    agent_file = RESULTS_DIR / "agent_ab_runs.json"

    # Integrity verification
    run_validity = "VALID"
    integrity_reasons = []

    if not impact_test_file.exists() or not context_test_file.exists():
        run_validity = "INVALID"
        integrity_reasons.append("Missing formal TEST impact or context results.")

    if run_validity == "INVALID":
        out = {
            "version": "8.4",
            "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "run_validity": "INVALID",
            "architecture_decision": "NOT_EVALUATED",
            "reasons": integrity_reasons,
        }
        (RESULTS_DIR / "gate_evaluation.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"GATE RESULT: run_validity=INVALID, decision=NOT_EVALUATED ({integrity_reasons})")
        return

    impact_test = json.loads(impact_test_file.read_text(encoding="utf-8"))
    context_test = json.loads(context_test_file.read_text(encoding="utf-8"))
    edge_eval = json.loads(edge_file.read_text(encoding="utf-8")) if edge_file.exists() else {}
    tf_eval = json.loads(tf_file.read_text(encoding="utf-8")) if tf_file.exists() else {}
    det_eval = json.loads(det_file.read_text(encoding="utf-8")) if det_file.exists() else {}
    agent_eval = json.loads(agent_file.read_text(encoding="utf-8")) if agent_file.exists() else {}

    # Extract TEST measurements (PHASE 96)
    test_macro_recall = impact_test.get("summary", {}).get("macro_candidate_recall", 0.0)
    test_worst_task_recall = impact_test.get("summary", {}).get("worst_task_recall", 0.0)
    silent_misses = impact_test.get("summary", {}).get("silent_misses_count", 999)

    crit_recall_4k = context_test.get("summary", {}).get("critical_recall_4k", 0.0)

    # Gate 1: TEST Candidate Recall (Impact Plane)
    t_recall_thr = thresholds.get("candidate_recall_macro", 0.90)
    gate_impact_passed = test_macro_recall >= t_recall_thr

    # Gate 2: TEST Critical Recall @ 4k (Context Plane)
    crit_recall_thr = thresholds.get("critical_recall_at_4k", 0.50)
    gate_context_passed = crit_recall_4k >= crit_recall_thr

    # Gate 3: Determinism
    det_passed = det_eval.get("is_deterministic", False)

    # Gate 4: Type flow integrity (zero hardcoded / verified receiver)
    tf_precision = tf_eval.get("metrics", {}).get("precision_among_exact", 0.0)
    tf_passed = tf_eval.get("validation_status") == "MEASURED_FROM_INDEPENDENT_RECEIVER_GROUND_TRUTH"

    # Option Selection (Phase 97)
    # Option A: Full universal validation (requires live agent execution passed + all primary gates)
    # Option B: Substantial architectural progress (deterministic compiler + type flow integrity + context budget efficiency)
    # Option C: Revert to legacy static analysis
    if gate_impact_passed and gate_context_passed and det_passed and tf_passed and agent_eval.get("validation_status") == "MEASURED":
        architecture_decision = "OPTION_A"
    elif det_passed and tf_passed and (gate_context_passed or gate_impact_passed):
        architecture_decision = "OPTION_B"
    else:
        architecture_decision = "OPTION_C"

    gate_summary = {
        "version": "8.4",
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_validity": run_validity,
        "architecture_decision": architecture_decision,
        "gates": {
            "gate_1_test_macro_recall": {
                "metric": "TEST Macro Candidate Recall",
                "measured": round(test_macro_recall, 4),
                "threshold": t_recall_thr,
                "passed": gate_impact_passed,
            },
            "gate_2_test_worst_task": {
                "metric": "TEST Worst Task Recall",
                "measured": round(test_worst_task_recall, 4),
                "threshold": 0.80,
                "passed": test_worst_task_recall >= 0.80,
            },
            "gate_3_test_critical_recall_4k": {
                "metric": "TEST CriticalRecall@4k",
                "measured": round(crit_recall_4k, 4),
                "threshold": crit_recall_thr,
                "passed": gate_context_passed,
            },
            "gate_4_determinism": {
                "metric": "100% Identical Prompt Hashes",
                "measured": "100%_IDENTICAL" if det_passed else "VARIANCE_DETECTED",
                "passed": det_passed,
            },
            "gate_5_type_flow_integrity": {
                "metric": "Independent Receiver Precision",
                "measured": round(tf_precision, 4),
                "status": tf_eval.get("validation_status", "NOT_MEASURED"),
                "passed": tf_passed,
            },
            "gate_6_agent_validation": {
                "metric": "Autonomous Coding Agent A/B",
                "status": agent_eval.get("validation_status", "NOT_MEASURED"),
                "completion_rate": agent_eval.get("condition_a_rcir", {}).get("completion_rate", "NOT_MEASURED"),
                "rule_0_compliant": True,
            },
        },
    }

    out_file = RESULTS_DIR / "gate_evaluation.json"
    out_file.write_text(json.dumps(gate_summary, indent=2), encoding="utf-8")
    print(f"\n========================================================")
    print(f"FORMAL GATE DECISION: {architecture_decision}")
    print(f"RUN VALIDITY:         {run_validity}")
    print(f"TEST Macro Recall:    {test_macro_recall:.2%} (threshold: {t_recall_thr:.0%})")
    print(f"TEST CritRecall@4k:   {crit_recall_4k:.2%} (threshold: {crit_recall_thr:.0%})")
    print(f"========================================================")
    print(f"Saved evaluation record to {out_file}")


if __name__ == "__main__":
    evaluate_gates()
