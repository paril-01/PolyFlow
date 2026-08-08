"""Regional Currency Detect — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/regional-currency-detect")
async def regional_currency_detect_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Regional Currency Detect."""
    from app.services.regional_currency_detect import RegionalCurrencyDetectService
    svc = RegionalCurrencyDetectService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/regional-currency-detect/status")
async def regional_currency_detect_status() -> Dict[str, Any]:
    """Health check for Regional Currency Detect."""
    return {"feature": "regional_currency_detect", "status": "operational"}
