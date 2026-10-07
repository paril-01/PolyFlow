"""
Stage 7: Contract Feasibility & Theoretical Metric Ceiling Tests.

Verifies:
- Accurate calculation of theoretical fixed-denominator Precision@K ceilings given sparse ground-truth labels.
- Pre-flight rejection of impossible contracts (e.g. P@20 >= 0.35 when ceiling is ~0.15).
- Clean acceptance of mathematically possible thresholds.
- Behavior with zero relevant items.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts"))

from contract_feasibility import calculate_ranking_ceilings, validate_contract_feasibility
from environment import get_default_environment


def test_theoretical_ceiling_calculation_on_real_test_split():
    """Verify that theoretical ceilings for Nextcloud TEST split are bounded by sparse labels."""
    env = get_default_environment()
    gt_path = env.ground_truth_root / "ground_truth.json"
    assert gt_path.exists(), "ground_truth.json must exist"

    gt_data = json.loads(gt_path.read_text(encoding="utf-8"))
    test_tasks = [t for t in gt_data["tasks"].values() if t.get("split") == "test"]
    ceilings = calculate_ranking_ceilings(test_tasks, k_values=(20, 50))

    # Nextcloud TEST tasks have ~2-4 dependencies after target exclusion
    # Mean P@20 ceiling must be <= 0.20 (typically ~0.15)
    # Mean P@50 ceiling must be <= 0.10 (typically ~0.06)
    assert "precision_at_20_excluding_target" in ceilings
    assert "precision_at_50_excluding_target" in ceilings
    assert ceilings["precision_at_20_excluding_target"] < 0.20
    assert ceilings["precision_at_50_excluding_target"] < 0.10


def test_impossible_contract_thresholds_detected():
    """Verify that contracts with thresholds exceeding theoretical maximum are marked INVALID_CONTRACT."""
    # Synthetic tasks where each task has only 2 dependencies
    tasks = [
        {"target_file": "app/A.php", "expected_files": ["app/A.php", "app/B.php", "app/C.php"]},
        {"target_file": "app/X.php", "expected_files": ["app/X.php", "app/Y.php", "app/Z.php"]},
    ]
    # For k=20, max possible is 2/20 = 0.10
    # For k=50, max possible is 2/50 = 0.04

    impossible_contract = {
        "ranking_plane": {
            "precision_at_20_excluding_target_min": 0.35,  # Exceeds 0.10
            "precision_at_50_excluding_target_min": 0.20,  # Exceeds 0.04
        }
    }

    is_feasible, details = validate_contract_feasibility(impossible_contract, tasks)
    assert is_feasible is False
    assert details["status"] == "INVALID_CONTRACT"
    assert len(details["violations"]) == 2
    assert "precision_at_20" in details["violations"][0]
    assert "precision_at_50" in details["violations"][1]


def test_feasible_contract_thresholds_accepted():
    """Verify that contracts with reachable thresholds pass feasibility validation."""
    tasks = [
        {"target_file": "app/A.php", "expected_files": ["app/A.php", "app/B.php", "app/C.php"]},
        {"target_file": "app/X.php", "expected_files": ["app/X.php", "app/Y.php", "app/Z.php"]},
    ]
    # Ceilings are 0.10 and 0.04
    feasible_contract = {
        "ranking_plane": {
            "precision_at_20_excluding_target_min": 0.08,
            "precision_at_50_excluding_target_min": 0.03,
        }
    }

    is_feasible, details = validate_contract_feasibility(feasible_contract, tasks)
    assert is_feasible is True
    assert details["status"] == "VALID_CONTRACT"
    assert len(details["violations"]) == 0


def test_zero_relevant_dependencies_behavior():
    """Verify that tasks with zero relevant dependencies are handled gracefully."""
    tasks = [
        {"target_file": "app/Solo.php", "expected_files": ["app/Solo.php"]},
    ]
    # Ceiling is 0.0
    contract = {
        "ranking_plane": {
            "precision_at_20_excluding_target_min": 0.05,
        }
    }

    is_feasible, details = validate_contract_feasibility(contract, tasks)
    assert is_feasible is False
    assert details["status"] == "INVALID_CONTRACT"
    assert details["theoretical_ceilings"]["precision_at_20_excluding_target"] == 0.0
