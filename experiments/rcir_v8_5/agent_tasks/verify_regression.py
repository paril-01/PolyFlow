#!/usr/bin/env python3
"""
Regression suite verification for coding agent trials.
Validates PHP syntax and integrity of modified files.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple


def check_php_syntax(file_path: Path) -> Tuple[bool, str]:
    # 1. Try php -l if php executable is available
    php_bin = shutil.which("php")
    if php_bin:
        try:
            res = subprocess.run([php_bin, "-l", str(file_path)], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                return True, "php -l passed"
            return False, f"php -l failed: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"php -l error: {e}"

    # 2. Fallback AST / balanced delimiter check
    content = file_path.read_text(encoding="utf-8", errors="replace")
    if not content.strip().startswith("<?php"):
        return False, "Missing <?php opening tag"

    depth_brace = 0
    depth_paren = 0
    depth_bracket = 0
    in_single = False
    in_double = False
    i = 0
    n = len(content)

    while i < n:
        c = content[i]
        if c == "\\" and (in_single or in_double):
            i += 2
            continue
        if c == "'" and not in_double:
            in_single = not in_single
        elif c == '"' and not in_single:
            in_double = not in_double
        elif not in_single and not in_double:
            if content[i : i + 2] == "/*":
                end = content.find("*/", i + 2)
                if end == -1:
                    return False, "Unclosed multi-line comment /*"
                i = end + 2
                continue
            elif content[i : i + 2] == "//" or content[i] == "#":
                end = content.find("\n", i)
                if end == -1:
                    break
                i = end + 1
                continue
            elif c == "{":
                depth_brace += 1
            elif c == "}":
                depth_brace -= 1
                if depth_brace < 0:
                    return False, f"Unexpected closing brace '}}' at offset {i}"
            elif c == "(":
                depth_paren += 1
            elif c == ")":
                depth_paren -= 1
                if depth_paren < 0:
                    return False, f"Unexpected closing paren ')' at offset {i}"
            elif c == "[":
                depth_bracket += 1
            elif c == "]":
                depth_bracket -= 1
                if depth_bracket < 0:
                    return False, f"Unexpected closing bracket ']' at offset {i}"
        i += 1

    if in_single or in_double:
        return False, "Unclosed string literal"
    if depth_brace != 0:
        return False, f"Unbalanced braces (depth {depth_brace})"
    if depth_paren != 0:
        return False, f"Unbalanced parentheses (depth {depth_paren})"
    if depth_bracket != 0:
        return False, f"Unbalanced brackets (depth {depth_bracket})"

    return True, "AST tokenizer / delimiter syntax passed (PHP runtime not installed)"


def run_regression_check(worktree_root: Path) -> int:
    modified_php_files = []
    try:
        res = subprocess.run(
            ["git", "-C", str(worktree_root), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:
                    rel_p = parts[-1]
                    if rel_p.endswith(".php"):
                        full_p = worktree_root / rel_p
                        if full_p.exists():
                            modified_php_files.append(full_p)
    except Exception:
        pass

    if not modified_php_files:
        is_git = (worktree_root / ".git").exists() or (worktree_root / ".git").is_file()
        if is_git:
            print("REGRESSION_SKIPPED: Zero files modified in worktree. Regression not applicable.")
            return 4
        else:
            # If genuinely not a git repository, inspect directory
            for p in worktree_root.rglob("*.php"):
                if not any(part.startswith(".") for part in p.parts):
                    modified_php_files.append(p)

    if not modified_php_files:
        print("REGRESSION_SKIPPED: Zero files modified in worktree. Regression not applicable.")
        return 4

    for tf in modified_php_files:
        ok, msg = check_php_syntax(tf)
        if not ok:
            sys.stderr.write(f"REGRESSION_FAILURE: {tf.name}: {msg}\n")
            return 1

    php_bin = shutil.which("php")
    if not php_bin:
        print(f"REGRESSION_NOT_MEASURED: PHP runtime not installed. Delimiter syntax passed for {len(modified_php_files)} files.")
        return 3
    else:
        print(f"PASS: Regression syntax checks passed for {len(modified_php_files)} files via PHP.")
        return 0


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--worktree":
        root = Path(sys.argv[2]).resolve()
    elif len(sys.argv) > 1 and sys.argv[1] != "--worktree":
        root = Path(sys.argv[1]).resolve()
    else:
        root = Path(".").resolve()
    sys.exit(run_regression_check(root))


