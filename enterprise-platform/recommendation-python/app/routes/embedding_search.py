"""Embedding Search — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/embedding-search")
async def embedding_search_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Embedding Search."""
    from app.services.embedding_search import EmbeddingSearchService
    svc = EmbeddingSearchService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/embedding-search/status")
async def embedding_search_status() -> Dict[str, Any]:
    """Health check for Embedding Search."""
    return {"feature": "embedding_search", "status": "operational"}
