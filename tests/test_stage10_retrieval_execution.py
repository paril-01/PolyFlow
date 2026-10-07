"""
Stage 10: Retrieval Execution and Control Flow Integrity Tests.

Verifies:
1. `build_ranker` fails closed with ValueError on unknown configurations (no silent R0 substitution).
2. `build_ranker` returns correct ranker types for valid configuration keys.
3. `execute_retrieval_suite` produces all mandatory output artifacts when run in an empty output directory.
4. Validation selection metrics, baseline R0 metrics, and TEST metrics are genuinely calculated.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5"))

from rcir.retrieval.ranker import DeterministicRanker, MultiObjectiveRanker
from retrieval_runner import (
    RANKER_CANDIDATE_CONFIGS,
    build_ranker,
    execute_retrieval_suite,
)
from environment import get_default_environment


def test_build_ranker_unknown_config_raises_value_error():
    """Verify that build_ranker does NOT silently default to R0 when given an unknown configuration."""
    with pytest.raises(ValueError, match="Unknown ranker configuration"):
        build_ranker("NON_EXISTENT_RANKER_CFG")

    with pytest.raises(ValueError, match="Unknown ranker configuration"):
        build_ranker("")

    with pytest.raises(ValueError, match="Unknown ranker configuration"):
        build_ranker("None")


def test_build_ranker_permitted_configs():
    """Verify that all declared candidate configurations instantiate valid rankers."""
    for cfg_name in RANKER_CANDIDATE_CONFIGS:
        ranker = build_ranker(cfg_name)
        assert ranker is not None
        assert hasattr(ranker, "rank")

    # Linear / R0
    r0 = build_ranker("R0")
    assert isinstance(r0, DeterministicRanker)
    assert r0.config.use_cascaded_ranking is False

    # Cascaded
    exact_first = build_ranker("ExactFirst")
    assert isinstance(exact_first, DeterministicRanker)
    assert exact_first.config.use_cascaded_ranking is True

    # Multi-Objective RRF
    rrf = build_ranker("AnchorCoverageRRF", operation="behavior_change")
    assert isinstance(rrf, MultiObjectiveRanker)


def test_retrieval_suite_generates_all_mandatory_outputs_in_clean_workspace(monkeypatch):
    """
    Verify that execute_retrieval_suite produces all mandatory files starting from an empty output directory,
    and that all metrics are genuinely calculated.
    """
    base_env = get_default_environment()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        sandbox_results = tmp_path / "results"
        sandbox_raw = tmp_path / "raw"
        sandbox_results.mkdir(parents=True, exist_ok=True)
        sandbox_raw.mkdir(parents=True, exist_ok=True)

        # Create isolated MockEnv pointing to clean sandbox results and raw
        class SandboxEnv:
            polyflow_root = base_env.polyflow_root
            target_repo_root = base_env.target_repo_root
            target_repo_commit = base_env.target_repo_commit
            polyflow_commit = base_env.polyflow_commit
            polyflow_dirty = base_env.polyflow_dirty
            polyflow_worktree_diff_hash = base_env.polyflow_worktree_diff_hash
            target_repo_dirty = base_env.target_repo_dirty
            working_tree_diff_hash = base_env.working_tree_diff_hash
            run_id = base_env.run_id
            v8_5_root = base_env.v8_5_root
            graph_path = base_env.graph_path
            dataset_root = base_env.dataset_root
            ground_truth_root = base_env.ground_truth_root
            edge_ground_truth_root = base_env.edge_ground_truth_root
            receiver_ground_truth_root = base_env.receiver_ground_truth_root
            canonicalization_ground_truth_root = base_env.canonicalization_ground_truth_root
            manifests_root = base_env.manifests_root
            contract_path = base_env.contract_path
            reports_root = tmp_path / "reports"
            results_root = sandbox_results
            raw_root = sandbox_raw

        import subprocess

        runner_script = REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts" / "retrieval_runner.py"
        code = f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{REPO_ROOT / 'rcir' / 'src'}")
sys.path.insert(0, r"{REPO_ROOT / 'experiments' / 'rcir_v8_5' / 'scripts'}")
import retrieval_runner as rr
from environment import get_default_environment

base_env = get_default_environment()

class SandboxEnv:
    polyflow_root = base_env.polyflow_root
    target_repo_root = base_env.target_repo_root
    target_repo_commit = base_env.target_repo_commit
    polyflow_commit = base_env.polyflow_commit
    polyflow_dirty = base_env.polyflow_dirty
    polyflow_worktree_diff_hash = base_env.polyflow_worktree_diff_hash
    target_repo_dirty = base_env.target_repo_dirty
    working_tree_diff_hash = base_env.working_tree_diff_hash
    run_id = base_env.run_id
    v8_5_root = base_env.v8_5_root
    graph_path = base_env.graph_path
    dataset_root = base_env.dataset_root
    ground_truth_root = base_env.ground_truth_root
    edge_ground_truth_root = base_env.edge_ground_truth_root
    receiver_ground_truth_root = base_env.receiver_ground_truth_root
    canonicalization_ground_truth_root = base_env.canonicalization_ground_truth_root
    manifests_root = base_env.manifests_root
    contract_path = base_env.contract_path
    reports_root = Path(r"{tmp_path / 'reports'}")
    results_root = Path(r"{sandbox_results}")
    raw_root = Path(r"{sandbox_raw}")

    def derive_run_id(self):
        return self.run_id

rr.env = SandboxEnv()
rr.execute_retrieval_suite()
"""
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        assert proc.returncode == 0, f"Retrieval suite execution failed: {proc.stderr}\n{proc.stdout}"

        # Assert all 12 mandatory outputs exist in the clean directory
        mandatory_files = [
            sandbox_results / "selected_ranker_config.json",
            sandbox_results / "ranker_baseline_r0.json",
            sandbox_results / "ranker_dev.json",
            sandbox_results / "ranker_validation.json",
            sandbox_results / "ranker_test.json",
            sandbox_results / "impact_dev.json",
            sandbox_results / "impact_validation.json",
            sandbox_results / "impact_test.json",
            sandbox_results / "dataset_split_overlap.json",
            sandbox_raw / "retrieval" / "dev_predictions.json",
            sandbox_raw / "retrieval" / "validation_predictions.json",
            sandbox_raw / "retrieval" / "test_predictions.json",
        ]

        for p in mandatory_files:
            assert p.exists(), f"Mandatory retrieval output missing: {p.name}"
            assert p.stat().st_size > 50, f"Output file is empty or trivial: {p.name}"

        # Verify selected_ranker_config content and validation metrics
        selected_data = json.loads((sandbox_results / "selected_ranker_config.json").read_text(encoding="utf-8"))
        assert "selected_configuration" in selected_data
        assert selected_data["selected_configuration"] in RANKER_CANDIDATE_CONFIGS
        assert "validation_metrics" in selected_data
        assert selected_data["validation_metrics"]["macro_pool_recall"] > 0.0
        assert selected_data["validation_metrics"]["dependency_mrr"] > 0.0

        # Verify baseline R0 content and metrics
        r0_data = json.loads((sandbox_results / "ranker_baseline_r0.json").read_text(encoding="utf-8"))
        assert r0_data["ranker_configuration"] == "R0_GraphDistanceBaseline"
        assert "metrics" in r0_data
        assert "precision_at_50_excluding_target" in r0_data["metrics"]

        # Verify TEST ranker metrics
        test_ranker_data = json.loads((sandbox_results / "ranker_test.json").read_text(encoding="utf-8"))
        assert "metrics" in test_ranker_data
        assert test_ranker_data["metrics"]["macro_pool_recall"] > 0.0
        assert test_ranker_data["metrics"]["dependency_mrr"] > 0.0

        # Verify dataset split overlap metrics (Issue 35: expected_files overlap must be computed)
        overlap_data = json.loads((sandbox_results / "dataset_split_overlap.json").read_text(encoding="utf-8"))
        assert "dev_vs_test" in overlap_data
        assert "overlapping_expected_files" in overlap_data["dev_vs_test"]
        assert "validation_vs_test" in overlap_data
        assert "overlapping_expected_files" in overlap_data["validation_vs_test"]
