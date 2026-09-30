"""
Edge data structures and confidence scoring for RCIR dependency graphs.

Edge types: calls, imports, inherits
Resolution types: static_exact, static_inference, dynamic_unresolved
Confidence: 1.0 / 0.7 / 0.3 respectively
"""

from dataclasses import dataclass, field
from typing import Literal


EdgeType = Literal[
    "calls", "imports", "inherits", "implements", "route", "config", "event", "cross_boundary"
]
ResolutionType = Literal[
    "static_exact",       # resolved via protobuf/typed interface, no ambiguity
    "static_inference",   # resolved via pattern-matching (route strings, naming conventions)
    "dynamic_unresolved", # a call exists, destination could not be statically determined
    "unsupported",        # outside current analysis scope entirely (not even attempted)
]

# Confidence scores per resolution type — derived from the resolution
# mechanism's reliability, not from a model or heuristic.
CONFIDENCE_BY_RESOLUTION: dict[ResolutionType, float] = {
    "static_exact": 1.0,
    "static_inference": 0.7,
    "dynamic_unresolved": 0.3,
    "unsupported": 0.0,
}


@dataclass(frozen=True, slots=True)
class Edge:
    """A directed edge in the dependency graph.

    Attributes:
        source: Qualified path of the calling/importing node.
        target: Qualified path of the called/imported node.
        edge_type: Relationship type (calls, imports, inherits).
        confidence: Float in [0, 1] — how reliable the resolution is.
        resolution: How the target was resolved.
    """
    source: str
    target: str
    edge_type: EdgeType
    confidence: float
    resolution: ResolutionType
    reason: str = ""  # why the edge was classified this way — §1 auditability

    def to_dict(self) -> dict:
        d = {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type,
            "edge_type": self.edge_type,
            "confidence": self.confidence,
            "resolution": self.resolution,
        }
        if self.reason:
            d["reason"] = self.reason
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Edge":
        return cls(
            source=d["source"],
            target=d["target"],
            edge_type=d.get("edge_type", d.get("type", "calls")),
            confidence=d["confidence"],
            resolution=d["resolution"],
            reason=d.get("reason", ""),
        )


def make_edge(
    source: str,
    target: str,
    edge_type: EdgeType,
    resolution: ResolutionType,
    reason: str = "",
) -> Edge:
    """Create an Edge with confidence derived from its resolution type."""
    return Edge(
        source=source,
        target=target,
        edge_type=edge_type,
        confidence=CONFIDENCE_BY_RESOLUTION[resolution],
        resolution=resolution,
        reason=reason,
    )
