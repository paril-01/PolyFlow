"""Text Language Detect — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/text-language-detect")
async def text_language_detect_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Text Language Detect."""
    from app.services.text_language_detect import TextLanguageDetectService
    svc = TextLanguageDetectService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/text-language-detect/status")
async def text_language_detect_status() -> Dict[str, Any]:
    """Health check for Text Language Detect."""
    return {"feature": "text_language_detect", "status": "operational"}
