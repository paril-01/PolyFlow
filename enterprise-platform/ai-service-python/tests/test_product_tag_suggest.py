"""Tests for Product Tag Suggest."""
import pytest
from app.services.product_tag_suggest import ProductTagSuggestService


class TestProductTagSuggestService:
    """Test suite for ProductTagSuggestService."""

    def setup_method(self):
        self.service = ProductTagSuggestService()

    def test_execute_success(self):
        result = self.service.execute({"test_key": "test_value"})
        assert result["status"] == "success"
        assert "trace_id" in result

    def test_execute_with_empty_request(self):
        result = self.service.execute({})
        assert result["status"] == "success"

    def test_process_returns_domain(self):
        result = self.service._process({"key": "value"})
        assert result["domain"] == "ai_features"
        assert result["feature"] == "product_tag_suggest"
