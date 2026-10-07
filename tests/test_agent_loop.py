"""
Unit tests for ReActAgentRunner and extract_tool_call in orchestrator/agent_loop.py.
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestrator.tools import RepoToolEnvironment
from orchestrator.providers import LLMProvider, LLMResponse
from orchestrator.agent_loop import extract_tool_call, ReActAgentRunner, AgentLoopResult


class MockProvider(LLMProvider):
    def __init__(self, responses):
        super().__init__(provider_name="mock")
        self.responses = list(responses)
        self.call_count = 0

    def generate_with_provenance(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        if self.call_count < len(self.responses):
            resp_text = self.responses[self.call_count]
        else:
            resp_text = '{"tool": "finish", "args": {"summary": "done"}}'
        self.call_count += 1
        return LLMResponse(
            content=resp_text,
            provider="mock-test",
            endpoint="test://mock",
            model="mock-v1",
            prompt_tokens=50,
            completion_tokens=25,
            total_tokens=75,
            latency_seconds=0.01,
            simulation_fallback=False,
        )


class TestAgentLoop(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="agent_loop_test_")
        self.repo_path = Path(self.test_dir)
        (self.repo_path / "hello.py").write_text("MSG = 'old'\n", encoding="utf-8")
        self.env = RepoToolEnvironment(str(self.repo_path))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_extract_tool_call(self):
        fenced = "Here is my tool call:\n```json\n{\"tool\": \"inspect_file\", \"args\": {\"path\": \"hello.py\"}}\n```"
        call = extract_tool_call(fenced)
        self.assertIsNotNone(call)
        self.assertEqual(call["tool"], "inspect_file")
        self.assertEqual(call["args"]["path"], "hello.py")

        raw = '{"tool": "edit_file", "args": {"path": "hello.py", "old_str": "old", "new_str": "new"}}'
        call2 = extract_tool_call(raw)
        self.assertIsNotNone(call2)
        self.assertEqual(call2["tool"], "edit_file")

    def test_react_loop_execution(self):
        mock_steps = [
            '```json\n{"tool": "inspect_file", "args": {"path": "hello.py"}}\n```',
            '```json\n{"tool": "edit_file", "args": {"path": "hello.py", "old_str": "MSG = \'old\'", "new_str": "MSG = \'new\'"}}\n```',
            '```json\n{"tool": "finish", "args": {"summary": "Successfully updated hello.py"}}\n```'
        ]
        provider = MockProvider(mock_steps)
        runner = ReActAgentRunner(provider=provider, env=self.env, max_turns=5)

        result = runner.run(
            task_id="TEST-001",
            task_description="Update MSG in hello.py to new",
            condition="mock_test",
            test_command="python -c \"import sys; sys.exit(0)\"",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.turns, 3)
        self.assertEqual(result.tool_calls_executed, 3)
        self.assertIn("hello.py", result.files_modified)
        self.assertIn("+MSG = 'new'", result.git_diff)
        self.assertEqual(result.gatekeeper_verdict, "APPROVE")
        self.assertFalse(result.provenance["simulation_fallback"])


if __name__ == "__main__":
    unittest.main()
