"""
Tests for hierarchy builder, hub scoring, and granularity detection.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rcir.hierarchy.builder import build_hierarchy, _extract_file_from_path, _extract_module_from_file
from rcir.hierarchy.hubs import compute_hub_scores, identify_hubs
from rcir.hierarchy.granularity import detect_coarse_artifacts


# ─── Hierarchy Builder Tests ───────────────────────────────────────

class TestHierarchyBuilder:
    @pytest.fixture
    def sample_graph(self):
        """A graph with functions across multiple files and modules."""
        return {
            "nodes": [
                {"path": "src/auth/login.py::authenticate", "kind": "function", "level": "function", "line": 5, "end_line": 15},
                {"path": "src/auth/login.py::validate_token", "kind": "function", "level": "function", "line": 18, "end_line": 25},
                {"path": "src/auth/models.py::User", "kind": "class", "level": "class", "line": 1, "end_line": 30},
                {"path": "src/auth/models.py::User.__init__", "kind": "method", "level": "function", "line": 3, "end_line": 8},
                {"path": "src/api/routes.py::get_users", "kind": "function", "level": "function", "line": 10, "end_line": 20},
                {"path": "src/api/routes.py::create_user", "kind": "function", "level": "function", "line": 22, "end_line": 35},
                {"path": "utils/helpers.py::hash_string", "kind": "function", "level": "function", "line": 1, "end_line": 3},
            ],
            "edges": [
                {"source": "src/api/routes.py::create_user", "target": "src/auth/models.py::User", "type": "calls", "confidence": 0.7},
                {"source": "src/api/routes.py::get_users", "target": "src/auth/login.py::validate_token", "type": "calls", "confidence": 1.0},
                {"source": "src/auth/login.py::authenticate", "target": "utils/helpers.py::hash_string", "type": "calls", "confidence": 1.0},
            ],
            "metadata": {"repo_path": "/tmp/test_repo"},
        }

    def test_builds_valid_hierarchy(self, sample_graph):
        """Hierarchy should produce nodes with ancestors."""
        h = build_hierarchy(sample_graph)

        assert len(h["nodes"]) > len(sample_graph["nodes"]), \
            "Hierarchy should add file/module nodes beyond the original graph nodes"

        # Check that leaf nodes have ancestors
        leaf_nodes = [n for n in h["nodes"] if n.get("level") == "function"]
        for leaf in leaf_nodes:
            assert "ancestors" in leaf, f"Leaf {leaf['path']} missing ancestors"
            assert len(leaf["ancestors"]) > 0, f"Leaf {leaf['path']} has empty ancestors"

    def test_different_files_have_different_ancestors(self, sample_graph):
        """§0.1 check: functions in different files MUST have different ancestor chains."""
        h = build_hierarchy(sample_graph)

        leaf_nodes = [n for n in h["nodes"] if n.get("level") == "function"]

        # Group by file
        by_file = {}
        for leaf in leaf_nodes:
            file_path = _extract_file_from_path(leaf["path"])
            by_file.setdefault(file_path, []).append(leaf)

        # Nodes from different files should have different ancestor chains
        ancestor_chains = []
        for file_path, nodes in by_file.items():
            if nodes:
                ancestor_chains.append((file_path, tuple(nodes[0]["ancestors"])))

        if len(ancestor_chains) >= 2:
            # At least two different chains should exist
            unique_chains = set(chain for _, chain in ancestor_chains)
            assert len(unique_chains) > 1, \
                f"All files have the same ancestor chain — hierarchy is broken: {ancestor_chains}"

    def test_hierarchy_contains_file_nodes(self, sample_graph):
        """File-level nodes should be present in the hierarchy."""
        h = build_hierarchy(sample_graph)

        file_nodes = [n for n in h["nodes"] if n.get("level") == "file"]
        assert len(file_nodes) > 0, "No file-level nodes in hierarchy"

        file_paths = {n["path"] for n in file_nodes}
        assert "src/auth/login.py" in file_paths
        assert "src/api/routes.py" in file_paths

    def test_hierarchy_contains_module_nodes(self, sample_graph):
        """Module-level nodes (directories) should be present."""
        h = build_hierarchy(sample_graph)

        module_nodes = [n for n in h["nodes"] if n.get("level") == "module"]
        assert len(module_nodes) > 0, "No module-level nodes in hierarchy"

    def test_hierarchy_has_root(self, sample_graph):
        """There should be exactly one root node."""
        h = build_hierarchy(sample_graph)

        root_nodes = [n for n in h["nodes"] if n.get("level") == "root"]
        assert len(root_nodes) == 1, f"Expected 1 root, got {len(root_nodes)}"

    def test_metadata_is_populated(self, sample_graph):
        """Metadata should have real counts, not zeros."""
        h = build_hierarchy(sample_graph)

        assert h["metadata"]["total_leaf_nodes"] == 7
        assert h["metadata"]["total_files"] > 0
        assert h["metadata"]["total_modules"] > 0


# ─── Path Extraction Tests ─────────────────────────────────────────

class TestPathExtraction:
    def test_extract_file_from_qualified(self):
        assert _extract_file_from_path("src/auth/login.py::authenticate") == "src/auth/login.py"

    def test_extract_file_from_file_only(self):
        assert _extract_file_from_path("setup.py") == "setup.py"

    def test_extract_module_from_nested(self):
        assert _extract_module_from_file("src/auth/login.py") == "src/auth"

    def test_extract_module_from_root_file(self):
        assert _extract_module_from_file("setup.py") == "."


# ─── Hub Scoring Tests ─────────────────────────────────────────────

class TestHubScoring:
    def test_hub_scores_reflect_in_degree(self):
        """Nodes with more incoming edges should have higher hub scores."""
        nodes = [
            {"path": "popular"},
            {"path": "caller1"},
            {"path": "caller2"},
            {"path": "caller3"},
            {"path": "unpopular"},
        ]
        edges = [
            {"target": "popular"},
            {"target": "popular"},
            {"target": "popular"},
            {"target": "unpopular"},
        ]

        scores = compute_hub_scores(nodes, edges)

        assert scores["popular"] > scores["unpopular"], \
            "Higher in-degree should produce higher hub score"
        assert scores["caller1"] == 0.0, \
            "Nodes with no incoming edges should have 0 hub score"

    def test_log_damping(self):
        """Hub score should be log-damped, not linear."""
        nodes = [{"path": f"n{i}"} for i in range(100)]
        # One node has 50 incoming edges, another has 10
        edges = (
            [{"target": "n0"}] * 50 +
            [{"target": "n1"}] * 10
        )

        scores = compute_hub_scores(nodes, edges)

        # n0's score should be higher but not 5x higher (log-damped)
        ratio = scores["n0"] / scores["n1"] if scores["n1"] > 0 else float("inf")
        assert ratio < 5.0, f"Hub score ratio {ratio} suggests linear, not log-damped scaling"

    def test_identify_hubs_returns_sorted(self):
        """identify_hubs should return paths sorted by score descending."""
        scores = {"a": 0.8, "b": 0.3, "c": 0.9, "d": 0.1}
        hubs = identify_hubs(scores, threshold=0.5)

        assert hubs == ["c", "a"]  # only those >= 0.5, sorted desc


# ─── Granularity Detection Tests ───────────────────────────────────

class TestGranularity:
    def test_detects_common_artifacts(self, tmp_path):
        """Should detect SQL, YAML, Dockerfile, etc."""
        (tmp_path / "schema.sql").write_text("CREATE TABLE users (id INT);", encoding="utf-8")
        (tmp_path / "config.yaml").write_text("key: value\n", encoding="utf-8")
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
        (tmp_path / "requirements.txt").write_text("flask>=2.0\n", encoding="utf-8")
        (tmp_path / "app.py").write_text("# Python code\n", encoding="utf-8")

        artifacts = detect_coarse_artifacts(tmp_path)

        types_found = {a["artifact_type"] for a in artifacts}
        assert "sql" in types_found
        assert "config" in types_found
        assert "docker" in types_found
        assert "dependency" in types_found

        # .py files should NOT be detected as coarse artifacts
        paths = {a["path"] for a in artifacts}
        assert not any(p.endswith(".py") for p in paths)

    def test_all_artifacts_have_coarse_granularity(self, tmp_path):
        """Every detected artifact should be flagged as coarse."""
        (tmp_path / "data.json").write_text("{}", encoding="utf-8")
        artifacts = detect_coarse_artifacts(tmp_path)

        for a in artifacts:
            assert a["granularity"] == "coarse"
