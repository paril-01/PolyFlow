"""Diversity Inject — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/diversity-inject")
async def diversity_inject_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Diversity Inject."""
    from app.services.diversity_inject import DiversityInjectService
    svc = DiversityInjectService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/diversity-inject/status")
async def diversity_inject_status() -> Dict[str, Any]:
    """Health check for Diversity Inject."""
    return {"feature": "diversity_inject", "status": "operational"}
