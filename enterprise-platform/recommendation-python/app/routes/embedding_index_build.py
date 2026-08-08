"""Embedding Index Build — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/embedding-index-build")
async def embedding_index_build_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Embedding Index Build."""
    from app.services.embedding_index_build import EmbeddingIndexBuildService
    svc = EmbeddingIndexBuildService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/embedding-index-build/status")
async def embedding_index_build_status() -> Dict[str, Any]:
    """Health check for Embedding Index Build."""
    return {"feature": "embedding_index_build", "status": "operational"}
