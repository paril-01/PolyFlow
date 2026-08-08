"""Warehouse Sync — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/warehouse-sync")
async def warehouse_sync_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Warehouse Sync."""
    from app.services.warehouse_sync import WarehouseSyncService
    svc = WarehouseSyncService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/warehouse-sync/status")
async def warehouse_sync_status() -> Dict[str, Any]:
    """Health check for Warehouse Sync."""
    return {"feature": "warehouse_sync", "status": "operational"}
