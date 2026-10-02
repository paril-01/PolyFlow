"""
ReAct Tool-Calling Agent Loop for AEF Coding Agents.
Enables agents to interactively inspect repository files, search code,
apply edits, run compilers/test suites, observe results, and repair code.
"""

import json
import re
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from orchestrator.providers import LLMProvider, LLMProviderError, LLMResponse
from orchestrator.tools import RepoToolEnvironment


@dataclass
class AgentLoopResult:
    task_id: str
    condition: str
    success: bool
    turns: int
    tool_calls_executed: int
    files_modified: List[str]
    git_diff: str
    final_test_result: Optional[Dict[str, Any]]
    gatekeeper_verdict: str  # "APPROVE", "REJECT", "ERROR"
    summary: str
    provenance: Dict[str, Any]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "condition": self.condition,
            "success": self.success,
            "turns": self.turns,
            "tool_calls_executed": self.tool_calls_executed,
            "files_modified": self.files_modified,
            "git_diff_length": len(self.git_diff),
            "final_test_result": self.final_test_result,
            "gatekeeper_verdict": self.gatekeeper_verdict,
            "summary": self.summary,
            "provenance": self.provenance,
            "error": self.error,
        }


TOOL_SYSTEM_PROMPT = """You are an expert AI software engineering agent working in a real repository.
You have access to the following tools to inspect, modify, and verify the codebase:

1. inspect_file: View file contents with line numbers.
   Usage: {"tool": "inspect_file", "args": {"path": "path/to/file", "start_line": 1, "end_line": 50}}

2. search_code: Search for symbol or regex across the repository.
   Usage: {"tool": "search_code", "args": {"query": "symbol_name", "path": "optional/subpath"}}

3. list_dir: List directory contents.
   Usage: {"tool": "list_dir", "args": {"path": "optional/dir"}}

4. edit_file: Safely replace an exact string in a file with new code.
   Usage: {"tool": "edit_file", "args": {"path": "path/to/file", "old_str": "exact old code", "new_str": "exact new code"}}

5. run_command: Run shell commands, compilers, or test suites.
   Usage: {"tool": "run_command", "args": {"command": "python path/to/test.py"}}

6. finish: Signal that the task is complete.
   Usage: {"tool": "finish", "args": {"summary": "Description of changes and verification results"}}

CRITICAL INSTRUCTIONS & WORKFLOW:
1. Turn 1 (Inspect): Use {"tool": "inspect_file", "args": {"path": "...", "start_line": 1, "end_line": 50}} to view target code lines.
2. Turn 2 (Edit): Use {"tool": "edit_file", "args": {"path": "...", "old_str": "...", "new_str": "..."}} to apply the exact minimal code change.
3. Turn 3 (Verify): Use {"tool": "run_command", "args": {"command": "..."}} to compile and test the code.
4. Turn 4 (Complete): If tests pass (exit 0), call {"tool": "finish", "args": {"summary": "..."}}.

Always wrap your tool call in ```json and ``` code fence, or output plain JSON object.
"""


