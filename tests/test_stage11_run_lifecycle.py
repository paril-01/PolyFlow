"""
Stage 11: Run Lifecycle, Provenance Envelope, and Manifest Integrity Tests.

Verifies:
1. Tampering with any config hash in an artifact fails `validate_artifact_provenance()`.
2. Tampering with any ground truth hash fails provenance validation.
3. Tampering with git diff hashes fails provenance validation.
4. Dirty working tree fails provenance validation when allow_development_dirty is False.
5. Manifest validation in evaluate_gates checks all input hashes, not merely run_id or manifest_hash.
6. BenchmarkEnvironment captures and verifies source cleanliness before and after runs.
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5"))

from environment import get_default_environment
from provenance import (
    REQUIRED_PROVENANCE_FIELDS,
    build_provenance_envelope,
    collect_input_hashes,
    validate_artifact_provenance,
)
from evaluate_gates import evaluate_gates


def test_artifact_provenance_passes_for_valid_envelope():
    """Verify that a freshly constructed valid envelope passes provenance validation."""
    env = get_default_environment()
    envelope = build_provenance_envelope(env, manifest_hash="0" * 64)
    # Mock clean for test
    envelope["polyflow_dirty"] = False
    envelope["target_repo_dirty"] = False

    is_valid, failures = validate_artifact_provenance(
        envelope, envelope, allow_development_dirty=False
    )
    assert is_valid is True, f"Valid envelope failed provenance: {failures}"
    assert len(failures) == 0


def test_tampered_config_hashes_fail_provenance():
    """Verify that modifying any nested config or code hash in an artifact fails provenance (Issue 6 & 7)."""
    env = get_default_environment()
    envelope = build_provenance_envelope(env, manifest_hash="0" * 64)
    envelope["polyflow_dirty"] = False
    envelope["target_repo_dirty"] = False

    config_keys = [
        "candidate_config",
        "ranker_config",
        "objective_config",
        "context_config",
        "typeflow_config",
        "retrieval_runner_code",
        "ranker_code",
        "adapter_code",
        "compiler_code",
        "typeflow_code",
    ]

    for key in config_keys:
        tampered_artifact = copy.deepcopy(envelope)
        assert key in tampered_artifact["config_hashes"], f"Missing config key {key}"
        tampered_artifact["config_hashes"][key] = "bad_tampered_hash_12345"

        is_valid, failures = validate_artifact_provenance(
            tampered_artifact, envelope, allow_development_dirty=False
        )
        assert is_valid is False, f"Tampered config '{key}' should have failed provenance"
        assert any(f"Config hash mismatch for '{key}'" in f for f in failures)


def test_tampered_ground_truth_hashes_fail_provenance():
    """Verify that modifying any ground truth hash fails provenance validation (Issue 6)."""
    env = get_default_environment()
    envelope = build_provenance_envelope(env, manifest_hash="0" * 64)
    envelope["polyflow_dirty"] = False
    envelope["target_repo_dirty"] = False

    gt_fields = [
        "ground_truth_hash",
        "edge_ground_truth_hash",
        "receiver_ground_truth_hash",
        "canonicalization_ground_truth_hash",
    ]

    for field in gt_fields:
        tampered_artifact = copy.deepcopy(envelope)
        tampered_artifact[field] = "bad_gt_hash_98765"

        is_valid, failures = validate_artifact_provenance(
            tampered_artifact, envelope, allow_development_dirty=False
        )
        assert is_valid is False, f"Tampered ground truth field '{field}' should have failed provenance"
        assert any(f"'{field}' mismatch" in f for f in failures)


def test_dirty_working_tree_fails_release_provenance():
    """Verify that a dirty working tree fails closed for release benchmarks (allow_development_dirty=False)."""
    env = get_default_environment()
    envelope = build_provenance_envelope(env, manifest_hash="0" * 64)
    envelope["polyflow_dirty"] = True

    is_valid, failures = validate_artifact_provenance(
        envelope, envelope, allow_development_dirty=False
    )
    assert is_valid is False
    assert any("PolyFlow working tree was dirty" in f for f in failures)

    # When development dirty is permitted, it should pass
    is_valid_dev, _ = validate_artifact_provenance(
        envelope, envelope, allow_development_dirty=True
    )
    assert is_valid_dev is True


def test_tampered_worktree_diff_hash_fails_provenance():
    """Verify that mismatched polyflow_worktree_diff_hash fails provenance."""
    env = get_default_environment()
    envelope = build_provenance_envelope(env, manifest_hash="0" * 64)
    envelope["polyflow_dirty"] = False
    envelope["target_repo_dirty"] = False

    tampered_artifact = copy.deepcopy(envelope)
    tampered_artifact["polyflow_worktree_diff_hash"] = "different_diff_hash"

    is_valid, failures = validate_artifact_provenance(
        tampered_artifact, envelope, allow_development_dirty=False
    )
    assert is_valid is False
    assert any("PolyFlow worktree diff hash mismatch" in f for f in failures)


def test_manifest_field_validation_in_evaluate_gates():
    """Verify that evaluate_gates validates manifest contents beyond just hash (Issue 5)."""
    env = get_default_environment()

    with tempfile.TemporaryDirectory() as tmp_dir:
        sandbox_path = Path(tmp_dir)
        sandbox_manifests = sandbox_path / "manifests"
        sandbox_results = sandbox_path / "results"
        sandbox_manifests.mkdir(parents=True, exist_ok=True)
        sandbox_results.mkdir(parents=True, exist_ok=True)

        # Create sandbox environment
        sandbox_env = get_default_environment(run_dir=sandbox_path)

        # Write a manifest with a forged polyflow_commit
        current_inputs = collect_input_hashes(sandbox_env)
        forged_manifest = {
            "run_id": sandbox_env.run_id,
            "polyflow_commit": "forged_commit_sha_000000",
            "target_repository_commit": current_inputs["target_repo_commit"],
            "contract_hash": current_inputs["contract_hash"],
            "graph_hash": current_inputs["graph_hash"],
            "dataset_hashes": current_inputs["dataset_hashes"],
            "ground_truth_hashes": current_inputs["ground_truth_hashes"],
            "config_hashes": current_inputs["config_hashes"],
        }
        (sandbox_manifests / "benchmark_run_manifest.json").write_text(
            json.dumps(forged_manifest, indent=2), encoding="utf-8"
        )

        res = evaluate_gates(allow_development_dirty=True, env=sandbox_env)
        integrity = res.get("integrity_gate", {})
        assert integrity.get("passed") is False
        assert any("Manifest polyflow_commit mismatch" in f for f in integrity.get("failures", []))


def test_benchmark_environment_source_cleanliness_tracking():
    """Verify that BenchmarkEnvironment captures source state and detects modifications."""
    env = get_default_environment()
    initial_state = env.capture_source_state()
    assert "polyflow_commit" in initial_state
    assert "target_repo_commit" in initial_state

    # Same state verifies clean
    assert env.verify_source_cleanliness(initial_state) is True

    # Mutated state fails verification
    mutated_state = copy.deepcopy(initial_state)
    mutated_state["polyflow_commit"] = "tampered_commit"
    assert env.verify_source_cleanliness(mutated_state) is False
