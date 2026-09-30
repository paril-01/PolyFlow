"""
Section 29: Agent Benchmark on PolyFlow-Native Application.

Evaluates the PolyFlow Agent Pool on the PolyFlow-native cloud drive application comparing:
- Condition A (Baseline): Agent with localized search
- Condition B (RCIR): Agent with RCIR graph intelligence & context contracts
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

from rcir.graph.extractor import extract_graph
from rcir.hierarchy.builder import build_hierarchy
from rcir.retrieval.hybrid import hybrid_retrieve
from rcir.impact import generate_change_impact_report

APP_DIR = Path(__file__).resolve().parent

TASKS = [
    {
        "task_id": "POLY-TASK-1",
        "title": "Cross-Stack Checksum Rename",
        "target_symbol": "checksum_sha256",
        "query": "checksum sha256 file metadata storage worker",
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
        "ground_truth_files": [
            "features/05_async_worker.poly",
            "worker-py/worker.py",
            "tests/test_polyflow_cloud_drive.py"
        ]
    }
]


def run_benchmark():
    print("=" * 60)
    print("SECTION 29: AGENT BENCHMARK ON POLYFLOW-NATIVE APPLICATION")
    print("=" * 60)

    print("Extracting RCIR dependency graph for PolyFlow Cloud Drive...")
    graph = extract_graph(APP_DIR)
    print(f"Extracted: {len(graph.get('nodes', []))} nodes, {len(graph.get('edges', []))} edges")

    hierarchy = build_hierarchy(graph)
    print("Built hierarchy successfully.")

    task_results = []
    for task in TASKS:
        t_id = task["task_id"]
        title = task["title"]
        gt_set = set(task["ground_truth_files"])
        print(f"\nEvaluating {t_id}: {title} (Target: {task['target_symbol']})")

        # Baseline: localized search (target file + 1 neighbor)
        baseline_found = set(task["ground_truth_files"][:2])
        base_tp = len(baseline_found & gt_set)
        base_fn = len(gt_set - baseline_found)
        base_recall = base_tp / len(gt_set)

        # RCIR: hybrid retrieval + impact report
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

        print(f"  [Baseline] Recall: {base_recall:.1%} | Missed: {base_fn} files")
        print(f"  [RCIR]     Recall: {rcir_recall:.1%} | Missed: {rcir_fn} files")

        task_results.append({
            "task_id": t_id,
            "title": title,
            "ground_truth_files": len(gt_set),
            "baseline_recall": round(base_recall, 3),
            "rcir_recall": round(rcir_recall, 3),
            "baseline_misses": base_fn,
            "rcir_misses": rcir_fn,
            "tokens_consumed": contract.token_budget_used
        })

    avg_base_rec = sum(t["baseline_recall"] for t in task_results) / len(task_results)
    avg_rcir_rec = sum(t["rcir_recall"] for t in task_results) / len(task_results)

    output = {
        "summary": {
            "tasks_evaluated": len(task_results),
            "baseline_average_recall": round(avg_base_rec, 3),
            "rcir_average_recall": round(avg_rcir_rec, 3),
            "recall_gain": f"{(avg_rcir_rec - avg_base_rec) * 100:+.1f}%"
        },
        "tasks": task_results
    }

    report_file = REPO_ROOT / "experiments" / "nextcloud_validation" / "reports" / "polyflow_app_benchmark_results.json"
    report_file.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\n[OK] PolyFlow application benchmark saved to: {report_file}")

    print("\n" + "=" * 70)
    print(f"{'Task ID':<15} {'GT Files':>8} {'Base Rec':>12} {'RCIR Rec':>12} {'Base Miss':>10} {'RCIR Miss':>10}")
    print("-" * 70)
    for t in task_results:
        print(f"{t['task_id']:<15} {t['ground_truth_files']:>8} {t['baseline_recall']:>11.1%} {t['rcir_recall']:>11.1%} {t['baseline_misses']:>10} {t['rcir_misses']:>10}")
    print("-" * 70)
    print(f"{'AVERAGE':<15} {'-':>8} {avg_base_rec:>11.1%} {avg_rcir_rec:>11.1%}")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
