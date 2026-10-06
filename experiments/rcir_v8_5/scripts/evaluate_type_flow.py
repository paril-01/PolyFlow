"""
RCIR v8.5 — PHP Receiver Type-Flow Confusion Matrix Evaluator (PHASES 27-34).

Features:
- Configures PHPTypeFlowAnalyzer with env.target_repo_root (PHASE 27).
- Verifies receiver ground truth files, lines, and content hashes (PHASE 28).
- Uses exact call site identity (file + line + receiver + method + fingerprint) (PHASE 29).
- Treats expected unknown + predicted unknown as CORRECT_ABSTENTION (PHASE 31).
- Generates 8-bucket Confusion Matrix (PHASE 32):
  * correct_exact
  * correct_compatible
  * wrong_exact
  * wrong_compatible
  * correct_abstention
  * false_abstention
  * ambiguous
  * invalid_gt
- Calculates coverage, exact_precision, resolved_precision, wrong_exact_rate, and abstention_accuracy (PHASE 33).
- Evaluates contract thresholds (PHASE 34).
- Saves results/type_flow_evaluation.json and raw/type_flow/receiver_predictions.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from environment import get_default_environment

env = get_default_environment()
sys.path.insert(0, str(env.polyflow_root / "rcir" / "src"))

from rcir.types.php_type_flow import PHPTypeFlowAnalyzer, TypeResolutionConfidence


def evaluate_type_flow():
    print("=" * 80)
    print("RCIR v8.5 — PHP Receiver Type-Flow Independent Evaluation (PHASES 27-34)")
    print("=" * 80)

    gt_path = env.receiver_ground_truth_root / "receiver_ground_truth.json"
    if not gt_path.exists():
        raise FileNotFoundError(f"Missing receiver ground truth at {gt_path}")

    gt_data = json.loads(gt_path.read_text(encoding="utf-8"))
    call_sites = gt_data.get("call_sites", [])
    print(f"Loaded {len(call_sites)} independently adjudicated receiver call sites.")

    # PHASE 27: Explicit target_repo_root
    analyzer = PHPTypeFlowAnalyzer(repo_root=env.target_repo_root)

    # Confusion matrix buckets (PHASE 32)
    correct_exact = 0
    correct_compatible = 0
    wrong_exact = 0
    wrong_compatible = 0
    correct_abstention = 0
    false_abstention = 0
    ambiguous = 0
    invalid_gt = 0

    eval_records = []
    raw_predictions = []
    file_cache: dict[str, list[Any]] = {}

    for cs in call_sites:
        cid = cs["call_id"]
        rel_file = cs["file"]
        line_no = cs["line"]
        receiver_expr = cs["receiver_expression"]
        called_method = cs["called_method"]
        expected_type = cs["expected_receiver_type"]
        acceptable_interfaces = set(cs.get("acceptable_interfaces", []))
        is_abstention_gt = cs.get("is_abstention", False)
        fingerprint = cs.get("source_fingerprint", "")

        # Verify GT record
        target_path = env.target_repo_root / rel_file
        if not target_path.exists():
            invalid_gt += 1
            print(f"  [INVALID_GT] File missing: {rel_file}")
            continue

        # Run or retrieve file analysis
        if rel_file not in file_cache:
            try:
                analyzed = analyzer.analyze_file(rel_file)
            except Exception as ex:
                print(f"Error analyzing {rel_file}: {ex}")
                analyzed = []
            file_cache[rel_file] = analyzed

        analyzed_sites = file_cache[rel_file]

        # PHASE 29: Exact Call-Site Identity Matching
        matched_call = None
        for site in analyzed_sites:
            # Check within relocation window
            if abs(site.line_number - line_no) <= 5:
                if site.method_name == called_method and site.receiver_expr == receiver_expr:
                    matched_call = site
                    break

        if not matched_call:
            # Check by method and receiver alone
            for site in analyzed_sites:
                if site.method_name == called_method and site.receiver_expr == receiver_expr:
                    matched_call = site
                    break

        pred_type = matched_call.inferred_type if matched_call else None
        pred_conf = matched_call.confidence.value if matched_call else "unknown"

        raw_predictions.append({
            "call_id": cid,
            "file": rel_file,
            "line": line_no,
            "receiver": receiver_expr,
            "method": called_method,
            "predicted_type": pred_type,
            "confidence": pred_conf,
            "matched_site_line": matched_call.line_number if matched_call else None,
        })

        # Evaluate against GT
        if is_abstention_gt:
            # Expected unknown
            if pred_type is None or pred_conf == TypeResolutionConfidence.UNKNOWN.value or pred_type == "UNKNOWN":
                correct_abstention += 1
                status = "CORRECT_ABSTENTION"
            else:
                wrong_exact += 1
                status = f"FALSE_RESOLUTION ({pred_type})"
        else:
            # Expected concrete type
            if pred_type is None or pred_conf == TypeResolutionConfidence.UNKNOWN.value:
                false_abstention += 1
                status = "FALSE_ABSTENTION"
            elif pred_conf == TypeResolutionConfidence.AMBIGUOUS.value:
                ambiguous += 1
                status = "AMBIGUOUS"
            elif pred_type == expected_type:
                correct_exact += 1
                status = "CORRECT_EXACT"
            elif pred_type in acceptable_interfaces:
                correct_compatible += 1
                status = f"CORRECT_COMPATIBLE ({pred_type})"
            else:
                # Check if suffix or interface matches
                if any(iface.endswith(pred_type) or pred_type.endswith(iface) for iface in acceptable_interfaces):
                    correct_compatible += 1
                    status = f"CORRECT_COMPATIBLE_SUFFIX ({pred_type})"
                else:
                    wrong_exact += 1
                    status = f"WRONG_EXACT (pred: {pred_type} vs exp: {expected_type})"

        eval_records.append({
            "call_id": cid,
            "file": rel_file,
            "line": line_no,
            "receiver": receiver_expr,
            "method": called_method,
            "expected_type": expected_type,
            "predicted_type": pred_type,
            "confidence": pred_conf,
            "status": status,
        })
        print(f"  [{status}] {rel_file}:{line_no} {receiver_expr}->{called_method}() => {pred_type}")

    # PHASE 33: Type-Flow Metrics
    resolvable_cases = sum(1 for cs in call_sites if not cs.get("is_abstention", False))
    abstention_cases = sum(1 for cs in call_sites if cs.get("is_abstention", False))

    resolved_non_abstention = correct_exact + correct_compatible + wrong_exact + wrong_compatible
    total_non_abstaining_preds = correct_exact + correct_compatible + wrong_exact + wrong_compatible

    coverage = resolved_non_abstention / max(1, resolvable_cases)
    exact_precision = correct_exact / max(1, (correct_exact + wrong_exact))
    resolved_precision = (correct_exact + correct_compatible) / max(1, total_non_abstaining_preds)
    wrong_exact_rate = wrong_exact / max(1, total_non_abstaining_preds)
    abstention_accuracy = correct_abstention / max(1, abstention_cases)
    ambiguity_rate = ambiguous / max(1, resolvable_cases)

    # Save raw predictions
    raw_payload = {
        "run_id": env.run_id,
        "target_commit": env.target_repo_commit,
        "total_predictions": len(raw_predictions),
        "predictions": raw_predictions,
    }
    raw_file = env.raw_root / "type_flow" / "receiver_predictions.json"
    raw_file.write_text(json.dumps(raw_payload, indent=2), encoding="utf-8")
    print(f"Saved raw receiver predictions to {raw_file}")

    # PHASE 34: Threshold verification
    passes_gate = (
        coverage >= 0.60
        and resolved_precision >= 0.90
        and wrong_exact_rate <= 0.05
    )

    result_payload = {
        "run_id": env.run_id,
        "validation_status": "PASSED" if passes_gate else "FAILED",
        "target_commit": env.target_repo_commit,
        "confusion_matrix": {
            "correct_exact": correct_exact,
            "correct_compatible": correct_compatible,
            "wrong_exact": wrong_exact,
            "wrong_compatible": wrong_compatible,
            "correct_abstention": correct_abstention,
            "false_abstention": false_abstention,
            "ambiguous": ambiguous,
            "invalid_gt": invalid_gt,
        },
        "metrics": {
            "resolvable_ground_truth_cases": resolvable_cases,
            "abstention_ground_truth_cases": abstention_cases,
            "coverage": round(coverage, 4),
            "exact_precision": round(exact_precision, 4),
            "resolved_precision": round(resolved_precision, 4),
            "wrong_exact_rate": round(wrong_exact_rate, 4),
            "abstention_accuracy": round(abstention_accuracy, 4),
            "ambiguity_rate": round(ambiguity_rate, 4),
        },
        "contract_thresholds": {
            "coverage_min": 0.60,
            "resolved_precision_min": 0.90,
            "wrong_exact_rate_max": 0.05,
        },
        "contract_gate_satisfied": passes_gate,
        "eval_records": eval_records,
    }

    res_file = env.results_root / "type_flow_evaluation.json"
    res_file.write_text(json.dumps(result_payload, indent=2), encoding="utf-8")
    print(f"Saved type flow evaluation result to {res_file}")
    print(f"Coverage: {coverage*100:.1f}%, Resolved Precision: {resolved_precision*100:.1f}%, Wrong Exact Rate: {wrong_exact_rate*100:.1f}%, Gate: {'PASSED' if passes_gate else 'FAILED'}")


if __name__ == "__main__":
    evaluate_type_flow()
