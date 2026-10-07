#!/usr/bin/env python3
"""
RCIR v8.5.1 — Cryptographic Provenance and Integrity Binding.

Centralizes:
- Cryptographic run identity derivation
- Input hashing (PolyFlow, Nextcloud, contract, datasets, graph, configs)
- Provenance envelope construction
- Strict artifact provenance validation
- Clean / dirty source enforcement
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def hash_file(file_path: Path | str) -> str:
    """Compute hex SHA-256 digest of a file, returning empty string if missing."""
    p = Path(file_path)
    if not p.exists() or p.is_dir():
        return ""
    return hashlib.sha256(p.read_bytes()).hexdigest()


def hash_dict(data: Dict[str, Any]) -> str:
    """Compute deterministic hex SHA-256 digest of dictionary data."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def collect_input_hashes(env: Any) -> Dict[str, Any]:
    """Collect cryptographic hashes for all benchmark inputs (v8.5.2)."""
    dataset_hashes = {
        "dev": hash_file(env.dataset_root / "dev.json"),
        "validation": hash_file(env.dataset_root / "validation.json"),
        "test": hash_file(env.dataset_root / "test.json"),
    }
    
    ground_truth_hashes = {
        "ground_truth": hash_file(env.ground_truth_root / "ground_truth.json"),
        "edges": hash_file(env.edge_ground_truth_root / "ground_truth_edges.json"),
        "receivers": hash_file(env.receiver_ground_truth_root / "receiver_ground_truth.json"),
        "canonicalization": hash_file(env.canonicalization_ground_truth_root / "canonicalization_corpus.json"),
    }

    config_dir = env.v8_5_root / "config"
    config_hashes = {
        "candidate_config": hash_file(config_dir / "candidate_generation.json"),
        "ranker_config": hash_file(config_dir / "ranker_candidates.json"),
        "objective_config": hash_file(config_dir / "ranking_objective.json"),
        "context_config": hash_file(config_dir / "context_compiler.json"),
        "typeflow_config": hash_file(config_dir / "type_flow.json"),
        # Code fingerprints of critical benchmark implementation modules (Issue 7)
        "retrieval_runner_code": hash_file(env.v8_5_root / "scripts" / "retrieval_runner.py"),
        "ranker_code": hash_file(env.polyflow_root / "rcir" / "src" / "rcir" / "retrieval" / "ranker.py"),
        "adapter_code": hash_file(env.polyflow_root / "rcir" / "src" / "rcir" / "adapters" / "nextcloud.py"),
        "compiler_code": hash_file(env.polyflow_root / "rcir" / "src" / "rcir" / "context" / "compiler.py"),
        "typeflow_code": hash_file(env.polyflow_root / "rcir" / "src" / "rcir" / "types" / "php_type_flow.py"),
    }

    return {
        "polyflow_commit": env.polyflow_commit,
        "polyflow_dirty": env.polyflow_dirty,
        "polyflow_worktree_diff_hash": env.polyflow_worktree_diff_hash,
        "target_repo_commit": env.target_repo_commit,
        "target_repo_dirty": env.target_repo_dirty,
        "target_repo_diff_hash": env.working_tree_diff_hash,
        "contract_hash": hash_file(env.contract_path),
        "dataset_hashes": dataset_hashes,
        "ground_truth_hashes": ground_truth_hashes,
        "graph_hash": hash_file(env.graph_path),
        "config_hashes": config_hashes,
    }


def compute_run_identity(input_hashes: Dict[str, Any]) -> str:
    """
    Derive an immutable run identity cryptographically from benchmark inputs.
    Same input set reproduces same identity. Different executable inputs produce a different identity.
    """
    digest = hash_dict(input_hashes)
    return f"rcir-v8.5.2-{digest[:16]}"


