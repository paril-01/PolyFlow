"""Tax Exempt Check — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/tax-exempt-check")
async def tax_exempt_check_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Tax Exempt Check."""
    from app.services.tax_exempt_check import TaxExemptCheckService
    svc = TaxExemptCheckService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/tax-exempt-check/status")
async def tax_exempt_check_status() -> Dict[str, Any]:
    """Health check for Tax Exempt Check."""
    return {"feature": "tax_exempt_check", "status": "operational"}
