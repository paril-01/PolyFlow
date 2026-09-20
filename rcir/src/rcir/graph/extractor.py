"""
AST-based dependency graph extractor for Python repositories.

Walks a repository, parses every .py file via ast.parse, extracts:
- Nodes: functions, methods, classes with qualified paths
- Edges: calls, imports, inheritance with confidence tagging

This is the foundational component — everything else (hierarchy, invalidation,
retrieval) depends on the graph this module produces.

CLI: python -m rcir.graph.extractor <repo_path> --output <path.json>
"""

import ast
import json
import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Any

from rcir.graph.edges import Edge, make_edge, EdgeType, ResolutionType


def _repo_relative_path(file_path: Path, repo_root: Path) -> str:
    """Convert absolute file path to repo-relative POSIX path."""
    try:
        return file_path.relative_to(repo_root).as_posix()
    except ValueError:
        return file_path.as_posix()


def _qualified_name(rel_path: str, *parts: str) -> str:
    """Build a qualified node name: 'path/to/file.py::ClassName.method_name'."""
    base = rel_path
    if parts:
        return f"{base}::{'.'.join(parts)}"
    return base


class _SymbolCollector(ast.NodeVisitor):
    """First pass: collect all defined symbols (functions, classes, methods)
    so we can resolve call targets in the second pass."""

    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.nodes: list[dict] = []
        self._class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        class_name = node.name
        qname = _qualified_name(self.rel_path, *self._class_stack, class_name)
        self.nodes.append({
            "path": qname,
            "kind": "class",
            "level": "class",
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "bases": [self._resolve_base_name(b) for b in node.bases],
        })
        self._class_stack.append(class_name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        func_name = node.name
        qname = _qualified_name(self.rel_path, *self._class_stack, func_name)
        kind = "method" if self._class_stack else "function"

        # Extract signature for interface state
        args_info = self._extract_args(node)
        return_annotation = ast.dump(node.returns) if node.returns else None
        decorators = [self._decorator_name(d) for d in node.decorator_list]

        self.nodes.append({
            "path": qname,
            "kind": kind,
            "level": "function",
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "args": args_info,
            "return_annotation": return_annotation,
            "decorators": decorators,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        })
        # Don't recurse into nested functions/classes from here — we want
        # them as their own nodes, but the visitor will handle that via
        # generic_visit on the class, not here.
        # However, we DO need to recurse to catch nested classes/functions.
        self.generic_visit(node)

    def _extract_args(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict]:
        """Extract argument names and annotations."""
        result = []
        for arg in node.args.args:
            result.append({
                "name": arg.arg,
                "annotation": ast.dump(arg.annotation) if arg.annotation else None,
            })
        return result

    def _decorator_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.dump(node)
        elif isinstance(node, ast.Call):
            return self._decorator_name(node.func)
        return ast.dump(node)

    def _resolve_base_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.dump(node)
        return ast.dump(node)


class _EdgeCollector(ast.NodeVisitor):
    """Second pass: extract edges (calls, imports, inheritance) with
    confidence/resolution tagging."""

    def __init__(self, rel_path: str, known_symbols: set[str]):
        self.rel_path = rel_path
        self.known_symbols = known_symbols
        self.edges: list[Edge] = []
        self._scope_stack: list[str] = []  # current function/class scope
        self._class_stack: list[str] = []
        # Track imports for resolution
        self._imports: dict[str, str] = {}  # alias -> module path

    def visit_Import(self, node: ast.Import):
        source = _qualified_name(self.rel_path, *self._scope_stack) if self._scope_stack else self.rel_path
        for alias in node.names:
            target_module = alias.name
            local_name = alias.asname or alias.name.split(".")[-1]
            self._imports[local_name] = target_module
            self.edges.append(make_edge(
                source=source,
                target=target_module,
                edge_type="imports",
                resolution="static_exact",
            ))

    def visit_ImportFrom(self, node: ast.ImportFrom):
        source = _qualified_name(self.rel_path, *self._scope_stack) if self._scope_stack else self.rel_path
        module = node.module or ""
        for alias in (node.names or []):
            target = f"{module}.{alias.name}" if module else alias.name
            local_name = alias.asname or alias.name
            self._imports[local_name] = target
            self.edges.append(make_edge(
                source=source,
                target=target,
                edge_type="imports",
                resolution="static_exact",
            ))

    def visit_ClassDef(self, node: ast.ClassDef):
        class_qname = _qualified_name(self.rel_path, *self._class_stack, node.name)

        # Inheritance edges
        for base in node.bases:
            base_name = self._resolve_name(base)
            if base_name:
                # Check if we can resolve the base to a known symbol
                resolution = self._classify_resolution(base_name)
                self.edges.append(make_edge(
                    source=class_qname,
                    target=base_name,
                    edge_type="inherits",
                    resolution=resolution,
                ))

        self._class_stack.append(node.name)
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_func_edges(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_func_edges(node)

    def _visit_func_edges(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_Call(self, node: ast.Call):
        source = _qualified_name(self.rel_path, *self._scope_stack) if self._scope_stack else self.rel_path

        target_name, resolution = self._resolve_call_target(node)
        if target_name:
            self.edges.append(make_edge(
                source=source,
                target=target_name,
                edge_type="calls",
                resolution=resolution,
            ))

        # Continue visiting arguments (they may contain nested calls)
        self.generic_visit(node)

    def _resolve_call_target(self, node: ast.Call) -> tuple[str | None, ResolutionType]:
        """Resolve a call node to a target name and resolution type.

        - Direct name call (foo()) → static_exact if known, static_inference otherwise
        - Attribute call (obj.method()) → static_inference (we infer, can't be sure)
        - getattr / dynamic → dynamic_unresolved
        """
        func = node.func

        if isinstance(func, ast.Name):
            name = func.id
            # Check if it's a known symbol or import
            if name in self._imports:
                return self._imports[name], "static_exact"
            # Check if it's a known symbol in the repo
            resolution = self._classify_resolution(name)
            return name, resolution

        elif isinstance(func, ast.Attribute):
            # obj.method() — we can get the attribute name but not
            # definitively resolve which class's method it is
            attr = func.attr
            # Try to resolve the object
            obj_name = self._resolve_name(func.value)
            if obj_name:
                full_target = f"{obj_name}.{attr}"
                return full_target, "static_inference"
            return attr, "static_inference"

        elif isinstance(func, ast.Call):
            # chained call: foo()() — resolve the inner call
            inner_target, _ = self._resolve_call_target(func)
            if inner_target:
                return f"{inner_target}()", "dynamic_unresolved"

        # getattr, subscript, or other dynamic patterns
        return None, "dynamic_unresolved"

    def _resolve_name(self, node: ast.expr) -> str | None:
        """Try to get a string name from an expression node."""
        if isinstance(node, ast.Name):
            name = node.id
            if name in self._imports:
                return self._imports[name]
            return name
        elif isinstance(node, ast.Attribute):
            obj = self._resolve_name(node.value)
            if obj:
                return f"{obj}.{node.attr}"
            return node.attr
        return None

    def _classify_resolution(self, name: str) -> ResolutionType:
        """Classify how confidently we resolved a name."""
        # If the name matches a known symbol in the repo graph, it's exact
        if name in self.known_symbols:
            return "static_exact"
        # If it's an imported name, it's exact
        if name in self._imports:
            return "static_exact"
        # Otherwise it's inference (could be a builtin, a local, etc.)
        return "static_inference"


def extract_graph(repo_path: str | Path) -> dict[str, Any]:
    """Extract a dependency graph from a Python repository.

    Args:
        repo_path: Path to the repository root.

    Returns:
        Dict with keys: nodes (list), edges (list), metadata (dict).
        Every node has a unique 'path' key. Edges connect node paths.
    """
    repo_path = Path(repo_path).resolve()
    if not repo_path.is_dir():
        raise ValueError(f"Not a directory: {repo_path}")

    # Collect all .py files, skipping common non-source directories
    skip_dirs = {
        ".git", ".hg", ".svn", "__pycache__", ".mypy_cache", ".pytest_cache",
        "node_modules", ".tox", ".nox", ".eggs", "*.egg-info", "venv", ".venv",
        "env", ".env", "build", "dist",
    }

    py_files: list[Path] = []
    for root, dirs, files in os.walk(repo_path):
        # Prune skipped directories
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.endswith(".egg-info")]
        for f in files:
            if f.endswith(".py"):
                py_files.append(Path(root) / f)

    # First pass: collect all symbols across the repo
    all_nodes: list[dict] = []
    all_symbol_names: set[str] = set()
    file_collectors: dict[str, _SymbolCollector] = {}

    for py_file in py_files:
        rel_path = _repo_relative_path(py_file, repo_path)
        try:
            source_code = py_file.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source_code, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError) as e:
            # Skip files that can't be parsed — don't fail the whole extraction
            continue

        collector = _SymbolCollector(rel_path)
        collector.visit(tree)
        file_collectors[rel_path] = collector

        for node in collector.nodes:
            all_nodes.append(node)
            all_symbol_names.add(node["path"])
            # Also add the short name for resolution
            short_name = node["path"].split("::")[-1] if "::" in node["path"] else node["path"]
            all_symbol_names.add(short_name)

    # Second pass: extract edges with resolution against known symbols
    all_edges: list[Edge] = []

    for py_file in py_files:
        rel_path = _repo_relative_path(py_file, repo_path)
        try:
            source_code = py_file.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source_code, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        edge_collector = _EdgeCollector(rel_path, all_symbol_names)
        edge_collector.visit(tree)
        all_edges.extend(edge_collector.edges)

    # Deduplicate edges (same source→target→type)
    seen_edges: set[tuple] = set()
    unique_edges: list[Edge] = []
    for edge in all_edges:
        key = (edge.source, edge.target, edge.edge_type)
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(edge)

    return {
        "nodes": all_nodes,
        "edges": [e.to_dict() for e in unique_edges],
        "metadata": {
            "repo_path": str(repo_path),
            "files_parsed": len(file_collectors),
            "files_skipped": len(py_files) - len(file_collectors),
            "total_nodes": len(all_nodes),
            "total_edges": len(unique_edges),
        },
    }


def main():
    """CLI entry point: python -m rcir.graph.extractor <repo_path> --output <path>"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract dependency graph from a Python repository"
    )
    parser.add_argument("repo_path", help="Path to the repository root")
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output JSON file path (default: stdout)"
    )
    args = parser.parse_args()

    graph = extract_graph(args.repo_path)

    output_json = json.dumps(graph, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        meta = graph["metadata"]
        print(
            f"Extracted {meta['total_nodes']} nodes, {meta['total_edges']} edges "
            f"from {meta['files_parsed']} files -> {args.output}"
        )
    else:
        print(output_json)


if __name__ == "__main__":
    main()
