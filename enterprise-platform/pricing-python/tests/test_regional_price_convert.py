"""Tests for Regional Price Convert."""
import pytest
from app.services.regional_price_convert import RegionalPriceConvertService


class TestRegionalPriceConvertService:
    """Test suite for RegionalPriceConvertService."""

    def setup_method(self):
        self.service = RegionalPriceConvertService()

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
        assert result["feature"] == "regional_price_convert"
