#!/usr/bin/env python3
"""
scripts/run_final_benchmark.py — Reproducible Entrypoint for Final Blind Benchmark & Verification.
"""

import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def main():
    print("=" * 80)
    print("POLYFLOW REPRODUCIBLE FINAL BENCHMARK & VERIFICATION")
    print("=" * 80)

    # 1. Run showcase builder & export pipeline
    print("\n[Step 1/3] Building showcase empirical data artifacts...")
    res1 = subprocess.run([sys.executable, "scripts/build_showcase_data.py"], cwd=REPO_ROOT)
    if res1.returncode != 0:
        print("[FAIL] Failed to build showcase data.")
        sys.exit(1)

    print("\n[Step 2/3] Generating canonical run exports and derived CSVs...")
    res2 = subprocess.run([sys.executable, "scripts/build_run_exports.py"], cwd=REPO_ROOT)
    if res2.returncode != 0:
        print("[FAIL] Failed to generate run exports.")
        sys.exit(1)

    # 2. Run anti-fabrication test suite
    print("\n[Step 3/3] Running pytest anti-fabrication & consistency verification suite...")
    res3 = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_feature_closure.py",
        "tests/test_ui_claims.py",
        "tests/test_final_claim_consistency.py",
        "tests/test_polyflow.py",
        "-v"
    ], cwd=REPO_ROOT)

    if res3.returncode == 0:
        print("\n" + "=" * 80)
        print("ALL BENCHMARK VERIFICATIONS PASSED SUCCESSFULLY (RULE 0 COMPLIANT)")
        print("=" * 80)
    else:
        print("\n[FAIL] Test suite failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
