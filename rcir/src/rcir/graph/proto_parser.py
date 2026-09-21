"""
Regex-based .proto file parser for cross-service edge resolution (v7 §10, Tier 1).

Extracts service definitions, RPC methods, and message types from .proto files
without requiring the protobuf compiler — zero external dependencies, consistent
with the zero-cloud design (§3).

Limitations (documented, not hidden):
- Does not handle nested messages or extensions
- Does not resolve imports between .proto files
- Does not handle map types or oneof
- Regex-based, not a full grammar parser — may miss edge cases with unusual
  formatting or comments containing proto-like syntax

These limitations are acceptable for Tier 1: the goal is to extract service/method
definitions that can be matched to Python gRPC client stubs. A full protobuf
compiler integration is a Tier 2+ concern.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProtoField:
    """A field within a protobuf message."""
    name: str
    type: str
    number: int
    repeated: bool = False
    optional: bool = False


@dataclass
class ProtoMessage:
    """A protobuf message definition."""
    name: str
    fields: list[ProtoField] = field(default_factory=list)
    file_path: str = ""  # which .proto file this was defined in


@dataclass
class ProtoRPC:
    """A single RPC method within a service."""
    name: str
    request_type: str
    response_type: str
    client_streaming: bool = False
    server_streaming: bool = False


@dataclass
class ProtoService:
    """A protobuf service definition."""
    name: str
    methods: list[ProtoRPC] = field(default_factory=list)
    file_path: str = ""  # which .proto file this was defined in


@dataclass
class ProtoParseResult:
    """Result of parsing one or more .proto files."""
    services: list[ProtoService] = field(default_factory=list)
    messages: list[ProtoMessage] = field(default_factory=list)
    files_parsed: int = 0
    files_failed: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "services": [
                {
                    "name": s.name,
                    "file_path": s.file_path,
                    "methods": [
                        {
                            "name": m.name,
                            "request_type": m.request_type,
                            "response_type": m.response_type,
                            "client_streaming": m.client_streaming,
                            "server_streaming": m.server_streaming,
                        }
                        for m in s.methods
                    ],
                }
                for s in self.services
            ],
            "messages": [
                {
                    "name": m.name,
                    "file_path": m.file_path,
                    "fields": [
                        {
                            "name": f.name,
                            "type": f.type,
                            "number": f.number,
                            "repeated": f.repeated,
                            "optional": f.optional,
                        }
                        for f in m.fields
                    ],
                }
                for m in self.messages
            ],
            "files_parsed": self.files_parsed,
            "files_failed": self.files_failed,
            "errors": self.errors,
        }


def _strip_comments(text: str) -> str:
    """Remove // and /* */ style comments from proto source."""
    # Remove block comments first
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Remove line comments
    text = re.sub(r'//[^\n]*', '', text)
    return text


# Regex patterns for proto syntax — RPC and message patterns work fine,
# but service bodies contain nested {} from RPC definitions, so we use
# a balanced-brace extractor instead of a flat regex for services.

_RPC_PATTERN = re.compile(
    r'rpc\s+(\w+)\s*\(\s*(stream\s+)?(\w+)\s*\)\s*returns\s*\(\s*(stream\s+)?(\w+)\s*\)',
    re.DOTALL,
)

_MESSAGE_PATTERN = re.compile(
    r'message\s+(\w+)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
    re.DOTALL,
)

_FIELD_PATTERN = re.compile(
    r'(repeated\s+|optional\s+)?(\w+(?:\.\w+)*)\s+(\w+)\s*=\s*(\d+)',
)

_SERVICE_START = re.compile(r'service\s+(\w+)\s*\{')


def _extract_brace_block(text: str, open_pos: int) -> str | None:
    """Extract the content between balanced braces starting at open_pos.

    open_pos must point to the opening '{'. Returns the content between
    the braces (exclusive), or None if braces are unbalanced.
    """
    if open_pos >= len(text) or text[open_pos] != '{':
        return None
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[open_pos + 1: i]
    return None


