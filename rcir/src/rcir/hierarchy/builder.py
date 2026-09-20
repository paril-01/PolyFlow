"""
Hierarchy builder — constructs a function→file→module→root tree from the
dependency graph.

The hierarchy is a DERIVED VIEW, not a replacement for the graph (§4.2).
The graph remains the source of truth. The hierarchy provides a navigable
structure for retrieval and invalidation.

Each node gets:
- path: its qualified name from the graph
- level: 'function' | 'class' | 'file' | 'module' | 'root'
- ancestors: ordered list from leaf to root
- children: list of child node paths

Multi-parent nodes get one canonical position; graph traversal handles
the rest (§7 fallback).

CLI: python -m rcir.hierarchy.builder <graph.json> --output <hierarchy.json>
"""

import json
import sys
from pathlib import Path, PurePosixPath
from collections import defaultdict
from typing import Any

from rcir.hierarchy.hubs import compute_hub_scores
from rcir.hierarchy.granularity import detect_coarse_artifacts


def _extract_file_from_path(node_path: str) -> str:
    """Extract the file portion from a qualified path like 'dir/file.py::Class.method'."""
    if "::" in node_path:
        return node_path.split("::")[0]
    return node_path


def _extract_module_from_file(file_path: str) -> str:
    """Extract the module (directory) from a file path.

    'src/flask/app.py' → 'src/flask'
    'setup.py' → '.'
    """
    parts = PurePosixPath(file_path)
    if parts.parent == PurePosixPath("."):
        return "."
    return str(parts.parent)


def _build_module_chain(module_path: str) -> list[str]:
    """Build the chain of module ancestors.

    'src/flask/blueprints' → ['src/flask/blueprints', 'src/flask', 'src', '.']
    """
    chain = []
    current = module_path
    while current and current != ".":
        chain.append(current)
        parent = str(PurePosixPath(current).parent)
        if parent == current:
            break
        current = parent
    chain.append(".")  # root
    return chain


def build_hierarchy(graph: dict[str, Any]) -> dict[str, Any]:
    """Build a hierarchy view from a dependency graph.

    Args:
        graph: Graph dict with 'nodes' and 'edges' keys.

    Returns:
        Hierarchy dict with:
        - nodes: enriched with 'ancestors' and hierarchy 'level'
        - files: file-level nodes
        - modules: module-level nodes
        - root: the root node
        - hub_scores: per-node hub score
    """
    graph_nodes = graph.get("nodes", [])
    graph_edges = graph.get("edges", [])

    # Step 1: Group leaf nodes by file
    file_to_leaves: dict[str, list[dict]] = defaultdict(list)
    for node in graph_nodes:
        file_path = _extract_file_from_path(node["path"])
        file_to_leaves[file_path].append(node)

    # Step 2: Build file-level nodes
    file_nodes: dict[str, dict] = {}
    for file_path, leaves in file_to_leaves.items():
        file_nodes[file_path] = {
            "path": file_path,
            "kind": "file",
            "level": "file",
            "children": [leaf["path"] for leaf in leaves],
            "child_count": len(leaves),
        }

    # Step 3: Build module-level nodes (directories)
    module_to_files: dict[str, list[str]] = defaultdict(list)
    for file_path in file_nodes:
        module = _extract_module_from_file(file_path)
        module_to_files[module].append(file_path)

    module_nodes: dict[str, dict] = {}
    all_modules: set[str] = set()

    for module_path, files in module_to_files.items():
        # Build full chain of modules up to root
        chain = _build_module_chain(module_path)
        all_modules.update(chain)

        module_nodes[module_path] = {
            "path": module_path,
            "kind": "module",
            "level": "module",
            "children": sorted(files),
            "child_count": len(files),
        }

    # Ensure intermediate modules exist (e.g., 'src' if we have 'src/flask')
    for mod in sorted(all_modules):
        if mod not in module_nodes:
            # Find direct children among known modules
            children = [
                m for m in module_nodes
                if _extract_module_from_file(m + "/dummy") == mod or
                str(PurePosixPath(m).parent) == mod
            ]
            module_nodes[mod] = {
                "path": mod,
                "kind": "module",
                "level": "module" if mod != "." else "root",
                "children": sorted(children),
                "child_count": len(children),
            }

    # Set root
    if "." in module_nodes:
        module_nodes["."]["level"] = "root"
        # Add top-level modules as children of root
        top_modules = [
            m for m in module_nodes
            if m != "." and str(PurePosixPath(m).parent) == "."
        ]
        top_files = [f for f in file_nodes if _extract_module_from_file(f) == "."]
        module_nodes["."]["children"] = sorted(set(top_modules + top_files))
        module_nodes["."]["child_count"] = len(module_nodes["."]["children"])

    # Step 4: Compute ancestor chains for every leaf node
    hierarchy_nodes = []
    for node in graph_nodes:
        file_path = _extract_file_from_path(node["path"])
        module_path = _extract_module_from_file(file_path)
        module_chain = _build_module_chain(module_path)

        ancestors = [file_path] + module_chain
        # Remove duplicates while preserving order
        seen = set()
        unique_ancestors = []
        for a in ancestors:
            if a not in seen and a != node["path"]:
                seen.add(a)
                unique_ancestors.append(a)

        hierarchy_nodes.append({
            **node,
            "ancestors": unique_ancestors,
        })

    # Add file nodes and module nodes to the hierarchy
    for fn in file_nodes.values():
        module_path = _extract_module_from_file(fn["path"])
        module_chain = _build_module_chain(module_path)
        fn["ancestors"] = module_chain
        hierarchy_nodes.append(fn)

    for mn in module_nodes.values():
        parent_module = str(PurePosixPath(mn["path"]).parent) if mn["path"] != "." else None
        if parent_module and parent_module != mn["path"]:
            chain = _build_module_chain(parent_module)
            mn["ancestors"] = chain
        else:
            mn["ancestors"] = []
        hierarchy_nodes.append(mn)

    # Step 5: Compute hub scores
    hub_scores = compute_hub_scores(graph_nodes, graph_edges)

    # Step 6: Detect coarse-granularity artifacts
    # (handled separately — see granularity.py)

    return {
        "nodes": hierarchy_nodes,
        "hub_scores": hub_scores,
        "metadata": {
            "total_leaf_nodes": len(graph_nodes),
            "total_files": len(file_nodes),
            "total_modules": len(module_nodes),
            "source_graph": graph.get("metadata", {}).get("repo_path", "unknown"),
        },
    }


def main():
    """CLI: python -m rcir.hierarchy.builder <graph.json> --output <path>"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build hierarchy view from a dependency graph"
    )
    parser.add_argument("graph_json", help="Path to the graph JSON file")
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output JSON file path (default: stdout)"
    )
    args = parser.parse_args()

    graph = json.loads(Path(args.graph_json).read_text(encoding="utf-8"))
    hierarchy = build_hierarchy(graph)

    output_json = json.dumps(hierarchy, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        meta = hierarchy["metadata"]
        print(
            f"Built hierarchy: {meta['total_leaf_nodes']} leaves, "
            f"{meta['total_files']} files, {meta['total_modules']} modules -> {args.output}"
        )
    else:
        print(output_json)


if __name__ == "__main__":
    main()
