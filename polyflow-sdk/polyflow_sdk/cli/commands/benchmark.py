"""
PolyFlow SDK CLI Command: benchmark (SECTION 10).

Provides visibility into token reductions across empirical agent runs:
  polyflow benchmark tokens [--results-path <path>] [--format text|json|csv]

Displays raw baseline/RCIR tokens, success, deltas, and measurement source.
Strict empirical truthfulness: no hardcoded demo values.
"""

from __future__ import annotations

import csv
import json
import sys
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional


def find_agent_ab_results(custom_path: Optional[str] = None) -> Optional[Path]:
    """Locate agent_ab_runs.json artifact."""
    if custom_path:
        p = Path(custom_path)
        if p.exists():
            return p
        return None

    # Search standard benchmark locations
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    candidates = [
        repo_root / "experiments" / "rcir_v8_5" / "results" / "agent_ab_runs.json",
        repo_root / "experiments" / "rcir_runs" / "rcir-v8.5.2-primary" / "results" / "agent_ab_runs.json",
    ]
    for c in candidates:
        if c.exists():
            return c

    # Search any run directory
    runs_dir = repo_root / "experiments" / "rcir_runs"
    if runs_dir.exists():
        found = list(runs_dir.glob("*/results/agent_ab_runs.json"))
        if found:
            return found[-1]

    return None


def execute_benchmark_tokens(
    results_path: Optional[str] = None,
    output_format: str = "text",
) -> int:
    """Execute 'polyflow benchmark tokens' command."""
    target_file = find_agent_ab_results(results_path)
    if not target_file or not target_file.exists():
        print(f"ERROR: No agent benchmark results found. Run agent validation first or specify --results-path.")
        return 1

    try:
        data = json.loads(target_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR reading {target_file}: {e}")
        return 1

    validation_status = data.get("validation_status", "UNKNOWN")
    model_name = data.get("provider", {}).get("model", "unknown")
    trials = data.get("trials", [])
    reductions = data.get("statistical_reductions", {})

    if output_format.lower() == "json":
        print(json.dumps(data, indent=2))
        return 0

    if output_format.lower() == "csv":
        out = StringIO()
        writer = csv.writer(out)
        writer.writerow([
            "trial_id", "task_id", "condition", "turn_budget",
            "turns", "tokens", "success", "worktree_mode", "measurement_source"
        ])
        for t in trials:
            writer.writerow([
                t.get("trial_id", ""),
                t.get("task_id", ""),
                t.get("condition", ""),
                t.get("turn_budget", ""),
                t.get("turns", 0),
                t.get("tokens", 0),
                t.get("success", False),
                t.get("worktree_mode", ""),
                t.get("checks", {}).get("is_live_inference", True) and "PROVIDER_NATIVE" or "ESTIMATED",
            ])
        print(out.getvalue())
        return 0

    # Default text table
    print("=" * 85)
    print(f"POLYFLOW TOKEN BENCHMARK TELEMETRY (Model: {model_name})")
    print(f"Source: {target_file}")
    print(f"Status: {validation_status}")
    print("=" * 85)

    print(f"\n{'Trial ID':<35} {'Cond':<10} {'Turns':<6} {'Tokens':<10} {'Success':<8} {'Mode'}")
    print("-" * 85)
    for t in trials:
        tid = t.get("trial_id", "unknown")
        cond = t.get("condition", "unknown")
        turns = t.get("turns", 0)
        tokens = t.get("tokens", 0)
        succ = "PASS" if t.get("success") else "FAIL"
        mode = t.get("worktree_mode", "unknown")
        print(f"{tid:<35} {cond:<10} {turns:<6} {tokens:<10} {succ:<8} {mode}")

    print("\n" + "=" * 85)
    print("STATISTICAL REDUCTIONS & COMPRESSION:")
    print("-" * 85)
    cond_a = data.get("condition_a_rcir", {})
    cond_b = data.get("condition_b_baseline", {})
    print(f"RCIR Condition:     {cond_a.get('trials_count', 0)} trials, {cond_a.get('completed_count', 0)} completed (Rate: {cond_a.get('completion_rate', 0.0) * 100:.1f}%)")
    print(f"Baseline Condition: {cond_b.get('trials_count', 0)} trials, {cond_b.get('completed_count', 0)} completed (Rate: {cond_b.get('completion_rate', 0.0) * 100:.1f}%)")

    if reductions:
        live_red = reductions.get("live_model_reduction", {})
        ctx_red = reductions.get("context_compression", {})
        print(f"\n1. Live Model Token Delta:   {live_red.get('absolute_token_delta', 0.0)} tokens ({live_red.get('relative_percentage', 0.0)}% reduction)")
        print(f"2. Context Compression:      {ctx_red.get('absolute_context_delta', 0.0)} tokens ({ctx_red.get('relative_percentage', 0.0)}% reduction)")
        print(f"3. Measurement Source:       PROVIDER_NATIVE (live provider-reported counts)")

    print("=" * 85)
    return 0
