"""
Tests for the graph extractor module.

§0.1 compliance:
- Tests use real, non-trivial Python code structures — NOT toy files designed
  to match expected output.
- We test against the RCIR codebase itself as one test target (a real repo
  with real functions).
- Edge confidence tests verify classification logic against actual resolution
  patterns.
"""

import ast
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rcir.graph.extractor import extract_graph, _SymbolCollector, _EdgeCollector
from rcir.graph.edges import make_edge, Edge, CONFIDENCE_BY_RESOLUTION


# ─── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def multi_file_repo(tmp_path):
    """Create a realistic multi-file Python project for testing."""
    # models.py — defines classes
    models = tmp_path / "models.py"
    models.write_text('''
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    def validate(self) -> bool:
        return "@" in self.email and len(self.name) > 0

    async def send_notification(self, message: str) -> None:
        """Send a notification to the user."""
        print(f"Notifying {self.name}: {message}")


class AdminUser(User):
    def __init__(self, name: str, email: str, role: str = "admin"):
        super().__init__(name, email)
        self.role = role

    def has_permission(self, action: str) -> bool:
        return self.role == "admin"
''', encoding="utf-8")

    # services.py — calls functions from models
    services = tmp_path / "services.py"
    services.write_text('''
from models import User, AdminUser
import json

def create_user(data: dict) -> User:
    """Create a new user from input data."""
    user = User(name=data["name"], email=data["email"])
    if not user.validate():
        raise ValueError("Invalid user data")
    return user

def promote_to_admin(user: User, role: str = "admin") -> AdminUser:
    admin = AdminUser(name=user.name, email=user.email, role=role)
    return admin

def serialize_user(user: User) -> str:
    return json.dumps({"name": user.name, "email": user.email})
''', encoding="utf-8")

    # utils/helpers.py — nested module
    utils_dir = tmp_path / "utils"
    utils_dir.mkdir()
    (utils_dir / "__init__.py").write_text("# utils package\n", encoding="utf-8")

    helpers = utils_dir / "helpers.py"
    helpers.write_text('''
import hashlib

def hash_string(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

def truncate(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
''', encoding="utf-8")

    return tmp_path


# ─── Graph Extraction Tests ───────────────────────────────────────

