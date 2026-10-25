"""
Unit tests for Router and Runner Stage Parity (PF-P0-005).
Verifies:
1. All stages output by TaskRiskRouter have corresponding handlers in OrchestratorRunner.
2. Missing or unsupported stage names fail preflight validation instead of being silently skipped.
3. Every scheduled stage in a RoutingDecision is recorded in stages_executed.
4. "retriever" and "maker_revision" stages are properly handled and produce outputs.
"""

import unittest
from pathlib import Path
import tempfile
import shutil

from orchestrator.providers import LLMProvider
from orchestrator.router import TaskRiskRouter, RoutingDecision, TaskRiskLevel
from orchestrator.runner import OrchestratorRunner, SUPPORTED_STAGES


class TestRouterStageParity(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="runner_parity_test_")
        self.runner = OrchestratorRunner(root_dir=Path(self.test_dir), provider_name="dry-run")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_all_router_stages_are_supported(self):
        """Every stage emitted by TaskRiskRouter for all risk levels must be in SUPPORTED_STAGES."""
        router = TaskRiskRouter()
        decisions = [
            router.route("Simple typo fix in helper method"),
            router.route("Standard cross-module feature update"),
            router.route("Architectural redesign and database migration"),
        ]
        for dec in decisions:
            for stage in dec.stages:
                # 'reviewer' and 'reviewer_code' are accepted review aliases
                normalized = "reviewer_code" if stage == "reviewer" else stage
                self.assertIn(
                    normalized,
                    SUPPORTED_STAGES,
                    f"Router emitted stage '{stage}' which is not in runner SUPPORTED_STAGES",
                )

    def test_unsupported_stage_raises_preflight_error(self):
        """Passing an unrecognized stage name must raise ValueError during preflight."""
        invalid_decision = RoutingDecision(
            risk_level=TaskRiskLevel.LOCAL_BUG,
            stages=["retriever", "nonexistent_stage_xyz", "implementer"],
            rationale="Test invalid stage",
            token_cost_estimate="0",
        )
        with self.assertRaises(ValueError) as ctx:
            self.runner.run_pipeline("test task", routing_decision=invalid_decision, verbose=False)
        self.assertIn("Unsupported pipeline stage", str(ctx.exception))

    def test_retriever_stage_execution(self):
        """The 'retriever' stage in LOCAL_BUG routing must execute and appear in stages_executed."""
        decision = RoutingDecision(
            risk_level=TaskRiskLevel.LOCAL_BUG,
            stages=["retriever", "gatekeeper"],
            rationale="Test retriever only",
            token_cost_estimate="0",
        )
        res = self.runner.run_pipeline("test task", routing_decision=decision, verbose=False)
        self.assertIn("retriever", res["stages_executed"])
        self.assertIn("stage_retriever", res)

    def test_maker_revision_stage_execution(self):
        """The 'maker_revision' stage in ARCHITECTURE_REFACTOR routing must execute and appear in stages_executed."""
        decision = RoutingDecision(
            risk_level=TaskRiskLevel.ARCHITECTURE_REFACTOR,
            stages=["maker", "reviewer_design", "maker_revision", "gatekeeper"],
            rationale="Test maker_revision",
            token_cost_estimate="0",
        )
        res = self.runner.run_pipeline("test task", routing_decision=decision, verbose=False)
        self.assertIn("maker_revision", res["stages_executed"])
        self.assertIn("stage_maker_revision", res)

    def test_no_scheduled_stage_is_silently_skipped(self):
        """Full ARCHITECTURE_REFACTOR pipeline must execute all 7 planned stages without skips."""
        decision = TaskRiskRouter.route("Architectural redesign of payment service")
        res = self.runner.run_pipeline("Architectural redesign", routing_decision=decision, verbose=False)
        for stage in decision.stages:
            normalized = "reviewer_code" if stage == "reviewer" else stage
            self.assertIn(
                normalized,
                res["stages_executed"],
                f"Scheduled stage '{stage}' was silently skipped by runner",
            )


if __name__ == "__main__":
    unittest.main()
