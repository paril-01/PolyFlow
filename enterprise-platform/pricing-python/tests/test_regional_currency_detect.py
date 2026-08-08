"""Tests for Regional Currency Detect."""
import pytest
from app.services.regional_currency_detect import RegionalCurrencyDetectService


class TestRegionalCurrencyDetectService:
    """Test suite for RegionalCurrencyDetectService."""

    def setup_method(self):
        self.service = RegionalCurrencyDetectService()

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
        assert result["feature"] == "regional_currency_detect"
