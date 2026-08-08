"""Similar Products Compute — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/similar-products-compute")
async def similar_products_compute_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Similar Products Compute."""
    from app.services.similar_products_compute import SimilarProductsComputeService
    svc = SimilarProductsComputeService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/similar-products-compute/status")
async def similar_products_compute_status() -> Dict[str, Any]:
    """Health check for Similar Products Compute."""
    return {"feature": "similar_products_compute", "status": "operational"}
