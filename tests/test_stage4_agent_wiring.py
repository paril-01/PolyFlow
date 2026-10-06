"""
Tests for Stage 4: Agent Wiring & Harness Hardening (F04, F05, F06).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_5"))

from run_agent_validation import ConcreteRCIRContextProvider, execute_harness_command
from agent_tasks.verify_task1 import test_api_controller as verify_api_controller


def test_f04_prompt_and_context_provider_wiring():
    """
    F04 Verification:
    - Context loader must read rendered_prompt_markdown when available.
    - ConcreteRCIRContextProvider must match requested symbols (e.g. getThumbnail),
      track already_seen by unique entity_id without collapsing onto empty string,
      and enforce token budgets.
    """
    dev_contexts_path = REPO_ROOT / "experiments" / "rcir_v8_5" / "raw" / "context" / "dev_contexts.json"
    assert dev_contexts_path.exists(), "dev_contexts.json must exist"

    with open(dev_contexts_path, "r", encoding="utf-8") as f:
        dev_ctx_data = json.load(f)

    task_ctx = dev_ctx_data["tasks"]["TASK-DEV-01"]
    prompt = task_ctx.get("rendered_prompt_markdown") or task_ctx.get("prompt_markdown", "")
    assert len(prompt) > 4000, f"Expected rendered_prompt_markdown > 4000 chars, got {len(prompt)}"

    provider = ConcreteRCIRContextProvider(dev_ctx_data["tasks"])
    already_seen = set()

    # Query 1: search for getThumbnail
    res1 = provider.retrieve(symbol="getThumbnail", already_seen=already_seen, token_budget=1000)
    assert res1["entities_found"] > 0
    assert len(res1["entries"]) > 0
    # Must have populated already_seen with real entity_ids, NOT empty string
    assert "" not in already_seen
    assert len(already_seen) == len(res1["entries"])

    # Query 2: subsequent query with already_seen must not re-return already_seen entities
    seen_count_before = len(already_seen)
    res2 = provider.retrieve(symbol="getThumbnail", already_seen=already_seen, token_budget=1000)
    # Any new entries must have unique IDs
    for e in res2["entries"]:
        assert e["entity_id"] not in already_seen


def test_f05_harness_command_windows_space_safety():
    """
    F05 Verification:
    Harness command execution must pass arguments as arrays without shell=True,
    ensuring paths with spaces and backslashes (Windows profile dirs) do not truncate.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a synthetic path with spaces
        spaced_dir = Path(tmp_dir) / "Path With Spaces"
        spaced_dir.mkdir(parents=True, exist_ok=True)
        test_file = spaced_dir / "test.txt"
        test_file.write_text("ok", encoding="utf-8")

        # Test python -c inline runner with {worktree}
        cmd_inline = 'python -c "import os; assert os.path.exists(\'{worktree}/test.txt\')"'
        proc = execute_harness_command(cmd_inline, spaced_dir, REPO_ROOT)
        assert proc.returncode == 0, f"Failed execution with spaces: stdout={proc.stdout}, stderr={proc.stderr}"


def test_f06_verify_task1_rejects_incorrect_default_and_unused_variable():
    """
    F06 Verification:
    Acceptance verifier must:
    1. Reject non-existent file with exit code 2 (SETUP_ERROR).
    2. Reject signature when $crop defaults to false (ASSERTION_FAIL).
    3. Reject body when $crop is declared but not passed to getPreview (ASSERTION_FAIL).
    4. Accept only correct signature ($crop = true) and propagation to getPreview.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = Path(tmp_dir)
        api_dir = repo_dir / "apps" / "files" / "lib" / "Controller"
        api_dir.mkdir(parents=True, exist_ok=True)
        target_file = api_dir / "ApiController.php"

        # Case 1: Missing file -> returncode 2
        assert verify_api_controller(repo_dir / "non_existent") == 2

        # Case 2: $crop = false -> returncode 1
        code_false_default = """<?php
class ApiController {
    public function getThumbnail($x, $y, $file, $crop = false) {
        return $this->previewManager->getPreview($file, $x, $y, $crop);
    }
}
"""
        target_file.write_text(code_false_default, encoding="utf-8")
        assert verify_api_controller(repo_dir) == 1

        # Case 3: $crop declared but unused variable, not passed to getPreview -> returncode 1
        code_unused = """<?php
class ApiController {
    public function getThumbnail($x, $y, $file, $crop = true) {
        $unused = $crop;
        return $this->previewManager->getPreview($file, $x, $y);
    }
}
"""
        target_file.write_text(code_unused, encoding="utf-8")
        assert verify_api_controller(repo_dir) == 1

        # Case 4: Correct signature and propagation -> returncode 0
        code_correct = """<?php
class ApiController {
    public function getThumbnail($x, $y, $file, $crop = true) {
        return $this->previewManager->getPreview($file, $x, $y, $crop);
    }
}
"""
        target_file.write_text(code_correct, encoding="utf-8")
        assert verify_api_controller(repo_dir) == 0
