"""Tax Rate Lookup — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/tax-rate-lookup")
async def tax_rate_lookup_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Tax Rate Lookup."""
    from app.services.tax_rate_lookup import TaxRateLookupService
    svc = TaxRateLookupService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/tax-rate-lookup/status")
async def tax_rate_lookup_status() -> Dict[str, Any]:
    """Health check for Tax Rate Lookup."""
    return {"feature": "tax_rate_lookup", "status": "operational"}
