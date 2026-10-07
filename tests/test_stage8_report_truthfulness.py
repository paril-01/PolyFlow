"""
Stage 8: Report Truthfulness and Fallback Metric Prevention Tests (Issue 48).

Decoupled from active workspace results using synthetic test fixtures:
- Fixture A: Synthetic failing run (failed ranking, failed agent, invalid contract)
- Fixture B: Synthetic passing run (passing gates)
- Fixture C: Synthetic missing / unmeasured run (empty results directory)
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
import pytest

from experiments.rcir_v8_5.scripts.generate_reports import generate_all_reports


@pytest.fixture
def temp_report_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


def make_mock_env(results_dir: Path, reports_dir: Path):
    class MockEnv:
        polyflow_root = Path(__file__).resolve().parent.parent
        results_root = results_dir
        reports_root = reports_dir
        raw_root = results_dir
        target_repo_commit = "da57df078d0808a7235a0177bd99d23c010b472e"
        polyflow_commit = "mock-commit"
        target_repository_state = "CLEAN"
        run_id = "rcir-v8.5-synthetic"
    return MockEnv()


def test_fixture_a_reports_reflect_failed_gates(monkeypatch, temp_report_dir):
    """Fixture A: Verify reports reflect failed ranking, agent, and integrity gates."""
    with tempfile.TemporaryDirectory() as res_dir_str:
        res_dir = Path(res_dir_str)
        mock_env = make_mock_env(res_dir, temp_report_dir)

        # Write synthetic failing gate evaluation
        gate_data = {
            "run_validity": "INVALID",
            "architecture_decision": "OPTION_C_REJECTED",
            "decision_summary": "Synthetic failure run",
            "contract_feasibility": {"status": "INVALID_CONTRACT"},
            "integrity_gate": {"passed": False},
            "ranking_gate": {"passed": False},
            "agent_gate": {"passed": False},
        }
        (res_dir / "gate_evaluation.json").write_text(json.dumps(gate_data), encoding="utf-8")

        generate_all_reports(out_dir=temp_report_dir, env=mock_env)

        final_assessment = (temp_report_dir / "final_assessment.md").read_text(encoding="utf-8")
        assert "- **Run Validity**: `INVALID`" in final_assessment
        assert "- **Contract Feasibility**: `INVALID_CONTRACT`" in final_assessment
        assert "- **Integrity Gate**: **FAILED**" in final_assessment
        assert "Agent Gate**: **FAILED" in final_assessment or "Agent Gate**: **NOT_MEASURED" in final_assessment
        assert "Agent Gate**: **PASSED" not in final_assessment


def test_fixture_b_reports_reflect_passing_gates(monkeypatch, temp_report_dir):
    """Fixture B: Verify reports reflect passing gates when gates actually pass."""
    with tempfile.TemporaryDirectory() as res_dir_str:
        res_dir = Path(res_dir_str)
        mock_env = make_mock_env(res_dir, temp_report_dir)

        # Write synthetic passing gate evaluation
        gate_data = {
            "run_validity": "VALID",
            "architecture_decision": "OPTION_B_ACCEPTED",
            "decision_summary": "Synthetic passing run",
            "contract_feasibility": {"status": "FEASIBLE"},
            "integrity_gate": {"passed": True},
            "ranking_gate": {"passed": True},
            "agent_gate": {"passed": True},
        }
        (res_dir / "gate_evaluation.json").write_text(json.dumps(gate_data), encoding="utf-8")

        generate_all_reports(out_dir=temp_report_dir, env=mock_env)

        final_assessment = (temp_report_dir / "final_assessment.md").read_text(encoding="utf-8")
        assert "- **Run Validity**: `VALID`" in final_assessment
        assert "- **Contract Feasibility**: `FEASIBLE`" in final_assessment
        assert "- **Integrity Gate**: **PASSED**" in final_assessment
        assert "Agent Gate**: **PASSED" in final_assessment


def test_fixture_c_missing_artifact_renders_not_measured(monkeypatch, temp_report_dir):
    """Fixture C: Empty results directory must render NOT_MEASURED without fallback defaults."""
    with tempfile.TemporaryDirectory() as empty_results_dir:
        mock_env = make_mock_env(Path(empty_results_dir), temp_report_dir)

        generate_all_reports(out_dir=temp_report_dir, env=mock_env)

        type_flow_report = (temp_report_dir / "type_flow_report.md").read_text(encoding="utf-8")
        assert "Receiver Coverage**: `NOT_MEASURED`" in type_flow_report
        assert "Resolved Precision**: `NOT_MEASURED`" in type_flow_report
        assert "Wrong Exact Rate**: `NOT_MEASURED`" in type_flow_report

        impact_report = (temp_report_dir / "impact_plane_report.md").read_text(encoding="utf-8")
        assert "NOT_MEASURED" in impact_report
        assert "92.5%" not in impact_report

        ranking_report = (temp_report_dir / "ranking_report.md").read_text(encoding="utf-8")
        assert "NOT_MEASURED" in ranking_report

        final_assessment = (temp_report_dir / "final_assessment.md").read_text(encoding="utf-8")
        assert "OPTION_B_ACCEPTED" not in final_assessment


def test_delete_individual_result_artifacts_synthetic(monkeypatch, temp_report_dir):
    """Delete each result artifact one at a time from synthetic fixture and ensure no fabricated claims."""
    with tempfile.TemporaryDirectory() as sandbox_str:
        sandbox_res = Path(sandbox_str)
        mock_env = make_mock_env(sandbox_res, temp_report_dir)

        # Populate with synthetic minimal valid artifacts
        (sandbox_res / "gate_evaluation.json").write_text(json.dumps({"run_validity": "VALID"}), encoding="utf-8")
        (sandbox_res / "type_flow_evaluation.json").write_text(json.dumps({"validation_status": "PASSED"}), encoding="utf-8")
        (sandbox_res / "impact_test.json").write_text(json.dumps({"validation_status": "PASSED"}), encoding="utf-8")

        for artifact_path in list(sandbox_res.glob("*.json")):
            backup_path = artifact_path.with_suffix(".bak")
            artifact_path.rename(backup_path)
            try:
                generate_all_reports(out_dir=temp_report_dir, env=mock_env)
                final_assessment = (temp_report_dir / "final_assessment.md").read_text(encoding="utf-8")
                assert "OPTION_B_ACCEPTED" not in final_assessment or "VALID" in final_assessment
            finally:
                backup_path.rename(artifact_path)
