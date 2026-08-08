"""Stock Level Update — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/stock-level-update")
async def stock_level_update_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Stock Level Update."""
    from app.services.stock_level_update import StockLevelUpdateService
    svc = StockLevelUpdateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/stock-level-update/status")
async def stock_level_update_status() -> Dict[str, Any]:
    """Health check for Stock Level Update."""
    return {"feature": "stock_level_update", "status": "operational"}
