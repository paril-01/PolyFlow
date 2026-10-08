#!/usr/bin/env python3
"""
Acceptance verification test for AGENT-TASK-03.
Verifies that IShare interface declares hasId(): bool method.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def run_verification(worktree_root: Path) -> int:
    target_file = worktree_root / "lib" / "public" / "Share" / "IShare.php"
    if not target_file.exists():
        sys.stderr.write(f"SETUP_ERROR: Target file not found: {target_file}\n")
        return 2

    content = target_file.read_text(encoding="utf-8", errors="replace")

    # Check for hasId(): bool declaration in interface
    pattern = r"function\s+hasId\s*\(\s*\)\s*:\s*bool\s*;"
    if re.search(pattern, content, re.IGNORECASE):
        print("PASS: IShare declares hasId(): bool method.")
        return 0
    else:
        sys.stderr.write("ACCEPTANCE_FAILURE: Missing method declaration 'public function hasId(): bool;' in IShare.php\n")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--worktree":
        root = Path(sys.argv[2]).resolve()
    elif len(sys.argv) > 1 and sys.argv[1] != "--worktree":
        root = Path(sys.argv[1]).resolve()
    else:
        root = Path(".").resolve()
    sys.exit(run_verification(root))
