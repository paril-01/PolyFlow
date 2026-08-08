"""Fraud Detect Transaction — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/ai_features", tags=["ai_features"])


@router.post("/fraud-detect-transaction")
async def fraud_detect_transaction_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Fraud Detect Transaction."""
    from app.services.fraud_detect_transaction import FraudDetectTransactionService
    svc = FraudDetectTransactionService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/fraud-detect-transaction/status")
async def fraud_detect_transaction_status() -> Dict[str, Any]:
    """Health check for Fraud Detect Transaction."""
    return {"feature": "fraud_detect_transaction", "status": "operational"}
