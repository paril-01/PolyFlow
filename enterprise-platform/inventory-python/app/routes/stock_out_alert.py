"""Stock Out Alert — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/stock-out-alert")
async def stock_out_alert_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Stock Out Alert."""
    from app.services.stock_out_alert import StockOutAlertService
    svc = StockOutAlertService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/stock-out-alert/status")
async def stock_out_alert_status() -> Dict[str, Any]:
    """Health check for Stock Out Alert."""
    return {"feature": "stock_out_alert", "status": "operational"}
