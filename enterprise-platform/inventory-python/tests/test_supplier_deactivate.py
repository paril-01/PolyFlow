"""Tests for Supplier Deactivate."""
import pytest
from app.services.supplier_deactivate import SupplierDeactivateService


class TestSupplierDeactivateService:
    """Test suite for SupplierDeactivateService."""

    def setup_method(self):
        self.service = SupplierDeactivateService()

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
        assert result["feature"] == "supplier_deactivate"
