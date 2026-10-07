#!/usr/bin/env python3
"""
RCIR v8.5 — Formal Determinism Benchmark Evaluator (PHASE 66).

Executes the REAL frozen Nextcloud retrieval + context pipeline N=5 times
for representative Nextcloud tasks.
Verifies bitwise identity across:
1. Candidate IDs and order
2. Ranked output (IDs, ranks, scores)
3. Context plan (role allocations, candidate selections)
4. Final prompt markdown

Saves results to results/determinism_evaluation.json.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

# Add project roots
SCRIPT_DIR = Path(__file__).resolve().parent
RCIR_V8_5_ROOT = SCRIPT_DIR.parent
POLYFLOW_ROOT = RCIR_V8_5_ROOT.parent.parent
sys.path.insert(0, str(POLYFLOW_ROOT / "rcir" / "src"))
sys.path.insert(0, str(POLYFLOW_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from environment import BenchmarkEnvironment, get_default_environment
from rcir.context.compiler import ContextCompiler
from rcir.context.planner import ContextPlanner
from rcir.context.tokenizer import get_default_token_counter
from rcir.graph.canonical_graph import CanonicalGraph
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from retrieval_runner import build_ranker, discover_multi_channel_candidates

N_TRIALS = 5


def hash_obj(obj: any) -> str:
    serialized = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def run_single_task_pipeline(tid: str, env: Any, cg: Any, selected_config_name: str) -> dict:
    with open(env.ground_truth_root / "ground_truth.json", "r", encoding="utf-8") as f:
        gt_data = json.load(f)
    task_dict = gt_data["tasks"] if isinstance(gt_data["tasks"], dict) else {t["task_id"]: t for t in gt_data["tasks"]}
    task = task_dict[tid]

    req_sym = task.get("target_symbol") or task.get("requested_symbol", "")
    op_str = task.get("category") or task.get("operation", "behavior_change")
    try:
        op = ChangeOperation(op_str)
    except ValueError:
        op = ChangeOperation.BEHAVIOR_CHANGE

    spec = ChangeSpecification(
        operation=op,
        requested_symbol=req_sym,
        target_file_hint=task["target_file"],
        canonical_target_ids=task.get("canonical_target_ids") or [task.get("target_entity", "")],
        description=f"Determinism evaluation for {tid}",
    )

    ranker = build_ranker(selected_config_name, operation=op_str)
    compiler = ContextCompiler(repo_root=env.target_repo_root, tokenizer=get_default_token_counter())

    res = discover_multi_channel_candidates(spec, cg, cg.registry)
    candidates = list(res.candidates.values())
    cand_repr = [(c.entity_id, c.file_path, c.hop_distance) for c in candidates]
    c_hash = hash_obj(cand_repr)

    ranked = ranker.rank(candidates)
    ranked_repr = [(r.entity_id, r.rank, round(r.total_score, 6)) for r in ranked]
    r_hash = hash_obj(ranked_repr)

    plan = ContextPlanner.create_plan(ranked, token_budget=4000, spec=spec)
    pl_hash = hash_obj(plan.to_dict())

    pinned = set(spec.canonical_target_ids) if spec.canonical_target_ids else {task["target_file"]}
    compiled = compiler.compile(ranked, token_budget=4000, pinned_targets=pinned, plan=plan)
    prompt_markdown = compiled.render_prompt_markdown()
    pr_hash = hashlib.sha256(prompt_markdown.encode("utf-8")).hexdigest()

    return {
        "candidate_hash": c_hash,
        "ranked_hash": r_hash,
        "plan_hash": pl_hash,
        "prompt_hash": pr_hash,
        "total_tokens": compiled.total_estimated_tokens,
    }


def evaluate_determinism():
    print("=" * 80)
    print("RCIR v8.5.1 — Formal Selected Ranker Determinism Evaluation (PHASE 66)")
    print("=" * 80)

    env = get_default_environment()
    print(f"Target Repo: {env.target_repo_root} (Commit: {env.target_repo_commit})")
    print(f"Run ID: {env.run_id}")

    # Load selected ranker config first (Issue 47)
    selected_ranker_path = env.results_root / "selected_ranker_config.json"
    if not selected_ranker_path.exists():
        raise FileNotFoundError(
            f"Missing selected_ranker_config.json at {selected_ranker_path}. "
            "Retrieval suite must execute before evaluating determinism."
        )

    sel_data = json.loads(selected_ranker_path.read_text(encoding="utf-8"))
    selected_config_name = sel_data.get("selected_configuration")
    if not selected_config_name:
        raise ValueError("selected_ranker_config.json missing 'selected_configuration' field")

    # Hash the full serialized configuration parameters (Issue 47)
    selected_config_hash = hashlib.sha256(
        json.dumps(sel_data, sort_keys=True).encode("utf-8")
    ).hexdigest()
    print(f"Selected Ranker Configuration: '{selected_config_name}' (Config Hash: {selected_config_hash[:16]}...)")

    # Load canonical graph
    print("Loading canonical graph...")
    t0 = time.time()
    with open(env.graph_path, "r", encoding="utf-8") as f:
        raw_graph = json.load(f)
    cg = CanonicalGraph.from_legacy_dict(raw_graph, target_repo_root=env.target_repo_root)
    total_edges = sum(len(edges) for edges in cg.outgoing_edges.values())
    print(f"Graph loaded: {len(cg.nodes)} nodes, {total_edges} edges in {time.time()-t0:.2f}s")

    # Select representative tasks (1 DEV, 1 VAL, 1 TEST)
    with open(env.ground_truth_root / "ground_truth.json", "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    task_dict = gt_data["tasks"] if isinstance(gt_data["tasks"], dict) else {t["task_id"]: t for t in gt_data["tasks"]}
    rep_task_ids = ["TASK-DEV-01", "TASK-VAL-01", "TASK-TEST-01"]
    rep_tasks = [task_dict[tid] for tid in rep_task_ids if tid in task_dict]

    results_per_task = []
    all_tasks_deterministic = True

    for task in rep_tasks:
        tid = task["task_id"]
        req_sym = task.get("target_symbol") or task.get("requested_symbol", "")
        print(f"\n--- Evaluating Determinism for Task {tid} ({req_sym}) with Selected Ranker '{selected_config_name}' ---")

        candidate_order_hashes = []
        ranked_output_hashes = []
        plan_hashes = []
        prompt_hashes = []
        trial_records = []

        for trial in range(1, N_TRIALS + 1):
            out = run_single_task_pipeline(tid, env, cg, selected_config_name)
            candidate_order_hashes.append(out["candidate_hash"])
            ranked_output_hashes.append(out["ranked_hash"])
            plan_hashes.append(out["plan_hash"])
            prompt_hashes.append(out["prompt_hash"])
            trial_records.append({
                "trial": trial,
                "candidate_hash": out["candidate_hash"],
                "ranked_hash": out["ranked_hash"],
                "plan_hash": out["plan_hash"],
                "prompt_hash": out["prompt_hash"],
                "total_tokens": out["total_tokens"],
            })
            print(f"  Trial {trial}: Tokens={out['total_tokens']}, Prompt Hash={out['prompt_hash'][:12]}...")

        # Check in-process determinism for this task
        task_c_det = len(set(candidate_order_hashes)) == 1
        task_r_det = len(set(ranked_output_hashes)) == 1
        task_pl_det = len(set(plan_hashes)) == 1
        task_pr_det = len(set(prompt_hashes)) == 1

        is_task_det = task_c_det and task_r_det and task_pl_det and task_pr_det
        if not is_task_det:
            all_tasks_deterministic = False

        results_per_task.append({
            "task_id": tid,
            "target_symbol": req_sym,
            "selected_config": selected_config_name,
            "is_deterministic": is_task_det,
            "candidates_deterministic": task_c_det,
            "ranking_deterministic": task_r_det,
            "planning_deterministic": task_pl_det,
            "prompt_deterministic": task_pr_det,
            "candidate_hash": candidate_order_hashes[0],
            "ranked_hash": ranked_output_hashes[0],
            "plan_hash": plan_hashes[0],
            "prompt_hash": prompt_hashes[0],
            "trials": trial_records,
        })

    # Process-level hash seed verification across multiple separate Python invocations
    print("\n--- Verifying Process-Level PYTHONHASHSEED Invariance across Independent Python Processes ---")
    import os
    import subprocess
    hashseed_results = {}
    seeds_to_test = ["0", "42", "1337"]
    test_task_id = "TASK-TEST-01"

    for seed in seeds_to_test:
        sub_env = dict(os.environ)
        sub_env["PYTHONHASHSEED"] = seed
        cmd = [
            sys.executable,
            "-c",
            f"""
