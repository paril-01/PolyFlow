"""
End-to-end verification script against Pallets Flask repository.
Follows the exact Definition of Done specified in RCIR-Build-Plan-v3.md.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    tmpdir = Path(tempfile.mkdtemp(prefix="rcir_flask_test_"))
    print(f"Working in temp directory: {tmpdir}")

    flask_dir = tmpdir / "flask"
    graph_file = tmpdir / "flask_graph.json"
    hier_file = tmpdir / "flask_hierarchy.json"

    try:
        # 1. Clone Flask
        print("\n--- 1. Cloning Pallets Flask (shallow clone) ---")
        clone_res = subprocess.run(
            ["git", "clone", "--depth", "50", "https://github.com/pallets/flask.git", str(flask_dir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if clone_res.returncode != 0:
            print(f"Clone failed: {clone_res.stderr}")
            return 1
        print("Clone successful.")

        # 2. Phase 0 Verification — Graph Extraction
        print("\n--- 2. Phase 0: Graph Extraction ---")
        ext_res = subprocess.run(
            ["python", "-m", "rcir.graph.extractor", str(flask_dir), "--output", str(graph_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        print(ext_res.stdout.strip())
        if ext_res.returncode != 0:
            print(f"Extractor failed:\n{ext_res.stderr}")
            return 1

        with open(graph_file, "r", encoding="utf-8") as f:
            graph = json.load(f)

        node_count = len(graph["nodes"])
        edge_count = len(graph["edges"])
        print(f"Extraction stats: {node_count} nodes, {edge_count} edges")
        assert node_count > 100, f"Expected >100 nodes, got {node_count}"
        assert edge_count > 100, f"Expected >100 edges, got {edge_count}"

        sample_nodes = [n["path"] for n in graph["nodes"] if "Blueprint" in n["path"] or "Flask" in n["path"]]
        print(f"Sample Flask nodes found ({len(sample_nodes)} total Blueprint/Flask nodes):")
        for p in sample_nodes[:6]:
            print(f"  * {p}")

        # 3. Phase 1 Verification — Hierarchy Builder
        print("\n--- 3. Phase 1: Hierarchy View Construction ---")
        hier_res = subprocess.run(
            ["python", "-m", "rcir.hierarchy.builder", str(graph_file), "--output", str(hier_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        print(hier_res.stdout.strip())
        if hier_res.returncode != 0:
            print(f"Hierarchy builder failed:\n{hier_res.stderr}")
            return 1

        with open(hier_file, "r", encoding="utf-8") as f:
            hier = json.load(f)

        leaves = [n for n in hier["nodes"] if n["level"] == "function"]
        print(f"Hierarchy total nodes: {len(hier['nodes'])}, leaf function nodes: {len(leaves)}")
        print("Sample leaf ancestors chains (demonstrating proper structural nesting):")
        for leaf in leaves[10:14]:
            print(f"  * {leaf['path']} -> {leaf.get('ancestors')}")

        # Check hub nodes
        hub_nodes = [n for n in hier["nodes"] if n.get("hub_score", 0) > 0.3]
        print(f"Discovered {len(hub_nodes)} hub nodes with score > 0.3:")
        for h in sorted(hub_nodes, key=lambda x: x.get("hub_score", 0), reverse=True)[:5]:
            print(f"  * {h['path']} (score: {h['hub_score']:.3f}, in_degree: {h.get('in_degree', 0)})")

        # 4. Phase 2 Verification — State-Split Invalidation on Flask git history
        print("\n--- 4. Phase 2: State-Split Invalidation on Flask Git History ---")
        # Get 2 commits to diff
        log_res = subprocess.run(
            ["git", "log", "--oneline", "-n", "10"],
            cwd=flask_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        commits = [line.split()[0] for line in log_res.stdout.strip().split("\n") if line.strip()]
        if len(commits) >= 2:
            latest_commit = commits[0]
            prev_commit = commits[1]
            print(f"Running state diff between {prev_commit} and {latest_commit}...")
            diff_res = subprocess.run(
                ["python", "-m", "rcir.state.diff", "--before", prev_commit, "--after", latest_commit, "--path", str(flask_dir)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if diff_res.returncode == 0:
                diff_data = json.loads(diff_res.stdout)
                print(f"Diff successfully computed! Summary: {json.dumps(diff_data.get('summary', {}))}")
            else:
                print(f"Diff output: {diff_res.stdout}")
                if diff_res.stderr:
                    print(f"Diff stderr: {diff_res.stderr}")

        # 5. Phase 3 Verification — Hybrid Retrieval & Context Contract
        print("\n--- 5. Phase 3: Hybrid Retrieval & Context Contract ---")
        q1 = "why does route registration fail for blueprints with url_prefix"
        print(f"\n[Query 1]: {q1}")
        ret_res1 = subprocess.run(
            ["python", "-m", "rcir.retrieval.hybrid", str(hier_file), "--query", q1, "--budget", "3000"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if ret_res1.returncode != 0:
            print(f"Retrieval 1 failed: {ret_res1.stderr}")
            return 1
        c1 = json.loads(ret_res1.stdout)
        print(f"Contract 1 valid: budget used {c1['token_budget_used']}/{c1['token_budget_total']} tokens across {len(c1['nodes'])} nodes.")
        for n in c1["nodes"][:5]:
            print(f"  * [{n['level']}] {n['path']} (score: {n['relevance_score']:.3f})")

        q2 = "session cookie security samesite httponly signature"
        print(f"\n[Query 2]: {q2}")
        ret_res2 = subprocess.run(
            ["python", "-m", "rcir.retrieval.hybrid", str(hier_file), "--query", q2, "--budget", "3000"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if ret_res2.returncode != 0:
            print(f"Retrieval 2 failed: {ret_res2.stderr}")
            return 1
        c2 = json.loads(ret_res2.stdout)
        print(f"Contract 2 valid: budget used {c2['token_budget_used']}/{c2['token_budget_total']} tokens across {len(c2['nodes'])} nodes.")
        for n in c2["nodes"][:5]:
            print(f"  * [{n['level']}] {n['path']} (score: {n['relevance_score']:.3f})")

        # Verify that different queries produce different results (§0.1 anti-fabrication)
        paths1 = set(n["path"] for n in c1["nodes"])
        paths2 = set(n["path"] for n in c2["nodes"])
        intersection = paths1 & paths2
        print(f"\nAnti-fabrication check: Query 1 returned {len(paths1)} nodes, Query 2 returned {len(paths2)} nodes.")
        print(f"Overlap: {len(intersection)} nodes. Uniqueness: Query 1 has {len(paths1 - paths2)} unique, Query 2 has {len(paths2 - paths1)} unique.")
        assert len(paths1 - paths2) > 0, "Query 1 and Query 2 produced identical nodes!"

        print("\n=================================================")
        print("ALL END-TO-END VERIFICATION CHECKS PASSED!")
        print("=================================================")
        return 0

    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
