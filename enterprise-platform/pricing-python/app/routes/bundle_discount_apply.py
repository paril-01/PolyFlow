"""Bundle Discount Apply — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/bundle-discount-apply")
async def bundle_discount_apply_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Bundle Discount Apply."""
    from app.services.bundle_discount_apply import BundleDiscountApplyService
    svc = BundleDiscountApplyService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/bundle-discount-apply/status")
async def bundle_discount_apply_status() -> Dict[str, Any]:
    """Health check for Bundle Discount Apply."""
    return {"feature": "bundle_discount_apply", "status": "operational"}
