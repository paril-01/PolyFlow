"""Recently Viewed Record — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/recently-viewed-record")
async def recently_viewed_record_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Recently Viewed Record."""
    from app.services.recently_viewed_record import RecentlyViewedRecordService
    svc = RecentlyViewedRecordService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/recently-viewed-record/status")
async def recently_viewed_record_status() -> Dict[str, Any]:
    """Health check for Recently Viewed Record."""
    return {"feature": "recently_viewed_record", "status": "operational"}
