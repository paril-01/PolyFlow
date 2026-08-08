"""Image Classify — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/image-classify")
async def image_classify_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Image Classify."""
    from app.services.image_classify import ImageClassifyService
    svc = ImageClassifyService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/image-classify/status")
async def image_classify_status() -> Dict[str, Any]:
    """Health check for Image Classify."""
    return {"feature": "image_classify", "status": "operational"}
