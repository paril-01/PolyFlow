"""Bundle Price Compute — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/bundle-price-compute")
async def bundle_price_compute_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Bundle Price Compute."""
    from app.services.bundle_price_compute import BundlePriceComputeService
    svc = BundlePriceComputeService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/bundle-price-compute/status")
async def bundle_price_compute_status() -> Dict[str, Any]:
    """Health check for Bundle Price Compute."""
    return {"feature": "bundle_price_compute", "status": "operational"}
