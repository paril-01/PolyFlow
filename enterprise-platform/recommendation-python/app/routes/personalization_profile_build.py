"""Personalization Profile Build — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/personalization-profile-build")
async def personalization_profile_build_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Personalization Profile Build."""
    from app.services.personalization_profile_build import PersonalizationProfileBuildService
    svc = PersonalizationProfileBuildService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/personalization-profile-build/status")
async def personalization_profile_build_status() -> Dict[str, Any]:
    """Health check for Personalization Profile Build."""
    return {"feature": "personalization_profile_build", "status": "operational"}
