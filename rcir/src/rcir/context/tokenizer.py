"""
RCIR v8.2 — Token Counting Subsystem (PHASE 31).

Provides exact and calibrated token estimation implementations:
- ExactTokenizerCounter (using tiktoken when available)
- ApproximateCharTokenCounter (calibrated 3.7 chars/token for code/whitespace)
- Records tokenizer provenance in benchmark artifacts
"""

from __future__ import annotations

import math
from typing import Any, Optional


class TokenCounter:
    """Abstract interface for counting tokens in prompt text."""

    def count(self, text: str) -> int:
        raise NotImplementedError

    def get_provenance(self) -> dict[str, Any]:
        raise NotImplementedError


class ApproximateCharTokenCounter(TokenCounter):
    """Calibrated character-ratio token counter."""

    def __init__(self, chars_per_token: float = 3.7):
        self.chars_per_token = chars_per_token

    def count(self, text: str) -> int:
        if not text:
            return 0
        return max(1, math.ceil(len(text) / self.chars_per_token))

    def get_provenance(self) -> dict[str, Any]:
        return {
            "tokenizer": "ApproximateCharTokenCounter",
            "model": "heuristic-qwen-calibrated",
            "token_count_type": "estimated",
            "chars_per_token": self.chars_per_token,
        }


class TiktokenTokenCounter(TokenCounter):
    """Exact BPE token counter using tiktoken (cl100k_base or o200k_base)."""

    def __init__(self, encoding_name: str = "cl100k_base"):
        self.encoding_name = encoding_name
        self._encoder = None
        try:
            import tiktoken
            self._encoder = tiktoken.get_encoding(encoding_name)
        except Exception:
            self._encoder = None

    def count(self, text: str) -> int:
        if not text:
            return 0
        if self._encoder:
            return len(self._encoder.encode(text, disallowed_special=()))
        # Fallback to calibrated char counter
        return max(1, math.ceil(len(text) / 3.7))

    def get_provenance(self) -> dict[str, Any]:
        return {
            "tokenizer": f"tiktoken:{self.encoding_name}" if self._encoder else "tiktoken-fallback",
            "model": "bpe-tokenizer",
            "token_count_type": "exact" if self._encoder else "estimated",
        }


def get_default_token_counter() -> TokenCounter:
    """Return TiktokenTokenCounter if tiktoken is available, else ApproximateCharTokenCounter."""
    try:
        import tiktoken
        return TiktokenTokenCounter("cl100k_base")
    except ImportError:
        return ApproximateCharTokenCounter(chars_per_token=3.7)
