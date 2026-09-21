"""
Zero-cloud standalone check for CI (v7 §3).

Verifies the core claim: RCIR's core analysis path (graph extraction,
hierarchy building, invalidation, retrieval) runs correctly with ALL
outbound network interfaces blocked.

Exit code:
  0 = Passed (zero network calls attempted)
  1 = Failed (network socket connection attempted)

Run:
  python rcir/ci/zero_cloud_check.py
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Ensure src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rcir.graph.extractor import extract_graph
from rcir.hierarchy.builder import build_hierarchy
from rcir.retrieval.hybrid import hybrid_retrieve
from rcir.state.diff import diff_file


class NetworkBlockedError(Exception):
    """Raised when code attempts a network connection during zero-cloud check."""
    pass


class _BlockedSocket:
    """Socket replacement that raises on any connection attempt."""

    def __init__(self, *args, **kwargs):
        raise NetworkBlockedError(
            "ZERO-CLOUD VIOLATION: code attempted to create a network socket "
            "during the core analysis path. This violates RCIR's zero-cloud "
            "claim (v7 §3)."
        )


def _build_sample_repo(base_dir: Path) -> Path:
    """Create a sample multi-file project with classes, calls, and proto."""
    pkg = base_dir / "sample_service"
    pkg.mkdir(parents=True, exist_ok=True)

    (pkg / "__init__.py").write_text("", encoding="utf-8")

    (pkg / "models.py").write_text('''
class Order:
    def __init__(self, order_id: str, amount: float):
        self.order_id = order_id
        self.amount = amount

    def is_valid(self) -> bool:
        return self.amount > 0
''', encoding="utf-8")

    (pkg / "service.py").write_text('''
from sample_service.models import Order

def process_order(order_id: str, amount: float) -> dict:
    order = Order(order_id, amount)
    if not order.is_valid():
        raise ValueError("Invalid amount")
    return {"id": order.order_id, "status": "processed"}
''', encoding="utf-8")

    (pkg / "order.proto").write_text('''
syntax = "proto3";
service OrderService {
    rpc ProcessOrder(OrderRequest) returns (OrderResponse) {}
}
message OrderRequest { string id = 1; double amount = 2; }
message OrderResponse { string status = 1; }
''', encoding="utf-8")

    return base_dir


def main() -> int:
    print("=== RCIR Zero-Cloud CI Check (v7 §3) ===")
    print("Blocking all network socket creation...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = _build_sample_repo(Path(tmp_dir))

        with patch("socket.socket", _BlockedSocket):
            try:
                # 1. Graph extraction
                print("1/4 Testing graph extraction (with proto & HTTP)...")
                graph = extract_graph(repo_path)
                assert graph["metadata"]["total_nodes"] > 0
                assert graph["metadata"]["proto_files_parsed"] == 1

                # 2. Hierarchy building
                print("2/4 Testing hierarchy building...")
                hierarchy = build_hierarchy(graph)
                assert hierarchy is not None

                # 3. Invalidation / diffing
                print("3/4 Testing state diffing / invalidation...")
                service_file = repo_path / "sample_service" / "service.py"
                old_code = service_file.read_text(encoding="utf-8")
                new_code = old_code.replace("is_valid()", "is_valid() and self.amount < 1000000")
                diff_result = diff_file(str(service_file), old_code, new_code)
                assert diff_result is not None

                # 4. Hybrid retrieval
                print("4/4 Testing hybrid retrieval...")
                contract = hybrid_retrieve(
                    hierarchy=hierarchy,
                    query="process order validation",
                    token_budget=2000,
                    graph_edges=graph.get("edges", []),
                )
                assert contract is not None
                assert len(contract.nodes) > 0

            except NetworkBlockedError as e:
                print(f"\n[FAILED] {e}", file=sys.stderr)
                return 1
            except Exception as e:
                print(f"\n[ERROR] Unexpected error during zero-cloud check: {e}", file=sys.stderr)
                return 1

    print("\n[PASSED] All core analysis steps executed with zero network calls.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
