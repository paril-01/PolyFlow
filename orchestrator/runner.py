"""
AEF Sequential Pipeline Runner.
Orchestrates Maker -> Reviewer -> Implementer -> Reviewer -> Gatekeeper -> Historian in strict sequence.
Supports concrete repository tools for the Implementer agent with automated compiler/test verification.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from orchestrator.providers import LLMProvider, LLMResponse, LLMProviderError
from orchestrator.tools import RepoToolEnvironment
from orchestrator.agent_loop import ReActAgentRunner, AgentLoopResult


def _safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        cleaned = msg.encode("ascii", "replace").decode("ascii")
        print(cleaned)


class OrchestratorRunner:
    def __init__(
        self,
        root_dir: Optional[Path] = None,
        provider_name: str = "auto",
        tool_env: Optional[RepoToolEnvironment] = None,
    ):
        if root_dir is None:
            self.root_dir = Path(__file__).parent.parent
        else:
            self.root_dir = Path(root_dir)

        self.provider = LLMProvider(provider_name=provider_name)
        self.tool_env = tool_env
        self.output_dir = self.root_dir / ".aef_output"
        self.output_dir.mkdir(exist_ok=True)

    def _load_prompt(self, relative_path: str) -> str:
        full_path = self.root_dir / relative_path
        if full_path.exists():
            return full_path.read_text(encoding="utf-8")
        return f"System prompt at {relative_path} not found."

    def run_pipeline(
        self,
        user_request: str,
        test_command: Optional[str] = None,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        if verbose:
            _safe_print("\n==================================================")
            _safe_print("STARTING AEF SEQUENTIAL PIPELINE RUN")
            _safe_print(f"Provider: {self.provider.provider_name.upper()}")
            _safe_print(f"Tool Environment: {'ACTIVE' if self.tool_env else 'PROMPT_ONLY'}")
            _safe_print(f"Request:  {user_request}")
            _safe_print("==================================================\n")

        # ---------------------------------------------------------
        # STAGE 1: Maker Agent (Discovery & Design)
        # ---------------------------------------------------------
        if verbose:
            _safe_print("[1/6] Executing Stage 1: Maker Agent (Discovery & Design)...")
        maker_prompt = self._load_prompt("agents/maker/system-prompt.md")
        maker_user_input = (
            f"User Request: {user_request}\n\n"
            "Perform requirement discovery, architecture trade-off analysis, and generate ADRs and requirements spec."
        )
        stage1_output = self.provider.generate(maker_prompt, maker_user_input)
        results["stage1_maker"] = stage1_output
        (self.output_dir / "01_maker_design.md").write_text(stage1_output, encoding="utf-8")

        # ---------------------------------------------------------
        # STAGE 2: Reviewer Agent (Design Review)
        # ---------------------------------------------------------
        if verbose:
            _safe_print("[2/6] Executing Stage 2: Reviewer Agent (Adversarial Design Review)...")
        reviewer_prompt = self._load_prompt("agents/reviewer/system-prompt.md")
        reviewer_user_input = (
            f"Original Request: {user_request}\n\n"
            f"Maker Design Output:\n{stage1_output}\n\n"
            "Perform an adversarial design review across the 12 engineering dimensions. Output severity findings and a clear Verdict."
        )
        stage2_output = self.provider.generate(reviewer_prompt, reviewer_user_input)
        results["stage2_reviewer_design"] = stage2_output
        (self.output_dir / "02_reviewer_design_review.md").write_text(stage2_output, encoding="utf-8")

        # ---------------------------------------------------------
        # STAGE 3: Implementer Agent (Production Code with Repo Tools)
        # ---------------------------------------------------------
        if verbose:
            _safe_print("[3/6] Executing Stage 3: Implementer Agent...")

        diff_content = ""
        files_modified = []
        test_result = None

        if self.tool_env:
            if verbose:
                _safe_print("  -> Running tool-calling ReAct loop (inspect, search, edit, compile/test)...")
            react_runner = ReActAgentRunner(provider=self.provider, env=self.tool_env, max_turns=5)
            agent_loop_res = react_runner.run(
                task_id="AEF-TASK",
                task_description=user_request,
                condition="tool_enabled",
                context_prompt=f"Approved Design:\n{stage1_output[:400]}\n\nReview Notes:\n{stage2_output[:400]}",
                test_command=test_command,
            )
            stage3_output = (
                f"Summary: {agent_loop_res.summary}\n"
                f"Files Modified: {agent_loop_res.files_modified}\n"
                f"Turns: {agent_loop_res.turns}\n"
                f"Git Diff:\n{agent_loop_res.git_diff}\n"
            )
            diff_content = agent_loop_res.git_diff
            files_modified = agent_loop_res.files_modified
            test_result = agent_loop_res.final_test_result
            results["agent_loop_result"] = agent_loop_res.to_dict()
        else:
            implementer_prompt = self._load_prompt("agents/implementer/system-prompt.md")
            implementer_user_input = (
                f"Original Request: {user_request}\n\n"
                f"Approved Design:\n{stage1_output}\n\n"
                f"Design Review Notes:\n{stage2_output}\n\n"
                "Write production-quality, tested, and documented code adhering to minimal safe changes and SOLID principles."
            )
            stage3_output = self.provider.generate(implementer_prompt, implementer_user_input)

        results["stage3_implementer"] = stage3_output
        (self.output_dir / "03_implementer_code.md").write_text(stage3_output, encoding="utf-8")

        # ---------------------------------------------------------
        # STAGE 4: Reviewer Agent (Code & Security Review)
        # ---------------------------------------------------------
        if verbose:
            _safe_print("[4/6] Executing Stage 4: Reviewer Agent (Adversarial Code & Diff Review)...")
        stage4_user_input = (
            f"Original Request: {user_request}\n\n"
            f"Implemented Code / Diff:\n{diff_content if diff_content else stage3_output}\n\n"
            f"Test Execution Result: {test_result}\n\n"
            "Review the changes for correctness, security, unintended regressions, and edge cases."
        )
        stage4_output = self.provider.generate(reviewer_prompt, stage4_user_input)
        results["stage4_reviewer_code"] = stage4_output
        (self.output_dir / "04_reviewer_code_review.md").write_text(stage4_output, encoding="utf-8")

        # ---------------------------------------------------------
        # STAGE 5: Gatekeeper Agent (Release Authority)
        # ---------------------------------------------------------
        if verbose:
            _safe_print("[5/6] Executing Stage 5: Gatekeeper Agent (Release Verification)...")
        gatekeeper_prompt = self._load_prompt("agents/gatekeeper/system-prompt.md")
        gatekeeper_user_input = (
            f"Original Request: {user_request}\n\n"
            f"Code Review Report:\n{stage4_output}\n\n"
            f"Files Modified: {files_modified}\n"
            f"Test Result: {test_result}\n\n"
            "Verify all release readiness criteria and issue a final decision: APPROVE, CONDITIONAL APPROVAL, or REJECT."
        )
        stage5_output = self.provider.generate(gatekeeper_prompt, gatekeeper_user_input)
        results["stage5_gatekeeper"] = stage5_output
        (self.output_dir / "05_gatekeeper_release_decision.md").write_text(stage5_output, encoding="utf-8")

        # ---------------------------------------------------------
        # STAGE 6: Historian Agent (Engineering Memory)
        # ---------------------------------------------------------
        if verbose:
            _safe_print("[6/6] Executing Stage 6: Historian Agent (Engineering Memory Log)...")
        historian_prompt = self._load_prompt("agents/historian/system-prompt.md")
        historian_user_input = (
            f"Full Lifecycle Summary:\n"
            f"Request: {user_request}\n"
            f"Design ADRs: {stage1_output[:300]}...\n"
            f"Gatekeeper Decision: {stage5_output[:300]}...\n\n"
            "Record the engineering history log, decision records, and technical debt entry."
        )
        stage6_output = self.provider.generate(historian_prompt, historian_user_input)
        results["stage6_historian"] = stage6_output
        (self.output_dir / "06_historian_memory_log.md").write_text(stage6_output, encoding="utf-8")

        # Capture complete provenance
        prov_dict = self.provider.last_response.to_dict() if self.provider.last_response else {
            "provider": self.provider.provider_name,
            "endpoint": "local",
            "model": "unknown",
            "simulation_fallback": False,
        }
        results["total_tokens_consumed"] = getattr(self.provider, "total_tokens_consumed", 0)
        results["gatekeeper_decision_text"] = stage5_output
        results["provenance"] = prov_dict
        results["files_modified"] = files_modified
        results["git_diff"] = diff_content
        results["test_result"] = test_result

        if verbose:
            _safe_print("\n==================================================")
            _safe_print("PIPELINE EXECUTION COMPLETE!")
            _safe_print(f"Total LLM Tokens: {results['total_tokens_consumed']}")
            _safe_print(f"Provider: {prov_dict.get('provider')} ({prov_dict.get('model')})")
            _safe_print(f"Simulation Fallback: {prov_dict.get('simulation_fallback')}")
            _safe_print(f"Artifacts saved to: {self.output_dir}")
            _safe_print("==================================================\n")

        return results
