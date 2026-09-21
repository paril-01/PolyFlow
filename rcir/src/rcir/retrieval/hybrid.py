"""
Hybrid three-pass retrieval engine (§7).

Three passes, merged and deduped:
1. Flattened/collapsed-tree scoring across all hierarchy levels (TF-IDF)
2. Direct symbol/keyword match (exact and substring)
3. Graph traversal outward from selected nodes by confidence-weighted edges

Then: merge, deduplicate, rank, fill token budget, report coverage_warning.

Hub nodes get a scoring boost in pass 1, NOT automatic inclusion (§4.2).

CLI: python -m rcir.retrieval.hybrid <hierarchy.json> --query "..." --budget 4000
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Any

from rcir.retrieval.scorer import TFIDFScorer, tokenize
from rcir.contract.schema import ContextContract, ContractNode, validate_contract


# ─── Pass 1: Hierarchy-wide TF-IDF scoring ─────────────────────────

def _pass1_tfidf_scoring(
    nodes: list[dict],
    query: str,
    hub_scores: dict[str, float],
    hub_boost: float = 0.15,
) -> dict[str, float]:
    """Score all nodes with TF-IDF + hub score boost.

    Hub nodes get a scoring boost proportional to their hub score,
    but capped — they're more likely to be relevant, but not guaranteed.
    """
    scorer = TFIDFScorer()
    scorer.build_index(nodes)
    raw_scores = scorer.score(query)

    # Apply hub boost
    boosted: dict[str, float] = {}
    for path, score in raw_scores.items():
        hub = hub_scores.get(path, 0.0)
        boosted[path] = score + (hub * hub_boost * score) if score > 0 else 0.0

    return boosted


# ─── Pass 2: Direct symbol/keyword match ───────────────────────────

def _pass2_symbol_match(
    nodes: list[dict],
    query: str,
) -> dict[str, float]:
    """Score nodes by direct symbol/keyword matching.

    Exact function/class name matches get a high score.
    Substring matches in paths get a moderate score.
    """
    query_tokens = set(tokenize(query))
    query_lower = query.lower()
    scores: dict[str, float] = {}

    for node in nodes:
        path = node.get("path", "")
        path_lower = path.lower()

        score = 0.0

        # Extract the symbol name (last component after :: and .)
        if "::" in path:
            symbol_part = path.split("::")[-1]
        else:
            symbol_part = path.split("/")[-1]

        symbol_tokens = set(tokenize(symbol_part))

        # Exact token matches in symbol name (high value)
        common = query_tokens & symbol_tokens
        if common:
            score += len(common) * 2.0

        # Substring match in full path (moderate value)
        for qt in query_tokens:
            if qt in path_lower:
                score += 0.5

        # Exact symbol name match (highest value)
        symbol_name = symbol_part.split(".")[-1].lower() if symbol_part else ""
        for qt in query_tokens:
            if qt == symbol_name:
                score += 5.0

        scores[path] = round(score, 4)

    return scores


# ─── Pass 3: Graph traversal from selected nodes ──────────────────

def _pass3_graph_traversal(
    selected_paths: set[str],
    edges: list[dict],
    max_hops: int = 2,
    min_confidence: float = 0.3,
) -> dict[str, float]:
    """Expand context by traversing the graph outward from selected nodes.

    Follows edges weighted by confidence — high-confidence edges
    contribute more to the neighbor's score.

    Args:
        selected_paths: Paths of nodes selected by passes 1 & 2.
        edges: List of edge dicts from the graph.
        max_hops: Maximum traversal depth.
        min_confidence: Minimum edge confidence to follow.

    Returns:
        Dict of discovered node paths → propagated score.
    """
    if not selected_paths:
        return {}

    # Build adjacency lists (both directions — calls and called-by)
    outgoing: dict[str, list[tuple[str, float]]] = defaultdict(list)
    incoming: dict[str, list[tuple[str, float]]] = defaultdict(list)

    for edge in edges:
        conf = edge.get("confidence", 0.0)
        if conf < min_confidence:
            continue
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        if src and tgt:
            outgoing[src].append((tgt, conf))
            incoming[tgt].append((src, conf))

    # BFS from selected nodes
    discovered: dict[str, float] = {}
    frontier = [(path, 1.0) for path in selected_paths]  # (path, accumulated_score)

    for hop in range(max_hops):
        next_frontier = []
        for current_path, current_score in frontier:
            # Traverse outgoing edges (what does this node call?)
            for neighbor, confidence in outgoing.get(current_path, []):
                if neighbor not in selected_paths:
                    propagated = current_score * confidence * (0.5 ** hop)
                    if neighbor not in discovered or discovered[neighbor] < propagated:
                        discovered[neighbor] = round(propagated, 4)
                        next_frontier.append((neighbor, propagated))

            # Traverse incoming edges (what calls this node?)
            for neighbor, confidence in incoming.get(current_path, []):
                if neighbor not in selected_paths:
                    propagated = current_score * confidence * (0.5 ** hop)
                    if neighbor not in discovered or discovered[neighbor] < propagated:
                        discovered[neighbor] = round(propagated, 4)
                        next_frontier.append((neighbor, propagated))

        frontier = next_frontier

    return discovered


# ─── Merge & Budget ────────────────────────────────────────────────

def _estimate_tokens(node: dict, granularity: str = "fine") -> int:
    """Estimate token count for a node in the context contract.

    In fine granularity: includes signature, annotations, docstrings, and snippet.
    In coarse granularity: includes qualified path, level, and signature reference.
    """
    if granularity == "coarse":
        return max(len(node.get("path", "")) // 4, 15)

    text_len = len(node.get("path", ""))
    text_len += len(json.dumps(node.get("args", []), default=str))
    text_len += len(node.get("return_annotation", "") or "")
    text_len += len(str(node.get("decorators", [])))
    # Add estimate for any raw snippet that would be included
    text_len += (node.get("end_line", 0) - node.get("line", 0) + 1) * 40
    return max(text_len // 4, 15)  # minimum 15 tokens per fine node


def hybrid_retrieve(
    hierarchy: dict[str, Any],
    query: str,
    token_budget: int = 8000,
    graph_edges: list[dict] | None = None,
    min_relative_score: float = 0.15,
) -> ContextContract:
    """Perform hybrid three-pass retrieval with adaptive granularity.

    Args:
        hierarchy: Hierarchy dict from builder.py.
        query: The LLM's question / context request.
        token_budget: Maximum tokens for the context response.
        graph_edges: Optional edge list (if not embedded in hierarchy).
        min_relative_score: Stop adding candidates once a node's score falls
            below this fraction of the top-scoring candidate.

    Returns:
        A ContextContract with the selected nodes, within budget.
    """
    nodes = hierarchy.get("nodes", [])
    hub_scores = hierarchy.get("hub_scores", {})
    edges = graph_edges or hierarchy.get("edges", [])

    # Pass 1: TF-IDF + hub boost
    p1_scores = _pass1_tfidf_scoring(nodes, query, hub_scores)

    # Pass 2: Symbol/keyword match
    p2_scores = _pass2_symbol_match(nodes, query)

    # Merge pass 1 & 2 scores
    merged: dict[str, float] = {}
    all_paths = set(p1_scores.keys()) | set(p2_scores.keys())
    for path in all_paths:
        merged[path] = p1_scores.get(path, 0.0) + p2_scores.get(path, 0.0)

    # Select top candidates for pass 3 seed
    ranked = sorted(merged.items(), key=lambda x: x[1], reverse=True)
    top_paths = {path for path, score in ranked[:20] if score > 0}

    # Pass 3: Graph traversal expansion
    p3_scores = _pass3_graph_traversal(top_paths, edges)

    # Final merge: add graph-discovered nodes
    for path, score in p3_scores.items():
        if path in merged:
            merged[path] += score * 0.5  # graph expansion has lower weight
        else:
            merged[path] = score * 0.5

    # Final ranking
    final_ranked = sorted(merged.items(), key=lambda x: x[1], reverse=True)
    top_score = final_ranked[0][1] if final_ranked else 0.0
    score_floor = top_score * min_relative_score

    # Build node lookup
    node_by_path = {n["path"]: n for n in nodes}

    # Fill token budget with adaptive granularity (v7 §5)
    selected_nodes: list[ContractNode] = []
    tokens_used = 0
    coverage_warning = None
    hierarchy_paths_used = set()
    stopped_at_relevance_floor = False
    skipped_for_budget: set[str] = set()

    for path, score in final_ranked:
        if score <= 0:
            continue
        if score < score_floor:
            stopped_at_relevance_floor = True
            break

        node = node_by_path.get(path)
        if node is None:
            continue

        default_granularity = "fine" if node.get("level") in ("function", "class", "service", "method") else "coarse"
        est_tokens = _estimate_tokens(node, granularity=default_granularity)
        chosen_granularity = default_granularity

        # Adaptive Granularity:
        # If fine representation exceeds remaining budget, try coarse representation
        if tokens_used + est_tokens > token_budget:
            coarse_tokens = _estimate_tokens(node, granularity="coarse")
            if tokens_used + coarse_tokens <= token_budget:
                chosen_granularity = "coarse"
                est_tokens = coarse_tokens
            else:
                skipped_for_budget.add(path)
                continue  # Cannot fit even at coarse granularity

        selected_nodes.append(ContractNode(
            path=path,
            level=node.get("level", "unknown"),
            summary=f"{node.get('kind', 'node')} at {path}",
            raw_snippet=None,
            interface_status=node.get("interface_status", "unknown"),
            body_status=node.get("body_status", "unknown"),
            summary_version=f"v{node.get('version_number', 1)}",
            summary_source="incremental_ast_analysis",
            granularity=chosen_granularity,
            relevance_score=score,
        ))
        tokens_used += est_tokens
        hierarchy_paths_used.add(path)

    # Check for coverage warning -- only for candidates that were relevant
    # enough to keep (above the relevance floor) but didn't fit the budget.
    # A node correctly excluded for being below the relevance floor is
    # working as intended, not a coverage gap, so it must not trigger this.
    graph_discovered_not_included = (set(p3_scores.keys()) - hierarchy_paths_used) & skipped_for_budget
    if graph_discovered_not_included and len(selected_nodes) > 0:
        coverage_warning = (
            f"cross-cutting query — hierarchy may have missed related nodes; "
            f"graph traversal found {len(graph_discovered_not_included)} additional "
            f"relevant candidates that did not fit in the token budget"
        )

    contract = ContextContract(
        query=query,
        nodes=selected_nodes,
        token_budget_used=tokens_used,
        token_budget_total=token_budget,
        coverage_warning=coverage_warning,
    )

    return contract


def main():
    """CLI: python -m rcir.retrieval.hybrid <hierarchy.json> --query "..." --budget 4000"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Hybrid context retrieval with token budget"
    )
    parser.add_argument("hierarchy_json", help="Path to hierarchy JSON file")
    parser.add_argument("--query", "-q", required=True, help="Context query")
    parser.add_argument("--budget", "-b", type=int, default=8000, help="Token budget")
    parser.add_argument(
        "--graph", "-g",
        default=None,
        help="Path to graph JSON (if edges not in hierarchy)"
    )
    args = parser.parse_args()

    hierarchy = json.loads(Path(args.hierarchy_json).read_text(encoding="utf-8"))

    graph_edges = None
    if args.graph:
        graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
        graph_edges = graph.get("edges", [])

    contract = hybrid_retrieve(
        hierarchy=hierarchy,
        query=args.query,
        token_budget=args.budget,
        graph_edges=graph_edges,
    )

    # Validate contract before output
    errors = validate_contract(contract)
    if errors:
        print("WARNING: Contract validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)

    print(json.dumps(contract.to_dict(), indent=2))


if __name__ == "__main__":
    main()
