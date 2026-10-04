"""
RCIR v8.3 — Iterative Context Provider & Session Tracking (PHASES 64, 65).

Implements the concrete RCIRContextProvider:
- Integrates TargetResolver -> Impact Plane -> Selected Ranker -> ContextPlanner -> ContextCompiler
- Maintains agent session state: entities_seen, spans_seen, files_seen, tokens_already_supplied
- Filters out already-supplied context to guarantee incremental, non-redundant context expansion
- Eliminates silent text grep fallbacks
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from orchestrator.tools import ContextProvider
from rcir.context.compiler import ContextCompiler, CompiledContext
from rcir.context.planner import ContextPlanner
from rcir.entities.canonical import CanonicalEntityRegistry, ResolutionResult, AliasResolution
from rcir.query.change_spec import ChangeOperation, ChangeSpecification
from rcir.retrieval.evidence_vector import EvidenceVector
from rcir.retrieval.ranker import DeterministicRanker, RankerConfig, RankedCandidate


@dataclass
class ContextSessionState:
    """Tracks state across multiple agent context requests within a single coding task."""
    entities_seen: set[str] = field(default_factory=set)
    spans_seen: set[tuple[str, int, int]] = field(default_factory=set)
    files_seen: set[str] = field(default_factory=set)
    tokens_already_supplied: int = 0
    request_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities_seen_count": len(self.entities_seen),
            "files_seen": sorted(list(self.files_seen)),
            "tokens_already_supplied": self.tokens_already_supplied,
            "request_count": self.request_count,
        }


class RCIRContextProvider(ContextProvider):
    """
    Production RCIR iterative context provider for coding agents.
    Provides verified, progressive architectural context without text-search fallbacks.
    """

    def __init__(
        self,
        raw_graph: dict[str, Any] | None = None,
        ranker: DeterministicRanker | None = None,
        compiler: ContextCompiler | None = None,
        registry: CanonicalEntityRegistry | None = None,
    ):
        self.raw_graph = raw_graph or {"nodes": {}, "edges": []}
        self.ranker = ranker or DeterministicRanker(RankerConfig(use_cascaded_ranking=True))
        self.compiler = compiler or ContextCompiler()
        self.registry = registry or CanonicalEntityRegistry()
        self.session_state = ContextSessionState()

    def retrieve(
        self,
        symbol: str,
        query: Optional[str] = None,
        already_seen: Optional[set[str]] = None,
        token_budget: int = 1500,
    ) -> dict[str, Any]:
        """
        Execute iterative context retrieval for symbol/query:
        1. Resolve canonical symbol
        2. Generate candidate evidence from graph
        3. Rank candidates
        4. Plan and compile new, unseen context units within token_budget
        """
        self.session_state.request_count += 1
        seen_entities = set(self.session_state.entities_seen)
        if already_seen:
            seen_entities.update(already_seen)

        # 1. Target resolution
        res = self.registry.resolve(symbol)
        canonical_target = res.canonical_id or symbol

        spec = ChangeSpecification(
            operation=ChangeOperation.BEHAVIOR_CHANGE,
            requested_symbol=symbol,
            canonical_target_ids=[canonical_target],
            description=query or f"Context inspection for {symbol}",
        )

        # 2. Extract graph candidates connected to canonical target
        candidate_vectors: list[EvidenceVector] = []
        edges = self.raw_graph.get("edges", [])

        # Target candidate
        v_target = EvidenceVector(
            entity_id=canonical_target,
            file_path=canonical_target.split("::")[0].replace("php://", "").replace("ts://", ""),
            entity_match="exact",
            resolution_class="static_exact",
            traversal_score=1.0,
        )
        if v_target.entity_id not in seen_entities:
            candidate_vectors.append(v_target)

        # Direct callers and callees
        for e in edges:
            src = e.get("source", "")
            tgt = e.get("target", "")
            etype = e.get("edge_type", "calls")
            res_class = e.get("resolution", "static_exact")

            if symbol in tgt or canonical_target in tgt:
                cand_id = src
                if cand_id not in seen_entities:
                    fp = cand_id.split("::")[0].replace("php://", "").replace("ts://", "")
                    candidate_vectors.append(EvidenceVector(
                        entity_id=cand_id,
                        file_path=fp,
                        resolution_class=res_class,
                        edge_types=[etype],
                        hop_distance=1,
                        traversal_score=0.8,
                    ))
            elif symbol in src or canonical_target in src:
                cand_id = tgt
                if cand_id not in seen_entities:
                    fp = cand_id.split("::")[0].replace("php://", "").replace("ts://", "")
                    candidate_vectors.append(EvidenceVector(
                        entity_id=cand_id,
                        file_path=fp,
                        resolution_class=res_class,
                        edge_types=[etype],
                        hop_distance=1,
                        traversal_score=0.7,
                    ))

        # 3. Rank unseen candidates
        ranked = self.ranker.rank(candidate_vectors)

        # 4. Plan and compile
        plan = ContextPlanner.create_plan(
            ranked_candidates=ranked,
            token_budget=token_budget,
            spec=spec,
        )

        compiled = self.compiler.compile(
            ranked_candidates=ranked,
            token_budget=token_budget,
            pinned_targets=set(spec.canonical_target_ids),
            plan=plan,
        )

        # Update session state with newly supplied context
        newly_seen: list[str] = []
        for entry in compiled.entries:
            self.session_state.entities_seen.add(entry.entity_id)
            self.session_state.files_seen.add(entry.source_file)
            lines = entry.source_lines
            if len(lines) >= 2:
                self.session_state.spans_seen.add((entry.source_file, lines[0], lines[1]))
            newly_seen.append(entry.entity_id)

        self.session_state.tokens_already_supplied += compiled.total_estimated_tokens

        return {
            "status": "success",
            "symbol": symbol,
            "canonical_target": canonical_target,
            "entries_count": len(compiled.entries),
            "new_entities": newly_seen,
            "tokens_consumed": compiled.total_estimated_tokens,
            "rendered_markdown": compiled.render_prompt_markdown(),
            "session": self.session_state.to_dict(),
        }
