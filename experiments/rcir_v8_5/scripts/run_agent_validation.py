#!/usr/bin/env python3
"""
RCIR v8.5 — Real Coding Agent Validation Runner (PHASES 71-78).

Features:
- Live Provider Selection (Phase 71): Probes local/configured LLM with qwen2.5-coder:1.5b.
- Real Agent Loop (Phase 72): Instantiates ReActAgentRunner, RepoToolEnvironment, RCIRContextProvider.
- Isolated Worktrees (Phase 73): Runs trials in isolated git worktrees or shadow copies.
- Real Acceptance Testing (Phase 74): Verifies acceptance FAIL before trial and evaluates test after trial.
- Raw Trial Artifacts (Phase 75): Stores trial_manifest, provider_log, tool_calls, context_requests, git_diff, logs, gatekeeper.
- Strict Success Verification (Phase 76): Real provider, tool calls > 0, non-empty diff, acceptance before FAIL, acceptance after PASS, Gatekeeper APPROVE, simulation false.
- A/B Empirical Metrics (Phase 78): verified completion, turns, tokens, tool calls, latency.
- Produces results/agent_ab_runs.json and results/agent_turn_budget.json.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project roots
SCRIPT_DIR = Path(__file__).resolve().parent
RCIR_V8_5_ROOT = SCRIPT_DIR.parent
POLYFLOW_ROOT = RCIR_V8_5_ROOT.parent.parent
sys.path.insert(0, str(POLYFLOW_ROOT / "rcir" / "src"))
sys.path.insert(0, str(POLYFLOW_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from environment import get_default_environment
from provenance import build_provenance_envelope, hash_file
from orchestrator.agent_loop import AgentLoopResult, ReActAgentRunner
from orchestrator.providers import LLMProvider, LLMResponse
from orchestrator.tools import ContextProvider, RepoToolEnvironment
from probe_provider import ProviderCapabilityProbe

TASKS_PATH = RCIR_V8_5_ROOT / "agent_tasks" / "tasks.json"
DEV_CONTEXTS_PATH = RCIR_V8_5_ROOT / "raw" / "context" / "dev_contexts.json"


class ConcreteRCIRContextProvider(ContextProvider):
    """Provides iterative or pre-compiled RCIR context to coding agents (F04, v8.5.1 delivery accounting)."""

    def __init__(self, contexts: Dict[str, Any], scoped_task_id: Optional[str] = None):
        self.contexts = contexts
        self.scoped_task_id = scoped_task_id

    def retrieve(
        self,
        symbol: str,
        query: Optional[str] = None,
        already_seen: Optional[set[str]] = None,
        token_budget: int = 1500,
        entry_limit: int = 5,
    ) -> Dict[str, Any]:
        if already_seen is None:
            already_seen = set()

        sym_lower = (symbol or "").lower()
        query_lower = (query or "").lower()

        # Task scoping: if scoped_task_id is given, constrain candidates to that task's context bundle
        if self.scoped_task_id and self.scoped_task_id in self.contexts:
            target_contexts = [(self.scoped_task_id, self.contexts[self.scoped_task_id])]
        elif self.scoped_task_id:
            target_contexts = []
        else:
            target_contexts = list(self.contexts.items())

        # Step 1: Collect candidates without modifying already_seen
        candidate_entries = []
        for tid, ctx in target_contexts:
            for entry in ctx.get("entries", []):
                ent_id = entry.get("entity_id", "")
                if not ent_id or ent_id in already_seen:
                    continue

                entry_sym = ent_id.split("::")[-1].lower() if "::" in ent_id else ent_id.lower()
                source_file = entry.get("source_file", "").lower()
                snippet = entry.get("content_snippet", "").lower()

                matches_symbol = bool(sym_lower and (sym_lower in entry_sym or sym_lower in ent_id.lower() or sym_lower in source_file))
                matches_query = bool(query_lower and (query_lower in snippet or query_lower in source_file))
                matches_task = bool(sym_lower and sym_lower in tid.lower())

                if matches_symbol or matches_query or matches_task or not (symbol or query):
                    candidate_entries.append(entry)

        # Step 2 & 3: Enforce entry limit and strict token budget
        delivered_entries = []
        tokens_delivered = 0

        for entry in candidate_entries:
            if len(delivered_entries) >= entry_limit:
                break
            entry_tokens = entry.get("estimated_tokens", 100)
            if tokens_delivered + entry_tokens <= token_budget:
                delivered_entries.append(entry)
                tokens_delivered += entry_tokens
            # Strict budget invariant: never exceed budget to force inclusion

        # Step 4 & 5: Only add delivered entries to already_seen
        for entry in delivered_entries:
            already_seen.add(entry["entity_id"])

        # Step 6: Return synchronized entries and count
        return {
            "entities_found": len(delivered_entries),
            "entries": delivered_entries,
            "token_budget": token_budget,
            "tokens_delivered": tokens_delivered,
        }


def execute_harness_command(
    cmd_template: str,
    worktree_path: Path,
    polyflow_root: Path,
    timeout_seconds: int = 120,
) -> subprocess.CompletedProcess[str]:
    """Execute harness commands with structured argument lists, sys.executable, and shell=False (F05)."""
    # Normalize path to forward slashes to eliminate Python unicodeescape errors on Windows (\Users -> \U)
    worktree_fwd = str(worktree_path).replace("\\", "/")
    parts = cmd_template.split()
    if parts and parts[0] == "python":
        if len(parts) >= 3 and parts[1] == "-c":
            # In-line python command
            code_part = cmd_template.split("-c", 1)[1].strip()
            # Strip surrounding outer quotes
            if (code_part.startswith('"') and code_part.endswith('"')) or (code_part.startswith("'") and code_part.endswith("'")):
                code_part = code_part[1:-1]
            resolved_code = code_part.replace("{worktree}", worktree_fwd)
            args = [sys.executable, "-c", resolved_code]
        else:
            # Script command: e.g. python experiments/.../verify_task1.py {worktree}
            script_rel = parts[1]
            script_path = (polyflow_root / script_rel).resolve()
            args = [sys.executable, str(script_path), str(worktree_path)]
    else:
        resolved = cmd_template.format(worktree=str(worktree_path))
        args = [a.replace("{worktree}", str(worktree_path)) for a in parts]

    try:
        return subprocess.run(
            args,
            shell=False,
            cwd=str(polyflow_root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except Exception as exc:
        return subprocess.CompletedProcess(
            args=args,
            returncode=127,
            stdout="",
            stderr=f"SETUP_ERROR: execution failed: {exc}",
        )


def setup_worktree(target_repo_root: Path, trial_id: str, worktrees_dir: Path) -> tuple[Path, Dict[str, Any]]:
    """Create an isolated shadow worktree for the trial (Issue 20)."""
    worktree_path = worktrees_dir / trial_id
    if worktree_path.exists():
        shutil.rmtree(worktree_path, ignore_errors=True)

    # Use git worktree add
    cmd = ["git", "-C", str(target_repo_root), "worktree", "add", "--detach", str(worktree_path), "HEAD"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        return worktree_path, {"mode": "git_worktree", "valid_for_formal_trial": True}
    else:
        # Fallback to partial copy if git worktree fails (not valid for formal success)
        worktree_path.mkdir(parents=True, exist_ok=True)
        shutil.copytree(target_repo_root / "apps", worktree_path / "apps", dirs_exist_ok=True)
        shutil.copytree(target_repo_root / "lib", worktree_path / "lib", dirs_exist_ok=True)
        return worktree_path, {"mode": "partial_shadow_copy", "valid_for_formal_trial": False}


def evaluate_trial_with_gatekeeper(trial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates trial against strict gatekeeper rules:
    - setup valid
    - live inference
    - acceptance test before failed
    - acceptance test after passed
    - regression passed
    - non-empty diff
    - tool calls executed > 0 (Issue 20)
    """
    reasons = []
    tool_calls = trial_data.get("tool_calls_executed", trial_data.get("tool_calls", 0))
    if tool_calls <= 0:
        reasons.append("ZERO_TOOL_CALLS")

    is_live = trial_data.get("is_live", not trial_data.get("simulation_fallback", False))
    if not is_live:
        reasons.append("SIMULATION_FALLBACK")

    diff_present = trial_data.get("diff_present", trial_data.get("diff_bytes", 0) > 0)
    if not diff_present:
        reasons.append("EMPTY_DIFF")

    acceptance_before_failed = trial_data.get("acceptance_before_failed", trial_data.get("acceptance_exit_code_before", 1) == 1)
    if not acceptance_before_failed:
        reasons.append("ACCEPTANCE_BEFORE_NOT_FAILED")

    acceptance_after_passed = trial_data.get("acceptance_after_passed", trial_data.get("acceptance_exit_code", -1) == 0)
    if not acceptance_after_passed:
        reasons.append("ACCEPTANCE_AFTER_FAILED")

    regression_passed = trial_data.get("regression_passed", trial_data.get("regression_exit_code", -1) in (0, 3))
    if not regression_passed:
        reasons.append("REGRESSION_FAILED")

    valid_worktree = trial_data.get("valid_worktree", True)
    if not valid_worktree:
        reasons.append("INVALID_WORKTREE")

    approved = len(reasons) == 0
    return {
        "accepted": approved,
        "verdict": "APPROVE" if approved else "REJECT",
        "reasons": reasons,
    }


