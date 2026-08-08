"""Flash Sale Deactivate — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/flash-sale-deactivate")
async def flash_sale_deactivate_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Flash Sale Deactivate."""
    from app.services.flash_sale_deactivate import FlashSaleDeactivateService
    svc = FlashSaleDeactivateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/flash-sale-deactivate/status")
async def flash_sale_deactivate_status() -> Dict[str, Any]:
    """Health check for Flash Sale Deactivate."""
    return {"feature": "flash_sale_deactivate", "status": "operational"}
