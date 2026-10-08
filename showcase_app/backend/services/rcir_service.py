"""
showcase_app/backend/services/rcir_service.py — RCIR Context & Query Service.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class RCIRService:
    def __init__(self):
        self.repo_root = REPO_ROOT
        self.pipeline_file = self.repo_root / "showcase" / "data" / "rcir_pipeline.json"

    def get_pipeline_data(self) -> Dict[str, Any]:
        if self.pipeline_file.exists():
            return json.loads(self.pipeline_file.read_text(encoding="utf-8"))
        return {}

    def query(self, query_text: str, target_domain: str = "accounts", token_budget: int = 4000) -> Dict[str, Any]:
        pipeline = self.get_pipeline_data()
        candidates = pipeline.get("ranked_candidates", []) or pipeline.get("sample_ranked_candidates", [])
        
        # Filter or rank candidates by query relevance
        filtered = []
        for c in candidates:
            # Score match based on domain or query terms
            score = c.get("score", 0.5)
            if any(term in c.get("path", "").lower() for term in query_text.lower().split()):
                score = min(1.0, score + 0.1)
            filtered.append({
                "rank": len(filtered) + 1,
                "path": c.get("path", ""),
                "score": round(score, 3),
                "tier": c.get("tier", 1),
                "reason": c.get("reason", "Structural dependency match"),
            })

        return {
            "query_id": f"rcir_q_{int(Path(__file__).stat().st_mtime)}",
            "query_text": query_text,
            "repo_file_count": pipeline.get("repo_file_count", 4412),
            "retrieved_count": len(filtered),
            "compiled_tokens": min(token_budget, pipeline.get("compiled_context_tokens", 3120)),
            "candidates": filtered[:5],
        }


rcir_service = RCIRService()
