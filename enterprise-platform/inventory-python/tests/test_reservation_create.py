"""Tests for Reservation Create."""
import pytest
from app.services.reservation_create import ReservationCreateService


class TestReservationCreateService:
    """Test suite for ReservationCreateService."""

    def setup_method(self):
        self.service = ReservationCreateService()

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
        assert result["feature"] == "reservation_create"
