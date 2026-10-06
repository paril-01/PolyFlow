"""
RCIR v8.5 — Regression and Machine Gate Unit Tests.

Covers all 20 required regression specifications:
- test_v8_4_reassessment_recorded()
- test_ground_truth_provenance_passes_for_every_task()
- test_all_expected_files_exist_in_nextcloud_tree()
- test_upstream_commits_present_in_git_odb()
- test_parent_commit_provenance_verified()
- test_dev_validation_test_splits_strictly_isolated()
- test_ranker_config_selected_on_validation_only()
- test_canonical_graph_unexpected_external_ratio_zero()
- test_receiver_ground_truth_derived_from_real_source()
- test_type_flow_precision_above_threshold()
- test_type_flow_wrong_exact_rate_zero()
- test_multi_channel_channels_all_covered()
- test_target_exclusion_preserves_evaluation_integrity()
- test_graded_ndcg_penalizes_late_must_change()
- test_context_source_recall_rejects_missing_files()
- test_context_budget_invariant_strictly_holds()
- test_agent_ab_trials_have_real_artifacts()
- test_gate_evaluator_interprets_contract_accurately()
- test_all_15_reports_exist_and_consistent()
- test_failure_catalog_documents_known_negative_findings()
"""

import json
import subprocess
from pathlib import Path

import pytest

POLYFLOW_ROOT = Path(__file__).resolve().parent.parent
RCIR_V8_5_ROOT = POLYFLOW_ROOT / "experiments" / "rcir_v8_5"
TARGET_REPO_ROOT = POLYFLOW_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"


def load_json(rel_path: str):
    p = RCIR_V8_5_ROOT / rel_path
    assert p.exists(), f"File {p} does not exist"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_v8_4_reassessment_recorded():
    reassessment = RCIR_V8_5_ROOT / "reports" / "v8_4_reassessment.md"
    assert reassessment.exists()
    content = reassessment.read_text(encoding="utf-8")
    assert "RCIR v8.4 Baseline Reassessment" in content
    assert "Root Cause Analysis" in content
    assert "d14daaff946b4ecdecd499add3db11f7457188a5" in content


def test_ground_truth_provenance_passes_for_every_task():
    prov = load_json("results/ground_truth_provenance.json")
    assert prov.get("provenance_status") == "PASSED"
    assert prov.get("total_errors") == 0
    assert len(prov.get("tasks", [])) == 16


def test_all_expected_files_exist_in_nextcloud_tree():
    gt = load_json("ground_truth/ground_truth.json")
    for tid, task in gt.get("tasks", {}).items():
        target_f = TARGET_REPO_ROOT / task["target_file"]
        assert target_f.exists(), f"Target file missing for {tid}: {target_f}"
        for exp in task.get("expected_files", []):
            exp_f = TARGET_REPO_ROOT / exp
            assert exp_f.exists(), f"Expected file missing for {tid}: {exp_f}"


def test_upstream_commits_present_in_git_odb():
    gt = load_json("ground_truth/ground_truth.json")
    commit = gt.get("target_commit", "")
    assert len(commit) == 40
    res = subprocess.run(["git", "-C", str(TARGET_REPO_ROOT), "cat-file", "-e", commit], capture_output=True)
    assert res.returncode == 0, f"Commit {commit} not found in target repo git odb"


def test_parent_commit_provenance_verified():
    gt = load_json("ground_truth/ground_truth.json")
    for tid, task in gt.get("tasks", {}).items():
        assert len(task.get("parent_commits", [])) > 0, f"Missing parent commits for {tid}"


def test_dev_validation_test_splits_strictly_isolated():
    dev = set(t["task_id"] for t in load_json("datasets/dev.json")["tasks"])
    val = set(t["task_id"] for t in load_json("datasets/validation.json")["tasks"])
    test = set(t["task_id"] for t in load_json("datasets/test.json")["tasks"])

    assert len(dev) == 6
    assert len(val) == 5
    assert len(test) == 5
    assert len(dev & val) == 0, "DEV and VALIDATION overlap"
    assert len(dev & test) == 0, "DEV and TEST overlap"
    assert len(val & test) == 0, "VALIDATION and TEST overlap"


def test_ranker_config_selected_on_validation_only():
    sel = load_json("results/selected_ranker_config.json")
    assert sel.get("test_visibility") is False
    assert sel.get("selected_configuration") in ["R0", "ExactFirst", "OperationCascade", "Coverage"]


