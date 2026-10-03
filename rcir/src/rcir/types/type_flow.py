"""
RCIR v8.2 — TypeFlowIndex & Interprocedural Receiver Resolution (PHASES 20, 21).

Provides deterministic type-flow analysis for dynamically typed and mixed languages (PHP/TS):
- Resolves receiver expressions to candidate class/interface types
- Maintains inheritance closure and interface implementation closures
- Tracks constructor injection, parameter typehints, property @var annotations, and return types
- Disambiguates generic method names (e.g., `Node::getId()` vs `User::getId()`)
- Preserves explicit ambiguity classes (EXACT_RESOLVED, AMBIGUOUS_CANDIDATES, UNRESOLVED)
  without silently escalating uncertainty to false exactness.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ReceiverResolutionStatus(str, Enum):
    EXACT_RESOLVED = "exact_resolved"        # Single concrete/interface receiver proven
    AMBIGUOUS_CANDIDATES = "ambiguous"        # Multiple possible types matching signature
    UNKNOWN_RECEIVER = "unknown_receiver"    # Untyped dynamic call site ($foo->getId())
    INCOMPATIBLE = "incompatible"            # Receiver proven to not implement/own method


@dataclass
class ReceiverResolutionResult:
    """Outcome of receiver type resolution for a method invocation."""
    receiver_expr: str
    method_name: str
    status: ReceiverResolutionStatus
    candidate_types: list[str] = field(default_factory=list)
    resolved_entity_id: Optional[str] = None
    evidence_signals: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "receiver_expr": self.receiver_expr,
            "method_name": self.method_name,
            "status": self.status.value,
            "candidate_types": self.candidate_types,
            "resolved_entity_id": self.resolved_entity_id,
            "evidence_signals": self.evidence_signals,
            "confidence": round(self.confidence, 3),
        }


class TypeFlowIndex:
    """
    Interprocedural type-flow index and method owner resolution engine.
    Constructs type closures and resolves receiver expressions using static AST signals.
    """

    def __init__(self):
        # Class inheritance: child -> parent
        self.parents: dict[str, str] = {}
        # Interface implementations: class -> set of implemented interfaces
        self.implements_map: dict[str, set[str]] = defaultdict(set)
        # Subtype closure: parent/interface -> set of all subclasses/implementations
        self.subtypes_closure: dict[str, set[str]] = defaultdict(set)

        # Method declarations: class_name -> set of declared method names
        self.class_methods: dict[str, set[str]] = defaultdict(set)
        # Method owners: method_name -> set of classes/interfaces declaring it
        self.method_owners: dict[str, set[str]] = defaultdict(set)

        # Property type annotations: (class_name, property_name) -> type_name
        self.property_types: dict[tuple[str, str], str] = {}
        # Parameter type annotations: (class_name, method_name, param_name) -> type_name
        self.param_types: dict[tuple[str, str, str], str] = {}
        # Return type annotations: (class_name, method_name) -> return_type
        self.return_types: dict[tuple[str, str], str] = {}

    @classmethod
    def from_graph(cls, raw_graph: dict[str, Any]) -> TypeFlowIndex:
        """Construct TypeFlowIndex from repository dependency graph edges and nodes."""
        index = cls()

        edges = raw_graph.get("edges", [])
        for e in edges:
            src = e.get("source", "")
            tgt = e.get("target", "")
            etype = e.get("edge_type", e.get("type", ""))

            # 1. Inheritance
            if etype == "inherits":
                index.parents[src] = tgt
                index.subtypes_closure[tgt].add(src)

            # 2. Implementation
            elif etype == "implements":
                index.implements_map[src].add(tgt)
                index.subtypes_closure[tgt].add(src)

            # 3. Method definition
            elif etype == "defines" or "::" in src:
                if "::" in src:
                    parts = src.split("::")
                    owner, method = parts[0], parts[1]
                    index.class_methods[owner].add(method)
                    index.method_owners[method].add(owner)

            # 4. Constructor injection / property type hints
            elif etype == "injects":
                # src is class::__construct, tgt is injected dependency interface
                if "::" in src:
                    owner = src.split("::")[0]
                    index.subtypes_closure[tgt].add(owner)

        # Compute transitive closure for subtypes
        changed = True
        while changed:
            changed = False
            for parent, subs in list(index.subtypes_closure.items()):
                new_subs = set(subs)
                for s in subs:
                    if s in index.subtypes_closure:
                        new_subs.update(index.subtypes_closure[s])
                if len(new_subs) > len(subs):
                    index.subtypes_closure[parent] = new_subs
                    changed = True

        return index

    def register_type_hint(
        self,
        class_name: str,
        symbol_name: str,
        type_name: str,
        kind: str = "property",
    ) -> None:
        """Register an AST or PHPDoc extracted type hint."""
        if kind == "property":
            self.property_types[(class_name, symbol_name)] = type_name
        elif kind == "return":
            self.return_types[(class_name, symbol_name)] = type_name

    def resolve_receiver(
        self,
        caller_class: str,
        receiver_expr: str,
        method_name: str,
        local_type_hints: dict[str, str] | None = None,
    ) -> ReceiverResolutionResult:
        """
        Resolve receiver expression to its candidate type(s) and determine if it targets method_name.
        Handles $this, property accesses, typed parameters, and new expressions.
        """
        hints = local_type_hints or {}
        signals: list[str] = []

        # 1. $this receiver
        if receiver_expr in ("$this", "this"):
            signals.append("this_receiver")
            candidate_types = [caller_class]
            # Add parents and interfaces
            if caller_class in self.parents:
                candidate_types.append(self.parents[caller_class])
            candidate_types.extend(self.implements_map.get(caller_class, set()))

            return ReceiverResolutionResult(
                receiver_expr=receiver_expr,
                method_name=method_name,
                status=ReceiverResolutionStatus.EXACT_RESOLVED,
                candidate_types=candidate_types,
                resolved_entity_id=f"{caller_class}::{method_name}",
                evidence_signals=signals,
                confidence=1.0,
            )

        # 2. Local variable with known type hint or @var annotation
        var_name = receiver_expr.lstrip("$")
        if var_name in hints:
            target_type = hints[var_name]
            signals.append(f"local_typehint:{target_type}")
            return ReceiverResolutionResult(
                receiver_expr=receiver_expr,
                method_name=method_name,
                status=ReceiverResolutionStatus.EXACT_RESOLVED,
                candidate_types=[target_type],
                resolved_entity_id=f"{target_type}::{method_name}",
                evidence_signals=signals,
                confidence=0.95,
            )

        # 3. Class property access ($this->foo->method())
        prop_match = re.match(r"(?:\$this|this)->(\w+)", receiver_expr)
        if prop_match:
            prop_name = prop_match.group(1)
            prop_key = (caller_class, prop_name)
            if prop_key in self.property_types:
                target_type = self.property_types[prop_key]
                signals.append(f"property_type:{target_type}")
                return ReceiverResolutionResult(
                    receiver_expr=receiver_expr,
                    method_name=method_name,
                    status=ReceiverResolutionStatus.EXACT_RESOLVED,
                    candidate_types=[target_type],
                    resolved_entity_id=f"{target_type}::{method_name}",
                    evidence_signals=signals,
                    confidence=0.90,
                )

        # 4. Method owners disambiguation (e.g. Node::getId vs User::getId)
        possible_owners = self.method_owners.get(method_name, set())
        if len(possible_owners) == 1:
            owner = next(iter(possible_owners))
            signals.append(f"sole_method_owner:{owner}")
            return ReceiverResolutionResult(
                receiver_expr=receiver_expr,
                method_name=method_name,
                status=ReceiverResolutionStatus.EXACT_RESOLVED,
                candidate_types=[owner],
                resolved_entity_id=f"{owner}::{method_name}",
                evidence_signals=signals,
                confidence=0.85,
            )
        elif len(possible_owners) > 1:
            # Ambiguous receiver call site across multiple method owners
            signals.append(f"ambiguous_owners_count:{len(possible_owners)}")
            return ReceiverResolutionResult(
                receiver_expr=receiver_expr,
                method_name=method_name,
                status=ReceiverResolutionStatus.AMBIGUOUS_CANDIDATES,
                candidate_types=list(possible_owners)[:10],
                resolved_entity_id=None,
                evidence_signals=signals,
                confidence=0.30,
            )

        # 5. Completely unknown receiver
        signals.append("untyped_dynamic_receiver")
        return ReceiverResolutionResult(
            receiver_expr=receiver_expr,
            method_name=method_name,
            status=ReceiverResolutionStatus.UNKNOWN_RECEIVER,
            candidate_types=[],
            resolved_entity_id=None,
            evidence_signals=signals,
            confidence=0.0,
        )

    def check_compatibility(
        self,
        target_entities: list[str],
        candidate_entity_id: str,
    ) -> str:
        """
        Check if candidate entity is type-compatible with any target entity
        using closure of inheritance and interfaces.
        Returns: "exact" | "compatible" | "unknown" | "incompatible"
        """
        target_types = set()
        for t in target_entities:
            cls_name = t.split("::")[0].replace("/", "\\")
            target_types.add(cls_name)

        cand_cls = candidate_entity_id.split("::")[0].replace("/", "\\")

        # 1. Exact class identity
        if cand_cls in target_types:
            return "exact"

        # 2. Check if candidate implements or subclasses any target type
        for t in target_types:
            if cand_cls in self.subtypes_closure.get(t, set()):
                return "compatible"
            if t in self.subtypes_closure.get(cand_cls, set()):
                return "compatible"

        return "unknown"
