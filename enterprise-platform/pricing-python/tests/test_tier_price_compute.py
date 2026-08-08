"""Tests for Tier Price Compute."""
import pytest
from app.services.tier_price_compute import TierPriceComputeService


class TestTierPriceComputeService:
    """Test suite for TierPriceComputeService."""

    def setup_method(self):
        self.service = TierPriceComputeService()

    def test_execute_success(self):
        result = self.service.execute({"test_key": "test_value"})
        assert result["status"] == "success"
        assert "trace_id" in result

    def test_execute_with_empty_request(self):
        result = self.service.execute({})
        assert result["status"] == "success"

    def test_process_returns_domain(self):
        result = self.service._process({"key": "value"})
        assert result["domain"] == "pricing"
        assert result["feature"] == "tier_price_compute"
