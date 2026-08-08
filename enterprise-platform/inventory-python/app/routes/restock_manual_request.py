"""Restock Manual Request — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/restock-manual-request")
async def restock_manual_request_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Restock Manual Request."""
    from app.services.restock_manual_request import RestockManualRequestService
    svc = RestockManualRequestService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/restock-manual-request/status")
async def restock_manual_request_status() -> Dict[str, Any]:
    """Health check for Restock Manual Request."""
    return {"feature": "restock_manual_request", "status": "operational"}
