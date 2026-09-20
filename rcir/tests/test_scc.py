"""
Tests for Tarjan's SCC algorithm and size-capped collapsing.

Uses known cyclic graph structures with independently verifiable SCCs.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rcir.graph.scc import tarjan_scc, collapse_sccs


class TestTarjanSCC:
    def test_no_cycles(self):
        """A DAG should produce only trivial single-node SCCs."""
        nodes = ["a", "b", "c", "d"]
        edges = [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "a", "target": "d"},
        ]
        sccs = tarjan_scc(nodes, edges)

        # All SCCs should be single-node
        for scc in sccs:
            assert len(scc) == 1, f"Non-trivial SCC in a DAG: {scc}"

    def test_simple_cycle(self):
        """Two nodes calling each other should form a single SCC."""
        nodes = ["a", "b"]
        edges = [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "a"},
        ]
        sccs = tarjan_scc(nodes, edges)

        # Should find one SCC containing both nodes
        multi_sccs = [s for s in sccs if len(s) > 1]
        assert len(multi_sccs) == 1
        assert set(multi_sccs[0]) == {"a", "b"}

    def test_three_node_cycle(self):
        """A→B→C→A should form a single SCC."""
        nodes = ["a", "b", "c"]
        edges = [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "a"},
        ]
        sccs = tarjan_scc(nodes, edges)

        multi_sccs = [s for s in sccs if len(s) > 1]
        assert len(multi_sccs) == 1
        assert set(multi_sccs[0]) == {"a", "b", "c"}

    def test_two_separate_cycles(self):
        """Two independent cycles should produce two separate SCCs."""
        nodes = ["a", "b", "c", "d"]
        edges = [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "a"},
            {"source": "c", "target": "d"},
            {"source": "d", "target": "c"},
        ]
        sccs = tarjan_scc(nodes, edges)

        multi_sccs = [s for s in sccs if len(s) > 1]
        assert len(multi_sccs) == 2

        scc_sets = [set(s) for s in multi_sccs]
        assert {"a", "b"} in scc_sets
        assert {"c", "d"} in scc_sets

    def test_self_loop(self):
        """A self-calling function should form an SCC of size 1."""
        nodes = ["a"]
        edges = [{"source": "a", "target": "a"}]
        sccs = tarjan_scc(nodes, edges)

        assert len(sccs) == 1
        assert sccs[0] == ["a"]

    def test_ignores_edges_to_unknown_nodes(self):
        """Edges targeting nodes not in the node list should be ignored."""
        nodes = ["a", "b"]
        edges = [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "unknown_node"},
        ]
        sccs = tarjan_scc(nodes, edges)

        # No cycle, all single-node SCCs
        for scc in sccs:
            assert len(scc) == 1


class TestCollapseSccs:
    def test_collapse_small_scc(self):
        """SCCs under threshold should be collapsed into meta-nodes."""
        graph = {
            "nodes": [
                {"path": "a", "kind": "function"},
                {"path": "b", "kind": "function"},
                {"path": "c", "kind": "function"},
            ],
            "edges": [
                {"source": "a", "target": "b", "type": "calls", "confidence": 1.0},
                {"source": "b", "target": "a", "type": "calls", "confidence": 1.0},
                {"source": "c", "target": "a", "type": "calls", "confidence": 1.0},
            ],
        }
        result = collapse_sccs(graph, threshold=5)

        # a and b form a cycle, should be collapsed
        scc_nodes = [n for n in result["nodes"] if n.get("kind") == "scc_collapsed"]
        assert len(scc_nodes) == 1
        assert set(scc_nodes[0]["members"]) == {"a", "b"}

        # c should still exist as a regular node
        regular_paths = {n["path"] for n in result["nodes"] if n.get("kind") != "scc_collapsed"}
        assert "c" in regular_paths

    def test_preserve_large_scc(self):
        """SCCs above threshold should NOT be collapsed."""
        # Create a cycle of 5 nodes
        nodes = [{"path": f"n{i}", "kind": "function"} for i in range(5)]
        edges = [
            {"source": f"n{i}", "target": f"n{(i+1)%5}", "type": "calls", "confidence": 1.0}
            for i in range(5)
        ]
        graph = {"nodes": nodes, "edges": edges}

        # Threshold = 3, so a 5-node SCC should NOT be collapsed
        result = collapse_sccs(graph, threshold=3)

        scc_nodes = [n for n in result["nodes"] if n.get("kind") == "scc_collapsed"]
        assert len(scc_nodes) == 0, "Large SCC should not be collapsed"

        # All nodes should still be present and annotated
        for node in result["nodes"]:
            assert "scc_group" in node, f"Node {node['path']} missing scc_group annotation"

    def test_no_cycles_produces_no_scc_info(self):
        """A DAG should have 0 SCCs."""
        graph = {
            "nodes": [
                {"path": "a", "kind": "function"},
                {"path": "b", "kind": "function"},
            ],
            "edges": [
                {"source": "a", "target": "b", "type": "calls", "confidence": 1.0},
            ],
        }
        result = collapse_sccs(graph)
        assert result["scc_info"]["total_sccs"] == 0
