"""Upsell Compute — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/upsell-compute")
async def upsell_compute_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Upsell Compute."""
    from app.services.upsell_compute import UpsellComputeService
    svc = UpsellComputeService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/upsell-compute/status")
async def upsell_compute_status() -> Dict[str, Any]:
    """Health check for Upsell Compute."""
    return {"feature": "upsell_compute", "status": "operational"}
