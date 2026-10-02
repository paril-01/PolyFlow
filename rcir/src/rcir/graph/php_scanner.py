"""
PHP Source Code Scanner for RCIR (Heuristic Pattern Extractor).

Architectural Classification:
- This is a high-throughput, regex- and lexical pattern-based heuristic scanner,
  NOT a full semantic PHP compiler or complete type-inference engine.
- Designed for fast, zero-dependency static extraction of PHP classes, methods, traits,
  DI type-hints, and static/instance invocations across large codebases (>50k symbols)
  without requiring a full PHP runtime, Composer autoloader execution, or whole-program
  type solvers.

Extracted Structural Elements:
1. Classes, abstract classes, interfaces, traits, and enums
2. Namespaces and use/import declarations
3. Inheritance (extends) and interface realization (implements)
4. Static invocations (Class::method()) and lexical $this->method() calls
5. Dependency Injection container lookups (e.g. $c->get(Service::class))
6. Lexical parameter type hints and PHPDoc references

Explicit Limitations (Documented, not hidden):
- Heuristic pattern-based, not full AST semantic compiler: cannot perform interprocedural dataflow
- Cannot trace through variable reassignments (e.g., $svc = getService(); $svc->method())
- Cannot resolve dynamic invocations (e.g., $this->$dynamicMethod(), new $className())
- Cannot resolve string-based service identifiers without ::class or registered container bindings
- Does not execute PHP code or Composer autoloader logic

Anti-Fabrication & Zero-Cloud:
- Pure Python pattern parsing with zero external dependencies.
- Operates entirely locally with zero outbound network calls.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rcir.graph.edges import Edge, make_edge


# ─── Data Classes ──────────────────────────────────────────────────

@dataclass
class PHPClass:
    """A PHP class/interface/trait definition."""
    file_path: str
    name: str
    fqcn: str          # Fully Qualified Class Name (namespace\ClassName)
    kind: str           # "class" | "interface" | "trait" | "abstract_class" | "enum"
    namespace: str
    extends: list[str] = field(default_factory=list)
    implements: list[str] = field(default_factory=list)
    uses_traits: list[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class PHPMethod:
    """A PHP method definition."""
    file_path: str
    class_name: str
    method_name: str
    fqcn: str          # namespace\Class::method
    visibility: str     # "public" | "protected" | "private"
    is_static: bool = False
    is_abstract: bool = False
    param_types: list[str] = field(default_factory=list)
    return_type: str = ""
    line_number: int = 0


@dataclass
class PHPUseStatement:
    """A PHP use statement (import)."""
    file_path: str
    imported_fqcn: str  # The fully-qualified name being imported
    alias: str           # The local alias (last segment or explicit 'as' alias)
    line_number: int = 0


@dataclass
class PHPFunctionCall:
    """A detected PHP function/method call."""
    file_path: str
    caller_context: str  # The enclosing class::method or file-level
    callee: str          # What's being called
    call_type: str       # "method" | "static" | "function" | "new" | "di_container"
    line_number: int = 0
    raw_snippet: str = ""


# ─── Regex Patterns ────────────────────────────────────────────────

# Namespace declaration
_PHP_NAMESPACE = re.compile(
    r'^\s*namespace\s+([\w\\]+)\s*;',
    re.MULTILINE,
)

# Use statements (imports)
_PHP_USE = re.compile(
    r'^\s*use\s+([\w\\]+)(?:\s+as\s+(\w+))?\s*;',
    re.MULTILINE,
)

# Class/interface/trait/enum/abstract class declaration
_PHP_CLASS_DEF = re.compile(
    r'^\s*(?:(?:abstract|final)\s+)?'
    r'(class|interface|trait|enum)\s+'
    r'(\w+)'
    r'(?:\s+extends\s+([\w\\,\s]+?))?'
    r'(?:\s+implements\s+([\w\\,\s]+?))?'
    r'\s*\{',
    re.MULTILINE,
)

# Trait use inside class body
_PHP_TRAIT_USE = re.compile(
    r'^\s*use\s+([\w\\]+(?:\s*,\s*[\w\\]+)*)\s*[;{]',
    re.MULTILINE,
)

# Method declaration
_PHP_METHOD = re.compile(
    r'^\s*(?:(public|protected|private)\s+)?'
    r'(?:(static)\s+)?'
    r'(?:(abstract)\s+)?'
    r'function\s+(\w+)\s*\('
    r'([^)]*)\)'
    r'(?:\s*:\s*([\w\\?|]+))?',
    re.MULTILINE,
)

# Top-level function declaration (not inside a class)
_PHP_FUNCTION = re.compile(
    r'^\s*function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*([\w\\?|]+))?',
    re.MULTILINE,
)

# $this->method() calls
_PHP_THIS_CALL = re.compile(
    r'\$this\s*->\s*(\w+)\s*\(',
    re.MULTILINE,
)

# $var->method() calls (instance method calls)
_PHP_INSTANCE_CALL = re.compile(
    r'\$(\w+)\s*->\s*(\w+)\s*\(',
    re.MULTILINE,
)

# ClassName::staticMethod() calls
_PHP_STATIC_CALL = re.compile(
    r'([\w\\]+)\s*::\s*(\w+)\s*\(',
    re.MULTILINE,
)

# new ClassName() instantiation
_PHP_NEW = re.compile(
    r'new\s+([\w\\]+)\s*\(',
    re.MULTILINE,
)

# DI Container patterns: $container->get(ClassName::class)
_PHP_DI_CONTAINER = re.compile(
    r'(?:\$\w+|->)\s*(?:get|query|resolve|make|build)\s*\(\s*([\w\\]+)::class\s*\)',
    re.MULTILINE,
)

# Type hints in parameters: function foo(TypeName $param)
_PHP_TYPE_HINT = re.compile(
    r'(?:[\w\\?|]+\s+)\$\w+',
)

# PHPDoc type references
_PHP_DOC_TYPE = re.compile(
    r'@(?:param|return|var|throws)\s+([\w\\|?]+)',
    re.MULTILINE,
)

# require/include statements
_PHP_INCLUDE = re.compile(
    r'(?:require|include)(?:_once)?\s*\(?\s*[\'"]([^"\']+)[\'"]\s*\)?\s*;',
    re.MULTILINE,
)

# Nextcloud/Laravel route patterns (annotations in docblocks)
_PHP_ROUTE_ANNOTATION = re.compile(
    r'@(?:Route|OCSRoute|CORS|NoCSRFRequired|NoAdminRequired|PublicPage)\s*\(([^)]*)\)',
    re.MULTILINE,
)

# Nextcloud OCS API route in routes.php
_PHP_ROUTES_ARRAY = re.compile(
    r"'url'\s*=>\s*'([^']+)'.*?'verb'\s*=>\s*'([^']+)'",
    re.DOTALL,
)

# Event listener registration: addEventListener / addListener / listen
_PHP_EVENT_LISTENER = re.compile(
    r'(?:addEventListener|addListener|listen)\s*\(\s*([\w\\]+)(?:::class)?\s*,',
    re.MULTILINE,
)

# Event dispatch: dispatchEvent / dispatch / dispatchTyped
_PHP_EVENT_DISPATCH = re.compile(
    r'(?:dispatchEvent|dispatch|dispatchTyped)\s*\(\s*(?:new\s+)?([\w\\]+)',
    re.MULTILINE,
)


# ─── Helper Functions ──────────────────────────────────────────────

def _split_csv_types(type_str: str) -> list[str]:
    """Split a comma-separated list of type names, stripping whitespace."""
    if not type_str:
        return []
    return [t.strip() for t in type_str.split(',') if t.strip()]


def _get_enclosing_class_method(source: str, line_no: int) -> str:
    """Find the enclosing class::method context for a given line number."""
    lines = source.splitlines()[:line_no]
    current_class = ""
    current_method = ""

    for line in lines:
        class_match = _PHP_CLASS_DEF.search(line)
        if class_match:
            current_class = class_match.group(2)
            current_method = ""

        method_match = _PHP_METHOD.search(line)
        if method_match:
            current_method = method_match.group(4)

    if current_class and current_method:
        return f"{current_class}::{current_method}"
    elif current_class:
        return current_class
    return "file_level"


def _resolve_fqcn(short_name: str, namespace: str, use_map: dict[str, str]) -> str:
    """Resolve a short class name to a fully qualified class name using use statements."""
    # Already fully qualified
    if '\\' in short_name:
        return short_name.lstrip('\\')

    # Check use map
    if short_name in use_map:
        return use_map[short_name]

    # Same namespace
    if namespace:
        return f"{namespace}\\{short_name}"

    return short_name


# ─── Core Scanner ──────────────────────────────────────────────────

def scan_php_file(
    content: str,
    file_path: str,
) -> tuple[list[dict], list[Edge]]:
    """Scan a single PHP file for dependency information.

    Args:
        content: The file content as a string.
        file_path: Repo-relative path to the file.

    Returns:
        tuple of (nodes, edges) extracted from this file.
    """
    nodes: list[dict] = []
    edges: list[Edge] = []

    # Extract namespace
    ns_match = _PHP_NAMESPACE.search(content)
    namespace = ns_match.group(1) if ns_match else ""

    # Build use-statement map: alias -> FQCN
    use_map: dict[str, str] = {}
    for m in _PHP_USE.finditer(content):
        imported = m.group(1)
        alias = m.group(2) or imported.split('\\')[-1]
        use_map[alias] = imported

        line_no = content[:m.start()].count('\n') + 1
        edges.append(make_edge(
            source=file_path,
            target=imported,
            edge_type="imports",
            resolution="static_exact",
            reason=f"PHP use statement: use {imported}" + (f" as {alias}" if m.group(2) else ""),
        ))

    # Add file-level node
    nodes.append({
        "path": file_path,
        "kind": "file",
        "level": "file",
        "line": 1,
        "end_line": max(1, content.count('\n') + 1),
        "language": "php",
        "namespace": namespace,
    })

    # Extract class/interface/trait definitions
    classes_in_file: list[PHPClass] = []
    for m in _PHP_CLASS_DEF.finditer(content):
        kind_raw = m.group(1)  # class | interface | trait | enum
        name = m.group(2)
        extends_raw = m.group(3)
        implements_raw = m.group(4)

        # Check if abstract
        full_match_text = m.group(0)
        is_abstract = 'abstract' in full_match_text.split(kind_raw)[0]
        kind = "abstract_class" if is_abstract else kind_raw

        fqcn = f"{namespace}\\{name}" if namespace else name
        line_no = content[:m.start()].count('\n') + 1

        extends_list = _split_csv_types(extends_raw) if extends_raw else []
        implements_list = _split_csv_types(implements_raw) if implements_raw else []

        php_class = PHPClass(
            file_path=file_path,
            name=name,
            fqcn=fqcn,
            kind=kind,
            namespace=namespace,
            extends=extends_list,
            implements=implements_list,
            line_number=line_no,
        )
        classes_in_file.append(php_class)

        # Node
        node_path = f"{file_path}::{fqcn}"
        nodes.append({
            "path": node_path,
            "kind": kind,
            "level": "class",
            "line": line_no,
            "end_line": line_no,  # Approximate; regex can't determine class end
            "language": "php",
            "namespace": namespace,
        })

        # Inheritance edges
        for base in extends_list:
            resolved_base = _resolve_fqcn(base, namespace, use_map)
            edges.append(make_edge(
                source=node_path,
                target=resolved_base,
                edge_type="inherits",
                resolution="static_exact" if base in use_map or '\\' in base else "static_inference",
                reason=f"{name} extends {base}",
            ))

        # Implements edges
        for iface in implements_list:
            resolved_iface = _resolve_fqcn(iface, namespace, use_map)
            edges.append(make_edge(
                source=node_path,
                target=resolved_iface,
                edge_type="inherits",  # Using inherits for implements (closest available)
                resolution="static_exact" if iface in use_map or '\\' in iface else "static_inference",
                reason=f"{name} implements {iface}",
            ))

    # Extract trait usage inside classes
    # We need to be careful: 'use TraitName;' inside a class body vs namespace-level 'use'
    # The trait use pattern only matches inside class bodies (indented lines starting with 'use')
    for m in _PHP_TRAIT_USE.finditer(content):
        trait_line = m.group(0)
        # Skip if this looks like a namespace-level use statement (those have backslashes typically
        # and are caught above). Trait uses are typically short names.
        line_no = content[:m.start()].count('\n') + 1

        # Find the enclosing class
        enclosing = _get_enclosing_class_method(content, line_no)
        if enclosing == "file_level":
            continue  # This is probably a namespace use, not a trait use

        trait_names = _split_csv_types(m.group(1))
        for trait_name in trait_names:
            # Skip if it looks like a namespace import (contains backslash at root level)
            resolved = _resolve_fqcn(trait_name.strip(), namespace, use_map)
            source_path = f"{file_path}::{namespace}\\{enclosing}" if namespace else f"{file_path}::{enclosing}"
            edges.append(make_edge(
                source=source_path,
                target=resolved,
                edge_type="inherits",  # Trait use is similar to inheritance
                resolution="static_inference",
                reason=f"Trait use: {enclosing} uses {trait_name}",
            ))

    # Extract method definitions
    for m in _PHP_METHOD.finditer(content):
        visibility = m.group(1) or "public"
        is_static = m.group(2) is not None
        is_abstract = m.group(3) is not None
        method_name = m.group(4)
        params_raw = m.group(5)
        return_type = m.group(6) or ""

        line_no = content[:m.start()].count('\n') + 1
        enclosing_class = _get_enclosing_class_method(content, line_no).split('::')[0]

        if enclosing_class and enclosing_class != "file_level":
            fqcn = f"{namespace}\\{enclosing_class}" if namespace else enclosing_class
            method_path = f"{file_path}::{fqcn}::{method_name}"
        else:
            method_path = f"{file_path}::{method_name}"

        # Extract parameter type hints
        param_types = []
        if params_raw:
            for param_match in re.finditer(r'([\w\\?|]+)\s+\$\w+', params_raw):
                ptype = param_match.group(1)
                if ptype and ptype not in ('int', 'string', 'float', 'bool', 'array',
                                           'callable', 'iterable', 'object', 'mixed',
                                           'void', 'null', 'self', 'static', 'parent',
                                           '?int', '?string', '?float', '?bool', '?array'):
                    param_types.append(ptype)

        nodes.append({
            "path": method_path,
            "kind": "method",
            "level": "function",
            "line": line_no,
            "end_line": line_no,
            "language": "php",
            "visibility": visibility,
            "is_static": is_static,
            "is_abstract": is_abstract,
            "return_type": return_type,
        })

        # Type hint edges (parameter types reference other classes)
        for ptype in param_types:
            clean_type = ptype.lstrip('?').split('|')[0]
            resolved = _resolve_fqcn(clean_type, namespace, use_map)
            edges.append(make_edge(
                source=method_path,
                target=resolved,
                edge_type="imports",  # Type hint is a dependency
                resolution="static_exact" if clean_type in use_map else "static_inference",
                reason=f"Parameter type hint: {clean_type}",
            ))

        # Return type edge
        if return_type and return_type not in ('int', 'string', 'float', 'bool', 'array',
                                                'callable', 'iterable', 'object', 'mixed',
                                                'void', 'null', 'self', 'static', 'parent'):
            clean_ret = return_type.lstrip('?').split('|')[0]
            if clean_ret and clean_ret[0].isupper():
                resolved = _resolve_fqcn(clean_ret, namespace, use_map)
                edges.append(make_edge(
                    source=method_path,
                    target=resolved,
                    edge_type="imports",
                    resolution="static_exact" if clean_ret in use_map else "static_inference",
                    reason=f"Return type hint: {clean_ret}",
                ))

    # Extract $this->method() calls
    for m in _PHP_THIS_CALL.finditer(content):
        method_name = m.group(1)
        line_no = content[:m.start()].count('\n') + 1
        caller = _get_enclosing_class_method(content, line_no)
        if caller == "file_level":
            continue

        caller_class = caller.split('::')[0]
        fqcn = f"{namespace}\\{caller_class}" if namespace else caller_class
        source = f"{file_path}::{fqcn}::{caller.split('::')[-1]}" if '::' in caller else f"{file_path}::{fqcn}"
        target = f"{fqcn}::{method_name}"

        edges.append(make_edge(
            source=source,
            target=target,
            edge_type="calls",
            resolution="static_inference",
            reason=f"$this->{method_name}() call",
        ))

    # Extract ClassName::staticMethod() calls
    for m in _PHP_STATIC_CALL.finditer(content):
        class_name = m.group(1)
        method_name = m.group(2)
        line_no = content[:m.start()].count('\n') + 1
        caller = _get_enclosing_class_method(content, line_no)

        # Skip self:: and parent:: and static:: — these are intra-class
        if class_name in ('self', 'parent', 'static'):
            caller_class = caller.split('::')[0] if '::' in caller else caller
            if caller_class != "file_level":
                fqcn = f"{namespace}\\{caller_class}" if namespace else caller_class
                target = f"{fqcn}::{method_name}"
            else:
                continue
        else:
            resolved = _resolve_fqcn(class_name, namespace, use_map)
            target = f"{resolved}::{method_name}"

        source_ctx = f"{file_path}::{namespace}\\{caller}" if namespace and caller != "file_level" else f"{file_path}::{caller}"
        resolution = "static_exact" if class_name in use_map else "static_inference"

        edges.append(make_edge(
            source=source_ctx,
            target=target,
            edge_type="calls",
            resolution=resolution,
            reason=f"{class_name}::{method_name}() static call",
        ))

    # Extract new ClassName() instantiation
    for m in _PHP_NEW.finditer(content):
        class_name = m.group(1)
        if class_name in ('self', 'static', 'parent'):
            continue

        line_no = content[:m.start()].count('\n') + 1
        caller = _get_enclosing_class_method(content, line_no)
        resolved = _resolve_fqcn(class_name, namespace, use_map)
        source_ctx = f"{file_path}::{namespace}\\{caller}" if namespace and caller != "file_level" else f"{file_path}::{caller}"

        edges.append(make_edge(
            source=source_ctx,
            target=resolved,
            edge_type="calls",
            resolution="static_exact" if class_name in use_map or '\\' in class_name else "static_inference",
            reason=f"new {class_name}() instantiation",
        ))

    # Extract DI container lookups: $container->get(ClassName::class)
    for m in _PHP_DI_CONTAINER.finditer(content):
        class_name = m.group(1)
        line_no = content[:m.start()].count('\n') + 1
        caller = _get_enclosing_class_method(content, line_no)
        resolved = _resolve_fqcn(class_name, namespace, use_map)
        source_ctx = f"{file_path}::{namespace}\\{caller}" if namespace and caller != "file_level" else f"{file_path}::{caller}"

        edges.append(make_edge(
            source=source_ctx,
            target=resolved,
            edge_type="calls",
            resolution="static_exact",
            reason=f"DI container lookup: {class_name}::class",
        ))

    # Extract event listener registrations
    for m in _PHP_EVENT_LISTENER.finditer(content):
        event_class = m.group(1)
        line_no = content[:m.start()].count('\n') + 1
        caller = _get_enclosing_class_method(content, line_no)
        resolved = _resolve_fqcn(event_class, namespace, use_map)
        source_ctx = f"{file_path}::{namespace}\\{caller}" if namespace and caller != "file_level" else f"{file_path}::{caller}"

        edges.append(make_edge(
            source=source_ctx,
            target=resolved,
            edge_type="calls",
            resolution="static_exact" if event_class in use_map else "static_inference",
            reason=f"Event listener for {event_class}",
        ))

    # Extract event dispatches
    for m in _PHP_EVENT_DISPATCH.finditer(content):
        event_class = m.group(1)
        line_no = content[:m.start()].count('\n') + 1
        caller = _get_enclosing_class_method(content, line_no)
        resolved = _resolve_fqcn(event_class, namespace, use_map)
        source_ctx = f"{file_path}::{namespace}\\{caller}" if namespace and caller != "file_level" else f"{file_path}::{caller}"

        edges.append(make_edge(
            source=source_ctx,
            target=resolved,
            edge_type="calls",
            resolution="static_exact" if event_class in use_map else "static_inference",
            reason=f"Event dispatch: {event_class}",
        ))

    # Extract require/include
    for m in _PHP_INCLUDE.finditer(content):
        included_path = m.group(1)
        line_no = content[:m.start()].count('\n') + 1

        edges.append(make_edge(
            source=file_path,
            target=included_path,
            edge_type="imports",
            resolution="static_inference",
            reason=f"PHP include/require: {included_path}",
        ))

    return nodes, edges


def scan_php_repo(
    repo_path: Path | str,
    exclude_dirs: set[str] | None = None,
) -> tuple[list[dict], list[Edge]]:
    """Scan an entire repository for PHP source files and extract dependencies.

    Args:
        repo_path: Root of the repository.
        exclude_dirs: Set of directory names to skip.

    Returns:
        tuple of (nodes, edges)
    """
    repo = Path(repo_path).resolve()
    skip_dirs = {
        ".git", "node_modules", "vendor", "bin", "obj", "__pycache__",
        "venv", ".venv", "build", "dist", ".idea", ".vscode", "target",
        "cache", ".cache",
    }
    if exclude_dirs:
        skip_dirs.update(exclude_dirs)

    all_nodes: list[dict] = []
    all_edges: list[Edge] = []
    files_parsed = 0
    files_failed = 0

    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        for f in files:
            if not f.endswith('.php'):
                continue

            file_p = Path(root) / f
            try:
                rel_path = file_p.relative_to(repo).as_posix()
                content = file_p.read_text(encoding='utf-8', errors='replace')
                nodes, edges = scan_php_file(content, rel_path)
                all_nodes.extend(nodes)
                all_edges.extend(edges)
                files_parsed += 1
            except Exception:
                files_failed += 1
                continue

    return all_nodes, all_edges
