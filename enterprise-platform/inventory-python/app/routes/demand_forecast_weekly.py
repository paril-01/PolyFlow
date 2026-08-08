"""Demand Forecast Weekly — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/demand-forecast-weekly")
async def demand_forecast_weekly_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Demand Forecast Weekly."""
    from app.services.demand_forecast_weekly import DemandForecastWeeklyService
    svc = DemandForecastWeeklyService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/demand-forecast-weekly/status")
async def demand_forecast_weekly_status() -> Dict[str, Any]:
    """Health check for Demand Forecast Weekly."""
    return {"feature": "demand_forecast_weekly", "status": "operational"}
