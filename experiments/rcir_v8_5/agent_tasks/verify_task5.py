#!/usr/bin/env python3
"""
Acceptance verification test for AGENT-TASK-05.
Verifies that IUserSession interface declares hasActiveSession(): bool method.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def run_verification(worktree_root: Path) -> int:
    target_file = worktree_root / "lib" / "public" / "IUserSession.php"
    if not target_file.exists():
        sys.stderr.write(f"SETUP_ERROR: Target file not found: {target_file}\n")
        return 2

    content = target_file.read_text(encoding="utf-8", errors="replace")

    # Check for hasActiveSession(): bool declaration in interface
    pattern = r"function\s+hasActiveSession\s*\(\s*\)\s*:\s*bool\s*;"
    if re.search(pattern, content, re.IGNORECASE):
        print("PASS: IUserSession declares hasActiveSession(): bool method.")
        return 0
    else:
        sys.stderr.write("ACCEPTANCE_FAILURE: Missing method declaration 'public function hasActiveSession(): bool;' in IUserSession.php\n")
        return 1


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".")
    sys.exit(run_verification(root))
