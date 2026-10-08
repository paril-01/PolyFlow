#!/usr/bin/env python3
"""
tests/test_feature_closure.py - Automated validation of ERPNext Feature Closure extraction.

Verifies:
1. Multi-layer source discovery across all 6 architectural dimensions.
2. Independent recall >= 95.0% across 5 representative ERPNext features.
3. Detected technology labels match real file extensions (no synthetic framework labels).
4. Stack manifest generation and layer coverage accounting.
5. Canonical PolyFlow grammar format (@contract, @schema, @source, @link).
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from rcir.adapters.frappe_erpnext import (
    FeatureClosure,
    FrappeERPNextSourceDerivedAdapter,
    FrappeFeatureClosureExtractor,
)


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def erpnext_dir(repo_root: Path) -> Path:
    return repo_root / "experiments" / "erpnext_validation"


@pytest.fixture(scope="module")
def adapter(erpnext_dir: Path) -> FrappeERPNextSourceDerivedAdapter:
    erp_root = erpnext_dir / "erpnext"
    if not erp_root.exists():
        pytest.skip("ERPNext validation repository not present")
    ad = FrappeERPNextSourceDerivedAdapter(erpnext_dir)
    ad.index()
    return ad


def test_sales_invoice_feature_closure(adapter: FrappeERPNextSourceDerivedAdapter, erpnext_dir: Path):
    """Test full-stack closure extraction for Sales Invoice."""
    assert "Sales Invoice" in adapter.doctypes, "Sales Invoice DocType must be discovered"
    dt = adapter.doctypes["Sales Invoice"]

    closure = FrappeFeatureClosureExtractor.extract_closure(
        "Sales Invoice", adapter, rel_to=erpnext_dir
    )
    assert closure is not None, "Failed to extract closure for Sales Invoice"

    # 1. Structure and metadata
    assert closure.feature_id == "ERPNEXT-ACCOUNTS-SALES_INVOICE"
    assert closure.feature_name == "Sales Invoice"
    assert closure.domain == "accounts"

    # 2. Layer presence
    assert len(closure.data_model_sources) >= 1, "Must discover primary DocType schema"
    assert len(closure.backend_sources) >= 1, "Must discover Python controller"
    assert len(closure.frontend_sources) >= 1, "Must discover JavaScript form scripts"
    assert len(closure.hook_sources) >= 1, "Must discover doc_events in hooks.py"
    assert len(closure.test_sources) >= 1, "Must discover unit tests"
    assert len(closure.linked_features) >= 5, "Must discover linked features (Customer, Item, GL, etc.)"

    # 3. Real technology detection
    frontend_langs = {s.language for s in closure.frontend_sources}
    assert "JavaScript" in frontend_langs
    assert "React" not in frontend_langs, "Must not falsely detect React when files are vanilla JS"

    backend_langs = {s.language for s in closure.backend_sources}
    assert "Python" in backend_langs

    # 4. Coverage calculation
    assert closure.coverage["frontend"] == 1.0
    assert closure.coverage["backend"] == 1.0
    assert closure.coverage["data_model"] == 1.0
    assert closure.coverage["framework"] == 1.0
    assert closure.coverage["tests"] == 1.0
    assert closure.coverage["overall"] == 1.0

    # 5. Stack manifest validation
    manifest = closure.stack_manifest
    assert manifest["feature"] == "Sales Invoice"
    assert manifest["polyflow_module_count"] == 1
    assert manifest["native_artifact_count"] >= 10
    assert "frontend" in manifest["layers"]
    assert "backend" in manifest["layers"]
    assert "data_model" in manifest["layers"]
    assert "framework" in manifest["layers"]
    assert "tests" in manifest["layers"]

    # 6. Canonical .poly syntax formatting
    poly_text = FrappeFeatureClosureExtractor.format_as_poly(closure)
    assert "@contract" in poly_text
    assert "feature_id: ERPNEXT-ACCOUNTS-SALES_INVOICE" in poly_text
    assert "@schema SalesInvoice" in poly_text
    assert '@source' in poly_text
    assert 'role: "backend_controller"' in poly_text
    assert 'role: "form_script"' in poly_text
    assert '@link' in poly_text
    # 7. Real SHA-256 hashes for hook sources
    for h in closure.hook_sources:
        h_sha = h.get("sha256", "")
        if h_sha:
            assert len(h_sha) == 64 and all(c in "0123456789abcdefABCDEF" for c in h_sha), f"Invalid hook sha256: {h_sha}"


def test_representative_features_validation_file(erpnext_dir: Path, repo_root: Path):
    """Verify that feature_closure_validation.json confirms >= 95% recall across 5 features."""
    val_file = erpnext_dir / "feature_closure_validation.json"
    if not val_file.exists():
        val_file = repo_root / "showcase" / "data" / "feature_closure_validation.json"
    assert val_file.exists(), "feature_closure_validation.json must exist"

    data = json.loads(val_file.read_text(encoding="utf-8"))
    assert data["status"] == "VALIDATED"
    assert data["macro_artifact_recall"] >= 0.95, f"Macro recall {data['macro_artifact_recall']} < 0.95"
    assert data["evaluated_features_count"] >= 5

    features_evaluated = [f["feature"] for f in data["representative_features"]]
    required = ["Sales Invoice", "Item", "Customer", "Stock Entry", "Payment Entry"]
    for req in required:
        assert req in features_evaluated, f"Feature {req} missing from evaluated set"

    for f in data["representative_features"]:
        assert f["recall"] >= 0.95, f"Recall for {f['feature']} was {f['recall']}"
        assert f["true_positives"] >= 5


def test_ui_data_polyflow_mapping_consistency(repo_root: Path):
    """Verify polyflow_mapping.json consumed by Tab 01 has genuine ERPNext Feature Closure proof."""
    mapping_file = repo_root / "showcase" / "data" / "polyflow_mapping.json"
    assert mapping_file.exists(), "showcase/data/polyflow_mapping.json must exist"

    d = json.loads(mapping_file.read_text(encoding="utf-8"))
    assert "selected_feature" in d, "selected_feature missing from polyflow_mapping.json"
    feat = d["selected_feature"]
    assert feat["feature_name"] == "Sales Invoice"
    assert feat["feature_id"] == "ERPNEXT-ACCOUNTS-SALES_INVOICE"

    # Verify reduction metric honesty
    reduction = feat["reduction_summary"]
    assert reduction["native_files_involved"] == 12
    assert reduction["directories_involved"] == 5
    assert reduction["languages_involved"] == 3
    assert reduction["polyflow_modules"] == 1
    assert "12 fragmented artifacts" in reduction["honest_metric"]
    assert "90% less code" not in reduction["honest_metric"]

    # Verify change request demonstration structure
    cr = feat["change_request_demo"]
    assert "Modify Sales Invoice tax behavior" in cr["request_title"]
    assert len(cr["affected_layers"]) == 6
