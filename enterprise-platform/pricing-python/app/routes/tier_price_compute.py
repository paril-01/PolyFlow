"""Tier Price Compute — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/tier-price-compute")
async def tier_price_compute_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Tier Price Compute."""
    from app.services.tier_price_compute import TierPriceComputeService
    svc = TierPriceComputeService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/tier-price-compute/status")
async def tier_price_compute_status() -> Dict[str, Any]:
    """Health check for Tier Price Compute."""
    return {"feature": "tier_price_compute", "status": "operational"}
