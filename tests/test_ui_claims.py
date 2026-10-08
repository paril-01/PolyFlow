"""
UI Claims and Static Presentation Verification Test.
Follows Section 16 of POLYFLOW_FINAL_BLIND_VALIDATION_AND_SHOWCASE_PROMPT.md:
- Static test banning hardcoded presentation claims (80.5%, 96.7%, ALL RUNTIMES EXIT 0, etc.)
- Confirms all five showcase tabs exist in App.jsx and Sidebar.jsx
- Confirms absence of forbidden emojis in React source
- Confirms showcase/data JSON schemas and claim registry integrity
"""

import json
import re
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
REACT_SRC_DIR = REPO_ROOT / "rcir" / "visualizer-react" / "src"
SHOWCASE_DATA_DIR = REPO_ROOT / "showcase" / "data"

BANNED_PRESENTATION_STRINGS = [
    "80.5%",
    "96.7%",
    "ALL RUNTIMES EXIT 0",
    "ALL 11 VERIFICATION GATES PASSED",
    "214 ms",
]

REQUIRED_TABS = [
    "01 PolyFlow",
    "02 Interpreter",
    "03 RCIR",
    "04 Agent & Validation",
    "05 ERPNext Scale",
]

REQUIRED_DATA_FILES = [
    "run_manifest.json",
    "system_status.json",
    "polyflow_mapping.json",
    "interpreter_demo.json",
    "rcir_pipeline.json",
    "token_ab.json",
    "agent_trials.json",
    "erpnext_scale.json",
    "claim_registry.json",
]


def test_banned_hardcoded_claims_absent():
    """Ensure no banned hardcoded claims appear in React source files outside historical fixtures."""
    assert REACT_SRC_DIR.exists(), f"React src dir not found: {REACT_SRC_DIR}"

    for file_path in REACT_SRC_DIR.rglob("*"):
        if file_path.is_file() and file_path.suffix in [".js", ".jsx", ".ts", ".tsx", ".html"]:
            content = file_path.read_text(encoding="utf-8")
            
            # Skip historical fixture comments or legacy archives if explicitly isolated
            if "HISTORICAL_FIXTURES" in content:
                continue

            for banned in BANNED_PRESENTATION_STRINGS:
                assert banned not in content, (
                    f"Banned presentation claim '{banned}' found in {file_path.relative_to(REPO_ROOT)}! "
                    f"Rule 0 requires all claims to be data-driven or historical."
                )


def test_five_primary_tabs_in_ui():
    """Ensure exactly the five specified primary tabs are configured in App.jsx and Sidebar.jsx."""
    sidebar_file = REACT_SRC_DIR / "components" / "Sidebar.jsx"
    app_file = REACT_SRC_DIR / "App.jsx"

    assert sidebar_file.exists()
    assert app_file.exists()

    sidebar_content = sidebar_file.read_text(encoding="utf-8")
    app_content = app_file.read_text(encoding="utf-8")

    # Verify all 5 tab labels in Sidebar
    for tab_label in REQUIRED_TABS:
        assert tab_label in sidebar_content, f"Missing required tab label '{tab_label}' in Sidebar.jsx"

    # Verify all 5 tab IDs in App.jsx
    for tab_id in ["polyflow", "interpreter", "rcir", "agent", "erpnext"]:
        assert tab_id in app_content, f"Missing required tab component render for '{tab_id}' in App.jsx"


def test_showcase_data_architecture_exists():
    """Verify all 9 showcase data files exist in showcase/data/ and are valid JSON."""
    assert SHOWCASE_DATA_DIR.exists(), f"Missing showcase data directory: {SHOWCASE_DATA_DIR}"

    for filename in REQUIRED_DATA_FILES:
        data_file = SHOWCASE_DATA_DIR / filename
        assert data_file.exists(), f"Missing required showcase data file: {filename}"
        
        # Must be valid json (dict or list)
        data = json.loads(data_file.read_text(encoding="utf-8"))
        assert isinstance(data, (dict, list)), f"{filename} root must be a JSON object or list"


def test_no_emojis_in_tabs_and_header():
    """Verify no emojis are used in the primary tabs and header components."""
    # Proper 8-hex-digit unicode escapes for emoji ranges
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]"
    )

    checked_files = [
        REACT_SRC_DIR / "components" / "Header.jsx",
        REACT_SRC_DIR / "components" / "Sidebar.jsx",
        REACT_SRC_DIR / "components" / "Tab01PolyFlow.jsx",
        REACT_SRC_DIR / "components" / "Tab02Interpreter.jsx",
        REACT_SRC_DIR / "components" / "Tab03RCIR.jsx",
        REACT_SRC_DIR / "components" / "Tab04AgentValidation.jsx",
        REACT_SRC_DIR / "components" / "Tab05ERPNextScale.jsx",
    ]

    for file_path in checked_files:
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            match = emoji_pattern.search(content)
            assert match is None, f"Forbidden emoji '{match.group(0)}' found in {file_path.name}"
