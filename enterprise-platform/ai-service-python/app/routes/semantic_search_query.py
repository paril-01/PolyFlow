"""Semantic Search Query — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/semantic-search-query")
async def semantic_search_query_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Semantic Search Query."""
    from app.services.semantic_search_query import SemanticSearchQueryService
    svc = SemanticSearchQueryService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/semantic-search-query/status")
async def semantic_search_query_status() -> Dict[str, Any]:
    """Health check for Semantic Search Query."""
    return {"feature": "semantic_search_query", "status": "operational"}
