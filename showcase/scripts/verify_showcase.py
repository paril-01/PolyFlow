#!/usr/bin/env python3
import json
from pathlib import Path

def verify():
    base = Path(__file__).resolve().parent.parent
    manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    print(f"Verifying {len(manifest['files'])} showcase artifacts...")
    errors = 0
    for rel_path, expected_hash in manifest["files"].items():
        p = base / rel_path
        if not p.exists():
            print(f"MISSING: {rel_path}")
            errors += 1
        elif expected_hash != "DYNAMIC":
            import hashlib
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            if h != expected_hash:
                print(f"HASH MISMATCH: {rel_path}")
                errors += 1
    if errors == 0:
        print("ALL SHOWCASE ARTIFACTS VERIFIED SUCCESSFULLY")
    else:
        print(f"FAILED: {errors} artifacts failed verification")

if __name__ == "__main__":
    verify()
