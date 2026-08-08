"""Restock Auto Trigger — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/restock-auto-trigger")
async def restock_auto_trigger_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Restock Auto Trigger."""
    from app.services.restock_auto_trigger import RestockAutoTriggerService
    svc = RestockAutoTriggerService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/restock-auto-trigger/status")
async def restock_auto_trigger_status() -> Dict[str, Any]:
    """Health check for Restock Auto Trigger."""
    return {"feature": "restock_auto_trigger", "status": "operational"}
