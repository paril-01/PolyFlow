#!/usr/bin/env python3
"""
Acceptance verification test for AGENT-TASK-01.
Verifies that ApiController::getThumbnail accepts $crop and passes it to getPreview.
"""
import re
import sys
from pathlib import Path


def test_api_controller(repo_root: Path) -> int:
    target = repo_root / "apps" / "files" / "lib" / "Controller" / "ApiController.php"
    if not target.exists():
        sys.stderr.write(f"SETUP_ERROR: Target file does not exist: {target}\n")
        return 2

    content = target.read_text(encoding="utf-8")
    if "function getThumbnail" not in content:
        sys.stderr.write("SETUP_ERROR: function getThumbnail not found in ApiController.php\n")
        return 2

    # Extract signature
    after_sig = content.split("function getThumbnail", 1)[1]
    sig = after_sig.split(")", 1)[0]
    
    # Structural check on signature: $crop must be present and default to true (F06)
    crop_match = re.search(r'\$crop\s*(=\s*([a-zA-Z0-9_]+))?', sig)
    if not crop_match:
        sys.stderr.write(f"ASSERTION_FAIL: getThumbnail parameter list does not include $crop. Signature: ({sig.strip()})\n")
        return 1

    default_val = crop_match.group(2)
    if not default_val or default_val.lower() != "true":
        sys.stderr.write(
            f"ASSERTION_FAIL: getThumbnail parameter $crop must default to true, found: {crop_match.group(0).strip()}\n"
        )
        return 1

    # Structural check on body: must propagate $crop into getPreview(...) call (F06)
    body = after_sig.split("{", 1)[1].split("public function", 1)[0]
    
    preview_match = re.search(r'->getPreview\s*\(([^;]+)\)', body)
    if not preview_match:
        sys.stderr.write("ASSERTION_FAIL: getPreview call not found in getThumbnail body\n")
        return 1

    preview_args_str = preview_match.group(1).split(")", 1)[0]
    args = [a.strip() for a in preview_args_str.split(",")]
    if not any("$crop" in a for a in args):
        sys.stderr.write(
            f"ASSERTION_FAIL: getPreview call does not pass $crop as an argument. Found arguments: {preview_args_str.strip()}\n"
        )
        return 1

    print("PASS: ApiController::getThumbnail correctly defines $crop = true and propagates to getPreview")
    return 0


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".")
    sys.exit(test_api_controller(root))
