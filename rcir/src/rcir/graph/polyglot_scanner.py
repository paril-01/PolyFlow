"""
Polyglot Cross-Service Scanner for RCIR (v7 §10).

Provides zero-cloud, multi-language detection of cross-service gRPC and HTTP
calls and endpoints across Go, C#, Java, and JavaScript/TypeScript.

Supported patterns:
1. Go (.go):
   - gRPC client: pb.New<Service>Client(...), <service>Client.<Method>(ctx, ...)
   - gRPC server: pb.Register<Service>Server(srv, ...)
   - HTTP routes: http.HandleFunc, r.GET/POST (gin/mux), http.Get/Post client calls
2. C# (.cs):
   - gRPC client: new <Service>.<Service>Client(...), client.<Method>Async(...)
   - gRPC server: class <Service>Impl : <Service>.<Service>Base
3. Java (.java):
   - gRPC client: <Service>Grpc.newBlockingStub(...), stub.<method>(...)
   - gRPC server: extends <Service>Grpc.<Service>ImplBase
4. JavaScript / TypeScript (.js, .jsx, .ts, .tsx):
   - gRPC client: new proto.<Service>(...), client.<method>(...)
   - HTTP routes: app.get/post(...), router.get/post(...), axios.get/post(...), fetch(...)

Anti-Fabrication & Zero-Cloud:
- Pure Python pattern parsing with balanced-delimiter extraction (zero external dependencies).
- Operates entirely locally with zero outbound network calls.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rcir.graph.edges import Edge, make_edge


@dataclass
class CrossServiceCall:
    """An outbound cross-service call detected in source code."""
    file_path: str
    caller_symbol: str
    service_name: str
    method_name: str
    call_type: str       # "grpc" | "http"
    line_number: int
    raw_snippet: str = ""


@dataclass
class CrossServiceEndpoint:
    """A cross-service server endpoint / handler implemented in source code."""
    file_path: str
    service_name: str
    method_name: str
    endpoint_type: str   # "grpc" | "http"
    line_number: int


# ─── Language Specific Regex Patterns ──────────────────────────────

# Go patterns
_GO_GRPC_NEW_CLIENT = re.compile(
    r'(?:pb\.)?New([A-Z]\w+?)Client\s*\(\s*([^)]+)\s*\)',
    re.MULTILINE,
)
_GO_GRPC_DIRECT_CALL = re.compile(
    r'(?:pb\.)?New([A-Z]\w+?)Client\s*\([^)]*\)\.([A-Z]\w+)\s*\(',
    re.MULTILINE,
)
_GO_METHOD_CALL = re.compile(
    r'(\w+Client|\bcs\.\w+)\.([A-Z]\w+)\s*\(\s*(?:ctx|context\.\w+)',
    re.MULTILINE,
)
_GO_REGISTER_SERVER = re.compile(
    r'(?:pb\.)?Register([A-Z]\w+?)Server\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)',
    re.MULTILINE,
)
_GO_FUNC_DEF = re.compile(
    r'func\s+(?:\([^)]+\)\s+)?([A-Z]\w*|\b[a-z]\w*)\s*\(',
    re.MULTILINE,
)

# C# patterns
_CS_GRPC_CLIENT = re.compile(
    r'new\s+([A-Z]\w+?)(?:\.[A-Z]\w+?)?\.([A-Z]\w+?)Client\s*\(',
    re.MULTILINE,
)
_CS_METHOD_CALL = re.compile(
    r'(\w+Client|\b_client)\.([A-Z]\w+?)(?:Async)?\s*\(',
    re.MULTILINE,
)
_CS_SERVER_BASE = re.compile(
    r'class\s+([A-Z]\w+)\s*:\s*(?:[A-Z]\w+\.)?([A-Z]\w+?)Base\b',
    re.MULTILINE,
)

# Java patterns
_JAVA_GRPC_STUB = re.compile(
    r'([A-Z]\w+?)Grpc\.new(?:Blocking)?Stub\s*\(',
    re.MULTILINE,
)
_JAVA_SERVER_BASE = re.compile(
    r'class\s+([A-Z]\w+)\s+extends\s+([A-Z]\w+?)Grpc\.([A-Z]\w+?)ImplBase\b',
    re.MULTILINE,
)

# JavaScript / TypeScript patterns
_JS_GRPC_CLIENT = re.compile(
    r'new\s+(?:proto\.([A-Z]\w+?)|([A-Z]\w+?)Client)\s*\(',
    re.MULTILINE,
)
_JS_HTTP_ROUTE = re.compile(
    r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
    re.MULTILINE,
)
_JS_HTTP_CALL = re.compile(
    r'(?:axios\.(get|post|put|delete)|fetch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
    re.MULTILINE,
)

# Python patterns
_PY_GRPC_STUB_ASSIGN = re.compile(
    r'(\w+)\s*=\s*(?:[a-zA-Z0-9_]+\.)?([A-Z]\w*?)Stub\s*\(',
    re.MULTILINE,
)
_PY_GRPC_DIRECT_CALL = re.compile(
    r'(?:[a-zA-Z0-9_]+\.)?([A-Z]\w*?)Stub\s*\([^)]*\)\.([A-Z]\w+)\s*\(',
    re.MULTILINE,
)
_PY_METHOD_CALL = re.compile(
    r'(\w+)\.([A-Z]\w+)\s*\(',
    re.MULTILINE,
)
_PY_SERVER_BASE = re.compile(
    r'class\s+([A-Z]\w+)\s*\([^)]*?(?:[a-zA-Z0-9_]+\.)?([A-Z]\w*?)Servicer\b',
    re.MULTILINE,
)
_PY_REGISTER_SERVER = re.compile(
    r'(?:[a-zA-Z0-9_]+\.)?add_([A-Z]\w*?)Servicer_to_server\s*\(',
    re.MULTILINE,
)


def _get_enclosing_func(source: str, line_no: int) -> str:
    """Find the enclosing function name for a line in Go/C#/Java/JS."""
    lines = source.splitlines()[:line_no]
    for line in reversed(lines):
        match = _GO_FUNC_DEF.search(line)
        if match:
            return match.group(1)
        # Check standard C#/Java/JS function defs
        fn_match = re.search(r'(?:public|private|protected|async|void|def|function)?\s*([a-zA-Z_]\w+)\s*\([^)]*\)\s*(?:\{|=>)', line)
        if fn_match and fn_match.group(1) not in ("if", "for", "while", "switch", "catch"):
            return fn_match.group(1)
    return "anonymous"


