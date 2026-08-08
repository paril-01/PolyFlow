"""Restock Approval — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/restock-approval")
async def restock_approval_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Restock Approval."""
    from app.services.restock_approval import RestockApprovalService
    svc = RestockApprovalService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/restock-approval/status")
async def restock_approval_status() -> Dict[str, Any]:
    """Health check for Restock Approval."""
    return {"feature": "restock_approval", "status": "operational"}
