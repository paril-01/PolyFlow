"""Reservation Create — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/reservation-create")
async def reservation_create_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Reservation Create."""
    from app.services.reservation_create import ReservationCreateService
    svc = ReservationCreateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/reservation-create/status")
async def reservation_create_status() -> Dict[str, Any]:
    """Health check for Reservation Create."""
    return {"feature": "reservation_create", "status": "operational"}
