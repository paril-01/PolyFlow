"""Review Sentiment Analyze — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/review-sentiment-analyze")
async def review_sentiment_analyze_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Review Sentiment Analyze."""
    from app.services.review_sentiment_analyze import ReviewSentimentAnalyzeService
    svc = ReviewSentimentAnalyzeService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/review-sentiment-analyze/status")
async def review_sentiment_analyze_status() -> Dict[str, Any]:
    """Health check for Review Sentiment Analyze."""
    return {"feature": "review_sentiment_analyze", "status": "operational"}
