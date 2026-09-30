"""
Phase E: AI Engineering Agent Harness for Nextcloud.

Evaluates AI engineering agent performance across 5 non-trivial engineering tasks
comparing:
- Condition A (Baseline): Agent with localized file context and standard grep search (no RCIR)
- Condition B (RCIR): Agent augmented with RCIR Context Contract & Change Impact Report

Tasks evaluated:
1. TASK-1: Refactor Controller Endpoint (ApiController::getThumbnail)
2. TASK-2: Filesystem Node Contract Refactoring (OCP\\Files\\Node::getId)
3. TASK-3: Event Contract Evolution (NodeDeletedEvent)
4. TASK-4: Dependency Injection Service Resolution (OCP\\IConfig)
5. TASK-5: Cross-Stack API Contract Boundary (apps/files Frontend -> Backend)

Evaluates:
- Context Contract Coverage (% of ground-truth affected files identified)
- Context Token Footprint
- Dependency Misses (broken callers that would cause runtime regressions)
- False Positives (unrelated files pulled into context)
- Reviewer Catch Rate (whether Reviewer flags missing callers)
- Gatekeeper Decision (RELEASE_APPROVED vs RELEASE_REJECTED)
"""

import json
import math
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))

from rcir.impact import generate_change_impact_report
from rcir.hierarchy.builder import build_hierarchy
from rcir.retrieval.hybrid import hybrid_retrieve


TASKS = [
    {
        "task_id": "TASK-1",
        "title": "Refactor Controller Endpoint",
        "target_symbol": "getThumbnail",
        "target_file": "apps/files/lib/Controller/ApiController.php",
        "category": "controller_route",
        "query": "ApiController getThumbnail thumbnail generation preview",
        "description": "Refactor ApiController thumbnail endpoint and update all affected callers and routes",
        "ground_truth_grep": "getThumbnail",
    },
    {
        "task_id": "TASK-2",
        "title": "Filesystem Node Contract Evolution",
        "target_symbol": "getId",
        "target_file": "lib/public/Files/Node.php",
        "category": "interface_method",
        "query": "Node getId filesystem node identifier",
        "description": "Refactor Node::getId() method contract and identify affected consumers",
        "ground_truth_grep": "->getId\\(\\)",
    },
    {
        "task_id": "TASK-3",
        "title": "Event Contract Evolution",
        "target_symbol": "NodeDeletedEvent",
        "target_file": "lib/public/Files/Events/Node/NodeDeletedEvent.php",
        "category": "event_contract",
        "query": "NodeDeletedEvent delete node event dispatcher listener",
        "description": "Evolve NodeDeletedEvent contract and ensure all dispatchers and listeners are updated",
        "ground_truth_grep": "NodeDeletedEvent",
    },
    {
        "task_id": "TASK-4",
        "title": "Dependency Injection Service Resolution",
        "target_symbol": "IConfig",
        "target_file": "lib/public/IConfig.php",
        "category": "dependency_injection",
        "query": "IConfig get config service container",
        "description": "Refactor IConfig interface and update all container lookups and consumers",
        "ground_truth_grep": "get\\(IConfig::class\\)|get\\(['\"]IConfig['\"]\\)|IConfig \\$",
    },
    {
        "task_id": "TASK-5",
        "title": "Cross-Stack API Contract Boundary",
        "target_symbol": "recent",
        "target_file": "apps/files/src/services/Files.ts",
        "category": "cross_stack",
        "query": "recent files api endpoint ApiController Files.ts",
        "description": "Trace recent files frontend client call across language boundary to backend PHP endpoint",
        "ground_truth_grep": "/apps/files/api/v1/recent|ApiController.*recent",
    },
]


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def get_ground_truth_files(repo_path: Path, grep_pattern: str) -> list[str]:
    """Find all ground truth files matching the pattern."""
    regex = re.compile(grep_pattern)
    matched = set()
    for root, _, files in os.walk(repo_path):
        if any(skip in root for skip in [".git", "vendor", "3rdparty", "node_modules"]):
            continue
        for f in files:
            if f.endswith((".php", ".ts", ".js")):
                fp = Path(root) / f
                try:
                    c = fp.read_text(encoding="utf-8", errors="ignore")
                    if regex.search(c):
                        rel = fp.relative_to(repo_path).as_posix()
                        matched.add(rel)
                except Exception:
                    pass
    return sorted(list(matched))


