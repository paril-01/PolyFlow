"""Trending Compute Hourly — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/trending-compute-hourly")
async def trending_compute_hourly_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Trending Compute Hourly."""
    from app.services.trending_compute_hourly import TrendingComputeHourlyService
    svc = TrendingComputeHourlyService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/trending-compute-hourly/status")
async def trending_compute_hourly_status() -> Dict[str, Any]:
    """Health check for Trending Compute Hourly."""
    return {"feature": "trending_compute_hourly", "status": "operational"}
