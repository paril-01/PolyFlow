"""Cross Sell Compute — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/cross-sell-compute")
async def cross_sell_compute_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Cross Sell Compute."""
    from app.services.cross_sell_compute import CrossSellComputeService
    svc = CrossSellComputeService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/cross-sell-compute/status")
async def cross_sell_compute_status() -> Dict[str, Any]:
    """Health check for Cross Sell Compute."""
    return {"feature": "cross_sell_compute", "status": "operational"}
