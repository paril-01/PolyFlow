"""Semantic Search Rerank — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/semantic-search-rerank")
async def semantic_search_rerank_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Semantic Search Rerank."""
    from app.services.semantic_search_rerank import SemanticSearchRerankService
    svc = SemanticSearchRerankService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/semantic-search-rerank/status")
async def semantic_search_rerank_status() -> Dict[str, Any]:
    """Health check for Semantic Search Rerank."""
    return {"feature": "semantic_search_rerank", "status": "operational"}
