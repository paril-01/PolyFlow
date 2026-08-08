"""Coupon Create — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/coupon-create")
async def coupon_create_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Coupon Create."""
    from app.services.coupon_create import CouponCreateService
    svc = CouponCreateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/coupon-create/status")
async def coupon_create_status() -> Dict[str, Any]:
    """Health check for Coupon Create."""
    return {"feature": "coupon_create", "status": "operational"}
