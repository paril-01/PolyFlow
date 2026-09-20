"""
RCIR — Dependency-Graph Context Runtime.

Lightweight middleware that sits between a repository and an LLM/IDE,
answers context questions with a token-budgeted, structurally-derived
slice of the codebase, and keeps that slice cheap to maintain as the
code changes.

Zero external dependencies — uses only Python stdlib.
"""

__version__ = "0.1.0"
