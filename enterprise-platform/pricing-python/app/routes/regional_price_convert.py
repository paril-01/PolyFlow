"""Regional Price Convert — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/regional-price-convert")
async def regional_price_convert_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Regional Price Convert."""
    from app.services.regional_price_convert import RegionalPriceConvertService
    svc = RegionalPriceConvertService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/regional-price-convert/status")
async def regional_price_convert_status() -> Dict[str, Any]:
    """Health check for Regional Price Convert."""
    return {"feature": "regional_price_convert", "status": "operational"}
