"""Price Predict — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/price-predict")
async def price_predict_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Price Predict."""
    from app.services.price_predict import PricePredictService
    svc = PricePredictService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/price-predict/status")
async def price_predict_status() -> Dict[str, Any]:
    """Health check for Price Predict."""
    return {"feature": "price_predict", "status": "operational"}
