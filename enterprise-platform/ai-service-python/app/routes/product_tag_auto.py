"""Product Tag Auto — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/product-tag-auto")
async def product_tag_auto_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Product Tag Auto."""
    from app.services.product_tag_auto import ProductTagAutoService
    svc = ProductTagAutoService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/product-tag-auto/status")
async def product_tag_auto_status() -> Dict[str, Any]:
    """Health check for Product Tag Auto."""
    return {"feature": "product_tag_auto", "status": "operational"}
