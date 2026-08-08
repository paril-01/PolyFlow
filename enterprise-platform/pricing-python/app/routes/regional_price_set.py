"""Regional Price Set — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/regional-price-set")
async def regional_price_set_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Regional Price Set."""
    from app.services.regional_price_set import RegionalPriceSetService
    svc = RegionalPriceSetService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/regional-price-set/status")
async def regional_price_set_status() -> Dict[str, Any]:
    """Health check for Regional Price Set."""
    return {"feature": "regional_price_set", "status": "operational"}
