"""Image Generate Thumbnail — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/image-generate-thumbnail")
async def image_generate_thumbnail_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Image Generate Thumbnail."""
    from app.services.image_generate_thumbnail import ImageGenerateThumbnailService
    svc = ImageGenerateThumbnailService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/image-generate-thumbnail/status")
async def image_generate_thumbnail_status() -> Dict[str, Any]:
    """Health check for Image Generate Thumbnail."""
    return {"feature": "image_generate_thumbnail", "status": "operational"}
