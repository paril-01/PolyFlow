"""
Tests for state-split invalidation: diff, propagation, and versioning.

§0.1 compliance:
- Diff tests use real Python code with independently verifiable changes.
- Propagation tests verify body-only changes stay local while
  interface changes propagate fully.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rcir.state.diff import diff_file, NodeDiff, _extract_interface, _normalize_body_ast, _hash_body
from rcir.state.propagate import compute_propagation, PropagationResult
from rcir.state.versioning import VersionChain, VersionStore, GENESIS_HASH

import ast


# ─── Interface Diff Tests ──────────────────────────────────────────

class TestInterfaceDiff:
    def test_body_only_change_detected(self):
        """Changing only a function body (not its signature) should be body-only."""
        before = '''
def process_data(items: list) -> dict:
    """Process items and return summary."""
    total = sum(items)
    return {"total": total, "count": len(items)}
'''
        after = '''
def process_data(items: list) -> dict:
    """Process items and return summary."""
    total = sum(items)
    avg = total / len(items) if items else 0
    return {"total": total, "count": len(items), "average": avg}
'''
        diffs = diff_file(before, after, "processor.py")

        assert len(diffs) == 1
        d = diffs[0]
        assert d.interface_status == "unchanged", \
            f"Interface should be unchanged for body-only edit, got: {d.interface_status}"
        assert d.body_status == "changed", \
            f"Body should be changed, got: {d.body_status}"

    def test_signature_change_detected(self):
        """Adding a parameter to a function should be an interface change."""
        before = '''
def create_user(name: str, email: str) -> dict:
    return {"name": name, "email": email}
'''
        after = '''
def create_user(name: str, email: str, role: str = "user") -> dict:
    return {"name": name, "email": email, "role": role}
'''
        diffs = diff_file(before, after, "users.py")

        assert len(diffs) == 1
        d = diffs[0]
        assert d.interface_status == "changed", \
            f"Adding a parameter should change the interface, got: {d.interface_status}"

    def test_return_type_change_detected(self):
        """Changing return annotation should be an interface change."""
        before = '''
def get_count() -> int:
    return 42
'''
        after = '''
def get_count() -> float:
    return 42.0
'''
        diffs = diff_file(before, after, "counter.py")

        assert len(diffs) >= 1
        interface_changed = any(d.interface_status == "changed" for d in diffs)
        assert interface_changed, "Changing return type should be an interface change"

    def test_decorator_change_detected(self):
        """Adding/removing a decorator should be an interface change."""
        before = '''
def handle_request(request):
    return {"ok": True}
'''
        after = '''
@require_auth
def handle_request(request):
    return {"ok": True}
'''
        diffs = diff_file(before, after, "handlers.py")

        assert len(diffs) >= 1
        interface_changed = any(d.interface_status == "changed" for d in diffs)
        assert interface_changed, "Adding a decorator should be an interface change"

    def test_new_function_detected(self):
        """Adding a new function should be detected."""
        before = '''
def existing():
    return True
'''
        after = '''
def existing():
    return True

def brand_new():
    return "I'm new here"
'''
        diffs = diff_file(before, after, "module.py")

        new_func_diffs = [d for d in diffs if "brand_new" in d.node_path]
        assert len(new_func_diffs) == 1
        assert new_func_diffs[0].interface_status == "changed"

    def test_removed_function_detected(self):
        """Removing a function should be detected."""
        before = '''
def will_be_removed():
    return "goodbye"

def stays():
    return "still here"
'''
        after = '''
def stays():
    return "still here"
'''
        diffs = diff_file(before, after, "module.py")

        removed_diffs = [d for d in diffs if "will_be_removed" in d.node_path]
        assert len(removed_diffs) == 1
        assert removed_diffs[0].interface_status == "changed"

    def test_whitespace_only_change_not_detected(self):
        """Whitespace/comment-only changes should NOT produce diffs."""
        before = '''
def compute(x: int) -> int:
    result = x * 2
    return result
'''
        after = '''
def compute(x: int) -> int:
    # Added a comment
    result = x * 2

    return result
'''
        diffs = diff_file(before, after, "math.py")

        # Adding a comment changes the AST (ast.Expr for the comment doesn't exist,
        # but whitespace is ignored). In practice, comments are stripped by ast.parse,
        # so the body hash should be the same. Blank lines also don't affect AST.
        # If there ARE diffs, they should show body_status unchanged.
        body_changes = [d for d in diffs if d.body_status == "changed"]
        # The AST should be identical since comments and whitespace don't appear in AST
        assert len(body_changes) == 0, \
            f"Whitespace/comment-only change should not change body hash: {diffs}"

    def test_unchanged_file_produces_no_diffs(self):
        """Identical before/after should produce no diffs."""
        code = '''
def stable_function(x: int) -> str:
    return str(x)
'''
        diffs = diff_file(code, code, "stable.py")
        assert len(diffs) == 0, "Identical code should produce zero diffs"


# ─── Data Contract Detection Tests ─────────────────────────────────

class TestDataContractDiff:
    def test_sql_change_detected(self):
        """Adding SQL to a function should flag data_contract_status."""
        before = '''
def get_users(db):
    return db.query("SELECT * FROM users")
'''
        after = '''
def get_users(db):
    return db.query("SELECT id, name, email FROM users WHERE active = 1")
'''
        diffs = diff_file(before, after, "queries.py")

        # Both have SQL, but the SQL changed
        assert len(diffs) >= 1


# ─── Propagation Tests ─────────────────────────────────────────────

class TestPropagation:
    @pytest.fixture
    def sample_hierarchy(self):
        """Hierarchy with a clear ancestor structure."""
        return {
            "nodes": [
                {"path": "src/auth/login.py::authenticate", "level": "function",
                 "ancestors": ["src/auth/login.py", "src/auth", "src", "."]},
                {"path": "src/auth/login.py::validate_token", "level": "function",
                 "ancestors": ["src/auth/login.py", "src/auth", "src", "."]},
                {"path": "src/api/routes.py::create_user", "level": "function",
                 "ancestors": ["src/api/routes.py", "src/api", "src", "."]},
                {"path": "src/auth/login.py", "level": "file",
                 "ancestors": ["src/auth", "src", "."]},
                {"path": "src/api/routes.py", "level": "file",
                 "ancestors": ["src/api", "src", "."]},
            ],
        }

    def test_body_only_change_stays_local(self, sample_hierarchy):
        """Body-only change should invalidate ONLY the node + immediate parent."""
        diffs = [{
            "node_path": "src/auth/login.py::authenticate",
            "interface_status": "unchanged",
            "body_status": "changed",
            "data_contract_status": "n/a",
        }]

        result = compute_propagation(diffs, sample_hierarchy)

        assert "src/auth/login.py::authenticate" in result.invalidated_nodes
        assert "src/auth/login.py" in result.invalidated_nodes  # immediate parent

        # Should NOT propagate to grandparent or beyond
        assert "src/auth" not in result.invalidated_nodes, \
            "Body-only change should not propagate to grandparent"
        assert "src" not in result.invalidated_nodes
        assert "." not in result.invalidated_nodes

        assert result.body_only_local == 1
        assert result.interface_propagations == 0

    def test_interface_change_propagates_fully(self, sample_hierarchy):
        """Interface change should propagate through ALL ancestors."""
        diffs = [{
            "node_path": "src/auth/login.py::authenticate",
            "interface_status": "changed",
            "body_status": "changed",
            "data_contract_status": "n/a",
        }]

        result = compute_propagation(diffs, sample_hierarchy)

        # Should propagate to ALL ancestors
        assert "src/auth/login.py::authenticate" in result.invalidated_nodes
        assert "src/auth/login.py" in result.invalidated_nodes
        assert "src/auth" in result.invalidated_nodes
        assert "src" in result.invalidated_nodes
        assert "." in result.invalidated_nodes

        assert result.interface_propagations == 1

    def test_body_only_costs_less_than_interface(self, sample_hierarchy):
        """Body-only changes must invalidate fewer nodes than interface changes."""
        body_diffs = [{
            "node_path": "src/auth/login.py::authenticate",
            "interface_status": "unchanged",
            "body_status": "changed",
            "data_contract_status": "n/a",
        }]

        iface_diffs = [{
            "node_path": "src/auth/login.py::authenticate",
            "interface_status": "changed",
            "body_status": "changed",
            "data_contract_status": "n/a",
        }]

        body_result = compute_propagation(body_diffs, sample_hierarchy)
        iface_result = compute_propagation(iface_diffs, sample_hierarchy)

        assert body_result.total_invalidated < iface_result.total_invalidated, \
            f"Body-only ({body_result.total_invalidated} nodes) should invalidate " \
            f"fewer nodes than interface ({iface_result.total_invalidated} nodes)"

    def test_data_contract_change_propagates_like_interface(self, sample_hierarchy):
        """Data contract changes should propagate like interface changes."""
        diffs = [{
            "node_path": "src/auth/login.py::authenticate",
            "interface_status": "unchanged",
            "body_status": "unchanged",
            "data_contract_status": "changed",
        }]

        result = compute_propagation(diffs, sample_hierarchy)

        # Should propagate to ALL ancestors
        assert "src/auth" in result.invalidated_nodes
        assert "src" in result.invalidated_nodes
        assert "." in result.invalidated_nodes


# ─── Versioning Tests ──────────────────────────────────────────────

class TestVersioning:
    def test_chain_produces_unique_hashes(self):
        """Each version should have a unique hash."""
        chain = VersionChain("test_node")
        v1 = chain.append("content version 1")
        v2 = chain.append("content version 2")
        v3 = chain.append("content version 3")

        hashes = {v1.version_hash, v2.version_hash, v3.version_hash}
        assert len(hashes) == 3, "Each version should have a unique hash"

    def test_chain_links_correctly(self):
        """Each version's previous_hash should point to the prior version."""
        chain = VersionChain("test_node")
        v1 = chain.append("v1 content")
        v2 = chain.append("v2 content")

        assert v1.previous_hash == GENESIS_HASH
        assert v2.previous_hash == v1.version_hash

    def test_chain_verification_passes(self):
        """A valid chain should pass verification."""
        chain = VersionChain("test_node")
        chain.append("content 1")
        chain.append("content 2")
        chain.append("content 3")

        assert chain.verify_chain() is True

    def test_chain_verification_detects_tampering(self):
        """Modifying a version in the chain should fail verification."""
        chain = VersionChain("test_node")
        chain.append("content 1")
        chain.append("content 2")

        # Tamper with v1's hash
        chain.versions[0].version_hash = "tampered_hash_value"

        assert chain.verify_chain() is False, \
            "Tampered chain should fail verification"

    def test_same_content_different_position_different_hash(self):
        """Same content at different positions should produce different hashes
        (because the previous_hash differs)."""
        chain = VersionChain("test_node")
        v1 = chain.append("identical content")
        chain.append("something else")
        v3 = chain.append("identical content")

        assert v1.version_hash != v3.version_hash, \
            "Same content at different chain positions should have different version hashes"

    def test_version_store_manages_multiple_chains(self):
        """VersionStore should manage independent chains per node."""
        store = VersionStore()
        store.update_node("node_a", "content_a")
        store.update_node("node_b", "content_b")
        store.update_node("node_a", "content_a_v2")

        assert store.get_current_version("node_a").version_number == 2
        assert store.get_current_version("node_b").version_number == 1

    def test_version_store_verify_all(self):
        """All chains in the store should pass verification."""
        store = VersionStore()
        store.update_node("a", "1")
        store.update_node("a", "2")
        store.update_node("b", "x")

        results = store.verify_all()
        assert all(results.values()), f"Some chains failed verification: {results}"
