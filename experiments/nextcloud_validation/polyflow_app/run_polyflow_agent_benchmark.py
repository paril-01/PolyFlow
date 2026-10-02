"""
Section 29: Agent Benchmark on PolyFlow-Native Experimental Prototype.

Evaluates the PolyFlow Agent Pool and dependency retrieval on the experimental
PolyFlow-native cloud drive application prototype (comprising Java backend, Python workers,
TypeScript frontend types, and .poly polyglot contract cells).

Evaluates:
- Part 1: Algorithmic Discovery Comparison (Genuine baseline keyword/proximity scan vs RCIR Graph Contract)
- Part 2: Real Multi-Agent Pipeline Execution (Maker -> Reviewer -> Implementer -> Gatekeeper)
  using OrchestratorRunner and real local LLM inference.
"""

import json
import math
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))
sys.path.insert(0, str(REPO_ROOT))

from rcir.graph.extractor import extract_graph
from rcir.hierarchy.builder import build_hierarchy
from rcir.retrieval.hybrid import hybrid_retrieve
from rcir.impact import generate_change_impact_report
from orchestrator.runner import OrchestratorRunner

APP_DIR = Path(__file__).resolve().parent

TASKS = [
    {
        "task_id": "POLY-TASK-1",
        "title": "Cross-Stack Checksum Rename",
        "target_symbol": "checksum_sha256",
        "query": "checksum sha256 file metadata storage worker",
        "description": "Refactor checksum_sha256 to content_hash_sha256 across Python worker, TypeScript types, and .poly contract.",
        "ground_truth_files": [
            "features/02_file_storage.poly",
            "frontend-ts/src/types/storage.ts",
            "worker-py/db_migrations.py",
            "worker-py/worker.py",
            "tests/test_polyflow_cloud_drive.py"
        ]
    },
    {
        "task_id": "POLY-TASK-2",
        "title": "Permission Capability Action Refactoring",
        "target_symbol": "PermissionChecker",
        "query": "PermissionChecker hasAccess userRole grantPermission",
        "description": "Refactor PermissionChecker.hasAccess method to support hierarchical role inheritance in Java and .poly.",
        "ground_truth_files": [
            "features/04_sharing_permissions.poly",
            "backend-java/src/main/java/polyflow/storage/PermissionChecker.java",
            "backend-java/src/main/java/polyflow/storage/StorageService.java",
            "backend-java/src/main/java/polyflow/storage/TestStorageSuite.java"
        ]
    },
    {
        "task_id": "POLY-TASK-3",
        "title": "Thumbnail Metadata Contract Evolution",
        "target_symbol": "thumbnail_ref",
        "query": "thumbnail ref process file metadata async task",
        "description": "Evolve thumbnail_ref schema to support multi-resolution thumbnail dictionaries in worker and async contract.",
        "ground_truth_files": [
            "features/05_async_worker.poly",
            "worker-py/worker.py",
            "tests/test_polyflow_cloud_drive.py"
        ]
    }
]


def genuine_baseline_file_search(app_dir: Path, target_symbol: str, query: str) -> set[str]:
    """Genuine baseline file search: scans project files for symbol occurrences and keywords."""
    found = set()
    terms = [target_symbol] + query.split()[:2]
    regexes = [re.compile(re.escape(t), re.IGNORECASE) for t in terms if len(t) > 3]

    for root, _, files in os.walk(app_dir):
        if any(skip in root for skip in [".git", "__pycache__", "build", "target"]):
            continue
        for f in files:
            if f.endswith((".poly", ".py", ".ts", ".java", ".json")):
                fp = Path(root) / f
                try:
                    content = fp.read_text(encoding="utf-8", errors="ignore")
                    # If target symbol or top terms appear in file
                    if any(r.search(content) for r in regexes):
                        rel = fp.relative_to(app_dir).as_posix()
                        found.add(rel)
                except Exception:
                    pass
    return found


