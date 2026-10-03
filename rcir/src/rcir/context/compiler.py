"""
RCIR v8 — Context Compiler (PHASE 13).

Compiles ranked candidates into bounded, multi-granularity LLM prompt context.
Separates raw candidate retrieval from final context synthesis.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

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
            "# RCIR v8 — Curated Engineering Context",
            f"**Budget:** {self.total_estimated_tokens} / {self.token_budget} tokens | **Included Entities:** {self.candidates_included}",
            "",
        ]

        for entry in self.entries:
            lines.append(f"## [{entry.rank}] {entry.entity_id} ({entry.granularity.value})")
            lines.append(f"- **File:** `{entry.source_file}` (lines {entry.source_lines})")
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

    def _extract_snippet(
        self,
        file_path: str,
        granularity: ContextGranularity,
    ) -> tuple[str, list[int], int]:
        """Extract appropriate code snippet based on requested granularity."""
        if not self.repo_root:
            stub = f"// Reference: {file_path} [{granularity.value}]"
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

        # Granularity-specific extraction
        if granularity == ContextGranularity.FULL_IMPLEMENTATION:
            selected = lines[:120]  # Cap at 120 lines
            return "\n".join(selected), [1, len(selected)], self._estimate_tokens("\n".join(selected))

        elif granularity in (ContextGranularity.ROUTE_DECLARATION, ContextGranularity.SCHEMA_FRAGMENT):
            # First 40 lines usually contain route/table defs
            selected = lines[:40]
            return "\n".join(selected), [1, len(selected)], self._estimate_tokens("\n".join(selected))

        elif granularity == ContextGranularity.TEST_FRAGMENT:
            # First 35 lines of test class
            selected = lines[:35]
            return "\n".join(selected), [1, len(selected)], self._estimate_tokens("\n".join(selected))

        elif granularity == ContextGranularity.SIGNATURE:
            # Header + first 25 lines
            selected = lines[:25]
            return "\n".join(selected), [1, len(selected)], self._estimate_tokens("\n".join(selected))

        else:
            # Summary / Caller snippet: first 15 lines
            selected = lines[:15]
            return "\n".join(selected), [1, len(selected)], self._estimate_tokens("\n".join(selected))

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

            snippet, line_range, est_tokens = self._extract_snippet(cand.file_path, granularity)

            # Check budget headroom
            if current_tokens + est_tokens > token_budget:
                # Try downgrading to summary if not already summary
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
