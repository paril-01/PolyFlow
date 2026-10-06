#!/usr/bin/env python3
"""
RCIR v8.5 — Report Consistency & Byte-Invariance Validator.

Validates that:
1. Generates all reports into an isolated temporary directory.
2. Compares SHA-256 byte-for-byte against committed reports in reports/.
3. Fails with exit code 1 if any discrepancy or non-determinism is detected.
"""

from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

# Add project roots
SCRIPT_DIR = Path(__file__).resolve().parent
RCIR_V8_5_ROOT = SCRIPT_DIR.parent
POLYFLOW_ROOT = RCIR_V8_5_ROOT.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from generate_reports import generate_all_reports

COMMITTED_REPORTS_DIR = RCIR_V8_5_ROOT / "reports"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def validate_consistency() -> bool:
    print("=" * 80)
    print("RCIR v8.5 — Report Byte/Hash Invariance Validator")
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
                # v8_4_reassessment.md is static historical audit
                if cf.name == "v8_4_reassessment.md":
                    print(f"  [STATIC] {cf.name} (historical audit baseline)")
                    continue
                print(f"  [MISSING] {cf.name} not generated in temp output")
                all_passed = False
                continue

            h_committed = compute_sha256(cf)
            h_temp = compute_sha256(tf)

            if h_committed != h_temp:
                print(f"  [MISMATCH] {cf.name}: committed {h_committed[:8]} != temp {h_temp[:8]}")
                all_passed = False
            else:
                print(f"  [PASSED] {cf.name} ({h_committed[:12]}...)")

        status_str = "PASSED (100% Byte Invariant)" if all_passed else "FAILED (Discrepancy Detected)"
        print(f"\nReport Consistency Result: {status_str}")
        return all_passed


if __name__ == "__main__":
    success = validate_consistency()
    sys.exit(0 if success else 1)
