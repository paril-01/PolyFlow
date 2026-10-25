"""
Graph Entity Source Resolver (Checkpoint G1 / P0-01, P0-02, P0-03).

Resolves canonical graph entities, symbols, and paths to validated source files
and concrete line spans within the target repository worktree.
Fail-closed on path traversal, missing files, or unbacked entity stubs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import re
from typing import Any, Optional


class EntityResolutionError(Exception):
    """Raised when an entity cannot be resolved to a validated source location."""
    pass


class PathTraversalError(EntityResolutionError):
    """Raised when an entity or path attempts directory traversal outside repo root."""
    pass


@dataclass
class SourceLocation:
    """Validated concrete location of an entity in the repository source tree."""
    entity_id: str
    relative_path: str
    absolute_path: Path
    sha256: str
    start_line: int
    end_line: int
    resolution_class: str  # 'exact_node_file', 'ast_resolved', 'fallback_inferred'
    graph_hash: str = ""
    target_sha: str = ""
    is_exact_match: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "relative_path": self.relative_path,
            "absolute_path": str(self.absolute_path),
            "sha256": self.sha256,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "resolution_class": self.resolution_class,
            "graph_hash": self.graph_hash,
            "target_sha": self.target_sha,
            "is_exact_match": self.is_exact_match,
            "metadata": self.metadata,
        }


@dataclass
class UnresolvedLocation:
    """Explicit typed failure when an entity cannot be bound to source."""
    entity_id: str
    reason: str
    candidate_paths: list[str] = field(default_factory=list)


class GraphEntitySourceResolver:
    """
    Binds graph entities to concrete, validated source locations in the repository.
    Handles graph nodes stored as either lists or dicts, and handles various entity naming schemes
    (PHP namespaces, URI schemes like php:// or ts://, path::symbol, and relative file paths).
    """

    def __init__(
        self,
        repo_root: Path | str,
        raw_graph: dict[str, Any] | None = None,
        graph_hash: str = "",
        target_sha: str = "",
    ):
        self.repo_root = Path(repo_root).resolve()
        self.raw_graph = raw_graph or {"nodes": [], "edges": []}
        self.graph_hash = graph_hash
        self.target_sha = target_sha

        # Build index for fast lookup:
        # 1. entity_id -> node_dict
        # 2. file_path -> list[node_dict]
        # 3. symbol_name -> list[node_dict]
        self.nodes_by_id: dict[str, dict[str, Any]] = {}
        self.nodes_by_path: dict[str, list[dict[str, Any]]] = {}
        self.nodes_by_symbol: dict[str, list[dict[str, Any]]] = {}

        self._build_indexes()

    def _build_indexes(self) -> None:
        nodes = self.raw_graph.get("nodes", [])
        if isinstance(nodes, dict):
            iterable_nodes = [
                dict(n, **{"_node_key": k}) if isinstance(n, dict) else {"_node_key": k}
                for k, n in nodes.items()
            ]
        elif isinstance(nodes, list):
            iterable_nodes = [n for n in nodes if isinstance(n, dict)]
        else:
            iterable_nodes = []

        for node in iterable_nodes:
            node_key = node.get("_node_key") or node.get("id") or node.get("path") or ""
            node_path = node.get("path") or node.get("file") or ""

            # Register by direct keys
            if node_key:
                self.nodes_by_id[node_key] = node
            if node_path and node_path not in self.nodes_by_id:
                self.nodes_by_id[node_path] = node

            # Extract base file path (strip ::symbol if present)
            base_file = node_path.split("::")[0].replace("\\", "/")
            if base_file:
                self.nodes_by_path.setdefault(base_file, []).append(node)

            # Register symbols
            symbol = node.get("name") or node.get("symbol")
            if not symbol and "::" in node_path:
                symbol = node_path.split("::")[-1]
            if symbol:
                self.nodes_by_symbol.setdefault(symbol, []).append(node)
                # Also index short unqualified symbol
                short = symbol.split("\\")[-1]
                if short != symbol:
                    self.nodes_by_symbol.setdefault(short, []).append(node)

    def _sanitize_and_validate_path(self, rel_path: str) -> Path:
        """
        Validates that rel_path is safe, strictly within repo_root, and free of traversal.
        """
        # Reject traversal attempts
        normalized = rel_path.replace("\\", "/").strip()
        if ".." in normalized.split("/"):
            raise PathTraversalError(f"Path traversal blocked: '{rel_path}' contains parent directory references")

        if normalized.startswith("/") or re.match(r"^[a-zA-Z]:", normalized):
            # Absolute path check: must still be within repo_root
            candidate_abs = Path(normalized).resolve()
        else:
            candidate_abs = (self.repo_root / normalized).resolve()

        try:
            candidate_abs.relative_to(self.repo_root)
        except ValueError:
            raise PathTraversalError(f"Path escape blocked: '{candidate_abs}' is outside repo_root '{self.repo_root}'")

        return candidate_abs

    def resolve(self, entity_or_symbol: str) -> SourceLocation | UnresolvedLocation:
        """
        Resolves an entity ID or symbol to a concrete, validated SourceLocation.
        Returns UnresolvedLocation if it cannot be found.
        """
        clean_target = entity_or_symbol.strip()
        # Strip scheme prefixes like php://, ts://, py://
        for prefix in ("php://", "ts://", "py://", "js://"):
            if clean_target.startswith(prefix):
                clean_target = clean_target[len(prefix):]
                break

        # Check path traversal on raw input early
        if ".." in clean_target.replace("\\", "/").split("/"):
            raise PathTraversalError(f"Path traversal detected in entity: {entity_or_symbol}")

        # 1. Direct node match in graph
        matched_node = None
        exact_match = False

        if clean_target in self.nodes_by_id:
            matched_node = self.nodes_by_id[clean_target]
            exact_match = True
        elif entity_or_symbol in self.nodes_by_id:
            matched_node = self.nodes_by_id[entity_or_symbol]
            exact_match = True

        # 2. Check path index
        if not matched_node:
            base_file = clean_target.split("::")[0].replace("\\", "/")
            if base_file in self.nodes_by_path:
                nodes_in_file = self.nodes_by_path[base_file]
                if len(clean_target.split("::")) > 1:
                    symbol_part = clean_target.split("::")[-1]
                    for n in nodes_in_file:
                        n_path = (n.get("path") or n.get("file") or "")
                        if symbol_part in n_path or n.get("name") == symbol_part:
                            matched_node = n
                            exact_match = True
                            break
                if not matched_node and nodes_in_file:
                    matched_node = nodes_in_file[0]

        # 3. Check symbol index
        if not matched_node:
            sym_part = clean_target.split("::")[-1].split("\\")[-1]
            if sym_part in self.nodes_by_symbol:
                matched_node = self.nodes_by_symbol[sym_part][0]

        # 4. Fallback: check if clean_target is itself a file on disk
        target_file_rel = ""
        node_meta = matched_node or {}

        if matched_node:
            node_path = node_meta.get("path") or node_meta.get("file") or ""
            target_file_rel = node_path.split("::")[0].replace("\\", "/")
        else:
            # Maybe clean_target itself points directly to a file
            candidate_rel = clean_target.split("::")[0].replace("\\", "/")
            if (self.repo_root / candidate_rel).is_file():
                target_file_rel = candidate_rel

        if not target_file_rel:
            return UnresolvedLocation(
                entity_id=entity_or_symbol,
                reason="No matching graph node or source file found",
            )

        # Validate path safety
        try:
            abs_path = self._sanitize_and_validate_path(target_file_rel)
        except PathTraversalError as e:
            raise e
        except Exception as e:
            return UnresolvedLocation(entity_id=entity_or_symbol, reason=str(e))

        if not abs_path.is_file():
            return UnresolvedLocation(
                entity_id=entity_or_symbol,
                reason=f"Target file does not exist on disk: {target_file_rel}",
                candidate_paths=[target_file_rel],
            )

        # Read file, compute SHA-256 and validate line range
        try:
            content_bytes = abs_path.read_bytes()
            file_sha = hashlib.sha256(content_bytes).hexdigest()
            total_lines = len(content_bytes.decode("utf-8", errors="ignore").splitlines())
            if total_lines == 0:
                total_lines = 1
        except Exception as e:
            return UnresolvedLocation(entity_id=entity_or_symbol, reason=f"Failed reading file: {e}")

        # Extract line range from node metadata if available
        start_line = int(node_meta.get("line") or 1)
        end_line = int(node_meta.get("end_line") or start_line)

        # Ensure valid bounds: 1 <= start_line <= end_line <= total_lines
        start_line = max(1, min(start_line, total_lines))
        end_line = max(start_line, min(end_line, total_lines))

        rel_normalized = abs_path.relative_to(self.repo_root).as_posix()
        resolution_class = "exact_node_file" if exact_match else "fallback_inferred"

        return SourceLocation(
            entity_id=entity_or_symbol,
            relative_path=rel_normalized,
            absolute_path=abs_path,
            sha256=file_sha,
            start_line=start_line,
            end_line=end_line,
            resolution_class=resolution_class,
            graph_hash=self.graph_hash,
            target_sha=self.target_sha,
            is_exact_match=exact_match,
            metadata=node_meta,
        )
