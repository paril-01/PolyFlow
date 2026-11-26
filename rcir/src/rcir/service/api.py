"""Snapshot-bound context, strict serialized budgets and scoped expansion."""
from __future__ import annotations

from collections import OrderedDict
import json
from pathlib import Path
import threading
import time

from rcir.context.tokenizer import TiktokenTokenCounter
from .index import SourceIndex
from .snapshot import Snapshot, ServiceError, canonical, digest, safe_path


class RepositoryService:
    def __init__(self, repo, ref="HEAD", *, allow_overlay=False, allow_unversioned=False, source_only=False, counter=None, cache_entries=256):
        self.root = Path(repo).resolve()
        self.ref = ref
        self.allow_overlay = allow_overlay
        self.allow_unversioned = allow_unversioned
        self.source_only = source_only
        self.counter = counter or TiktokenTokenCounter()
        if self.counter.get_provenance().get("token_count_type") != "exact":
            raise ServiceError("UNSUPPORTED", "An available exact tokenizer is required")
        if type(cache_entries) is not int or cache_entries < 1:
            raise ServiceError("INVALID_SCOPE", "Cache must have positive capacity")
        self.cache_entries = cache_entries
        self.originals = OrderedDict()
        self.lock = threading.RLock()
        self.generation = 0
        self.retrieval_method = "BM25_SOURCE_SYMBOL_V1"
        self.candidate_provider = None
        self.refresh()

    def refresh(self):
        with self.lock:
            snapshot = Snapshot(self.root, self.ref, self.allow_overlay, self.allow_unversioned, self.source_only)
            index = SourceIndex(snapshot)
            snapshot.verify()
            self.snapshot, self.index = snapshot, index
            self.generation += 1
            self.originals.clear()
            return self.status()

    def status(self):
        return {"schema_version": "rcir.status.v1", **self.snapshot.manifest(), "generation": self.generation,
                "indexed_files": len(self.snapshot.files), "tokenizer": self.counter.get_provenance(),
                "retrieval": self.retrieval_method, "graph_provider": "EXPERIMENTAL_CANDIDATE_PROVIDER" if self.candidate_provider else "NOT_CONFIGURED",
                "language_support": {"python": "AST_DEFINITIONS_AND_SYNTACTIC_IMPORTS", "other_text": "LEXICAL_INFERRED_ONLY"},
                "limitations": self.index.unsupported, "read_only": True, "release_eligible": False}

    def _measure(self, envelope):
        previous = -1
        envelope["tokens_consumed"] = 0
        for _ in range(12):
            count = self.counter.count(canonical(envelope).decode("utf-8"))
            if count == previous:
                return count
            envelope["tokens_consumed"] = count
            previous = count
        raise ServiceError("BUDGET_INSUFFICIENT", "Token envelope did not stabilize")

    def retrieve(self, query, token_budget=4000, *, required_symbols=()):
        if not isinstance(query, str) or not query.strip() or len(query) > 16384:
            raise ServiceError("UNRESOLVED", "A bounded nonempty query is required")
        if type(token_budget) is not int or token_budget < 1 or token_budget > 1_000_000:
            raise ServiceError("BUDGET_INSUFFICIENT", "Budget must be an integer from 1 to 1000000")
        if not isinstance(required_symbols, (tuple, list)) or not all(isinstance(s, str) for s in required_symbols):
            raise ServiceError("INVALID_SCOPE", "Required symbols must be a string list")
        with self.lock:
            started = time.perf_counter()
            self.snapshot.verify()
            candidates = self.candidate_provider(query) if self.candidate_provider else self.index.candidates(query)
            envelope = {"schema_version": "rcir.context_evidence.v2", "status": "COMPLETE" if candidates else "UNRESOLVED",
                        "query": query, "snapshot_id": self.snapshot.id, "target_repo_commit": self.snapshot.commit,
                        "generation": self.generation, "token_budget": token_budget, "tokens_consumed": 0,
                        "tokenizer_name": self.counter.get_provenance()["tokenizer"],
                        "token_count_type": "exact_serialized_envelope", "evidence_items": [], "omitted_targets": [],
                        "omitted_count": 0, "omission_reason": None, "retrieval_method": self.retrieval_method}
            required = set(required_symbols)
            present = {s["symbol_name"] for s in candidates}
            if required - present:
                raise ServiceError("UNRESOLVED", "Required symbol is unavailable or ambiguous")
            for symbol in required:
                if sum(s["symbol_name"] == symbol for s in candidates) > 1:
                    raise ServiceError("AMBIGUOUS", "Required symbol resolves to multiple source definitions")
            selected, handles = [], []
            # Required candidates are packed before optional context, with no silent loss.
            candidates.sort(key=lambda s: (s["symbol_name"] not in required, -s["score"], s["file_path"], s["start_byte"]))
            for span in candidates:
                if any(span["file_path"] == prior["file_path"] and span["start_byte"] >= prior["start_byte"] and span["end_byte"] <= prior["end_byte"] for prior in selected):
                    continue
                identifier = digest(canonical([self.snapshot.id, span["file_path"], span["start_byte"], span["end_byte"], span["span_sha256"]]))
                item = {**span, "evidence_id": f"{self.snapshot.id}:{identifier}", "required": span["symbol_name"] in required}
                envelope["evidence_items"] = selected + [item]
                count = self._measure(envelope)
                if count <= token_budget:
                    selected.append(item)
                    handles.append((item["evidence_id"], item))
                elif item["required"]:
                    raise ServiceError("BUDGET_INSUFFICIENT", f"Pinned source requires at least {count} serialized tokens")
                else:
                    envelope["omitted_count"] += 1
                    envelope["omission_reason"] = "TOKEN_BUDGET"
                    envelope["status"] = "PARTIAL"
                envelope["evidence_items"] = selected
            # Metadata is included too. Drop optional spans if omission metadata grew.
            while self._measure(envelope) > token_budget:
                if not selected or selected[-1]["required"]:
                    raise ServiceError("BUDGET_INSUFFICIENT", f"Envelope requires at least {envelope['tokens_consumed']} tokens")
                selected.pop()
                envelope["omitted_count"] += 1
                envelope["status"], envelope["omission_reason"] = "PARTIAL", "TOKEN_BUDGET"
            self.snapshot.verify()
            selected_ids = {item["evidence_id"] for item in selected}
            for handle, item in handles:
                if handle in selected_ids:
                    self.originals[handle] = dict(item)
            while len(self.originals) > self.cache_entries:
                self.originals.popitem(last=False)
            # Timing remains out of the counted delivery payload; caller receipts can measure it.
            self.last_receipt = {"snapshot_id": self.snapshot.id, "query_seconds": time.perf_counter() - started,
                                 "candidate_count": len(candidates), "delivered_count": len(selected)}
            return envelope

    def expand(self, evidence_id, token_budget=4000):
        with self.lock:
            self.snapshot.verify()
            if not isinstance(evidence_id, str) or not evidence_id.startswith(self.snapshot.id + ":"):
                raise ServiceError("STALE", "Handle is not bound to current snapshot")
            if evidence_id not in self.originals:
                raise ServiceError("UNRESOLVED", "Evidence handle is unavailable or evicted")
            result = {"schema_version": "rcir.evidence_expand.v1", "snapshot_id": self.snapshot.id,
                      "token_budget": token_budget, "tokens_consumed": 0, "evidence": self.originals[evidence_id]}
            if type(token_budget) is not int or token_budget < 1 or self._measure(result) > token_budget:
                raise ServiceError("BUDGET_INSUFFICIENT", "Expansion does not fit serialized budget")
            self.snapshot.verify()
            self.originals.move_to_end(evidence_id)
            return result

    def impact(self, path):
        with self.lock:
            self.snapshot.verify()
            safe_path(self.root, path)
            if path not in self.snapshot.files:
                raise ServiceError("UNRESOLVED", "File is not in the indexed source scope")
            return {"snapshot_id": self.snapshot.id, "path": path, "affected_files": self.index.impact(path),
                    "relation_scope": "RESOLVED_PYTHON_MODULE_IMPORTS_ONLY", "relations": self.index.relations,
                    "completeness": "PARTIAL_STATIC_IMPORTS_NOT_DYNAMIC_CALL_GRAPH"}

    def save_manifest(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_bytes(canonical(self.status()))
        temporary.replace(path)
