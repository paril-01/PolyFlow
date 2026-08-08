"""Recently Viewed Fetch — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/recently-viewed-fetch")
async def recently_viewed_fetch_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Recently Viewed Fetch."""
    from app.services.recently_viewed_fetch import RecentlyViewedFetchService
    svc = RecentlyViewedFetchService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/recently-viewed-fetch/status")
async def recently_viewed_fetch_status() -> Dict[str, Any]:
    """Health check for Recently Viewed Fetch."""
    return {"feature": "recently_viewed_fetch", "status": "operational"}
