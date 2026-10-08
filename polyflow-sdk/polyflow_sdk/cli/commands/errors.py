"""
'polyflow errors' Command.

Displays structured project-local diagnostic error logs and fix suggestions.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


def execute_errors(target: Optional[str] = None) -> int:
    base = Path(target).resolve() if target else Path.cwd()

    # Search for polyflow_errors.log in base or parent directories
    log_candidates = [
        base / "polyflow_errors.log",
        base.parent / "polyflow_errors.log",
        Path(__file__).resolve().parents[4] / "polyflow_errors.log",
    ]

    log_path = None
    for cand in log_candidates:
        if cand.is_file():
            log_path = cand
            break

    print("=" * 80)
    print("PolyFlow Structured Error Diagnostics & Fix Assistant")
    print("=" * 80)

    if not log_path or log_path.stat().st_size == 0:
        print("\nNo runtime execution errors currently logged in 'polyflow_errors.log'.")
        print("Your PolyFlow environment is running cleanly!\n")
        return 0

    print(f"Log Location: {log_path}\n")
    content = log_path.read_text(encoding="utf-8")
    entries = [e.strip() for e in content.split("========================================================================") if e.strip()]

    print(f"Found {len(entries)} recorded execution issue(s):\n")
    for i, entry in enumerate(entries[-5:], 1):
        print(f"--- [Report #{i}] ---")
        print(entry)
        print("")

    if len(entries) > 5:
        print(f"... and {len(entries) - 5} earlier entries in log.")

    return 0
