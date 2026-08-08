"""Popularity Score Compute — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/popularity-score-compute")
async def popularity_score_compute_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Popularity Score Compute."""
    from app.services.popularity_score_compute import PopularityScoreComputeService
    svc = PopularityScoreComputeService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/popularity-score-compute/status")
async def popularity_score_compute_status() -> Dict[str, Any]:
    """Health check for Popularity Score Compute."""
    return {"feature": "popularity_score_compute", "status": "operational"}
