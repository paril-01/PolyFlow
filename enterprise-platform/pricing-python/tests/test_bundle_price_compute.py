"""Tests for Bundle Price Compute."""
import pytest
from app.services.bundle_price_compute import BundlePriceComputeService


class TestBundlePriceComputeService:
    """Test suite for BundlePriceComputeService."""

    def setup_method(self):
        self.service = BundlePriceComputeService()

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
        assert result["feature"] == "bundle_price_compute"
