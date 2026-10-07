#!/usr/bin/env python3
"""
RCIR v8.5.1 — PHP Receiver Type-Flow Confusion Matrix Evaluator (PHASES 27-34).

Features:
- Configures PHPTypeFlowAnalyzer with env.target_repo_root (PHASE 27).
- Verifies receiver ground truth files, lines, and content hashes (PHASE 28).
- Uses exact normalized fingerprint and unique call site identity matching (PHASE 29 & v8.5.1).
- Uses canonical graph hierarchy for true type compatibility checking.
- Fails formal gate if invalid_gt > 0.
- Calculates coverage, exact_precision, resolved_precision, wrong_exact_rate, and abstention_accuracy.
- Evaluates contract thresholds.
- Attaches standard cryptographic provenance envelope.
- Saves results/type_flow_evaluation.json and raw/type_flow/receiver_predictions.json.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Optional, Set

from environment import get_default_environment
from provenance import build_provenance_envelope

env = get_default_environment()
sys.path.insert(0, str(env.polyflow_root / "rcir" / "src"))

from rcir.graph.canonical_graph import CanonicalGraph
from rcir.types.php_type_flow import PHPTypeFlowAnalyzer, TypeResolutionConfidence


def evaluate_type_flow():
    print("=" * 80)
    print("RCIR v8.5.1 — PHP Receiver Type-Flow Independent Evaluation (PHASES 27-34)")
    print("=" * 80)

    gt_path = env.receiver_ground_truth_root / "receiver_ground_truth.json"
    if not gt_path.exists():
        raise FileNotFoundError(f"Missing receiver ground truth at {gt_path}")

    gt_data = json.loads(gt_path.read_text(encoding="utf-8"))
    call_sites = gt_data.get("call_sites", [])
    print(f"Loaded {len(call_sites)} independently adjudicated receiver call sites.")

    # Explicit target_repo_root
    analyzer = PHPTypeFlowAnalyzer(repo_root=env.target_repo_root)

    # Load canonical graph for true hierarchy-based type compatibility
    with open(env.graph_path, "r", encoding="utf-8") as f:
        raw_graph = json.load(f)
    cg = CanonicalGraph.from_legacy_dict(raw_graph, target_repo_root=env.target_repo_root)

    def classify_type_prediction(pred_t: Optional[str], exp_t: str, acc_interfaces: Set[str]) -> str:
        """Strict four-way classification (Issue 32)."""
        if not pred_t or pred_t == "UNKNOWN":
            return "UNRESOLVED"
        if pred_t == exp_t:
            return "EXACT"
        pred_res = cg.registry.resolve(pred_t)
        exp_res = cg.registry.resolve(exp_t)
        if pred_res.canonical_id and exp_res.canonical_id:
            for edge in cg.get_outgoing_edges(pred_res.canonical_id):
                if edge.target_id == exp_res.canonical_id and edge.edge_type.value in ("implements", "inherits"):
                    return "GRAPH_COMPATIBLE"
            for edge in cg.get_incoming_edges(exp_res.canonical_id):
                if edge.source_id == pred_res.canonical_id and edge.edge_type.value in ("implements", "inherits"):
                    return "GRAPH_COMPATIBLE"
        if pred_t in acc_interfaces:
            return "ADJUDICATED_COMPATIBLE"
        return "WRONG"

    # Confusion matrix buckets (Issue 32)
    correct_exact = 0
    correct_graph_compatible = 0
    correct_adjudicated_compatible = 0
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
        expected_method = cs.get("enclosing_method", "")

        # 1. Verify GT record file existence & hash
        target_path = env.target_repo_root / rel_file
        if not target_path.exists():
            invalid_gt += 1
            print(f"  [INVALID_GT] File missing: {rel_file}")
            continue

        if cs.get("file_hash"):
            actual_f_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
            if actual_f_hash != cs["file_hash"]:
                invalid_gt += 1
                print(f"  [INVALID_GT] File hash mismatch for {rel_file}: {actual_f_hash} != {cs['file_hash']}")
                continue

        target_lines = target_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        norm_expected_fp = re.sub(r"\s+", " ", fingerprint.strip()) if fingerprint else ""

        # Run or retrieve file analysis
        if rel_file not in file_cache:
            try:
                analyzed = analyzer.analyze_file(rel_file)
            except Exception as ex:
                print(f"Error analyzing {rel_file}: {ex}")
                analyzed = []
            file_cache[rel_file] = analyzed

        analyzed_sites = file_cache[rel_file]

        # 2. Exact Call-Site Identity Matching with normalized fingerprint & context (Issue 33)
        matched_call = None

        # Check exact line match first
        if 1 <= line_no <= len(target_lines):
            exact_line_norm = re.sub(r"\s+", " ", target_lines[line_no - 1].strip())
            if not norm_expected_fp or norm_expected_fp in exact_line_norm:
                for site in analyzed_sites:
                    if site.line_number == line_no and site.method_name == called_method and site.receiver_expr == receiver_expr:
                        matched_call = site
                        break

        # Relocation window (+/- 5 lines): search ONLY for exact normalized fingerprint + context
        if matched_call is None and norm_expected_fp:
            candidate_matches = []
            for site in analyzed_sites:
                if abs(site.line_number - line_no) <= 5 and site.method_name == called_method and site.receiver_expr == receiver_expr:
                    if expected_method and getattr(site, "enclosing_method", "") and site.enclosing_method != expected_method:
                        continue
                    s_idx = site.line_number - 1
                    if 0 <= s_idx < len(target_lines):
                        s_line_norm = re.sub(r"\s+", " ", target_lines[s_idx].strip())
                        if norm_expected_fp in s_line_norm:
                            candidate_matches.append(site)

            if len(candidate_matches) == 1:
                matched_call = candidate_matches[0]
            elif len(candidate_matches) > 1:
                invalid_gt += 1
                print(f"  [AMBIGUOUS_IDENTITY] Multiple duplicate identical call sites for {cid}")
                continue
            else:
                invalid_gt += 1
                print(f"  [INVALID_GT] Fingerprint not found in relocation window for {cid}")
                continue
        elif matched_call is None and not norm_expected_fp:
            candidate_matches = [
                s for s in analyzed_sites
                if abs(s.line_number - line_no) <= 5 and s.method_name == called_method and s.receiver_expr == receiver_expr
            ]
            if len(candidate_matches) == 1:
                matched_call = candidate_matches[0]
            else:
                invalid_gt += 1
                print(f"  [INVALID_GT] Cannot uniquely identify call site {cid} without fingerprint")
                continue

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
            else:
                cls_res = classify_type_prediction(pred_type, expected_type, acceptable_interfaces)
                if cls_res == "EXACT":
                    correct_exact += 1
                    status = "CORRECT_EXACT"
                elif cls_res == "GRAPH_COMPATIBLE":
                    correct_graph_compatible += 1
                    status = f"CORRECT_GRAPH_COMPATIBLE ({pred_type})"
                elif cls_res == "ADJUDICATED_COMPATIBLE":
                    correct_adjudicated_compatible += 1
                    status = f"CORRECT_ADJUDICATED_COMPATIBLE ({pred_type})"
                else:
                    wrong_exact += 1
                    status = f"WRONG (pred: {pred_type} vs exp: {expected_type})"


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

    # Population-calibrated denominators
    resolvable_cases = sum(1 for cs in call_sites if not cs.get("is_abstention", False))
    abstention_cases = sum(1 for cs in call_sites if cs.get("is_abstention", False))

    correct_compatible = correct_graph_compatible + correct_adjudicated_compatible
    resolvable_resolved = sum(1 for r in eval_records if not r.get("is_abstention", False) and (r["status"].startswith("CORRECT_") or r["status"].startswith("WRONG")))
    total_non_abstaining_preds = correct_exact + correct_compatible + wrong_exact + wrong_compatible

    coverage = min(1.0, max(0.0, resolvable_resolved / max(1, resolvable_cases)))
    exact_precision = min(1.0, max(0.0, correct_exact / max(1, (correct_exact + wrong_exact))))
    resolved_precision = min(1.0, max(0.0, (correct_exact + correct_compatible) / max(1, total_non_abstaining_preds)))
    wrong_exact_rate = min(1.0, max(0.0, wrong_exact / max(1, total_non_abstaining_preds)))
    abstention_accuracy = min(1.0, max(0.0, correct_abstention / max(1, abstention_cases)))
    ambiguity_rate = min(1.0, max(0.0, ambiguous / max(1, resolvable_cases)))

    env.derive_run_id()
    envelope = build_provenance_envelope(env)

    # Save raw predictions
    raw_payload = {
        **envelope,
        "target_commit": env.target_repo_commit,
        "total_predictions": len(raw_predictions),
        "predictions": raw_predictions,
    }
    raw_file = env.raw_root / "type_flow" / "receiver_predictions.json"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text(json.dumps(raw_payload, indent=2), encoding="utf-8")
    print(f"Saved raw receiver predictions to {raw_file}")

    passes_gate = (
        coverage >= 0.60
        and resolved_precision >= 0.90
        and wrong_exact_rate <= 0.05
        and invalid_gt == 0
    )

    result_payload = {
        **envelope,
        "validation_status": "PASSED" if passes_gate else "FAILED",
        "target_commit": env.target_repo_commit,
        "confusion_matrix": {
            "correct_exact": correct_exact,
            "correct_graph_compatible": correct_graph_compatible,
            "correct_adjudicated_compatible": correct_adjudicated_compatible,
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
