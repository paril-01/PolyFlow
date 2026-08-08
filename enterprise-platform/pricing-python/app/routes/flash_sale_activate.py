"""Flash Sale Activate — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/flash-sale-activate")
async def flash_sale_activate_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Flash Sale Activate."""
    from app.services.flash_sale_activate import FlashSaleActivateService
    svc = FlashSaleActivateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/flash-sale-activate/status")
async def flash_sale_activate_status() -> Dict[str, Any]:
    """Health check for Flash Sale Activate."""
    return {"feature": "flash_sale_activate", "status": "operational"}
