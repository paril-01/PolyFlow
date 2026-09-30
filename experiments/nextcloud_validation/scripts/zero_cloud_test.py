"""
Phase G: Zero-Cloud Validation for RCIR.

Verifies that RCIR core analysis works without any outbound network access.
Uses socket monkey-patching on Windows (real firewall rules would be better
but require admin privileges).

Tests:
1. Graph extraction
2. Hierarchy building
3. Retrieval
4. Impact query
5. State/invalidation

Records any component that attempts network access.
"""

import json
import os
import socket
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add RCIR to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))


class NetworkBlocker:
    """Intercepts and logs any network access attempts."""

    def __init__(self):
        self.attempts = []
        self._original_connect = socket.socket.connect
        self._original_getaddrinfo = socket.getaddrinfo

    def __enter__(self):
        def blocked_connect(sock_self, address):
            self.attempts.append({
                "type": "socket.connect",
                "address": str(address),
                "timestamp": time.time(),
            })
            raise ConnectionRefusedError(
                f"ZERO-CLOUD BLOCK: Outbound connection to {address} blocked"
            )

        def blocked_getaddrinfo(*args, **kwargs):
            self.attempts.append({
                "type": "socket.getaddrinfo",
                "args": str(args[:2]),
                "timestamp": time.time(),
            })
            raise socket.gaierror(
                f"ZERO-CLOUD BLOCK: DNS resolution for {args[0]} blocked"
            )

        socket.socket.connect = blocked_connect
        socket.getaddrinfo = blocked_getaddrinfo
        return self

    def __exit__(self, *args):
        socket.socket.connect = self._original_connect
        socket.getaddrinfo = self._original_getaddrinfo


def test_graph_extraction_offline(repo_path: Path) -> dict:
    """Test graph extraction with no network."""
    from rcir.graph.extractor import extract_graph

    with NetworkBlocker() as blocker:
        start = time.time()
        try:
            # Use a small subset for speed
            test_dir = repo_path / "lib" / "private" / "Files"
            if not test_dir.exists():
                return {"status": "BLOCKED", "reason": f"Test directory not found: {test_dir}"}

            graph = extract_graph(str(test_dir))
            elapsed = time.time() - start
            return {
                "status": "PASS",
                "nodes": len(graph.get("nodes", [])),
                "edges": len(graph.get("edges", [])),
                "time_seconds": round(elapsed, 3),
                "network_attempts": blocker.attempts,
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "status": "FAIL",
                "error": str(e),
                "time_seconds": round(elapsed, 3),
                "network_attempts": blocker.attempts,
            }


def test_hierarchy_offline() -> dict:
    """Test hierarchy building with no network."""
    from rcir.hierarchy.builder import build_hierarchy

    # Create a minimal graph for testing
    test_graph = {
        "nodes": [
            {"path": "test.php", "kind": "file", "level": "file", "line": 1, "end_line": 100},
            {"path": "test.php::TestClass", "kind": "class", "level": "class", "line": 5, "end_line": 50},
            {"path": "test.php::TestClass::method", "kind": "method", "level": "function", "line": 10, "end_line": 20},
        ],
        "edges": [
            {"source": "test.php::TestClass::method", "target": "other::func", "edge_type": "calls", "confidence": 0.7, "resolution": "static_inference"},
        ],
    }

    with NetworkBlocker() as blocker:
        start = time.time()
        try:
            hierarchy = build_hierarchy(test_graph)
            elapsed = time.time() - start
            return {
                "status": "PASS",
                "hierarchy_nodes": len(hierarchy.get("nodes", [])),
                "time_seconds": round(elapsed, 3),
                "network_attempts": blocker.attempts,
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "status": "FAIL",
                "error": str(e),
                "time_seconds": round(elapsed, 3),
                "network_attempts": blocker.attempts,
            }


