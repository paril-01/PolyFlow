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
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from experiments.benchmark_core.models import CheckStatus, VerificationResult


class EvaluatorOracle:
    def __init__(self, oracle_path: Path, repo_root: Path):
        self.oracle_path = oracle_path
        self.repo_root = repo_root
        self.oracle_data: Dict[str, Any] = {}
        if oracle_path.exists():
            self.oracle_data = json.loads(oracle_path.read_text(encoding="utf-8"))

    def get_task_oracle(self, task_id: str) -> Optional[Dict[str, Any]]:
        if isinstance(self.oracle_data, list):
            for t in self.oracle_data:
                if isinstance(t, dict) and t.get("task_id") == task_id:
                    return t
            return None
        elif isinstance(self.oracle_data, dict):
            tasks = self.oracle_data.get("tasks", self.oracle_data)
            if isinstance(tasks, dict) and task_id in tasks:
                return tasks[task_id]
            elif isinstance(tasks, list):
                for t in tasks:
                    if isinstance(t, dict) and t.get("task_id") == task_id:
                        return t
        return None

    def evaluate_negative_control(self, clean_worktree_path: Path, task_id: str) -> CheckStatus:
        """
        L0 Negative Control: runs task behavioral test on pristine unedited worktree.
        Must FAIL for the issue/feature to confirm valid test oracle.
        Returns CheckStatus.PASS if the clean repo fails (expected), or CheckStatus.FAIL if clean repo already passes.
        """
        task_oracle = self.get_task_oracle(task_id) or {}
        hidden_eval = task_oracle.get("hidden_evaluator", {})
        verif_script = hidden_eval.get("verification_script")
        if not verif_script:
            return CheckStatus.SKIPPED

        script_path = self.repo_root / verif_script
        if not script_path.exists():
            return CheckStatus.SETUP_ERROR

        cmd = [sys.executable, str(script_path), "--worktree", str(clean_worktree_path)]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            # If it exits non-zero on pristine worktree, the negative control PASSES (defect confirmed present)
            if res.returncode != 0:
                return CheckStatus.PASS
            else:
                # Defect was already absent or test falsely passes on pristine tree!
                return CheckStatus.FAIL
        except Exception:
            return CheckStatus.SETUP_ERROR

    def evaluate_worktree(
        self, worktree_path: Path, task_id: str, modified_files: List[str], l0_status: Optional[CheckStatus] = None
    ) -> VerificationResult:
        """Executes full multi-level verification suite with quad-state checks."""
        t_start = time.perf_counter()
        task_oracle = self.get_task_oracle(task_id) or {}
        hidden_eval = task_oracle.get("hidden_evaluator", {})
        verif_script = hidden_eval.get("verification_script")
        levels = hidden_eval.get("verification_levels", ["L1_SYNTAX", "L2_TARGETED_TEST"])

        l0_check = l0_status if l0_status is not None else CheckStatus.PASS

        # 1. L1: Syntax Check
        php_bin = shutil.which("php")
        php_files = [f for f in modified_files if f.endswith(".php")]
        l1_pass = True
        l1_status = CheckStatus.NOT_MEASURED
        l1_logs = []

        if not php_files:
            l1_pass = True
            l1_status = CheckStatus.SKIPPED if len(modified_files) == 0 else CheckStatus.PASS
            l1_logs.append("No modified PHP files to lint")
        elif not php_bin:
            l1_pass = False
            l1_status = CheckStatus.SETUP_ERROR
            l1_logs.append("PHP binary not found on PATH; cannot perform L1 syntax check")
        else:
            for f in php_files:
                full_f = worktree_path / f
                if full_f.exists():
                    res = subprocess.run(["php", "-l", str(full_f)], capture_output=True, text=True)
                    if res.returncode != 0:
                        l1_pass = False
                        l1_logs.append(f"Syntax error in {f}: {res.stderr.strip()}")
                    else:
                        l1_logs.append(f"Syntax OK: {f}")
                else:
                    l1_pass = False
                    l1_logs.append(f"Missing modified file on disk: {f}")
            l1_status = CheckStatus.PASS if l1_pass else CheckStatus.FAIL

        # 2. L2: Targeted Behavioral Test
        l2_pass = False
        l2_status = CheckStatus.NOT_MEASURED
        l2_log = "L2 test skipped or not configured"
        if len(modified_files) == 0:
            l2_pass = False
            l2_status = CheckStatus.SKIPPED
            l2_log = "FAIL: Zero modified files; task not completed"
        elif "L2_TARGETED_TEST" in levels and verif_script:
            script_path = self.repo_root / verif_script
            if script_path.exists():
                cmd = [sys.executable, str(script_path), "--worktree", str(worktree_path)]
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    l2_pass = (res.returncode == 0)
                    l2_status = CheckStatus.PASS if l2_pass else CheckStatus.FAIL
                    l2_log = res.stdout.strip() if res.returncode == 0 else (res.stderr.strip() or res.stdout.strip())
                except subprocess.TimeoutExpired:
                    l2_pass = False
                    l2_status = CheckStatus.FAIL
                    l2_log = "L2 verification script timed out"
            else:
                l2_pass = False
                l2_status = CheckStatus.SETUP_ERROR
                l2_log = f"ERROR: Verification script {verif_script} not found on disk"

        # 3. L3: Upstream Affected Regression
        l3_pass = False
        l3_status = CheckStatus.NOT_MEASURED
        l3_log = "L3 regression not run"
        if len(modified_files) == 0:
            l3_pass = False
            l3_status = CheckStatus.SKIPPED
            l3_log = "REGRESSION_SKIPPED: Zero files modified in worktree"
        elif "L3_RELEVANT_REGRESSION" in levels:
            reg_script = self.repo_root / "experiments" / "rcir_v8_5" / "agent_tasks" / "verify_regression.py"
            if reg_script.exists():
                cmd = [sys.executable, str(reg_script), "--worktree", str(worktree_path)]
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                    l3_pass = (res.returncode == 0)
                    l3_status = CheckStatus.PASS if l3_pass else CheckStatus.FAIL
                    l3_log = res.stdout.strip() if res.returncode == 0 else (res.stderr.strip() or res.stdout.strip())
                except subprocess.TimeoutExpired:
                    l3_pass = False
                    l3_status = CheckStatus.FAIL
                    l3_log = "L3 regression timed out"
            else:
                l3_pass = False
                l3_status = CheckStatus.SETUP_ERROR
                l3_log = "SETUP_ERROR: verify_regression.py not found"
        else:
            # When L3 is not required, mark SKIPPED; l3_regression_passed remains False (Rule 0: skipped != pass)
            l3_pass = False
            l3_status = CheckStatus.SKIPPED
            l3_log = "L3_OPTIONAL_SKIPPED: Not required for this task"

        # Overall acceptance gate:
        # Requires:
        # 1. Nonempty modifications
        # 2. L0 negative control passed
        # 3. L1 syntax passed
        # 4. L2 targeted test passed
        # 5. L3 regression passed (if required)
        l3_satisfaction = (l3_status == CheckStatus.PASS) if "L3_RELEVANT_REGRESSION" in levels else True
        accepted = bool(
            len(modified_files) > 0
            and (l0_check in (CheckStatus.PASS, CheckStatus.SKIPPED))
            and l1_status == CheckStatus.PASS
            and l2_status == CheckStatus.PASS
            and l3_satisfaction
        )
        t_duration = time.perf_counter() - t_start

        return VerificationResult(
            accepted=accepted,
            l0_negative_control=l0_check,
            l1_syntax_passed=l1_pass,
            l1_syntax_status=l1_status,
            l1_logs=l1_logs,
            l2_targeted_passed=l2_pass,
            l2_targeted_status=l2_status,
            l2_log=l2_log[:1000],
            l3_regression_passed=l3_pass,
            l3_regression_status=l3_status,
            l3_log=l3_log[:1000],
            verification_duration_seconds=t_duration,
        )
