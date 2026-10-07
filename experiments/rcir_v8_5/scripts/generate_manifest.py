#!/usr/bin/env python3
"""
RCIR v8.5.2 — Benchmark Run Manifest Generator (Issue 5).

Generates manifests/benchmark_run_manifest.json with all cryptographic hashes
derived directly from the active BenchmarkEnvironment and provenance inputs.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from environment import get_default_environment
from provenance import collect_input_hashes, compute_run_identity


def generate_benchmark_manifest(env=None) -> Path:
    if env is None:
        env = get_default_environment()

    env.derive_run_id()
    inputs = collect_input_hashes(env)
    expected_run_id = compute_run_identity(inputs)

    manifest_payload = {
        "run_id": expected_run_id,
        "polyflow_commit": inputs["polyflow_commit"],
        "polyflow_dirty": inputs["polyflow_dirty"],
        "polyflow_worktree_diff_hash": inputs["polyflow_worktree_diff_hash"],
        "target_repository": env.target_repo_name,
        "target_repository_commit": inputs["target_repo_commit"],
        "target_repo_dirty": inputs["target_repo_dirty"],
        "contract_hash": inputs["contract_hash"],
        "dev_dataset_hash": inputs["dataset_hashes"].get("dev", ""),
        "validation_dataset_hash": inputs["dataset_hashes"].get("validation", ""),
        "test_dataset_hash": inputs["dataset_hashes"].get("test", ""),
        "dataset_hashes": inputs["dataset_hashes"],
        "ground_truth_hash": inputs["ground_truth_hashes"].get("ground_truth", ""),
        "edge_ground_truth_hash": inputs["ground_truth_hashes"].get("edges", ""),
        "receiver_ground_truth_hash": inputs["ground_truth_hashes"].get("receivers", ""),
        "canonicalization_ground_truth_hash": inputs["ground_truth_hashes"].get("canonicalization", ""),
        "ground_truth_hashes": inputs["ground_truth_hashes"],
        "graph_hash": inputs["graph_hash"],
        "config_hashes": inputs["config_hashes"],
        "candidate_config_hash": inputs["config_hashes"].get("candidate_config", ""),
        "ranker_config_hash": inputs["config_hashes"].get("ranker_config", ""),
        "context_config_hash": inputs["config_hashes"].get("context_config", ""),
        "typeflow_config_hash": inputs["config_hashes"].get("typeflow_config", ""),
        "tokenizer": "cl100k_base_exact_with_header_invariant",
        "environment": env.to_dict(),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    env.manifests_root.mkdir(parents=True, exist_ok=True)
    manifest_path = env.manifests_root / "benchmark_run_manifest.json"
    manifest_path.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")
    print(f"Generated benchmark run manifest at {manifest_path} with Run ID: {expected_run_id}")
    return manifest_path


if __name__ == "__main__":
    generate_benchmark_manifest()
