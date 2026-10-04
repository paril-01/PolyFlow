"""
RCIR v8.3 — Canonical Graph Fabric & Resolution Ledger (PHASES 9, 10, 11, 12).

Provides:
- CanonicalGraph with normalized endpoints and typed edge semantics
- CanonicalGraphDegreeAnalyzer operating strictly on canonical entity IDs
- ResolutionLedger tracking exact, inferred, ambiguous, dynamic_unresolved, unsupported, and not_analyzed relations
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional

from rcir.entities.canonical import CanonicalEntityRegistry, CanonicalEntityID, SourceSpan
from rcir.query.change_spec import ChangeOperation


class CanonicalEdgeType(str, Enum):
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    OVERRIDES = "overrides"
    INJECTS = "injects"
    ROUTE_TO_CONTROLLER = "route_to_controller"
    FRONTEND_TO_ROUTE = "frontend_to_route"
    EVENT_DISPATCH = "event_dispatch"
    EVENT_LISTENER = "event_listener"
    EVENT_PAYLOAD = "event_payload"
    CONFIG_READS = "config_reads"
    CONFIG_WRITES = "config_writes"
    SOURCE_TO_TEST = "source_to_test"
    SERVICE_REGISTRATION = "service_registration"
    SCHEMA_RELATION = "schema_relation"


class ResolutionClass(str, Enum):
    STATIC_EXACT = "static_exact"
    STATIC_INFERENCE = "static_inference"
    AMBIGUOUS = "ambiguous"
    DYNAMIC_UNRESOLVED = "dynamic_unresolved"
    UNSUPPORTED = "unsupported"
    NOT_ANALYZED = "not_analyzed"


@dataclass
class CanonicalEdge:
    """A strongly typed edge between canonical entity endpoints."""
    source_id: str
    target_id: str
    edge_type: CanonicalEdgeType
    resolution_class: ResolutionClass = ResolutionClass.STATIC_EXACT
    source_span: Optional[SourceSpan] = None
    target_span: Optional[SourceSpan] = None
    call_line: int = 0
    receiver_expression: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value if isinstance(self.edge_type, CanonicalEdgeType) else str(self.edge_type),
            "resolution_class": self.resolution_class.value if isinstance(self.resolution_class, ResolutionClass) else str(self.resolution_class),
            "source_span": self.source_span.to_dict() if self.source_span else None,
            "target_span": self.target_span.to_dict() if self.target_span else None,
            "call_line": self.call_line,
            "receiver_expression": self.receiver_expression,
            "evidence": self.evidence,
        }


@dataclass
class DegreeRecord:
    """Canonical graph degree analysis record."""
    target_id: str
    incoming_exact: int = 0
    incoming_inferred: int = 0
    outgoing_exact: int = 0
    outgoing_inferred: int = 0
    boundary_degree: int = 0
    verification_degree: int = 0
    policy_relevant_degree: int = 0
    fanout_mode: str = "medium_degree"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResolutionLedger:
    """Transparent audit ledger of dependency resolution status."""

    def __init__(self):
        self.counts: Counter[str] = Counter()
        self.items: list[dict[str, Any]] = []

    def record(self, source: str, target: str, status: ResolutionClass, reason: str = ""):
        st_val = status.value if isinstance(status, ResolutionClass) else str(status)
        self.counts[st_val] += 1
        if status in (ResolutionClass.AMBIGUOUS, ResolutionClass.DYNAMIC_UNRESOLVED, ResolutionClass.UNSUPPORTED):
            self.items.append({
                "source": source,
                "target": target,
                "status": st_val,
                "reason": reason,
            })

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": dict(self.counts),
            "total_evaluated": sum(self.counts.values()),
            "unresolved_items": self.items[:50],
        }


class CanonicalGraph:
    """Canonical dependency graph fabric."""

    def __init__(self, registry: CanonicalEntityRegistry | None = None):
        self.registry = registry or CanonicalEntityRegistry()
        self.nodes: dict[str, CanonicalEntityID] = {}
        # source_id -> list of CanonicalEdge
        self.outgoing_edges: dict[str, list[CanonicalEdge]] = defaultdict(list)
        # target_id -> list of CanonicalEdge
        self.incoming_edges: dict[str, list[CanonicalEdge]] = defaultdict(list)
        self.ledger = ResolutionLedger()

    def add_node(self, entity: CanonicalEntityID) -> str:
        uri = self.registry.register(entity)
        self.nodes[uri] = entity
        return uri

    def add_edge(self, edge: CanonicalEdge) -> None:
        self.outgoing_edges[edge.source_id].append(edge)
        self.incoming_edges[edge.target_id].append(edge)
        self.ledger.record(edge.source_id, edge.target_id, edge.resolution_class)

    def get_incoming_edges(self, target_id: str) -> list[CanonicalEdge]:
        """Fetch incoming edges for target_id, checking canonical URI and aliases."""
        target_keys = {target_id}
        res = self.registry.resolve(target_id)
        if res.canonical_id:
            target_keys.add(res.canonical_id)
            target_keys.update(self.registry.get_aliases_for_uri(res.canonical_id))

        edges = []
        for k in target_keys:
            if k in self.incoming_edges:
                edges.extend(self.incoming_edges[k])

        # Deduplicate edges by (source_id, target_id, edge_type)
        seen = set()
        deduped = []
        for e in edges:
            key = (e.source_id, e.target_id, e.edge_type)
            if key not in seen:
                seen.add(key)
                deduped.append(e)
        return deduped

    def get_outgoing_edges(self, source_id: str) -> list[CanonicalEdge]:
        """Fetch outgoing edges for source_id, checking canonical URI and aliases."""
        source_keys = {source_id}
        res = self.registry.resolve(source_id)
        if res.canonical_id:
            source_keys.add(res.canonical_id)
            source_keys.update(self.registry.get_aliases_for_uri(res.canonical_id))

        edges = []
        for k in source_keys:
            if k in self.outgoing_edges:
                edges.extend(self.outgoing_edges[k])

        seen = set()
        deduped = []
        for e in edges:
            key = (e.source_id, e.target_id, e.edge_type)
            if key not in seen:
                seen.add(key)
                deduped.append(e)
        return deduped

    def analyze_degree(self, target_id: str, operation: ChangeOperation | None = None) -> DegreeRecord:
        """Compute structured degree metrics on canonical entity ID."""
        incoming = self.get_incoming_edges(target_id)
        outgoing = self.get_outgoing_edges(target_id)

        inc_exact = sum(1 for e in incoming if e.resolution_class == ResolutionClass.STATIC_EXACT)
        inc_inferred = sum(1 for e in incoming if e.resolution_class == ResolutionClass.STATIC_INFERENCE)
        out_exact = sum(1 for e in outgoing if e.resolution_class == ResolutionClass.STATIC_EXACT)
        out_inferred = sum(1 for e in outgoing if e.resolution_class == ResolutionClass.STATIC_INFERENCE)

        boundary_deg = sum(
            1 for e in incoming + outgoing
            if e.edge_type in (
                CanonicalEdgeType.ROUTE_TO_CONTROLLER,
                CanonicalEdgeType.FRONTEND_TO_ROUTE,
                CanonicalEdgeType.EVENT_DISPATCH,
                CanonicalEdgeType.EVENT_LISTENER,
                CanonicalEdgeType.SERVICE_REGISTRATION,
            )
        )
        verification_deg = sum(
            1 for e in incoming + outgoing
            if e.edge_type == CanonicalEdgeType.SOURCE_TO_TEST
        )

        # Policy relevant degree tailored to operation
        op_val = operation.value if operation else "behavior_change"
        if op_val == "signature_change":
            relevant = inc_exact + inc_inferred
        elif op_val in ("route_change", "event_change"):
            relevant = boundary_deg + inc_exact
        else:
            relevant = inc_exact + inc_inferred + boundary_deg

        if relevant > 100:
            mode = "high_degree"
        elif relevant < 10:
            mode = "low_degree"
        else:
            mode = "medium_degree"

        return DegreeRecord(
            target_id=target_id,
            incoming_exact=inc_exact,
            incoming_inferred=inc_inferred,
            outgoing_exact=out_exact,
            outgoing_inferred=out_inferred,
            boundary_degree=boundary_deg,
            verification_degree=verification_deg,
            policy_relevant_degree=relevant,
            fanout_mode=mode,
        )

    @classmethod
    def from_legacy_dict(cls, raw_graph: dict[str, Any]) -> CanonicalGraph:
        """Construct a CanonicalGraph from raw extraction dictionary."""
        cg = cls()
        nodes_data = raw_graph.get("nodes", {})
        edges_data = raw_graph.get("edges", [])

        # Ingest nodes
        for k, v in nodes_data.items():
            # Derive components
            lang = v.get("language", "php" if ".php" in k else "ts" if ".ts" in k else "python")
            file_p = v.get("file", k.split("::")[0] if "::" in k else k)
            owner = v.get("owner", "")
            sym = v.get("symbol", k.split("::")[-1] if "::" in k else "")
            ns = v.get("namespace", "")

            kind_str = v.get("type", "class")
            try:
                ekind = EntityKind(kind_str.lower())
            except ValueError:
                ekind = EntityKind.CLASS

            ent = CanonicalEntityID(
                repository="nextcloud-server",
                language=lang,
                file=file_p,
                namespace=ns,
                owner_type=owner,
                symbol=sym,
                kind=ekind,
                signature=v.get("signature", ""),
            )
            cg.add_node(ent)

        # Ingest edges
        for e in edges_data:
            src = e.get("source", "")
            tgt = e.get("target", "")
            etype_str = e.get("edge_type", "calls")
            try:
                etype = CanonicalEdgeType(etype_str.lower())
            except ValueError:
                etype = CanonicalEdgeType.CALLS

            res_str = e.get("resolution", "static_exact")
            try:
                res = ResolutionClass(res_str.lower())
            except ValueError:
                res = ResolutionClass.STATIC_EXACT

            edge = CanonicalEdge(
                source_id=src,
                target_id=tgt,
                edge_type=etype,
                resolution_class=res,
                call_line=e.get("call_line", e.get("line", 0)),
                receiver_expression=e.get("receiver_expression", ""),
                evidence=e.get("evidence", {}),
            )
            cg.add_edge(edge)

        return cg
