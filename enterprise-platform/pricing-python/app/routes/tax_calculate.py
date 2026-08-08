"""Tax Calculate — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/tax-calculate")
async def tax_calculate_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Tax Calculate."""
    from app.services.tax_calculate import TaxCalculateService
    svc = TaxCalculateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/tax-calculate/status")
async def tax_calculate_status() -> Dict[str, Any]:
    """Health check for Tax Calculate."""
    return {"feature": "tax_calculate", "status": "operational"}
