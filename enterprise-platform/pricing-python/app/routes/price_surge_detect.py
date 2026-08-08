"""Price Surge Detect — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/price-surge-detect")
async def price_surge_detect_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Price Surge Detect."""
    from app.services.price_surge_detect import PriceSurgeDetectService
    svc = PriceSurgeDetectService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/price-surge-detect/status")
async def price_surge_detect_status() -> Dict[str, Any]:
    """Health check for Price Surge Detect."""
    return {"feature": "price_surge_detect", "status": "operational"}
