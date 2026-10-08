"""
'polyflow lint' and 'polyflow fmt' Commands.

Lints and formats PolyFlow (.poly) files for syntax errors, missing @end tags,
malformed schema definitions, and style conventions.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Tuple

from polyflow_sdk.core.parser import PolyParser


def lint_poly_content(content: str, filename: str = "<source>") -> List[Tuple[int, str]]:
    """Check a .poly text content for syntax and structural errors. Returns (line_no, error_msg)."""
    errors: List[Tuple[int, str]] = []
    lines = content.splitlines()

    open_blocks = []  # stack of (directive, line_no)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("@"):
            if stripped == "@end":
                if not open_blocks:
                    errors.append((i, "Unexpected '@end' without matching opening directive."))
                else:
                    open_blocks.pop()
                continue

            # Directives that open a block
            m_lang = re.match(r"^@([a-zA-Z0-9_\-]+)(?:\[([a-zA-Z0-9_\-:]+)\])?\s*$", stripped)
            if m_lang and m_lang.group(1).lower() not in {"link"}:
                open_blocks.append((m_lang.group(1), i))
                continue

            if stripped.startswith("@schema"):
                if not re.match(r"^@schema\s+([a-zA-Z0-9_]+)\s*$", stripped):
                    errors.append((i, "Malformed '@schema' declaration. Expected '@schema <Name>'."))
                open_blocks.append(("schema", i))
                continue

            if stripped.startswith("@contract"):
                open_blocks.append(("contract", i))
                continue

            if stripped.startswith("@source"):
                open_blocks.append(("source", i))
                continue

            if stripped.startswith("@merge"):
                open_blocks.append(("merge", i))
                continue

            if stripped.startswith("@error-map"):
                open_blocks.append(("error-map", i))
                continue

            if stripped.startswith("@decision") or stripped.startswith("@rationale") or stripped.startswith("@standard") or stripped.startswith("@audit") or stripped.startswith("@ledger"):
                open_blocks.append((stripped.split()[0][1:], i))
                continue

    for dname, lno in open_blocks:
        errors.append((lno, f"Unclosed directive '@{dname}' (missing matching '@end')."))

    return errors


def execute_lint(target_path: str) -> int:
    path = Path(target_path).resolve()
    if not path.exists():
        print(f"Error: Path '{target_path}' does not exist.", file=sys.stderr)
        return 1

    files_to_check = [path] if path.is_file() else list(path.glob("**/*.poly"))
    if not files_to_check:
        print(f"No .poly files found under '{target_path}'.")
        return 0

    total_errors = 0
    print(f"[PolyFlow Linter] Checking {len(files_to_check)} file(s)...")

    for f in sorted(files_to_check):
        content = f.read_text(encoding="utf-8")
        errs = lint_poly_content(content, filename=str(f))
        if errs:
            total_errors += len(errs)
            for lno, msg in errs:
                print(f"  {f.name}:{lno}: ERROR: {msg}")

    if total_errors == 0:
        print(f"All {len(files_to_check)} file(s) passed linting with 0 errors.")
        return 0
    else:
        print(f"\nLint failed with {total_errors} error(s).", file=sys.stderr)
        return 1


def format_poly_content(content: str) -> str:
    """Standardize indentation, trim trailing whitespace, format directives."""
    lines = content.splitlines()
    formatted = []
    in_block = False

    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            formatted.append("")
            continue

        trimmed = stripped.strip()
        if trimmed.startswith("@"):
            if trimmed == "@end":
                formatted.append("@end")
                in_block = False
            else:
                formatted.append(trimmed)
                if not trimmed.startswith("@link"):
                    in_block = True
        else:
            if in_block:
                formatted.append("  " + trimmed)
            else:
                formatted.append(trimmed)

    return "\n".join(formatted).rstrip() + "\n"


def execute_fmt(target_path: str, write: bool = False) -> int:
    path = Path(target_path).resolve()
    if not path.exists():
        print(f"Error: Path '{target_path}' does not exist.", file=sys.stderr)
        return 1

    files_to_fmt = [path] if path.is_file() else list(path.glob("**/*.poly"))
    if not files_to_fmt:
        print(f"No .poly files found under '{target_path}'.")
        return 0

    for f in files_to_fmt:
        content = f.read_text(encoding="utf-8")
        new_content = format_poly_content(content)
        if write:
            f.write_text(new_content, encoding="utf-8")
            print(f"Formatted: {f.name}")
        else:
            if new_content != content:
                print(f"Would reformat: {f.name}")
            else:
                print(f"Already clean: {f.name}")

    return 0
