"""Tests for Tax Calculate."""
import pytest
from app.services.tax_calculate import TaxCalculateService


class TestTaxCalculateService:
    """Test suite for TaxCalculateService."""

    def setup_method(self):
        self.service = TaxCalculateService()

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
        assert result["feature"] == "tax_calculate"
