"""
RCIR v8.5 — Canonical Graph Fabric & Integrity Evaluator (PHASES 21-25).

Evaluates the canonical graph fabric built from raw nextcloud_graph.json:
- Ingests nodes and edges using CanonicalGraph with LegacyEndpointNormalizer.
- Classifies endpoints into internal canonical, external, unresolved, and unsupported.
- Measures unexpected_external_internal_ratio.
- Produces results/canonical_graph_integrity.json and raw/graph/canonical_graph_summary.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from environment import get_default_environment

# Ensure rcir is importable
env = get_default_environment()
sys.path.insert(0, str(env.polyflow_root / "rcir" / "src"))

from rcir.graph.canonical_graph import CanonicalGraph, CanonicalEdgeType, ResolutionClass


def evaluate_graph_integrity():
    print("=" * 80)
    print("RCIR v8.5 — Canonical Graph Integrity Evaluation (PHASES 21-25)")
    print("=" * 80)

    t0 = time.time()
    print(f"Loading raw dependency graph from {env.graph_path}...")
    raw_graph = json.loads(env.graph_path.read_text(encoding="utf-8"))
    load_time = time.time() - t0
    print(f"Loaded raw graph in {load_time:.2f}s")

    t1 = time.time()
    cg = CanonicalGraph.from_legacy_dict(raw_graph, target_repo_root=env.target_repo_root)
    build_time = time.time() - t1
    print(f"CanonicalGraph constructed in {build_time:.2f}s")

    # Analyze endpoints across all edges
    all_endpoints = set()
    internal_endpoints = set()
    external_endpoints = set()
    unresolved_endpoints = set()
    unexpected_external_endpoints = set()

    edge_type_counts = {et.value: 0 for et in CanonicalEdgeType}
    resolution_counts = {rc.value: 0 for rc in ResolutionClass}
    total_edges = 0

    for src, edges in cg.outgoing_edges.items():
        all_endpoints.add(src)
        for e in edges:
            total_edges += 1
            all_endpoints.add(e.target_id)
            et_str = e.edge_type.value if hasattr(e.edge_type, "value") else str(e.edge_type)
            rc_str = e.resolution_class.value if hasattr(e.resolution_class, "value") else str(e.resolution_class)
            edge_type_counts[et_str] = edge_type_counts.get(et_str, 0) + 1
            resolution_counts[rc_str] = resolution_counts.get(rc_str, 0) + 1

    for ep in all_endpoints:
        if ep.startswith("external://"):
            external_endpoints.add(ep)
            sym = ep.replace("external://", "")
            # Check if this external endpoint looks like internal Nextcloud
            if cg.normalizer.is_internal_symbol(sym) or cg.normalizer.is_repo_local_file(sym):
                unexpected_external_endpoints.add(ep)
        elif ep.startswith("unresolved://"):
            unresolved_endpoints.add(ep)
        else:
            internal_endpoints.add(ep)

    total_ep = len(all_endpoints)
    unexpected_ratio = len(unexpected_external_endpoints) / max(1, len(internal_endpoints))

    print(f"Total Nodes in Registry: {len(cg.nodes)}")
    print(f"Total Unique Edge Endpoints: {total_ep}")
    print(f"  Internal Endpoints: {len(internal_endpoints)} ({len(internal_endpoints)/max(1, total_ep)*100:.1f}%)")
    print(f"  External Endpoints: {len(external_endpoints)} ({len(external_endpoints)/max(1, total_ep)*100:.1f}%)")
    print(f"  Unresolved Endpoints: {len(unresolved_endpoints)} ({len(unresolved_endpoints)/max(1, total_ep)*100:.1f}%)")
    print(f"  Unexpected External Endpoints: {len(unexpected_external_endpoints)} (ratio: {unexpected_ratio:.4f})")
    print(f"Total Evaluated Edges: {total_edges}")

    # Write raw summary
    raw_summary = {
        "run_id": env.run_id,
        "target_commit": env.target_repo_commit,
        "total_nodes": len(cg.nodes),
        "total_edges": total_edges,
        "edge_types": edge_type_counts,
        "resolution_classes": resolution_counts,
        "total_endpoints": total_ep,
        "internal_endpoints_count": len(internal_endpoints),
        "external_endpoints_count": len(external_endpoints),
        "unresolved_endpoints_count": len(unresolved_endpoints),
        "build_latency_seconds": round(build_time, 3),
    }
    raw_file = env.raw_root / "graph" / "canonical_graph_summary.json"
    raw_file.write_text(json.dumps(raw_summary, indent=2), encoding="utf-8")
    print(f"Saved raw graph summary to {raw_file}")

    # Write results/canonical_graph_integrity.json
    env.derive_run_id()
    from provenance import build_provenance_envelope
    envelope = build_provenance_envelope(env)
    integrity_result = {
        **envelope,
        "status": "PASSED" if unexpected_ratio <= 0.0 else "WARNING",
        "target_commit": env.target_repo_commit,
        "total_nodes": len(cg.nodes),
        "total_edges": total_edges,
        "total_unique_endpoints": total_ep,
        "internal_canonical_endpoints": len(internal_endpoints),
        "external_endpoints": len(external_endpoints),
        "unresolved_endpoints": len(unresolved_endpoints),
        "unexpected_external_endpoints": len(unexpected_external_endpoints),
        "unexpected_external_internal_ratio": round(unexpected_ratio, 6),
        "unsupported_edge_types": edge_type_counts.get("unsupported_edge_type", 0),
        "not_analyzed_edges": edge_type_counts.get("not_analyzed", 0),
        "edge_type_distribution": edge_type_counts,
        "resolution_class_distribution": resolution_counts,
        "build_latency_seconds": round(build_time, 3),
    }
    res_file = env.results_root / "canonical_graph_integrity.json"
    res_file.write_text(json.dumps(integrity_result, indent=2), encoding="utf-8")
    print(f"Saved canonical graph integrity result to {res_file}")


if __name__ == "__main__":
    evaluate_graph_integrity()
