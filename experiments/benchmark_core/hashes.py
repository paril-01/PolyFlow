"""
experiments/benchmark_core/hashes.py — Cryptographic Hash Verification Utilities.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Computes SHA-256 hex digest of file on disk."""
    if not path.exists() or not path.is_file():
        return ""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def sha256_text(text: str) -> str:
    """Computes SHA-256 hex digest of string content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_file_hash(path: Path, expected_hash: str) -> bool:
    """Verifies that file matches expected SHA-256 hash."""
    actual = sha256_file(path)
    return bool(actual and actual.lower() == expected_hash.lower())
