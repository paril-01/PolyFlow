"""
Export Nextcloud AST Graph and Hierarchy into visualizer-react public data.
Creates public/data/nextcloud.json and registers nextcloud as #1 in manifest.json.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))

from rcir.hierarchy.builder import build_hierarchy

GRAPH_PATH = REPO_ROOT / "experiments" / "nextcloud_validation" / "rcir" / "nextcloud_graph.json"
REACT_DATA_DIR = REPO_ROOT / "rcir" / "visualizer-react" / "public" / "data"
MANIFEST_PATH = REACT_DATA_DIR / "manifest.json"
OUT_JSON = REACT_DATA_DIR / "nextcloud.json"


def main():
    print(f"Loading Nextcloud graph from: {GRAPH_PATH}")
    if not GRAPH_PATH.exists():
        print(f"Error: {GRAPH_PATH} not found!")
        sys.exit(1)

    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        full_graph = json.load(f)

    nodes = full_graph.get("nodes", [])
    edges = full_graph.get("edges", [])
    print(f"Total graph: {len(nodes):,} nodes, {len(edges):,} edges")

    # Build full hierarchy
    print("Building full AST hierarchy...")
    hierarchy = build_hierarchy(full_graph)

    # For browser canvas performance and readability (avoiding 50k-node clutter),
    # select architectural nodes (classes, interfaces, routes, controllers, and key entrypoints)
    # while preserving complete connectivity.
    print("Filtering visualizer node set for optimal canvas responsiveness...")
    arch_kinds = {"class", "interface", "trait", "proto_service", "service", "file"}
    # Include all classes, services, files, and high-impact methods from evaluated tasks
    priority_symbols = {"ApiController", "Node", "getId", "NodeDeletedEvent", "IConfig", "Recent", "getThumbnail", "getRecentSearch"}
    
    selected_nodes = []
    selected_paths = set()

    for n in nodes:
        p = n.get("path", "")
        kind = n.get("kind", "")
        level = n.get("level", "")
        
        is_priority = any(sym in p for sym in priority_symbols)
        is_arch = kind in arch_kinds or level in ("root", "module", "file", "class")
        
        # Keep priority symbols and architectural components
        if is_priority or (is_arch and ("apps/files" in p or "lib/public" in p or "apps/dav" in p or "lib/private" in p)):
            selected_nodes.append(n)
            selected_paths.add(p)

    # If count is small, widen to include more classes
    if len(selected_nodes) < 500:
        for n in nodes:
            p = n.get("path", "")
            if n.get("kind") == "class" and p not in selected_paths:
                selected_nodes.append(n)
                selected_paths.add(p)
                if len(selected_nodes) >= 1500:
                    break

    print(f"Selected {len(selected_nodes):,} visualizer nodes from {len(nodes):,} full nodes")

    # Filter edges connecting selected nodes
    selected_edges = []
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        # Match if source and target paths or base symbols are in selected_paths
        src_base = src.split("::")[0] if "::" in src else src
        tgt_base = tgt.split("::")[0] if "::" in tgt else tgt
        if src in selected_paths or src_base in selected_paths or tgt in selected_paths or tgt_base in selected_paths:
            selected_edges.append(e)

    print(f"Selected {len(selected_edges):,} visualizer edges from {len(edges):,} full edges")

    # Ensure all hierarchy nodes have parent populated for TreeExplorer
    h_nodes = hierarchy.get("nodes", [])
    for n in h_nodes:
        if "parent" not in n:
            ancestors = n.get("ancestors", [])
            n["parent"] = ancestors[0] if ancestors else None

    # Filter hierarchy nodes to modules, files, and classes for snappy tree explorer
    tree_nodes = [n for n in h_nodes if n.get("level") in ("root", "module", "file", "class")][:5000]

    payload = {
        "id": "nextcloud",
        "name": "Nextcloud Server Core",
        "source_path": "experiments/nextcloud_validation/nextcloud-server",
        "total_repository_nodes": len(nodes),
        "total_repository_edges": len(edges),
        "graph": {
            "nodes": selected_nodes,
            "edges": selected_edges[:4000],  # Bound to 4000 top edges for smooth 60fps canvas
        },
        "hierarchy": {
            "nodes": tree_nodes,
            "root": ".",
            "hub_scores": hierarchy.get("hub_scores", {}),
            "total_nodes": len(tree_nodes),
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    print(f"[OK] Wrote visualizer payload to: {OUT_JSON} ({OUT_JSON.stat().st_size / (1024*1024):.2f} MB)")

    # Update manifest.json
    manifest = []
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            manifest = []

    # Remove existing nextcloud if any
    manifest = [m for m in manifest if m.get("id") != "nextcloud"]

    # Insert nextcloud as #1
    nextcloud_entry = {
        "id": "nextcloud",
        "name": "Nextcloud Server Core",
        "path": "/data/nextcloud.json",
        "nodes": len(nodes),
        "edges": len(edges),
        "visual_nodes": len(selected_nodes),
        "visual_edges": len(selected_edges[:4000]),
        "hierarchy_nodes": len(nodes),
        "description": "Nextcloud Server Core (11,793 files, 926,080 LOC, 33 apps)",
    }
    manifest.insert(0, nextcloud_entry)

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[OK] Updated manifest at: {MANIFEST_PATH} with nextcloud as primary default.")


if __name__ == "__main__":
    main()
