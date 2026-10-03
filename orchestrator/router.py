"""
RCIR v8 — Adaptive Task-Risk Router (PHASE 17).

Determines optimal orchestration pipeline stages based on change complexity,
saving tokens on localized bug fixes while ensuring deep adversarial review on architectural changes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from rcir.query.change_spec import ChangeOperation, ChangeSpecification, RequestedScope


class TaskRiskLevel(str, Enum):
    LOCAL_BUG = "local_bug"
    CROSS_MODULE = "cross_module"
    ARCHITECTURE_REFACTOR = "architecture_refactor"


@dataclass
class RoutingDecision:
    """Orchestration routing plan for a specific task."""
    risk_level: TaskRiskLevel
    stages: list[str]
    rationale: str
    token_cost_estimate: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_level": self.risk_level.value,
            "stages": self.stages,
            "stage_count": len(self.stages),
            "rationale": self.rationale,
            "token_cost_estimate": self.token_cost_estimate,
        }


class TaskRiskRouter:
    """Deterministic risk router directing tasks to tailored orchestration pipelines."""

    @classmethod
    def route(
        cls,
        task_description: str,
        spec: ChangeSpecification | None = None,
        candidate_count: int = 0,
    ) -> RoutingDecision:
        """Determine pipeline stages based on formal specification and text signals."""
        desc_lower = task_description.lower()

        # 1. Architecture / System boundary change
        if spec and (spec.operation in (ChangeOperation.SCHEMA_CHANGE, ChangeOperation.SERVICE_BOUNDARY_CHANGE)
                     or spec.requested_scope == RequestedScope.REPOSITORY):
            return RoutingDecision(
                risk_level=TaskRiskLevel.ARCHITECTURE_REFACTOR,
                stages=["maker", "reviewer_design", "maker_revision", "implementer", "reviewer_code", "gatekeeper", "historian"],
                rationale="High-risk schema/service boundary change requires upfront design review and revision.",
                token_cost_estimate="~32,000 tokens (7 stages)",
            )

        if any(w in desc_lower for w in ["architecture", "redesign", "cross-service contract", "database migration"]):
            return RoutingDecision(
                risk_level=TaskRiskLevel.ARCHITECTURE_REFACTOR,
                stages=["maker", "reviewer_design", "maker_revision", "implementer", "reviewer_code", "gatekeeper", "historian"],
                rationale="Architectural refactoring requires design review and iterative design revision.",
                token_cost_estimate="~32,000 tokens (7 stages)",
            )

        # 2. Localized bug / Simple single-file change
        if spec and (spec.requested_scope == RequestedScope.LOCAL or
                     (spec.operation in (ChangeOperation.RENAME, ChangeOperation.BEHAVIOR_CHANGE) and candidate_count <= 20)):
            return RoutingDecision(
                risk_level=TaskRiskLevel.LOCAL_BUG,
                stages=["retriever", "implementer", "reviewer", "gatekeeper"],
                rationale="Localized change bypasses Maker design stage, directly implementing and reviewing.",
                token_cost_estimate="~12,000 tokens (4 stages, saving ~45% vs fixed 6-stage)",
            )

        if any(w in desc_lower for w in ["small bug", "typo", "single file", "rename local"]):
            return RoutingDecision(
                risk_level=TaskRiskLevel.LOCAL_BUG,
                stages=["retriever", "implementer", "reviewer", "gatekeeper"],
                rationale="Simple targeted bug fix requires only implementation, verification, and gatekeeper approval.",
                token_cost_estimate="~12,000 tokens (4 stages)",
            )

        # 3. Standard cross-module change (Default)
        return RoutingDecision(
            risk_level=TaskRiskLevel.CROSS_MODULE,
            stages=["maker", "retriever", "implementer", "reviewer", "gatekeeper", "historian"],
            rationale="Cross-module evolution requires Maker requirement discovery, contextual retrieval, and review.",
            token_cost_estimate="~22,000 tokens (6 stages)",
        )
