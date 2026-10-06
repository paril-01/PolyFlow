"""
Unit and regression tests for RCIR v8.5 Stage 2 Submodule & CI Infrastructure (F01).

Verifies:
- .gitmodules exists at repository root and maps gitlinks to valid URLs.
- experiments/nextcloud_validation/nextcloud-server is properly mapped to nextcloud/server.
- git submodule status and sync commands succeed.
- GitHub Actions workflow checkout configurations are consistent and functional.
"""

import subprocess
from pathlib import Path
import pytest

POLYFLOW_ROOT = Path(__file__).resolve().parent.parent


def test_gitmodules_file_exists_and_maps_nextcloud():
    """F01: .gitmodules must exist and declare the submodule URL for nextcloud-server."""
    gitmodules_path = POLYFLOW_ROOT / ".gitmodules"
    assert gitmodules_path.exists(), ".gitmodules missing from repository root"

    content = gitmodules_path.read_text(encoding="utf-8")
    assert 'submodule "experiments/nextcloud_validation/nextcloud-server"' in content
    assert "https://github.com/nextcloud/server.git" in content
    assert "experiments/nextcloud_validation/nextcloud-server" in content


def test_git_submodule_status_succeeds_with_pinned_commit():
    """F01: git submodule status must succeed and report the pinned commit."""
    res = subprocess.run(
        ["git", "submodule", "status"],
        cwd=str(POLYFLOW_ROOT),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"git submodule status failed: {res.stderr}"
    assert "da57df078d0808a7235a0177bd99d23c010b472e" in res.stdout
    assert "experiments/nextcloud_validation/nextcloud-server" in res.stdout


def test_git_submodule_sync_succeeds():
    """F01: git submodule sync must execute cleanly without error."""
    res = subprocess.run(
        ["git", "submodule", "sync"],
        cwd=str(POLYFLOW_ROOT),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"git submodule sync failed: {res.stderr}"


def test_ci_workflows_have_submodules_enabled():
    """F01: All RCIR workflows must checkout with submodules enabled."""
    workflows_dir = POLYFLOW_ROOT / ".github" / "workflows"
    expected_workflows = [
        "rcir-unit.yml",
        "rcir-artifact-integrity.yml",
        "rcir-smoke-benchmark.yml",
        "rcir-full-benchmark.yml",
    ]

    for wf_name in expected_workflows:
        wf_path = workflows_dir / wf_name
        assert wf_path.exists(), f"Workflow missing: {wf_name}"
        content = wf_path.read_text(encoding="utf-8")
        assert "submodules: true" in content, f"{wf_name} missing 'submodules: true'"
