"""
RCIR v8.1 — Context Compiler (PHASES 25 & 26).

Compiles ranked candidates into bounded, multi-granularity LLM prompt context
using entity-aware source span extraction rather than naive file-head slicing.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from rcir.retrieval.ranker import RankedCandidate


class ContextGranularity(str, Enum):
    SIGNATURE = "signature"
    DEFINITION = "definition"
    CALLER_SNIPPET = "caller_snippet"
    INTERFACE = "interface"
    ROUTE_DECLARATION = "route_declaration"
    SCHEMA_FRAGMENT = "schema_fragment"
    TEST_FRAGMENT = "test_fragment"
    SUMMARY = "summary"
    FULL_IMPLEMENTATION = "full_implementation"


@dataclass
class ContextEntry:
    """A compiled context slice for a single entity."""
    entity_id: str
    rank: int
    reason: str
    evidence: list[str]
    granularity: ContextGranularity
    source_file: str
    source_lines: list[int]
    estimated_tokens: int
    content_snippet: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "rank": self.rank,
            "reason": self.reason,
            "evidence": list(self.evidence),
            "granularity": self.granularity.value if isinstance(self.granularity, ContextGranularity) else str(self.granularity),
            "source_file": self.source_file,
            "source_lines": self.source_lines,
            "estimated_tokens": self.estimated_tokens,
            "content_snippet": self.content_snippet,
        }


@dataclass
class CompiledContext:
    """Bounded, compiled context payload ready for coding agent consumption."""
    entries: list[ContextEntry] = field(default_factory=list)
    total_estimated_tokens: int = 0
    token_budget: int = 4000
    candidates_evaluated: int = 0
    candidates_included: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_estimated_tokens": self.total_estimated_tokens,
            "token_budget": self.token_budget,
            "candidates_evaluated": self.candidates_evaluated,
            "candidates_included": self.candidates_included,
            "entries": [e.to_dict() for e in self.entries],
        }

    def render_prompt_markdown(self) -> str:
        """Render formatted markdown section for agent prompt."""
        lines = [
            "# RCIR v8.1 — Curated Engineering Context",
            f"**Budget:** {self.total_estimated_tokens} / {self.token_budget} tokens | **Included Entities:** {self.candidates_included}",
            "",
        ]

        for entry in self.entries:
            lines.append(f"## [{entry.rank}] {entry.entity_id} ({entry.granularity.value if hasattr(entry.granularity, 'value') else entry.granularity})")
            lines.append(f"- **File:** `{entry.source_file}` (lines {entry.source_lines[0]}-{entry.source_lines[1]})")
            lines.append(f"- **Inclusion Reason:** {entry.reason}")
            if entry.evidence:
                lines.append(f"- **Evidence:** {', '.join(entry.evidence)}")
            if entry.content_snippet:
                lines.append("```")
                lines.append(entry.content_snippet.strip())
                lines.append("```")
            lines.append("")

        return "\n".join(lines)


class ContextCompiler:
    """Compiles ranked candidates into a strictly token-budgeted context package."""

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root

    def _estimate_tokens(self, text: str) -> int:
        return max(1, math.ceil(len(text) / 4))

    def _locate_entity_span(
        self,
        lines: list[str],
        entity_symbol: str,
        granularity: ContextGranularity,
    ) -> tuple[int, int]:
        """Locate exact start and end line for entity rather than default top-of-file (PHASE 25)."""
        clean_symbol = entity_symbol.split("::")[-1].split("\\")[-1]
        pattern = re.compile(rf"\b(function|class|interface|trait|const|var|let)\s+{re.escape(clean_symbol)}\b|\b{re.escape(clean_symbol)}\s*\(", re.IGNORECASE)

        start_line = 1
        for idx, line in enumerate(lines, 1):
            if pattern.search(line):
                start_line = idx
                break

        # Adjust span based on granularity
        total_lines = len(lines)
        if granularity == ContextGranularity.FULL_IMPLEMENTATION:
            # Span up to 80 lines around definition
            s = max(1, start_line - 2)
            e = min(total_lines, start_line + 60)
            return s, e
        elif granularity == ContextGranularity.SIGNATURE:
            s = max(1, start_line - 3)
            e = min(total_lines, start_line + 15)
            return s, e
        elif granularity == ContextGranularity.CALLER_SNIPPET:
            s = max(1, start_line - 2)
            e = min(total_lines, start_line + 8)
            return s, e
        elif granularity == ContextGranularity.ROUTE_DECLARATION:
            # Look for route mapping
            for idx, line in enumerate(lines, 1):
                if "route" in line.lower() or "url" in line.lower() or clean_symbol.lower() in line.lower():
                    start_line = idx
                    break
            s = max(1, start_line - 1)
            e = min(total_lines, start_line + 25)
            return s, e
        elif granularity == ContextGranularity.TEST_FRAGMENT:
            s = max(1, start_line - 1)
            e = min(total_lines, start_line + 30)
            return s, e
        else:
            s = max(1, start_line)
            e = min(total_lines, start_line + 10)
            return s, e

    def _extract_snippet(
        self,
        file_path: str,
        entity_id: str,
        granularity: ContextGranularity,
    ) -> tuple[str, list[int], int]:
        """Extract appropriate code snippet based on requested granularity and entity location."""
        if not self.repo_root:
            stub = f"// Reference: {file_path} [{entity_id}] ({granularity.value})"
            return stub, [1, 10], self._estimate_tokens(stub)

        full_path = self.repo_root / file_path
        if not full_path.exists():
            stub = f"// File referenced: {file_path}"
            return stub, [1, 1], self._estimate_tokens(stub)

        try:
            lines = full_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            stub = f"// Error reading {file_path}"
            return stub, [1, 1], 10

        if not lines:
            return "", [1, 1], 0

        start_line, end_line = self._locate_entity_span(lines, entity_id, granularity)
        selected_lines = lines[start_line - 1 : end_line]
        snippet_text = "\n".join(selected_lines)
        return snippet_text, [start_line, end_line], self._estimate_tokens(snippet_text)

    def compile(
        self,
        ranked_candidates: list[RankedCandidate],
        token_budget: int = 4000,
    ) -> CompiledContext:
        """Compile ranked candidates into budgeted context bundle."""
        compiled = CompiledContext(
            token_budget=token_budget,
            candidates_evaluated=len(ranked_candidates),
        )

        current_tokens = 0

        for cand in ranked_candidates:
            ev = cand.evidence

            # Determine appropriate granularity
            if cand.rank == 1:
                granularity = ContextGranularity.FULL_IMPLEMENTATION
                reason = "Primary change target entity"
            elif "route" in ev.edge_types or ev.boundary_contract == "route_matched":
                granularity = ContextGranularity.ROUTE_DECLARATION
                reason = "Boundary route declaration / client contract"
            elif "direct_test" in ev.test_relationship:
                granularity = ContextGranularity.TEST_FRAGMENT
                reason = "Direct regression verification test suite"
            elif cand.rank <= 5:
                granularity = ContextGranularity.SIGNATURE
                reason = "Direct 1-hop caller or contract interface"
            else:
                granularity = ContextGranularity.SUMMARY
                reason = "Transitive dependency in blast radius"

            snippet, line_range, est_tokens = self._extract_snippet(cand.file_path, cand.entity_id, granularity)

            # Check budget headroom
            if current_tokens + est_tokens > token_budget:
                if granularity != ContextGranularity.SUMMARY:
                    granularity = ContextGranularity.SUMMARY
                    snippet = f"// Brief reference: {cand.file_path} (rank {cand.rank})"
                    line_range = [1, 1]
                    est_tokens = self._estimate_tokens(snippet)

                if current_tokens + est_tokens > token_budget:
                    # Budget full, stop compiling further entries
                    break

            evidence_items = []
            if ev.entity_match != "none":
                evidence_items.append(f"entity_match:{ev.entity_match}")
            if ev.resolution_class != "unknown":
                evidence_items.append(f"resolution:{ev.resolution_class}")
            if ev.type_compatibility != "unknown":
                evidence_items.append(f"type:{ev.type_compatibility}")
            if ev.boundary_contract != "none":
                evidence_items.append(f"boundary:{ev.boundary_contract}")
            if ev.test_relationship != "none":
                evidence_items.append(f"test:{ev.test_relationship}")

            entry = ContextEntry(
                entity_id=cand.entity_id,
                rank=cand.rank,
                reason=reason,
                evidence=evidence_items,
                granularity=granularity,
                source_file=cand.file_path,
                source_lines=line_range,
                estimated_tokens=est_tokens,
                content_snippet=snippet,
            )

            compiled.entries.append(entry)
            current_tokens += est_tokens
            compiled.candidates_included += 1

        compiled.total_estimated_tokens = current_tokens
        return compiled
