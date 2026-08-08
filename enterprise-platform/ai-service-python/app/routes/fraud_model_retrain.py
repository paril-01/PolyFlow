"""Fraud Model Retrain — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/fraud-model-retrain")
async def fraud_model_retrain_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Fraud Model Retrain."""
    from app.services.fraud_model_retrain import FraudModelRetrainService
    svc = FraudModelRetrainService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/fraud-model-retrain/status")
async def fraud_model_retrain_status() -> Dict[str, Any]:
    """Health check for Fraud Model Retrain."""
    return {"feature": "fraud_model_retrain", "status": "operational"}
