"""Tests for Price Surge Detect."""
import pytest
from app.services.price_surge_detect import PriceSurgeDetectService


class TestPriceSurgeDetectService:
    """Test suite for PriceSurgeDetectService."""

    def setup_method(self):
        self.service = PriceSurgeDetectService()

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
        assert result["feature"] == "price_surge_detect"
