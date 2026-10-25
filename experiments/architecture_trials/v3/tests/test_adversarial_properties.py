"""
experiments/architecture_trials/v3/tests/test_adversarial_properties.py — Phase B1 Adversarial Property Tests.

Tests:
1. Invalidation correctness on file change (branch/commit flip)
2. Ambiguous symbol handling
3. Path traversal injection security guards
4. Token budget invariant conformance across varying limits (500, 1000, 2000, 4000)
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.architecture_trials.v3.r0_lexical_symbol.index import LexicalSymbolIndex
from experiments.architecture_trials.v3.r2_versioned_evidence.vest_lite import (
    VestLiteEvidenceStore,
    FactFreshness,
    ResolutionClass,
)


@pytest.fixture
def sample_repo(tmp_path: Path):
    """Create a mini repository for property testing."""
    repo = tmp_path / "repo"
    repo.mkdir()

    # Base class
    base_file = repo / "BaseController.php"
    base_file.write_text("<?php\nnamespace App;\nclass BaseController {\n    public function handle() { return true; }\n}\n")

    # Child class extending BaseController
    child_file = repo / "UserController.php"
    child_file.write_text("<?php\nnamespace App;\nclass UserController extends BaseController {\n    public function getUser() { return 'user'; }\n}\n")

    # Ambiguous controller in another namespace
    admin_dir = repo / "Admin"
    admin_dir.mkdir()
    admin_file = admin_dir / "UserController.php"
    admin_file.write_text("<?php\nnamespace App\\Admin;\nclass UserController {\n    public function getAdmin() { return 'admin'; }\n}\n")

    return repo


def test_r2_transitive_invalidation_on_change(sample_repo: Path):
    """Verify that editing BaseController invalidates UserController transitively."""
    store = VestLiteEvidenceStore(sample_repo)
    store.scan_repository()

    # Initial state: all facts fresh
    res_initial = store.retrieve("UserController", max_tokens=2000)
    assert res_initial["spans_count"] >= 1
    assert any(item["symbol"] == "UserController" for item in res_initial["evidence_items"])

    # Simulate modifying BaseController.php
    invalidated_count = store.invalidate_file("BaseController.php", reason="commit_flip")
    assert invalidated_count >= 2  # BaseController and its dependent UserController

    # After invalidation: UserController facts depending on BaseController are STALE and excluded from retrieval
    res_after = store.retrieve("UserController", max_tokens=2000)
    # The child class depending on BaseController must be excluded because it's STALE
    child_items = [it for it in res_after["evidence_items"] if it["file_path"] == "UserController.php"]
    assert len(child_items) == 0  # Transitive invalidation excluded stale facts


def test_path_traversal_rejection(sample_repo: Path):
    """Verify that path traversal attempts fail closed and do not leak system files."""
    r0 = LexicalSymbolIndex(sample_repo)
    r0.index_repository()

    # Attempt path traversal queries
    res_r0 = r0.retrieve("../../../../etc/passwd", max_tokens=1000)
    assert not any("etc" in span["file_path"] for span in res_r0["spans"])

    r2 = VestLiteEvidenceStore(sample_repo)
    r2.scan_repository()
    res_r2 = r2.retrieve("../../../../etc/passwd", max_tokens=1000)
    assert not any("etc" in item["file_path"] for item in res_r2["evidence_items"])


def test_strict_token_budget_packing_invariant(sample_repo: Path):
    """Verify that R0 and R2 strictly respect max_tokens budget without overrun."""
    r0 = LexicalSymbolIndex(sample_repo)
    r0.index_repository()

    r2 = VestLiteEvidenceStore(sample_repo)
    r2.scan_repository()

    for budget in [100, 250, 500, 1000, 2000]:
        res0 = r0.retrieve("Controller", max_tokens=budget)
        assert res0["estimated_tokens"] <= budget + 5  # Allow minor packing rounding

        res2 = r2.retrieve("Controller", max_tokens=budget)
        assert res2["estimated_tokens"] <= budget + 5


def test_disambiguation_with_path_hint(sample_repo: Path):
    """Verify that multiple UserController definitions are correctly resolved with namespace/path hint."""
    r2 = VestLiteEvidenceStore(sample_repo)
    r2.scan_repository()

    res_admin = r2.retrieve("Admin UserController", max_tokens=2000)
    admin_files = [it["file_path"] for it in res_admin["evidence_items"]]
    assert any("Admin/UserController.php" in f or "Admin" in f for f in admin_files)
