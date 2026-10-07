"""
Stage 14 Regression Tests: Report Run Consistency & Truthfulness (Issues 40-45).
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest

from experiments.rcir_v8_5.scripts.generate_reports import generate_all_reports


def test_agent_turn_budget_sub_dictionary_extraction():
    """Issue 43: agent_validation_report.md must extract turn_budgets sub-dict, not top-level keys."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_p = Path(tmp_dir)
        results_dir = tmp_p / "results"
        reports_dir = tmp_p / "reports"
        results_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)

        class MockEnv:
            results_root = results_dir
            reports_root = reports_dir
            raw_root = results_dir
            target_repo_commit = "commit-123"
            polyflow_commit = "commit-poly"
            target_repository_state = "CLEAN"
            run_id = "run-test-01"

        # Synthetic agent_turn_budget.json with nested turn_budgets and extra top-level fields
        tb_payload = {
            "run_id": "run-test-01",
            "validation_status": "MEASURED_TURN_BUDGET",
            "turn_budgets": {
                "5": {"trials_evaluated": 2, "completion_rate": 0.5},
                "8": {"trials_evaluated": 2, "completion_rate": 1.0},
            },
            "unrelated_metadata": {"foo": "bar"}
        }
        (results_dir / "agent_turn_budget.json").write_text(json.dumps(tb_payload), encoding="utf-8")
        (results_dir / "agent_ab_runs.json").write_text(json.dumps({
            "run_id": "run-test-01",
            "validation_status": "NOT_MEASURED",
            "provider": {"model": "mock-model"}
        }), encoding="utf-8")

        generate_all_reports(out_dir=reports_dir, env=MockEnv())

        agent_report = (reports_dir / "agent_validation_report.md").read_text(encoding="utf-8")
        # Must contain Budget 5 and Budget 8
        assert "Budget 5 Turns**: Evaluated: `2`" in agent_report
        assert "Budget 8 Turns**: Evaluated: `2`" in agent_report
        # Must NOT iterate over unrelated_metadata or turn_budgets as a budget key
        assert "Budget unrelated_metadata Turns" not in agent_report
        assert "Budget turn_budgets Turns" not in agent_report
        # Truthful provider status
        assert "UNAVAILABLE / NOT_MEASURED" in agent_report


def test_generalization_status_reflects_prerequisites():
    """Issue 38: evaluate_generalization marks PHP as IMPLEMENTED_VERIFIED only when prerequisites pass."""
    from experiments.rcir_v8_5.scripts import environment
    from experiments.rcir_v8_5.scripts.evaluate_generalization import evaluate_generalization
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_p = Path(tmp_dir)
        results_dir = tmp_p / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        env = environment.get_default_environment()
        env.results_root = results_dir

        # Case 1: Missing prerequisites -> IMPLEMENTED_UNVERIFIED
        from unittest.mock import patch
        with patch("experiments.rcir_v8_5.scripts.evaluate_generalization.get_default_environment", return_value=env):
            evaluate_generalization()
            gen_data = json.loads((results_dir / "generalization_readiness.json").read_text(encoding="utf-8"))
            assert gen_data["languages"]["php"]["status"] == "IMPLEMENTED_UNVERIFIED"

        # Case 2: All prerequisites present and passing -> IMPLEMENTED_VERIFIED
        (results_dir / "type_flow_evaluation.json").write_text(json.dumps({
            "validation_status": "PASSED",
            "metrics": {"coverage": 0.85, "resolved_precision": 0.95}
        }), encoding="utf-8")
        (results_dir / "canonical_graph_integrity.json").write_text(json.dumps({"validation_status": "PASSED"}), encoding="utf-8")
        (results_dir / "impact_test.json").write_text(json.dumps({"validation_status": "PASSED"}), encoding="utf-8")

        with patch("experiments.rcir_v8_5.scripts.evaluate_generalization.get_default_environment", return_value=env):
            evaluate_generalization()
            gen_data2 = json.loads((results_dir / "generalization_readiness.json").read_text(encoding="utf-8"))
            assert gen_data2["languages"]["php"]["status"] == "IMPLEMENTED_VERIFIED"
            assert gen_data2["languages"]["php"]["evidence"]["type_flow_coverage"] == "85.0%"
            assert gen_data2["languages"]["php"]["evidence"]["type_flow_precision"] == "95.0%"

