"""
'polyflow test' Command.

Discovers and tests all .poly feature contracts in a project directory.
"""

import sys
import time
from pathlib import Path
from typing import Optional

from polyflow_sdk.core.interpreter import PolyInterpreter
from polyflow_sdk.core.contract import ContractValidator


def _generate_sample_payload(schemas: dict) -> dict:
    payload = {}
    for sname, schema in schemas.items():
        for fname, fdef in schema.fields.items():
            t = fdef.type_str.lower()
            if t == "string":
                if fdef.constraints.get("format") == "email":
                    payload[fname] = "admin@polyflow.internal"
                elif "min" in fdef.constraints:
                    payload[fname] = "SecurePassword123!"
                else:
                    payload[fname] = "test_file.txt"
            elif t in ("int", "integer"):
                payload[fname] = int(fdef.constraints.get("min", 10))
            elif t in ("bool", "boolean"):
                payload[fname] = True
            elif t in ("bytes", "binary"):
                payload[fname] = "cG9seWZsb3dfdGVzdF9ieXRlcw=="
            elif t in ("list", "array"):
                payload[fname] = []
            elif t in ("dict", "map"):
                payload[fname] = {}
            else:
                payload[fname] = "sample"
    # Common polyflow test defaults
    payload.setdefault("email", "admin@polyflow.internal")
    payload.setdefault("password", "SecurePassword123!")
    payload.setdefault("file_bytes", "cG9seWZsb3dfdGVzdF9ieXRlcw==")
    payload.setdefault("file_name", "document.pdf")
    payload.setdefault("user_id", "usr_test_1001")
    payload.setdefault("file_id", "file_blob_2026")
    return payload


def execute_test(directory: str = ".") -> int:
    root = Path(directory).resolve()
    poly_files = list(root.glob("**/*.poly"))

    if not poly_files:
        print(f"No .poly feature contract files found in '{root}'.")
        return 0

    print(f"\n[PolyFlow Test Runner] Discovered {len(poly_files)} .poly contract files in {root.name}")
    print("=" * 65)

    interpreter = PolyInterpreter()
    total_passed = 0
    total_failed = 0

    t0 = time.time()
    for pf in poly_files:
        rel_path = pf.relative_to(root)
        try:
            parsed = interpreter.parse_file(pf)
            audit = ContractValidator.audit_contract_compliance(parsed)
            test_payload = _generate_sample_payload(parsed.schemas)
            exec_res = interpreter.execute_file(pf, payload=test_payload)

            if audit["compliant"] and exec_res["status"] == "success":
                print(f"[PASS] {rel_path} ({len(exec_res['results'])} cells, {len(parsed.schemas)} schemas)")
                total_passed += 1
            else:
                print(f"[FAIL] {rel_path}")
                for iss in audit.get("issues", []):
                    print(f"    • Contract Issue: {iss}")
                for cell in exec_res.get("results", []):
                    if cell["status"] != "success":
                        print(f"    • Cell @{cell['language']}[{cell['tag']}] Error: {cell['error']}")
                total_failed += 1
        except Exception as e:
            print(f"[ERROR] {rel_path}: {e}")
            total_failed += 1

    elapsed = time.time() - t0
    print("=" * 65)
    print(f"Test Run Completed in {elapsed:.2f}s: {total_passed} Passed, {total_failed} Failed\n")
    return 0 if total_failed == 0 else 1
