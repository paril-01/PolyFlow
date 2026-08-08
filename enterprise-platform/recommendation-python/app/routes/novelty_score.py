"""Novelty Score — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/novelty-score")
async def novelty_score_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Novelty Score."""
    from app.services.novelty_score import NoveltyScoreService
    svc = NoveltyScoreService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/novelty-score/status")
async def novelty_score_status() -> Dict[str, Any]:
    """Health check for Novelty Score."""
    return {"feature": "novelty_score", "status": "operational"}
