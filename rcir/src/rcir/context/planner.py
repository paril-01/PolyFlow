"""
RCIR v8.3 — Semantic Context Planner & Budget Allocator (PHASES 49, 50, 51, 52, 53, 59, 60).

Features:
- Semantic Context Roles: TARGET, DIRECT_CALLER, IMPLEMENTATION, BOUNDARY, TEST, CONFIG_SCHEMA, INDIRECT_SUPPORT, IMPACT_SUMMARY
- Explicit Target Pinning: Target context is reserved first; targets never compete against supporting candidates
- Deterministic Role Quotas: Allocates budget dynamically according to ChangeOperation to maximize CriticalRecall@Budget
- High-Fanout Strategy: Injects structural ImpactSummary + top representative consumers rather than overflowing context
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional
import math

from rcir.context.summarizer import ImpactSummary
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.retrieval.ranker import RankedCandidate


class ContextRole(str, Enum):
    TARGET = "target"
    DIRECT_CALLER = "direct_caller"
    IMPLEMENTATION = "implementation"
    BOUNDARY = "boundary"
    TEST = "test"
    CONFIG_SCHEMA = "config_schema"
    INDIRECT_SUPPORT = "indirect_support"
    IMPACT_SUMMARY = "impact_summary"


@dataclass
class RoleQuota:
    """Fractional budget allocation across semantic roles."""
    target_fraction: float = 0.20
    implementation_fraction: float = 0.20
    caller_fraction: float = 0.20
    test_fraction: float = 0.15
    boundary_fraction: float = 0.10
    indirect_fraction: float = 0.05
    summary_fraction: float = 0.10

    @classmethod
    def for_operation(cls, operation: ChangeOperation | str | None) -> RoleQuota:
        op = str(operation.value if hasattr(operation, "value") else (operation or "")).lower()
        if op == "signature_change":
            # Signatures need more implementation + caller budget
            return cls(
                target_fraction=0.20,
                implementation_fraction=0.25,
                caller_fraction=0.25,
                test_fraction=0.15,
                boundary_fraction=0.05,
                indirect_fraction=0.00,
                summary_fraction=0.10,
            )
        elif op == "route_change":
            # Route changes need high boundary and test allocation
            return cls(
                target_fraction=0.15,
                implementation_fraction=0.15,
                caller_fraction=0.15,
                test_fraction=0.25,
                boundary_fraction=0.20,
                indirect_fraction=0.05,
                summary_fraction=0.05,
            )
        elif op in ("event_change", "service_boundary_change"):
            return cls(
                target_fraction=0.15,
                implementation_fraction=0.15,
                caller_fraction=0.20,
                test_fraction=0.20,
                boundary_fraction=0.20,
                indirect_fraction=0.00,
                summary_fraction=0.10,
            )
        return cls()


@dataclass
class PlannedItem:
    candidate: RankedCandidate
    role: ContextRole
    allocated_tokens: int = 0
    inclusion_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.candidate.entity_id,
            "file_path": self.candidate.file_path,
            "role": self.role.value,
            "allocated_tokens": self.allocated_tokens,
            "reason": self.inclusion_reason,
            "rank": self.candidate.rank,
        }


@dataclass
class ContextPlan:
    """Computed execution plan for ContextCompiler."""
    total_budget: int
    target_tokens_reserved: int
    role_quotas: dict[str, int]
    planned_items: list[PlannedItem] = field(default_factory=list)
    impact_summary: Optional[ImpactSummary] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_budget": self.total_budget,
            "target_tokens_reserved": self.target_tokens_reserved,
            "role_quotas": self.role_quotas,
            "planned_items": [item.to_dict() for item in self.planned_items],
            "has_impact_summary": self.impact_summary is not None,
        }


class ContextPlanner:
    """Plans and quotas context candidates into bounded token allocations."""

    @classmethod
    def assign_role(
        cls,
        candidate: RankedCandidate,
        pinned_targets: set[str],
    ) -> ContextRole:
        """Deterministically classify candidate into a semantic context role."""
        cid = candidate.entity_id
        ev = candidate.evidence
        fp = candidate.file_path.lower()

        # 1. Pinned target: strictly verified target IDs (Phase 48)
        if cid in pinned_targets:
            return ContextRole.TARGET

        # 2. Test
        if "test" in fp or ev.test_relationship != "none" or "test" in ev.edge_types:
            return ContextRole.TEST

        # 3. Direct Implementation / Override
        if any(et in ("implements", "inherits", "overrides") for et in ev.edge_types):
            return ContextRole.IMPLEMENTATION

        # 4. Direct Callers / Importers
        if any(et in ("calls", "imports") for et in ev.edge_types) or ev.resolution_class in ("static_exact", "static_inference"):
            if ev.hop_distance <= 1:
                return ContextRole.DIRECT_CALLER

        # 5. Boundary / Route / Event / Config
        if ev.boundary_contract != "none" or any(et in ("route_to_controller", "frontend_to_route", "event_dispatch", "event_listener") for et in ev.edge_types):
            return ContextRole.BOUNDARY

        if "config" in fp or any("config" in et for et in ev.edge_types):
            return ContextRole.CONFIG_SCHEMA

        return ContextRole.INDIRECT_SUPPORT

    @classmethod
    def create_plan(
        cls,
        ranked_candidates: list[RankedCandidate],
        token_budget: int = 4000,
        spec: Optional[ChangeSpecification] = None,
        impact_summary: Optional[ImpactSummary] = None,
    ) -> ContextPlan:
        """Construct multi-role budget allocation plan."""
        op = spec.operation if spec else ChangeOperation.BEHAVIOR_CHANGE
        quota = RoleQuota.for_operation(op)

        # Identify pinned targets strictly from ChangeSpecification (Phase 48)
        pinned: set[str] = set()
        if spec:
            pinned.update(spec.canonical_target_ids)
            if spec.requested_symbol:
                pinned.add(spec.requested_symbol)

        # Distribute budget across roles ensuring sum(role budgets) + summary <= token_budget (Phase 43)
        summary_budget = int(token_budget * quota.summary_fraction)
        avail_budget = max(0, token_budget - summary_budget)

        target_budget = int(avail_budget * quota.target_fraction)
        impl_budget = int(avail_budget * quota.implementation_fraction)
        caller_budget = int(avail_budget * quota.caller_fraction)
        test_budget = int(avail_budget * quota.test_fraction)
        boundary_budget = int(avail_budget * quota.boundary_fraction)
        
        # Explicit CONFIG_SCHEMA allocation carved out from boundary budget (Phase 43)
        config_schema_budget = min(boundary_budget // 2, 100) if boundary_budget > 10 else 0
        adj_boundary_budget = max(0, boundary_budget - config_schema_budget)
        
        allocated_so_far = target_budget + impl_budget + caller_budget + test_budget + adj_boundary_budget + config_schema_budget
        indirect_budget = max(0, avail_budget - allocated_so_far)

        role_budgets = {
            ContextRole.TARGET: target_budget,
            ContextRole.IMPLEMENTATION: impl_budget,
            ContextRole.DIRECT_CALLER: caller_budget,
            ContextRole.TEST: test_budget,
            ContextRole.BOUNDARY: adj_boundary_budget,
            ContextRole.CONFIG_SCHEMA: config_schema_budget,
            ContextRole.INDIRECT_SUPPORT: indirect_budget,
        }

        # Invariant check
        assert sum(role_budgets.values()) + summary_budget <= token_budget, "Budget accounting invariant violation!"

        # Role candidate queues
        role_queues: dict[ContextRole, list[RankedCandidate]] = {r: [] for r in ContextRole}

        for cand in ranked_candidates:
            role = cls.assign_role(cand, pinned)
            role_queues[role].append(cand)

        planned_items: list[PlannedItem] = []
        tokens_spent_by_role: dict[ContextRole, int] = {r: 0 for r in ContextRole}

        # 1. First Pass: PIN Target candidates (mandatory reservation, Phase 44)
        for cand in role_queues[ContextRole.TARGET]:
            target_cost = 200  # Target representation
            if tokens_spent_by_role[ContextRole.TARGET] + target_cost <= target_budget or not planned_items:
                planned_items.append(PlannedItem(
                    candidate=cand,
                    role=ContextRole.TARGET,
                    allocated_tokens=target_cost,
                    inclusion_reason="Primary change target entity (PINNED)",
                ))
                tokens_spent_by_role[ContextRole.TARGET] += target_cost

        # 2. Second Pass: Utility-per-token candidate selection (Phase 44 & 45)
        role_priority = [
            ContextRole.IMPLEMENTATION,
            ContextRole.DIRECT_CALLER,
            ContextRole.TEST,
            ContextRole.BOUNDARY,
            ContextRole.CONFIG_SCHEMA,
            ContextRole.INDIRECT_SUPPORT,
        ]

        for role in role_priority:
            budget = role_budgets[role] if role_queues[ContextRole.TARGET] else avail_budget
            cands = role_queues[role]

            # Dynamic cost and utility per token optimization (Phase 45)
            def compute_cand_cost_and_utility(c: RankedCandidate, r: ContextRole) -> tuple[int, float]:
                cost = 80 if r == ContextRole.BOUNDARY else 100 if r == ContextRole.CONFIG_SCHEMA else 120 if r == ContextRole.TEST else 150
                rel_conf = 1.0 if c.evidence.resolution_class == "static_exact" else 0.7 if c.evidence.resolution_class == "static_inference" else 0.4
                rank_boost = 1.0 / math.log2(c.rank + 2)
                crit = 1.5 if r in (ContextRole.IMPLEMENTATION, ContextRole.DIRECT_CALLER) else 1.0
                utility = (rel_conf * 20.0 + rank_boost * 30.0) * crit
                return cost, utility / cost

            # Sort by utility-per-token descending
            cands_with_metric = [(c, compute_cand_cost_and_utility(c, role)) for c in cands]
            cands_with_metric.sort(key=lambda item: (-item[1][1], item[0].rank))

            for cand, (cost, util_per_tok) in cands_with_metric:
                if tokens_spent_by_role[role] + cost <= budget:
                    planned_items.append(PlannedItem(
                        candidate=cand,
                        role=role,
                        allocated_tokens=cost,
                        inclusion_reason=f"Role allocation: {role.value} (utility/tok: {util_per_tok:.2f})",
                    ))
                    tokens_spent_by_role[role] += cost

        # Sort planned items: Target first, then by candidate rank
        planned_items.sort(key=lambda p: (0 if p.role == ContextRole.TARGET else 1, p.candidate.rank))

        return ContextPlan(
            total_budget=token_budget,
            target_tokens_reserved=tokens_spent_by_role[ContextRole.TARGET],
            role_quotas={r.value: role_budgets[r] for r in role_budgets},
            planned_items=planned_items,
            impact_summary=impact_summary,
        )
