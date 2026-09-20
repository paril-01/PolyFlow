"""
Extract and bundle real open source repositories for the RCIR visualizer.
"""

import json
import subprocess
from pathlib import Path


def bundle():
    vis_dir = Path("rcir/visualizer")
    vis_dir.mkdir(parents=True, exist_ok=True)

    # 1. PSF Requests
    print("--- 1. Processing psf/requests ---")
    req_graph_file = vis_dir / "requests_graph.json"
    req_hier_file = vis_dir / "requests_hierarchy.json"

    res = subprocess.run(
        ["python", "-m", "rcir.graph.extractor", "repos/requests/src/requests", "--output", str(req_graph_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(res.stdout.strip())

    res = subprocess.run(
        ["python", "-m", "rcir.hierarchy.builder", str(req_graph_file), "--output", str(req_hier_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(res.stdout.strip())

    with open(req_graph_file, "r", encoding="utf-8") as f:
        rg = json.load(f)
    with open(req_hier_file, "r", encoding="utf-8") as f:
        rh = json.load(f)

    (vis_dir / "data_requests.js").write_text(
        "window.REQUESTS_DATA = " + json.dumps({"graph": rg, "hierarchy": rh}) + ";\n",
        encoding="utf-8",
    )
    req_graph_file.unlink(missing_ok=True)
    req_hier_file.unlink(missing_ok=True)
    print(f"Requests successfully bundled: {len(rh['nodes'])} nodes, {len(rg['edges'])} edges")

    # 2. Pallets Flask
    print("\n--- 2. Processing pallets/flask ---")
    flask_graph_file = vis_dir / "flask_graph.json"
    flask_hier_file = vis_dir / "flask_hierarchy.json"

    res = subprocess.run(
        ["python", "-m", "rcir.graph.extractor", "repos/flask/src/flask", "--output", str(flask_graph_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(res.stdout.strip())

    res = subprocess.run(
        ["python", "-m", "rcir.hierarchy.builder", str(flask_graph_file), "--output", str(flask_hier_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(res.stdout.strip())

    with open(flask_graph_file, "r", encoding="utf-8") as f:
        fg = json.load(f)
    with open(flask_hier_file, "r", encoding="utf-8") as f:
        fh = json.load(f)

    (vis_dir / "data_flask.js").write_text(
        "window.FLASK_DATA = " + json.dumps({"graph": fg, "hierarchy": fh}) + ";\n",
        encoding="utf-8",
    )
    flask_graph_file.unlink(missing_ok=True)
    flask_hier_file.unlink(missing_ok=True)
    print(f"Flask successfully bundled: {len(fh['nodes'])} nodes, {len(fg['edges'])} edges")


if __name__ == "__main__":
    bundle()
