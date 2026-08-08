"""Flash Sale Create — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/flash-sale-create")
async def flash_sale_create_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Flash Sale Create."""
    from app.services.flash_sale_create import FlashSaleCreateService
    svc = FlashSaleCreateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/flash-sale-create/status")
async def flash_sale_create_status() -> Dict[str, Any]:
    """Health check for Flash Sale Create."""
    return {"feature": "flash_sale_create", "status": "operational"}
