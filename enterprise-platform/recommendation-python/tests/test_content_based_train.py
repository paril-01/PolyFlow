"""Tests for Content Based Train."""
import pytest
from app.services.content_based_train import ContentBasedTrainService


class TestContentBasedTrainService:
    """Test suite for ContentBasedTrainService."""

    def setup_method(self):
        self.service = ContentBasedTrainService()

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
        assert result["feature"] == "content_based_train"
