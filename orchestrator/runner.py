"""
AEF Sequential Pipeline Runner.
Orchestrates Maker -> Reviewer -> Implementer -> Reviewer -> Gatekeeper -> Historian in strict sequence.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from orchestrator.providers import LLMProvider

def _safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        # Fallback for Windows charmap console
        cleaned = msg.encode("ascii", "replace").decode("ascii")
        print(cleaned)

class OrchestratorRunner:
    def __init__(self, root_dir: Optional[Path] = None, provider_name: str = "auto"):
        if root_dir is None:
            self.root_dir = Path(__file__).parent.parent
        else:
            self.root_dir = Path(root_dir)

        self.provider = LLMProvider(provider_name=provider_name)
        self.output_dir = self.root_dir / ".aef_output"
        self.output_dir.mkdir(exist_ok=True)

    def _load_prompt(self, relative_path: str) -> str:
        full_path = self.root_dir / relative_path
        if full_path.exists():
            return full_path.read_text(encoding="utf-8")
        return f"System prompt at {relative_path} not found."

    def run_pipeline(self, user_request: str, verbose: bool = True) -> Dict[str, Any]:
        results = {}

        if verbose:
            _safe_print("\n==================================================")
            _safe_print("STARTING AEF SEQUENTIAL PIPELINE RUN")
            _safe_print(f"Provider: {self.provider.provider_name.upper()}")
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
        # STAGE 3: Implementer Agent (Production Code)
        # ---------------------------------------------------------
        if verbose:
            _safe_print("[3/6] Executing Stage 3: Implementer Agent (Production Coding & Tests)...")
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
            _safe_print("[4/6] Executing Stage 4: Reviewer Agent (Adversarial Code & Security Review)...")
        stage4_user_input = (
            f"Implemented Code & Tests:\n{stage3_output}\n\n"
            "Review the code for correctness, security, error handling, performance, and test coverage."
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
            f"Implementation Output:\n{stage3_output}\n\n"
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

        if verbose:
            _safe_print("\n==================================================")
            _safe_print("PIPELINE EXECUTION COMPLETE!")
            _safe_print(f"Artifacts saved to: {self.output_dir}")
            _safe_print("==================================================\n")

        return results
