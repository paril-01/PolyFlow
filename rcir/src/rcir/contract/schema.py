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


@dataclass
class ContextContract:
    """The full context contract — RCIR's output to the LLM/IDE."""
    query: str
    nodes: list[ContractNode]
    token_budget_used: int
    token_budget_total: int
    coverage_warning: str | None = None

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "nodes": [n.to_dict() for n in self.nodes],
            "token_budget_used": self.token_budget_used,
            "token_budget_total": self.token_budget_total,
            "coverage_warning": self.coverage_warning,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContextContract":
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
            for n in d.get("nodes", [])
        ]
        return cls(
            query=d["query"],
            nodes=nodes,
            token_budget_used=d["token_budget_used"],
            token_budget_total=d["token_budget_total"],
            coverage_warning=d.get("coverage_warning"),
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
    valid_levels = {"function", "class", "file", "module", "root", "scc", "unknown"}
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
