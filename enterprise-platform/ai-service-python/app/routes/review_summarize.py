"""Review Summarize — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/review-summarize")
async def review_summarize_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Review Summarize."""
    from app.services.review_summarize import ReviewSummarizeService
    svc = ReviewSummarizeService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/review-summarize/status")
async def review_summarize_status() -> Dict[str, Any]:
    """Health check for Review Summarize."""
    return {"feature": "review_summarize", "status": "operational"}
