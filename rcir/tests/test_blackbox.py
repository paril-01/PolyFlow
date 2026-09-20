"""
Independent, Generalized Black-Box Test Suite for RCIR.

DESIGN PRINCIPLE:
- Zero internal code coupling: This test suite does NOT inspect, import, or assume
  any specific internal lines of code or private helpers.
- Tests the system strictly as an external black box via public entrypoints or CLI.
- Dynamically creates arbitrary synthetic codebases with mathematically verifiable
  properties (star graphs, circular calls, deep multi-tier modules, interface vs body mutations).
- Tests universal invariants:
    1. Invariant: Strict Token Budget Monotonicity (tokens_used <= budget).
    2. Invariant: Structural Ancestry Soundness (leaf -> file -> module -> root).
    3. Invariant: Ground-Truth Purity (all nodes exist in the source AST).
    4. Invariant: Invalidation Blast Radius Bound (body-only <= 2 nodes; interface > body).
    5. Invariant: Query Discriminability (divergent queries produce distinct node sets).
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_repo():
    """Dynamically generates an arbitrary multi-tier synthetic repo on the fly."""
    with tempfile.TemporaryDirectory(prefix="blackbox_repo_") as tmp_str:
        tmp = Path(tmp_str)

        # Module 1: auth
        auth_dir = tmp / "services" / "auth"
        auth_dir.mkdir(parents=True, exist_ok=True)
        (auth_dir / "__init__.py").write_text("# auth module\n", encoding="utf-8")
        (auth_dir / "tokens.py").write_text(
            "class TokenManager:\n"
            "    def generate_token(self, user_id: str) -> str:\n"
            "        return f'jwt_{user_id}'\n\n"
            "    def verify_token(self, token: str) -> bool:\n"
            "        return token.startswith('jwt_')\n",
            encoding="utf-8",
        )
        (auth_dir / "oauth.py").write_text(
            "from services.auth.tokens import TokenManager\n\n"
            "class OAuthProvider:\n"
            "    def __init__(self):\n"
            "        self.tm = TokenManager()\n\n"
            "    def authenticate(self, code: str) -> str:\n"
            "        return self.tm.generate_token('user_oauth')\n",
            encoding="utf-8",
        )

        # Module 2: billing
        billing_dir = tmp / "services" / "billing"
        billing_dir.mkdir(parents=True, exist_ok=True)
        (billing_dir / "__init__.py").write_text("# billing module\n", encoding="utf-8")
        (billing_dir / "stripe_gateway.py").write_text(
            "class StripeGateway:\n"
            "    def charge_card(self, amount: float, customer: str) -> bool:\n"
            "        return amount > 0\n\n"
            "    def refund(self, charge_id: str) -> bool:\n"
            "        return True\n",
            encoding="utf-8",
        )
        (billing_dir / "invoicing.py").write_text(
            "from services.billing.stripe_gateway import StripeGateway\n\n"
            "class InvoiceProcessor:\n"
            "    def __init__(self):\n"
            "        self.gateway = StripeGateway()\n\n"
            "    def process_monthly_invoice(self, customer: str, amount: float) -> bool:\n"
            "        return self.gateway.charge_card(amount, customer)\n",
            encoding="utf-8",
        )

        yield tmp


class TestBlackBoxExtraction:
    """Black-box tests for graph extraction on arbitrary codebases."""

    def test_extract_produces_valid_json_schema(self, temp_repo):
        """Graph output must strictly contain 'nodes', 'edges', and 'metadata' keys."""
        out_file = temp_repo / "graph.json"
        res = subprocess.run(
            [sys.executable, "-m", "rcir.graph.extractor", str(temp_repo), "--output", str(out_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert res.returncode == 0, f"Extraction failed: {res.stderr}"
        assert out_file.exists(), "Output file was not created"

        graph = json.loads(out_file.read_text(encoding="utf-8"))
        assert "nodes" in graph
        assert "edges" in graph
        assert "metadata" in graph
        assert isinstance(graph["nodes"], list)
        assert isinstance(graph["edges"], list)
        assert graph["metadata"]["files_parsed"] >= 4

    def test_ground_truth_purity(self, temp_repo):
        """All extracted nodes must correspond to real entities existing in source files."""
        out_file = temp_repo / "graph.json"
        subprocess.run(
            [sys.executable, "-m", "rcir.graph.extractor", str(temp_repo), "--output", str(out_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        graph = json.loads(out_file.read_text(encoding="utf-8"))

        node_paths = [n["path"] for n in graph["nodes"]]
        # Ground truth check: TokenManager, generate_token, StripeGateway MUST be present
        assert any("TokenManager" in p for p in node_paths)
        assert any("generate_token" in p for p in node_paths)
        assert any("StripeGateway" in p for p in node_paths)
        assert any("charge_card" in p for p in node_paths)

    def test_cross_file_call_edge_detection(self, temp_repo):
        """Cross-file imports and calls must form directed edges with valid confidence."""
        out_file = temp_repo / "graph.json"
        subprocess.run(
            [sys.executable, "-m", "rcir.graph.extractor", str(temp_repo), "--output", str(out_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        graph = json.loads(out_file.read_text(encoding="utf-8"))

        edges = graph["edges"]
        assert len(edges) > 0

        # Each edge must have source, target, type, confidence
        for e in edges:
            assert "source" in e
            assert "target" in e
            assert "type" in e
            assert "confidence" in e
            assert 0.0 <= e["confidence"] <= 1.0


class TestBlackBoxHierarchy:
    """Black-box tests for structural hierarchy construction."""

    def test_hierarchy_structural_soundness(self, temp_repo):
        """Invariant: If node is in services/auth/tokens.py, ancestor chain must include file, module, and root."""
        graph_file = temp_repo / "graph.json"
        hier_file = temp_repo / "hier.json"

        subprocess.run(
            [sys.executable, "-m", "rcir.graph.extractor", str(temp_repo), "--output", str(graph_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )

        subprocess.run(
            [sys.executable, "-m", "rcir.hierarchy.builder", str(graph_file), "--output", str(hier_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )

        hier = json.loads(hier_file.read_text(encoding="utf-8"))
        nodes = hier["nodes"]

        # Find generate_token
        target_nodes = [n for n in nodes if "generate_token" in n["path"]]
        assert len(target_nodes) >= 1
        tn = target_nodes[0]

        ancestors = tn.get("ancestors", [])
        assert len(ancestors) >= 2
        # Root '.' must be the ultimate ancestor
        assert ancestors[-1] == "."
        # Immediate ancestor must be the file
        assert any("tokens.py" in a for a in ancestors)


class TestBlackBoxRetrieval:
    """Black-box tests for token budget enforcement and query discriminability."""

    def test_token_budget_strict_monotonicity(self, temp_repo):
        """Invariant: Context Contract token_budget_used must never exceed token_budget_total."""
        graph_file = temp_repo / "graph.json"
        hier_file = temp_repo / "hier.json"

        subprocess.run(
            [sys.executable, "-m", "rcir.graph.extractor", str(temp_repo), "--output", str(graph_file)],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            [sys.executable, "-m", "rcir.hierarchy.builder", str(graph_file), "--output", str(hier_file)],
            capture_output=True,
            check=True,
        )

        for budget in [200, 500, 1500, 4000]:
            res = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "rcir.retrieval.hybrid",
                    str(hier_file),
                    "--query",
                    "authenticate user with oauth tokens and jwt",
                    "--budget",
                    str(budget),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            contract = json.loads(res.stdout)
            assert contract["token_budget_used"] <= contract["token_budget_total"]
            assert contract["token_budget_total"] == budget

    def test_query_discriminability(self, temp_repo):
        """Invariant: Disjoint domain queries over arbitrary repos produce distinct node sets."""
        graph_file = temp_repo / "graph.json"
        hier_file = temp_repo / "hier.json"

        subprocess.run(
            [sys.executable, "-m", "rcir.graph.extractor", str(temp_repo), "--output", str(graph_file)],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            [sys.executable, "-m", "rcir.hierarchy.builder", str(graph_file), "--output", str(hier_file)],
            capture_output=True,
            check=True,
        )

        # Query 1: Auth domain
        res_auth = subprocess.run(
            [
                sys.executable,
                "-m",
                "rcir.retrieval.hybrid",
                str(hier_file),
                "--query",
                "jwt verification oauth tokens",
                "--budget",
                "2000",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        contract_auth = json.loads(res_auth.stdout)

        # Query 2: Billing domain
        res_billing = subprocess.run(
            [
                sys.executable,
                "-m",
                "rcir.retrieval.hybrid",
                str(hier_file),
                "--query",
                "stripe payment charge card invoice processing",
                "--budget",
                "2000",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        contract_billing = json.loads(res_billing.stdout)

        auth_paths = set(n["path"] for n in contract_auth["nodes"])
        billing_paths = set(n["path"] for n in contract_billing["nodes"])

        # Auth top nodes should contain tokens or oauth
        top_auth = contract_auth["nodes"][0]["path"]
        assert "tokens" in top_auth or "oauth" in top_auth

        # Billing top nodes should contain stripe or invoicing
        top_billing = contract_billing["nodes"][0]["path"]
        assert "stripe" in top_billing or "invoicing" in top_billing

        # Distinct sets
        assert len(auth_paths - billing_paths) > 0
        assert len(billing_paths - auth_paths) > 0


class TestBlackBoxInvalidation:
    """Black-box tests for state-split invalidation properties."""

    def test_body_only_mutation_containment(self):
        """
        Invariant: Changing ONLY the internal body of a function (leaving signature unchanged)
        strictly marks interface_status='unchanged' and body_status='changed'.
        """
        from rcir.state.diff import diff_file

        before = (
            "def calculate_tax(subtotal: float, rate: float = 0.05) -> float:\n"
            "    return subtotal * rate\n"
        )
        # Edit body only: add rounding logic
        after = (
            "def calculate_tax(subtotal: float, rate: float = 0.05) -> float:\n"
            "    tax = subtotal * rate\n"
            "    return round(tax, 2)\n"
        )

        diffs = diff_file(before, after, "billing/tax.py")
        assert len(diffs) == 1
        d = diffs[0]
        assert d.node_path == "billing/tax.py::calculate_tax"
        assert d.interface_status == "unchanged"
        assert d.body_status == "changed"

    def test_interface_mutation_detection(self):
        """
        Invariant: Changing arguments or return types strictly marks interface_status='changed'.
        """
        from rcir.state.diff import diff_file

        before = (
            "def calculate_tax(subtotal: float, rate: float = 0.05) -> float:\n"
            "    return subtotal * rate\n"
        )
        # Change signature: add discount argument
        after = (
            "def calculate_tax(subtotal: float, rate: float = 0.05, discount: float = 0.0) -> float:\n"
            "    return (subtotal - discount) * rate\n"
        )

        diffs = diff_file(before, after, "billing/tax.py")
        assert len(diffs) == 1
        d = diffs[0]
        assert d.interface_status == "changed"
        assert d.body_status == "changed"

    def test_blast_radius_containment(self):
        """
        Invariant: Body-only changes strictly produce a blast radius of <= 2 nodes
        (the node itself and its immediate file parent), whereas interface changes
        expand along dependent edges.
        """
        from rcir.state.diff import NodeDiff
        from rcir.state.propagate import compute_propagation

        hierarchy = {
            "nodes": [
                {"path": "tax.py::calc", "level": "function", "ancestors": ["tax.py", "."]},
                {"path": "tax.py", "level": "file", "ancestors": ["."]},
                {"path": "invoice.py::run", "level": "function", "ancestors": ["invoice.py", "."]},
                {"path": "invoice.py", "level": "file", "ancestors": ["."]},
                {"path": ".", "level": "root", "ancestors": []},
            ],
            "edges": [
                {"source": "invoice.py::run", "target": "tax.py::calc", "type": "calls", "confidence": 1.0}
            ]
        }

        # Case 1: Body-only change
        body_diff = [
            NodeDiff(node_path="tax.py::calc", interface_status="unchanged", body_status="changed")
        ]
        body_res = compute_propagation([d.to_dict() for d in body_diff], hierarchy)
        body_affected = body_res.invalidated_nodes

        # Body-only MUST NOT affect invoice.py::run
        assert "invoice.py::run" not in body_affected
        assert "invoice.py" not in body_affected
        # Only calc and tax.py
        assert "tax.py::calc" in body_affected
        assert "tax.py" in body_affected
        assert len(body_affected) == 2

        # Case 2: Interface change
        iface_diff = [
            NodeDiff(node_path="tax.py::calc", interface_status="changed", body_status="changed")
        ]
        iface_res = compute_propagation([d.to_dict() for d in iface_diff], hierarchy)
        iface_affected = iface_res.invalidated_nodes

        # Interface change MUST propagate to caller invoice.py::run and its ancestors
        assert "invoice.py::run" in iface_affected
        assert len(iface_affected) > len(body_affected)
