"""Reservation Expire — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/reservation-expire")
async def reservation_expire_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Reservation Expire."""
    from app.services.reservation_expire import ReservationExpireService
    svc = ReservationExpireService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/reservation-expire/status")
async def reservation_expire_status() -> Dict[str, Any]:
    """Health check for Reservation Expire."""
    return {"feature": "reservation_expire", "status": "operational"}