def run_benchmark():
    print("=" * 70)
    print("SECTION 29: AGENT BENCHMARK ON POLYFLOW-NATIVE EXPERIMENTAL PROTOTYPE")
    print("=" * 70)
    print("Note: PolyFlow Cloud Drive is an experimental multi-language prototype")
    print("(Java backend, Python workers, TypeScript frontend types, .poly contracts).")

    print("\nExtracting RCIR dependency graph for PolyFlow Cloud Drive...")
    graph = extract_graph(APP_DIR)
    print(f"Extracted: {len(graph.get('nodes', []))} nodes, {len(graph.get('edges', []))} edges")

    hierarchy = build_hierarchy(graph)
    print("Built hierarchy successfully.")

    task_results = []
    agent_executions = []

    print("\n" + "=" * 70)
    print("PART 1: ALGORITHMIC CONTEXT RETRIEVAL EVALUATION")
    print("=" * 70)

    for task in TASKS:
        t_id = task["task_id"]
        title = task["title"]
        gt_set = set(task["ground_truth_files"])
        print(f"\nEvaluating {t_id}: {title} (Target: {task['target_symbol']})")

        # Genuine Baseline Search (Symbol + keyword scanning)
        baseline_found = genuine_baseline_file_search(APP_DIR, task["target_symbol"], task["query"])
        base_tp = len(baseline_found & gt_set)
        base_fn = len(gt_set - baseline_found)
        base_recall = base_tp / len(gt_set) if gt_set else 1.0

        # RCIR Retrieval (Graph contract + change impact report)
        contract = hybrid_retrieve(hierarchy, task["query"], token_budget=2000, graph_edges=graph.get("edges", []))
        impact = generate_change_impact_report(repo_path=APP_DIR, target_symbol=task["target_symbol"], graph=graph)

        rcir_files = set()
        for n in contract.nodes:
            p = n.path.replace("\\", "/").split("::")[0].strip("/")
            for gf in gt_set:
                if gf in p or p.endswith(gf):
                    rcir_files.add(gf)
        for e in impact.affected_edges:
            s = e.get("source", "").replace("\\", "/").split("::")[0].strip("/")
            for gf in gt_set:
                if gf in s or s.endswith(gf):
                    rcir_files.add(gf)

        rcir_tp = len(rcir_files & gt_set)
        rcir_fn = len(gt_set - rcir_files)
        rcir_recall = rcir_tp / len(gt_set) if gt_set else 1.0

        print(f"  [Baseline Search] Recall: {base_recall:.1%} | Identified: {base_tp}/{len(gt_set)} | Missed: {base_fn} files")
        print(f"  [RCIR Graph]     Recall: {rcir_recall:.1%} | Identified: {rcir_tp}/{len(gt_set)} | Missed: {rcir_fn} files")
        print(f"  Exact Resolution Fraction: {impact.exact_resolution_fraction:.1%} ({impact.exact_call_sites} exact, {impact.inferred_call_sites} inferred)")

        task_results.append({
            "task_id": t_id,
            "title": title,
            "ground_truth_files": len(gt_set),
            "baseline_recall": round(base_recall, 3),
            "rcir_recall": round(rcir_recall, 3),
            "baseline_misses": base_fn,
            "rcir_misses": rcir_fn,
            "exact_resolution_fraction": round(impact.exact_resolution_fraction, 4),
            "tokens_consumed": contract.token_budget_used
        })

    print("\n" + "=" * 70)
    print("PART 2: REAL MULTI-AGENT PIPELINE EXECUTION (AEF AGENT POOL)")
    print("=" * 70)
    print("Running Maker -> Reviewer -> Implementer -> Gatekeeper via OrchestratorRunner...")

    # Run real agent pipeline on POLY-TASK-1
    task_eval = TASKS[0]
    runner = OrchestratorRunner()
    user_prompt = (
        f"Task: {task_eval['task_id']} - {task_eval['title']}\n"
        f"Target: {task_eval['target_symbol']}\n"
        f"Requirement: {task_eval['description']}\n"
        "PolyFlow Contracts: features/02_file_storage.poly, worker-py/worker.py\n"
        "Verify cross-stack synchronization between Python worker and TypeScript definitions."
    )
    t0 = time.perf_counter()
    pipeline_res = runner.run_pipeline(user_request=user_prompt, verbose=False)
    agent_duration = time.perf_counter() - t0

    gatekeeper_text = pipeline_res.get("stage5_gatekeeper", "")
    decision = "APPROVE" if "APPROVE" in gatekeeper_text.upper() and "REJECT" not in gatekeeper_text.upper() else "CONDITIONAL_OR_HOLD"

    agent_executions.append({
        "task_id": task_eval["task_id"],
        "title": task_eval["title"],
        "duration_seconds": round(agent_duration, 2),
        "total_llm_tokens": pipeline_res.get("total_tokens_consumed", 0),
        "gatekeeper_decision": decision,
        "maker_summary": pipeline_res.get("stage1_maker", "")[:250].replace("\n", " "),
        "gatekeeper_summary": gatekeeper_text[:250].replace("\n", " "),
    })

    print(f"Agent Execution Finished in {agent_duration:.2f}s | LLM Tokens: {pipeline_res.get('total_tokens_consumed', 0)} | Gatekeeper: {decision}")

    avg_base_rec = sum(t["baseline_recall"] for t in task_results) / len(task_results)
    avg_rcir_rec = sum(t["rcir_recall"] for t in task_results) / len(task_results)

    output = {
        "summary": {
            "application_description": "PolyFlow Cloud Drive Experimental Polyglot Prototype (Java, Python, TypeScript, .poly)",
            "tasks_evaluated": len(task_results),
            "baseline_average_recall": round(avg_base_rec, 3),
            "rcir_average_recall": round(avg_rcir_rec, 3),
            "observed_recall_gain_points": round((avg_rcir_rec - avg_base_rec) * 100, 1),
            "methodology_note": "Genuine file content search vs RCIR graph contract. Real AEF pipeline executed with local LLM.",
        },
        "tasks": task_results,
        "agent_executions": agent_executions
    }

    report_file = REPO_ROOT / "experiments" / "nextcloud_validation" / "reports" / "polyflow_app_benchmark_results.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\n[OK] PolyFlow application benchmark saved to: {report_file}")

    print("\n" + "=" * 80)
    print(f"{'Task ID':<15} {'GT Files':>8} {'Base Rec':>12} {'RCIR Rec':>12} {'Base Miss':>10} {'RCIR Miss':>10} {'Exact Res Frac':>16}")
    print("-" * 80)
    for t in task_results:
        print(f"{t['task_id']:<15} {t['ground_truth_files']:>8} {t['baseline_recall']:>11.1%} {t['rcir_recall']:>11.1%} {t['baseline_misses']:>10} {t['rcir_misses']:>10} {t['exact_resolution_fraction']:>15.1%}")
    print("-" * 80)
    print(f"{'AVERAGE':<15} {'-':>8} {avg_base_rec:>11.1%} {avg_rcir_rec:>11.1%} {'-':>10} {'-':>10} {'-':>16}")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()
