"""Image Similarity — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/image-similarity")
async def image_similarity_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Image Similarity."""
    from app.services.image_similarity import ImageSimilarityService
    svc = ImageSimilarityService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/image-similarity/status")
async def image_similarity_status() -> Dict[str, Any]:
    """Health check for Image Similarity."""
    return {"feature": "image_similarity", "status": "operational"}
