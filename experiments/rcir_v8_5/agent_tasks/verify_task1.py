#!/usr/bin/env python3
"""
Acceptance verification test for AGENT-TASK-01.
Verifies that ApiController::getThumbnail accepts $crop and passes it to getPreview.
"""
import sys
from pathlib import Path

def test_api_controller(repo_root: Path) -> int:
    target = repo_root / "apps" / "files" / "lib" / "Controller" / "ApiController.php"
    if not target.exists():
        sys.stderr.write(f"Target file does not exist: {target}\n")
        return 1

    content = target.read_text(encoding="utf-8")
    if "function getThumbnail" not in content:
        sys.stderr.write("FAIL: function getThumbnail not found in ApiController.php\n")
        return 1

    # Extract signature
    after_sig = content.split("function getThumbnail", 1)[1]
    sig = after_sig.split(")", 1)[0]
    if "$crop" not in sig:
        sys.stderr.write(f"FAIL: getThumbnail parameter list does not include $crop. Signature: ({sig})\n")
        return 1

    # Check propagation to getPreview
    body = after_sig.split("{", 1)[1].split("public function", 1)[0]
    if "getPreview(" not in body or "$crop" not in body:
        sys.stderr.write("FAIL: getPreview does not propagate $crop parameter\n")
        return 1

    print("PASS: ApiController::getThumbnail correctly defines and propagates $crop")
    return 0

if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".")
    sys.exit(test_api_controller(root))
