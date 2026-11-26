"""
RCIR — Dependency-Graph Context Runtime.

Lightweight middleware that sits between a repository and an LLM/IDE,
answers context questions with a token-budgeted, structurally-derived
slice of the codebase, and keeps that slice cheap to maintain as the
code changes.

The optional source service requires an exact tokenizer. MCP transport is an
optional SDK extra; neither requires an external model or Agent Pool.
"""

__version__ = "0.2.0.dev0"
