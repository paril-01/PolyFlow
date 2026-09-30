"""
Phase B: RCIR Graph Extraction on Nextcloud.

Runs the real RCIR graph extractor against the Nextcloud server repository
and captures all performance and output metrics.
"""

import json
import os
import sys
import time
import tracemalloc
from pathlib import Path

# Add RCIR to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))

from rcir.graph.extractor import extract_graph

NEXTCLOUD_PATH = REPO_ROOT / "experiments" / "nextcloud_validation" / "nextcloud-server"
OUTPUT_DIR = REPO_ROOT / "experiments" / "nextcloud_validation" / "rcir"


def main():
    print(f"Running RCIR graph extraction on: {NEXTCLOUD_PATH}")
    print(f"RCIR source: {REPO_ROOT / 'rcir' / 'src'}")

    if not NEXTCLOUD_PATH.exists():
        print("ERROR: Nextcloud repo not found!")
        return

    # Start memory tracking
    tracemalloc.start()

    # Run extraction
    start_time = time.time()
    try:
        graph = extract_graph(
            str(NEXTCLOUD_PATH),
            exclude_dirs={"vendor", "node_modules", "3rdparty", ".git"},
        )
        success = True
        error = None
    except Exception as e:
        graph = None
        success = False
        error = str(e)
        import traceback
        traceback.print_exc()

    end_time = time.time()
    elapsed = end_time - start_time

    # Memory stats
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if not success:
        result = {
            "status": "FAILED",
            "error": error,
            "extraction_time_seconds": round(elapsed, 3),
            "peak_memory_mb": round(peak_mem / (1024 * 1024), 2),
        }
    else:
        # Analyze graph
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        metadata = graph.get("metadata", {})

        # Edge type distribution
        edge_type_counts = {}
        resolution_counts = {}
        for e in edges:
            et = e.get("edge_type", e.get("type", "unknown"))
            edge_type_counts[et] = edge_type_counts.get(et, 0) + 1
            res = e.get("resolution", "unknown")
            resolution_counts[res] = resolution_counts.get(res, 0) + 1

        # Node kind distribution
        node_kind_counts = {}
        node_lang_counts = {}
        for n in nodes:
            kind = n.get("kind", "unknown")
            node_kind_counts[kind] = node_kind_counts.get(kind, 0) + 1
            lang = n.get("language", "python")  # Default python for original extractor nodes
            node_lang_counts[lang] = node_lang_counts.get(lang, 0) + 1

        result = {
            "status": "SUCCESS",
            "extraction_time_seconds": round(elapsed, 3),
            "peak_memory_mb": round(peak_mem / (1024 * 1024), 2),
            "graph_stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
            },
            "edge_type_distribution": edge_type_counts,
            "resolution_distribution": resolution_counts,
            "node_kind_distribution": node_kind_counts,
            "node_language_distribution": node_lang_counts,
            "metadata": metadata,
        }

        # Save full graph (may be large)
        graph_path = OUTPUT_DIR / "nextcloud_graph.json"
        graph_path.write_text(json.dumps(graph, indent=2, default=str), encoding="utf-8")
        print(f"\nFull graph saved to: {graph_path} ({graph_path.stat().st_size / (1024*1024):.1f} MB)")

    # Save metrics
    metrics_path = OUTPUT_DIR / "extraction_metrics.json"
    metrics_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"Metrics saved to: {metrics_path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"RCIR EXTRACTION RESULTS - NEXTCLOUD")
    print(f"{'='*60}")
    print(f"Status:           {result['status']}")
    print(f"Extraction time:  {result['extraction_time_seconds']:.1f}s")
    print(f"Peak memory:      {result['peak_memory_mb']:.1f} MB")

    if success:
        print(f"Total nodes:      {result['graph_stats']['total_nodes']}")
        print(f"Total edges:      {result['graph_stats']['total_edges']}")
        print(f"\nEdge types:")
        for et, count in sorted(edge_type_counts.items(), key=lambda x: -x[1]):
            print(f"  {et:25s}  {count:8d}")
        print(f"\nResolution types:")
        for res, count in sorted(resolution_counts.items(), key=lambda x: -x[1]):
            print(f"  {res:25s}  {count:8d}")
        print(f"\nNode kinds:")
        for kind, count in sorted(node_kind_counts.items(), key=lambda x: -x[1]):
            print(f"  {kind:25s}  {count:8d}")
        print(f"\nNode languages:")
        for lang, count in sorted(node_lang_counts.items(), key=lambda x: -x[1]):
            print(f"  {lang:25s}  {count:8d}")

        # Report what the extractor metadata says
        print(f"\nExtractor metadata:")
        for k, v in metadata.items():
            if k != "repo_path":
                print(f"  {k:35s}  {v}")


if __name__ == "__main__":
    main()
