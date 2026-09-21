"""
Context Contract schema and validation (§6).

The Context Contract is the JSON envelope that RCIR returns to the LLM/IDE.
It contains selected nodes with their state information, token budget usage,
and coverage warnings.

The validation layer uses a composable-checks pattern adapted from PolyFlow's
guard engine shape (§3.1) — independent check functions, each returning
pass/fail plus a message. The actual checks are domain-specific to RCIR,
NOT reused regex patterns from PolyFlow.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class ContractNode:
    """A single node in the context contract response."""
    path: str
    level: str  # function | class | file | module | root | scc
    summary: str
    raw_snippet: str | None
    interface_status: str  # unchanged | changed | unknown
    body_status: str  # unchanged | changed | unknown
    summary_version: str
    summary_source: str  # incremental_ast_analysis | full_recompute | initial
    granularity: str  # fine | coarse
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        d = {
            "path": self.path,
            "level": self.level,
            "summary": self.summary,
            "interface_status": self.interface_status,
            "body_status": self.body_status,
            "summary_version": self.summary_version,
            "summary_source": self.summary_source,
            "granularity": self.granularity,
        }
        if self.raw_snippet is not None:
            d["raw_snippet"] = self.raw_snippet
        if self.relevance_score > 0:
            d["relevance_score"] = round(self.relevance_score, 4)
        return d


# ─── Semantic Layers (v7 §5) ──────────────────────────────────────
#
# These layers separate analysis-confidence, structural characteristics,
# retrieval output, and routing into distinct semantic blocks — replacing
# the flat object from v6 that mixed everything together.

@dataclass
class AnalysisLayer:
    """Analysis confidence and coverage information (v7 §5).

    Reports what RCIR found, what it couldn't resolve, and why.
    This is the data layer behind the Change Impact Report (§9).
    """
    resolved: int = 0           # edges RCIR successfully resolved
    unresolved: int = 0         # edges RCIR explicitly flagged as unresolvable
    denominator_basis: str = "" # what the denominator comes from (e.g. "ground_truth_v1")
    confidence_breakdown: dict[str, int] = field(default_factory=dict)
    # e.g. {"static_exact": 240, "static_inferred": 7, "dynamic_unresolved": 3}
    unresolved_locations: list[dict] = field(default_factory=list)
    # e.g. [{"path": "billing/handlers.py:142", "edge_class": "dynamic_unresolved",
    #         "reason": "getattr() dynamic dispatch"}]

    def to_dict(self) -> dict:
        return {
            "coverage": {
                "resolved": self.resolved,
                "unresolved": self.unresolved,
                "denominator_basis": self.denominator_basis,
            },
            "confidence": self.confidence_breakdown,
            "unresolved_locations": self.unresolved_locations,
        }


@dataclass
class StructureLayer:
    """Structural complexity signal (v7 §4, §5).

    Explicitly NOT a difficulty estimator — estimates structural scope only.
    A 247-node rename can be trivial; a 3-file race condition fix can be hard.
    """
    nodes_touched: int = 0
    cross_service_edges_involved: int = 0
    low_confidence_edge_fraction: float = 0.0
    change_scope: str = "unknown"  # "local" | "module" | "cross_service" | "unknown"

    def to_dict(self) -> dict:
        return {
            "structural_complexity_signal": {
                "nodes_touched": self.nodes_touched,
                "cross_service_edges_involved": self.cross_service_edges_involved,
                "low_confidence_edge_fraction": round(self.low_confidence_edge_fraction, 4),
                "change_scope": self.change_scope,
            },
        }


@dataclass
class RoutingLayer:
    """Model routing advisory (v7 §4, §5).

    Placeholder until Checkpoint 5. When populated, suggests the cheapest
    model tier that achieves a required success probability for this task's
    structural features. Per §8, this is entirely optional and deletable
    without touching the graph, invalidation, or retrieval layers.
    """
    suggested_tier: str | None = None  # "cheap" | "balanced" | "frontier" | None
    rationale: str = ""
    note: str = (
        "advisory only; estimates structural scope and known-unknowns, "
        "not reasoning difficulty"
    )

    def to_dict(self) -> dict:
        if self.suggested_tier is None:
            return {}  # omit entirely if not populated
        return {
            "routing": {
                "suggested_tier": self.suggested_tier,
                "rationale": self.rationale,
                "note": self.note,
            },
        }


@dataclass
class ContextContract:
    """The full context contract — RCIR's output to the LLM/IDE.

    v7 §5: restructured into semantic layers (query, analysis, structure,
    retrieval, routing). Backward compatible — existing flat fields remain
    for consumers that don't need the layered view.
    """
    query: str
    nodes: list[ContractNode]
    token_budget_used: int
    token_budget_total: int
    coverage_warning: str | None = None

    # v7 §5 semantic layers — all optional, populated when data is available
    analysis: AnalysisLayer | None = None
    structure: StructureLayer | None = None
    routing: RoutingLayer | None = None

    def to_dict(self) -> dict:
        d = {
            "query": self.query,
            "retrieval": {
                "nodes": [n.to_dict() for n in self.nodes],
                "token_budget_used": self.token_budget_used,
                "token_budget_total": self.token_budget_total,
            },
            # Keep flat fields for backward compat
            "nodes": [n.to_dict() for n in self.nodes],
            "token_budget_used": self.token_budget_used,
            "token_budget_total": self.token_budget_total,
            "coverage_warning": self.coverage_warning,
        }
        if self.analysis:
            d["analysis"] = self.analysis.to_dict()
        if self.structure:
            d["structure"] = self.structure.to_dict()
        if self.routing:
            routing_dict = self.routing.to_dict()
            if routing_dict:
                d.update(routing_dict)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ContextContract":
        # Support both layered and flat format
        nodes_data = d.get("nodes", [])
        if not nodes_data and "retrieval" in d:
            nodes_data = d["retrieval"].get("nodes", [])

        nodes = [
            ContractNode(
                path=n["path"],
                level=n["level"],
                summary=n["summary"],
                raw_snippet=n.get("raw_snippet"),
                interface_status=n["interface_status"],
                body_status=n["body_status"],
                summary_version=n["summary_version"],
                summary_source=n["summary_source"],
                granularity=n["granularity"],
                relevance_score=n.get("relevance_score", 0.0),
            )
            for n in nodes_data
        ]

        token_used = d.get("token_budget_used", 0)
        token_total = d.get("token_budget_total", 0)
        if "retrieval" in d:
            token_used = d["retrieval"].get("token_budget_used", token_used)
            token_total = d["retrieval"].get("token_budget_total", token_total)

        analysis = None
        if "analysis" in d:
            cov = d["analysis"].get("coverage", {})
            analysis = AnalysisLayer(
                resolved=cov.get("resolved", 0),
                unresolved=cov.get("unresolved", 0),
                denominator_basis=cov.get("denominator_basis", ""),
                confidence_breakdown=d["analysis"].get("confidence", {}),
                unresolved_locations=d["analysis"].get("unresolved_locations", []),
            )

        structure = None
        if "structure" in d:
            sig = d["structure"].get("structural_complexity_signal", {})
            structure = StructureLayer(
                nodes_touched=sig.get("nodes_touched", 0),
                cross_service_edges_involved=sig.get("cross_service_edges_involved", 0),
                low_confidence_edge_fraction=sig.get("low_confidence_edge_fraction", 0.0),
                change_scope=sig.get("change_scope", "unknown"),
            )

        routing = None
        if "routing" in d:
            r = d["routing"]
            routing = RoutingLayer(
                suggested_tier=r.get("suggested_tier"),
                rationale=r.get("rationale", ""),
                note=r.get("note", "advisory only; estimates structural scope and known-unknowns, not reasoning difficulty"),
            )

        return cls(
            query=d["query"],
            nodes=nodes,
            token_budget_used=token_used,
            token_budget_total=token_total,
            coverage_warning=d.get("coverage_warning"),
            analysis=analysis,
            structure=structure,
            routing=routing,
        )


# ─── Composable Validation Checks ─────────────────────────────────
#
# Pattern adapted from PolyFlow's guard engine (guards.py):
# - Each check is an independent function
# - Each returns a list of error messages (empty = pass)
# - Checks are composed by running all and collecting errors
#
# The checks themselves are RCIR-specific — not reused from PolyFlow.

def _check_query_present(contract: ContextContract) -> list[str]:
    """Check that the query is non-empty."""
    if not contract.query or not contract.query.strip():
        return ["Contract must have a non-empty query"]
    return []


def _check_budget_integrity(contract: ContextContract) -> list[str]:
    """Check that token budget usage is consistent."""
    errors = []
    if contract.token_budget_used < 0:
        errors.append(f"token_budget_used ({contract.token_budget_used}) cannot be negative")
    if contract.token_budget_total <= 0:
        errors.append(f"token_budget_total ({contract.token_budget_total}) must be positive")
    if contract.token_budget_used > contract.token_budget_total:
        errors.append(
            f"token_budget_used ({contract.token_budget_used}) exceeds "
            f"token_budget_total ({contract.token_budget_total})"
        )
    return errors


def _check_node_paths_unique(contract: ContextContract) -> list[str]:
    """Check that no two nodes have the same path."""
    paths = [n.path for n in contract.nodes]
    seen = set()
    dupes = []
    for p in paths:
        if p in seen:
            dupes.append(p)
        seen.add(p)
    if dupes:
        return [f"Duplicate node paths: {dupes}"]
    return []


def _check_node_fields_valid(contract: ContextContract) -> list[str]:
    """Check that each node has valid field values."""
    errors = []
    valid_levels = {"function", "method", "class", "service", "file", "module", "root", "scc", "unknown"}
    valid_statuses = {"unchanged", "changed", "unknown", "n/a"}
    valid_granularities = {"fine", "coarse"}

    for i, node in enumerate(contract.nodes):
        if not node.path:
            errors.append(f"Node {i}: empty path")
        if node.level not in valid_levels:
            errors.append(f"Node {i} ({node.path}): invalid level '{node.level}'")
        if node.interface_status not in valid_statuses:
            errors.append(
                f"Node {i} ({node.path}): invalid interface_status '{node.interface_status}'"
            )
        if node.body_status not in valid_statuses:
            errors.append(
                f"Node {i} ({node.path}): invalid body_status '{node.body_status}'"
            )
        if node.granularity not in valid_granularities:
            errors.append(
                f"Node {i} ({node.path}): invalid granularity '{node.granularity}'"
            )
    return errors


def _check_no_empty_response(contract: ContextContract) -> list[str]:
    """Warn (not error) if the contract has no nodes."""
    if len(contract.nodes) == 0:
        return ["Contract contains no nodes — query may be too specific or budget too small"]
    return []


# All checks, in order
_VALIDATION_CHECKS = [
    _check_query_present,
    _check_budget_integrity,
    _check_node_paths_unique,
    _check_node_fields_valid,
    _check_no_empty_response,
]


def validate_contract(contract: ContextContract) -> list[str]:
    """Run all validation checks on a context contract.

    Returns a list of error/warning messages. Empty list = valid.
    """
    all_errors = []
    for check in _VALIDATION_CHECKS:
        all_errors.extend(check(contract))
    return all_errors
