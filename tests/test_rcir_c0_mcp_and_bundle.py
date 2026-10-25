"""
tests/test_rcir_c0_mcp_and_bundle.py — Phase C0 Integration & MCP Tool Verification.

Tests:
1. ContextEvidenceBundle v1 instantiation, dict roundtrip, and fields.
2. RCIRContextMCPTool definition discovery and read-only execution.
3. Least privilege security guards: rejects write/exec intents.
4. Path traversal injection prevention fail-closed.
5. Strict token budget enforcement.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "rcir" / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "rcir" / "src"))

from rcir.context.models import ContextEvidenceBundle, ContextEvidenceItem, ContextRetrievalResult
from rcir.mcp.tool_adapter import RCIRContextMCPTool, RCIRSecurityError


def test_context_evidence_bundle_roundtrip():
    """Verify ContextEvidenceBundle v1 schema serialization and fields."""
    item = ContextEvidenceItem(
        file_path="apps/files/lib/Controller/ApiController.php",
        file_sha256="abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
        start_line=10,
        end_line=25,
        snippet="public function getThumbnail() { return true; }",
        symbol_name="getThumbnail",
        resolution_class="STATIC_EXACT",
        confidence=1.0,
        freshness="FRESH",
    )
    bundle = ContextEvidenceBundle(
        schema_version="v1",
        query="getThumbnail ApiController",
        target_repo_commit="da57df078d0808a7235a0177bd99d23c010b472e",
        evidence_items=[item],
        omitted_targets=[],
        tokens_consumed=15,
        token_budget=4000,
        tokenizer_name="cl100k_base_exact_with_header_invariant",
        freshness_ratio=1.0,
    )
    data = bundle.to_dict()
    assert data["schema_version"] == "v1"
    assert len(data["evidence_items"]) == 1
    assert data["evidence_items"][0]["symbol_name"] == "getThumbnail"
    assert data["evidence_items"][0]["file_sha256"] == "abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234"
    assert data["tokenizer_name"] == "cl100k_base_exact_with_header_invariant"


def test_mcp_tool_discovery_and_definition(tmp_path: Path):
    """Verify that RCIRContextMCPTool exposes valid MCP tool metadata."""
    tool = RCIRContextMCPTool(repo_root=tmp_path)
    defn = tool.tool_definition
    assert defn["name"] == "rcir_context_retrieve"
    assert "parameters" in defn
    assert "query" in defn["parameters"]["required"]


def test_mcp_tool_execution_read_only(tmp_path: Path):
    """Verify that RCIRContextMCPTool executes read-only retrieval without mutating repo."""
    test_file = tmp_path / "TestController.php"
    test_file.write_text("<?php\nclass TestController {\n    public function index() {}\n}\n")

    tool = RCIRContextMCPTool(repo_root=tmp_path)
    res = tool.execute({"query": "TestController", "token_budget": 1000})
    assert res["schema_version"] == "v1"
    assert len(res["evidence_items"]) >= 1
    assert res["evidence_items"][0]["symbol_name"] == "TestController"
    assert res["tokens_consumed"] <= 1000


def test_mcp_security_guard_rejects_mutation(tmp_path: Path):
    """Verify that attempting to execute or write via MCP tool fails closed."""
    tool = RCIRContextMCPTool(repo_root=tmp_path)
    with pytest.raises(RCIRSecurityError) as exc_info:
        tool.execute({"query": "Test", "write": True})
    assert "strictly read-only" in str(exc_info.value)


def test_mcp_security_guard_rejects_path_traversal(tmp_path: Path):
    """Verify that path traversal attempts fail closed."""
    tool = RCIRContextMCPTool(repo_root=tmp_path)
    with pytest.raises(RCIRSecurityError) as exc_info:
        tool.execute({"query": "../../../etc/passwd"})
    assert "traversal" in str(exc_info.value).lower()
