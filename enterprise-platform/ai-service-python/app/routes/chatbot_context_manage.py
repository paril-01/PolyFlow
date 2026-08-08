"""Chatbot Context Manage — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/chatbot-context-manage")
async def chatbot_context_manage_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Chatbot Context Manage."""
    from app.services.chatbot_context_manage import ChatbotContextManageService
    svc = ChatbotContextManageService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/chatbot-context-manage/status")
async def chatbot_context_manage_status() -> Dict[str, Any]:
    """Health check for Chatbot Context Manage."""
    return {"feature": "chatbot_context_manage", "status": "operational"}
