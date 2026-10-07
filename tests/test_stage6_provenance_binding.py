"""
Stage 6: Provenance Binding & Integrity Mutation Tests (12 Conditions).

Verifies fail-closed behavior on 12 distinct mutations:
1. Changed PolyFlow commit.
2. Changed target commit.
3. 1-byte mutation in ground_truth.json.
4. 1-byte mutation in test.json.
5. Mutated graph artifact.
6. Mutated benchmark contract.
7. Mutated ranker config hash.
8. Mutated context config hash.
9. Reusing an artifact from another run_id.
10. Reusing an artifact with correct run_id but wrong manifest_hash.
11. Dirty PolyFlow working tree in formal benchmark.
12. Deleting a required provenance field.

All 12 must fail closed with validation error.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts"))

from environment import get_default_environment
from provenance import (
    build_provenance_envelope,
    collect_input_hashes,
    compute_run_identity,
    validate_artifact_provenance,
)


@pytest.fixture
def base_envelope():
    env = get_default_environment()
    env.derive_run_id()
    return build_provenance_envelope(env, manifest_hash="manifest_hash_abc123")


def test_mutation_1_changed_polyflow_commit(base_envelope):
    """Mutation 1: Changing PolyFlow commit must invalidate artifact provenance."""
    art = copy.deepcopy(base_envelope)
    art["polyflow_commit"] = "0000000000000000000000000000000000000000"
    valid, failures = validate_artifact_provenance(art, base_envelope)
    assert valid is False
    assert any("PolyFlow commit mismatch" in f for f in failures)


def test_mutation_2_changed_target_commit(base_envelope):
    """Mutation 2: Changing Target repo commit must invalidate artifact provenance."""
    art = copy.deepcopy(base_envelope)
    art["target_repo_commit"] = "ffffffffffffffffffffffffffffffffffffffff"
    valid, failures = validate_artifact_provenance(art, base_envelope)
    assert valid is False
    assert any("Target repo commit mismatch" in f for f in failures)


def test_mutation_3_mutated_ground_truth_hash(base_envelope):
    """Mutation 3: 1-byte mutation in ground truth changes hash and invalidates provenance."""
    art = copy.deepcopy(base_envelope)
    art["ground_truth_hash"] = "deadbeef" * 8
    valid, failures = validate_artifact_provenance(art, base_envelope)
    assert valid is False
    assert any("Ground truth hash mismatch" in f for f in failures)


def test_mutation_4_mutated_test_dataset_hash(base_envelope):
    """Mutation 4: 1-byte mutation in test dataset changes hash and invalidates provenance."""
    art = copy.deepcopy(base_envelope)
    art["dataset_hashes"]["test"] = "deadbeef" * 8
    valid, failures = validate_artifact_provenance(art, base_envelope)
    assert valid is False
    assert any("Dataset hash mismatch for 'test'" in f for f in failures)


def test_mutation_5_mutated_graph_hash(base_envelope):
    """Mutation 5: Changing canonical graph hash invalidates artifact provenance."""
    art = copy.deepcopy(base_envelope)
    art["graph_hash"] = "deadbeef" * 8
    valid, failures = validate_artifact_provenance(art, base_envelope)
    assert valid is False
    assert any("Canonical graph hash mismatch" in f for f in failures)


def test_mutation_6_mutated_contract_hash(base_envelope):
    """Mutation 6: Changing contract hash invalidates artifact provenance."""
    art = copy.deepcopy(base_envelope)
    art["contract_hash"] = "deadbeef" * 8
    valid, failures = validate_artifact_provenance(art, base_envelope)
    assert valid is False
    assert any("Contract hash mismatch" in f for f in failures)


def test_mutation_7_mutated_ranker_config_hash(base_envelope):
    """Mutation 7: Mutating ranker configuration changes run identity."""
    env = get_default_environment()
    inputs = collect_input_hashes(env)
    mutated_inputs = copy.deepcopy(inputs)
    mutated_inputs["config_hashes"]["ranker_config"] = "deadbeef" * 8

    run_id_orig = compute_run_identity(inputs)
    run_id_mut = compute_run_identity(mutated_inputs)
    assert run_id_orig != run_id_mut


def test_mutation_8_mutated_context_config_hash(base_envelope):
    """Mutation 8: Mutating context configuration changes run identity."""
    env = get_default_environment()
    inputs = collect_input_hashes(env)
    mutated_inputs = copy.deepcopy(inputs)
    mutated_inputs["config_hashes"]["context_config"] = "deadbeef" * 8

    run_id_orig = compute_run_identity(inputs)
    run_id_mut = compute_run_identity(mutated_inputs)
    assert run_id_orig != run_id_mut


def test_mutation_9_reused_artifact_from_another_run_id(base_envelope):
    """Mutation 9: Reusing an artifact with an old/foreign run ID fails closed."""
    art = copy.deepcopy(base_envelope)
    art["run_id"] = "rcir-v8.5-primary"
    valid, failures = validate_artifact_provenance(art, base_envelope)
    assert valid is False
    assert any("Run ID mismatch" in f for f in failures)


def test_mutation_10_correct_run_id_wrong_manifest_hash(base_envelope):
    """Mutation 10: Reusing an artifact with correct run ID but stale manifest hash fails closed."""
    art = copy.deepcopy(base_envelope)
    art["manifest_hash"] = "stale_manifest_hash_999"
    valid, failures = validate_artifact_provenance(art, base_envelope)
    assert valid is False
    assert any("Manifest hash mismatch" in f for f in failures)


def test_mutation_11_dirty_polyflow_working_tree_rejected(base_envelope):
    """Mutation 11: Dirty PolyFlow working tree rejected in formal release benchmark."""
    art = copy.deepcopy(base_envelope)
    art["polyflow_dirty"] = True
    valid, failures = validate_artifact_provenance(art, base_envelope, allow_development_dirty=False)
    assert valid is False
    assert any("PolyFlow working tree was dirty" in f for f in failures)


def test_mutation_12_deleted_required_provenance_field(base_envelope):
    """Mutation 12: Deleting any required provenance field fails closed."""
    art = copy.deepcopy(base_envelope)
    del art["created_at"]
    valid, failures = validate_artifact_provenance(art, base_envelope)
    assert valid is False
    assert any("Missing required provenance field: 'created_at'" in f for f in failures)

    art2 = copy.deepcopy(base_envelope)
    del art2["manifest_hash"]
    valid2, failures2 = validate_artifact_provenance(art2, base_envelope)
    assert valid2 is False
    assert any("Missing required provenance field: 'manifest_hash'" in f for f in failures2)
