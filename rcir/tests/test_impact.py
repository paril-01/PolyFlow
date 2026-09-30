"""
Tests for Change Impact Report Generator (v7 §9).
"""

import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rcir.impact import generate_change_impact_report, ChangeImpactReport


def test_generate_impact_report_mock_graph():
    mock_graph = {
        "edges": [
            {
                "source": "src/frontend/rpc.go::insertCart",
                "target": "protos/demo.proto::CartService.AddItem",
                "edge_type": "calls",
                "resolution": "static_exact",
                "reason": "gRPC call",
            },
            {
                "source": "src/checkoutservice/main.go::chargeCard",
                "target": "protos/demo.proto::CartService.AddItem",
                "edge_type": "calls",
                "resolution": "static_inference",
                "reason": "inferred call",
            },
            {
                "source": "src/cartservice/client.py::dynamic_call",
                "target": "protos/demo.proto::CartService.AddItem",
                "edge_type": "calls",
                "resolution": "dynamic_unresolved",
                "reason": "dynamic getattr dispatch",
            },
            {
                "source": "kubernetes-manifests/frontend.yaml::frontend",
                "target": "kubernetes-manifests/cartservice.yaml::cartservice",
                "edge_type": "config_service",
                "resolution": "static_exact",
                "reason": "Config-mediated CART_SERVICE_ADDR",
            },
        ]
    }

    report = generate_change_impact_report(
        repo_path="/tmp/mock_repo",
        target_symbol="CartService.AddItem",
        graph=mock_graph,
    )

    assert report.total_affected_call_sites == 2
    assert report.exact_call_sites == 1
    assert report.inferred_call_sites == 1
    assert report.unresolved_count == 1
    assert len(report.unresolved_locations) == 1
    assert report.unresolved_locations[0].location == "src/cartservice/client.py::dynamic_call"
    assert report.confidence == 0.3333333333333333  # 1 / 3 total evaluated
    assert report.zero_cloud_verified is True

    # Test Markdown rendering
    md = report.to_markdown()
    assert "CHANGE IMPACT REPORT" in md
    assert "Change: CartService.AddItem" in md
    assert "Affected: 2 static call sites (1 exact, 1 inferred)" in md
    assert "Unresolved: 1 — manual review required:" in md
    assert "src/cartservice/client.py::dynamic_call" in md
    assert "Zero-Cloud Verified: PASS" in md

    # Test JSON dict serialization
    d = report.to_dict()
    assert d["target_change"] == "CartService.AddItem"
    assert d["unresolved"]["manual_review_required"] is True
    assert json.dumps(d)
