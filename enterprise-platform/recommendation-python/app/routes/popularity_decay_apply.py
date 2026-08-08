"""Popularity Decay Apply — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/popularity-decay-apply")
async def popularity_decay_apply_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Popularity Decay Apply."""
    from app.services.popularity_decay_apply import PopularityDecayApplyService
    svc = PopularityDecayApplyService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/popularity-decay-apply/status")
async def popularity_decay_apply_status() -> Dict[str, Any]:
    """Health check for Popularity Decay Apply."""
    return {"feature": "popularity_decay_apply", "status": "operational"}
