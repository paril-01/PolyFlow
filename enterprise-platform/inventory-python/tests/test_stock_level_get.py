"""Tests for Stock Level Get."""
import pytest
from app.services.stock_level_get import StockLevelGetService


class TestStockLevelGetService:
    """Test suite for StockLevelGetService."""

    def setup_method(self):
        self.service = StockLevelGetService()

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
        assert result["feature"] == "stock_level_get"
