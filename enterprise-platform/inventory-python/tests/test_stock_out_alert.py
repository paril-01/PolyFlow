"""Tests for Stock Out Alert."""
import pytest
from app.services.stock_out_alert import StockOutAlertService


class TestStockOutAlertService:
    """Test suite for StockOutAlertService."""

    def setup_method(self):
        self.service = StockOutAlertService()

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
        assert result["feature"] == "stock_out_alert"
