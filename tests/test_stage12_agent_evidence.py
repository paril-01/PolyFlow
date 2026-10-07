"""
Stage 12 Regression Tests: Coding Agent Hardening & Evidence Verification (Issues 13-23).
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5"))

from agent_tasks.verify_task1 import test_api_controller as verify_task1_impl
from agent_tasks.verify_regression import run_regression_check, check_php_syntax


def test_verify_task1_rejects_decoy_comments_and_strings():
    """Issue 15 & 23: Acceptance verifier must resist decoy comments and strings."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = Path(tmp_dir)
        api_dir = repo_dir / "apps" / "files" / "lib" / "Controller"
        api_dir.mkdir(parents=True, exist_ok=True)
        target_file = api_dir / "ApiController.php"

        # Case 1: Decoy comment with valid call, but actual code does NOT call getPreview with 4 args
        decoy_comment_code = """<?php
class ApiController {
    public function getThumbnail($x, $y, $file, $crop = true) {
        // $this->previewManager->getPreview($file, $x, $y, $crop);
        return $this->previewManager->getPreview($file, $x, $y);
    }
}
"""
        target_file.write_text(decoy_comment_code, encoding="utf-8")
        assert verify_task1_impl(repo_dir) == 1, "Must reject decoy in comment"

        # Case 2: Decoy string literal containing valid call
        decoy_string_code = """<?php
class ApiController {
    public function getThumbnail($x, $y, $file, $crop = true) {
        $dummy = "$this->previewManager->getPreview($file, $x, $y, $crop);";
        return $this->previewManager->getPreview($file, $x, $y);
    }
}
"""
        target_file.write_text(decoy_string_code, encoding="utf-8")
        assert verify_task1_impl(repo_dir) == 1, "Must reject decoy in string literal"

        # Case 3: Reordered arguments (wrong order: $crop in wrong position)
        wrong_order_code = """<?php
class ApiController {
    public function getThumbnail($x, $y, $file, $crop = true) {
        return $this->previewManager->getPreview($crop, $file, $x, $y);
    }
}
"""
        target_file.write_text(wrong_order_code, encoding="utf-8")
        assert verify_task1_impl(repo_dir) == 1, "Must reject wrong argument order to getPreview"

        # Case 4: Correct implementation passes
        correct_code = """<?php
class ApiController {
    public function getThumbnail($x, $y, $file, $crop = true) {
        return $this->previewManager->getPreview($file, $x, $y, $crop);
    }
}
"""
        target_file.write_text(correct_code, encoding="utf-8")
        assert verify_task1_impl(repo_dir) == 0, "Must accept correct implementation"


def test_verify_regression_exit_code_3_when_no_php():
    """Issue 16: Regression suite must return exit code 3 (NOT_MEASURED) when PHP runtime is missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = Path(tmp_dir)
        api_dir = repo_dir / "apps" / "files" / "lib" / "Controller"
        api_dir.mkdir(parents=True, exist_ok=True)
        target_file = api_dir / "ApiController.php"

        target_file.write_text("<?php\nclass ApiController { public function test() { return true; } }\n", encoding="utf-8")

        # Mock shutil.which to return None (no php binary)
        with patch("shutil.which", return_value=None):
            code = run_regression_check(repo_dir)
            assert code == 3, f"Expected returncode 3 (NOT_MEASURED), got {code}"


def test_verify_regression_syntax_error():
    """Issue 16: Regression suite must return code 1 when syntax is broken."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = Path(tmp_dir)
        api_dir = repo_dir / "apps" / "files" / "lib" / "Controller"
        api_dir.mkdir(parents=True, exist_ok=True)
        target_file = api_dir / "ApiController.php"

        # Unbalanced brace syntax error
        target_file.write_text("<?php\nclass ApiController { public function test() { return true;\n", encoding="utf-8")

        with patch("shutil.which", return_value=None):
            code = run_regression_check(repo_dir)
            assert code == 1, f"Expected returncode 1 (SYNTAX_ERROR), got {code}"


def test_gatekeeper_enforces_tool_calls_requirement():
    """Issue 20 & 22: Gatekeeper must reject trials that executed 0 tool calls."""
    from run_agent_validation import evaluate_trial_with_gatekeeper

    # Synthetic trial where test passed and syntax passed, but tool_calls == 0
    trial_zero_tools = {
        "trial_id": "trial_001",
        "task_id": "TASK-DEV-01",
        "tool_calls_executed": 0,
        "acceptance_exit_code": 0,
        "regression_exit_code": 0,
        "diff_present": True
    }
    eval_result = evaluate_trial_with_gatekeeper(trial_zero_tools)
    assert eval_result["accepted"] is False, "Trial with 0 tool calls must be rejected"
    assert "ZERO_TOOL_CALLS" in eval_result["reasons"] or "NO_TOOL_EXECUTION" in eval_result["reasons"]

    # Trial with tool_calls > 0 and passing tests
    trial_valid = {
        "trial_id": "trial_002",
        "task_id": "TASK-DEV-01",
        "tool_calls_executed": 3,
        "acceptance_exit_code": 0,
        "regression_exit_code": 0,
        "diff_present": True
    }
    eval_valid = evaluate_trial_with_gatekeeper(trial_valid)
    assert eval_valid["accepted"] is True, "Valid trial with tool calls must be accepted"


def test_turn_budget_matrix_isolation():
    """Issue 19: Turn budget matrix (5 and 8) aggregated independently."""
    from run_agent_validation import aggregate_turn_budgets

    trials = [
        {"turn_budget": 5, "condition": "A", "accepted": True, "turns_used": 4},
        {"turn_budget": 5, "condition": "B", "accepted": False, "turns_used": 5},
        {"turn_budget": 8, "condition": "A", "accepted": True, "turns_used": 7},
        {"turn_budget": 8, "condition": "B", "accepted": True, "turns_used": 6},
    ]

    summary = aggregate_turn_budgets(trials)
    assert "budget_5" in summary or 5 in summary or "5" in summary
    assert "budget_8" in summary or 8 in summary or "8" in summary

    key5 = "budget_5" if "budget_5" in summary else (5 if 5 in summary else "5")
    key8 = "budget_8" if "budget_8" in summary else (8 if 8 in summary else "8")
    b5 = summary[key5]
    b8 = summary[key8]
    assert b5["total_trials"] == 2
    assert b8["total_trials"] == 2
    assert b5["accepted_trials"] == 1
    assert b8["accepted_trials"] == 2
