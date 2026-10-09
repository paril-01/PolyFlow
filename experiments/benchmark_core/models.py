"""
experiments/benchmark_core/models.py — Canonical Typed Models for PolyFlow & RCIR Benchmarks.

Defines immutable dataclasses and schemas for:
- RunManifest: Run metadata, pinned commits, input hashes, and toolchain versions.
- TrialKey: Uniquely identifies a comparable trial pair (task, commit, model, seed, turn budget).
- TrialResult: Full execution trace, tool calls, diffs, and verification logs.
- VerificationResult: Segregated L1 (Syntax), L2 (Targeted Behavior), L3 (Regression).
- UsageRecord: Provider-native token counts, latency, and cache statistics per turn.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    NOT_MEASURED = "NOT_MEASURED"
    SETUP_ERROR = "SETUP_ERROR"


class TrialStatus(str, Enum):
    TRIAL_SUCCESS = "TRIAL_SUCCESS"
    TRIAL_FAILED_BEHAVIOR = "TRIAL_FAILED_BEHAVIOR"
    TRIAL_FAILED_REGRESSION = "TRIAL_FAILED_REGRESSION"
    TRIAL_FAILED_AGENT = "TRIAL_FAILED_AGENT"
    TRIAL_BUDGET_EXHAUSTED = "TRIAL_BUDGET_EXHAUSTED"
    TRIAL_TIMEOUT_PROVIDER = "TRIAL_TIMEOUT_PROVIDER"
    TRIAL_TIMEOUT_TOOL = "TRIAL_TIMEOUT_TOOL"
    TRIAL_INVALID_SETUP = "TRIAL_INVALID_SETUP"
    TRIAL_INVALID_CONTEXT = "TRIAL_INVALID_CONTEXT"
    TRIAL_INVALID_EVIDENCE = "TRIAL_INVALID_EVIDENCE"
    TRIAL_NOT_MEASURED = "TRIAL_NOT_MEASURED"


class PairValidityStatus(str, Enum):
    VALID_PAIR = "VALID_PAIR"
    TIMEOUT_PAIR = "TIMEOUT_PAIR"
    INVALID_SETUP_PAIR = "INVALID_SETUP_PAIR"
    INVALID_CONTEXT_PAIR = "INVALID_CONTEXT_PAIR"
    DUPLICATE_ARM = "DUPLICATE_ARM"
    INCOMPLETE_PAIR = "INCOMPLETE_PAIR"
    MISMATCHED_PAIR = "MISMATCHED_PAIR"
    TOOL_ERROR_PAIR = "TOOL_ERROR_PAIR"
    ERROR_PAIR = "ERROR_PAIR"


@dataclass(frozen=True)
class TrialKey:
    """Exact tuple key that determines comparability between baseline and RCIR arms."""
    task_id: str
    target_commit: str
    model: str
    seed: int
    turn_budget: int
    replicate: int = 1
    experiment_version: str = "3.0.0"

    def to_string(self, condition: str = "") -> str:
        cond_part = f"_{condition}" if condition else ""
        return f"{self.task_id}{cond_part}_m{self.model[:8]}_c{self.target_commit[:7]}_s{self.seed}_rep{self.replicate}_turn{self.turn_budget}"


@dataclass
class UsageRecord:
    turn: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_seconds: float
    measurement_source: str = "PROVIDER_NATIVE"
    cached_input_tokens: Optional[int] = None
    provider_cost_usd: Optional[float] = None
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn": self.turn,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "latency_seconds": round(self.latency_seconds, 3),
            "measurement_source": self.measurement_source,
            "cached_input_tokens": self.cached_input_tokens,
            "provider_cost_usd": self.provider_cost_usd,
            "timestamp": self.timestamp,
        }


@dataclass
class VerificationResult:
    accepted: bool
    l1_syntax_passed: bool
    l1_logs: List[str]
    l2_targeted_passed: bool
    l2_log: str
    l3_regression_passed: bool
    l3_log: str
    l0_negative_control: CheckStatus = CheckStatus.NOT_MEASURED
    l1_syntax_status: CheckStatus = CheckStatus.NOT_MEASURED
    l2_targeted_status: CheckStatus = CheckStatus.NOT_MEASURED
    l3_regression_status: CheckStatus = CheckStatus.NOT_MEASURED
    verification_duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accepted": self.accepted,
            "l0_negative_control": self.l0_negative_control.value if isinstance(self.l0_negative_control, CheckStatus) else str(self.l0_negative_control),
            "l1_syntax_passed": self.l1_syntax_passed,
            "l1_syntax_status": self.l1_syntax_status.value if isinstance(self.l1_syntax_status, CheckStatus) else str(self.l1_syntax_status),
            "l1_logs": self.l1_logs,
            "l2_targeted_passed": self.l2_targeted_passed,
            "l2_targeted_status": self.l2_targeted_status.value if isinstance(self.l2_targeted_status, CheckStatus) else str(self.l2_targeted_status),
            "l2_log": self.l2_log,
            "l3_regression_passed": self.l3_regression_passed,
            "l3_regression_status": self.l3_regression_status.value if isinstance(self.l3_regression_status, CheckStatus) else str(self.l3_regression_status),
            "l3_log": self.l3_log,
            "verification_duration_seconds": round(self.verification_duration_seconds, 3),
        }


@dataclass
class TrialResult:
    trial_id: str
    task_id: str
    condition: str  # "baseline" or "rcir"
    model: str
    turn_budget: int
    turns_used: int
    tool_calls_executed: int
    files_modified: List[str]
    diff_length: int
    git_diff: str
    verification: VerificationResult
    gatekeeper: str  # "APPROVE", "REJECT", "ERROR"
    status: TrialStatus
    success: bool
    duration_seconds: float
    usage: Dict[str, int]
    usage_records: List[UsageRecord]
    key: Optional[TrialKey] = None
    target_commit: str = ""
    seed: int = 42
    replicate: int = 1
    stop_reason: str = ""
    agent_workflow_completed: bool = False
    verified_success: bool = False
    error: Optional[str] = None
    retrieval_trace_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "task_id": self.task_id,
            "condition": self.condition,
            "model": self.model,
            "target_commit": self.target_commit,
            "seed": self.seed,
            "replicate": self.replicate,
            "turn_budget": self.turn_budget,
            "turns_used": self.turns_used,
            "tool_calls_executed": self.tool_calls_executed,
            "files_modified": self.files_modified,
            "diff_length": self.diff_length,
            "git_diff": self.git_diff,
            "verification": self.verification.to_dict(),
            "gatekeeper": self.gatekeeper,
            "status": self.status.value,
            "success": self.success,
            "verified_success": self.verified_success,
            "agent_workflow_completed": self.agent_workflow_completed,
            "stop_reason": self.stop_reason,
            "duration_seconds": round(self.duration_seconds, 2),
            "usage": self.usage,
            "usage_records": [u.to_dict() for u in self.usage_records],
            "error": self.error,
            "retrieval_trace_id": self.retrieval_trace_id,
        }


@dataclass
class RunManifest:
    schema_version: str = "3.0.0"
    run_id: str = ""
    polyflow_sha: str = ""
    polyflow_dirty: bool = False
    target_repo: str = "nextcloud/server"
    target_sha: str = "da57df078d0808a7235a0177bd99d23c010b472e"
    task_manifest_sha256: str = ""
    hidden_oracle_sha256: str = ""
    graph_sha256: str = ""
    graph_target_sha: str = ""
    ranker_config_sha256: str = ""
    index_manifest_sha256: str = ""
    provider: str = "ollama"
    model: str = "qwen2.5-coder:1.5b"
    turn_budget: int = 12
    replicate_count: int = 1
    measurement_source: str = "PROVIDER_NATIVE"
    started_at_utc: str = ""
    start_time_utc: str = ""
    end_time_utc: Optional[str] = None
    status: str = "INITIALIZED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "polyflow_sha": self.polyflow_sha,
            "polyflow_dirty": self.polyflow_dirty,
            "target_repo": self.target_repo,
            "target_sha": self.target_sha,
            "task_manifest_sha256": self.task_manifest_sha256,
            "hidden_oracle_sha256": self.hidden_oracle_sha256,
            "graph_sha256": self.graph_sha256,
            "graph_target_sha": self.graph_target_sha,
            "ranker_config_sha256": self.ranker_config_sha256,
            "index_manifest_sha256": self.index_manifest_sha256,
            "provider": self.provider,
            "model": self.model,
            "turn_budget": self.turn_budget,
            "replicate_count": self.replicate_count,
            "measurement_source": self.measurement_source,
            "started_at_utc": self.started_at_utc or self.start_time_utc,
            "start_time_utc": self.start_time_utc or self.started_at_utc,
            "end_time_utc": self.end_time_utc,
            "status": self.status,
        }
