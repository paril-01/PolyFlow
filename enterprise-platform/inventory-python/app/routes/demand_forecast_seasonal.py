"""Demand Forecast Seasonal — API Route."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/demand-forecast-seasonal")
async def demand_forecast_seasonal_endpoint(request: Dict[str, Any] = {}) -> Dict[str, Any]:
    """API endpoint for Demand Forecast Seasonal."""
    from app.services.demand_forecast_seasonal import DemandForecastSeasonalService
    svc = DemandForecastSeasonalService()
    result = svc.execute(request)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/demand-forecast-seasonal/status")
async def demand_forecast_seasonal_status() -> Dict[str, Any]:
    """Health check for Demand Forecast Seasonal."""
    return {"feature": "demand_forecast_seasonal", "status": "operational"}