def build_provenance_envelope(env: Any, manifest_hash: str = "") -> Dict[str, Any]:
    """Build a complete, standardized provenance envelope for result artifacts."""
    inputs = collect_input_hashes(env)
    run_id = compute_run_identity(inputs)

    if not manifest_hash:
        manifest_path = env.manifests_root / "benchmark_run_manifest.json"
        manifest_hash = hash_file(manifest_path) if manifest_path.exists() else ""

    return {
        "run_id": run_id,
        "manifest_hash": manifest_hash,
        "polyflow_commit": env.polyflow_commit,
        "polyflow_dirty": env.polyflow_dirty,
        "polyflow_worktree_diff_hash": env.polyflow_worktree_diff_hash,
        "target_repo_commit": env.target_repo_commit,
        "target_repo_dirty": env.target_repo_dirty,
        "target_repo_diff_hash": env.working_tree_diff_hash,
        "contract_hash": inputs["contract_hash"],
        "dataset_hashes": inputs["dataset_hashes"],
        "ground_truth_hash": inputs["ground_truth_hashes"]["ground_truth"],
        "edge_ground_truth_hash": inputs["ground_truth_hashes"]["edges"],
        "receiver_ground_truth_hash": inputs["ground_truth_hashes"]["receivers"],
        "canonicalization_ground_truth_hash": inputs["ground_truth_hashes"]["canonicalization"],
        "graph_hash": inputs["graph_hash"],
        "config_hashes": inputs["config_hashes"],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


REQUIRED_PROVENANCE_FIELDS = [
    "run_id",
    "manifest_hash",
    "polyflow_commit",
    "polyflow_dirty",
    "polyflow_worktree_diff_hash",
    "target_repo_commit",
    "target_repo_dirty",
    "target_repo_diff_hash",
    "contract_hash",
    "dataset_hashes",
    "ground_truth_hash",
    "edge_ground_truth_hash",
    "receiver_ground_truth_hash",
    "canonicalization_ground_truth_hash",
    "graph_hash",
    "config_hashes",
    "created_at",
]


def validate_artifact_provenance(
    artifact_data: Dict[str, Any],
    expected_envelope: Any,
    allow_development_dirty: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Validate an artifact's embedded provenance against the expected current run envelope.
    Returns (is_valid, list_of_failure_reasons).
    """
    if hasattr(expected_envelope, "derive_run_id"):
        expected_envelope = build_provenance_envelope(expected_envelope)

    failures: List[str] = []

    # Check required fields
    for field in REQUIRED_PROVENANCE_FIELDS:
        if field not in artifact_data:
            failures.append(f"Missing required provenance field: '{field}'")

    if failures:
        return False, failures

    # Check run ID
    if artifact_data.get("run_id") != expected_envelope.get("run_id"):
        failures.append(
            f"Run ID mismatch: artifact has '{artifact_data.get('run_id')}' but expected '{expected_envelope.get('run_id')}'"
        )

    # Check manifest hash
    if artifact_data.get("manifest_hash") != expected_envelope.get("manifest_hash"):
        failures.append(
            f"Manifest hash mismatch: artifact has '{artifact_data.get('manifest_hash')}' but expected '{expected_envelope.get('manifest_hash')}'"
        )

    # Check PolyFlow commit
    if artifact_data.get("polyflow_commit") != expected_envelope.get("polyflow_commit"):
        failures.append(
            f"PolyFlow commit mismatch: artifact has '{artifact_data.get('polyflow_commit')}' but expected '{expected_envelope.get('polyflow_commit')}'"
        )

    # Check dirty status for formal release benchmarks
    if artifact_data.get("polyflow_dirty", False) and not allow_development_dirty:
        failures.append("PolyFlow working tree was dirty during execution (formal release benchmark requires clean tree)")

    # Check PolyFlow worktree diff hash
    if artifact_data.get("polyflow_worktree_diff_hash") != expected_envelope.get("polyflow_worktree_diff_hash"):
        failures.append(
            f"PolyFlow worktree diff hash mismatch: artifact has '{artifact_data.get('polyflow_worktree_diff_hash')}' but expected '{expected_envelope.get('polyflow_worktree_diff_hash')}'"
        )

    # Check Target repo commit
    if artifact_data.get("target_repo_commit") != expected_envelope.get("target_repo_commit"):
        failures.append(
            f"Target repo commit mismatch: artifact has '{artifact_data.get('target_repo_commit')}' but expected '{expected_envelope.get('target_repo_commit')}'"
        )

    # Check Target repo dirty and diff hash
    if artifact_data.get("target_repo_dirty") != expected_envelope.get("target_repo_dirty"):
        failures.append(
            f"Target repo dirty state mismatch: artifact has '{artifact_data.get('target_repo_dirty')}' but expected '{expected_envelope.get('target_repo_dirty')}'"
        )
    if artifact_data.get("target_repo_diff_hash") != expected_envelope.get("target_repo_diff_hash"):
        failures.append(
            f"Target repo diff hash mismatch: artifact has '{artifact_data.get('target_repo_diff_hash')}' but expected '{expected_envelope.get('target_repo_diff_hash')}'"
        )

    # Check contract hash
    if artifact_data.get("contract_hash") != expected_envelope.get("contract_hash"):
        failures.append(
            f"Contract hash mismatch: artifact has '{artifact_data.get('contract_hash')}' but expected '{expected_envelope.get('contract_hash')}'"
        )

    # Check graph hash
    if artifact_data.get("graph_hash") != expected_envelope.get("graph_hash"):
        failures.append(
            f"Canonical graph hash mismatch: artifact has '{artifact_data.get('graph_hash')}' but expected '{expected_envelope.get('graph_hash')}'"
        )

    # Check dataset hashes
    art_datasets = artifact_data.get("dataset_hashes", {})
    exp_datasets = expected_envelope.get("dataset_hashes", {})
    for split_name, exp_hash in exp_datasets.items():
        if art_datasets.get(split_name) != exp_hash:
            failures.append(
                f"Dataset hash mismatch for '{split_name}': artifact has '{art_datasets.get(split_name)}' but expected '{exp_hash}'"
            )

    # Check all ground truth hashes (Issue 6)
    for gt_field in [
        "ground_truth_hash",
        "edge_ground_truth_hash",
        "receiver_ground_truth_hash",
        "canonicalization_ground_truth_hash",
    ]:
        if artifact_data.get(gt_field) != expected_envelope.get(gt_field):
            failures.append(
                f"Ground truth hash mismatch: field '{gt_field}' mismatch: artifact has '{artifact_data.get(gt_field)}' but expected '{expected_envelope.get(gt_field)}'"
            )

    # Check config hashes key-by-key (Issue 6)
    art_configs = artifact_data.get("config_hashes", {})
    exp_configs = expected_envelope.get("config_hashes", {})
    for cfg_key, exp_h in exp_configs.items():
        art_h = art_configs.get(cfg_key)
        if art_h != exp_h:
            failures.append(
                f"Config hash mismatch for '{cfg_key}': artifact has '{art_h}' but expected '{exp_h}'"
            )

    return len(failures) == 0, failures

