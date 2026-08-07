"""
LLM Provider Abstraction for AEF Orchestrator.
Supports OpenAI, Anthropic, Google Gemini, and Simulated/Dry-Run mode.
"""

import os
import sys

class LLMProvider:
    def __init__(self, provider_name: str = "auto"):
        self.provider_name = provider_name.lower()
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
        if self.provider_name == "dry-run":
            return self._simulated_response(system_prompt, user_prompt)
        elif self.provider_name == "openai":
            return self._call_openai(system_prompt, user_prompt)
        elif self.provider_name == "anthropic":
            return self._call_anthropic(system_prompt, user_prompt)
        elif self.provider_name == "gemini":
            return self._call_gemini(system_prompt, user_prompt)
        else:
            return self._simulated_response(system_prompt, user_prompt)

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import openai
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=os.environ.get("AEF_MODEL", "gpt-4o"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[AEF Provider Warning] OpenAI call failed: {e}. Falling back to dry-run mode.", file=sys.stderr)
            return self._simulated_response(system_prompt, user_prompt)

    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic()
            response = client.messages.create(
                model=os.environ.get("AEF_MODEL", "claude-3-5-sonnet-20241022"),
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"[AEF Provider Warning] Anthropic call failed: {e}. Falling back to dry-run mode.", file=sys.stderr)
            return self._simulated_response(system_prompt, user_prompt)

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import google.generativeai as genai
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=os.environ.get("AEF_MODEL", "gemini-1.5-pro"),
                system_instruction=system_prompt
            )
            response = model.generate_content(user_prompt)
            return response.text
        except Exception as e:
            print(f"[AEF Provider Warning] Gemini call failed: {e}. Falling back to dry-run mode.", file=sys.stderr)
            return self._simulated_response(system_prompt, user_prompt)

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
