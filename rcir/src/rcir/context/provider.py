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
from rcir.context.models import ContextRetrievalResult
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

        entries_data = [e.to_dict() for e in compiled.entries]
        return ContextRetrievalResult(
            entries=entries_data,
            entity_ids=newly_seen,
            rendered_markdown=compiled.render_prompt_markdown(),
            tokens_added=compiled.total_estimated_tokens,
            duplicates_skipped=len(seen_entities),
            requested_symbol=symbol,
            source_task_id="",
            budget=token_budget,
            candidate_count=len(candidate_vectors),
            remaining_budget=max(0, token_budget - compiled.total_estimated_tokens),
            provider_name="RCIRContextProvider",
            metadata={
                "status": "success",
                "canonical_target": canonical_target,
                "session": self.session_state.to_dict(),
            },
        )


class RCIRContextError(Exception):
    """Raised when live RCIR retrieval fails to produce verified context."""
    pass


class LiveRCIRContextProvider(RCIRContextProvider):
    """
    Live RCIR Context Provider for benchmark and agent trials.
    Executes live entity resolution, graph retrieval, ranking, and compilation
    directly against the target repository without precompiled task bundles or DEV mappings.
    """

    def __init__(
        self,
        target_repo: Path,
        graph_path: Optional[Path] = None,
        token_budget: int = 4000,
        expected_commit: Optional[str] = None,
    ):
        self.target_repo = Path(target_repo).resolve()
        if not self.target_repo.exists():
            raise RCIRContextError(f"Target repository not found: {self.target_repo}")

        # Resolve graph path
        if not graph_path:
            candidates = [
                self.target_repo.parent / "rcir" / "nextcloud_graph.json",
                Path(__file__).resolve().parent.parent.parent.parent / "experiments" / "nextcloud_validation" / "rcir" / "nextcloud_graph.json",
            ]
            for c in candidates:
                if c.exists():
                    graph_path = c
                    break

        if not graph_path or not graph_path.exists():
            raise RCIRContextError(f"RCIR dependency graph not found for target {self.target_repo}")

        self.graph_path = graph_path
        import hashlib
        import json

        graph_bytes = graph_path.read_bytes()
        self.graph_sha256 = hashlib.sha256(graph_bytes).hexdigest()
        raw_graph = json.loads(graph_bytes.decode("utf-8"))

        # Verify graph target commit if present (F27)
        self.graph_target_sha = raw_graph.get("metadata", {}).get("target_commit", raw_graph.get("target_commit", ""))
        if expected_commit and self.graph_target_sha:
            if expected_commit.lower() != self.graph_target_sha.lower():
                raise RCIRContextError(
                    f"Graph target revision mismatch: graph built for {self.graph_target_sha}, but worktree expects {expected_commit}"
                )

        # F01: Bind ContextCompiler directly to target_repo so snippet extraction reads real files
        compiler = ContextCompiler(repo_root=self.target_repo)

        # F11: Populate CanonicalEntityRegistry from graph nodes
        registry = CanonicalEntityRegistry()
        nodes = raw_graph.get("nodes", {})
        if isinstance(nodes, dict):
            for node_id, node_data in nodes.items():
                fpath = node_data.get("file", "")
                if fpath:
                    registry.alias_to_uris.setdefault(fpath, set()).add(node_id)
                # Short symbol name (after last \ or ::)
                short_name = node_id.replace("::", "\\").split("\\")[-1]
                if short_name and len(short_name) >= 3:
                    registry.alias_to_uris.setdefault(short_name, set()).add(node_id)

        super().__init__(raw_graph=raw_graph, compiler=compiler, registry=registry)
        self.default_token_budget = token_budget
        self.last_retrieval_trace: dict[str, Any] = {}

    def reset_session(self) -> None:
        """F03: Resets session state to guarantee per-trial isolation with zero cross-trial leakage."""
        self.session_state = ContextSessionState()

    def compile_task_context(
        self,
        task_id: str,
        instructions: str,
        token_budget: Optional[int] = None,
        reject_stubs: bool = True,
    ) -> str:
        """
        Derives change intent from instructions, retrieves candidates from graph,
        ranks them deterministically, and compiles markdown context.
        Fails closed on zero context or unresolved stubs.
        """
        # Guarantee per-trial session isolation (F03)
        self.reset_session()

        budget = token_budget or self.default_token_budget
        if not self.raw_graph.get("nodes") and not self.raw_graph.get("edges"):
            raise RCIRContextError(f"RCIR_CONTEXT_ERROR: zero retrieved context for task {task_id} (empty graph)")

        # F11: Robust multi-entity symbol extraction
        import re

        # Look for PHP namespaces, paths, or qualified identifiers
        namespace_matches = re.findall(r'[A-Za-z0-9_]+(?:\\[A-Za-z0-9_]+)+', instructions)
        path_matches = re.findall(r'[A-Za-z0-9_/-]+\.php', instructions)
        general_symbols = re.findall(r'[A-Z][a-zA-Z0-9_]{3,}', instructions)

        common_words = {
            "Nextcloud", "Server", "Implement", "Create", "Update", "Method",
            "Class", "Interface", "Function", "Return", "Public", "Private",
            "When", "Then", "Should", "Ensure", "Verify", "Error", "Test"
        }
        filtered_symbols = [s for s in general_symbols if s not in common_words]

        # Prioritize matching graph entities
        candidates_to_check = namespace_matches + path_matches + filtered_symbols
        nodes = self.raw_graph.get("nodes", {})

        primary_symbol = None
        for cand in candidates_to_check:
            if cand in nodes or cand in getattr(self.registry, "alias_to_uris", {}):
                primary_symbol = cand
                break

        if not primary_symbol and candidates_to_check:
            primary_symbol = candidates_to_check[0]

        if not primary_symbol:
            raise RCIRContextError(f"RCIR_CONTEXT_ERROR: zero retrieved context for task {task_id} (no symbol identified)")

        res = self.retrieve(symbol=primary_symbol, query=instructions, token_budget=budget)

        if not res.rendered_markdown or res.tokens_added == 0:
            raise RCIRContextError(f"RCIR_CONTEXT_ERROR: zero retrieved context for task {task_id}")

        # F01: Reject stub-only results in formal benchmarking
        if reject_stubs and res.entries:
            verified_spans = [
                e for e in res.entries
                if (e.get("source_exists", False) if isinstance(e, dict) else getattr(e, "source_exists", False))
                and ((e.get("representation_type", "") if isinstance(e, dict) else getattr(e, "representation_type", "")).upper() == "SOURCE_SPAN")
            ]
            if not verified_spans:
                raise RCIRContextError(
                    f"RCIR_CONTEXT_ERROR: rejected stub-only context for task {task_id}; no verified source-backed spans produced"
                )

        self.last_retrieval_trace = {
            "task_id": task_id,
            "primary_symbol": primary_symbol,
            "candidate_count": res.candidate_count,
            "tokens_added": res.tokens_added,
            "entries_count": len(res.entries),
            "graph_path": str(self.graph_path),
            "graph_sha256": getattr(self, "graph_sha256", ""),
        }
        return res.rendered_markdown

