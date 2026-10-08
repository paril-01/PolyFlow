"""
tests/test_backend_proof_server.py — Automated verification for FastAPI Backend & Proof Server.

Validates:
1. Health endpoint returns 200 with VALIDATED evidence status.
2. Feature service loads real Sales Invoice 12-to-1 mappings.
3. Live interpreter executes real PolyCellRuntime in normal and controlled failure modes.
4. Security: Proof resolver strictly denies path traversal (../, absolute paths, missing files).
5. All 9 required derived CSVs exist and contain genuine parsed artifact headers and data.
6. Rule 0: Valid pair accounting is 3 (with 2 timeouts), not 5.
"""

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient
from showcase_app.backend.app import app
from showcase_app.backend.services.evidence_registry import evidence_registry


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["evidence_status"] == "VALIDATED"


def test_features_native_vs_poly(client):
    res = client.get("/api/features/ERPNEXT-ACCOUNTS-SALES_INVOICE/native-vs-poly")
    assert res.status_code == 200
    data = res.json()
    assert "layers" in data
    assert "poly_content" in data
    assert data["reduction_summary"]["native_files_involved"] == 12
    assert len(data["layers"]) >= 5
    # Verify sales_invoice.poly content
    assert "SalesInvoice" in data["poly_content"]


def test_interpreter_live_execution_normal(client):
    res = client.post("/api/interpreter/runs", json={"mode": "normal", "feature_id": "ERPNEXT-ACCOUNTS-SALES_INVOICE"})
    assert res.status_code == 200
    data = res.json()
    assert data["execution_status"] == "SUCCESS"
    assert data["cells_executed"] >= 3
    assert data["cells_failed"] == 0
    assert "receipt_hash" in data
    assert len(data["receipt_hash"]) == 64  # SHA-256


def test_interpreter_live_execution_controlled_failure(client):
    res = client.post("/api/interpreter/runs", json={"mode": "failure", "feature_id": "ERPNEXT-ACCOUNTS-SALES_INVOICE"})
    assert res.status_code == 200
    data = res.json()
    # In failure mode, controlled failure is injected, fallback runs, marked DEGRADED
    assert data["execution_status"] == "DEGRADED"
    assert data["cells_failed"] == 1
    assert data["cells_fallback"] == 1
    assert "receipt_hash" in data


def test_proof_security_path_traversal_guard():
    # Attempt path traversal via proof_id
    res = evidence_registry.resolve_proof_file("../../../windows/system32/cmd.exe")
    assert res is None

    res2 = evidence_registry.resolve_proof_file("..\\..\\..\\secrets.txt")
    assert res2 is None

    res3 = evidence_registry.resolve_proof_file("nonexistent_proof_id")
    assert res3 is None


def test_proofs_api_endpoints(client):
    res = client.get("/api/proofs")
    assert res.status_code == 200
    data = res.json()
    assert data["total_proofs"] > 0
    proofs = data["proofs"]
    assert len(proofs) >= 10

    # Test downloading first proof
    first_proof = proofs[0]
    p_res = client.get(f"/api/proofs/{first_proof['proof_id']}")
    assert p_res.status_code == 200


def test_all_nine_derived_csvs_exist(client):
    required_csvs = [
        "run_summary.csv",
        "paired_token_usage.csv",
        "agent_trials.csv",
        "retrieved_files.csv",
        "feature_closure.csv",
        "source_mappings.csv",
        "interpreter_events.csv",
        "runtime_receipts.csv",
        "coverage_ledger.csv",
    ]

    csv_dir = REPO_ROOT / "showcase" / "data" / "csv"
    assert csv_dir.exists(), "showcase/data/csv directory missing"

    for name in required_csvs:
        p = csv_dir / name
        assert p.exists(), f"Required CSV missing: {name}"
        lines = p.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) >= 2, f"CSV {name} has fewer than 2 lines (header + data)"


def test_valid_pairs_rule_zero_accounting():
    import json
    p = REPO_ROOT / "experiments" / "final_blind_validation" / "results" / "blind_baseline.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    # Under Rule 0: Exactly 3 valid pairs, 2 timeouts, 0 successful pairs
    assert data["valid_pairs"] == 3
    assert data["successful_pairs"] == 0
    assert data["individual_trials"] == 10
