import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))

from experiments.nextcloud_validation.scripts.agent_harness import TASKS, get_ground_truth_files, evaluate_rcir_retrieval, evaluate_baseline_retrieval
from rcir.hierarchy.builder import build_hierarchy

repo_path = Path('experiments/nextcloud_validation/nextcloud-server')
graph_path = Path('experiments/nextcloud_validation/rcir/nextcloud_graph.json')
with open(graph_path, 'r', encoding='utf-8') as f:
    graph = json.load(f)
hierarchy = build_hierarchy(graph)

print("--- EVALUATING ALL 5 TASKS ---")
for t in TASKS:
    gt = get_ground_truth_files(repo_path, t['ground_truth_grep'], t.get('semantic_filter'))
    b_res = evaluate_baseline_retrieval(t, repo_path, gt)
    r_res = evaluate_rcir_retrieval(t, repo_path, graph, hierarchy, gt)
    tid = t['task_id']
    gtn = len(gt)
    brec = b_res['recall'] * 100
    bmiss = b_res['dependency_misses']
    rrec = r_res['recall'] * 100
    rmiss = r_res['dependency_misses']
    exact = r_res['exact_resolution_fraction'] * 100
    print(f"{tid}: GT={gtn:>3} | Base={brec:>5.1f}% (miss={bmiss:>3}) | RCIR={rrec:>5.1f}% (miss={rmiss:>3}) | ExactFrac={exact:>5.1f}%")
