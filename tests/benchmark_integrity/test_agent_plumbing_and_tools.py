"""
tests/benchmark_integrity/test_agent_plumbing_and_tools.py — Verification of Agent Loop & Tools.

Verifies:
1. Tool call parser correctly handles balanced nested braces, string escapes, and code fences.
2. apply_patch applies unified diffs atomically and blocks path traversal attempts.
3. Evaluator rejects trials where agent finished with zero modified files.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from orchestrator.agent_loop import extract_tool_call
from orchestrator.tools import RepoToolEnvironment
from experiments.benchmark_core.evaluator import EvaluatorOracle

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_tool_json_parser_nested_braces():
    """Verify that extract_tool_call handles nested JSON objects inside args and code fences."""
    # Test 1: Nested args object
    text_1 = """Here is my patch:
```json
{
  "tool": "apply_patch",
  "args": {
    "patch": "--- a/test.php\\n+++ b/test.php\\n@@ -1,2 +1,2 @@\\n-old\\n+new",
    "target_path": "lib/test.php"
  }
}
```
Done."""
    parsed_1 = extract_tool_call(text_1)
    assert parsed_1 is not None
    assert parsed_1["tool"] == "apply_patch"
    assert "patch" in parsed_1["args"]
    assert parsed_1["args"]["target_path"] == "lib/test.php"

    # Test 2: Unfenced raw JSON with nested braces and escaped quotes
    text_2 = 'I will now run: {"tool": "run_command", "args": {"command": "php -r \\"echo 123;\\""}}'
    parsed_2 = extract_tool_call(text_2)
    assert parsed_2 is not None
    assert parsed_2["tool"] == "run_command"
    assert parsed_2["args"]["command"] == 'php -r "echo 123;"'


def test_apply_patch_has_nonempty_real_diff():
    """Verify that apply_patch modifies target file and prevents directory traversal outside repo."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = Path(tmp_dir) / "repo"
        repo_dir.mkdir()
        test_file = repo_dir / "test.php"
        test_file.write_text("<?php\n$val = 1;\n", encoding="utf-8")

        env = RepoToolEnvironment(repo_root=repo_dir)

        # Valid edit
        patch = "--- a/test.php\n+++ b/test.php\n@@ -1,2 +1,2 @@\n-<?php\n-$val = 1;\n+<?php\n+$val = 2;\n"
        res = env.apply_patch(patch, target_path="test.php")
        assert "SUCCESS" in res
        assert "$val = 2;" in test_file.read_text(encoding="utf-8")

        # Path traversal attack attempt
        bad_patch = "--- a/../secret.txt\n+++ b/../secret.txt\n@@ -1,1 +1,1 @@\n+hack\n"
        bad_res = env.apply_patch(bad_patch, target_path="../secret.txt")
        assert "ERROR" in bad_res
        assert "Security violation" in bad_res or "Access denied" in bad_res


def test_agent_finish_without_patch_rejected():
    """Verify that an agent calling finish without modifying any files is rejected by the evaluator."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        worktree = Path(tmp_dir)
        oracle = EvaluatorOracle(REPO_ROOT / "experiments" / "final_blind_validation" / "test_design.json", REPO_ROOT)

        # Evaluate with zero modified files
        res = oracle.evaluate_worktree(worktree, "BLIND-TASK-01", modified_files=[])
        assert res.accepted is False, "Empty patch must never be accepted"
        assert "Zero files modified" in res.l3_log or "SETUP_ERROR" in res.l2_log
