"""Content Based Predict — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/content-based-predict")
async def content_based_predict_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Content Based Predict."""
    from app.services.content_based_predict import ContentBasedPredictService
    svc = ContentBasedPredictService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/content-based-predict/status")
async def content_based_predict_status() -> Dict[str, Any]:
    """Health check for Content Based Predict."""
    return {"feature": "content_based_predict", "status": "operational"}
