"""Tests for Coupon Expire."""
import pytest
from app.services.coupon_expire import CouponExpireService


class TestCouponExpireService:
    """Test suite for CouponExpireService."""

    def setup_method(self):
        self.service = CouponExpireService()

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
        assert result["feature"] == "coupon_expire"