import sys, json
sys.path.insert(0, r"{SCRIPT_DIR}")
from evaluate_determinism import run_single_task_pipeline, get_default_environment
from rcir.graph.canonical_graph import CanonicalGraph
env = get_default_environment()
with open(env.graph_path, "r", encoding="utf-8") as f:
    raw_graph = json.load(f)
cg = CanonicalGraph.from_legacy_dict(raw_graph, target_repo_root=env.target_repo_root)
out = run_single_task_pipeline("{test_task_id}", env, cg, "{selected_config_name}")
print("SEED_OUTPUT:" + json.dumps(out))
""",
        ]
        proc = subprocess.run(cmd, env=sub_env, capture_output=True, text=True)
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if line.startswith("SEED_OUTPUT:"):
                    hashseed_results[seed] = json.loads(line.split("SEED_OUTPUT:", 1)[1])
                    break
        else:
            print(f"  Warning: Subprocess for seed {seed} exited with code {proc.returncode}: {proc.stderr[:100]}")

    process_level_det = False
    process_level_hashseed_status = "NOT_MEASURED"
    process_level_det = False
    if len(hashseed_results) == len(seeds_to_test):
        prompt_hashes_across_seeds = [r["prompt_hash"] for r in hashseed_results.values()]
        cand_hashes_across_seeds = [r["candidate_hash"] for r in hashseed_results.values()]
        ranked_hashes_across_seeds = [r["ranked_hash"] for r in hashseed_results.values()]
        process_level_det = (
            len(set(prompt_hashes_across_seeds)) == 1
            and len(set(cand_hashes_across_seeds)) == 1
            and len(set(ranked_hashes_across_seeds)) == 1
        )
        process_level_hashseed_status = "PASSED" if process_level_det else "FAILED"
        print(f"Process-level PYTHONHASHSEED match: {process_level_det} (Tested seeds: {seeds_to_test})")
    else:
        # Issue 46: Do NOT convert subprocess failure into a silent pass
        process_level_det = False
        process_level_hashseed_status = "NOT_MEASURED"
        print("Subprocess execution constrained; reporting process_level_hashseed_status = 'NOT_MEASURED'")

    overall_deterministic = all_tasks_deterministic and (process_level_hashseed_status == "PASSED")

    env.derive_run_id()
    from provenance import build_provenance_envelope
    envelope = build_provenance_envelope(env)

    eval_result = {
        **envelope,
        "validation_status": "MEASURED_DETERMINISM",
        "selected_ranker_config": selected_config_name,
        "selected_ranker_config_hash": selected_config_hash,
        "trials_per_task": N_TRIALS,
        "tasks_evaluated": len(results_per_task),
        "is_deterministic": overall_deterministic,
        "process_level_hashseed_verified": process_level_det,
        "process_level_hashseed_status": process_level_hashseed_status,
        "pipeline_stages_verified": [
            "candidate_discovery",
            "multi_objective_ranking",
            "context_planning",
            "context_compilation_and_rendering",
        ],
        "tasks": results_per_task,
    }

    out_file = env.results_root / "determinism_evaluation.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(eval_result, f, indent=2)

    status_str = "PASSED (100% Bitwise Identity)" if overall_deterministic else "FAILED (Variance Detected)"
    print(f"\n================================================================================")
    print(f"Overall Determinism Result: {status_str}")
    print(f"Saved evaluation to: {out_file}")
    print(f"================================================================================")


if __name__ == "__main__":
    evaluate_determinism()

