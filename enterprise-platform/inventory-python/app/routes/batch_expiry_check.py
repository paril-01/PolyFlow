"""Batch Expiry Check — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/batch-expiry-check")
async def batch_expiry_check_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Batch Expiry Check."""
    from app.services.batch_expiry_check import BatchExpiryCheckService
    svc = BatchExpiryCheckService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/batch-expiry-check/status")
async def batch_expiry_check_status() -> Dict[str, Any]:
    """Health check for Batch Expiry Check."""
    return {"feature": "batch_expiry_check", "status": "operational"}
