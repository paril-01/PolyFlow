"""
Unit test for ReActAgentRunner telemetry and execution (Finding F01).
Verifies that ReActAgentRunner can execute without NameError on 'os'
and accurately records UsageRecord telemetry.
"""

from pathlib import Path
from unittest.mock import MagicMock

from orchestrator.agent_loop import ReActAgentRunner
from orchestrator.providers import LLMResponse
from orchestrator.tools import RepoToolEnvironment


def test_agent_loop_runs_without_name_error_and_records_telemetry(tmp_path):
    # Create a dummy repo worktree
    dummy_file = tmp_path / "hello.py"
    dummy_file.write_text("print('hello')\n", encoding="utf-8")

    # Mock LLM provider that returns a valid tool call then stops
    mock_provider = MagicMock()
    mock_provider.generate_with_provenance.side_effect = [
        LLMResponse(
            content='{"tool": "inspect_file", "args": {"path": "hello.py", "start_line": 1, "end_line": 5}}',
            provider="mock-provider",
            endpoint="http://mock",
            model="mock-model",
            prompt_tokens=45,
            completion_tokens=20,
            total_tokens=65,
            latency_seconds=0.05,
        ),
        LLMResponse(
            content="I have inspected the file and verified the contents.",
            provider="mock-provider",
            endpoint="http://mock",
            model="mock-model",
            prompt_tokens=60,
            completion_tokens=15,
            total_tokens=75,
            latency_seconds=0.04,
        ),
    ]

    env = RepoToolEnvironment(repo_root=tmp_path)
    runner = ReActAgentRunner(
        provider=mock_provider,
        env=env,
        max_turns=2,
    )

    result = runner.run(
        task_id="TEST-TASK-01",
        task_description="Inspect hello.py and verify.",
        condition="rcir",
    )

    assert result.error is None, f"Runner failed with error: {result.error}"
    assert result.turns > 0
    assert result.tool_calls_executed == 1
    assert len(result.usage_records) == 2
    assert result.usage_records[0]["input_tokens"] == 45
    assert result.usage_records[0]["output_tokens"] == 20
