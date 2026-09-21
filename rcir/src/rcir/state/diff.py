"""
State-split diff computation — the core of RCIR's incremental invalidation.

Computes three independent diffs per function/class node:
1. Interface diff: signature, args, return type, decorators, exports
2. Behavioral diff: AST-normalized body hash (ignoring whitespace/comments)
3. Data-contract diff: SQL strings, schema literals in function bodies

The key insight (§5): body-only changes don't propagate beyond the immediate
parent, while interface/data-contract changes propagate upward through the
full blast radius. This is what makes invalidation cheap for the common case.

CLI: python -m rcir.state.diff --before <path_or_sha> --after <path_or_sha> --path <repo>
"""

import ast
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


@dataclass
class NodeDiff:
    """Result of comparing a node between two versions."""
    node_path: str
    interface_status: Literal["unchanged", "changed"]
    body_status: Literal["unchanged", "changed"]
    data_contract_status: Literal["unchanged", "changed", "n/a"] = "n/a"

    # Detail fields for debugging/auditing
    interface_details: dict[str, Any] | None = None
    body_hash_before: str | None = None
    body_hash_after: str | None = None
    data_contract_details: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        d = {
            "node_path": self.node_path,
            "interface_status": self.interface_status,
            "body_status": self.body_status,
            "data_contract_status": self.data_contract_status,
        }
        if self.interface_details:
            d["interface_details"] = self.interface_details
        if self.body_hash_before or self.body_hash_after:
            d["body_hash_before"] = self.body_hash_before
            d["body_hash_after"] = self.body_hash_after
        if self.data_contract_details:
            d["data_contract_details"] = self.data_contract_details
        return d


# ─── Interface extraction ───────────────────────────────────────────

