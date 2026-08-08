"""Reservation Release — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/reservation-release")
async def reservation_release_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Reservation Release."""
    from app.services.reservation_release import ReservationReleaseService
    svc = ReservationReleaseService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/reservation-release/status")
async def reservation_release_status() -> Dict[str, Any]:
    """Health check for Reservation Release."""
    return {"feature": "reservation_release", "status": "operational"}
