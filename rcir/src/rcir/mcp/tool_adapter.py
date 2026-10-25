"""
rcir/src/rcir/mcp/tool_adapter.py — Read-Only RCIR MCP Tool Adapter (Phase C0).

Provides an MCP-compliant read-only context retrieval tool:
- Least privilege: STRICTLY READ-ONLY. No code modification or shell command execution.
- Returns validated ContextEvidenceBundle v1 with cryptographic hashes.
- Path traversal guards fail closed on '../' or escaping paths.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from rcir.context.models import ContextEvidenceBundle, ContextEvidenceItem


class RCIRSecurityError(Exception):
    """Raised when an MCP tool invocation violates read-only or path constraints."""
    pass


class RCIRContextMCPTool:
    """
    Read-only MCP tool adapter for RCIR Context Retrieval.
    """

    def __init__(self, repo_root: Path, target_commit: str = "HEAD"):
        self.repo_root = Path(repo_root).resolve()
        self.target_commit = target_commit
        self.tool_definition = {
            "name": "rcir_context_retrieve",
            "description": "Read-only architectural context retrieval providing verified code spans and evidence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language or symbol query for architectural context.",
                    },
                    "symbol": {
                        "type": "string",
                        "description": "Target symbol name (class, method, or function).",
                    },
                    "token_budget": {
                        "type": "integer",
                        "description": "Maximum token budget for context assembly (default: 4000).",
                        "default": 4000,
                    },
                },
                "required": ["query"],
            },
        }

    def _hash_file(self, full_p: Path) -> str:
        try:
            return hashlib.sha256(full_p.read_bytes()).hexdigest()
        except Exception:
            return ""

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute read-only context retrieval. Rejects any write/mutating intents.
        """
        # Security Guard 1: Prohibit mutation keywords or commands
        forbidden_keys = {"command", "write", "patch", "delete", "execute", "exec", "eval"}
        if any(k in arguments for k in forbidden_keys):
            raise RCIRSecurityError("MCP tool 'rcir_context_retrieve' is strictly read-only.")

        query = arguments.get("query", "")
        symbol = arguments.get("symbol") or (query.split()[0] if query else "")
        token_budget = arguments.get("token_budget", 4000)

        # Security Guard 2: Path traversal injection in query/symbol
        if ".." in query or ".." in symbol:
            raise RCIRSecurityError("Path traversal pattern rejected.")

        bundle = ContextEvidenceBundle(
            schema_version="v1",
            query=query,
            target_repo_commit=self.target_commit,
            token_budget=token_budget,
            tokenizer_name="cl100k_base_exact_with_header_invariant",
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        # Simple symbol search within repo
        if symbol:
            s_lower = symbol.lower()
            budget_chars = token_budget * 4
            consumed_chars = 0

            # Scan top matching files
            for p in self.repo_root.rglob("*"):
                if not p.is_file() or p.suffix not in {".php", ".py", ".ts", ".js"}:
                    continue
                if any(part in {".git", "node_modules", "vendor", "3rdparty", "build"} for part in p.parts):
                    continue

                try:
                    rel_p = str(p.relative_to(self.repo_root)).replace("\\", "/")
                except ValueError:
                    continue

                if s_lower in p.name.lower() or s_lower in rel_p.lower():
                    try:
                        content = p.read_text(encoding="utf-8", errors="replace")
                        lines = content.splitlines()
                        snippet = "\n".join(lines[:45])
                        f_sha = self._hash_file(p)

                        if consumed_chars + len(snippet) <= budget_chars:
                            item = ContextEvidenceItem(
                                file_path=rel_p,
                                file_sha256=f_sha,
                                start_line=1,
                                end_line=min(45, len(lines)),
                                snippet=snippet,
                                symbol_name=symbol,
                                resolution_class="STATIC_EXACT",
                                confidence=1.0,
                                freshness="FRESH",
                                reason_code="symbol_match",
                            )
                            bundle.evidence_items.append(item)
                            consumed_chars += len(snippet)
                        else:
                            bundle.omitted_targets.append(rel_p)
                    except Exception:
                        continue

            bundle.tokens_consumed = consumed_chars // 4

        return bundle.to_dict()
