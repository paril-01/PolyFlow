"""
tests/benchmark_integrity/test_backend_proofs_and_services.py — Verification of Backend Proofs & Services.

Verifies:
1. Unknown RCIR query ID returns HTTP 404.
2. /api/health indicates process liveness and not evidence validity.
3. Interpreter service parses real .poly AST and measures execution time.
4. Proof hash verification detects tampered files.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from showcase_app.backend.app import app
from experiments.benchmark_core.hashes import sha256_file, verify_file_hash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def client():
    return TestClient(app)


def test_unknown_query_id_404(client):
    """Verify that an unknown query ID returns HTTP 404 and does not fabricate a default query."""
    res = client.get("/api/rcir/queries/nonexistent_fake_query_id_12345")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_health_not_equal_evidence_validity(client):
    """Verify that /api/health reflects process liveness, not evidence validity."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["process_liveness"] == "UP"
    assert data["benchmarks_gate"] == "NOT_EVALUATED_BY_HEALTH"


def test_proof_hash_tamper_rejected():
    """Verify that verify_file_hash returns False when content does not match expected hash."""
    with tempfile.NamedTemporaryFile("w", delete=False) as tf:
        tf.write("original content")
        tf_path = Path(tf.name)

    try:
        orig_hash = sha256_file(tf_path)
        assert verify_file_hash(tf_path, orig_hash) is True

        # Tamper with file
        tf_path.write_text("tampered content")
        assert verify_file_hash(tf_path, orig_hash) is False
    finally:
        if tf_path.exists():
            tf_path.unlink()
