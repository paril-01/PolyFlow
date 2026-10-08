"""
Unit and Integration Tests for RCIR Context Delivery Model & RepoToolEnvironment (SECTION 7).

Verifies Section 7 contract:
1. Canonical ContextRetrievalResult structure and dictionary compatibility.
2. Synthetic test with 8 matching entries, limit 5:
   - First call returns 5 entries,
   - Second call returns remaining 3 entries,
   - Real RepoToolEnvironment.request_context() receives non-empty RCIR markdown.
3. Only delivered entries become already_seen.
4. Per-request telemetry logging (candidate entries, returned entries, skipped, tokens, budget).
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest

from orchestrator.tools import RepoToolEnvironment
from rcir.context.models import ContextRetrievalResult
from experiments.rcir_v8_5.scripts.run_agent_validation import ConcreteRCIRContextProvider


def test_context_retrieval_result_model():
    """Verify ContextRetrievalResult fields and dict-access compatibility."""
    res = ContextRetrievalResult(
        entries=[
            {
                "entity_id": "OCP\\Files\\Folder::getDirectoryListing",
                "source_file": "lib/public/Files/Folder.php",
                "source_lines": [45, 60],
                "content_snippet": "public function getDirectoryListing()",
                "estimated_tokens": 85,
            }
        ],
        requested_symbol="Folder::getDirectoryListing",
        source_task_id="TASK-TEST",
        budget=1500,
        tokens_added=85,
        duplicates_skipped=2,
    )

    # Direct dataclass access
    assert res.tokens_added == 85
    assert len(res.entries) == 1
    assert res.entity_ids == ["OCP\\Files\\Folder::getDirectoryListing"]
    assert "Context for `Folder::getDirectoryListing`" in res.rendered_markdown
    assert res.remaining_budget == 1415

    # Dict-like compatibility access (for legacy code)
    assert res["context_markdown"] == res.rendered_markdown
    assert res["entities"] == res.entity_ids
    assert res["tokens_delivered"] == 85
    assert res["entities_found"] == 1
    assert res.get("duplicates_skipped") == 2
    assert res.get("nonexistent_key", "default_val") == "default_val"


def test_end_to_end_context_pagination_and_markdown_delivery():
    """
    Section 7 mandatory synthetic test:
    8 matching entries, limit 5:
    - First call returns 5
    - Second returns remaining 3
    - Real RepoToolEnvironment.request_context() receives non-empty RCIR markdown
    - Only delivered entries become already_seen
    """
    # 1. Create 8 synthetic matching entries
    synthetic_entries = [
        {
            "entity_id": f"App\\Service\\Manager::method_{i}",
            "source_file": "lib/private/Manager.php",
            "source_lines": [i * 10, i * 10 + 8],
            "content_snippet": f"public function method_{i}() {{ return {i}; }}",
            "estimated_tokens": 100,
            "reason": f"dependency_{i}",
        }
        for i in range(1, 9)
    ]

    mock_contexts = {
        "TASK-SYNTHETIC": {
            "entries": synthetic_entries,
        }
    }

    provider = ConcreteRCIRContextProvider(
        contexts=mock_contexts,
        scoped_task_id="TASK-SYNTHETIC",
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        env = RepoToolEnvironment(
            repo_root=tmp_dir,
            context_provider=provider,
        )

        # First request: limit 5 entries
        resp1 = env.request_context(symbol="Manager")
        assert "RCIR ITERATIVE CONTEXT for 'Manager'" in resp1
        assert "method_1" in resp1
        assert "method_5" in resp1
        assert "method_6" not in resp1  # Must not include entries beyond limit

        # Invariant: 5 delivered entries are now in already_seen
        assert len(env.already_seen_entities) == 5
        assert env.context_tokens_added == 500
        assert env.context_telemetry["entities_returned"] == 5
        assert env.context_telemetry["duplicate_entities_skipped"] == 0

        # Telemetry record for request 1
        assert len(env.context_request_records) == 1
        rec1 = env.context_request_records[0]
        assert rec1["requested_symbol"] == "Manager"
        assert rec1["returned_entries"] == 5
        assert rec1["candidate_entries"] == 8
        assert rec1["already_seen_skipped"] == 0
        assert rec1["exact_rendered_token_count"] == 500

        # Second request for same symbol: should return remaining 3 entries
        resp2 = env.request_context(symbol="Manager")
        assert "RCIR ITERATIVE CONTEXT for 'Manager'" in resp2
        assert "method_6" in resp2
        assert "method_8" in resp2
        assert "method_1" not in resp2  # Already seen entries are excluded

        # Invariant: all 8 entries now delivered
        assert len(env.already_seen_entities) == 8
        assert env.context_tokens_added == 800
        assert env.context_telemetry["entities_returned"] == 8
        assert env.context_telemetry["duplicate_entities_skipped"] == 5

        # Telemetry record for request 2
        assert len(env.context_request_records) == 2
        rec2 = env.context_request_records[1]
        assert rec2["returned_entries"] == 3
        assert rec2["already_seen_skipped"] == 5
        assert rec2["exact_rendered_token_count"] == 300

        # Third request: all 8 entries seen, should return 0 new entries
        resp3 = env.request_context(symbol="Manager")
        assert len(env.already_seen_entities) == 8
        assert env.context_telemetry["duplicate_entities_skipped"] == 13
        assert env.context_tokens_added == 800