def _extract_interface(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict:
    """Extract the interface (signature) of a function/method node.

    Interface = everything a caller depends on:
    - Name
    - Arguments (names, annotations, defaults count)
    - Return annotation
    - Decorators
    """
    args = node.args

    arg_list = []
    for arg in args.args:
        arg_list.append({
            "name": arg.arg,
            "annotation": ast.dump(arg.annotation) if arg.annotation else None,
        })

    # *args
    vararg = None
    if args.vararg:
        vararg = {
            "name": args.vararg.arg,
            "annotation": ast.dump(args.vararg.annotation) if args.vararg.annotation else None,
        }

    # **kwargs
    kwarg = None
    if args.kwarg:
        kwarg = {
            "name": args.kwarg.arg,
            "annotation": ast.dump(args.kwarg.annotation) if args.kwarg.annotation else None,
        }

    # Keyword-only args
    kwonly = []
    for arg in args.kwonlyargs:
        kwonly.append({
            "name": arg.arg,
            "annotation": ast.dump(arg.annotation) if arg.annotation else None,
        })

    # Positional defaults apply to the trailing N entries of args.args —
    # align them so a changed default value (e.g. code=302 -> code=303) is
    # visible even though the *count* and *names* of defaults are unchanged.
    # Bug found by testing against a real Flask commit (redirect() default
    # code changed 302->303, a real interface-relevant behavior change) —
    # the old defaults_count-only field was blind to this class of edit.
    n_pos_defaults = len(args.defaults)
    default_values = [ast.dump(d) for d in args.defaults]
    positional_defaults = {}
    if n_pos_defaults:
        defaulted_arg_names = [a.arg for a in args.args[-n_pos_defaults:]]
        positional_defaults = dict(zip(defaulted_arg_names, default_values))

    kw_default_values = {
        arg.arg: (ast.dump(default) if default is not None else None)
        for arg, default in zip(args.kwonlyargs, args.kw_defaults)
    }

    return {
        "name": node.name,
        "args": arg_list,
        "vararg": vararg,
        "kwarg": kwarg,
        "kwonlyargs": kwonly,
        "defaults_count": len(args.defaults),
        "kw_defaults_count": len([d for d in args.kw_defaults if d is not None]),
        "positional_defaults": positional_defaults,
        "kw_defaults": kw_default_values,
        "return_annotation": ast.dump(node.returns) if node.returns else None,
        "decorators": [ast.dump(d) for d in node.decorator_list],
        "is_async": isinstance(node, ast.AsyncFunctionDef),
    }


def _extract_class_interface(node: ast.ClassDef) -> dict:
    """Extract the interface of a class node.

    Interface = class name, bases, decorators, and public method signatures.
    """
    return {
        "name": node.name,
        "bases": [ast.dump(b) for b in node.bases],
        "keywords": [(kw.arg, ast.dump(kw.value)) for kw in node.keywords],
        "decorators": [ast.dump(d) for d in node.decorator_list],
    }


# ─── Body hashing ──────────────────────────────────────────────────

def _normalize_body_ast(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Create a normalized AST dump of the function body.

    Normalizes:
    - Removes line numbers and column offsets
    - Removes docstrings (they're documentation, not behavior)
    - Removes comments (already stripped by ast.parse)

    The result is a string that changes only when the actual logic changes.
    """
    body = list(node.body)

    # Remove leading docstring if present
    if (body and isinstance(body[0], ast.Expr) and
            isinstance(body[0].value, ast.Constant) and
            isinstance(body[0].value.value, str)):
        body = body[1:]

    if not body:
        return "EMPTY_BODY"

    # Create a clean module to dump
    wrapper = ast.Module(body=body, type_ignores=[])

    # ast.dump produces a canonical string representation
    # that ignores source formatting differences
    return ast.dump(wrapper)


def _hash_body(normalized: str) -> str:
    """SHA-256 hash of the normalized body string."""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


# ─── Data contract detection ───────────────────────────────────────

# Patterns that suggest data contracts in function bodies
_SQL_PATTERNS = [
    re.compile(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s', re.IGNORECASE),
    re.compile(r'\b(CREATE\s+TABLE|ALTER\s+TABLE)\b', re.IGNORECASE),
]

_SCHEMA_PATTERNS = [
    re.compile(r'Schema\s*\('),          # marshmallow, etc.
    re.compile(r'Column\s*\('),          # SQLAlchemy
    re.compile(r'Field\s*\('),           # Pydantic, Django
    re.compile(r'ForeignKey\s*\('),      # Django/SQLAlchemy
    re.compile(r'relationship\s*\('),    # SQLAlchemy
    re.compile(r'db\.Model'),            # Flask-SQLAlchemy
]


def _extract_data_contracts(source_code: str) -> list[str]:
    """Extract data contract indicators from source code.

    Returns a list of matched patterns (for change detection).
    Empty list means no data contracts detected → 'n/a' status.
    """
    contracts = []
    for pattern in _SQL_PATTERNS + _SCHEMA_PATTERNS:
        matches = pattern.findall(source_code)
        contracts.extend(matches)
    return contracts


def _hash_contracts(contracts: list[str]) -> str | None:
    """Hash the sorted list of data contracts for comparison."""
    if not contracts:
        return None
    canonical = "\n".join(sorted(contracts))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


# ─── File-level diffing ────────────────────────────────────────────

class _FunctionFinder(ast.NodeVisitor):
    """Find all function/class definitions in a parsed AST."""

    def __init__(self):
        self.functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        self.classes: dict[str, ast.ClassDef] = {}
        self._class_stack: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._register_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._register_func(node)

    def _register_func(self, node):
        prefix = ".".join(self._class_stack) + "." if self._class_stack else ""
        key = f"{prefix}{node.name}"
        self.functions[key] = node
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        prefix = ".".join(self._class_stack) + "." if self._class_stack else ""
        key = f"{prefix}{node.name}"
        self.classes[key] = node
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()


def diff_file(
    before_source: str,
    after_source: str,
    file_path: str,
) -> list[NodeDiff]:
    """Compute state-split diffs for all functions/classes in a file.

    Args:
        before_source: Source code of the file before the change.
        after_source: Source code of the file after the change.
        file_path: Relative path of the file (for qualified names).

    Returns:
        List of NodeDiff objects, one per changed function/class.
    """
    try:
        before_tree = ast.parse(before_source)
        after_tree = ast.parse(after_source)
    except SyntaxError:
        # Can't parse → treat entire file as changed
        return [NodeDiff(
            node_path=file_path,
            interface_status="changed",
            body_status="changed",
            data_contract_status="changed",
        )]

    before_finder = _FunctionFinder()
    before_finder.visit(before_tree)
    after_finder = _FunctionFinder()
    after_finder.visit(after_tree)

    diffs: list[NodeDiff] = []

    # Check all functions present in either version
    all_func_names = set(before_finder.functions.keys()) | set(after_finder.functions.keys())

    for func_name in sorted(all_func_names):
        qname = f"{file_path}::{func_name}"

        before_func = before_finder.functions.get(func_name)
        after_func = after_finder.functions.get(func_name)

        if before_func is None or after_func is None:
            # Function added or removed — interface changed
            diffs.append(NodeDiff(
                node_path=qname,
                interface_status="changed",
                body_status="changed",
                data_contract_status="changed",
            ))
            continue

        # Interface diff
        before_iface = _extract_interface(before_func)
        after_iface = _extract_interface(after_func)
        interface_changed = before_iface != after_iface

        # Body diff
        before_body_norm = _normalize_body_ast(before_func)
        after_body_norm = _normalize_body_ast(after_func)
        before_hash = _hash_body(before_body_norm)
        after_hash = _hash_body(after_body_norm)
        body_changed = before_hash != after_hash

        # Data-contract diff
        before_body_src = ast.get_source_segment(before_source, before_func) or ""
        after_body_src = ast.get_source_segment(after_source, after_func) or ""
        before_contracts = _extract_data_contracts(before_body_src)
        after_contracts = _extract_data_contracts(after_body_src)
        before_contract_hash = _hash_contracts(before_contracts)
        after_contract_hash = _hash_contracts(after_contracts)

        if before_contract_hash is None and after_contract_hash is None:
            dc_status = "n/a"
        elif before_contract_hash == after_contract_hash:
            dc_status = "unchanged"
        else:
            dc_status = "changed"

        # Only report nodes that actually changed
        if interface_changed or body_changed or dc_status == "changed":
            details = None
            if interface_changed:
                details = {
                    "before": before_iface,
                    "after": after_iface,
                }

            dc_details = None
            if dc_status == "changed":
                dc_details = {
                    "before_contracts": before_contracts,
                    "after_contracts": after_contracts,
                }

            diffs.append(NodeDiff(
                node_path=qname,
                interface_status="changed" if interface_changed else "unchanged",
                body_status="changed" if body_changed else "unchanged",
                data_contract_status=dc_status,
                interface_details=details,
                body_hash_before=before_hash,
                body_hash_after=after_hash,
                data_contract_details=dc_details,
            ))

    # Check classes
    all_class_names = set(before_finder.classes.keys()) | set(after_finder.classes.keys())
    for class_name in sorted(all_class_names):
        qname = f"{file_path}::{class_name}"
        before_cls = before_finder.classes.get(class_name)
        after_cls = after_finder.classes.get(class_name)

        if before_cls is None or after_cls is None:
            diffs.append(NodeDiff(
                node_path=qname,
                interface_status="changed",
                body_status="changed",
                data_contract_status="changed",
            ))
            continue

        before_ciface = _extract_class_interface(before_cls)
        after_ciface = _extract_class_interface(after_cls)
        if before_ciface != after_ciface:
            diffs.append(NodeDiff(
                node_path=qname,
                interface_status="changed",
                body_status="unchanged",
                data_contract_status="n/a",
                interface_details={"before": before_ciface, "after": after_ciface},
            ))

    return diffs


def diff_repo_versions(
    repo_path: str | Path,
    before_sha: str,
    after_sha: str,
) -> list[NodeDiff]:
    """Compare two git commits and compute state-split diffs for changed files.

    Args:
        repo_path: Path to the git repository.
        before_sha: Git SHA (or ref) for the "before" version.
        after_sha: Git SHA (or ref) for the "after" version.

    Returns:
        List of NodeDiff objects for all changed functions/classes.
    """
    import subprocess

    repo_path = Path(repo_path).resolve()

    # Get list of changed .py files
    result = subprocess.run(
        ["git", "diff", "--name-only", before_sha, after_sha],
        cwd=repo_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"git diff failed: {result.stderr}")

    changed_files = [
        f.strip() for f in result.stdout.strip().split("\n")
        if f.strip() and f.strip().endswith(".py")
    ]

    all_diffs: list[NodeDiff] = []

    for file_path in changed_files:
        # Get before content
        before_result = subprocess.run(
            ["git", "show", f"{before_sha}:{file_path}"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        before_source = before_result.stdout if before_result.returncode == 0 and before_result.stdout else ""

        # Get after content
        after_result = subprocess.run(
            ["git", "show", f"{after_sha}:{file_path}"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        after_source = after_result.stdout if after_result.returncode == 0 and after_result.stdout else ""

        if before_source == after_source:
            continue

        file_diffs = diff_file(before_source, after_source, file_path)
        all_diffs.extend(file_diffs)

    return all_diffs


def main():
    """CLI: python -m rcir.state.diff --before <sha> --after <sha> --path <repo>"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute state-split diffs between code versions"
    )
    parser.add_argument("--before", required=True, help="Before SHA or ref (e.g., abc123~1)")
    parser.add_argument("--after", required=True, help="After SHA or ref (e.g., abc123)")
    parser.add_argument("--path", required=True, help="Path to the git repository")
    args = parser.parse_args()

    diffs = diff_repo_versions(args.path, args.before, args.after)

    output = {
        "before": args.before,
        "after": args.after,
        "repo": args.path,
        "diffs": [d.to_dict() for d in diffs],
        "summary": {
            "total_changed_nodes": len(diffs),
            "interface_changes": sum(1 for d in diffs if d.interface_status == "changed"),
            "body_only_changes": sum(
                1 for d in diffs
                if d.body_status == "changed" and d.interface_status == "unchanged"
            ),
            "data_contract_changes": sum(1 for d in diffs if d.data_contract_status == "changed"),
        },
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