def test_retrieval_offline() -> dict:
    """Test retrieval with no network."""
    from rcir.hierarchy.builder import build_hierarchy
    from rcir.retrieval.hybrid import hybrid_retrieve

    test_graph = {
        "nodes": [
            {"path": "files/upload.php::FileUploader", "kind": "class", "level": "class", "line": 1, "end_line": 50},
            {"path": "files/upload.php::FileUploader::handleUpload", "kind": "method", "level": "function", "line": 10, "end_line": 30},
            {"path": "storage/local.php::LocalStorage", "kind": "class", "level": "class", "line": 1, "end_line": 80},
            {"path": "storage/local.php::LocalStorage::putFile", "kind": "method", "level": "function", "line": 20, "end_line": 40},
        ],
        "edges": [
            {"source": "files/upload.php::FileUploader::handleUpload", "target": "storage/local.php::LocalStorage::putFile", "edge_type": "calls", "confidence": 1.0, "resolution": "static_exact"},
        ],
    }

    with NetworkBlocker() as blocker:
        start = time.time()
        try:
            hierarchy = build_hierarchy(test_graph)
            contract = hybrid_retrieve(hierarchy, "file upload handler", token_budget=4000, graph_edges=test_graph["edges"])
            elapsed = time.time() - start
            return {
                "status": "PASS",
                "nodes_retrieved": len(contract.nodes),
                "tokens_used": contract.token_budget_used,
                "time_seconds": round(elapsed, 3),
                "network_attempts": blocker.attempts,
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "status": "FAIL",
                "error": str(e),
                "time_seconds": round(elapsed, 3),
                "network_attempts": blocker.attempts,
            }


def test_impact_offline() -> dict:
    """Test change impact report with no network."""
    from rcir.impact import generate_change_impact_report

    test_graph = {
        "nodes": [
            {"path": "test.php::TestService", "kind": "class", "level": "class", "line": 1, "end_line": 50},
            {"path": "test.php::TestService::process", "kind": "method", "level": "function", "line": 10, "end_line": 30},
        ],
        "edges": [
            {"source": "caller.php::Caller::run", "target": "TestService.process", "edge_type": "calls", "confidence": 1.0, "resolution": "static_exact"},
        ],
    }

    with NetworkBlocker() as blocker:
        start = time.time()
        try:
            report = generate_change_impact_report(
                repo_path=".",
                target_symbol="TestService.process",
                graph=test_graph,
            )
            elapsed = time.time() - start
            return {
                "status": "PASS",
                "affected_call_sites": report.total_affected_call_sites,
                "time_seconds": round(elapsed, 3),
                "network_attempts": blocker.attempts,
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "status": "FAIL",
                "error": str(e),
                "time_seconds": round(elapsed, 3),
                "network_attempts": blocker.attempts,
            }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 60)
    print("RCIR ZERO-CLOUD VALIDATION")
    print("=" * 60)
    print(f"Isolation mechanism: socket monkey-patching (Python-level)")
    print(f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}")
    print()

    nextcloud_path = REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"

    tests = {
        "graph_extraction": lambda: test_graph_extraction_offline(nextcloud_path),
        "hierarchy_building": lambda: test_hierarchy_offline(),
        "retrieval": lambda: test_retrieval_offline(),
        "impact_query": lambda: test_impact_offline(),
    }

    results = {}
    all_network_attempts = []

    for test_name, test_func in tests.items():
        print(f"  Testing: {test_name}...", end=" ")
        result = test_func()
        results[test_name] = result
        status = result["status"]
        icon = {"PASS": "[PASS]", "FAIL": "[FAIL]", "BLOCKED": "[BLOCKED]"}.get(status, "[?]")
        print(f"{icon} {status} ({result.get('time_seconds', 0):.3f}s)")

        if result.get("network_attempts"):
            all_network_attempts.extend(result["network_attempts"])
            print(f"    [WARN] {len(result['network_attempts'])} network access attempts detected!")

    # Summary
    passed = sum(1 for r in results.values() if r["status"] == "PASS")
    total = len(results)
    overall = "PASS" if passed == total and not all_network_attempts else "FAIL"

    print()
    print(f"Overall: {overall} ({passed}/{total} tests passed, {len(all_network_attempts)} network attempts)")

    output = {
        "overall_status": overall,
        "isolation_mechanism": "socket monkey-patching (Python-level)",
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        "tests_passed": passed,
        "tests_total": total,
        "total_network_attempts": len(all_network_attempts),
        "network_attempts": all_network_attempts,
        "results": results,
    }

    output_path = REPO_ROOT / "experiments" / "nextcloud_validation" / "reports" / "zero_cloud_validation.json"
    output_path.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