def extract_tool_call(response_text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse tool call JSON from model response."""
    # Pattern 1: fenced json ```json ... ```
    fence_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(fence_pattern, response_text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1))
            if "tool" in parsed:
                return parsed
        except Exception:
            pass

    # Pattern 2: raw json object containing "tool"
    # Find { ... } with "tool":
    obj_pattern = r"(\{\s*\"tool\"\s*:\s*\"[^\"]+\".*?\})"
    match = re.search(obj_pattern, response_text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1))
            if "tool" in parsed:
                return parsed
        except Exception:
            pass

    # Pattern 3: Look for balanced braces
    start_idx = response_text.find('{"tool"')
    if start_idx == -1:
        start_idx = response_text.find('{ "tool"')
    if start_idx != -1:
        # scan forward for matching closing brace
        depth = 0
        end_idx = -1
        for i in range(start_idx, len(response_text)):
            if response_text[i] == '{':
                depth += 1
            elif response_text[i] == '}':
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break
        if end_idx != -1:
            try:
                candidate = response_text[start_idx:end_idx]
                parsed = json.loads(candidate)
                if "tool" in parsed:
                    return parsed
            except Exception:
                pass

    return None


class ReActAgentRunner:
    """Executes iterative tool-calling loops with fail-closed LLM inference."""

    def __init__(self, provider: LLMProvider, env: RepoToolEnvironment, max_turns: int = 5):
        self.provider = provider
        self.env = env
        self.max_turns = max_turns

    def run(
        self,
        task_id: str,
        task_description: str,
        condition: str,
        context_prompt: str = "",
        test_command: Optional[str] = None,
    ) -> AgentLoopResult:
        """
        Execute ReAct loop for a task.
        """
        user_message = f"TASK ID: {task_id}\n\nDESCRIPTION:\n{task_description}\n"
        if context_prompt:
            user_message += f"\nAVAILABLE CONTEXT:\n{context_prompt}\n"
        if test_command:
            user_message += f"\nVERIFICATION COMMAND:\nRun this command to test your changes:\n{test_command}\n"

        conversation_history = [
            {"role": "system", "content": TOOL_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_latency = 0.0
        tool_calls_count = 0
        final_summary = ""
        final_test_res = None
        turn = 0

        last_prov: Dict[str, Any] = {
            "provider": self.provider.provider_name,
            "endpoint": "unknown",
            "model": "unknown",
            "simulation_fallback": False,
        }

        while turn < self.max_turns:
            turn += 1

            # Format full prompt for LLM
            system_msg = conversation_history[0]["content"]
            # Combine history into user turn
            history_text = ""
            for msg in conversation_history[1:]:
                prefix = "AGENT: " if msg["role"] == "assistant" else "OBSERVATION:\n"
                history_text += f"{prefix}{msg['content']}\n\n"

            # Execute LLM call with fail-closed integrity
            try:
                llm_resp: LLMResponse = self.provider.generate_with_provenance(
                    system_prompt=system_msg,
                    user_prompt=history_text.strip(),
                )
            except Exception as e:
                # Fail-closed: record error and return FAILED
                return AgentLoopResult(
                    task_id=task_id,
                    condition=condition,
                    success=False,
                    turns=turn,
                    tool_calls_executed=tool_calls_count,
                    files_modified=self.env.get_modified_files(),
                    git_diff=self.env.get_git_diff(),
                    final_test_result=final_test_res,
                    gatekeeper_verdict="ERROR",
                    summary="Execution failed due to provider error.",
                    provenance=last_prov,
                    error=f"LLMProviderError: {str(e)}",
                )

            total_prompt_tokens += llm_resp.prompt_tokens
            total_completion_tokens += llm_resp.completion_tokens
            total_latency += llm_resp.latency_seconds
            last_prov = {
                "provider": llm_resp.provider,
                "endpoint": llm_resp.endpoint,
                "model": llm_resp.model,
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_prompt_tokens + total_completion_tokens,
                "latency_seconds": round(total_latency, 3),
                "simulation_fallback": llm_resp.simulation_fallback,
            }

            resp_text = llm_resp.content.strip()
            conversation_history.append({"role": "assistant", "content": resp_text})

            # Parse tool call
            tool_call = extract_tool_call(resp_text)
            if not tool_call:
                # If model didn't emit a tool, check if it claims completion
                if "finish" in resp_text.lower() or "completed" in resp_text.lower():
                    final_summary = resp_text[:300]
                    break
                else:
                    # Provide feedback to agent
                    obs = "ERROR: No valid JSON tool call was found in your response. Please output a valid tool call object, e.g., ```json {\"tool\": \"run_command\", \"args\": {\"command\": \"...\"}} ```"
                    conversation_history.append({"role": "user", "content": obs})
                    continue

            tool_name = tool_call.get("tool", "")
            args = tool_call.get("args", {})
            tool_calls_count += 1

            if tool_name == "finish":
                final_summary = args.get("summary", resp_text[:300])
                break

            # Execute tool in RepoToolEnvironment
            observation = ""
            if tool_name == "inspect_file":
                path = args.get("path", "")
                s = args.get("start_line")
                e = args.get("end_line")
                observation = self.env.inspect_file(path, start_line=s, end_line=e)
                if not self.env.get_modified_files():
                    observation += "\n[ACTION GUIDE]: Target inspected. Next step: call 'edit_file' with exact old_str and new_str to implement the required change."

            elif tool_name == "search_code":
                query = args.get("query", "")
                path = args.get("path")
                is_regex = bool(args.get("is_regex", False))
                observation = self.env.search_code(query, path=path, is_regex=is_regex)

            elif tool_name == "list_dir":
                path = args.get("path")
                observation = self.env.list_dir(path)

            elif tool_name == "edit_file":
                path = args.get("path", "")
                old_str = args.get("old_str", "")
                new_str = args.get("new_str", "")
                observation = self.env.edit_file(path, old_str, new_str)
                if "SUCCESS" in observation:
                    observation += "\n[ACTION GUIDE]: Edit applied successfully. Next step: call 'run_command' with the test command to compile and verify."

            elif tool_name == "run_command":
                cmd = args.get("command", "")
                cmd_res = self.env.run_command(cmd, timeout_sec=60)
                final_test_res = cmd_res
                status = "PASSED (exit 0)" if cmd_res["exit_code"] == 0 else f"FAILED (exit {cmd_res['exit_code']})"
                observation = f"Command output [{status}]:\nSTDOUT:\n{cmd_res['stdout'][:1500]}\nSTDERR:\n{cmd_res['stderr'][:1000]}"
                if cmd_res["exit_code"] == 0:
                    observation += "\n[ACTION GUIDE]: Verification tests PASSED (exit code 0). Next step: call 'finish' with summary."
                else:
                    observation += "\n[ACTION GUIDE]: Verification FAILED. Next step: call 'edit_file' to repair the error."

            else:
                observation = f"ERROR: Unknown tool '{tool_name}'."

            # Truncate observation to prevent context explosion on local models
            if len(observation) > 2500:
                observation = observation[:2500] + "\n... [truncated for model context limit]"

            conversation_history.append({"role": "user", "content": f"TOOL RESULT ({tool_name}):\n{observation}"})

        # Run final verification if test_command provided and not yet run or needs final verification
        if test_command:
            final_verification = self.env.run_command(test_command, timeout_sec=60)
            final_test_res = final_verification
            passed = (final_verification["exit_code"] == 0)
        else:
            passed = bool(self.env.get_modified_files())

        # Gatekeeper evaluation
        diff = self.env.get_git_diff()
        gatekeeper_verdict = "APPROVE" if passed and (len(diff) > 0 or not test_command) else "REJECT"

        return AgentLoopResult(
            task_id=task_id,
            condition=condition,
            success=passed,
            turns=turn,
            tool_calls_executed=tool_calls_count,
            files_modified=self.env.get_modified_files(),
            git_diff=diff,
            final_test_result=final_test_res,
            gatekeeper_verdict=gatekeeper_verdict,
            summary=final_summary or "Completed agent run.",
            provenance=last_prov,
            error=None,
        )
