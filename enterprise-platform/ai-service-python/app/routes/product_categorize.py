"""Product Categorize — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/product-categorize")
async def product_categorize_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Product Categorize."""
    from app.services.product_categorize import ProductCategorizeService
    svc = ProductCategorizeService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/product-categorize/status")
async def product_categorize_status() -> Dict[str, Any]:
    """Health check for Product Categorize."""
    return {"feature": "product_categorize", "status": "operational"}