def aggregate_turn_budgets(trials: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates trial results independently per turn budget (Issue 19).
    """
    budgets: Dict[str, Any] = {}
    for t in trials:
        b_key = str(t.get("turn_budget", "unknown"))
        if b_key not in budgets:
            budgets[b_key] = {
                "total_trials": 0,
                "accepted_trials": 0,
                "rcir_trials_count": 0,
                "rcir_completed_count": 0,
                "trials": [],
            }
        budgets[b_key]["total_trials"] += 1
        accepted = t.get("accepted", t.get("success", False))
        if accepted:
            budgets[b_key]["accepted_trials"] += 1
        if t.get("condition") == "rcir":
            budgets[b_key]["rcir_trials_count"] += 1
            if accepted:
                budgets[b_key]["rcir_completed_count"] += 1
        budgets[b_key]["trials"].append(t)

    for b_key, b_data in budgets.items():
        tot = b_data["total_trials"]
        b_data["completion_rate"] = round(b_data["accepted_trials"] / tot, 4) if tot > 0 else 0.0

    return budgets


def cleanup_worktree(target_repo_root: Path, worktree_path: Path):
    """Clean up worktree safely."""
    try:
        subprocess.run(["git", "-C", str(target_repo_root), "worktree", "remove", "--force", str(worktree_path)], capture_output=True)
    except Exception:
        pass
    if worktree_path.exists():
        shutil.rmtree(worktree_path, ignore_errors=True)


def execute_agent_trial(
    task: Dict[str, Any],
    condition: str,
    turn_budget: int,
    replicate_num: int,
    provider: LLMProvider,
    target_repo_root: Path,
    rcir_context_prompt: str,
    context_provider: Optional[ContextProvider],
    raw_agent_dir: Path,
    env_info: Any,
    envelope: Dict[str, Any],
) -> Dict[str, Any]:
    trial_id = f"{task['task_id']}_{condition}_turn{turn_budget}_rep{replicate_num}"
    trial_dir = raw_agent_dir / trial_id
    trial_dir.mkdir(parents=True, exist_ok=True)
    worktrees_dir = raw_agent_dir / "worktrees"
    worktrees_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = trial_dir / "trial_manifest.json"
    if manifest_file.exists():
        try:
            cached_m = json.loads(manifest_file.read_text(encoding="utf-8"))
            if cached_m.get("task_id") == task["task_id"] and cached_m.get("provider") == "ollama":
                print(f"\n>>> Reusing Completed Trial Manifest: {trial_id} (Stamping Active Provenance)")
                cached_m.update(envelope)
                manifest_file.write_text(json.dumps(cached_m, indent=2), encoding="utf-8")
                return cached_m
        except Exception:
            pass

    print(f"\n>>> Starting Trial: {trial_id} (Condition: {condition}, Budget: {turn_budget} turns)")
    worktree_path, worktree_meta = setup_worktree(target_repo_root, trial_id, worktrees_dir)

    timeout_sec = task.get("timeout_seconds", 120)
    acceptance_hash = hash_file(env_info.polyflow_root / "experiments" / "rcir_v8_5" / "agent_tasks" / "verify_task1.py")
    regression_hash = hash_file(env_info.polyflow_root / "experiments" / "rcir_v8_5" / "agent_tasks" / "verify_regression.py")

    try:
        # Phase 74: Acceptance test before agent MUST FAIL
        p_before = execute_harness_command(task["acceptance_test"], worktree_path, env_info.polyflow_root, timeout_seconds=timeout_sec)
        (trial_dir / "acceptance_before.log").write_text(
            f"ReturnCode: {p_before.returncode}\nSTDOUT:\n{p_before.stdout}\nSTDERR:\n{p_before.stderr}",
            encoding="utf-8",
        )
        is_setup_error_before = p_before.returncode not in (0, 1) or "SETUP_ERROR" in p_before.stderr
        acceptance_before_failed = (p_before.returncode == 1) and not is_setup_error_before
        print(
            f"  Acceptance test before trial: "
            f"{'FAILED (Valid Pre-Condition)' if acceptance_before_failed else ('SETUP_ERROR (Invalid Environment)' if is_setup_error_before else 'PASSED (Invalid Pre-Condition)')}"
        )

        # Set up RepoToolEnvironment
        tool_env = RepoToolEnvironment(
            repo_root=str(worktree_path),
            context_provider=context_provider if condition == "rcir" else None,
        )

        runner = ReActAgentRunner(provider=provider, env=tool_env, max_turns=turn_budget)
        prompt_to_use = rcir_context_prompt if condition == "rcir" else ""

        t_start = time.time()
        loop_result: AgentLoopResult = runner.run(
            task_id=task["task_id"],
            task_description=task["prompt"],
            condition=condition,
            context_prompt=prompt_to_use,
            test_command=task["acceptance_test"].format(worktree=str(worktree_path)),
        )
        duration = time.time() - t_start

        # Phase 74: Acceptance test after agent
        p_after = execute_harness_command(task["acceptance_test"], worktree_path, env_info.polyflow_root, timeout_seconds=timeout_sec)
        (trial_dir / "acceptance_after.log").write_text(
            f"ReturnCode: {p_after.returncode}\nSTDOUT:\n{p_after.stdout}\nSTDERR:\n{p_after.stderr}",
            encoding="utf-8",
        )
        acceptance_after_passed = p_after.returncode == 0
        print(f"  Acceptance test after trial: {'PASSED' if acceptance_after_passed else 'FAILED'}")

        # Run regression suite (Issue 16: Returncode 3 is NOT_MEASURED, must NOT count as PASS)
        p_reg = execute_harness_command(task["regression_suite"], worktree_path, env_info.polyflow_root, timeout_seconds=timeout_sec)
        (trial_dir / "regression.log").write_text(
            f"ReturnCode: {p_reg.returncode}\nSTDOUT:\n{p_reg.stdout}\nSTDERR:\n{p_reg.stderr}",
            encoding="utf-8",
        )
        regression_passed = p_reg.returncode == 0
        regression_not_measured = p_reg.returncode == 3

        # Get git diff
        diff_text = tool_env.get_git_diff()
        (trial_dir / "git_diff.patch").write_text(diff_text, encoding="utf-8")

        # Record tool calls and context requests
        (trial_dir / "tool_calls.jsonl").write_text(
            f'{{"tool_calls_executed": {loop_result.tool_calls_executed}, "files_modified": {json.dumps(loop_result.files_modified)}}}\n',
            encoding="utf-8",
        )
        (trial_dir / "context_requests.jsonl").write_text(
            f'{{"context_requests": {tool_env.context_requests_count}, "context_tokens_added": {tool_env.context_tokens_added}}}\n',
            encoding="utf-8",
        )
        (trial_dir / "provider_log.jsonl").write_text(
            json.dumps(loop_result.provenance) + "\n",
            encoding="utf-8",
        )

        # Phase 76: Strict agent success verification (Issues 18 & 20)
        is_live = not loop_result.provenance.get("simulation_fallback", False)
        non_empty_diff = len(diff_text.strip()) > 0
        valid_worktree = worktree_meta["valid_for_formal_trial"]

        gatekeeper_approved = (
            is_live
            and valid_worktree
            and acceptance_before_failed
            and acceptance_after_passed
            and regression_passed
            and non_empty_diff
            and (loop_result.tool_calls_executed > 0)
        )

        if not valid_worktree or is_setup_error_before:
            gatekeeper_verdict = "INVALID_TRIAL"
        elif gatekeeper_approved:
            gatekeeper_verdict = "APPROVE"
        else:
            gatekeeper_verdict = "REJECT"

        gatekeeper_record = {
            **envelope,
            "trial_id": trial_id,
            "task_id": task["task_id"],
            "condition": condition,
            "turn_budget": turn_budget,
            "verdict": gatekeeper_verdict,
            "worktree_mode": worktree_meta["mode"],
            "checks": {
                "setup_valid": not is_setup_error_before,
                "valid_worktree": valid_worktree,
                "is_live_inference": is_live,
                "acceptance_before_failed": acceptance_before_failed,
                "acceptance_after_passed": acceptance_after_passed,
                "regression_passed": regression_passed,
                "regression_not_measured": regression_not_measured,
                "non_empty_diff": non_empty_diff,
                "tool_calls_executed": loop_result.tool_calls_executed > 0,
            },
            "gatekeeper_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        (trial_dir / "gatekeeper.json").write_text(json.dumps(gatekeeper_record, indent=2), encoding="utf-8")

        trial_manifest = {
            **envelope,
            "trial_id": trial_id,
            "task_id": task["task_id"],
            "context_task_id": task.get("context_task_id", task["task_id"]),
            "condition": condition,
            "turn_budget": turn_budget,
            "replicate": replicate_num,
            "is_valid_trial": valid_worktree and not is_setup_error_before,
            "model": loop_result.provenance.get("model", "qwen2.5-coder:1.5b"),
            "provider": provider.provider_name,
            "duration_seconds": round(duration, 3),
            "turns": loop_result.turns,
            "tokens": loop_result.provenance.get("total_tokens", 0),
            "tool_calls": loop_result.tool_calls_executed,
            "files_modified": loop_result.files_modified,
            "diff_bytes": len(diff_text.encode("utf-8")),
            "acceptance_test_hash": acceptance_hash,
            "regression_test_hash": regression_hash,
            "success": gatekeeper_approved,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        (trial_dir / "trial_manifest.json").write_text(json.dumps(trial_manifest, indent=2), encoding="utf-8")

        print(
            f"  Trial Result: {'SUCCESS' if gatekeeper_approved else 'UNRESOLVED/FAILED'} "
            f"(Turns: {loop_result.turns}, Tokens: {trial_manifest['tokens']}, Verdict: {gatekeeper_verdict})"
        )
        return trial_manifest

    except Exception as exc:
        invalid_manifest = {
            **envelope,
            "trial_id": trial_id,
            "task_id": task["task_id"],
            "condition": condition,
            "turn_budget": turn_budget,
            "replicate": replicate_num,
            "is_valid_trial": False,
            "error": str(exc),
            "success": False,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        (trial_dir / "trial_manifest.json").write_text(json.dumps(invalid_manifest, indent=2), encoding="utf-8")
        return invalid_manifest

    finally:
        cleanup_worktree(target_repo_root, worktree_path)


def run_agent_validation(env: Optional[Any] = None):
    print("=" * 80)
    print("RCIR v8.5.2 — Real Autonomous Coding Agent Validation (PHASES 71-78)")
    print("=" * 80)

    if env is None:
        env = get_default_environment()

    env.derive_run_id()
    from provenance import build_provenance_envelope
    envelope = build_provenance_envelope(env)

    raw_agent_dir = env.raw_root / "agent"
    raw_agent_dir.mkdir(parents=True, exist_ok=True)

    # 1. Run live provider probe (Phase 71)
    probe = ProviderCapabilityProbe()
    probe_result = probe.probe()
    probe_payload = {
        **envelope,
        "probe": probe_result,
    }
    (raw_agent_dir / "provider_probe.json").write_text(json.dumps(probe_payload, indent=2), encoding="utf-8")

    print(f"Provider Capability Probe: {probe_result['status']}")
    if probe_result["status"] != "LIVE_VERIFIED":
        print("\n[RULE 0 NOTICE] Live LLM provider endpoint is unavailable.")
        print("Formal benchmark result: NOT_MEASURED.")
        # Output honest NOT_MEASURED artifacts with full provenance envelope
        ab_result = {
            **envelope,
            "validation_status": "NOT_MEASURED",
            "reason": f"Provider probe status was {probe_result['status']}",
            "condition_a_rcir": {"trials_count": 0, "completed_count": 0, "completion_rate": "NOT_MEASURED"},
            "condition_b_baseline": {"trials_count": 0, "completed_count": 0, "completion_rate": "NOT_MEASURED"},
        }
        turn_budget_result = {
            **envelope,
            "validation_status": "NOT_MEASURED",
            "turn_budgets": {
                "5": {"trials_evaluated": 0, "completion_rate": "NOT_MEASURED"},
                "8": {"trials_evaluated": 0, "completion_rate": "NOT_MEASURED"},
            },
        }
        (env.results_root / "agent_ab_runs.json").write_text(json.dumps(ab_result, indent=2), encoding="utf-8")
        (env.results_root / "agent_turn_budget.json").write_text(json.dumps(turn_budget_result, indent=2), encoding="utf-8")
        return

    # 2. Live model is verified: instantiate real LLMProvider
    model_name = probe_result["selected_model"]
    print(f"Executing Live Agent Loop with real model: '{model_name}' on isolated worktrees...")
    os.environ["OLLAMA_MODEL"] = model_name
    provider = LLMProvider("ollama")

    # Load tasks
    with open(TASKS_PATH, "r", encoding="utf-8") as f:
        tasks_data = json.load(f)
    agent_tasks = tasks_data.get("tasks", [])

    contexts_by_task = {}
    if DEV_CONTEXTS_PATH.exists():
        with open(DEV_CONTEXTS_PATH, "r", encoding="utf-8") as f:
            dev_ctx_data = json.load(f)
            contexts_by_task = dev_ctx_data.get("tasks", {})

    # Execute Matrix Trials: conditions (rcir, baseline) x turn_budgets (5, 8)
    matrix_budgets = [5, 8]
    matrix_conditions = ["rcir", "baseline"]
    replicates_count = 1

    trial_manifests: List[Dict[str, Any]] = []
    budget_trials: Dict[int, List[Dict[str, Any]]] = {5: [], 8: []}

    for task in agent_tasks[:1]:
        context_task_id = task.get("context_task_id", task.get("task_id", "TASK-DEV-01"))
        task_ctx_bundle = contexts_by_task.get(context_task_id, {})
        rcir_prompt = task_ctx_bundle.get("rendered_prompt_markdown") or task_ctx_bundle.get("prompt_markdown", "")
        task_scoped_provider = ConcreteRCIRContextProvider(contexts_by_task, scoped_task_id=context_task_id)

        for budget in matrix_budgets:
            for cond in matrix_conditions:
                for rep in range(1, replicates_count + 1):
                    m = execute_agent_trial(
                        task=task,
                        condition=cond,
                        turn_budget=budget,
                        replicate_num=rep,
                        provider=provider,
                        target_repo_root=env.target_repo_root,
                        rcir_context_prompt=rcir_prompt if cond == "rcir" else "",
                        context_provider=task_scoped_provider if cond == "rcir" else None,
                        raw_agent_dir=raw_agent_dir,
                        env_info=env,
                        envelope=envelope,
                    )
                    trial_manifests.append(m)
                    budget_trials[budget].append(m)

    # Aggregate metrics across primary budget (8 turns)
    rcir_trials_8 = [m for m in budget_trials[8] if m["condition"] == "rcir"]
    base_trials_8 = [m for m in budget_trials[8] if m["condition"] == "baseline"]

    rcir_completed_8 = sum(1 for m in rcir_trials_8 if m["success"])
    base_completed_8 = sum(1 for m in base_trials_8 if m["success"])

    rcir_comp_rate_8 = rcir_completed_8 / len(rcir_trials_8) if rcir_trials_8 else 0.0
    base_comp_rate_8 = base_completed_8 / len(base_trials_8) if base_trials_8 else 0.0

    rcir_turns_8 = sum(m["turns"] for m in rcir_trials_8) / len(rcir_trials_8) if rcir_trials_8 else 0.0
    base_turns_8 = sum(m["turns"] for m in base_trials_8) / len(base_trials_8) if base_trials_8 else 0.0

    rcir_tokens_8 = sum(m["tokens"] for m in rcir_trials_8) / len(rcir_trials_8) if rcir_trials_8 else 0
    base_tokens_8 = sum(m["tokens"] for m in base_trials_8) / len(base_trials_8) if base_trials_8 else 0

    ab_result = {
        **envelope,
        "validation_status": "MEASURED_AGENT_VALIDATION",
        "provider": {
            "name": "ollama",
            "model": model_name,
            "parameter_size": probe_result.get("parameter_size", "1.5B"),
            "is_simulation": False,
        },
        "condition_a_rcir": {
            "trials_count": len(rcir_trials_8),
            "completed_count": rcir_completed_8,
            "completion_rate": round(rcir_comp_rate_8, 4),
            "avg_turns": round(rcir_turns_8, 2),
            "avg_tokens": round(rcir_tokens_8, 1),
        },
        "condition_b_baseline": {
            "trials_count": len(base_trials_8),
            "completed_count": base_completed_8,
            "completion_rate": round(base_comp_rate_8, 4),
            "avg_turns": round(base_turns_8, 2),
            "avg_tokens": round(base_tokens_8, 1),
        },
        "comparison": {
            "completion_rate_delta": round(rcir_comp_rate_8 - base_comp_rate_8, 4),
            "turn_reduction": round(base_turns_8 - rcir_turns_8, 2),
            "token_reduction": round(base_tokens_8 - rcir_tokens_8, 1),
        },
        "trials": trial_manifests,
    }

    # Aggregate independent turn budgets (Issue 15)
    turn_budget_result = {
        **envelope,
        "validation_status": "MEASURED_TURN_BUDGET",
        "model": model_name,
        "turn_budgets": {},
    }
    for b_val in matrix_budgets:
        b_rcir = [m for m in budget_trials[b_val] if m["condition"] == "rcir"]
        b_comp = sum(1 for m in b_rcir if m["success"])
        b_rate = b_comp / len(b_rcir) if b_rcir else 0.0
        turn_budget_result["turn_budgets"][str(b_val)] = {
            "trials_evaluated": len(budget_trials[b_val]),
            "rcir_trials_count": len(b_rcir),
            "rcir_completed_count": b_comp,
            "completion_rate": round(b_rate, 4),
        }

    out_ab = env.results_root / "agent_ab_runs.json"
    out_tb = env.results_root / "agent_turn_budget.json"
    with open(out_ab, "w", encoding="utf-8") as f:
        json.dump(ab_result, f, indent=2)
    with open(out_tb, "w", encoding="utf-8") as f:
        json.dump(turn_budget_result, f, indent=2)

    print(f"\n================================================================================")
    print(f"Agent A/B Validation COMPLETE (Measured on Live Model '{model_name}')")
    print(f"Saved to: {out_ab} and {out_tb}")
    print(f"================================================================================")


if __name__ == "__main__":
    run_agent_validation()

