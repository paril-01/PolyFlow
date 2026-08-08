"""Stock Low Alert — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/stock-low-alert")
async def stock_low_alert_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Stock Low Alert."""
    from app.services.stock_low_alert import StockLowAlertService
    svc = StockLowAlertService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/stock-low-alert/status")
async def stock_low_alert_status() -> Dict[str, Any]:
    """Health check for Stock Low Alert."""
    return {"feature": "stock_low_alert", "status": "operational"}
