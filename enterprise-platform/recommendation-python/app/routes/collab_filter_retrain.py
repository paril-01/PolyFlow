"""Collab Filter Retrain — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/collab-filter-retrain")
async def collab_filter_retrain_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Collab Filter Retrain."""
    from app.services.collab_filter_retrain import CollabFilterRetrainService
    svc = CollabFilterRetrainService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/collab-filter-retrain/status")
async def collab_filter_retrain_status() -> Dict[str, Any]:
    """Health check for Collab Filter Retrain."""
    return {"feature": "collab_filter_retrain", "status": "operational"}
