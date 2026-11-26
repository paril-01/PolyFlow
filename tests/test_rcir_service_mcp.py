"""Real SDK subprocess transport, not an in-process MCP simulation."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip("mcp.server.mcpserver")
from mcp import ClientSession, StdioServerParameters, stdio_client


def test_real_stdio_client(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    for key, value in [("user.email", "test@example.invalid"), ("user.name", "test")]:
        subprocess.run(["git", "-C", str(tmp_path), "config", key, value], check=True)
    (tmp_path / "worker.py").write_text("def unique_target():\n    return 7\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "fixture"], check=True, capture_output=True)
    async def flow():
        parameters = StdioServerParameters(command=sys.executable,
            args=["-m", "rcir.service.cli", "serve", "--repo", str(tmp_path)], env=dict(os.environ))
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as client:
                initialized = await client.initialize()
                listed = await client.list_tools()
                assert {t.name for t in listed.tools} == {"rcir_context_retrieve", "rcir_evidence_expand", "rcir_impact_analyze", "rcir_status"}
                receipt = await client.call_tool("rcir_context_retrieve", {"query": "unique_target", "token_budget": 1000})
                data = receipt.structured_content
                if data is None:
                    data = json.loads(receipt.content[0].text)
                assert data["evidence_items"][0]["symbol_name"] == "unique_target"
                from rcir.context.tokenizer import TiktokenTokenCounter
                from rcir.service.snapshot import canonical
                measured = TiktokenTokenCounter().count(canonical(receipt.model_dump(mode="json", by_alias=True, exclude_none=True)).decode())
                assert measured == data["tokens_consumed"] <= 1000
                handle = data["evidence_items"][0]["evidence_id"]
                expanded = await client.call_tool("rcir_evidence_expand", {"evidence_id": handle})
                assert not expanded.is_error
                invalid = await client.call_tool("rcir_context_retrieve", {"query": "unique_target", "token_budget": 1})
                failure = invalid.structured_content or json.loads(invalid.content[0].text)
                assert failure["status"] == "BUDGET_INSUFFICIENT"
                malformed = await client.call_tool("rcir_context_retrieve", {"query": {"write": True}})
                assert malformed.is_error
                print(json.dumps({"initialize": initialized.model_dump(mode="json"), "tools": listed.model_dump(mode="json"),
                                  "retrieve": data, "expand": expanded.model_dump(mode="json"),
                                  "budget_error": failure, "malformed": malformed.model_dump(mode="json")}, ensure_ascii=True))
    asyncio.run(asyncio.wait_for(flow(), timeout=45))

