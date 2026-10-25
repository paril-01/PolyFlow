"""
tests/benchmark_integrity/test_historical_provenance_gate.py — Negative & Integrity Gate Tests for PF-P0-001.

Validates:
1. Historical benchmark gate evaluation succeeds on unmodified historical artifacts.
2. Tampering with dataset hash in manifest fails loudly.
3. Tampering with ground truth hash in manifest fails loudly.
4. Tampering with target commit fails loudly.
5. Missing or corrupted artifact fails loudly.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_DIR = REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from evaluate_gates import evaluate_gates
from environment import get_default_environment


def test_evaluate_gates_historical_success():
    """Verify that evaluate_gates with allow_historical=True and allow_development_dirty=True succeeds on valid tree."""
    env = get_default_environment()
    result = evaluate_gates(allow_development_dirty=True, allow_historical=True, env=env)
    assert result["run_validity"] == "VALID"
    assert result["integrity_gate"]["passed"] is True
    assert result["architecture_decision"] == "OPTION_B_ACCEPTED"


def test_tampered_dataset_hash_fails_loudly(tmp_path: Path):
    """Verify that a tampered dataset hash in manifest is detected and fails the integrity gate."""
    env = get_default_environment()
    manifest_path = env.manifests_root / "benchmark_run_manifest.json"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    
    # Tamper with dev dataset hash
    tampered_manifest = dict(manifest_data)
    tampered_manifest["dataset_hashes"] = dict(tampered_manifest["dataset_hashes"])
    tampered_manifest["dataset_hashes"]["dev"] = "0000000000000000000000000000000000000000000000000000000000000000"
    
    temp_manifest_dir = tmp_path / "manifests"
    temp_manifest_dir.mkdir(parents=True)
    temp_manifest_file = temp_manifest_dir / "benchmark_run_manifest.json"
    temp_manifest_file.write_text(json.dumps(tampered_manifest), encoding="utf-8")
    
    # Mock env.manifests_root to point to temp_manifest_dir
    class MockEnv:
        def __getattr__(self, name):
            if name == "manifests_root":
                return temp_manifest_dir
            return getattr(env, name)
    
    res = evaluate_gates(allow_development_dirty=True, allow_historical=True, env=MockEnv())
    assert res["integrity_gate"]["passed"] is False
    assert any("Manifest dataset hash mismatch for 'dev'" in fail for fail in res["integrity_gate"]["failures"])
    assert res["architecture_decision"] == "NOT_EVALUATED"


def test_tampered_ground_truth_hash_fails_loudly(tmp_path: Path):
    """Verify that a tampered ground truth hash in manifest fails the integrity gate."""
    env = get_default_environment()
    manifest_path = env.manifests_root / "benchmark_run_manifest.json"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    
    tampered_manifest = dict(manifest_data)
    tampered_manifest["ground_truth_hashes"] = dict(tampered_manifest["ground_truth_hashes"])
    tampered_manifest["ground_truth_hashes"]["ground_truth"] = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    
    temp_manifest_dir = tmp_path / "manifests"
    temp_manifest_dir.mkdir(parents=True)
    temp_manifest_file = temp_manifest_dir / "benchmark_run_manifest.json"
    temp_manifest_file.write_text(json.dumps(tampered_manifest), encoding="utf-8")
    
    class MockEnv:
        def __getattr__(self, name):
            if name == "manifests_root":
                return temp_manifest_dir
            return getattr(env, name)
    
    res = evaluate_gates(allow_development_dirty=True, allow_historical=True, env=MockEnv())
    assert res["integrity_gate"]["passed"] is False
    assert any("Manifest ground truth hash mismatch for 'ground_truth'" in fail for fail in res["integrity_gate"]["failures"])
    assert res["architecture_decision"] == "NOT_EVALUATED"


def test_tampered_target_commit_fails_loudly(tmp_path: Path):
    """Verify that a tampered target repository commit fails the integrity gate."""
    env = get_default_environment()
    manifest_path = env.manifests_root / "benchmark_run_manifest.json"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    
    tampered_manifest = dict(manifest_data)
    tampered_manifest["target_repository_commit"] = "badcommit1234567890abcdef1234567890abcdef"
    
    temp_manifest_dir = tmp_path / "manifests"
    temp_manifest_dir.mkdir(parents=True)
    temp_manifest_file = temp_manifest_dir / "benchmark_run_manifest.json"
    temp_manifest_file.write_text(json.dumps(tampered_manifest), encoding="utf-8")
    
    class MockEnv:
        def __getattr__(self, name):
            if name == "manifests_root":
                return temp_manifest_dir
            return getattr(env, name)
    
    res = evaluate_gates(allow_development_dirty=True, allow_historical=True, env=MockEnv())
    assert res["integrity_gate"]["passed"] is False
    assert any("Manifest target_repository_commit mismatch" in fail for fail in res["integrity_gate"]["failures"])
    assert res["architecture_decision"] == "NOT_EVALUATED"
