"""
Hub node detection and scoring for hierarchy nodes.

Hub nodes (high in-degree) are common in dependency graphs — e.g., utility
functions called from everywhere. These get a relevance-weighted prior
boost in retrieval scoring, NOT unconditional inclusion (§4.2, failure mode #5).

Scoring: log-damped in-degree to prevent linear scaling from dominating
the token budget.
"""

import math
from collections import Counter
from typing import Any


def compute_hub_scores(
    nodes: list[dict],
    edges: list[dict],
) -> dict[str, float]:
    """Compute hub scores for all nodes based on in-degree.

    Uses log-damped in-degree: score = log2(1 + in_degree) / log2(1 + max_in_degree)
    This normalizes to [0, 1] and dampens extreme hubs.

    Args:
        nodes: List of node dicts with 'path' keys.
        edges: List of edge dicts with 'target' keys.

    Returns:
        Dict mapping node path → hub score (float in [0, 1]).
    """
    # Count in-degree for each node
    in_degree: Counter = Counter()
    node_paths = {n["path"] for n in nodes}

    for edge in edges:
        target = edge.get("target", "")
        if target in node_paths:
            in_degree[target] += 1

    if not in_degree:
        return {n["path"]: 0.0 for n in nodes}

    max_in_degree = max(in_degree.values())

    if max_in_degree == 0:
        return {n["path"]: 0.0 for n in nodes}

    log_max = math.log2(1 + max_in_degree)

    scores: dict[str, float] = {}
    for node in nodes:
        path = node["path"]
        deg = in_degree.get(path, 0)
        if deg == 0:
            scores[path] = 0.0
        else:
            scores[path] = round(math.log2(1 + deg) / log_max, 4)

    return scores


def identify_hubs(
    hub_scores: dict[str, float],
    threshold: float = 0.5,
) -> list[str]:
    """Identify nodes that are hubs (high connectivity).

    Args:
        hub_scores: Dict from compute_hub_scores.
        threshold: Minimum score to be considered a hub.

    Returns:
        List of node paths that are hubs, sorted by score descending.
    """
    hubs = [
        (path, score) for path, score in hub_scores.items()
        if score >= threshold
    ]
    hubs.sort(key=lambda x: x[1], reverse=True)
    return [path for path, _ in hubs]
