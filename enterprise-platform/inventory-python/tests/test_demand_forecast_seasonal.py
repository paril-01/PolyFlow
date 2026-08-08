"""Tests for Demand Forecast Seasonal."""
import pytest
from app.services.demand_forecast_seasonal import DemandForecastSeasonalService


class TestDemandForecastSeasonalService:
    """Test suite for DemandForecastSeasonalService."""

    def setup_method(self):
        self.service = DemandForecastSeasonalService()

    def test_execute_success(self):
        result = self.service.execute({"test_key": "test_value"})
        assert result["status"] == "success"
        assert "trace_id" in result

    def test_execute_with_empty_request(self):
        result = self.service.execute({})
        assert result["status"] == "success"

    def test_process_returns_domain(self):
        result = self.service._process({"key": "value"})
        assert result["domain"] == "inventory"
        assert result["feature"] == "demand_forecast_seasonal"