def _find_services(text: str) -> list[tuple[str, str]]:
    """Find all service definitions using balanced-brace extraction.

    Returns list of (service_name, service_body) tuples.
    """
    results = []
    for match in _SERVICE_START.finditer(text):
        service_name = match.group(1)
        brace_pos = match.end() - 1  # position of the '{'
        body = _extract_brace_block(text, brace_pos)
        if body is not None:
            results.append((service_name, body))
    return results


def parse_proto_content(content: str, file_path: str = "") -> ProtoParseResult:
    """Parse a single .proto file's content.

    Args:
        content: The raw text of a .proto file.
        file_path: Path to the file (for attribution in results).

    Returns:
        ProtoParseResult with extracted services and messages.
    """
    result = ProtoParseResult(files_parsed=1)
    cleaned = _strip_comments(content)

    # Extract services using balanced-brace extraction (handles nested {} from RPCs)
    for service_name, service_body in _find_services(cleaned):

        methods = []
        for rpc_match in _RPC_PATTERN.finditer(service_body):
            methods.append(ProtoRPC(
                name=rpc_match.group(1),
                request_type=rpc_match.group(3),
                response_type=rpc_match.group(5),
                client_streaming=rpc_match.group(2) is not None,
                server_streaming=rpc_match.group(4) is not None,
            ))

        result.services.append(ProtoService(
            name=service_name,
            methods=methods,
            file_path=file_path,
        ))

    # Extract messages
    for msg_match in _MESSAGE_PATTERN.finditer(cleaned):
        msg_name = msg_match.group(1)
        msg_body = msg_match.group(2)

        fields = []
        for field_match in _FIELD_PATTERN.finditer(msg_body):
            modifier = (field_match.group(1) or "").strip()
            fields.append(ProtoField(
                name=field_match.group(3),
                type=field_match.group(2),
                number=int(field_match.group(4)),
                repeated=modifier == "repeated",
                optional=modifier == "optional",
            ))

        result.messages.append(ProtoMessage(
            name=msg_name,
            fields=fields,
            file_path=file_path,
        ))

    return result


def parse_proto_files(repo_path: str | Path) -> ProtoParseResult:
    """Find and parse all .proto files in a repository.

    Args:
        repo_path: Path to the repository root.

    Returns:
        Aggregated ProtoParseResult across all .proto files.
    """
    repo_path = Path(repo_path).resolve()
    combined = ProtoParseResult()

    skip_dirs = {".git", "node_modules", "__pycache__", "venv", ".venv", "build", "dist"}
    proto_files: list[Path] = []

    for root, dirs, files in __import__("os").walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            if f.endswith(".proto"):
                proto_files.append(Path(root) / f)

    for proto_file in proto_files:
        try:
            content = proto_file.read_text(encoding="utf-8", errors="replace")
            rel_path = proto_file.relative_to(repo_path).as_posix()
            result = parse_proto_content(content, file_path=rel_path)
            combined.services.extend(result.services)
            combined.messages.extend(result.messages)
            combined.files_parsed += 1
        except Exception as e:
            combined.files_failed += 1
            combined.errors.append(f"{proto_file}: {e}")

    return combined


def proto_edges_from_parse_result(
    parse_result: ProtoParseResult,
) -> list[dict]:
    """Convert proto service definitions into dependency graph edges.

    Each RPC method creates edges:
    - service -> request message type (the service consumes the request)
    - service -> response message type (the service produces the response)

    These are static_exact edges — protobuf definitions are unambiguous.
    """
    edges = []
    message_names = {m.name for m in parse_result.messages}

    for service in parse_result.services:
        for method in service.methods:
            service_node = f"{service.file_path}::{service.name}.{method.name}"

            # Edge to request type
            if method.request_type in message_names:
                edges.append({
                    "source": service_node,
                    "target": method.request_type,
                    "target_message": method.request_type,
                    "edge_type": "calls",
                    "resolution": "static_exact",
                    "reason": f"gRPC method {method.name} takes {method.request_type} as request",
                })

            # Edge to response type
            if method.response_type in message_names:
                edges.append({
                    "source": service_node,
                    "target": method.response_type,
                    "target_message": method.response_type,
                    "edge_type": "calls",
                    "resolution": "static_exact",
                    "reason": f"gRPC method {method.name} returns {method.response_type} as response",
                })

    return edges
