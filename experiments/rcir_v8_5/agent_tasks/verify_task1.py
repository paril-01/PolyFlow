#!/usr/bin/env python3
"""
Acceptance verification test for AGENT-TASK-01.
Verifies that ApiController::getThumbnail accepts $crop with default true
and passes $crop as the 4th argument to getPreview.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def strip_php_comments_and_strings(content: str) -> str:
    """Strips comments from PHP code while keeping string structure intact."""
    # Remove single line comments // ... and # ...
    # Be careful not to strip inside strings
    res = []
    i = 0
    n = len(content)
    while i < n:
        if content[i : i + 2] == "/*":
            end = content.find("*/", i + 2)
            if end == -1:
                break
            i = end + 2
            continue
        elif content[i : i + 2] == "//" or content[i] == "#":
            end = content.find("\n", i)
            if end == -1:
                break
            i = end + 1
            continue
        elif content[i] in ('"', "'"):
            quote = content[i]
            res.append(quote)
            i += 1
            while i < n and content[i] != quote:
                if content[i] == "\\" and i + 1 < n:
                    res.append("  ")
                    i += 2
                else:
                    res.append(" ")
                    i += 1
            if i < n:
                res.append(content[i])
                i += 1
            continue
        else:
            res.append(content[i])
            i += 1
    return "".join(res)



def extract_balanced_block(text: str, start_pos: int, open_char: str = "{", close_char: str = "}") -> Optional[Tuple[str, int, int]]:
    """Finds the first block delimited by open_char and close_char starting at or after start_pos."""
    first_open = text.find(open_char, start_pos)
    if first_open == -1:
        return None

    depth = 0
    in_single_quote = False
    in_double_quote = False
    i = first_open
    n = len(text)

    while i < n:
        char = text[i]
        if char == "\\" and (in_single_quote or in_double_quote):
            i += 2
            continue
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif not in_single_quote and not in_double_quote:
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0:
                    return text[first_open + 1 : i], first_open, i + 1
        i += 1
    return None


def parse_call_args(args_str: str) -> List[str]:
    """Parses top-level comma-separated arguments in a function call."""
    args: List[str] = []
    curr: List[str] = []
    depth_paren = 0
    depth_bracket = 0
    depth_brace = 0
    in_single = False
    in_double = False
    i = 0
    n = len(args_str)

    while i < n:
        c = args_str[i]
        if c == "\\" and (in_single or in_double):
            curr.append(args_str[i : i + 2])
            i += 2
            continue
        if c == "'" and not in_double:
            in_single = not in_single
            curr.append(c)
        elif c == '"' and not in_single:
            in_double = not in_double
            curr.append(c)
        elif not in_single and not in_double:
            if c == "(":
                depth_paren += 1
                curr.append(c)
            elif c == ")":
                depth_paren -= 1
                curr.append(c)
            elif c == "[":
                depth_bracket += 1
                curr.append(c)
            elif c == "]":
                depth_bracket -= 1
                curr.append(c)
            elif c == "{":
                depth_brace += 1
                curr.append(c)
            elif c == "}":
                depth_brace -= 1
                curr.append(c)
            elif c == "," and depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
                args.append("".join(curr).strip())
                curr = []
            else:
                curr.append(c)
        else:
            curr.append(c)
        i += 1

    if curr:
        args.append("".join(curr).strip())
    return args


def test_api_controller(repo_root: Path) -> int:
    target = repo_root / "apps" / "files" / "lib" / "Controller" / "ApiController.php"
    if not target.exists():
        sys.stderr.write(f"SETUP_ERROR: Target file does not exist: {target}\n")
        return 2

    raw_content = target.read_text(encoding="utf-8")
    if "function getThumbnail" not in raw_content:
        sys.stderr.write("SETUP_ERROR: function getThumbnail not found in ApiController.php\n")
        return 2

    # Strip comments to prevent commented-out code from passing checks
    clean_content = strip_php_comments_and_strings(raw_content)

    func_match = re.search(r'function\s+getThumbnail\s*\(', clean_content)
    if not func_match:
        sys.stderr.write("SETUP_ERROR: function getThumbnail signature not found in ApiController.php\n")
        return 2

    sig_paren_block = extract_balanced_block(clean_content, func_match.end() - 1, open_char="(", close_char=")")
    if not sig_paren_block:
        sys.stderr.write("SETUP_ERROR: Unable to parse getThumbnail signature parameter list\n")
        return 2

    sig_str, _, sig_end = sig_paren_block

    # 1. Structural check on signature: $crop must be in parameter list with default boolean true
    crop_match = re.search(r'\$crop\s*(=\s*([a-zA-Z0-9_]+))?', sig_str)
    if not crop_match:
        sys.stderr.write(f"ASSERTION_FAIL: getThumbnail signature does not include $crop. Signature: ({sig_str.strip()})\n")
        return 1

    default_val = crop_match.group(2)
    if not default_val or default_val.lower() != "true":
        sys.stderr.write(
            f"ASSERTION_FAIL: getThumbnail parameter $crop must default to true, found: {crop_match.group(0).strip()}\n"
        )
        return 1

    # 2. Extract getThumbnail method body using balanced braces
    body_block = extract_balanced_block(clean_content, sig_end, open_char="{", close_char="}")
    if not body_block:
        sys.stderr.write("SETUP_ERROR: Unable to extract getThumbnail method body\n")
        return 2

    body_str, _, _ = body_block

    # 3. Locate getPreview call inside getThumbnail method body
    preview_call_match = re.search(r'->getPreview\s*\(', body_str)
    if not preview_call_match:
        sys.stderr.write("ASSERTION_FAIL: getPreview call not found in getThumbnail body\n")
        return 1

    preview_args_block = extract_balanced_block(body_str, preview_call_match.end() - 1, open_char="(", close_char=")")
    if not preview_args_block:
        sys.stderr.write("ASSERTION_FAIL: Unable to parse getPreview arguments\n")
        return 1

    args_str, _, _ = preview_args_block
    args = parse_call_args(args_str)

    if len(args) != 4:
        sys.stderr.write(f"ASSERTION_FAIL: getPreview call must have exactly 4 arguments: {args}\n")
        return 1

    arg1 = args[0].strip()
    arg2 = args[1].strip()
    arg3 = args[2].strip()
    arg4 = args[3].strip()

    if arg1 != "$file":
        sys.stderr.write(f"ASSERTION_FAIL: 1st argument to getPreview must strictly be '$file'. Found: '{arg1}'\n")
        return 1
    if arg2 != "$x":
        sys.stderr.write(f"ASSERTION_FAIL: 2nd argument to getPreview must strictly be '$x'. Found: '{arg2}'\n")
        return 1
    if arg3 != "$y":
        sys.stderr.write(f"ASSERTION_FAIL: 3rd argument to getPreview must strictly be '$y'. Found: '{arg3}'\n")
        return 1
    if arg4 != "$crop":
        sys.stderr.write(f"ASSERTION_FAIL: 4th argument to getPreview must strictly be '$crop'. Found: '{arg4}'\n")
        return 1

    print("PASS: ApiController::getThumbnail correctly defines $crop = true and propagates to getPreview($file, $x, $y, $crop)")
    return 0



if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--worktree":
        root = Path(sys.argv[2]).resolve()
    elif len(sys.argv) > 1 and sys.argv[1] != "--worktree":
        root = Path(sys.argv[1]).resolve()
    else:
        root = Path(".").resolve()
    sys.exit(test_api_controller(root))
