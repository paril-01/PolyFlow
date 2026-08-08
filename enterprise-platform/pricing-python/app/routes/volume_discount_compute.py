"""Volume Discount Compute — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/volume-discount-compute")
async def volume_discount_compute_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Volume Discount Compute."""
    from app.services.volume_discount_compute import VolumeDiscountComputeService
    svc = VolumeDiscountComputeService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/volume-discount-compute/status")
async def volume_discount_compute_status() -> Dict[str, Any]:
    """Health check for Volume Discount Compute."""
    return {"feature": "volume_discount_compute", "status": "operational"}
