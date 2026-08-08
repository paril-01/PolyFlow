"""Stock Level Get — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/stock-level-get")
async def stock_level_get_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Stock Level Get."""
    from app.services.stock_level_get import StockLevelGetService
    svc = StockLevelGetService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/stock-level-get/status")
async def stock_level_get_status() -> Dict[str, Any]:
    """Health check for Stock Level Get."""
    return {"feature": "stock_level_get", "status": "operational"}
