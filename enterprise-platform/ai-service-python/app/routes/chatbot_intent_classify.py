"""Chatbot Intent Classify — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/chatbot-intent-classify")
async def chatbot_intent_classify_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Chatbot Intent Classify."""
    from app.services.chatbot_intent_classify import ChatbotIntentClassifyService
    svc = ChatbotIntentClassifyService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/chatbot-intent-classify/status")
async def chatbot_intent_classify_status() -> Dict[str, Any]:
    """Health check for Chatbot Intent Classify."""
    return {"feature": "chatbot_intent_classify", "status": "operational"}
