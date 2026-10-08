#!/usr/bin/env python3
"""
Acceptance verification test for AGENT-TASK-02.
Verifies that NodeDeletedEvent declares $permanent property and isPermanent(): bool method.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def run_verification(worktree_root: Path) -> int:
    target_file = worktree_root / "lib" / "public" / "Files" / "Events" / "Node" / "NodeDeletedEvent.php"
    if not target_file.exists():
        sys.stderr.write(f"SETUP_ERROR: Target file not found: {target_file}\n")
        return 2

    content = target_file.read_text(encoding="utf-8", errors="replace")

    # Check for isPermanent method
    has_method = bool(re.search(r"function\s+isPermanent\s*\(\s*\)\s*:\s*bool", content, re.IGNORECASE))
    has_property = "$permanent" in content

    if has_method and has_property:
        print("PASS: NodeDeletedEvent declares $permanent property and isPermanent(): bool method.")
        return 0
    else:
        missing = []
        if not has_property:
            missing.append("property $permanent")
        if not has_method:
            missing.append("method isPermanent(): bool")
        sys.stderr.write(f"ACCEPTANCE_FAILURE: Missing {', '.join(missing)} in NodeDeletedEvent.php\n")
        return 1


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".")
    sys.exit(run_verification(root))
