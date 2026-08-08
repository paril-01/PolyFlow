"""Supplier Create — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/supplier-create")
async def supplier_create_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Supplier Create."""
    from app.services.supplier_create import SupplierCreateService
    svc = SupplierCreateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/supplier-create/status")
async def supplier_create_status() -> Dict[str, Any]:
    """Health check for Supplier Create."""
    return {"feature": "supplier_create", "status": "operational"}
