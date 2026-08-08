"""Warehouse Deactivate — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/warehouse-deactivate")
async def warehouse_deactivate_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Warehouse Deactivate."""
    from app.services.warehouse_deactivate import WarehouseDeactivateService
    svc = WarehouseDeactivateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/warehouse-deactivate/status")
async def warehouse_deactivate_status() -> Dict[str, Any]:
    """Health check for Warehouse Deactivate."""
    return {"feature": "warehouse_deactivate", "status": "operational"}
