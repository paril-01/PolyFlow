"""Coupon Validate — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/coupon-validate")
async def coupon_validate_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Coupon Validate."""
    from app.services.coupon_validate import CouponValidateService
    svc = CouponValidateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/coupon-validate/status")
async def coupon_validate_status() -> Dict[str, Any]:
    """Health check for Coupon Validate."""
    return {"feature": "coupon_validate", "status": "operational"}
