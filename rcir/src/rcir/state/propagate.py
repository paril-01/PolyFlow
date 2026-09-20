"""
Propagation rules for state-split invalidation (§5).

The core rule:
  - Interface or data-contract changed → regenerate summary, propagate
    upward through the FULL dependency hierarchy (blast radius)
  - Body-only changed → regenerate own summary, update immediate parent
    only, do NOT propagate further

This is where the cost savings come from: most edits are body-only changes
(refactoring logic inside a function without changing its signature), and
those only invalidate the function itself and its direct parent in the
hierarchy — not the entire transitive closure.
"""

from dataclasses import dataclass, field
from typing import Any
from collections import deque


@dataclass
class PropagationResult:
    """Result of computing blast radius from a set of diffs."""
    # Nodes that need their summaries regenerated
    invalidated_nodes: set[str] = field(default_factory=set)
    # How each node was invalidated (for debugging/audit)
    invalidation_reasons: dict[str, str] = field(default_factory=dict)
    # Statistics
    total_invalidated: int = 0
    interface_propagations: int = 0
    body_only_local: int = 0

    def to_dict(self) -> dict:
        return {
            "invalidated_nodes": sorted(self.invalidated_nodes),
            "invalidation_reasons": self.invalidation_reasons,
            "total_invalidated": self.total_invalidated,
            "interface_propagations": self.interface_propagations,
            "body_only_local": self.body_only_local,
        }


def _build_parent_map(hierarchy: dict[str, Any]) -> dict[str, list[str]]:
    """Build a mapping from node path → its ancestors from the hierarchy.

    Returns dict mapping each node path to its ordered list of ancestors
    (immediate parent first, root last).
    """
    parent_map: dict[str, list[str]] = {}
    for node in hierarchy.get("nodes", []):
        path = node.get("path", "")
        ancestors = node.get("ancestors", [])
        if path and ancestors:
            parent_map[path] = ancestors
    return parent_map


def _build_dependents_map(hierarchy: dict[str, Any]) -> dict[str, set[str]]:
    """Build a reverse dependency map: for each node, which nodes depend on it (call it).

    This is needed for interface-change propagation — when a function's
    interface changes, all its callers need to be notified.
    """
    dependents: dict[str, set[str]] = {}
    # 1. Structural dependents from children
    for node in hierarchy.get("nodes", []):
        path = node.get("path", "")
        children = node.get("children", [])
        for child in children:
            if child not in dependents:
                dependents[child] = set()
            dependents[child].add(path)

    # 2. Call/import edges: target is called by source -> source depends on target
    for edge in hierarchy.get("edges", []):
        src = edge.get("source")
        tgt = edge.get("target")
        if src and tgt:
            dependents.setdefault(tgt, set()).add(src)

    return dependents


def compute_propagation(
    diffs: list[dict],
    hierarchy: dict[str, Any],
) -> PropagationResult:
    """Compute which nodes need invalidation given a set of diffs.

    Args:
        diffs: List of NodeDiff.to_dict() objects.
        hierarchy: The hierarchy dict from builder.py.

    Returns:
        PropagationResult with the set of invalidated nodes and statistics.
    """
    result = PropagationResult()
    parent_map = _build_parent_map(hierarchy)
    dependents_map = _build_dependents_map(hierarchy)

    for diff in diffs:
        node_path = diff["node_path"]
        iface_status = diff.get("interface_status", "unchanged")
        body_status = diff.get("body_status", "unchanged")
        dc_status = diff.get("data_contract_status", "n/a")

        # Always invalidate the changed node itself
        result.invalidated_nodes.add(node_path)

        if iface_status == "changed" or dc_status == "changed":
            # Interface or data-contract change: propagate up through
            # the FULL ancestor chain
            result.invalidation_reasons[node_path] = (
                f"interface={'changed' if iface_status == 'changed' else 'unchanged'}, "
                f"data_contract={dc_status}"
            )
            result.interface_propagations += 1

            ancestors = parent_map.get(node_path, [])
            for ancestor in ancestors:
                result.invalidated_nodes.add(ancestor)
                result.invalidation_reasons[ancestor] = (
                    f"propagated from {node_path} (interface/data-contract change)"
                )

            # Also notify direct callers (dependents)
            dependents = dependents_map.get(node_path, set())
            for dep in dependents:
                result.invalidated_nodes.add(dep)
                result.invalidation_reasons[dep] = (
                    f"caller of {node_path} (interface changed)"
                )

        elif body_status == "changed":
            # Body-only change: invalidate self + immediate parent ONLY
            result.invalidation_reasons[node_path] = "body-only change (local)"
            result.body_only_local += 1

            ancestors = parent_map.get(node_path, [])
            if ancestors:
                immediate_parent = ancestors[0]
                result.invalidated_nodes.add(immediate_parent)
                result.invalidation_reasons[immediate_parent] = (
                    f"immediate parent of {node_path} (body-only change)"
                )

    result.total_invalidated = len(result.invalidated_nodes)
    return result
