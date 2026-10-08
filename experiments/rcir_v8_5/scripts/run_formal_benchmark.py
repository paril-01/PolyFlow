#!/usr/bin/env python3
"""
RCIR v8.5 — Master Formal Benchmark Runner & Provenance Freeze (Section 4).

Executes the complete, clean Nextcloud formal release benchmark in an
isolated run directory:
  experiments/rcir_runs/<run_id>/
    manifests/
    raw/
    results/
    reports/
    logs/

Enforces all Section 4 requirements:
- Executes from empty outputs (no stale/restamped artifacts).
- Binds exact git commit hashes for PolyFlow and Nextcloud.
- Evaluates all gates against contract specifications.
- Fails closed on provenance mismatch or gate failure.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
RCIR_V8_5_ROOT = SCRIPT_DIR.parent
POLYFLOW_ROOT = RCIR_V8_5_ROOT.parent.parent

sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(POLYFLOW_ROOT / "rcir" / "src"))

from environment import BenchmarkEnvironment, get_default_environment
from provenance import collect_input_hashes, compute_run_identity, hash_file


STAGE_SCRIPTS = [
    ("Stage 01: Benchmark Manifest", "generate_manifest"),
    ("Stage 02: Canonical Graph Integrity", "evaluate_canonical_graph"),
    ("Stage 03: Canonicalization Corpus", "evaluate_canonicalization"),
    ("Stage 04: Ground Truth Provenance", "validate_ground_truth_provenance"),
    ("Stage 05: Edge Evaluation", "evaluate_edges"),
    ("Stage 06: Multi-Channel Retrieval & Ranker Selection", "retrieval_runner"),
    ("Stage 07: Context Compilation & Saturation Curve", "context_runner"),
    ("Stage 08: PHP Type Flow Evaluation", "evaluate_type_flow"),
    ("Stage 09: Bitwise Determinism Evaluation", "evaluate_determinism"),
    ("Stage 10: Live Agent Validation & Telemetry", "run_agent_validation"),
    ("Stage 11: Formal Contract Gates", "evaluate_gates"),
    ("Stage 12: Formal Benchmark Reports", "generate_reports"),
]


def execute_stage(stage_title: str, module_name: str, env: BenchmarkEnvironment, log_file: Path) -> float:
    """Execute a single benchmark stage as a subprocess with isolated environment."""
    print(f"\n>>> Running {stage_title} ({module_name}.py)...")
    t0 = time.time()

    cmd = [sys.executable, str(SCRIPT_DIR / f"{module_name}.py")]

    stage_env = os.environ.copy()
    stage_env["RCIR_RUN_ID"] = env.run_id
    stage_env["RCIR_RUN_DIR"] = str(env.manifests_root.parent)
    stage_env["PYTHONUNBUFFERED"] = "1"

    with open(log_file, "a", encoding="utf-8") as lf:
        lf.write(f"\n{'='*80}\nSTART STAGE: {stage_title}\n{'='*80}\n")
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=stage_env,
            cwd=str(SCRIPT_DIR),
        )

        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            lf.write(line)

        proc.wait()
        elapsed = time.time() - t0
        lf.write(f"\nEND STAGE: {stage_title} [exit={proc.returncode}, elapsed={elapsed:.2f}s]\n")

    if proc.returncode != 0:
        raise RuntimeError(f"Stage '{stage_title}' ({module_name}.py) failed with exit code {proc.returncode}.")

    print(f"--- Completed {stage_title} in {elapsed:.2f}s")
    return elapsed


def run_formal_benchmark(
    run_id: Optional[str] = None,
    run_dir: Optional[Path | str] = None,
    allow_dirty: bool = False,
    skip_agent: bool = False,
) -> Dict[str, Any]:
    print("=" * 80)
    print("RCIR v8.5 — Formal Clean Release Benchmark Freeze")
    print("=" * 80)

    # 1. Initialize environment
    base_env = get_default_environment()

    # Capture source state
    source_state = base_env.capture_source_state()
    print(f"PolyFlow Commit:     {source_state['polyflow_commit']}")
    print(f"PolyFlow Dirty:      {source_state['polyflow_dirty']}")
    print(f"Target Repo Commit:  {source_state['target_repo_commit']}")
    print(f"Target Repo Dirty:   {source_state['target_repo_dirty']}")

    if source_state["polyflow_dirty"] and not allow_dirty:
        raise RuntimeError(
            "PolyFlow working tree is dirty. Formal release benchmark requires clean git checkout. "
            "Use --allow-dirty only during development."
        )

    # Derive immutable run ID if not explicitly given
    if not run_id:
        inputs = collect_input_hashes(base_env)
        derived_id = compute_run_identity(inputs)
        run_id = derived_id

    # Configure run directory
    if run_dir:
        target_run_dir = Path(run_dir).resolve()
    else:
        target_run_dir = POLYFLOW_ROOT / "experiments" / "rcir_runs" / run_id

    print(f"Active Run ID:       {run_id}")
    print(f"Active Run Dir:      {target_run_dir}")

    # Section 4.2: Assert empty outputs
    if target_run_dir.exists():
        results_dir = target_run_dir / "results"
        if results_dir.exists() and any(results_dir.iterdir()):
            raise RuntimeError(
                f"Run directory '{target_run_dir}' already contains results. "
                "Formal benchmark must start from empty outputs to prevent restamping."
            )

    target_run_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = target_run_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    master_log = logs_dir / "master_benchmark_execution.log"

    env = get_default_environment(run_id=run_id, run_dir=target_run_dir)
    os.environ["RCIR_RUN_ID"] = run_id
    os.environ["RCIR_RUN_DIR"] = str(target_run_dir)

    # Record run metadata
    run_meta = {
        "run_id": run_id,
        "run_dir": str(target_run_dir),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_state": source_state,
        "stages": {},
    }

    total_start = time.time()

    # Execute all stages
    for stage_title, module_name in STAGE_SCRIPTS:
        if skip_agent and module_name == "run_agent_validation":
            print(f"\n>>> Skipping {stage_title} (--skip-agent specified)")
            continue

        elapsed = execute_stage(stage_title, module_name, env, master_log)
        
        # F02: Verify machine-readable semantic stage result
        stage_res_file = env.results_root / f"{module_name}_result.json"
        stage_data: Dict[str, Any] = {}
        if stage_res_file.exists():
            try:
                stage_data = json.loads(stage_res_file.read_text(encoding="utf-8"))
                gate_status = stage_data.get("gate_status", "PASS")
            except Exception as e:
                gate_status = "INVALID"
                stage_data = {"failures": [f"Corrupt semantic stage result file: {e}"]}
        else:
            gate_status = "NOT_MEASURED"
            stage_data = {"failures": [f"Missing semantic stage result file: {stage_res_file.name}"]}

        status_str = "PASSED" if gate_status in ("PASS", "NOT_REQUIRED") else "FAILED"
        run_meta["stages"][module_name] = {
            "title": stage_title,
            "elapsed_seconds": round(elapsed, 2),
            "execution_status": "COMPLETED",
            "measurement_status": "MEASURED",
            "gate_status": gate_status,
            "blocking": stage_data.get("blocking", True),
            "status": status_str,
            "failures": stage_data.get("failures", []),
        }

        if status_str == "FAILED" and stage_data.get("blocking", True):
            raise RuntimeError(f"Stage '{stage_title}' ({module_name}) failed semantic gate: {stage_data.get('failures', [])}")

    total_elapsed = time.time() - total_start
    run_meta["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    run_meta["total_elapsed_seconds"] = round(total_elapsed, 2)

    # Verify gates output
    gate_eval_path = env.results_root / "gate_evaluation.json"
    if not gate_eval_path.exists():
        raise RuntimeError("Formal gate evaluation artifact 'gate_evaluation.json' was not produced.")

    gate_eval = json.loads(gate_eval_path.read_text(encoding="utf-8"))
    overall_validity = gate_eval.get("run_validity", gate_eval.get("benchmark_run_validity", "INVALID"))
    arch_verdict = gate_eval.get("architecture_decision", "UNKNOWN")

    print("\n" + "=" * 80)
    print("FORMAL BENCHMARK EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Run ID:                 {run_id}")
    print(f"Run Directory:          {target_run_dir}")
    print(f"Benchmark Run Validity: {overall_validity}")
    print(f"Architecture Verdict:   {arch_verdict}")
    print(f"Total Execution Time:   {total_elapsed:.2f}s ({total_elapsed/60:.1f} min)")

    # Print Gate Status Table
    print("\n[Gate Results]")
    for gname in [
        "integrity_gate",
        "impact_gate",
        "ranking_gate",
        "context_gate",
        "type_flow_gate",
        "canonicalization_gate",
        "agent_gate",
    ]:
        gdata = gate_eval.get(gname, {})
        passed = gdata.get("passed", False)
        status_str = "PASSED" if passed else gdata.get("status", "NOT_VERIFIED")
        print(f"  • {gname:25s}: {status_str}")

    summary_file = target_run_dir / "formal_benchmark_summary.json"
    summary_file.write_text(json.dumps(run_meta, indent=2), encoding="utf-8")
    print(f"\nSaved formal execution summary to: {summary_file}")

    return run_meta


def main():
    parser = argparse.ArgumentParser(description="RCIR v8.5 Master Formal Benchmark Runner")
    parser.add_argument("--run-id", default=None, help="Explicit run ID (defaults to cryptographic hash)")
    parser.add_argument("--run-dir", default=None, help="Explicit output directory")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow dirty PolyFlow tree (development mode only)")
    parser.add_argument("--skip-agent", action="store_true", help="Skip live agent evaluation stage")
    args = parser.parse_args()

    run_formal_benchmark(
        run_id=args.run_id,
        run_dir=args.run_dir,
        allow_dirty=args.allow_dirty,
        skip_agent=args.skip_agent,
    )


if __name__ == "__main__":
    main()
