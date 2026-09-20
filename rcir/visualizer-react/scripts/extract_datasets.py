"""
Extract datasets for the RCIR React Visualizer.
Runs extractor and hierarchy builder for:
1. OpenTelemetry Astronomy Shop - Recommendation Service
2. OpenTelemetry Astronomy Shop - Agent Service
3. PSF Requests
4. Pallets Flask
5. PolyFlow Core
"""

import json
import os
import sys
from pathlib import Path

# Add PolyFlow and rcir/src to sys.path
polyflow_root = Path(__file__).resolve().parents[3]
rcir_src = polyflow_root / "rcir" / "src"
sys.path.insert(0, str(polyflow_root))
sys.path.insert(0, str(rcir_src))

from rcir.graph.extractor import extract_graph
from rcir.hierarchy.builder import build_hierarchy


def extract_and_save(target_path: Path, output_json: Path, name: str):
    print(f"\n--- Extracting {name} from {target_path} ---")
    if not target_path.exists():
        print(f"Warning: {target_path} does not exist. Skipping.")
        return None

    # Run extract_graph
    graph_dict = extract_graph(target_path)
    print(f"Extracted {len(graph_dict.get('nodes', []))} nodes, {len(graph_dict.get('edges', []))} edges")

    # Run build_hierarchy
    hierarchy_dict = build_hierarchy(graph_dict)
    print(f"Built hierarchy with {len(hierarchy_dict.get('nodes', []))} nodes")

    bundle = {
        "id": name,
        "name": name,
        "source_path": str(target_path),
        "graph": graph_dict,
        "hierarchy": hierarchy_dict,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(bundle, indent=2, default=str), encoding="utf-8")
    print(f"Saved to {output_json} ({output_json.stat().st_size / 1024:.1f} KB)")
    return bundle


def main():
    data_dir = polyflow_root / "rcir" / "visualizer-react" / "public" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    targets = [
        ("otel_recommendation", polyflow_root / "repos" / "opentelemetry-demo" / "src" / "recommendation"),
        ("otel_agent", polyflow_root / "repos" / "opentelemetry-demo" / "src" / "agent"),
        ("requests", polyflow_root / "repos" / "requests" / "src" / "requests"),
        ("flask", polyflow_root / "repos" / "flask" / "src" / "flask"),
        ("polyflow", polyflow_root / "rcir" / "src" / "rcir"),
    ]

    manifest = []

    for key, path in targets:
        out_file = data_dir / f"{key}.json"
        res = extract_and_save(path, out_file, key)
        if res:
            manifest.append({
                "id": key,
                "name": key.replace("_", " ").title(),
                "path": f"/data/{key}.json",
                "nodes": len(res["graph"].get("nodes", [])),
                "edges": len(res["graph"].get("edges", [])),
                "hierarchy_nodes": len(res["hierarchy"].get("nodes", [])),
            })

    manifest_file = data_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nWrote manifest with {len(manifest)} datasets to {manifest_file}")


if __name__ == "__main__":
    main()