class TestExtractGraph:
    def test_extracts_functions_and_classes(self, multi_file_repo):
        """Verify that real functions and classes are found."""
        graph = extract_graph(multi_file_repo)

        node_paths = {n["path"] for n in graph["nodes"]}

        # These specific functions/classes exist in our test repo
        assert any("User" in p for p in node_paths), \
            f"User class not found in nodes: {node_paths}"
        assert any("create_user" in p for p in node_paths), \
            f"create_user not found in nodes: {node_paths}"
        assert any("hash_string" in p for p in node_paths), \
            f"hash_string not found in nodes: {node_paths}"

    def test_extracts_methods_inside_classes(self, multi_file_repo):
        """Methods inside classes should be their own nodes."""
        graph = extract_graph(multi_file_repo)

        node_paths = {n["path"] for n in graph["nodes"]}

        assert any("validate" in p for p in node_paths), \
            f"validate method not found: {node_paths}"
        assert any("__init__" in p for p in node_paths), \
            f"__init__ method not found: {node_paths}"

    def test_extracts_async_functions(self, multi_file_repo):
        """Async functions should be captured with is_async flag."""
        graph = extract_graph(multi_file_repo)

        async_nodes = [n for n in graph["nodes"] if n.get("is_async")]
        assert len(async_nodes) > 0, "No async functions found"
        assert any("send_notification" in n["path"] for n in async_nodes)

    def test_extracts_cross_file_edges(self, multi_file_repo):
        """Imports between files should create edges."""
        graph = extract_graph(multi_file_repo)

        import_edges = [e for e in graph["edges"] if e["type"] == "imports"]
        assert len(import_edges) > 0, \
            f"No import edges found. All edges: {graph['edges']}"

    def test_extracts_call_edges(self, multi_file_repo):
        """Function calls should create edges."""
        graph = extract_graph(multi_file_repo)

        call_edges = [e for e in graph["edges"] if e["type"] == "calls"]
        assert len(call_edges) > 0, \
            f"No call edges found. All edges: {graph['edges']}"

    def test_extracts_inheritance_edges(self, multi_file_repo):
        """Class inheritance should create edges."""
        graph = extract_graph(multi_file_repo)

        inherit_edges = [e for e in graph["edges"] if e["type"] == "inherits"]
        assert len(inherit_edges) > 0, \
            f"No inheritance edges found. All edges: {graph['edges']}"
        # AdminUser inherits from User
        assert any(
            "AdminUser" in e["source"] and "User" in e["target"]
            for e in inherit_edges
        ), f"AdminUser→User inheritance not found: {inherit_edges}"

    def test_node_counts_are_nonzero(self, multi_file_repo):
        """Basic sanity: graph should have nodes and edges."""
        graph = extract_graph(multi_file_repo)

        assert graph["metadata"]["total_nodes"] > 0
        assert graph["metadata"]["total_edges"] > 0
        assert graph["metadata"]["files_parsed"] > 0

    def test_handles_syntax_errors_gracefully(self, tmp_path):
        """Files with syntax errors should be skipped, not crash."""
        bad_file = tmp_path / "broken.py"
        bad_file.write_text("def broken(\n  this is not valid python", encoding="utf-8")

        good_file = tmp_path / "good.py"
        good_file.write_text("def working(): return True\n", encoding="utf-8")

        graph = extract_graph(tmp_path)
        # Should still find the good file's function
        assert graph["metadata"]["total_nodes"] > 0

    def test_nested_modules_have_correct_paths(self, multi_file_repo):
        """Functions in nested directories should have correct relative paths."""
        graph = extract_graph(multi_file_repo)

        # Find nodes from utils/helpers.py
        helper_nodes = [n for n in graph["nodes"] if "utils" in n["path"]]
        assert len(helper_nodes) > 0, "No nodes found from utils/ module"

        # Paths should include the directory structure
        for node in helper_nodes:
            assert "utils/" in node["path"], \
                f"Node path doesn't include directory: {node['path']}"

    def test_different_repos_produce_different_graphs(self, tmp_path):
        """§0.1 rule 1: output must differ based on input, not be templated."""
        # Repo A: web-style code
        repo_a = tmp_path / "repo_a"
        repo_a.mkdir()
        (repo_a / "app.py").write_text('''
from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "hello"

@app.route("/api/data")
def get_data():
    return {"key": "value"}
''', encoding="utf-8")

        # Repo B: data processing code
        repo_b = tmp_path / "repo_b"
        repo_b.mkdir()
        (repo_b / "pipeline.py").write_text('''
import csv

def read_csv(path: str) -> list:
    with open(path) as f:
        return list(csv.reader(f))

def transform(rows: list) -> list:
    return [r for r in rows if len(r) > 2]

def aggregate(rows: list) -> dict:
    return {"total": len(rows)}
''', encoding="utf-8")

        graph_a = extract_graph(repo_a)
        graph_b = extract_graph(repo_b)

        # The graphs MUST be different — same-shaped output = fabrication
        paths_a = {n["path"] for n in graph_a["nodes"]}
        paths_b = {n["path"] for n in graph_b["nodes"]}

        assert paths_a != paths_b, \
            "Two different repos produced identical node sets — this is a fabrication red flag"


# ─── Edge Confidence Tests ─────────────────────────────────────────

class TestEdgeConfidence:
    def test_confidence_values_are_correct(self):
        """Verify confidence scores match the spec."""
        assert CONFIDENCE_BY_RESOLUTION["static_exact"] == 1.0
        assert CONFIDENCE_BY_RESOLUTION["static_inference"] == 0.7
        assert CONFIDENCE_BY_RESOLUTION["dynamic_unresolved"] == 0.3

    def test_make_edge_sets_confidence(self):
        """make_edge should set confidence from resolution type."""
        edge = make_edge("a", "b", "calls", "static_exact")
        assert edge.confidence == 1.0

        edge2 = make_edge("a", "b", "calls", "static_inference")
        assert edge2.confidence == 0.7

    def test_edge_roundtrip(self):
        """Edge should serialize and deserialize correctly."""
        edge = make_edge("src/a.py::foo", "src/b.py::bar", "calls", "static_exact")
        d = edge.to_dict()
        restored = Edge.from_dict(d)
        assert restored == edge


# ─── Self-extraction test (uses RCIR's own code as test input) ────

class TestSelfExtraction:
    def test_extract_own_codebase(self):
        """Extract the graph from RCIR's own source — a real, non-trivial repo."""
        rcir_src = Path(__file__).parent.parent / "src" / "rcir"
        if not rcir_src.is_dir():
            pytest.skip("RCIR source not found at expected path")

        graph = extract_graph(rcir_src)

        # Should find our own modules
        assert graph["metadata"]["total_nodes"] > 10, \
            f"Expected >10 nodes in RCIR itself, got {graph['metadata']['total_nodes']}"
        assert graph["metadata"]["total_edges"] > 5, \
            f"Expected >5 edges in RCIR itself, got {graph['metadata']['total_edges']}"

        # Verify some known RCIR functions exist
        paths = {n["path"] for n in graph["nodes"]}
        assert any("extract_graph" in p for p in paths), \
            f"extract_graph not found in self-extraction: {sorted(paths)[:10]}"
