#!/usr/bin/env python3
"""
scripts/run_benchmark.py — Canonical Command for Live PolyFlow & RCIR Experiments.

Executes live, isolated paired A/B benchmark trials:
- Target: Pinned Nextcloud worktree (da57df078d0808a7235a0177bd99d23c010b472e).
- Arms: Baseline (tools only) vs RCIR (LiveRCIRContextProvider + tools).
- Provenance: Provider-native usage per turn, git diff, full verifier execution.
- Persistence: Immutable run folder under experiments/runs/<commit>_<timestamp>/.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from experiments.benchmark_core.models import (
    RunManifest,
    TrialKey,
    TrialResult,
    TrialStatus,
    UsageRecord,
    VerificationResult,
)
from experiments.benchmark_core.isolation import WorktreeManager, BenchmarkSetupError, PINNED_NEXTCLOUD_COMMIT
from experiments.benchmark_core.task_loader import load_public_tasks
from experiments.benchmark_core.evaluator import EvaluatorOracle
from experiments.benchmark_core.pairer import pair_trials
from experiments.benchmark_core.metrics import compute_benchmark_metrics
from experiments.benchmark_core.hashes import sha256_file, sha256_text

from orchestrator.providers import LLMProvider
from orchestrator.tools import RepoToolEnvironment
from orchestrator.agent_loop import ReActAgentRunner
from rcir.context.provider import LiveRCIRContextProvider, RCIRContextError


def parse_args():
    parser = argparse.ArgumentParser(description="Run live PolyFlow/RCIR benchmark experiments.")
    parser.add_argument("--target", default="nextcloud", help="Target repository identifier.")
    parser.add_argument("--target-sha", default=PINNED_NEXTCLOUD_COMMIT, help="Pinned target commit SHA.")
    parser.add_argument("--mode", default="dev", choices=["dev", "test"], help="Experiment mode (dev or test).")
    parser.add_argument("--tasks", default="", help="Path to public tasks manifest JSON.")
    parser.add_argument("--model", default="qwen2.5-coder:1.5b", help="LLM model name.")
    parser.add_argument("--provider", default="ollama", help="LLM provider name.")
    parser.add_argument("--turn-budget", type=int, default=12, help="Max agent turns per trial.")
    parser.add_argument("--replicates", type=int, default=1, help="Replication count per task.")
    parser.add_argument("--run-root", default="experiments/runs", help="Output directory for immutable runs.")
    parser.add_argument("--dry-run", action="store_true", help="Validate setup, task oracles, and provider without executing agent.")
    parser.add_argument("--verify-only", action="store_true", help="Run multi-tier evaluation on an existing worktree.")
    parser.add_argument("--worktree", default="", help="Worktree path for --verify-only mode.")
    return parser.parse_args()


def get_git_commit(repo_path: Path) -> str:
    res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else "unknown"


def is_git_dirty(repo_path: Path) -> bool:
    res = subprocess.run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)
    return bool(res.stdout.strip()) if res.returncode == 0 else False


def main():
    args = parse_args()
    print("=" * 80)
    print("POLYFLOW & RCIR BENCHMARK RUNNER (RULE 0 ENFORCED)")
    print(f"Target: {args.target} | Mode: {args.mode.upper()} | Model: {args.model} | Turns: {args.turn_budget}")
    print("=" * 80)

    # 1. Pinned commit & target repo validation
    target_repo = REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"
    if not target_repo.exists():
        print(f"[FAIL] Target repository not found: {target_repo}")
        sys.exit(1)

    polyflow_sha = get_git_commit(REPO_ROOT)
    polyflow_dirty = is_git_dirty(REPO_ROOT)
    start_iso_utc = datetime.utcnow().isoformat() + "Z"
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{polyflow_sha[:7]}_{run_timestamp}_{args.mode}"
    run_dir = REPO_ROOT / args.run_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Initialize Worktree Manager
    worktrees_root = run_dir / "worktrees"
    wt_manager = WorktreeManager(target_repo, worktrees_root)
    try:
        target_head = wt_manager.verify_target_checkout()
        print(f"[OK] Verified target repo at pinned commit: {target_head}")
    except BenchmarkSetupError as bse:
        print(f"[FAIL] Benchmark setup error: {bse}")
        sys.exit(1)

    # 2. Tasks & Evaluator setup
    default_tasks = REPO_ROOT / "experiments" / "final_blind_validation" / "test_design.json"
    tasks_file = Path(args.tasks) if args.tasks else default_tasks
    public_tasks = load_public_tasks(tasks_file)
    evaluator = EvaluatorOracle(tasks_file, REPO_ROOT)
    tasks_sha256 = sha256_file(tasks_file)
    print(f"[OK] Loaded {len(public_tasks)} public tasks from: {tasks_file.name} (SHA-256: {tasks_sha256[:12]}...)")

    # Handle --verify-only
    if args.verify_only:
        if not args.worktree:
            print("[FAIL] --verify-only requires --worktree path.")
            sys.exit(1)
        target_wt = Path(args.worktree).resolve()
        task_id = public_tasks[0]["task_id"] if public_tasks else "task_1"
        res = evaluator.evaluate_worktree(target_wt, task_id, ["lib/public/AppFramework/Http/Response.php"])
        print(f"[VERIFY-ONLY] Result: accepted={res.accepted}, l1={res.l1_syntax_passed}, l2={res.l2_targeted_passed}, l3={res.l3_regression_passed}")
        sys.exit(0 if res.accepted else 1)

    # Initialize Live RCIR Context Provider
    live_rcir = None
    graph_sha256 = ""
    graph_target_sha = ""
    try:
        live_rcir = LiveRCIRContextProvider(target_repo=target_repo, token_budget=4000, expected_commit=target_head)
        graph_sha256 = getattr(live_rcir, "graph_sha256", "")
        graph_target_sha = getattr(live_rcir, "graph_target_sha", "")
        print(f"[OK] Live RCIR Provider initialized (Graph: {live_rcir.graph_path.name}, SHA: {graph_sha256[:12]}...)")
    except Exception as e:
        print(f"[WARN] Live RCIR Provider initialization failed: {e}")
        live_rcir = None

    # Handle --dry-run
    if args.dry_run:
        print("\n--- DRY RUN SANITY CHECKS ---")
        print(f"Target commit verification: OK ({target_head})")
        print(f"Public tasks count: {len(public_tasks)}")
        if live_rcir and public_tasks:
            sample_t = public_tasks[0]
            try:
                sample_ctx = live_rcir.compile_task_context(sample_t["task_id"], sample_t["instructions"], token_budget=2000)
                print(f"Sample RCIR retrieval for {sample_t['task_id']}: OK ({len(sample_ctx)} chars)")
            except Exception as rce:
                print(f"Sample RCIR retrieval failed: {rce}")
        print("Dry run completed successfully under Rule 0.")
        sys.exit(0)

    provider = LLMProvider(provider_name=args.provider, model_name=args.model)

    # 3. Execute Paired Trials
    trials_results: List[TrialResult] = []
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    for task in public_tasks:
        task_id = task["task_id"]
        title = task["title"]
        instructions = task["instructions"]
        print(f"\n--- TASK: {task_id} ({title}) ---")

        for rep in range(1, args.replicates + 1):
            key = TrialKey(
                task_id=task_id,
                target_commit=target_head,
                model=args.model,
                seed=42 + rep,
                turn_budget=args.turn_budget,
                replicate=rep,
                experiment_version="3.0.0",
            )

            for condition in ["baseline", "rcir"]:
                trial_id = key.to_string(condition)
                print(f"  • Condition: {condition.upper()} (Trial: {trial_id})")

                # F02: Fail-closed if RCIR is requested but provider failed to initialize
                if condition == "rcir" and live_rcir is None:
                    print(f"    [FAIL-CLOSED] RCIR provider unavailable; marking trial TRIAL_INVALID_SETUP")
                    empty_verif = VerificationResult(
                        accepted=False,
                        l1_syntax_passed=False,
                        l1_logs=[],
                        l2_targeted_passed=False,
                        l2_log="RCIR provider setup failed",
                        l3_regression_passed=False,
                        l3_log="",
                    )
                    trials_results.append(
                        TrialResult(
                            trial_id=trial_id,
                            task_id=task_id,
                            condition=condition,
                            model=args.model,
                            target_commit=target_head,
                            seed=42 + rep,
                            replicate=rep,
                            turn_budget=args.turn_budget,
                            turns_used=0,
                            tool_calls_executed=0,
                            files_modified=[],
                            diff_length=0,
                            git_diff="",
                            verification=empty_verif,
                            gatekeeper="REJECT",
                            status=TrialStatus.TRIAL_INVALID_SETUP,
                            success=False,
                            verified_success=False,
                            agent_workflow_completed=False,
                            stop_reason="PROVIDER_UNAVAILABLE",
                            duration_seconds=0.0,
                            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                            usage_records=[],
                            error="Live RCIR context provider failed initialization",
                        )
                    )
                    continue

                trial_raw_dir = raw_dir / task_id / condition / f"rep{rep}"
                trial_raw_dir.mkdir(parents=True, exist_ok=True)

                context_prompt = ""
                context_provider = None
                trace_id = None

                # Compile context for RCIR arm with fail-closed guarantee (F02)
                if condition == "rcir":
                    try:
                        context_prompt = live_rcir.compile_task_context(task_id, instructions, token_budget=4000)
                        context_provider = live_rcir
                        trace_id = f"trace_{trial_id}"
                    except Exception as rce:
                        print(f"    [FAIL-CLOSED] Live RCIR retrieval failed: {rce}")
                        empty_verif = VerificationResult(
                            accepted=False,
                            l1_syntax_passed=False,
                            l1_logs=[],
                            l2_targeted_passed=False,
                            l2_log=f"RCIR context failed: {rce}",
                            l3_regression_passed=False,
                            l3_log="",
                        )
                        trials_results.append(
                            TrialResult(
                                trial_id=trial_id,
                                task_id=task_id,
                                condition=condition,
                                model=args.model,
                                target_commit=target_head,
                                seed=42 + rep,
                                replicate=rep,
                                turn_budget=args.turn_budget,
                                turns_used=0,
                                tool_calls_executed=0,
                                files_modified=[],
                                diff_length=0,
                                git_diff="",
                                verification=empty_verif,
                                gatekeeper="REJECT",
                                status=TrialStatus.TRIAL_INVALID_CONTEXT,
                                success=False,
                                verified_success=False,
                                agent_workflow_completed=False,
                                stop_reason="RCIR_RETRIEVAL_FAILED",
                                duration_seconds=0.0,
                                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                                usage_records=[],
                                error=f"RCIR context failed: {rce}",
                            )
                        )
                        continue

                # Create isolated worktree with try/finally cleanup (F16)
                trial_worktree = wt_manager.create_trial_worktree(trial_id)
                diff_text = ""
                modified: List[str] = []
                try:
                    # L0 Negative control verification on pristine worktree (F08)
                    l0_status = evaluator.evaluate_negative_control(trial_worktree, task_id)

                    env = RepoToolEnvironment(repo_root=trial_worktree, context_provider=context_provider)
                    runner = ReActAgentRunner(provider=provider, env=env, max_turns=args.turn_budget)

                    t0 = time.perf_counter()
                    agent_res = runner.run(
                        task_id=task_id,
                        task_description=instructions,
                        condition=condition,
                        context_prompt=context_prompt,
                    )
                    duration = time.perf_counter() - t0

                    # Independent git diff census (F10)
                    modified = env.get_modified_files()
                    diff_text = wt_manager.get_worktree_diff(trial_worktree) or env.get_git_diff()

                    # Multi-tier verification with L0 negative control
                    verif = evaluator.evaluate_worktree(trial_worktree, task_id, modified, l0_status=l0_status)

                    # Distinct terminal states (F05)
                    if verif.accepted:
                        status = TrialStatus.TRIAL_SUCCESS
                        stop_reason = "VERIFIED_SUCCESS"
                    elif agent_res.error and ("timeout" in agent_res.error.lower() or "timed out" in agent_res.error.lower()):
                        status = TrialStatus.TRIAL_TIMEOUT_PROVIDER
                        stop_reason = "PROVIDER_TIMEOUT"
                    elif agent_res.turns >= args.turn_budget:
                        status = TrialStatus.TRIAL_BUDGET_EXHAUSTED
                        stop_reason = "BUDGET_EXHAUSTED"
                    elif len(modified) == 0:
                        status = TrialStatus.TRIAL_FAILED_AGENT
                        stop_reason = "NO_MODIFICATIONS"
                    elif not verif.l1_syntax_passed:
                        status = TrialStatus.TRIAL_FAILED_BEHAVIOR
                        stop_reason = "SYNTAX_ERROR"
                    elif not verif.l2_targeted_passed:
                        status = TrialStatus.TRIAL_FAILED_BEHAVIOR
                        stop_reason = "TARGETED_TEST_FAILED"
                    elif not verif.l3_regression_passed:
                        status = TrialStatus.TRIAL_FAILED_REGRESSION
                        stop_reason = "REGRESSION_FAILED"
                    else:
                        status = TrialStatus.TRIAL_FAILED_BEHAVIOR
                        stop_reason = "FAILED"

                    prompt_tokens = sum(u.get("input_tokens", 0) for u in agent_res.usage_records)
                    completion_tokens = sum(u.get("output_tokens", 0) for u in agent_res.usage_records)
                    total_tokens = prompt_tokens + completion_tokens

                    trial_record = TrialResult(
                        trial_id=trial_id,
                        task_id=task_id,
                        condition=condition,
                        model=args.model,
                        target_commit=target_head,
                        seed=42 + rep,
                        replicate=rep,
                        turn_budget=args.turn_budget,
                        turns_used=agent_res.turns,
                        tool_calls_executed=agent_res.tool_calls_executed,
                        files_modified=modified,
                        diff_length=len(diff_text),
                        git_diff=diff_text,
                        verification=verif,
                        gatekeeper="APPROVE" if verif.accepted else "REJECT",
                        status=status,
                        success=verif.accepted,
                        verified_success=verif.accepted,
                        agent_workflow_completed=getattr(agent_res, "agent_workflow_completed", False),
                        stop_reason=stop_reason,
                        duration_seconds=duration,
                        usage={
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": total_tokens,
                        },
                        usage_records=[
                            UsageRecord(
                                turn=u.get("turn", 1),
                                input_tokens=u.get("input_tokens", 0),
                                output_tokens=u.get("output_tokens", 0),
                                total_tokens=u.get("total_tokens", 0),
                                latency_seconds=u.get("latency", 0.0),
                                measurement_source=u.get("measurement_source", "PROVIDER_NATIVE"),
                            )
                            for u in agent_res.usage_records
                        ],
                        error=agent_res.error,
                        retrieval_trace_id=trace_id,
                    )
                    trials_results.append(trial_record)

                    # Persist raw trial artifacts immediately (F16)
                    (trial_raw_dir / "trial.json").write_text(json.dumps(trial_record.to_dict(), indent=2), encoding="utf-8")
                    (trial_raw_dir / "patch.diff").write_text(diff_text, encoding="utf-8")
                    with (trial_raw_dir / "provider_usage.jsonl").open("w", encoding="utf-8") as pf:
                        for u in agent_res.usage_records:
                            pf.write(json.dumps(u) + "\n")

                finally:
                    # Guaranteed cleanup in finally block (F16)
                    wt_manager.remove_trial_worktree(trial_id)

    # 4. Compute Pairs & Benchmark Metrics
    pairs = pair_trials(trials_results)
    metrics = compute_benchmark_metrics(pairs, total_trials=len(trials_results))

    # 5. Persist Immutable Run Directory
    results_dir = run_dir / "results"
    exports_dir = run_dir / "exports"
    reports_dir = run_dir / "reports"
    results_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Manifest with complete provenance (F15)
    manifest = RunManifest(
        schema_version="3.0.0",
        run_id=run_id,
        polyflow_sha=polyflow_sha,
        polyflow_dirty=polyflow_dirty,
        target_repo="nextcloud/server",
        target_sha=target_head,
        task_manifest_sha256=tasks_sha256,
        hidden_oracle_sha256=tasks_sha256,
        graph_sha256=graph_sha256,
        graph_target_sha=graph_target_sha,
        model=args.model,
        turn_budget=args.turn_budget,
        replicate_count=args.replicates,
        started_at_utc=start_iso_utc,
        start_time_utc=start_iso_utc,
        end_time_utc=datetime.utcnow().isoformat() + "Z",
        status="COMPLETED",
    )
    (run_dir / "manifest.json").write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
    (results_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (results_dir / "trials.json").write_text(json.dumps([t.to_dict() for t in trials_results], indent=2), encoding="utf-8")
    (results_dir / "pairs.json").write_text(json.dumps(pairs, indent=2), encoding="utf-8")

    # Generate CSV Exports
    _write_csv(exports_dir / "run_summary.csv", [metrics])
    _write_csv(exports_dir / "paired_token_usage.csv", pairs)
    _write_csv(exports_dir / "agent_trials.csv", [t.to_dict() for t in trials_results])

    print("\n" + "=" * 80)
    print("BENCHMARK EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Trials: {metrics['total_trials']} | Total Pairs: {metrics['total_pairs']}")
    print(f"Valid Pairs: {metrics['valid_pairs_count']} | Timeout Pairs: {metrics['timeout_pairs_count']}")
    print(f"Both Succeeded Pairs: {metrics['successful_both_pairs_count']}")
    print(f"Baseline Successes: {metrics['baseline_success_count']} | RCIR Successes: {metrics['rcir_success_count']}")
    print(f"Primary Efficiency Headline: {metrics['primary_efficiency_headline']} ({metrics['primary_efficiency_status']})")
    print(f"Agent Success Gate: {metrics['agent_gate_status']}")
    print(f"\nArtifacts persisted immutably in: {run_dir}")
    print("=" * 80)


def _write_csv(path: Path, rows: List[Dict[str, Any]]):
    if not rows:
        return
    headers = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            # Flatten dict/list values for CSV cells
            flat = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in r.items()}
            writer.writerow(flat)


if __name__ == "__main__":
    main()
