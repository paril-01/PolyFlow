"""
tests/conftest.py — Pytest Configuration and Global Python Path Setup.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Add repository root and RCIR package paths to sys.path
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

rcir_src = REPO_ROOT / "rcir" / "src"
if str(rcir_src) not in sys.path:
    sys.path.insert(0, str(rcir_src))

sdk_src = REPO_ROOT / "polyflow-sdk"
if str(sdk_src) not in sys.path:
    sys.path.insert(0, str(sdk_src))
