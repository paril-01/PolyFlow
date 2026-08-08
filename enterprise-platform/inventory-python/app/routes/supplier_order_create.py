"""Supplier Order Create — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/supplier-order-create")
async def supplier_order_create_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Supplier Order Create."""
    from app.services.supplier_order_create import SupplierOrderCreateService
    svc = SupplierOrderCreateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/supplier-order-create/status")
async def supplier_order_create_status() -> Dict[str, Any]:
    """Health check for Supplier Order Create."""
    return {"feature": "supplier_order_create", "status": "operational"}
