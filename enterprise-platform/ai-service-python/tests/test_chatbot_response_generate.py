"""Tests for Chatbot Response Generate."""
import pytest
from app.services.chatbot_response_generate import ChatbotResponseGenerateService


class TestChatbotResponseGenerateService:
    """Test suite for ChatbotResponseGenerateService."""

    def setup_method(self):
        self.service = ChatbotResponseGenerateService()

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
        assert result["feature"] == "chatbot_response_generate"
