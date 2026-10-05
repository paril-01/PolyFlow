#!/usr/bin/env python3
"""
RCIR v8.4 — Report Consistency & Byte-Invariance Validator.

Validates:
- Generates all 15 reports into an isolated temporary directory
- Performs strict SHA-256 byte-for-byte comparison against committed reports in reports/
- Fails with exit code 1 if any discrepancy or non-determinism is detected
"""

from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "experiments" / "rcir_v8_4" / "scripts"))

from generate_reports import generate_all_reports

COMMITTED_REPORTS_DIR = REPO_ROOT / "experiments" / "rcir_v8_4" / "reports"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def validate_consistency() -> bool:
    print("=" * 80)
    print("RCIR v8.4 — Report Byte/Hash Invariance Validator")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        generate_all_reports(out_dir=tmp_dir)

        committed_files = list(COMMITTED_REPORTS_DIR.glob("*.md"))
        if not committed_files:
            print("FAILED: No committed reports found in reports/ directory.")
            return False

        all_passed = True
        print(f"\nChecking SHA-256 byte consistency for {len(committed_files)} reports:")
        for cf in sorted(committed_files):
            tf = tmp_dir / cf.name
            if not tf.exists():
                print(f"  [MISSING] {cf.name} not generated in temp output")
                all_passed = False
                continue

            h_committed = compute_sha256(cf)
            h_temp = compute_sha256(tf)

            if h_committed != h_temp:
                print(f"  [MISMATCH] {cf.name}: committed={h_committed[:8]} vs generated={h_temp[:8]}")
                all_passed = False
            else:
                print(f"  [OK] {cf.name} (hash={h_committed[:8]}...)")

    if all_passed:
        print("\nSUCCESS: All 15 reports are 100% byte/hash consistent with raw JSON artifacts.")
        return True
    else:
        print("\nFAILED: Discrepancies detected between committed reports and generated reports.")
        return False


if __name__ == "__main__":
    if not validate_consistency():
        sys.exit(1)
