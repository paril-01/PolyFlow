"""Text Translate — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/text-translate")
async def text_translate_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Text Translate."""
    from app.services.text_translate import TextTranslateService
    svc = TextTranslateService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/text-translate/status")
async def text_translate_status() -> Dict[str, Any]:
    """Health check for Text Translate."""
    return {"feature": "text_translate", "status": "operational"}
