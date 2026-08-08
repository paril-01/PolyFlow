"""Demand Forecast Daily — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/demand-forecast-daily")
async def demand_forecast_daily_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Demand Forecast Daily."""
    from app.services.demand_forecast_daily import DemandForecastDailyService
    svc = DemandForecastDailyService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/demand-forecast-daily/status")
async def demand_forecast_daily_status() -> Dict[str, Any]:
    """Health check for Demand Forecast Daily."""
    return {"feature": "demand_forecast_daily", "status": "operational"}
