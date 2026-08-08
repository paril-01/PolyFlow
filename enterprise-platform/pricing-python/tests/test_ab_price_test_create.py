"""Tests for Ab Price Test Create."""
import pytest
from app.services.ab_price_test_create import AbPriceTestCreateService


class TestAbPriceTestCreateService:
    """Test suite for AbPriceTestCreateService."""

    def setup_method(self):
        self.service = AbPriceTestCreateService()

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
        assert result["feature"] == "ab_price_test_create"
