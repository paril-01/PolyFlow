#!/usr/bin/env python3
"""
scripts/run_final_benchmark.py — Report Validation and Artifact Verification Runner.

IMPORTANT NOTE (RULE 0 & SPEC CONTRACT):
This script is a Report Validation & Derived Export Verification Tool.
It validates consistency test suites, regenerates showcase data, and checks proof exports
against raw empirical run receipts.

To execute LIVE paired model benchmark trials, use:
    python scripts/run_benchmark.py [options]
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(
        description="PolyFlow Report Validation and Artifact Verification Tool. "
                    "Validates test suites and exports from raw run receipts. "
                    "NOTE: To execute live paired model trials, use scripts/run_benchmark.py."
    )
    parser.add_argument(
        "--mode",
        choices=["validate-reports", "run-live"],
        default="validate-reports",
        help="Execution mode: 'validate-reports' verifies test suites and exports; "
             "'run-live' dispatches to scripts/run_benchmark.py for live agent trials."
    )
    return parser.parse_known_args()


def main():
    args, extra_args = parse_args()

    if args.mode == "run-live":
        print("=" * 80)
        print("DISPATCHING TO LIVE BENCHMARK RUNNER (scripts/run_benchmark.py)")
        print("=" * 80)
        cmd = [sys.executable, str(REPO_ROOT / "scripts" / "run_benchmark.py")] + extra_args
        res = subprocess.run(cmd, cwd=REPO_ROOT)
        sys.exit(res.returncode)

    print("=" * 80)
    print("POLYFLOW REPORT VALIDATION & ARTIFACT INTEGRITY VERIFICATION")
    print("Mode: VALIDATE-REPORTS (Rule 0 & Verification Contract Enforced)")
    print("=" * 80)

    # Pre-check: Ensure raw run receipts exist before validating derived exports
    raw_receipts_dir = REPO_ROOT / "experiments" / "runs" / "run_20261009_blind_verified"
    if not raw_receipts_dir.exists():
        print(f"[FAIL-CLOSED] Missing required raw empirical receipts at: {raw_receipts_dir}")
        print("Cannot validate or rebuild reports without original raw run data.")
        sys.exit(1)

    # 1. Run unit and anti-fabrication test suites
    print("\n[Step 1/3] Running benchmark integrity and claim consistency tests...")
    test_cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_feature_closure.py",
        "tests/test_ui_claims.py",
        "tests/test_final_claim_consistency.py",
        "tests/test_backend_proof_server.py",
        "tests/test_polyflow.py",
        "-v"
    ]
    test_res = subprocess.run(test_cmd, cwd=REPO_ROOT)
    unit_tests_passed = (test_res.returncode == 0)

    # 2. Build showcase data artifacts
    print("\n[Step 2/3] Building showcase empirical data artifacts from receipts...")
    sc_res = subprocess.run([sys.executable, "scripts/build_showcase_data.py"], cwd=REPO_ROOT)
    showcase_passed = (sc_res.returncode == 0)

    # 3. Build canonical run exports
    print("\n[Step 3/3] Generating canonical run exports and derived CSVs from receipts...")
    exp_res = subprocess.run([sys.executable, "scripts/build_run_exports.py"], cwd=REPO_ROOT)
    exports_passed = (exp_res.returncode == 0)

    # Segregated Status Reporting
    print("\n" + "=" * 80)
    print("SYSTEM STATUS BREAKDOWN (RULE 0 COMPLIANT)")
    print("=" * 80)
    print(f"  • Unit & Consistency Tests:   {'PASSED' if unit_tests_passed else 'FAILED'}")
    print(f"  • Showcase Artifacts Build:   {'PASSED' if showcase_passed else 'FAILED'}")
    print(f"  • Run Exports & Proofs:       {'PASSED' if exports_passed else 'FAILED'}")
    print(f"  • Historical Index Gate:      SATISFIED (840 DocTypes, 842 Poly Features from ea221b9)")
    print(f"  • Historical Retrieval Gate:  SATISFIED (100% Macro Recall across 5 Verticals from run_20261009)")
    print(f"  • Historical Agent Task Gate: NOT_SATISFIED (0/5 Completed on qwen2.5-coder:1.5b)")
    print(f"  • Historical Token Savings:   NOT_MEASURED (Requires Both-Successful Pairs)")
    print(f"  • Live Paired Trial Status:   NOT_RUN_BY_THIS_WRAPPER (use 'python scripts/run_benchmark.py')")
    print("=" * 80)

    if not unit_tests_passed or not showcase_passed or not exports_passed:
        print("[FAIL] Verification failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()

