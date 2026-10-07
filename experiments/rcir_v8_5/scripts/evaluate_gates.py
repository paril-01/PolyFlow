#!/usr/bin/env python3
"""
RCIR v8.5.1 — Formal Gate, Contract, and Provenance Evaluator.

Strictly enforces benchmark_contract.json as an executable specification:
- Benchmark Integrity & Cryptographic Provenance Binding.
- Clean working tree verification (fails closed on dirty release benchmarks).
- Real canonical graph integrity evaluation (no bogus boolean flags).
- Contract Feasibility & Theoretical Ceiling Validation (P0).
- Option B Machine-Readable Contract Enforcement (P0).
- Exact Coding Agent Trial Evidence Verification (P1).
- Truthful Architecture Decision (Option A, Option B, Option C, INVALID_CONTRACT, NOT_EVALUATED).
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project roots
SCRIPT_DIR = Path(__file__).resolve().parent
RCIR_V8_5_ROOT = SCRIPT_DIR.parent
POLYFLOW_ROOT = RCIR_V8_5_ROOT.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from contract_feasibility import validate_contract_feasibility
from environment import get_default_environment
from provenance import (
    REQUIRED_PROVENANCE_FIELDS,
    build_provenance_envelope,
    collect_input_hashes,
    compute_run_identity,
    hash_file,
    validate_artifact_provenance,
)


def evaluate_gates(allow_development_dirty: bool = False, env: Optional[Any] = None) -> Dict[str, Any]:
    print("=" * 80)
    print("RCIR v8.5.2 — Formal Contract Gate Evaluation")
    print("=" * 80)

    if env is None:
        env = get_default_environment()

    contract_path = env.contract_path
    if not contract_path.exists():
        raise FileNotFoundError(f"Contract file missing: {contract_path}")

    with open(contract_path, "r", encoding="utf-8") as f:
        contract = json.load(f)

    # -------------------------------------------------------------------------
    # STAGE 1: INTEGRITY GATE (Evaluated FIRST)
    # -------------------------------------------------------------------------
    print("\n[STAGE 1] Evaluating Benchmark Integrity Gate...")
    integrity_failures = []

    # 1. Derive expected run identity from current inputs BEFORE validating manifest (Issues 4 & 5)
    env.derive_run_id()
    current_inputs = collect_input_hashes(env)
    expected_run_id = compute_run_identity(current_inputs)

    # 2. Manifest existence, content validation, and hash
    manifest_path = env.manifests_root / "benchmark_run_manifest.json"
    manifest_hash = ""
    if not manifest_path.exists():
        integrity_failures.append("benchmark_run_manifest.json does not exist")
    else:
        manifest_hash = hash_file(manifest_path)
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            # Validate manifest run_id
            if manifest.get("run_id") != expected_run_id:
                integrity_failures.append(f"Manifest run_id mismatch: {manifest.get('run_id')} != {expected_run_id}")

            # Issue 5: Validate all manifest fields against independently recomputed inputs
            if manifest.get("polyflow_commit") != current_inputs["polyflow_commit"]:
                integrity_failures.append(
                    f"Manifest polyflow_commit mismatch: {manifest.get('polyflow_commit')} != {current_inputs['polyflow_commit']}"
                )
            if manifest.get("target_repository_commit") != current_inputs["target_repo_commit"]:
                integrity_failures.append(
                    f"Manifest target_repository_commit mismatch: {manifest.get('target_repository_commit')} != {current_inputs['target_repo_commit']}"
                )
            if manifest.get("contract_hash") != current_inputs["contract_hash"]:
                integrity_failures.append(
                    f"Manifest contract_hash mismatch: {manifest.get('contract_hash')} != {current_inputs['contract_hash']}"
                )
            if manifest.get("graph_hash") != current_inputs["graph_hash"]:
                integrity_failures.append(
                    f"Manifest graph_hash mismatch: {manifest.get('graph_hash')} != {current_inputs['graph_hash']}"
                )

            # Validate dataset hashes
            m_datasets = manifest.get("dataset_hashes", {})
            for d_name, d_hash in current_inputs["dataset_hashes"].items():
                if m_datasets.get(d_name) != d_hash:
                    integrity_failures.append(
                        f"Manifest dataset hash mismatch for '{d_name}': {m_datasets.get(d_name)} != {d_hash}"
                    )

            # Validate ground truth hashes
            m_gt = manifest.get("ground_truth_hashes", {})
            for gt_name, gt_hash in current_inputs["ground_truth_hashes"].items():
                if m_gt.get(gt_name) != gt_hash:
                    integrity_failures.append(
                        f"Manifest ground truth hash mismatch for '{gt_name}': {m_gt.get(gt_name)} != {gt_hash}"
                    )

            # Validate config hashes key-by-key
            m_cfg = manifest.get("config_hashes", {})
            for cfg_name, cfg_hash in current_inputs["config_hashes"].items():
                if m_cfg.get(cfg_name) != cfg_hash:
                    integrity_failures.append(
                        f"Manifest config hash mismatch for '{cfg_name}': {m_cfg.get(cfg_name)} != {cfg_hash}"
                    )

        except Exception as e:
            integrity_failures.append(f"Manifest corrupted: {e}")

    # Build expected current run envelope
    expected_envelope = build_provenance_envelope(env, manifest_hash=manifest_hash)


    # 2. Strict provenance validation across all result artifacts
    artifacts_to_check = [
        "ground_truth_provenance.json",
        "canonical_graph_integrity.json",
        "canonicalization_evaluation.json",
        "edge_evaluation.json",
        "type_flow_evaluation.json",
        "impact_test.json",
        "ranker_test.json",
        "context_test.json",
        "determinism_evaluation.json",
    ]

    for fname in artifacts_to_check:
        fpath = env.results_root / fname
        if not fpath.exists():
            integrity_failures.append(f"Required artifact missing: {fname}")
        else:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                art_run_id = data.get("run_id")
                if art_run_id != env.run_id:
                    integrity_failures.append(f"Artifact {fname} run_id mismatch: {art_run_id} != {env.run_id}")
                # Check provenance envelope if artifact has been generated in v8.5.1 format
                if "manifest_hash" in data or "polyflow_commit" in data:
                    is_valid_prov, prov_errs = validate_artifact_provenance(
                        data, expected_envelope, allow_development_dirty=allow_development_dirty
                    )
                    if not is_valid_prov:
                        integrity_failures.extend([f"Artifact {fname}: {err}" for err in prov_errs])
            except Exception as e:
                integrity_failures.append(f"Artifact {fname} corrupted: {e}")

    # 3. Ground truth provenance verification
    gt_prov_path = env.results_root / "ground_truth_provenance.json"
    provenance_passed = False
    if gt_prov_path.exists():
        try:
            with open(gt_prov_path, "r", encoding="utf-8") as f:
                prov_data = json.load(f)
            prov_status = prov_data.get("provenance_status") or prov_data.get("validation_status")
            err_count = prov_data.get("total_errors", 0)
            provenance_passed = (prov_status == "PASSED") and (err_count == 0)
            if not provenance_passed:
                integrity_failures.append(f"Ground truth provenance failed: status={prov_status}, errors={err_count}")
        except Exception as e:
            integrity_failures.append(f"Could not load ground truth provenance: {e}")

    # 4. Strict token budget invariant
    ctx_test_path = env.results_root / "context_test.json"
    token_budget_invariant_passed = False
    if ctx_test_path.exists():
        try:
            with open(ctx_test_path, "r", encoding="utf-8") as f:
                ctx_data = json.load(f)
            violations = ctx_data.get("token_budget_violations", 0)
            token_budget_invariant_passed = (violations == 0)
            if violations > 0:
                integrity_failures.append(f"Context budget violations detected: {violations}")
        except Exception as e:
            integrity_failures.append(f"Could not load context test artifact: {e}")

    # 5. Graph integrity verification (Actual evaluation, no bogus boolean flag)
    cg_integ_path = env.results_root / "canonical_graph_integrity.json"
    unexpected_external_ratio_zero = False
    if cg_integ_path.exists():
        try:
            with open(cg_integ_path, "r", encoding="utf-8") as f:
                cg_data = json.load(f)
            observed_ratio = cg_data.get("unexpected_external_internal_ratio", 1.0)
            max_ratio = contract.get("canonical_graph", {}).get("max_external_ratio", 0.0)
            unexpected_external_ratio_zero = observed_ratio <= max_ratio
            if not unexpected_external_ratio_zero:
                integrity_failures.append(
                    f"Canonical graph unexpected_external_internal_ratio ({observed_ratio}) exceeds maximum allowed ({max_ratio})"
                )
        except Exception as e:
            integrity_failures.append(f"Could not load canonical graph integrity artifact: {e}")

    # 6. Clean source state verification (formal release benchmark requires clean tree)
    if env.polyflow_dirty and not allow_development_dirty:
        integrity_failures.append("PolyFlow working tree was dirty during execution (formal release benchmark requires clean tree)")

    manifest_valid = manifest_path.exists() and not any("manifest" in f.lower() for f in integrity_failures)
    run_id_consistent = not any("run_id mismatch" in f.lower() for f in integrity_failures)
    integrity_passed = len(integrity_failures) == 0

    print(f"Integrity Gate Verdict: {'PASSED' if integrity_passed else 'FAILED'}")

    integrity_result = {
        **expected_envelope,
        "status": "PASSED" if integrity_passed else "FAILED",
        "manifest_valid": manifest_valid,
        "run_id_consistent": run_id_consistent,
        "provenance_passed": provenance_passed,
        "token_budget_invariant_passed": token_budget_invariant_passed,
        "unexpected_external_ratio_zero": unexpected_external_ratio_zero,
        "failures": integrity_failures,
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(env.results_root / "integrity_evaluation.json", "w", encoding="utf-8") as f:
        json.dump(integrity_result, f, indent=2)

    integrity_gate = {
        "passed": integrity_passed,
        "failures": integrity_failures,
    }

    # -------------------------------------------------------------------------
    # STAGE 2: CONTRACT FEASIBILITY VALIDATION (P0)
    # -------------------------------------------------------------------------
    print("\n[STAGE 2] Validating Contract Feasibility against Sparse Ground Truth Labels...")
    gt_file = env.ground_truth_root / "ground_truth.json"
    gt_tasks = {}
    if gt_file.exists():
        gt_data = json.loads(gt_file.read_text(encoding="utf-8"))
        gt_tasks = gt_data.get("tasks", {})

    test_gt_tasks = [t for t in gt_tasks.values() if t.get("split") == "test"]
    is_contract_feasible, feasibility_details = validate_contract_feasibility(contract, test_gt_tasks)

    if not is_contract_feasible:
        print(f"  [CONTRACT INFEASIBILITY DETECTED] Violations: {feasibility_details['violations']}")

    # -------------------------------------------------------------------------
    # STAGE 3: PRIMARY ARCHITECTURE CONTRACT GATES
    # -------------------------------------------------------------------------
    print("\n[STAGE 3] Evaluating Contract Gates against TEST split...")

    def load_json_safe(fpath: Path) -> Dict[str, Any]:
        if not fpath.exists():
            return {}
        try:
            with open(fpath, "r", encoding="utf-8") as jf:
                return json.load(jf)
        except Exception:
            return {}

    impact_test = load_json_safe(env.results_root / "impact_test.json")
    ranker_test = load_json_safe(env.results_root / "ranker_test.json")
    context_test = load_json_safe(env.results_root / "context_test.json")
    type_flow_res = load_json_safe(env.results_root / "type_flow_evaluation.json")
    canon_res = load_json_safe(env.results_root / "canonicalization_evaluation.json")
    det_res = load_json_safe(env.results_root / "determinism_evaluation.json")

    # 1. Impact Plane Gate
    cfg_impact = contract["impact_plane"]
    macro_recall = impact_test.get("macro_pool_recall", 0.0)
    worst_recall = impact_test.get("worst_task_pool_recall", 0.0)
    silent_misses = impact_test.get("silent_misses", 999)

    impact_gate = {
        "macro_recall": macro_recall,
        "macro_recall_threshold": cfg_impact["macro_pool_recall_min"],
        "macro_passed": macro_recall >= cfg_impact["macro_pool_recall_min"],
        "worst_task_recall": worst_recall,
        "worst_task_floor": cfg_impact["worst_task_pool_recall_floor"],
        "worst_task_passed": worst_recall >= cfg_impact["worst_task_pool_recall_floor"],
        "silent_misses": silent_misses,
        "max_silent_misses": cfg_impact["max_silent_misses"],
        "silent_misses_passed": silent_misses <= cfg_impact["max_silent_misses"],
    }
    impact_gate["passed"] = (
        impact_gate["macro_passed"]
        and impact_gate["worst_task_passed"]
        and impact_gate["silent_misses_passed"]
    )
    print(f"  Impact Gate: {'PASSED' if impact_gate['passed'] else 'FAILED'} (Macro: {macro_recall*100:.1f}%, Worst: {worst_recall*100:.1f}%, Silent Misses: {silent_misses})")

    # 2. Ranking Plane Gate (v8.5.2)
    cfg_rank = contract["ranking_plane"]
    rank_metrics = ranker_test.get("metrics", ranker_test)
    p20_excl = rank_metrics.get("precision_at_20_excluding_target", 0.0)
    p50_excl = rank_metrics.get("precision_at_50_excluding_target", 0.0)
    ndcg_50 = rank_metrics.get("graded_ndcg_at_50", 0.0)
    dep_mrr = rank_metrics.get("dependency_mrr", 0.0)

    blocking_cfg = cfg_rank.get("blocking_metrics", {})
    if blocking_cfg:
        ndcg_min = blocking_cfg.get("ndcg_at_50_graded_min", 0.20)
        dep_mrr_min = blocking_cfg.get("dependency_mrr_min", 0.20)
        ndcg_passed = ndcg_50 >= ndcg_min
        dep_mrr_passed = dep_mrr >= dep_mrr_min
        p20_passed = True
        p50_passed = True
        ranking_passed = ndcg_passed and dep_mrr_passed
    else:
        # Legacy contract v8.5
        p20_min = cfg_rank.get("precision_at_20_excluding_target_min", 0.35)
        p50_min = cfg_rank.get("precision_at_50_excluding_target_min", 0.20)
        ndcg_min = cfg_rank.get("ndcg_at_50_graded_min", 0.50)
        dep_mrr_min = cfg_rank.get("dependency_mrr_min", 0.70)
        p20_passed = p20_excl >= p20_min
        p50_passed = p50_excl >= p50_min
        ndcg_passed = ndcg_50 >= ndcg_min
        dep_mrr_passed = dep_mrr >= dep_mrr_min
        ranking_passed = p20_passed and p50_passed and ndcg_passed and dep_mrr_passed

    ranking_gate = {
        "p20_excluding_target": p20_excl,
        "p20_passed": p20_passed,
        "p50_excluding_target": p50_excl,
        "p50_passed": p50_passed,
        "ndcg_at_50": ndcg_50,
        "ndcg_min": ndcg_min,
        "ndcg_passed": ndcg_passed,
        "dependency_mrr": dep_mrr,
        "dependency_mrr_min": dep_mrr_min,
        "dependency_mrr_passed": dep_mrr_passed,
        "contract_feasible": is_contract_feasible,
        "theoretical_ceilings": feasibility_details.get("theoretical_ceilings", {}),
        "passed": ranking_passed and is_contract_feasible,
    }
    print(f"  Ranking Gate: {'PASSED' if ranking_gate['passed'] else 'FAILED'} (P@20_excl: {p20_excl*100:.1f}%, P@50_excl: {p50_excl*100:.1f}%, nDCG@50: {ndcg_50:.4f}, MRR: {dep_mrr:.4f})")


    # 3. Context Plane Gate
    cfg_ctx = contract["context_plane"]
    crit_src_recall = context_test.get("critical_source_recall_at_4k") or context_test.get("critical_source_recall_at_budget", 0.0)
    violations = context_test.get("token_budget_violations", 0)
    is_det = det_res.get("is_deterministic", False)

    context_gate = {
        "critical_source_recall_at_4k": crit_src_recall,
        "critical_source_recall_min": cfg_ctx["critical_source_recall_at_4k_min"],
        "source_recall_passed": crit_src_recall >= cfg_ctx["critical_source_recall_at_4k_min"],
        "budget_violations": violations,
        "budget_invariant_passed": violations == 0,
        "is_deterministic": is_det,
        "determinism_passed": is_det is True,
    }
    context_gate["passed"] = (
        context_gate["source_recall_passed"]
        and context_gate["budget_invariant_passed"]
        and context_gate["determinism_passed"]
    )
    print(f"  Context Gate: {'PASSED' if context_gate['passed'] else 'FAILED'} (CriticalSourceRecall@4k: {crit_src_recall*100:.1f}%, BudgetViolations: {violations}, Determinism: {is_det})")

    # 4. Type Flow Gate
    cfg_tf = contract["type_flow"]
    tf_metrics = type_flow_res.get("metrics", {})
    tf_cov = tf_metrics.get("coverage", 0.0)
    tf_prec = tf_metrics.get("resolved_precision", 0.0)
    tf_wrong = tf_metrics.get("wrong_exact_rate", 1.0)
    tf_invalid_gt = type_flow_res.get("confusion_matrix", {}).get("invalid_gt", 0)

    type_flow_gate = {
        "coverage": tf_cov,
        "coverage_min": cfg_tf["coverage_min"],
        "coverage_passed": tf_cov >= cfg_tf["coverage_min"],
        "resolved_precision": tf_prec,
        "resolved_precision_min": cfg_tf["resolved_precision_min"],
        "precision_passed": tf_prec >= cfg_tf["resolved_precision_min"],
        "wrong_exact_rate": tf_wrong,
        "wrong_exact_max": cfg_tf["wrong_exact_rate_max"],
        "wrong_exact_passed": tf_wrong <= cfg_tf["wrong_exact_rate_max"],
        "invalid_gt_count": tf_invalid_gt,
        "ground_truth_valid": tf_invalid_gt == 0,
    }
    type_flow_gate["passed"] = (
        type_flow_gate["coverage_passed"]
        and type_flow_gate["precision_passed"]
        and type_flow_gate["wrong_exact_passed"]
        and type_flow_gate["ground_truth_valid"]
    )
    print(f"  Type Flow Gate: {'PASSED' if type_flow_gate['passed'] else 'FAILED'} (Coverage: {tf_cov*100:.1f}%, Precision: {tf_prec*100:.1f}%, WrongExact: {tf_wrong*100:.1f}%, InvalidGT: {tf_invalid_gt})")

    # 5. Canonicalization Gate
    cfg_canon = contract["canonicalization"]
    wrong_canon_rate = canon_res.get("wrong_resolution_rate", 1.0)
    canon_gate = {
        "wrong_canonical_rate": wrong_canon_rate,
        "wrong_canonical_max": cfg_canon["wrong_canonical_resolution_max"],
        "passed": wrong_canon_rate <= cfg_canon["wrong_canonical_resolution_max"],
    }
    print(f"  Canonicalization Gate: {'PASSED' if canon_gate['passed'] else 'FAILED'} (Wrong Rate: {wrong_canon_rate*100:.2f}%)")

    # 6. Edge Evaluation Gate (Advisory)
    edge_gate = {
        "status": "ADVISORY_ONLY",
        "rationale": "Edge precision methodology requires complete prediction adjudication before promoting to formal gate (PHASE 85).",
    }

    # 7. Agent Gate (Exact trial evidence validation - Section 9)
    agent_ab_path = env.results_root / "agent_ab_runs.json"
    agent_live_verified = False
    agent_trials_verified = False
    agent_comp_rate = 0.0
    trials_count = 0
    agent_validation_status = "NOT_MEASURED"

    if agent_ab_path.exists():
        with open(agent_ab_path, "r", encoding="utf-8") as f:
            agent_data = json.load(f)

        agent_validation_status = agent_data.get("validation_status", "NOT_MEASURED")
        prov = agent_data.get("provider", {})
        agent_live_verified = (not prov.get("is_simulation", True)) and (agent_validation_status == "MEASURED_AGENT_VALIDATION")

        cond_a = agent_data.get("condition_a_rcir", {})
        reported_comp_rate = cond_a.get("completion_rate", 0.0)
        agent_comp_rate = reported_comp_rate if isinstance(reported_comp_rate, (int, float)) else 0.0
        trials_count = cond_a.get("trials_count", 0)

        # Exact trial verification against raw trial directories
        agent_raw_dir = env.raw_root / "agent"
        verified_total_trials = 0
        verified_successful_trials = 0

        if agent_raw_dir.exists() and agent_live_verified and trials_count > 0:
            for trial in agent_data.get("trials", []):
                t_id = trial.get("trial_id", "")
                t_cond = trial.get("condition", "")
                if not t_id or t_cond != "rcir":
                    continue

                t_dir = agent_raw_dir / t_id
                if not t_dir.exists():
                    continue

                manifest_f = t_dir / "trial_manifest.json"
                gatekeeper_f = t_dir / "gatekeeper.json"
                diff_f = t_dir / "git_diff.patch"
                before_log = t_dir / "acceptance_before.log"
                after_log = t_dir / "acceptance_after.log"
                reg_log = t_dir / "regression.log"
                tool_calls_f = t_dir / "tool_calls.jsonl"
                prov_log = t_dir / "provider_log.jsonl"

                if not (manifest_f.exists() and gatekeeper_f.exists() and diff_f.exists() and before_log.exists() and after_log.exists()):
                    continue

                try:
                    m = json.loads(manifest_f.read_text(encoding="utf-8"))
                    gk = json.loads(gatekeeper_f.read_text(encoding="utf-8"))
                    diff_text = diff_f.read_text(encoding="utf-8").strip()

                    # Verify matching trial metadata
                    m_run_id = m.get("run_id")
                    if m_run_id != env.run_id:
                        continue
                    if m.get("task_id") != trial.get("task_id"):
                        continue
                    if m.get("replicate") != trial.get("replicate"):
                        continue

                    # Verify required artifacts
                    before_text = before_log.read_text(encoding="utf-8")
                    after_text = after_log.read_text(encoding="utf-8")
                    reg_text = reg_log.read_text(encoding="utf-8") if reg_log.exists() else ""

                    has_before_failure = "ReturnCode: 1" in before_text
                    has_after_pass = "ReturnCode: 0" in after_text
                    has_reg_pass = "ReturnCode: 0" in reg_text if reg_log.exists() else True
                    has_diff = len(diff_text) > 0
                    gk_approved = gk.get("verdict") == "APPROVE"

                    verified_total_trials += 1
                    if m.get("success") and has_before_failure and has_after_pass and has_reg_pass and has_diff and gk_approved:
                        verified_successful_trials += 1
                except Exception:
                    pass

            reported_completed = cond_a.get("completed_count", 0)
            agent_trials_verified = (
                (verified_total_trials == trials_count)
                and (verified_successful_trials == reported_completed)
                and (verified_total_trials > 0)
            )

    agent_gate = {
        "status": agent_validation_status,
        "live_inference_verified": agent_live_verified,
        "trials_evidence_verified": agent_trials_verified,
        "simulation_forbidden": True,
        "rcir_completion_rate": agent_comp_rate,
        "trials_count": trials_count,
        "passed": agent_live_verified and agent_trials_verified and (agent_comp_rate >= 0.50),
    }
    print(f"  Agent Gate: {'PASSED' if agent_gate['passed'] else ('NOT_MEASURED' if agent_validation_status == 'NOT_MEASURED' else 'NOT_VERIFIED')}")

    # -------------------------------------------------------------------------
    # STAGE 4: FORMAL ARCHITECTURE DECISION (Option A vs Option B vs Option C vs INVALID_CONTRACT)
    # -------------------------------------------------------------------------
    # Option A: All primary gates satisfied
    option_a_satisfied = (
        impact_gate["passed"]
        and ranking_gate["passed"]
        and context_gate["passed"]
        and type_flow_gate["passed"]
        and canon_gate["passed"]
        and agent_gate["passed"]
    )

    # Option B: Machine-readable contract enforcement (Section 3)
    cfg_opt_b = contract.get("decision_rules", {}).get("option_b", {})
    macro_recall_passed = macro_recall >= cfg_opt_b.get("macro_pool_recall_min", 0.90)
    worst_recall_passed = worst_recall >= cfg_opt_b.get("worst_task_pool_recall_floor", 0.80)
    det_passed = (is_det is True) if cfg_opt_b.get("requires_determinism", True) else True
    tf_passed = type_flow_gate["passed"] if cfg_opt_b.get("requires_type_flow_gate", True) else True
    canon_passed = canon_gate["passed"] if cfg_opt_b.get("requires_canonicalization_gate", True) else True
    budget_passed = context_gate["budget_invariant_passed"] if cfg_opt_b.get("requires_budget_invariant", True) else True

    # Option B Ranking Improvement Check
    rank_imp_cfg = cfg_opt_b.get("ranking_improvement")
    ranking_imp_evaluable = True
    ranking_imp_passed = True
    ranking_imp_details = "No ranking improvement required by contract."

    if rank_imp_cfg:
        metric_name = rank_imp_cfg.get("metric", "precision_at_50_excluding_target")
        baseline_rel = rank_imp_cfg.get("baseline_artifact")
        min_rel_imp = rank_imp_cfg.get("min_relative_improvement", 0.15)

        baseline_path = (env.polyflow_root / baseline_rel) if baseline_rel else None
        if not baseline_path or not baseline_path.exists():
            ranking_imp_evaluable = False
            ranking_imp_passed = False
            ranking_imp_details = f"Baseline artifact missing or undefined: {baseline_rel}. Cannot evaluate Option B."
        else:
            try:
                with open(baseline_path, "r", encoding="utf-8") as bf:
                    b_data = json.load(bf)

                # Validate baseline provenance (Issue 10)
                req_prov = rank_imp_cfg.get("baseline_provenance_validation", {})
                prov_mismatches = []
                if req_prov.get("require_same_target_commit") and b_data.get("target_repo_commit") != env.target_repo_commit:
                    prov_mismatches.append(f"target_repo_commit ({b_data.get('target_repo_commit')} != {env.target_repo_commit})")
                if req_prov.get("require_same_ground_truth_hash") and b_data.get("ground_truth_hash") != expected_envelope.get("ground_truth_hash"):
                    prov_mismatches.append("ground_truth_hash mismatch")

                if prov_mismatches:
                    ranking_imp_evaluable = False
                    ranking_imp_passed = False
                    ranking_imp_details = f"OPTION_B = NOT_EVALUABLE: Baseline provenance mismatch: {', '.join(prov_mismatches)}"
                else:
                    b_metrics = b_data.get("metrics", b_data)
                    b_val = b_metrics.get(metric_name, 0.0)
                    curr_val = rank_metrics.get(metric_name, 0.0)

                    if b_val == 0.0:
                        # Issue 10: Zero baseline rule
                        abs_delta = curr_val - b_val
                        min_abs_delta = rank_imp_cfg.get("min_absolute_delta", 0.02)
                        ranking_imp_passed = abs_delta >= min_abs_delta
                        ranking_imp_details = (
                            f"Zero baseline encountered. Absolute delta: {abs_delta:.4f} "
                            f"(required >= {min_abs_delta:.4f})"
                        )
                    else:
                        rel_imp = (curr_val - b_val) / float(b_val)
                        ranking_imp_passed = rel_imp >= min_rel_imp
                        ranking_imp_details = (
                            f"Current {metric_name} = {curr_val:.4f} vs Baseline = {b_val:.4f} "
                            f"=> Relative improvement = {rel_imp*100:.2f}% (required >= {min_rel_imp*100:.1f}%)"
                        )
            except Exception as ex:
                ranking_imp_evaluable = False
                ranking_imp_passed = False
                ranking_imp_details = f"Error reading baseline artifact {baseline_path}: {ex}"


    option_b_evaluation = {
        "evaluable": ranking_imp_evaluable,
        "passed": (
            macro_recall_passed
            and worst_recall_passed
            and det_passed
            and tf_passed
            and canon_passed
            and budget_passed
            and ranking_imp_passed
        ),
        "requirements": {
            "macro_recall": {
                "passed": macro_recall_passed,
                "observed": macro_recall,
                "threshold": cfg_opt_b.get("macro_pool_recall_min", 0.90),
            },
            "worst_task_recall": {
                "passed": worst_recall_passed,
                "observed": worst_recall,
                "threshold": cfg_opt_b.get("worst_task_pool_recall_floor", 0.80),
            },
            "determinism": {"passed": det_passed, "observed": is_det},
            "type_flow": {"passed": tf_passed, "gate_verdict": type_flow_gate["passed"]},
            "canonicalization": {"passed": canon_passed, "observed": wrong_canon_rate},
            "budget_invariant": {"passed": budget_passed, "violations": violations},
            "ranking_improvement": {
                "evaluable": ranking_imp_evaluable,
                "passed": ranking_imp_passed,
                "details": ranking_imp_details,
            },
        },
    }

    # Final Architecture Decision Selection
    if not integrity_passed:
        formal_decision = "NOT_EVALUATED"
        decision_summary = (
            f"Benchmark integrity gate failed with {len(integrity_failures)} violation(s). "
            f"Run is invalid."
        )
        run_validity = "INVALID"
    elif not is_contract_feasible:
        formal_decision = "INVALID_CONTRACT"
        decision_summary = (
            f"Contract ranking thresholds ({', '.join(feasibility_details['violations'])}) "
            f"exceed theoretical maximum possible ceilings for sparse Nextcloud TEST ground truth labels. "
            f"Architectural acceptance refused."
        )
        run_validity = "INVALID"
    elif option_a_satisfied:
        formal_decision = "OPTION_A_ACCEPTED"
        decision_summary = "All primary impact, context, type-flow, ranking, and live agent validation gates fully passed."
        run_validity = "VALID"
    elif option_b_evaluation["passed"]:
        formal_decision = "OPTION_B_ACCEPTED"
        decision_summary = (
            f"Option B accepted: Substantial architectural progress demonstrated on real Nextcloud Server TEST split "
            f"(Macro Recall {macro_recall*100:.1f}%, Worst Task {worst_recall*100:.1f}%, Determinism: {is_det}, "
            f"Type Flow {tf_cov*100:.1f}% cov / {tf_prec*100:.1f}% prec, 0 budget violations, {ranking_imp_details})."
        )
        run_validity = "VALID"
    elif not option_b_evaluation["evaluable"]:
        formal_decision = "OPTION_C_REJECTED"
        decision_summary = f"Option B cannot be evaluated: {ranking_imp_details}. Formal benchmark thresholds not met; architectural retreat required."
        run_validity = "VALID"
    else:
        formal_decision = "OPTION_C_REJECTED"
        decision_summary = "Formal benchmark thresholds not met; architectural retreat required."
        run_validity = "VALID"

    print(f"\n================================================================================")
    print(f"Formal Architecture Decision: {formal_decision}")
    print(f"Summary: {decision_summary}")
    print(f"================================================================================")

    gate_result = {
        **expected_envelope,
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_validity": run_validity,
        "architecture_decision": formal_decision,
        "decision_summary": decision_summary,
        "contract_version": contract.get("contract_version", "8.5"),
        "contract_feasibility": feasibility_details,
        "integrity_gate": integrity_gate,
        "impact_gate": impact_gate,
        "ranking_gate": ranking_gate,
        "context_gate": context_gate,
        "type_flow_gate": type_flow_gate,
        "canonicalization_gate": canon_gate,
        "edge_gate": edge_gate,
        "agent_gate": agent_gate,
        "option_b_evaluation": option_b_evaluation,
    }

    out_file = env.results_root / "gate_evaluation.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(gate_result, f, indent=2)

    print(f"Saved formal gate evaluation to: {out_file}")
    return gate_result


if __name__ == "__main__":
    allow_dirty = "--allow-dirty" in sys.argv
    res = evaluate_gates(allow_development_dirty=allow_dirty)
    if not res or res.get("run_validity") != "VALID" or res.get("architecture_decision") in ("NOT_EVALUATED", "INVALID_CONTRACT"):
        sys.exit(1)

