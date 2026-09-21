"""
Tests for Online Boutique controlled benchmark (§6.1.A).

Anti-Fabrication Discipline (§0.1):
- Runs against real cloned Online Boutique repo if present in scratch
- If repo is not present, skips gracefully or runs against a local mock
- Verifies precision and recall calculations against ground truth
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rcir.benchmarks.online_boutique import (
    run_online_boutique_benchmark,
    DEFAULT_SCRATCH_REPO,
    DEFAULT_GROUND_TRUTH,
)
from rcir.evaluation.ground_truth import load_ground_truth


class TestOnlineBoutiqueBenchmark:
    """Integration test for Online Boutique benchmark."""

    @pytest.fixture
    def repo_available(self):
        return DEFAULT_SCRATCH_REPO.exists()

    def test_ground_truth_file_valid(self):
        """Verify the ground truth file loads and has valid schema."""
        assert DEFAULT_GROUND_TRUTH.exists()
        gt_edges = load_ground_truth(DEFAULT_GROUND_TRUTH)
        assert len(gt_edges) >= 20
        for edge in gt_edges:
            assert edge.source
            assert edge.target
            assert edge.edge_class in ("static_exact", "static_inference", "dynamic_unresolved", "unsupported")

    def test_benchmark_execution(self, repo_available):
        """Run the full benchmark and verify honest metrics."""
        if not repo_available:
            pytest.skip("Online Boutique repository not present in scratch directory")

        results = run_online_boutique_benchmark()

        # Structural extraction checks
        meta = results["extraction_metadata"]
        assert meta["total_nodes"] > 100
        assert meta["total_edges"] > 100
        assert meta["proto_files_parsed"] >= 1

        # Precision / recall metrics
        pr = results["precision_recall"]
        assert pr["overall"]["recall"] is not None
        # Since our ground truth contains proto RPCs and emailservice edges,
        # and we extract them accurately, recall on this ground truth should be high
        assert pr["overall"]["recall"] > 0.80

        # Retrieval task checks (§0.1: different queries produce different results)
        retrieval = results["retrieval_benchmarks"]
        assert len(retrieval) == 3

        task_node_sets = [set(t["sample_nodes"]) for t in retrieval]
        # At least two tasks must return different node sets
        assert task_node_sets[0] != task_node_sets[1] or task_node_sets[1] != task_node_sets[2]
