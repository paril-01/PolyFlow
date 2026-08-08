"""Embedding Generate — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/embedding-generate")
async def embedding_generate_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Embedding Generate."""
    from app.services.embedding_generate import EmbeddingGenerateService
    svc = EmbeddingGenerateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/embedding-generate/status")
async def embedding_generate_status() -> Dict[str, Any]:
    """Health check for Embedding Generate."""
    return {"feature": "embedding_generate", "status": "operational"}
