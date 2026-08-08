"""Semantic Search Index — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/semantic-search-index")
async def semantic_search_index_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Semantic Search Index."""
    from app.services.semantic_search_index import SemanticSearchIndexService
    svc = SemanticSearchIndexService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/semantic-search-index/status")
async def semantic_search_index_status() -> Dict[str, Any]:
    """Health check for Semantic Search Index."""
    return {"feature": "semantic_search_index", "status": "operational"}
