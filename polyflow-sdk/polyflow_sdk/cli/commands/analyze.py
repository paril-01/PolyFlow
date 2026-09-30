"""
'polyflow analyze' Command.

Performs static multi-language dependency graph extraction and change impact analysis.
"""

import sys
import json
import time
from pathlib import Path
from typing import Optional

from polyflow_sdk.core.rcir_bridge import RcirBridge


def execute_analyze(target_dir: str, impact_symbol: Optional[str] = None, output_json: Optional[str] = None) -> int:
    path = Path(target_dir).resolve()
    if not path.exists():
        print(f"Error: Path '{target_dir}' does not exist.")
        return 1

    print(f"\n[PolyFlow RCIR] Analyzing codebase at: {path}")
    t0 = time.time()

    try:
        graph = RcirBridge.extract_repository(path)
    except Exception as e:
        print(f"Error extracting RCIR graph: {e}")
        return 1

    elapsed = time.time() - t0
    meta = graph.get("metadata", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    print(f"\nAnalysis completed in {elapsed:.2f}s:")
    print(f"  • Total Nodes:         {len(nodes):,}")
    print(f"  • Total Edges:         {len(edges):,}")
    print(f"  • Declarative Routes:  {meta.get('php_routes_found', meta.get('http_routes_found', 0)):,}")
    print(f"  • Cross-Boundary Edges:{meta.get('cross_boundary_edges_found', 0):,}")
    print(f"  • Config Dependencies: {meta.get('config_edges_found', 0):,}")

    if impact_symbol:
        print(f"\n[Impact Query] Calculating blast radius for: '{impact_symbol}'...")
        impact = RcirBridge.analyze_impact(graph, impact_symbol)
        affected = impact.get("affected_files", [])
        print(f"  • Direct Callers:     {len(impact.get('direct_callers', []))}")
        print(f"  • Transitive Callers: {len(impact.get('transitive_callers', []))}")
        print(f"  • Impacted Files:     {len(affected)}")
        for f in affected[:10]:
            print(f"      - {f}")
        if len(affected) > 10:
            print(f"      ... and {len(affected) - 10} more files")

    if output_json:
        out_p = Path(output_json)
        out_p.write_text(json.dumps(graph, indent=2, default=str), encoding="utf-8")
        print(f"\nFull graph saved to: {out_p}")

    print("")
    return 0
