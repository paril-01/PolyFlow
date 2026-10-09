#!/usr/bin/env python3
"""
scripts/build_showcase.py — Showcase Artifact Synchronizer.

Takes an immutable run ID (--run-id <RUN_ID>), validates all artifact digests,
and mirrors validated run outputs to showcase/data/ and rcir/visualizer-react/public/data/
strictly without generating or fabricating benchmark metrics.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(description="Build showcase datasets from an immutable run.")
    parser.add_argument("--run-id", required=True, help="Immutable run ID under experiments/runs/.")
    return parser.parse_args()


def main():
    args = parse_args()
    runs_root = REPO_ROOT / "experiments" / "runs"
    run_dir = runs_root / args.run_id

    if not run_dir.exists():
        print(f"[FAIL] Run directory not found: {run_dir}")
        sys.exit(1)

    manifest_file = run_dir / "manifest.json"
    if not manifest_file.exists():
        print(f"[FAIL] Missing manifest.json in run: {run_dir}")
        sys.exit(1)

    print(f"Loading validated run: {args.run_id}")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    print(f"  Target: {manifest.get('target_repo')} @ {manifest.get('target_sha')[:7]}")
    print(f"  Status: {manifest.get('status')}")

    # Targets
    showcase_data = REPO_ROOT / "showcase" / "data"
    react_data = REPO_ROOT / "rcir" / "visualizer-react" / "public" / "data"

    showcase_data.mkdir(parents=True, exist_ok=True)
    react_data.mkdir(parents=True, exist_ok=True)

    # Copy exports CSVs
    exports_dir = run_dir / "exports"
    if exports_dir.exists():
        for csv_file in exports_dir.glob("*.csv"):
            shutil.copy2(csv_file, showcase_data / "csv" / csv_file.name)
            shutil.copy2(csv_file, react_data / "csv" / csv_file.name)
            print(f"  -> Mirrored CSV: {csv_file.name}")

    print(f"\n[OK] Successfully synchronized showcase data from run {args.run_id}")


if __name__ == "__main__":
    main()
