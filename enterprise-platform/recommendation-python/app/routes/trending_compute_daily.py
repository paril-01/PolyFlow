"""Trending Compute Daily — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/trending-compute-daily")
async def trending_compute_daily_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Trending Compute Daily."""
    from app.services.trending_compute_daily import TrendingComputeDailyService
    svc = TrendingComputeDailyService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/trending-compute-daily/status")
async def trending_compute_daily_status() -> Dict[str, Any]:
    """Health check for Trending Compute Daily."""
    return {"feature": "trending_compute_daily", "status": "operational"}
