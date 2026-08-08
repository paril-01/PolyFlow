"""Warehouse Update — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/warehouse-update")
async def warehouse_update_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Warehouse Update."""
    from app.services.warehouse_update import WarehouseUpdateService
    svc = WarehouseUpdateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/warehouse-update/status")
async def warehouse_update_status() -> Dict[str, Any]:
    """Health check for Warehouse Update."""
    return {"feature": "warehouse_update", "status": "operational"}
