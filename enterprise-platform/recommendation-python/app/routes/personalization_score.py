"""Personalization Score — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/personalization-score")
async def personalization_score_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Personalization Score."""
    from app.services.personalization_score import PersonalizationScoreService
    svc = PersonalizationScoreService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/personalization-score/status")
async def personalization_score_status() -> Dict[str, Any]:
    """Health check for Personalization Score."""
    return {"feature": "personalization_score", "status": "operational"}
