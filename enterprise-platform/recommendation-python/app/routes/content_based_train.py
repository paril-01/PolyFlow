"""Content Based Train — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/content-based-train")
async def content_based_train_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Content Based Train."""
    from app.services.content_based_train import ContentBasedTrainService
    svc = ContentBasedTrainService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/content-based-train/status")
async def content_based_train_status() -> Dict[str, Any]:
    """Health check for Content Based Train."""
    return {"feature": "content_based_train", "status": "operational"}
