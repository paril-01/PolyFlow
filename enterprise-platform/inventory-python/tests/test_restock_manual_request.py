"""Tests for Restock Manual Request."""
import pytest
from app.services.restock_manual_request import RestockManualRequestService


class TestRestockManualRequestService:
    """Test suite for RestockManualRequestService."""

    def setup_method(self):
        self.service = RestockManualRequestService()

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
        assert result["feature"] == "restock_manual_request"
