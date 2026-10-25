"""
Unit tests for LLMProvider and model parameter contract (PF-P0-002).
Verifies:
1. Provider accepts explicit model_name parameter.
2. Provider propagates model_name correctly across all supported backends.
3. Provider enforces model identity and detects silent mismatches.
4. Backwards compatibility when model_name is omitted.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from orchestrator.providers import LLMProvider, LLMResponse, LLMProviderError


class TestLLMProviderContract(unittest.TestCase):
    def test_init_with_model_name(self):
        """Verify LLMProvider accepts model_name argument without TypeError."""
        p = LLMProvider(provider_name="dry-run", model_name="qwen2.5-coder:1.5b")
        self.assertEqual(p.provider_name, "dry-run")
        self.assertEqual(p.model_name, "qwen2.5-coder:1.5b")

    def test_init_default_model_name(self):
        """Verify backwards compatibility: model_name defaults to None."""
        p = LLMProvider(provider_name="dry-run")
        self.assertIsNone(p.model_name)

    def test_dry_run_reflects_model_name(self):
        """Dry-run provider should reflect requested model_name in LLMResponse."""
        p = LLMProvider(provider_name="dry-run", model_name="custom-dry-model")
        resp = p.generate_with_provenance("system prompt", "user prompt")
        self.assertIsInstance(resp, LLMResponse)
        self.assertEqual(resp.model, "custom-dry-model")
        self.assertEqual(resp.provider, "dry-run")

    def test_dry_run_default_model(self):
        """Dry-run provider without model_name uses simulated default."""
        p = LLMProvider(provider_name="dry-run")
        resp = p.generate_with_provenance("system prompt", "user prompt")
        self.assertEqual(resp.model, "simulated-aef-mock")

    def test_model_identity_mismatch_raises_error(self):
        """Fail-closed: if provider returns a different model than requested, raise LLMProviderError."""
        p = LLMProvider(provider_name="dry-run", model_name="expected-model")
        with patch.object(p, "_simulated_response", return_value="simulated"):
            # Mock return of unexpected model
            with patch.object(
                p,
                "generate_with_provenance",
                side_effect=LLMProviderError("Model identity mismatch: requested 'expected-model', got 'wrong-model'")
            ):
                with self.assertRaises(LLMProviderError) as ctx:
                    p.generate_with_provenance("sys", "user")
                self.assertIn("Model identity mismatch", str(ctx.exception))

    @patch.dict(os.environ, {"AEF_MODEL": "env-model"})
    def test_explicit_model_precedes_env_openai(self):
        """Explicit model_name takes precedence over AEF_MODEL environment variable."""
        p = LLMProvider(provider_name="openai", model_name="cli-specified-model")
        self.assertEqual(p.model_name, "cli-specified-model")

    def test_unsupported_provider_raises_error(self):
        """Unsupported provider name must fail-closed immediately with LLMProviderError."""
        with self.assertRaises(LLMProviderError):
            LLMProvider(provider_name="unknown-provider")

    def test_model_identity_mismatch_direct(self):
        """generate_with_provenance raises LLMProviderError if returned model doesn't match requested model."""
        p = LLMProvider(provider_name="dry-run", model_name="requested-model-A")
        # Intentionally tamper with simulated response to emit a mismatching model
        def mock_call(*args, **kwargs):
            return LLMResponse(
                content="test",
                provider="dry-run",
                endpoint="local",
                model="different-model-B",
            )
        p._call_openai = mock_call
        p.provider_name = "openai"
        with self.assertRaises(LLMProviderError) as ctx:
            p.generate_with_provenance("sys", "user")
        self.assertIn("Model identity mismatch", str(ctx.exception))


    @patch.dict(os.environ, {"OLLAMA_MODEL": "env-ollama-model"})
    def test_ollama_explicit_model_precedes_env(self):
        """Explicit model_name takes precedence over OLLAMA_MODEL environment variable in request payload."""
        import json
        import io
        p = LLMProvider(provider_name="ollama", model_name="cli-ollama-model")
        captured_payload = {}

        def mock_urlopen(req, timeout=120):
            nonlocal captured_payload
            captured_payload = json.loads(req.data.decode("utf-8"))
            mock_resp = io.BytesIO(json.dumps({
                "response": "ok",
                "model": "cli-ollama-model",
                "prompt_eval_count": 10,
                "eval_count": 5,
            }).encode("utf-8"))
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=mock_urlopen):
            resp = p._call_ollama("sys", "user", 0.0)
            self.assertEqual(captured_payload.get("model"), "cli-ollama-model")
            self.assertEqual(resp.model, "cli-ollama-model")

    def test_ollama_response_model_mismatch_aborts(self):
        """If Ollama server returns a model different than requested, fail-closed with LLMProviderError."""
        import json
        import io
        p = LLMProvider(provider_name="ollama", model_name="requested-qwen")

        def mock_urlopen(req, timeout=120):
            mock_resp = io.BytesIO(json.dumps({
                "response": "ok",
                "model": "different-llama",
            }).encode("utf-8"))
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=mock_urlopen):
            with self.assertRaises(LLMProviderError) as ctx:
                p._call_ollama("sys", "user", 0.0)
            self.assertIn("Ollama model identity mismatch", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()


