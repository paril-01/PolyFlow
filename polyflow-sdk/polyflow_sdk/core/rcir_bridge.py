"""
PolyFlow SDK RCIR Bridge.

Provides high-level programmatic access to RCIR graph extraction,
semantic code hierarchy construction, hybrid retrieval, and change impact analysis.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Bridge to RCIR core
try:
    from rcir.graph.extractor import extract_graph
    from rcir.hierarchy.builder import build_hierarchy
    from rcir.retrieval.hybrid import hybrid_retrieve
    from rcir.impact import generate_change_impact_report
    RCIR_AVAILABLE = True
except ImportError:
    RCIR_AVAILABLE = False


class RcirBridge:
    """Interface to RCIR dependency analysis engine."""

    @classmethod
    def is_available(cls) -> bool:
        return RCIR_AVAILABLE

    @classmethod
    def extract_repository(
        cls,
        repo_path: str | Path,
        exclude_dirs: Optional[set[str]] = None
    ) -> Dict[str, Any]:
        """Extract multi-language dependency graph from a repository."""
        if not RCIR_AVAILABLE:
            raise RuntimeError("RCIR dependency analysis engine is not found on PYTHONPATH.")
        return extract_graph(
            repo_path=str(repo_path),
            exclude_dirs=exclude_dirs or {".git", "vendor", "node_modules", "3rdparty"}
        )

    @classmethod
    def analyze_impact(
        cls,
        graph: Dict[str, Any],
        target_symbol: str,
        repo_path: str | Path = "."
    ) -> Any:
        """Compute blast-radius impact analysis for a changed target symbol."""
        if not RCIR_AVAILABLE:
            raise RuntimeError("RCIR dependency analysis engine is not found on PYTHONPATH.")
        return generate_change_impact_report(repo_path=str(repo_path), target_symbol=target_symbol, graph=graph)
