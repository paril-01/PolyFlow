"""
Tarjan's Strongly Connected Components algorithm + size-capped collapsing.

For dependency graphs with cycles (mutual recursion, circular imports),
this module:
1. Detects all SCCs using Tarjan's algorithm
2. Collapses SCCs ≤ threshold into a single meta-node
3. Keeps larger SCCs as internal sub-graphs (recursive decomposition)

This prevents "god node" formation (failure mode #4 from §4.2).
"""

from collections import defaultdict
from typing import Any


def tarjan_scc(nodes: list[str], edges: list[dict]) -> list[list[str]]:
    """Find all strongly connected components using Tarjan's algorithm.

    Args:
        nodes: List of node path strings.
        edges: List of edge dicts with 'source' and 'target' keys.

    Returns:
        List of SCCs, each SCC being a list of node paths.
        Single-node SCCs (no self-loop) are included.
    """
    # Build adjacency list — only include edges between known nodes
    node_set = set(nodes)
    adj: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        src, tgt = edge["source"], edge["target"]
        if src in node_set and tgt in node_set:
            adj[src].append(tgt)

    # Tarjan's algorithm state
    index_counter = [0]
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    result: list[list[str]] = []

    def strongconnect(v: str):
        indices[v] = index_counter[0]
        lowlinks[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack.add(v)

        for w in adj.get(v, []):
            if w not in indices:
                strongconnect(w)
                lowlinks[v] = min(lowlinks[v], lowlinks[w])
            elif w in on_stack:
                lowlinks[v] = min(lowlinks[v], indices[w])

        # If v is a root node, pop the SCC
        if lowlinks[v] == indices[v]:
            scc: list[str] = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                scc.append(w)
                if w == v:
                    break
            result.append(scc)

    # Handle potentially disconnected graph
    for node in nodes:
        if node not in indices:
            strongconnect(node)

    return result


def collapse_sccs(
    graph: dict[str, Any],
    threshold: int = 30,
) -> dict[str, Any]:
    """Collapse small SCCs into meta-nodes, keep large ones as sub-graphs.

    Args:
        graph: The full graph dict with 'nodes' and 'edges'.
        threshold: Maximum SCC size to collapse into a single node.

    Returns:
        Modified graph dict with:
        - Small SCCs replaced by a single meta-node
        - Large SCCs annotated but kept as individual nodes
        - 'scc_info' metadata added
    """
    node_paths = [n["path"] for n in graph["nodes"]]
    sccs = tarjan_scc(node_paths, graph["edges"])

    # Filter to only non-trivial SCCs (size > 1)
    # Single-node "SCCs" with no self-loop are not real cycles
    self_loop_targets = set()
    for edge in graph["edges"]:
        if edge["source"] == edge["target"]:
            self_loop_targets.add(edge["source"])

    nontrivial_sccs = [
        scc for scc in sccs
        if len(scc) > 1 or (len(scc) == 1 and scc[0] in self_loop_targets)
    ]

    if not nontrivial_sccs:
        return {
            **graph,
            "scc_info": {
                "total_sccs": 0,
                "collapsed": 0,
                "kept_as_subgraph": 0,
            }
        }

    # Build node lookup
    node_by_path = {n["path"]: n for n in graph["nodes"]}

    # Track which nodes belong to which SCC
    node_to_scc: dict[str, int] = {}
    for scc_idx, scc in enumerate(nontrivial_sccs):
        for node_path in scc:
            node_to_scc[node_path] = scc_idx

    collapsed_count = 0
    kept_count = 0
    new_nodes = []
    removed_paths: set[str] = set()
    scc_meta_paths: dict[int, str] = {}  # scc_idx -> meta-node path

    for scc_idx, scc in enumerate(nontrivial_sccs):
        if len(scc) <= threshold:
            # Collapse into a meta-node
            collapsed_count += 1
            meta_path = f"SCC_{scc_idx}::[{', '.join(sorted(scc)[:5])}{'...' if len(scc) > 5 else ''}]"
            scc_meta_paths[scc_idx] = meta_path
            removed_paths.update(scc)

            new_nodes.append({
                "path": meta_path,
                "kind": "scc_collapsed",
                "level": "scc",
                "members": sorted(scc),
                "member_count": len(scc),
            })
        else:
            # Keep as individual nodes but annotate
            kept_count += 1
            for node_path in scc:
                if node_path in node_by_path:
                    node_by_path[node_path]["scc_group"] = scc_idx
                    node_by_path[node_path]["scc_size"] = len(scc)

    # Rebuild node list: keep non-removed nodes + add meta-nodes
    final_nodes = [n for n in graph["nodes"] if n["path"] not in removed_paths]
    final_nodes.extend(new_nodes)

    # Rebuild edges: redirect edges involving collapsed SCC members
    final_edges = []
    for edge in graph["edges"]:
        src = edge["source"]
        tgt = edge["target"]

        # Remap collapsed SCC members to their meta-node
        if src in removed_paths and src in node_to_scc:
            scc_idx = node_to_scc[src]
            if scc_idx in scc_meta_paths:
                src = scc_meta_paths[scc_idx]
        if tgt in removed_paths and tgt in node_to_scc:
            scc_idx = node_to_scc[tgt]
            if scc_idx in scc_meta_paths:
                tgt = scc_meta_paths[scc_idx]

        # Skip self-loops on meta-nodes (internal SCC edges)
        if src == tgt and src.startswith("SCC_"):
            continue

        final_edges.append({**edge, "source": src, "target": tgt})

    # Deduplicate edges after remapping
    seen: set[tuple] = set()
    deduped_edges = []
    for edge in final_edges:
        key = (edge["source"], edge["target"], edge["type"])
        if key not in seen:
            seen.add(key)
            deduped_edges.append(edge)

    return {
        "nodes": final_nodes,
        "edges": deduped_edges,
        "metadata": {
            **graph.get("metadata", {}),
            "scc_processing": True,
        },
        "scc_info": {
            "total_sccs": len(nontrivial_sccs),
            "collapsed": collapsed_count,
            "kept_as_subgraph": kept_count,
            "threshold": threshold,
        },
    }