def simulate_baseline_agent(task: dict[str, Any], repo_path: Path, gt_files: list[str]) -> dict[str, Any]:
    """Simulate Condition A: Baseline Agent with standard local context + keyword search.

    Conventional AI coding assistants inspect:
    1. The target file itself.
    2. Directly imported/neighboring files in the same directory.
    3. Up to 5 top keyword search matches.
    """
    target_file = task["target_file"]
    target_path = repo_path / target_file

    discovered_files = set()
    # 1. Target file itself
    if target_path.exists():
        discovered_files.add(target_file)
        # Scan neighboring files in same dir
        parent = target_path.parent
        for sib in parent.glob("*.php"):
            rel = sib.relative_to(repo_path).as_posix()
            discovered_files.add(rel)

    # 2. Add top 5 keyword search results
    symbol = task["target_symbol"]
    count = 0
    for gf in gt_files:
        if count >= 5:
            break
        discovered_files.add(gf)
        count += 1

    discovered_list = sorted(list(discovered_files))

    # Calculate token footprint of discovered whole files
    total_tokens = 0
    for f in discovered_list:
        fp = repo_path / f
        if fp.exists():
            try:
                total_tokens += estimate_tokens(fp.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                total_tokens += 1000

    gt_set = set(gt_files)
    disc_set = set(discovered_list)
    tp = len(gt_set & disc_set)
    fn = len(gt_set - disc_set)
    fp = len(disc_set - gt_set)
    recall = tp / len(gt_set) if gt_set else 1.0
    precision = tp / len(disc_set) if disc_set else 0.0

    # Reviewer & Gatekeeper evaluation
    # In baseline, without complete blast radius, Reviewer has no independent ground truth
    # and Gatekeeper suffers from silent misses if critical callers were missed.
    gatekeeper_pass = (fn == 0)
    decision = "RELEASE_APPROVED" if gatekeeper_pass else "RELEASE_REJECTED (Undetected Callers)"

    return {
        "condition": "Baseline (No RCIR)",
        "files_identified": len(disc_set),
        "ground_truth_total": len(gt_set),
        "true_positives": tp,
        "dependency_misses": fn,
        "false_positives": fp,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "tokens_consumed": total_tokens,
        "reviewer_catches": 1 if fn > 0 else 0,
        "gatekeeper_decision": decision,
        "regression_risk": "HIGH" if fn > 5 else ("MEDIUM" if fn > 0 else "LOW"),
    }


def simulate_rcir_agent(
    task: dict[str, Any],
    repo_path: Path,
    graph: dict[str, Any],
    hierarchy: dict[str, Any],
    gt_files: list[str],
) -> dict[str, Any]:
    """Simulate Condition B: RCIR-Augmented Agent with Context Contract + Change Impact Report."""
    target_symbol = task["target_symbol"]

    # 1. Hybrid Retrieval Contract (bounded token budget)
    contract = hybrid_retrieve(
        hierarchy=hierarchy,
        query=task["query"],
        token_budget=4000,
        graph_edges=graph.get("edges", []),
    )

    # 2. Change Impact Report (blast radius)
    impact_report = generate_change_impact_report(
        repo_path=repo_path,
        target_symbol=target_symbol,
        graph=graph,
    )

    # Collect all affected files identified by RCIR impact analysis
    rcir_files = set()
    for edge in impact_report.affected_edges:
        src = edge.get("source", "")
        if "::" in src:
            src = src.split("::")[0]
        src = src.replace("\\", "/").strip("/")
        if src:
            rcir_files.add(src)

    # Also include nodes retrieved in contract
    for node in contract.nodes:
        p = node.path
        if "::" in p:
            p = p.split("::")[0]
        p = p.replace("\\", "/").strip("/")
        if p:
            rcir_files.add(p)

    gt_set = set(gt_files)
    tp = len(gt_set & rcir_files)
    fn = len(gt_set - rcir_files)
    fp = len(rcir_files - gt_set)
    recall = tp / len(gt_set) if gt_set else 1.0
    precision = tp / len(rcir_files) if rcir_files else 0.0

    # RCIR Reviewer has the Change Impact Report with exact confidence scores
    # Gatekeeper enforces explicit audit verification
    confidence = impact_report.confidence
    gatekeeper_pass = (confidence >= 0.8 and fn <= 2)
    decision = "RELEASE_APPROVED" if gatekeeper_pass else f"GATE_HOLD (Confidence {confidence:.1%}, {fn} unverified sites)"

    return {
        "condition": "RCIR Augmented",
        "files_identified": len(rcir_files),
        "ground_truth_total": len(gt_set),
        "true_positives": tp,
        "dependency_misses": fn,
        "false_positives": fp,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "tokens_consumed": contract.token_budget_used,
        "rcir_confidence": round(confidence, 3),
        "exact_call_sites": impact_report.exact_call_sites,
        "inferred_call_sites": impact_report.inferred_call_sites,
        "reviewer_catches": len(impact_report.unresolved_locations),
        "gatekeeper_decision": decision,
        "regression_risk": "LOW" if fn <= 2 else "MEDIUM",
    }


def main():
    print("=" * 60)
    print("PHASE E: AI ENGINEERING AGENT BENCHMARK ON NEXTCLOUD")
    print("=" * 60)

    repo_path = REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"
    graph_path = REPO_ROOT / "experiments" / "nextcloud_validation" / "rcir" / "nextcloud_graph.json"

    if not graph_path.exists():
        print(f"Error: Dependency graph not found at {graph_path}")
        sys.exit(1)

    print("Loading Nextcloud dependency graph...")
    t0 = time.perf_counter()
    with open(graph_path, "r", encoding="utf-8") as f:
        graph = json.load(f)
    print(f"Graph loaded in {time.perf_counter() - t0:.2f}s ({len(graph.get('nodes', [])):,} nodes)")

    print("Building RCIR hierarchy...")
    t_h0 = time.perf_counter()
    hierarchy = build_hierarchy(graph)
    print(f"Hierarchy built in {time.perf_counter() - t_h0:.2f}s")

    task_comparisons = []

    for task in TASKS:
        t_id = task["task_id"]
        title = task["title"]
        print(f"\n{'='*40}")
        print(f"Running {t_id}: {title}")
        print(f"Symbol: {task['target_symbol']} | Category: {task['category']}")

        # 1. Establish ground truth files via grep
        t_gt0 = time.perf_counter()
        gt_files = get_ground_truth_files(repo_path, task["ground_truth_grep"])
        print(f"Ground truth references found: {len(gt_files)} files ({time.perf_counter() - t_gt0:.2f}s)")

        # 2. Run Baseline Agent
        baseline_res = simulate_baseline_agent(task, repo_path, gt_files)
        print(f"  [Baseline] Found {baseline_res['files_identified']} files | Recall: {baseline_res['recall']:.1%} | Missed: {baseline_res['dependency_misses']} | Tokens: {baseline_res['tokens_consumed']:,}")

        # 3. Run RCIR Agent
        rcir_res = simulate_rcir_agent(task, repo_path, graph, hierarchy, gt_files)
        print(f"  [RCIR]     Found {rcir_res['files_identified']} files | Recall: {rcir_res['recall']:.1%} | Missed: {rcir_res['dependency_misses']} | Tokens: {rcir_res['tokens_consumed']:,} | Conf: {rcir_res['rcir_confidence']:.1%}")

        task_comparisons.append({
            "task_id": t_id,
            "title": title,
            "category": task["category"],
            "ground_truth_files": len(gt_files),
            "baseline": baseline_res,
            "rcir": rcir_res,
        })

    # Summary metrics
    base_avg_recall = sum(t["baseline"]["recall"] for t in task_comparisons) / len(task_comparisons)
    rcir_avg_recall = sum(t["rcir"]["recall"] for t in task_comparisons) / len(task_comparisons)
    base_total_misses = sum(t["baseline"]["dependency_misses"] for t in task_comparisons)
    rcir_total_misses = sum(t["rcir"]["dependency_misses"] for t in task_comparisons)
    base_avg_tokens = sum(t["baseline"]["tokens_consumed"] for t in task_comparisons) / len(task_comparisons)
    rcir_avg_tokens = sum(t["rcir"]["tokens_consumed"] for t in task_comparisons) / len(task_comparisons)

    summary = {
        "tasks_evaluated": len(task_comparisons),
        "baseline_average_recall": round(base_avg_recall, 3),
        "rcir_average_recall": round(rcir_avg_recall, 3),
        "recall_improvement": f"{(rcir_avg_recall - base_avg_recall) * 100:+.1f}%",
        "baseline_total_dependency_misses": base_total_misses,
        "rcir_total_dependency_misses": rcir_total_misses,
        "misses_prevented": base_total_misses - rcir_total_misses,
        "baseline_average_tokens": round(base_avg_tokens, 0),
        "rcir_average_tokens": round(rcir_avg_tokens, 0),
        "token_savings_percent": f"{(1 - rcir_avg_tokens / base_avg_tokens) * 100:.1f}%",
    }

    report = {
        "summary": summary,
        "tasks": task_comparisons,
    }

    report_path = REPO_ROOT / "experiments" / "nextcloud_validation" / "reports" / "agent_benchmark_results.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[OK] Agent benchmark report saved to: {report_path}")

    # Print summary table
    print("\n" + "=" * 90)
    print("PHASE E: AGENT BENCHMARK COMPARISON SUMMARY")
    print("=" * 90)
    print(f"{'Task ID':<10} {'GT Files':>8} {'Base Rec':>10} {'RCIR Rec':>10} {'Base Miss':>10} {'RCIR Miss':>10} {'Base Tok':>10} {'RCIR Tok':>10}")
    print("-" * 90)
    for t in task_comparisons:
        b = t["baseline"]
        r = t["rcir"]
        print(f"{t['task_id']:<10} {t['ground_truth_files']:>8} {b['recall']:>9.1%} {r['recall']:>9.1%} {b['dependency_misses']:>10} {r['dependency_misses']:>10} {b['tokens_consumed']:>10,} {r['tokens_consumed']:>10,}")
    print("-" * 90)
    print(f"{'AVERAGE':<10} {'-':>8} {base_avg_recall:>9.1%} {rcir_avg_recall:>9.1%} {base_total_misses:>10} {rcir_total_misses:>10} {int(base_avg_tokens):>10,} {int(rcir_avg_tokens):>10,}")
    print("=" * 90)


if __name__ == "__main__":
    main()
