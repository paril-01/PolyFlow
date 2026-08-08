"""Product Tag Suggest — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/product-tag-suggest")
async def product_tag_suggest_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Product Tag Suggest."""
    from app.services.product_tag_suggest import ProductTagSuggestService
    svc = ProductTagSuggestService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/product-tag-suggest/status")
async def product_tag_suggest_status() -> Dict[str, Any]:
    """Health check for Product Tag Suggest."""
    return {"feature": "product_tag_suggest", "status": "operational"}
