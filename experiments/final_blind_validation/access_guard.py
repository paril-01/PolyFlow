"""
Blind Validation Access Guard (Section 0.2).

Enforces an explicit deny-list during blind benchmark design and execution.
Prevents evaluation scripts from reading prior conclusions, hardcoded summaries,
or manufactured benchmark constants.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List


DENIED_PATTERNS = [
    "FINAL_SYSTEM_ASSESSMENT.md",
    "showcase",
    "benchmarkData.js",
    "rcir_runs",
]


class BlindAccessGuard:
    @staticmethod
    def validate_path(path: str | Path) -> bool:
        p_str = str(path).replace("\\", "/")
        for denied in DENIED_PATTERNS:
            if denied in p_str:
                raise PermissionError(
                    f"BLIND ACCESS VIOLATION: Access to '{p_str}' is denied under Rule 0.2."
                )
        return True

    @staticmethod
    def sanitize_environment() -> None:
        """Strip environment variables that could leak prior benchmark results."""
        for k in list(os.environ.keys()):
            if "PREV_BENCHMARK" in k or "SAVED_METRIC" in k:
                del os.environ[k]
