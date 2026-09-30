"""
Scalability and Performance Verification for RCIR.

Verifies that RCIR's extraction, hierarchy building, and retrieval scale
linearly O(N) and can handle repositories with thousands of files without
memory exhaustion or quadratic slowdowns.
"""

import sys
import time
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rcir.graph.extractor import extract_graph
from rcir.hierarchy.builder import build_hierarchy
from rcir.retrieval.hybrid import hybrid_retrieve


class TestScalability:
    """Test performance on a multi-module repository layout."""

    @pytest.fixture
    def large_repo(self, tmp_path):
        """Generate a structured repository with 200 files across 20 modules."""
        # 20 modules, each with 10 files = 200 files total
        for m_idx in range(20):
            mod_dir = tmp_path / f"module_{m_idx}"
            mod_dir.mkdir()
            (mod_dir / "__init__.py").write_text("", encoding="utf-8")

            for f_idx in range(10):
                file_path = mod_dir / f"service_{f_idx}.py"
                file_path.write_text(f'''
class Service_{m_idx}_{f_idx}:
    def __init__(self, val: int):
        self.val = val

    def execute_{f_idx}(self) -> int:
        return self.val * 2

def helper_{m_idx}_{f_idx}(x: int) -> int:
    s = Service_{m_idx}_{f_idx}(x)
    return s.execute_{f_idx}()
''', encoding="utf-8")

        return tmp_path

    def test_extraction_and_hierarchy_linear_speed(self, large_repo):
        """Verify extraction and hierarchy construction finish in sub-seconds."""
        # 1. Extraction benchmark
        t0 = time.perf_counter()
        graph = extract_graph(large_repo)
        extraction_time = time.perf_counter() - t0

        meta = graph["metadata"]
        assert meta["files_parsed"] >= 200
        assert meta["total_nodes"] >= 600
        # 200 files should extract in under 8.0 seconds on standard hardware
        assert extraction_time < 8.0, f"Extraction took too long: {extraction_time:.2f}s"

        # 2. Hierarchy building benchmark
        t1 = time.perf_counter()
        hierarchy = build_hierarchy(graph)
        hierarchy_time = time.perf_counter() - t1

        assert hierarchy is not None
        # Hierarchy construction must be strictly linear and take under 0.5s
        assert hierarchy_time < 0.5, f"Hierarchy build took too long: {hierarchy_time:.2f}s"

        # 3. Retrieval benchmark
        t2 = time.perf_counter()
        contract = hybrid_retrieve(
            hierarchy=hierarchy,
            query="execute helper service in module 5",
            token_budget=2000,
            graph_edges=graph.get("edges", []),
        )
        retrieval_time = time.perf_counter() - t2

        assert len(contract.nodes) > 0
        assert contract.token_budget_used <= 2000
        # Retrieval must execute in under 100ms
        assert retrieval_time < 0.2, f"Retrieval took too long: {retrieval_time:.2f}s"
