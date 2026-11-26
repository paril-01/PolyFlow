"""Canonical provider adapter: explicit identity, entries contract, no fallback."""
from pathlib import Path
import json
from rcir.context.provider import LiveRCIRContextProvider
from rcir.entities.canonical import CanonicalEntityID, EntityKind
from rcir.service import RepositoryService, ServiceError


class R1RCIRAdapter:
    def __init__(self, target_repo: Path, graph_path=None, expected_commit=None):
        self.service = RepositoryService(target_repo, ref=expected_commit or "HEAD")
        if not graph_path or not Path(graph_path).is_file():
            raise ServiceError("INVALID_SCOPE", "R1 requires an explicit existing canonical graph")
        graph = json.loads(Path(graph_path).read_text(encoding="utf-8"))
        identity = graph.get("metadata", {}).get("target_commit", graph.get("target_commit"))
        if identity != self.service.snapshot.commit:
            raise ServiceError("STALE", "Graph target identity is missing or mismatched")
        if not graph.get("nodes"):
            raise ServiceError("UNRESOLVED", "Canonical graph is empty")
        if not isinstance(graph["nodes"], dict):
            raise ServiceError("UNSUPPORTED", "Canonical provider requires keyed entity nodes; raw extractor graphs require explicit normalization")
        self.graph = graph
        self.provider = LiveRCIRContextProvider(Path(target_repo), Path(graph_path), expected_commit=identity)
        # The legacy provider populated aliases without registering entities;
        # unique alias resolution then indexed an empty entity dictionary.
        for identifier, node in graph["nodes"].items():
            if identifier.startswith("python://") and ":" in identifier[len("python://"):]:
                # Legacy from_uri only parses PHP/TS; construct the existing
                # canonical Python model rather than registering a file alias.
                qualified = identifier[len("python://"):].split(":", 1)[1]
                owner, _, symbol = qualified.rpartition(".")
                entity = CanonicalEntityID(repository=self.service.root.name, language="python", file=node.get("file", ""),
                    namespace="", owner_type=owner, symbol=symbol or qualified, kind=EntityKind.METHOD if owner else EntityKind.FUNCTION)
            else:
                entity = CanonicalEntityID.from_uri(identifier, repository=self.service.root.name, file_hint=node.get("file", ""))
            if entity.uri != identifier:
                raise ServiceError("INVALID_SCOPE", "Graph entity URI is not canonical")
            self.provider.registry.register(entity)
        self.service.retrieval_method = "R1_CANONICAL_PROVIDER"
        self.service.candidate_provider = self.candidates

    def candidates(self, query):
        self.provider.reset_session()
        # Provider-specific estimates only select candidates. Delivery below is
        # recounted from the same raw snapshot as the lexical comparator.
        result = self.provider.retrieve(symbol=query.split()[0], query=query, token_budget=50000)
        candidates = []
        for rank, entry in enumerate(result.entries):
            path, lines = entry.get("source_file"), entry.get("source_lines", [])
            node = self.graph["nodes"].get(entry.get("entity_id"), {})
            if node.get("file"):
                path = node["file"]
                if node.get("line") is not None and node.get("end_line") is not None:
                    lines = [node["line"], node["end_line"]]
            if path not in self.service.snapshot.files or len(lines) != 2:
                raise ServiceError("UNRESOLVED", "Provider returned an unavailable source span")
            source_lines = self.service.snapshot.files[path].raw.splitlines()
            start, end = lines
            if not (type(start) is int and type(end) is int and 1 <= start <= end <= len(source_lines)):
                raise ServiceError("INVALID_SCOPE", "Provider returned invalid source coordinates")
            span = self.service.index._span(path, start, end, entry.get("entity_id", ""),
                                             "INFERRED", "canonical_provider_source_rehydrated")
            candidates.append({**span, "score": float(len(result.entries) - rank)})
        return candidates

    def retrieve(self, query, max_tokens=4000):
        return self.service.retrieve(query, max_tokens)
