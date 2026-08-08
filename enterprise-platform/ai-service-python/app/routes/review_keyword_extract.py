"""Review Keyword Extract — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/review-keyword-extract")
async def review_keyword_extract_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Review Keyword Extract."""
    from app.services.review_keyword_extract import ReviewKeywordExtractService
    svc = ReviewKeywordExtractService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/review-keyword-extract/status")
async def review_keyword_extract_status() -> Dict[str, Any]:
    """Health check for Review Keyword Extract."""
    return {"feature": "review_keyword_extract", "status": "operational"}