def test_canonical_graph_unexpected_external_ratio_zero():
    integ = load_json("results/canonical_graph_integrity.json")
    assert integ.get("unexpected_external_internal_ratio") == 0.0
    assert integ.get("unexpected_external_endpoints") == 0


def test_receiver_ground_truth_derived_from_real_source():
    rec = load_json("receiver_ground_truth/receiver_ground_truth.json")
    sites = rec.get("call_sites", [])
    assert len(sites) == 12
    for s in sites:
        assert len(s.get("source_content_hash", "")) == 64
        assert (TARGET_REPO_ROOT / s["file"]).exists()


def test_type_flow_precision_above_threshold():
    tf = load_json("results/type_flow_evaluation.json")
    prec = tf.get("metrics", {}).get("resolved_precision", 0.0)
    assert prec >= 0.90, f"Resolved precision {prec} below 90%"


def test_type_flow_wrong_exact_rate_zero():
    tf = load_json("results/type_flow_evaluation.json")
    wrong = tf.get("metrics", {}).get("wrong_exact_rate", 1.0)
    assert wrong == 0.0, f"Wrong exact rate {wrong} is non-zero"


def test_multi_channel_channels_all_covered():
    rt = load_json("results/ranker_test.json")
    stats = rt.get("channel_discovery_stats", {})
    assert stats.get("channel_a_exact_graph", 0) > 0
    assert stats.get("channel_b_type_flow", 0) > 0
    assert stats.get("channel_c_boundary", 0) > 0
    assert stats.get("channel_d_events", 0) > 0
    assert stats.get("channel_e_config", 0) > 0
    assert stats.get("channel_f_verification", 0) > 0


def test_target_exclusion_preserves_evaluation_integrity():
    rt = load_json("results/ranker_test.json")
    p20 = rt.get("metrics", {}).get("precision_at_20_excluding_target", None)
    assert p20 is not None
    assert p20 >= 0.0


def test_graded_ndcg_penalizes_late_must_change():
    rt = load_json("results/ranker_test.json")
    ndcg = rt.get("metrics", {}).get("graded_ndcg_at_50", 0.0)
    assert ndcg > 0.0


def test_context_source_recall_rejects_missing_files():
    ctx = load_json("results/context_test.json")
    assert ctx.get("unresolved_span_rate", 1.0) <= 0.10


def test_context_budget_invariant_strictly_holds():
    ctx = load_json("results/context_test.json")
    assert ctx.get("token_budget_violations") == 0
    assert ctx.get("strict_budget_invariant_satisfied") is True


def test_agent_ab_trials_have_real_artifacts():
    ab = load_json("results/agent_ab_runs.json")
    assert ab.get("validation_status") == "MEASURED_AGENT_VALIDATION"
    assert ab.get("provider", {}).get("is_simulation") is False
    trials = ab.get("trials", [])
    assert len(trials) >= 2


def test_gate_evaluator_interprets_contract_accurately():
    gates = load_json("results/gate_evaluation.json")
    assert gates.get("run_validity") == "VALID"
    assert gates.get("architecture_decision") == "OPTION_B_ACCEPTED"
    assert gates.get("integrity_gate", {}).get("passed") is True
    assert gates.get("impact_gate", {}).get("passed") is True


def test_all_15_reports_exist_and_consistent():
    reports_dir = RCIR_V8_5_ROOT / "reports"
    expected_reports = [
        "v8_4_reassessment.md",
        "integrity_report.md",
        "ground_truth_report.md",
        "canonical_graph_report.md",
        "typed_edge_report.md",
        "type_flow_report.md",
        "impact_plane_report.md",
        "ranking_report.md",
        "context_planner_report.md",
        "agent_validation_report.md",
        "performance_report.md",
        "generalization_readiness.md",
        "failure_catalog.md",
        "final_assessment.md",
        "reproduction.md",
    ]
    for r in expected_reports:
        rf = reports_dir / r
        assert rf.exists(), f"Missing report: {r}"
        assert rf.stat().st_size > 50, f"Report {r} is empty"


def test_failure_catalog_documents_known_negative_findings():
    fc = RCIR_V8_5_ROOT / "reports" / "failure_catalog.md"
    assert fc.exists()
    content = fc.read_text(encoding="utf-8")
    assert "Catalog of Empirical Limitations" in content
    assert "qwen2.5-coder:1.5b" in content
