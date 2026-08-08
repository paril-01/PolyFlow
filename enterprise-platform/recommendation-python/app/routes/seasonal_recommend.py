"""Seasonal Recommend — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/seasonal-recommend")
async def seasonal_recommend_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Seasonal Recommend."""
    from app.services.seasonal_recommend import SeasonalRecommendService
    svc = SeasonalRecommendService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/seasonal-recommend/status")
async def seasonal_recommend_status() -> Dict[str, Any]:
    """Health check for Seasonal Recommend."""
    return {"feature": "seasonal_recommend", "status": "operational"}
