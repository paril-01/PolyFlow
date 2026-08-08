"""New Arrival Boost — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/new-arrival-boost")
async def new_arrival_boost_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for New Arrival Boost."""
    from app.services.new_arrival_boost import NewArrivalBoostService
    svc = NewArrivalBoostService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/new-arrival-boost/status")
async def new_arrival_boost_status() -> Dict[str, Any]:
    """Health check for New Arrival Boost."""
    return {"feature": "new_arrival_boost", "status": "operational"}
