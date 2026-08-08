"""Tests for Volume Discount Compute."""
import pytest
from app.services.volume_discount_compute import VolumeDiscountComputeService


class TestVolumeDiscountComputeService:
    """Test suite for VolumeDiscountComputeService."""

    def setup_method(self):
        self.service = VolumeDiscountComputeService()

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
        assert result["feature"] == "volume_discount_compute"
