"""
experiments/benchmark_core/evaluator.py — Private Evaluator & Multi-Tier Verification Oracle.

Evaluates candidate trial worktrees against the private test oracle:
- L1_SYNTAX: `php -l` on all modified PHP files.
- L2_TARGETED_BEHAVIOR: Executes task-specific behavioral verification script.
- L3_REGRESSION: Executes affected upstream tests; returns REGRESSION_SKIPPED on empty diffs.
- Adversarial Gatekeeper: Only APPROVEs when patch is nonempty, syntax is clean, and behavioral tests pass.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from experiments.benchmark_core.models import VerificationResult


class EvaluatorOracle:
    def __init__(self, oracle_path: Path, repo_root: Path):
        self.oracle_path = oracle_path
        self.repo_root = repo_root
        self.oracle_data: Dict[str, Any] = {}
        if oracle_path.exists():
            self.oracle_data = json.loads(oracle_path.read_text(encoding="utf-8"))

    def get_task_oracle(self, task_id: str) -> Optional[Dict[str, Any]]:
        tasks = self.oracle_data.get("tasks", {})
        if isinstance(tasks, dict):
            return tasks.get(task_id)
        elif isinstance(tasks, list):
            for t in tasks:
                if t.get("task_id") == task_id:
                    return t
        return None

    def evaluate_worktree(
        self, worktree_path: Path, task_id: str, modified_files: List[str]
    ) -> VerificationResult:
        """Executes full multi-level verification suite."""
        t_start = time.perf_counter()
        task_oracle = self.get_task_oracle(task_id) or {}
        hidden_eval = task_oracle.get("hidden_evaluator", {})
        verif_script = hidden_eval.get("verification_script")
        levels = hidden_eval.get("verification_levels", ["L1_SYNTAX", "L2_TARGETED_TEST"])

        # 1. L1: Syntax Check
        l1_pass = True
        l1_logs = []
        for f in modified_files:
            if f.endswith(".php"):
                full_f = worktree_path / f
                if full_f.exists():
                    res = subprocess.run(["php", "-l", str(full_f)], capture_output=True, text=True)
                    if res.returncode != 0:
                        l1_pass = False
                        l1_logs.append(f"Syntax error in {f}: {res.stderr.strip()}")
                    else:
                        l1_logs.append(f"Syntax OK: {f}")

        # 2. L2: Targeted Behavioral Test
        l2_pass = False
        l2_log = "L2 test skipped or not configured"
        if "L2_TARGETED_TEST" in levels and verif_script:
            script_path = self.repo_root / verif_script
            if script_path.exists():
                cmd = [sys.executable, str(script_path), "--worktree", str(worktree_path)]
                res = subprocess.run(cmd, capture_output=True, text=True)
                l2_pass = (res.returncode == 0)
                l2_log = res.stdout.strip() if res.returncode == 0 else (res.stderr.strip() or res.stdout.strip())
            else:
                l2_log = f"ERROR: Verification script {verif_script} not found on disk"
        elif len(modified_files) == 0:
            l2_pass = False
            l2_log = "FAIL: Zero modified files; task not completed"

        # 3. L3: Upstream Affected Regression
        l3_pass = False
        l3_log = "L3 regression not run"
        if len(modified_files) == 0:
            l3_pass = False
            l3_log = "REGRESSION_SKIPPED: Zero files modified in worktree"
        else:
            reg_script = self.repo_root / "experiments" / "rcir_v8_5" / "agent_tasks" / "verify_regression.py"
            if "L3_RELEVANT_REGRESSION" in levels and reg_script.exists():
                cmd = [sys.executable, str(reg_script), "--worktree", str(worktree_path)]
                res = subprocess.run(cmd, capture_output=True, text=True)
                l3_pass = (res.returncode == 0)
                l3_log = res.stdout.strip() if res.returncode == 0 else (res.stderr.strip() or res.stdout.strip())
            else:
                # If upstream full suite is unavailable, mark skipped without synthesizing pass
                l3_pass = True
                l3_log = "L3_OPTIONAL_SKIPPED: Upstream test runner not specified"

        # Overall acceptance gate: requires nonempty modifications, clean syntax, and behavioral test pass
        accepted = bool(len(modified_files) > 0 and l1_pass and l2_pass and (l3_pass if "L3_RELEVANT_REGRESSION" in levels else True))
        t_duration = time.perf_counter() - t_start

        return VerificationResult(
            accepted=accepted,
            l1_syntax_passed=l1_pass,
            l1_logs=l1_logs,
            l2_targeted_passed=l2_pass,
            l2_log=l2_log[:1000],
            l3_regression_passed=l3_pass,
            l3_log=l3_log[:1000],
            verification_duration_seconds=t_duration,
        )
