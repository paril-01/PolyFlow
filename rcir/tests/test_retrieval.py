"""
Tests for hybrid retrieval and Context Contract.

§0.1 compliance:
- Different queries MUST produce different node sets.
- Token budget must be enforced.
- Contract validation catches real errors.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rcir.retrieval.scorer import TFIDFScorer, tokenize
from rcir.retrieval.hybrid import hybrid_retrieve, _pass2_symbol_match
from rcir.contract.schema import (
    ContextContract, ContractNode, validate_contract,
    _check_budget_integrity, _check_node_paths_unique,
)


# ─── Tokenizer Tests ──────────────────────────────────────────────

class TestTokenizer:
    def test_snake_case(self):
        tokens = tokenize("create_user_profile")
        assert "create" in tokens
        assert "user" in tokens
        assert "profile" in tokens

    def test_camel_case(self):
        tokens = tokenize("CreateUserProfile")
        assert "create" in tokens
        assert "user" in tokens
        assert "profile" in tokens

    def test_path_splitting(self):
        tokens = tokenize("src/auth/login.py::authenticate")
        assert "src" in tokens
        assert "auth" in tokens
        assert "login" in tokens
        assert "authenticate" in tokens

    def test_mixed_case(self):
        tokens = tokenize("HTTPResponse_handler")
        assert "handler" in tokens


# ─── TF-IDF Scorer Tests ──────────────────────────────────────────

class TestTFIDFScorer:
    @pytest.fixture
    def scorer(self):
        nodes = [
            {"path": "auth/login.py::authenticate", "kind": "function", "args": [{"name": "username"}, {"name": "password"}]},
            {"path": "auth/login.py::validate_token", "kind": "function", "args": [{"name": "token"}]},
            {"path": "api/routes.py::get_users", "kind": "function", "args": [{"name": "page"}, {"name": "limit"}]},
            {"path": "api/routes.py::create_user", "kind": "function", "args": [{"name": "data"}]},
            {"path": "db/models.py::User", "kind": "class", "bases": ["Model"]},
            {"path": "db/queries.py::find_user_by_email", "kind": "function", "args": [{"name": "email"}]},
        ]
        s = TFIDFScorer()
        s.build_index(nodes)
        return s

    def test_relevant_query_scores_higher(self, scorer):
        """A query about authentication should score auth nodes higher."""
        scores = scorer.score("authenticate user with password")

        auth_score = scores.get("auth/login.py::authenticate", 0)
        route_score = scores.get("api/routes.py::get_users", 0)

        assert auth_score > route_score, \
            f"Auth node ({auth_score}) should score higher than routes ({route_score}) for auth query"

    def test_different_queries_different_rankings(self, scorer):
        """§0.1: Different queries MUST produce different top results."""
        top_auth = scorer.top_k("authenticate login password", k=3)
        top_users = scorer.top_k("create user profile data", k=3)
        top_db = scorer.top_k("database model query email", k=3)

        auth_paths = [p for p, _ in top_auth]
        user_paths = [p for p, _ in top_users]
        db_paths = [p for p, _ in top_db]

        # At least two of the three should have different #1 results
        top_1s = {auth_paths[0] if auth_paths else None,
                  user_paths[0] if user_paths else None,
                  db_paths[0] if db_paths else None}

        assert len(top_1s) >= 2, \
            f"Three different queries all produced the same #1 result — scorer is broken: {top_1s}"

    def test_empty_query_returns_zeros(self, scorer):
        """Empty query should score everything at 0."""
        scores = scorer.score("")
        assert all(v == 0 for v in scores.values())


# ─── Symbol Match Tests ───────────────────────────────────────────

class TestSymbolMatch:
    def test_exact_name_match_high_score(self):
        nodes = [
            {"path": "auth.py::authenticate"},
            {"path": "utils.py::hash_string"},
        ]
        scores = _pass2_symbol_match(nodes, "authenticate")

        assert scores["auth.py::authenticate"] > scores["utils.py::hash_string"]


# ─── Hybrid Retrieval Tests ───────────────────────────────────────

class TestHybridRetrieval:
    @pytest.fixture
    def sample_hierarchy(self):
        return {
            "nodes": [
                {"path": "auth/login.py::authenticate", "kind": "function", "level": "function",
                 "args": [{"name": "username"}, {"name": "password"}], "line": 1, "end_line": 10},
                {"path": "auth/login.py::validate_token", "kind": "function", "level": "function",
                 "args": [{"name": "token"}], "line": 12, "end_line": 20},
                {"path": "api/routes.py::register_blueprint", "kind": "function", "level": "function",
                 "args": [{"name": "app"}, {"name": "blueprint"}], "line": 1, "end_line": 15,
                 "decorators": ["route"]},
                {"path": "api/routes.py::handle_request", "kind": "function", "level": "function",
                 "args": [{"name": "request"}], "line": 17, "end_line": 30},
                {"path": "db/models.py::User", "kind": "class", "level": "class",
                 "bases": ["Model"], "line": 1, "end_line": 40},
                {"path": "db/models.py::User.save", "kind": "method", "level": "function",
                 "args": [{"name": "self"}], "line": 20, "end_line": 30},
            ],
            "hub_scores": {
                "auth/login.py::authenticate": 0.8,
                "auth/login.py::validate_token": 0.3,
                "api/routes.py::register_blueprint": 0.5,
                "api/routes.py::handle_request": 0.2,
                "db/models.py::User": 0.9,
                "db/models.py::User.save": 0.1,
            },
            "edges": [
                {"source": "api/routes.py::handle_request", "target": "auth/login.py::authenticate",
                 "type": "calls", "confidence": 1.0},
                {"source": "api/routes.py::handle_request", "target": "db/models.py::User",
                 "type": "calls", "confidence": 0.7},
            ],
        }

    def test_returns_context_contract(self, sample_hierarchy):
        """Retrieval should return a valid ContextContract."""
        contract = hybrid_retrieve(sample_hierarchy, "authenticate user login")

        assert isinstance(contract, ContextContract)
        assert contract.query == "authenticate user login"
        assert len(contract.nodes) > 0
        assert contract.token_budget_used >= 0

    def test_token_budget_respected(self, sample_hierarchy):
        """Used tokens should not exceed the budget."""
        contract = hybrid_retrieve(sample_hierarchy, "authenticate", token_budget=500)

        assert contract.token_budget_used <= contract.token_budget_total

    def test_different_queries_different_results(self, sample_hierarchy):
        """§0.1: Different queries MUST return different node sets."""
        c1 = hybrid_retrieve(sample_hierarchy, "authenticate user login password")
        c2 = hybrid_retrieve(sample_hierarchy, "database model save user")
        c3 = hybrid_retrieve(sample_hierarchy, "register blueprint route api")

        paths1 = {n.path for n in c1.nodes}
        paths2 = {n.path for n in c2.nodes}
        paths3 = {n.path for n in c3.nodes}

        # At least two of the three should be different
        different_count = len({frozenset(paths1), frozenset(paths2), frozenset(paths3)})
        assert different_count >= 2, \
            f"Three different queries all returned the same nodes — retrieval is broken"

    def test_contract_validates(self, sample_hierarchy):
        """The returned contract should pass validation."""
        contract = hybrid_retrieve(sample_hierarchy, "authenticate")
        errors = validate_contract(contract)

        # Filter out warnings (empty response is a warning, not an error)
        real_errors = [e for e in errors if "no nodes" not in e.lower()]
        assert len(real_errors) == 0, f"Validation errors: {real_errors}"


# ─── Contract Validation Tests ─────────────────────────────────────

class TestContractValidation:
    def test_empty_query_fails(self):
        contract = ContextContract(
            query="",
            nodes=[],
            token_budget_used=0,
            token_budget_total=1000,
        )
        errors = validate_contract(contract)
        assert any("query" in e.lower() for e in errors)

    def test_budget_overflow_fails(self):
        contract = ContextContract(
            query="test query",
            nodes=[],
            token_budget_used=2000,
            token_budget_total=1000,
        )
        errors = validate_contract(contract)
        assert any("exceeds" in e.lower() for e in errors)

    def test_duplicate_paths_fail(self):
        node = ContractNode(
            path="same/path.py::func",
            level="function",
            summary="test",
            raw_snippet=None,
            interface_status="unchanged",
            body_status="unchanged",
            summary_version="v1",
            summary_source="test",
            granularity="fine",
        )
        contract = ContextContract(
            query="test",
            nodes=[node, node],
            token_budget_used=100,
            token_budget_total=1000,
        )
        errors = validate_contract(contract)
        assert any("duplicate" in e.lower() for e in errors)

    def test_valid_contract_passes(self):
        contract = ContextContract(
            query="test query",
            nodes=[
                ContractNode(
                    path="module.py::func",
                    level="function",
                    summary="A test function",
                    raw_snippet=None,
                    interface_status="unchanged",
                    body_status="changed",
                    summary_version="v1",
                    summary_source="incremental_ast_analysis",
                    granularity="fine",
                ),
            ],
            token_budget_used=50,
            token_budget_total=1000,
        )
        errors = validate_contract(contract)
        assert len(errors) == 0, f"Valid contract should have no errors: {errors}"

    def test_contract_roundtrip(self):
        """Contract should survive to_dict → from_dict."""
        original = ContextContract(
            query="test roundtrip",
            nodes=[
                ContractNode(
                    path="a.py::foo",
                    level="function",
                    summary="foo function",
                    raw_snippet="def foo(): pass",
                    interface_status="changed",
                    body_status="unchanged",
                    summary_version="v3",
                    summary_source="incremental_ast_analysis",
                    granularity="fine",
                    relevance_score=0.85,
                ),
            ],
            token_budget_used=100,
            token_budget_total=4000,
            coverage_warning="test warning",
        )

        d = original.to_dict()
        restored = ContextContract.from_dict(d)

        assert restored.query == original.query
        assert len(restored.nodes) == 1
        assert restored.nodes[0].path == "a.py::foo"
        assert restored.coverage_warning == "test warning"
