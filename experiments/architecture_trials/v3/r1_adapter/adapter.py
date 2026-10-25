"""
experiments/architecture_trials/v3/r1_adapter/adapter.py — R1 Existing RCIR Adapter.

Interfaces with the existing RCIR typed graph, ranker, and context compiler.
Exposes the standardized retrieval contract for fair head-to-head bakeoff evaluation:
- Query processing and symbol resolution against CanonicalEntityRegistry
- Graph neighbor traversal and edge scoring
- Context compilation with source span extraction
- Token budget enforcement
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
import sys
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))

try:
    from rcir.context.provider import LiveRCIRContextProvider, ContextSessionState
    from rcir.context.compiler import ContextCompiler
    from rcir.entities.canonical import CanonicalEntityRegistry
except ImportError:
    LiveRCIRContextProvider = None
    ContextCompiler = None
    CanonicalEntityRegistry = None


class R1RCIRAdapter:
    """
    R1: Adapter wrapping existing RCIR graph & compiler into the standardized retrieval contract.
    """

    def __init__(self, target_repo: Path, graph_path: Optional[Path] = None):
        self.target_repo = target_repo.resolve()
        self.graph_path = graph_path
        self.provider: Optional[Any] = None
        self.graph_data: Dict[str, Any] = {}

        if graph_path and graph_path.exists():
            try:
                with open(graph_path, "r", encoding="utf-8") as f:
                    self.graph_data = json.load(f)
            except Exception:
                self.graph_data = {}

        if LiveRCIRContextProvider and graph_path and graph_path.exists():
            try:
                self.provider = LiveRCIRContextProvider(target_repo=self.target_repo, graph_path=graph_path)
            except Exception:
                self.provider = None

    def retrieve(self, query: str, max_tokens: int = 4000) -> Dict[str, Any]:
        """
        Execute R1 retrieval using existing RCIR graph components.
        """
        # If live provider is available and functional, use it
        if self.provider:
            try:
                self.provider.session_state = ContextSessionState()
                sym = query.split()[0] if query.strip() else query
                res = self.provider.retrieve(symbol=sym, query=query, token_budget=max_tokens)
                packed_spans: List[Dict[str, Any]] = []
                for u in res.context_units:
                    packed_spans.append({
                        "file_path": u.source_file,
                        "start_line": u.line_range[0] if u.line_range else 1,
                        "end_line": u.line_range[1] if u.line_range else 50,
                        "snippet": u.content,
                        "symbol": u.entity_id,
                        "score": u.relevance_score,
                        "resolution_class": "STATIC_EXACT" if u.entity_id else "GRAPH_NEIGHBOR",
                    })
                return {
                    "retriever": "R1_EXISTING_RCIR",
                    "query": query,
                    "max_tokens": max_tokens,
                    "estimated_tokens": res.total_estimated_tokens,
                    "spans_count": len(packed_spans),
                    "spans": packed_spans,
                    "target_files": list({s["file_path"] for s in packed_spans}),
                }
            except Exception:
                pass

        # Fallback to direct graph traversal if provider initialization failed
        nodes = self.graph_data.get("nodes", {})
        edges = self.graph_data.get("edges", [])
        matched_spans: List[Dict[str, Any]] = []
        budget_chars = max_tokens * 4
        consumed_chars = 0

        # Case-insensitive query match on entity names
        q_lower = query.lower()
        node_items = nodes.items() if isinstance(nodes, dict) else enumerate(nodes)

        for _, node in node_items:
            n_name = node.get("name", "").lower()
            n_path = node.get("file") or node.get("path", "")
            if q_lower in n_name or n_name in q_lower:
                fpath = self.target_repo / n_path
                if fpath.exists() and str(fpath.resolve()).startswith(str(self.target_repo)):
                    try:
                        content = fpath.read_text(encoding="utf-8", errors="replace")
                        lines = content.splitlines()
                        s_line = node.get("line", 1)
                        e_line = node.get("end_line", min(s_line + 40, len(lines)))
                        snippet = "\n".join(lines[s_line - 1 : e_line])
                        if consumed_chars + len(snippet) <= budget_chars:
                            matched_spans.append({
                                "file_path": n_path,
                                "start_line": s_line,
                                "end_line": e_line,
                                "snippet": snippet,
                                "symbol": node.get("name"),
                                "score": 8.0,
                                "resolution_class": "STATIC_EXACT",
                            })
                            consumed_chars += len(snippet)
                    except Exception:
                        continue

        return {
            "retriever": "R1_EXISTING_RCIR",
            "query": query,
            "max_tokens": max_tokens,
            "estimated_tokens": consumed_chars // 4,
            "spans_count": len(matched_spans),
            "spans": matched_spans,
            "target_files": list({s["file_path"] for s in matched_spans}),
        }
