"""Coupon Apply — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/coupon-apply")
async def coupon_apply_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Coupon Apply."""
    from app.services.coupon_apply import CouponApplyService
    svc = CouponApplyService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/coupon-apply/status")
async def coupon_apply_status() -> Dict[str, Any]:
    """Health check for Coupon Apply."""
    return {"feature": "coupon_apply", "status": "operational"}