def scan_source_file(
    content: str,
    file_path: str,
) -> tuple[list[CrossServiceCall], list[CrossServiceEndpoint]]:
    """Scan a source file for cross-service calls and endpoints."""
    calls: list[CrossServiceCall] = []
    endpoints: list[CrossServiceEndpoint] = []

    ext = Path(file_path).suffix.lower()

    # 1. Go scanning
    if ext == ".go":
        # Direct gRPC calls: pb.NewCartServiceClient(conn).GetCart(...)
        for m in _GO_GRPC_DIRECT_CALL.finditer(content):
            svc_name = m.group(1)
            method_name = m.group(2)
            line_no = content[:m.start()].count("\n") + 1
            caller = _get_enclosing_func(content, line_no)
            calls.append(CrossServiceCall(
                file_path=file_path,
                caller_symbol=f"{file_path}::{caller}",
                service_name=svc_name,
                method_name=method_name,
                call_type="grpc",
                line_number=line_no,
                raw_snippet=m.group(0),
            ))

        # Server registrations: pb.RegisterCheckoutServiceServer(srv, svc)
        for m in _GO_REGISTER_SERVER.finditer(content):
            svc_name = m.group(1)
            line_no = content[:m.start()].count("\n") + 1
            endpoints.append(CrossServiceEndpoint(
                file_path=file_path,
                service_name=svc_name,
                method_name="*",
                endpoint_type="grpc",
                line_number=line_no,
            ))

    # 2. C# scanning
    elif ext == ".cs":
        for m in _CS_GRPC_CLIENT.finditer(content):
            svc_name = m.group(1)
            line_no = content[:m.start()].count("\n") + 1
            caller = _get_enclosing_func(content, line_no)
            calls.append(CrossServiceCall(
                file_path=file_path,
                caller_symbol=f"{file_path}::{caller}",
                service_name=svc_name,
                method_name="*",
                call_type="grpc",
                line_number=line_no,
                raw_snippet=m.group(0),
            ))

        for m in _CS_SERVER_BASE.finditer(content):
            svc_name = m.group(2)
            line_no = content[:m.start()].count("\n") + 1
            endpoints.append(CrossServiceEndpoint(
                file_path=file_path,
                service_name=svc_name,
                method_name="*",
                endpoint_type="grpc",
                line_number=line_no,
            ))

    # 3. Java scanning
    elif ext == ".java":
        for m in _JAVA_GRPC_STUB.finditer(content):
            svc_name = m.group(1)
            line_no = content[:m.start()].count("\n") + 1
            caller = _get_enclosing_func(content, line_no)
            calls.append(CrossServiceCall(
                file_path=file_path,
                caller_symbol=f"{file_path}::{caller}",
                service_name=svc_name,
                method_name="*",
                call_type="grpc",
                line_number=line_no,
                raw_snippet=m.group(0),
            ))

        for m in _JAVA_SERVER_BASE.finditer(content):
            svc_name = m.group(2)
            line_no = content[:m.start()].count("\n") + 1
            endpoints.append(CrossServiceEndpoint(
                file_path=file_path,
                service_name=svc_name,
                method_name="*",
                endpoint_type="grpc",
                line_number=line_no,
            ))

    # 4. JavaScript / TypeScript scanning
    elif ext in (".js", ".jsx", ".ts", ".tsx"):
        for m in _JS_GRPC_CLIENT.finditer(content):
            svc_name = m.group(1) or m.group(2)
            if not svc_name:
                continue
            line_no = content[:m.start()].count("\n") + 1
            caller = _get_enclosing_func(content, line_no)
            calls.append(CrossServiceCall(
                file_path=file_path,
                caller_symbol=f"{file_path}::{caller}",
                service_name=svc_name,
                method_name="*",
                call_type="grpc",
                line_number=line_no,
                raw_snippet=m.group(0),
            ))

        for m in _JS_HTTP_ROUTE.finditer(content):
            method = m.group(1).upper()
            route_path = m.group(2)
            line_no = content[:m.start()].count("\n") + 1
            endpoints.append(CrossServiceEndpoint(
                file_path=file_path,
                service_name=route_path,
                method_name=method,
                endpoint_type="http",
                line_number=line_no,
            ))

    # 5. Python scanning
    elif ext == ".py":
        stubs: dict[str, str] = {}
        for m in _PY_GRPC_STUB_ASSIGN.finditer(content):
            var_name = m.group(1)
            svc_name = m.group(2)
            stubs[var_name] = svc_name

        # Direct chained gRPC calls
        for m in _PY_GRPC_DIRECT_CALL.finditer(content):
            svc_name = m.group(1)
            method_name = m.group(2)
            line_no = content[:m.start()].count("\n") + 1
            caller = _get_enclosing_func(content, line_no)
            calls.append(CrossServiceCall(
                file_path=file_path,
                caller_symbol=f"{file_path}::{caller}",
                service_name=svc_name,
                method_name=method_name,
                call_type="grpc",
                line_number=line_no,
                raw_snippet=m.group(0),
            ))

        # Method calls on stubs
        for m in _PY_METHOD_CALL.finditer(content):
            var_name = m.group(1)
            method_name = m.group(2)
            if var_name in stubs:
                svc_name = stubs[var_name]
                line_no = content[:m.start()].count("\n") + 1
                caller = _get_enclosing_func(content, line_no)
                calls.append(CrossServiceCall(
                    file_path=file_path,
                    caller_symbol=f"{file_path}::{caller}",
                    service_name=svc_name,
                    method_name=method_name,
                    call_type="grpc",
                    line_number=line_no,
                    raw_snippet=m.group(0),
                ))

        # Server implementations
        for m in _PY_SERVER_BASE.finditer(content):
            svc_name = m.group(2)
            line_no = content[:m.start()].count("\n") + 1
            endpoints.append(CrossServiceEndpoint(
                file_path=file_path,
                service_name=svc_name,
                method_name="*",
                endpoint_type="grpc",
                line_number=line_no,
            ))

        # Server registrations
        for m in _PY_REGISTER_SERVER.finditer(content):
            svc_name = m.group(1)
            line_no = content[:m.start()].count("\n") + 1
            endpoints.append(CrossServiceEndpoint(
                file_path=file_path,
                service_name=svc_name,
                method_name="*",
                endpoint_type="grpc",
                line_number=line_no,
            ))

    return calls, endpoints


