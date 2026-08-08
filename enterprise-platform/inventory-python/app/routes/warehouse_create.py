"""Warehouse Create — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/warehouse-create")
async def warehouse_create_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Warehouse Create."""
    from app.services.warehouse_create import WarehouseCreateService
    svc = WarehouseCreateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/warehouse-create/status")
async def warehouse_create_status() -> Dict[str, Any]:
    """Health check for Warehouse Create."""
    return {"feature": "warehouse_create", "status": "operational"}
