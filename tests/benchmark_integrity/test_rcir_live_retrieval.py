"""
tests/benchmark_integrity/test_rcir_live_retrieval.py — Verification of Live RCIR Retrieval.

Verifies:
1. LiveRCIRContextProvider performs live retrieval against target repository.
2. Missing graph raises RCIRContextError and never returns a synthetic pass.
3. Missing context raises RCIRContextError and never returns generic fallback hint text.
4. Baseline arm executes with no context provider.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from rcir.context.provider import LiveRCIRContextProvider, RCIRContextError
from orchestrator.tools import RepoToolEnvironment

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_rcir_arm_uses_live_context_provider():
    """Verify that LiveRCIRContextProvider loads the real graph and compiles context."""
    target_repo = REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"
    if not target_repo.exists():
        pytest.skip("Nextcloud server repository not available locally")

    provider = LiveRCIRContextProvider(target_repo=target_repo, token_budget=4000)
    assert provider.graph_path.exists(), "RCIR graph path must exist on disk"
    assert len(provider.raw_graph.get("nodes", {})) > 1000, "Graph must contain nodes"

    # Test live compilation for an instruction
    context_md = provider.compile_task_context(
        task_id="TEST-TASK-01",
        instructions="Implement storage adapter encryption user keys in OCP\\Files",
        token_budget=2000,
    )
    assert context_md, "Compiled context must be nonempty"
    assert provider.last_retrieval_trace["tokens_added"] > 0
    assert provider.last_retrieval_trace["candidate_count"] > 0


def test_rcir_missing_index_invalidates_trial():
    """Verify that a missing graph raises RCIRContextError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_target = Path(tmp_dir) / "fake_repo"
        fake_target.mkdir()

        with pytest.raises(RCIRContextError) as exc_info:
            LiveRCIRContextProvider(target_repo=fake_target, graph_path=Path(tmp_dir) / "missing_graph.json")

        assert "RCIR dependency graph not found" in str(exc_info.value)


def test_rcir_missing_context_never_returns_hint():
    """Verify that an unrecognized symbol raises RCIRContextError instead of returning generic hint text."""
    target_repo = REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"
    if not target_repo.exists():
        pytest.skip("Nextcloud server repository not available locally")

    provider = LiveRCIRContextProvider(target_repo=target_repo, token_budget=4000)
    # Clear raw graph nodes/edges temporarily to simulate zero context found
    empty_provider = LiveRCIRContextProvider.__new__(LiveRCIRContextProvider)
    empty_provider.target_repo = target_repo
    empty_provider.graph_path = provider.graph_path
    super(LiveRCIRContextProvider, empty_provider).__init__(raw_graph={"nodes": {}, "edges": []})
    empty_provider.default_token_budget = 4000
    empty_provider.last_retrieval_trace = {}

    with pytest.raises(RCIRContextError) as exc_info:
        empty_provider.compile_task_context("FAIL-TASK", "RandomNonexistentSymbol12345678")

    assert "zero retrieved context" in str(exc_info.value)


def test_baseline_has_no_rcir_context():
    """Verify that the baseline tool environment operates with no context provider."""
    env = RepoToolEnvironment(repo_root=REPO_ROOT, context_provider=None)
    assert env.context_provider is None
    res = env.request_context("Storage")
    assert "not configured" in res