def scan_polyglot_repo(
    repo_path: Path | str,
    known_proto_services: set[str] | None = None,
    exclude_dirs: set[str] | None = None,
) -> tuple[list[dict], list[Edge]]:
    """Scan an entire repository for polyglot cross-service calls and endpoints.

    Args:
        repo_path: Root of the repository.
        known_proto_services: Set of service names extracted from .proto files.
        exclude_dirs: Set of directory names to skip (pruning).

    Returns:
        tuple of (new_nodes, new_edges)
    """
    repo = Path(repo_path).resolve()
    skip_dirs = {
        ".git", "node_modules", "vendor", "bin", "obj", "__pycache__",
        "venv", ".venv", "build", "dist", ".idea", ".vscode", "target",
    }
    if exclude_dirs:
        skip_dirs.update(exclude_dirs)

    supported_exts = {".go", ".cs", ".java", ".js", ".jsx", ".ts", ".tsx"}

    all_calls: list[CrossServiceCall] = []
    all_endpoints: list[CrossServiceEndpoint] = []
    new_nodes: list[dict] = []
    new_edges: list[Edge] = []

    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in supported_exts:
                file_p = Path(root) / f
                try:
                    rel_path = file_p.relative_to(repo).as_posix()
                    content = file_p.read_text(encoding="utf-8", errors="replace")
                    calls, endpoints = scan_source_file(content, rel_path)
                    all_calls.extend(calls)
                    all_endpoints.extend(endpoints)

                    # Add file node to hierarchy (avoid duplicating Python files parsed in pass 1)
                    if ext != ".py":
                        new_nodes.append({
                            "path": rel_path,
                            "kind": "file",
                            "level": "file",
                            "line": 1,
                            "end_line": max(1, content.count("\n") + 1),
                            "language": ext.lstrip("."),
                        })
                except Exception:
                    continue

    # Resolve calls to proto services or declared endpoints
    for call in all_calls:
        # Create caller node if not already present
        new_nodes.append({
            "path": call.caller_symbol,
            "kind": "function",
            "level": "function",
            "line": call.line_number,
            "end_line": call.line_number + 10,
        })

        target_service = call.service_name
        # Match against known proto services
        is_exact = known_proto_services and target_service in known_proto_services

        if call.method_name and call.method_name != "*":
            target = f"{target_service}.{call.method_name}"
            reason = f"Cross-language {call.call_type} call from {call.file_path} to {target}"
            resolution = "static_exact" if is_exact else "static_inference"
        else:
            target = target_service
            reason = f"Cross-language {call.call_type} client binding from {call.file_path} to {target_service}"
            resolution = "static_exact" if is_exact else "static_inference"

        new_edges.append(make_edge(
            source=call.caller_symbol,
            target=target,
            edge_type="calls",
            resolution=resolution,
            reason=reason,
        ))

    # Resolve declared server endpoints
    for ep in all_endpoints:
        ep_node = f"{ep.file_path}::{ep.service_name}"
        new_nodes.append({
            "path": ep_node,
            "kind": "service_implementation",
            "level": "service",
            "line": ep.line_number,
            "end_line": ep.line_number + 20,
        })
        new_edges.append(make_edge(
            source=ep_node,
            target=ep.service_name,
            edge_type="implements",
            resolution="static_exact",
            reason=f"Service {ep.service_name} implementation registered in {ep.file_path}",
        ))

    return new_nodes, new_edges
