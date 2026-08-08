"""Similar Products Fetch — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/similar-products-fetch")
async def similar_products_fetch_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Similar Products Fetch."""
    from app.services.similar_products_fetch import SimilarProductsFetchService
    svc = SimilarProductsFetchService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/similar-products-fetch/status")
async def similar_products_fetch_status() -> Dict[str, Any]:
    """Health check for Similar Products Fetch."""
    return {"feature": "similar_products_fetch", "status": "operational"}
