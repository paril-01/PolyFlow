"""
Stage 8: Report Truthfulness and Fallback Metric Prevention Tests.

Verifies:
1. Reports reflect failed ranking gate accurately.
2. Reports reflect failed agent gate accurately.
3. Missing artifacts cannot produce successful fallback metrics (must show NOT_MEASURED or fail).
4. No hardcoded passing constants (e.g. 0.925, OPTION_B_ACCEPTED) in generated reports.
"""

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


def test_reports_reflect_failed_ranking_gate(temp_report_dir):
    """Verify final_assessment.md and ranking_report.md reflect failed ranking gate."""
    generate_all_reports(out_dir=temp_report_dir)

    final_assessment = (temp_report_dir / "final_assessment.md").read_text(encoding="utf-8")
    assert "Ranking Gate**: **FAILED" in final_assessment, (
        "final_assessment.md must accurately reflect that the ranking gate failed"
    )

    ranking_report = (temp_report_dir / "ranking_report.md").read_text(encoding="utf-8")
    assert "Ranking Gate Verdict**: **FAILED" in ranking_report, (
        "ranking_report.md must report FAILED for ranking gate verdict"
    )


def test_reports_reflect_failed_agent_gate(temp_report_dir):
    """Verify final_assessment.md reflects failed agent gate."""
    generate_all_reports(out_dir=temp_report_dir)

    final_assessment = (temp_report_dir / "final_assessment.md").read_text(encoding="utf-8")
    assert "Agent Gate**: **FAILED" in final_assessment or "Agent Gate**: **NOT_MEASURED" in final_assessment, (
        "final_assessment.md must accurately reflect that the agent gate failed or is unmeasured"
    )
    # Must NOT claim passed
    assert "Agent Gate**: **PASSED" not in final_assessment


def test_reports_reflect_invalid_contract_and_failed_integrity(temp_report_dir):
    """Verify final_assessment.md reflects INVALID_CONTRACT and integrity failure."""
    generate_all_reports(out_dir=temp_report_dir)

    final_assessment = (temp_report_dir / "final_assessment.md").read_text(encoding="utf-8")
    assert "- **Run Validity**: `INVALID`" in final_assessment
    assert "- **Contract Feasibility**: `INVALID_CONTRACT`" in final_assessment
    assert "- **Integrity Gate**: **FAILED**" in final_assessment


def test_missing_artifact_renders_not_measured_without_fallback_defaults(monkeypatch, temp_report_dir):
    """
    Simulate missing results directory where artifacts are not present.
    Reports must display NOT_MEASURED and never fabricate passing metrics like 0.925 or OPTION_B_ACCEPTED.
    """
    with tempfile.TemporaryDirectory() as empty_results_dir:
        from experiments.rcir_v8_5.scripts import environment

        # Mock results_root to an empty directory
        class MockEnv:
            results_root = Path(empty_results_dir)
            reports_root = temp_report_dir
            raw_root = Path(empty_results_dir)
            target_repo_commit = "mock-commit"
            polyflow_commit = "mock-commit"
            target_repository_state = "CLEAN"
            run_id = "mock-run"

        mock_env = MockEnv()
        monkeypatch.setattr(environment, "get_default_environment", lambda: mock_env)

        generate_all_reports(out_dir=temp_report_dir, env=mock_env)

        # Inspect generated reports
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
        assert "NOT_MEASURED" in final_assessment or "NOT_EVALUATED" in final_assessment


def test_delete_individual_result_artifacts_one_by_one(monkeypatch, temp_report_dir):
    """
    Regression requirement:
    Delete each result artifact one at a time and invoke report generation.
    The generator must either fail or explicitly show NOT_MEASURED, and never fabricate passing claims.
    """
    from experiments.rcir_v8_5.scripts import environment
    original_env = environment.get_default_environment()

    # Create a sandbox results directory copied from the real one
    with tempfile.TemporaryDirectory() as sandbox_results_str:
        sandbox_results = Path(sandbox_results_str)
        for json_file in original_env.results_root.glob("*.json"):
            shutil.copy(json_file, sandbox_results / json_file.name)

        class MockEnv:
            results_root = sandbox_results
            reports_root = temp_report_dir
            raw_root = original_env.raw_root
            target_repo_commit = original_env.target_repo_commit
            polyflow_commit = original_env.polyflow_commit
            target_repository_state = original_env.target_repository_state
            run_id = original_env.run_id

        monkeypatch.setattr(environment, "get_default_environment", lambda: MockEnv())

        # Test deleting each artifact one at a time
        for artifact_path in list(sandbox_results.glob("*.json")):
            # Temporarily rename/remove
            backup_path = artifact_path.with_suffix(".bak")
            artifact_path.rename(backup_path)

            try:
                generate_all_reports(out_dir=temp_report_dir)
                # Verify that no positive passing fallback metric was fabricated
                final_assessment = (temp_report_dir / "final_assessment.md").read_text(encoding="utf-8")
                assert "OPTION_B_ACCEPTED" not in final_assessment
            finally:
                backup_path.rename(artifact_path)
