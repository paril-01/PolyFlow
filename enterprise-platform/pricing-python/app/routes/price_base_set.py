"""Price Base Set — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/price-base-set")
async def price_base_set_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Price Base Set."""
    from app.services.price_base_set import PriceBaseSetService
    svc = PriceBaseSetService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/price-base-set/status")
async def price_base_set_status() -> Dict[str, Any]:
    """Health check for Price Base Set."""
    return {"feature": "price_base_set", "status": "operational"}
