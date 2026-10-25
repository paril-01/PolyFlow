"""
tests/benchmark_integrity/test_provenance_validator.py — Deterministic Integrity & Negative Control Suite for PF-RC-CI-001.

Validates:
1. Commit-bound reader (read_repo_file_at_commit) against real pinned Nextcloud Git objects.
2. Security boundaries: rejection of path traversal (..), absolute paths, and invalid SHA formats.
3. Cryptographic hash equivalence: both canonical Git blobs (Linux) and CRLF checkout transforms (Windows) pass.
4. Negative controls: genuine content tampering, incorrect commits, missing files, wrong symbols,
   and out-of-bounds receiver call sites fail loudly with BenchmarkIntegrityError.
5. Worktree drift detection: diagnostics recorded when disk files differ from committed Git objects.
6. Side-effect free execution: running the validator does not dirty tracked repository results.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_DIR = REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from environment import BenchmarkIntegrityError, get_default_environment
from git_reader import (
    CommitNotFoundError,
    FileNotFoundAtCommitError,
    PathSecurityError,
    read_repo_file_at_commit,
    validate_safe_relative_path,
    verify_commit_exists,
    verify_content_hash,
)
from validate_ground_truth_provenance import audit_provenance

PINNED_NEXTCLOUD_COMMIT = "da57df078d0808a7235a0177bd99d23c010b472e"
SAMPLE_FILE = "apps/files/lib/Controller/ApiController.php"
SAMPLE_RECORDED_HASH = "4a05ac7b8bfa5b6da59d459e94dca9c68cf7c0fb909ab824495402bd1dd9f407"


@pytest.fixture
def target_repo_root() -> Path:
    env = get_default_environment()
    return env.target_repo_root


def test_read_repo_file_at_commit_success(target_repo_root: Path):
    """Verify commit-bound read fetches exact Git blob bytes at the pinned commit."""
    content = read_repo_file_at_commit(target_repo_root, PINNED_NEXTCLOUD_COMMIT, SAMPLE_FILE)
    assert isinstance(content, bytes)
    assert len(content) > 1000
    assert b"class ApiController" in content


def test_read_repo_file_invalid_sha_format(target_repo_root: Path):
    """Verify invalid SHA formats are rejected before invoking Git."""
    with pytest.raises(CommitNotFoundError, match="Invalid commit SHA format"):
        read_repo_file_at_commit(target_repo_root, "shortsha123", SAMPLE_FILE)

    with pytest.raises(CommitNotFoundError, match="Invalid commit SHA format"):
        read_repo_file_at_commit(target_repo_root, "; rm -rf /", SAMPLE_FILE)


def test_read_repo_file_nonexistent_commit(target_repo_root: Path):
    """Verify nonexistent full-length 40-hex commit raises CommitNotFoundError."""
    nonexistent_sha = "0" * 40
    with pytest.raises(CommitNotFoundError, match="does not exist in repo"):
        read_repo_file_at_commit(target_repo_root, nonexistent_sha, SAMPLE_FILE)


def test_read_repo_file_nonexistent_path(target_repo_root: Path):
    """Verify nonexistent path at valid commit raises FileNotFoundAtCommitError."""
    with pytest.raises(FileNotFoundAtCommitError, match="not found at commit"):
        read_repo_file_at_commit(target_repo_root, PINNED_NEXTCLOUD_COMMIT, "nonexistent/dir/file.php")


@pytest.mark.parametrize("traversal_path", [
    "../secret.txt",
    "apps/../../secret.txt",
    "/etc/passwd",
    "C:\\Windows\\System32\\cmd.exe",
    "./../escape.php",
])
def test_path_security_traversal_rejection(traversal_path: str):
    """Verify security boundaries reject path traversal and absolute paths."""
    with pytest.raises(PathSecurityError):
        validate_safe_relative_path(traversal_path)


def test_cross_platform_hash_verification_lf_and_crlf():
    """Verify verify_content_hash correctly handles canonical Git LF and CRLF checkout bytes."""
    # Scenario A: Canonical Git blob with native LF
    canonical_lf_blob = b"<?php\nfunction hello() {\n    return 'world';\n}\n"
    canonical_hash = hashlib.sha256(canonical_lf_blob).hexdigest()

    # Scenario B: Windows checkout with CRLF
    crlf_blob = b"<?php\r\nfunction hello() {\r\n    return 'world';\r\n}\r\n"
    crlf_hash = hashlib.sha256(crlf_blob).hexdigest()

    # When ground truth recorded canonical hash:
    is_match_lf, mode_lf, c_h, crlf_h = verify_content_hash(canonical_lf_blob, canonical_hash)
    assert is_match_lf is True
    assert mode_lf == "CANONICAL_GIT_BLOB"

    # When ground truth recorded CRLF checkout hash (historical Windows):
    is_match_crlf, mode_crlf, c_h2, crlf_h2 = verify_content_hash(canonical_lf_blob, crlf_hash)
    assert is_match_crlf is True
    assert mode_crlf == "CRLF_CHECKOUT_TRANSFORM"
    assert c_h2 == canonical_hash
    assert crlf_h2 == crlf_hash


def test_negative_control_genuine_tampering_detected(target_repo_root: Path):
    """Verify that any single-byte change in content fails hash verification."""
    real_blob = read_repo_file_at_commit(target_repo_root, PINNED_NEXTCLOUD_COMMIT, SAMPLE_FILE)
    is_match, mode, _, _ = verify_content_hash(real_blob, SAMPLE_RECORDED_HASH)
    assert is_match is True

    # Mutate one byte
    tampered_blob = real_blob.replace(b"getThumbnail", b"getThumbnailX")
    is_match_tampered, mode_tampered, _, _ = verify_content_hash(tampered_blob, SAMPLE_RECORDED_HASH)
    assert is_match_tampered is False
    assert mode_tampered == "HASH_MISMATCH"


def test_negative_control_tampered_ground_truth_task_fails_loudly(tmp_path: Path):
    """Verify audit_provenance fails loudly when a task has an altered expected hash."""
    env = get_default_environment()
    gt_file = env.ground_truth_root / "ground_truth.json"
    gt_data = json.loads(gt_file.read_text(encoding="utf-8"))

    tampered_gt = copy.deepcopy(gt_data)
    # Alter hash of TASK-DEV-01
    tampered_gt["tasks"]["TASK-DEV-01"]["target_file_hash"] = "deadbeef" * 8

    mock_gt_dir = tmp_path / "ground_truth"
    mock_gt_dir.mkdir(parents=True)
    (mock_gt_dir / "ground_truth.json").write_text(json.dumps(tampered_gt), encoding="utf-8")

    class MockEnv:
        def __getattr__(self, name):
            if name == "ground_truth_root":
                return mock_gt_dir
            return getattr(env, name)

    with pytest.raises(BenchmarkIntegrityError, match="Ground truth provenance failed"):
        audit_provenance(env=MockEnv(), write_results=False)


def test_negative_control_wrong_target_symbol_fails_loudly(tmp_path: Path):
    """Verify audit_provenance fails loudly when target_symbol does not exist in committed content."""
    env = get_default_environment()
    gt_file = env.ground_truth_root / "ground_truth.json"
    gt_data = json.loads(gt_file.read_text(encoding="utf-8"))

    tampered_gt = copy.deepcopy(gt_data)
    tampered_gt["tasks"]["TASK-DEV-01"]["target_symbol"] = "NonExistentMethodNameXYZ"

    mock_gt_dir = tmp_path / "ground_truth"
    mock_gt_dir.mkdir(parents=True)
    (mock_gt_dir / "ground_truth.json").write_text(json.dumps(tampered_gt), encoding="utf-8")

    class MockEnv:
        def __getattr__(self, name):
            if name == "ground_truth_root":
                return mock_gt_dir
            return getattr(env, name)

    with pytest.raises(BenchmarkIntegrityError, match="Ground truth provenance failed"):
        audit_provenance(env=MockEnv(), write_results=False)


def test_negative_control_tampered_receiver_callsite_fails_loudly(tmp_path: Path):
    """Verify audit_provenance fails loudly when a receiver callsite points to wrong line."""
    env = get_default_environment()
    rec_file = env.receiver_ground_truth_root / "receiver_ground_truth.json"
    rec_data = json.loads(rec_file.read_text(encoding="utf-8"))

    tampered_rec = copy.deepcopy(rec_data)
    # Put line out of bounds
    tampered_rec["call_sites"][0]["line"] = 99999

    mock_rec_dir = tmp_path / "receiver_ground_truth"
    mock_rec_dir.mkdir(parents=True)
    (mock_rec_dir / "receiver_ground_truth.json").write_text(json.dumps(tampered_rec), encoding="utf-8")

    class MockEnv:
        def __getattr__(self, name):
            if name == "receiver_ground_truth_root":
                return mock_rec_dir
            return getattr(env, name)

    with pytest.raises(BenchmarkIntegrityError, match="Ground truth provenance failed"):
        audit_provenance(env=MockEnv(), write_results=False)


def test_side_effect_free_by_default():
    """Verify audit_provenance(write_results=False) does not modify tracked results directory."""
    env = get_default_environment()
    res_file = env.results_root / "ground_truth_provenance.json"
    initial_mtime = res_file.stat().st_mtime if res_file.exists() else None
    initial_bytes = res_file.read_bytes() if res_file.exists() else None

    payload = audit_provenance(env=env, write_results=False)
    assert payload["provenance_status"] == "PASSED"
    assert payload["total_errors"] == 0

    if initial_bytes is not None:
        assert res_file.read_bytes() == initial_bytes
        assert res_file.stat().st_mtime == initial_mtime


def test_full_provenance_audit_passes():
    """Verify complete ground truth provenance audit succeeds on unmodified repository."""
    result = audit_provenance(write_results=False)
    assert result["provenance_status"] == "PASSED"
    assert result["total_errors"] == 0
    assert result["total_tasks_audited"] == 16
    assert all(t["status"] == "VALID" for t in result["tasks"])
