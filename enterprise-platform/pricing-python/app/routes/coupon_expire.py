"""Coupon Expire — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/coupon-expire")
async def coupon_expire_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Coupon Expire."""
    from app.services.coupon_expire import CouponExpireService
    svc = CouponExpireService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/coupon-expire/status")
async def coupon_expire_status() -> Dict[str, Any]:
    """Health check for Coupon Expire."""
    return {"feature": "coupon_expire", "status": "operational"}
