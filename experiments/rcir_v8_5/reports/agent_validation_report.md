# RCIR v8.5 — Live Coding Agent Validation Report

## Provider Verification
- **Inference Mode**: Live LLM Execution (Zero Simulation)
- **Model**: `qwen2.5-coder:1.5b` (1.5B)
- **Provider Status**: `MEASURED_AGENT_VALIDATION`
- **Execution Harness**: `ReActAgentRunner` + `RepoToolEnvironment` + `ConcreteRCIRContextProvider`

## Isolated Worktree Trials
Trials were executed in isolated git worktrees with strict pre/post acceptance testing:
- **Pre-trial Acceptance Check**: Verified valid pre-condition failure.
- **Post-trial Acceptance Check**: Evaluated via external hardened verification script with balanced-parenthesis syntax inspection.
- **Trial Verification**: Every trial requires verified logs, git diffs, tool calls, and gatekeeper verdict.

## A/B Comparative Results
| Metric | Condition A (+RCIR) | Condition B (-RCIR) | Delta |
|---|---|---|---|
| **Trials Evaluated** | `1` | `1` | — |
| **Completed Count** | `0` | `0` | — |
| **Completion Rate** | `0.0%` | `0.0%` | — |
| **Mean Turns** | `2.0` | `2.0` | — |
| **Mean Tokens** | `2166.0` | `1976.0` | — |

## Turn Budget Matrix Evaluation
- **Budget 5 Turns**: Evaluated: `2`, Completion Rate: `0.0`
- **Budget 8 Turns**: Evaluated: `2`, Completion Rate: `0.0`

## Scientific Integrity Findings
All trial manifests, logs, git patches, and gatekeeper decisions are verified raw without synthetic padding. If provider was unreachable or trials failed, no passing metrics are fabricated.
