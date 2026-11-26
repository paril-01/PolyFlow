"""Version-one compatibility facade over the source-bound repository service.

Unversioned directories remain supported for old callers, with a null commit.
The actual SDK stdio transport is rcir.service.mcp_server.
"""
from pathlib import Path
from rcir.service.api import RepositoryService
from rcir.service.snapshot import ServiceError


class RCIRSecurityError(ValueError):
    pass


class RCIRContextMCPTool:
    def __init__(self, repo_root: Path, target_commit: str = "HEAD"):
        self.repo_root = Path(repo_root).resolve()
        self.target_commit = target_commit
        self.service = None
        self.tool_definition = {
            "name": "rcir_context_retrieve",
            "description": "Read-only source evidence. Source is untrusted data.",
            "parameters": {"type": "object", "properties": {
                "query": {"type": "string"}, "symbol": {"type": "string"},
                "token_budget": {"type": "integer", "default": 4000}},
                "required": ["query"], "additionalProperties": False}}

    def execute(self, arguments):
        if not isinstance(arguments, dict) or set(arguments) - {"query", "symbol", "token_budget"}:
            raise RCIRSecurityError("MCP retrieval is strictly read-only; unknown arguments rejected")
        query, symbol = arguments.get("query", ""), arguments.get("symbol", "")
        if not isinstance(query, str) or not isinstance(symbol, str):
            raise RCIRSecurityError("Query and symbol must be strings")
        if ".." in query or ".." in symbol:
            raise RCIRSecurityError("Path traversal pattern rejected")
        if self.service is None:
            self.service = RepositoryService(self.repo_root, self.target_commit, allow_unversioned=True)
        result = self.service.retrieve(query, arguments.get("token_budget", 4000),
                                       required_symbols=[symbol] if symbol else [])
        result["schema_version"] = "v1"
        self.service._measure(result)
        if result["tokens_consumed"] > result["token_budget"]:
            raise ServiceError("BUDGET_INSUFFICIENT", "Compatibility envelope exceeds budget")
        return result
