"""Supplier Deactivate — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/supplier-deactivate")
async def supplier_deactivate_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Supplier Deactivate."""
    from app.services.supplier_deactivate import SupplierDeactivateService
    svc = SupplierDeactivateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/supplier-deactivate/status")
async def supplier_deactivate_status() -> Dict[str, Any]:
    """Health check for Supplier Deactivate."""
    return {"feature": "supplier_deactivate", "status": "operational"}
