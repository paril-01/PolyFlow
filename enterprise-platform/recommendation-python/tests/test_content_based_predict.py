"""Tests for Content Based Predict."""
import pytest
from app.services.content_based_predict import ContentBasedPredictService


class TestContentBasedPredictService:
    """Test suite for ContentBasedPredictService."""

    def setup_method(self):
        self.service = ContentBasedPredictService()

    def test_execute_success(self):
        result = self.service.execute({"test_key": "test_value"})
        assert result["status"] == "success"
        assert "trace_id" in result

    def test_execute_with_empty_request(self):
        result = self.service.execute({})
        assert result["status"] == "success"

    def test_process_returns_domain(self):
        result = self.service._process({"key": "value"})
        assert result["domain"] == "recommendations"
        assert result["feature"] == "content_based_predict"
