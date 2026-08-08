"""Tests for Cross Sell Compute."""
import pytest
from app.services.cross_sell_compute import CrossSellComputeService


class TestCrossSellComputeService:
    """Test suite for CrossSellComputeService."""

    def setup_method(self):
        self.service = CrossSellComputeService()

    def test_execute_success(self):
        result = self.service.execute({"test_key": "test_value"})
        assert result["status"] == "success"
        assert "trace_id" in result

    def test_execute_with_empty_request(self):
        result = self.service.execute({})
        assert result["status"] == "success"

    def test_process_returns_domain(self):
        result = self.service._process({"key": "value"})
        assert result["domain"] == "recommendations"
        assert result["feature"] == "cross_sell_compute"
