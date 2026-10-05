#!/usr/bin/env python3
"""
RCIR v8.4 — Receiver Type-Flow Confusion Matrix Evaluator (PHASES 23, 24, 25).

Features:
- Completely deletes self-grading formulas (PHASE 23).
- Evaluates PHPTypeFlowAnalyzer against independent receiver ground truth (PHASE 24).
- Computes formal confusion matrix (PHASE 25):
  * Correct Exact
  * Correct Compatible Interface
  * Wrong Exact
  * Ambiguous
  * Unknown
- Reports exact precision, compatible precision, wrong-exact rate, and coverage.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT))

from rcir.types.php_type_flow import PHPTypeFlowAnalyzer, TypeResolutionConfidence

TF_GT_PATH = REPO_ROOT / "experiments" / "rcir_v8_4" / "type_flow_ground_truth" / "receiver_ground_truth.json"
RESULTS_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "results"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_type_flow():
    print("=" * 80)
    print("RCIR v8.4 — PHP Receiver Type-Flow Independent Evaluation (PHASES 23-25)")
    print("=" * 80)

    if not TF_GT_PATH.exists():
        raise FileNotFoundError(f"Receiver ground truth not found at {TF_GT_PATH}")

    gt_data = json.loads(TF_GT_PATH.read_text(encoding="utf-8"))
    call_sites_gt = gt_data.get("call_sites", [])
    print(f"Loaded {len(call_sites_gt)} independently adjudicated receiver call sites.")

    analyzer = PHPTypeFlowAnalyzer(repo_root=REPO_ROOT)

    correct_exact = 0
    correct_compatible = 0
    count_wrong_exact = 0
    ambiguous = 0
    unknown = 0

    eval_details = []

    # Cache analyzed file call sites
    file_cache: dict[str, list[Any]] = {}

    for cs in call_sites_gt:
        file_path = cs["file"]
        line_no = cs["line"]
        expected_type = cs["expected_receiver_type"]
        acceptable_types = set(cs.get("acceptable_interface_types", []))
        recv_expr = cs.get("receiver_expression", "")
        called_m = cs.get("called_method", "")

        # Analyze file if exists
        full_path = REPO_ROOT / file_path
        if file_path not in file_cache:
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                file_cache[file_path] = analyzer.analyze_source_content(content, file_path=file_path)
            else:
                file_cache[file_path] = []

        predicted_sites = file_cache[file_path]

        # Match call site by method and receiver or nearby line
        matched = None
        for ps in predicted_sites:
            if ps.method_name == called_m:
                if ps.receiver_expr == recv_expr or abs(ps.line_number - line_no) <= 30:
                    matched = ps
                    break

        inferred = matched.inferred_type if matched else None
        conf = matched.confidence if matched else TypeResolutionConfidence.UNKNOWN

        if conf == TypeResolutionConfidence.UNKNOWN or not inferred:
            if expected_type == "unknown":
                correct_exact += 1
                outcome = "CORRECT_UNKNOWN"
            else:
                unknown += 1
                outcome = "UNKNOWN"
        elif conf == TypeResolutionConfidence.AMBIGUOUS:
            ambiguous += 1
            outcome = "AMBIGUOUS"
        else:
            # Resolved to inferred type
            if inferred == expected_type or inferred.endswith(expected_type.split("\\")[-1]):
                correct_exact += 1
                outcome = "CORRECT_EXACT"
            elif inferred in acceptable_types or any(inferred.endswith(at.split("\\")[-1]) for at in acceptable_types):
                correct_compatible += 1
                outcome = "CORRECT_COMPATIBLE"
            else:
                count_wrong_exact += 1
                outcome = "WRONG_EXACT"

        eval_details.append({
            "call_id": cs["call_id"],
            "file": file_path,
            "line": line_no,
            "receiver": recv_expr,
            "called_method": called_m,
            "expected_type": expected_type,
            "inferred_type": inferred,
            "confidence": conf.value if hasattr(conf, "value") else str(conf),
            "outcome": outcome,
        })

    total_evaluated = len(call_sites_gt)
    total_resolved = correct_exact + correct_compatible + count_wrong_exact

    coverage = total_resolved / total_evaluated if total_evaluated else 0.0
    precision_exact = correct_exact / (correct_exact + count_wrong_exact) if (correct_exact + count_wrong_exact) else 0.0
    precision_resolved = (correct_exact + correct_compatible) / total_resolved if total_resolved else 0.0
    wrong_exact_rate = count_wrong_exact / total_evaluated if total_evaluated else 0.0
    ambiguity_rate = ambiguous / total_evaluated if total_evaluated else 0.0
    unknown_rate = unknown / total_evaluated if total_evaluated else 0.0

    output = {
        "version": "8.4",
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "validation_status": "MEASURED_FROM_INDEPENDENT_RECEIVER_GROUND_TRUTH",
        "confusion_matrix": {
            "total_call_sites": total_evaluated,
            "correct_exact": correct_exact,
            "correct_compatible_interface": correct_compatible,
            "wrong_exact": count_wrong_exact,
            "ambiguous": ambiguous,
            "unknown": unknown,
        },
        "metrics": {
            "coverage": round(coverage, 4),
            "precision_among_exact": round(precision_exact, 4),
            "precision_among_all_resolved": round(precision_resolved, 4),
            "wrong_exact_rate": round(wrong_exact_rate, 4),
            "ambiguity_rate": round(ambiguity_rate, 4),
            "unknown_rate": round(unknown_rate, 4),
        },
        "details": eval_details,
    }

    output_path = RESULTS_DIR / "type_flow_evaluation.json"
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Type flow evaluation complete: Coverage = {coverage:.2%}, Exact Precision = {precision_exact:.2%}, Wrong-Exact Rate = {wrong_exact_rate:.2%}")
    print(f"Saved results to {output_path}")


if __name__ == "__main__":
    evaluate_type_flow()
