"""
LLM Provider Abstraction for AEF Orchestrator.
Supports OpenAI, Anthropic, Google Gemini, and Simulated/Dry-Run mode.
"""

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider fails inference in fail-closed mode."""
    pass


@dataclass
class LLMResponse:
    content: str
    provider: str
    endpoint: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_seconds: float = 0.0
    simulation_fallback: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "endpoint": self.endpoint,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_seconds": round(self.latency_seconds, 3),
            "simulation_fallback": self.simulation_fallback,
        }


class LLMProvider:
    def __init__(self, provider_name: str = "auto"):
        self.provider_name = provider_name.lower()
        self.last_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.total_tokens_consumed: int = 0
        self.last_response: Optional[LLMResponse] = None

        if self.provider_name == "auto":
            if os.environ.get("OPENAI_API_KEY"):
                self.provider_name = "openai"
            elif os.environ.get("ANTHROPIC_API_KEY"):
                self.provider_name = "anthropic"
            elif os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
                self.provider_name = "gemini"
            else:
                self.provider_name = "dry-run"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Execute generation and return text response (fail-closed)."""
        resp = self.generate_with_provenance(system_prompt, user_prompt)
        return resp.content

    def generate_with_provenance(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Execute generation with fail-closed integrity and provenance recording."""
        t0 = time.time()
        if self.provider_name == "dry-run":
            content = self._simulated_response(system_prompt, user_prompt)
            resp = LLMResponse(
                content=content,
                provider="dry-run",
                endpoint="local-simulation",
                model="simulated-aef-mock",
                prompt_tokens=len(user_prompt) // 4,
                completion_tokens=len(content) // 4,
                total_tokens=(len(user_prompt) + len(content)) // 4,
                latency_seconds=time.time() - t0,
                simulation_fallback=False,
            )
            self.last_response = resp
            return resp
        elif self.provider_name == "openai":
            return self._call_openai(system_prompt, user_prompt, t0)
        elif self.provider_name == "anthropic":
            return self._call_anthropic(system_prompt, user_prompt, t0)
        elif self.provider_name == "gemini":
            return self._call_gemini(system_prompt, user_prompt, t0)
        else:
            raise LLMProviderError(f"Unsupported LLM provider: '{self.provider_name}'")

    def _call_openai(self, system_prompt: str, user_prompt: str, start_time: float) -> LLMResponse:
        try:
            import openai
            base_url = os.environ.get("OPENAI_BASE_URL")
            client = openai.OpenAI(base_url=base_url, timeout=120.0) if base_url else openai.OpenAI(timeout=120.0)
            model_name = os.environ.get("AEF_MODEL")
            endpoint = str(getattr(client, "base_url", "https://api.openai.com/v1"))
            if not model_name:
                if "11434" in endpoint or os.environ.get("OPENAI_API_KEY") == "ollama":
                    model_name = "qwen2.5-coder:1.5b"
                else:
                    model_name = "gpt-4o"

            max_tokens = int(os.environ.get("AEF_MAX_TOKENS", "500"))
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=max_tokens,
            )

            p_tokens = 0
            c_tokens = 0
            t_tokens = 0
            if hasattr(response, "usage") and response.usage:
                p_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
                c_tokens = getattr(response.usage, "completion_tokens", 0) or 0
                t_tokens = getattr(response.usage, "total_tokens", 0) or 0

            self.last_usage = {
                "prompt_tokens": p_tokens,
                "completion_tokens": c_tokens,
                "total_tokens": t_tokens,
            }
            self.total_tokens_consumed += t_tokens
            latency = time.time() - start_time

            provider_type = "ollama" if ("11434" in endpoint or os.environ.get("OPENAI_API_KEY") == "ollama") else "openai"
            resp = LLMResponse(
                content=response.choices[0].message.content or "",
                provider=provider_type,
                endpoint=endpoint,
                model=model_name,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=t_tokens,
                latency_seconds=latency,
                simulation_fallback=False,
            )
            self.last_response = resp
            return resp
        except Exception as e:
            # FAIL-CLOSED: strictly raise exception, no silent fallback to simulation
            raise LLMProviderError(f"OpenAI/Ollama provider call failed: {e}") from e

    def _call_anthropic(self, system_prompt: str, user_prompt: str, start_time: float) -> LLMResponse:
        try:
            import anthropic
            client = anthropic.Anthropic()
            model_name = os.environ.get("AEF_MODEL", "claude-3-5-sonnet-20241022")
            response = client.messages.create(
                model=model_name,
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            p_tokens = getattr(response.usage, "input_tokens", 0) or 0
            c_tokens = getattr(response.usage, "output_tokens", 0) or 0
            t_tokens = p_tokens + c_tokens
            self.total_tokens_consumed += t_tokens

            resp = LLMResponse(
                content=response.content[0].text,
                provider="anthropic",
                endpoint="https://api.anthropic.com",
                model=model_name,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=t_tokens,
                latency_seconds=time.time() - start_time,
                simulation_fallback=False,
            )
            self.last_response = resp
            return resp
        except Exception as e:
            raise LLMProviderError(f"Anthropic provider call failed: {e}") from e

    def _call_gemini(self, system_prompt: str, user_prompt: str, start_time: float) -> LLMResponse:
        try:
            import google.generativeai as genai
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            genai.configure(api_key=api_key)
            model_name = os.environ.get("AEF_MODEL", "gemini-1.5-pro")
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
            response = model.generate_content(user_prompt)
            content = response.text or ""
            p_tokens = len(system_prompt + user_prompt) // 4
            c_tokens = len(content) // 4
            t_tokens = p_tokens + c_tokens
            self.total_tokens_consumed += t_tokens

            resp = LLMResponse(
                content=content,
                provider="gemini",
                endpoint="google-generative-ai",
                model=model_name,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=t_tokens,
                latency_seconds=time.time() - start_time,
                simulation_fallback=False,
            )
            self.last_response = resp
            return resp
        except Exception as e:
            raise LLMProviderError(f"Gemini provider call failed: {e}") from e

    def _simulated_response(self, system_prompt: str, user_prompt: str) -> str:
        """Dry-run simulation for verifying pipeline mechanics without external API keys."""
        if "Maker Agent" in system_prompt or "Maker" in system_prompt:
            return (
                "## Stage 1 Output: Maker Agent (Discovery & Design)\n\n"
                "### Functional Requirements\n"
                "- FR-01: Core feature workflow implementation\n"
                "- FR-02: Input validation and security checks\n\n"
                "### Architecture Decision Record (ADR-001)\n"
                "**Status**: Accepted\n"
                "**Decision**: Clean Architecture with layered separation of concerns.\n"
            )
        elif "Reviewer Agent" in system_prompt or "Reviewer" in system_prompt:
            return (
                "## Stage Output: Reviewer Agent (Adversarial Review)\n\n"
                "### Review Findings\n"
                "- P3: Add structured logging correlation IDs.\n\n"
                "**Verdict**: APPROVE\n"
            )
        elif "Implementer Agent" in system_prompt or "Implementer" in system_prompt:
            return (
                "## Stage 3 Output: Implementer Agent (Production Code)\n\n"
                "```python\n"
                "# main.py - Production Implementation\n"
                "def main():\n"
                "    print('Feature implemented adhering to SOLID/DRY principles')\n"
                "```\n\n"
                "### Tests\n"
                "Unit tests passed 100%.\n"
            )
        elif "Gatekeeper Agent" in system_prompt or "Gatekeeper" in system_prompt:
            return (
                "## Stage 5 Output: Gatekeeper Agent (Release Authority)\n\n"
                "### Release Decision\n"
                "**Decision**: APPROVE ✅\n"
                "All release criteria and production readiness checks passed.\n"
            )
        elif "Historian Agent" in system_prompt or "Historian" in system_prompt:
            return (
                "## Stage 6 Output: Historian Agent (Engineering Memory)\n\n"
                "### Memory Entry\n"
                "- Recorded ADR-001 into decision log.\n"
                "- Updated repository knowledge graph.\n"
            )
        return "Simulated AEF Agent Output."
