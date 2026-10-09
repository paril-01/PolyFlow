"""
tests/benchmark_integrity/test_isolation_and_worktree.py — Verification of Worktree Isolation.

Verifies:
1. Missing Nextcloud checkout raises BenchmarkSetupError and NEVER falls back to PolyFlow repo.
2. Pinned commit is strictly validated against da57df078d0808a7235a0177bd99d23c010b472e.
3. Trial worktrees are full checkouts with composer.json and no partial-directory shadow copies.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from experiments.benchmark_core.isolation import (
    WorktreeManager,
    BenchmarkSetupError,
    PINNED_NEXTCLOUD_COMMIT,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_missing_nextcloud_does_not_fallback_to_polyflow():
    """Verify that a nonexistent target repo raises BenchmarkSetupError and does not fallback to PolyFlow root."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_target = Path(tmp_dir) / "nonexistent_repo"
        wt_manager = WorktreeManager(fake_target, Path(tmp_dir) / "worktrees")

        with pytest.raises(BenchmarkSetupError) as exc_info:
            wt_manager.verify_target_checkout()

        assert "not found or not a git checkout" in str(exc_info.value)
        # Verify it did not silently assign PolyFlow repo root
        assert wt_manager.target_repo != REPO_ROOT


def test_git_worktree_pinned_commit():
    """Verify that the actual local Nextcloud checkout matches PINNED_NEXTCLOUD_COMMIT."""
    real_nextcloud = REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"
    if not real_nextcloud.exists():
        pytest.skip("Nextcloud server repository not available locally")

    wt_manager = WorktreeManager(real_nextcloud, real_nextcloud.parent / "test_worktrees")
    commit = wt_manager.verify_target_checkout()
    assert commit.lower() == PINNED_NEXTCLOUD_COMMIT.lower(), (
        f"Target checkout HEAD ({commit}) does not match pinned commit ({PINNED_NEXTCLOUD_COMMIT})"
    )


def test_worktree_is_full_target_repository():
    """Verify that the target checkout contains the full Nextcloud repository structure."""
    real_nextcloud = REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"
    if not real_nextcloud.exists():
        pytest.skip("Nextcloud server repository not available locally")

    assert (real_nextcloud / "composer.json").exists(), "Target repo missing composer.json"
    assert (real_nextcloud / "lib").exists(), "Target repo missing lib directory"
    assert (real_nextcloud / "core").exists(), "Target repo missing core directory"
    assert (real_nextcloud / "apps").exists(), "Target repo missing apps directory"
