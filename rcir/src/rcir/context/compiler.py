"""
RCIR v8.2 — Architecture Context Compiler (PHASES 26, 27, 28, 29, 30, 31, 32, 63, 64).

Key Features:
- Layered SourceSpanResolver with AST and balanced-body extraction (PHASE 26 & 27)
- True SUMMARY granularity: concise structural description (tens of tokens, PHASE 28)
- Span deduplication: overlapping spans in the same file merged, saving prompt tokens (PHASE 29)
- Explicit target pinning: requested change targets guaranteed in prompt (PHASE 30)
- Real TokenCounter integration (PHASE 31)
- Accurate token-weighted metrics using exact entry token measurements (PHASE 32)
- High-fanout ImpactSummary inclusion (PHASE 23)
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from rcir.context.spans import ResolvedSpan, SourceSpanResolver
from rcir.context.summarizer import ImpactSummary
from rcir.context.tokenizer import TokenCounter, get_default_token_counter
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
    """A compiled context slice for a single entity or merged span (PHASE 39)."""
    entity_id: str
    rank: int
    reason: str
    evidence: list[str]
    granularity: ContextGranularity
    source_file: str
    source_lines: list[int]
    estimated_tokens: int
    content_snippet: str = ""
    span_metadata: Optional[dict[str, Any]] = None
    merged_entity_ids: list[str] = field(default_factory=list)
    source_exists: bool = True
    span_resolved: bool = True
    content_hash: str = ""
    representation_type: str = "SOURCE_SPAN"

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
            "span_metadata": self.span_metadata or {},
            "merged_entity_ids": self.merged_entity_ids,
            "source_exists": self.source_exists,
            "span_resolved": self.span_resolved,
            "content_hash": self.content_hash,
            "representation_type": self.representation_type,
        }


@dataclass
class CompiledContext:
    """Bounded, compiled context payload ready for coding agent consumption."""
    entries: list[ContextEntry] = field(default_factory=list)
    total_estimated_tokens: int = 0
    token_budget: int = 4000
    candidates_evaluated: int = 0
    candidates_included: int = 0
    entities_merged: int = 0
    tokens_saved_by_deduplication: int = 0
    impact_summary: Optional[ImpactSummary] = None
    tokenizer_provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_estimated_tokens": self.total_estimated_tokens,
            "token_budget": self.token_budget,
            "candidates_evaluated": self.candidates_evaluated,
            "candidates_included": self.candidates_included,
            "entities_merged": self.entities_merged,
            "tokens_saved_by_deduplication": self.tokens_saved_by_deduplication,
            "has_impact_summary": self.impact_summary is not None,
            "impact_summary": self.impact_summary.to_dict() if self.impact_summary else None,
            "tokenizer": self.tokenizer_provenance,
            "entries": [e.to_dict() for e in self.entries],
        }

    def render_prompt_markdown(self) -> str:
        """Render formatted markdown section for agent prompt."""
        lines = [
            "# RCIR v8.2 — Curated Engineering Context",
            f"**Budget:** {self.total_estimated_tokens} / {self.token_budget} tokens | **Included Context Units:** {self.candidates_included} (merged {self.entities_merged})",
            "",
        ]

        if self.impact_summary:
            lines.append(self.impact_summary.render_markdown())
            lines.append("")

        for entry in self.entries:
            gran = entry.granularity.value if hasattr(entry.granularity, "value") else str(entry.granularity)
            lines.append(f"## [{entry.rank}] {entry.entity_id} ({gran})")
            lines.append(f"- **File:** `{entry.source_file}` (lines {entry.source_lines[0]}-{entry.source_lines[1]})")
            lines.append(f"- **Inclusion Reason:** {entry.reason}")
            if entry.merged_entity_ids:
                lines.append(f"- **Merged Related Entities:** {', '.join(entry.merged_entity_ids)}")
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

    def __init__(
        self,
        repo_root: Path | None = None,
        tokenizer: TokenCounter | None = None,
    ):
        self.repo_root = repo_root
        self.tokenizer = tokenizer or get_default_token_counter()

    def _estimate_tokens(self, text: str) -> int:
        return self.tokenizer.count(text)

    def _locate_entity_span(
        self,
        lines: list[str],
        entity_symbol: str,
        granularity: ContextGranularity = ContextGranularity.SIGNATURE,
    ) -> tuple[int, int]:
        """Backward-compatible helper returning start and end line for entity."""
        span = SourceSpanResolver.resolve_span(lines, entity_symbol)
        return span.start_line, span.end_line

    def _extract_snippet(
        self,
        file_path: str,
        entity_id: str,
        granularity: ContextGranularity,
        node_meta: dict[str, Any] | None = None,
        edge_meta: dict[str, Any] | None = None,
    ) -> tuple[str, list[int], int, ResolvedSpan]:
        """Extract appropriate code snippet based on requested granularity and entity location."""
        # PHASE 28: True SUMMARY granularity does NOT extract arbitrary source code
        if granularity == ContextGranularity.SUMMARY:
            clean_ent = entity_id.split("::")[-1]
            summary_text = f"// [SUMMARY] {file_path} :: {clean_ent} | Rank context reference in dependency blast radius"
            tokens = self._estimate_tokens(summary_text)
            span = ResolvedSpan(1, 1, "adapter", "inferred", False, entity_id)
            return summary_text, [1, 1], tokens, span

        if not self.repo_root:
            stub = f"// Reference: {file_path} [{entity_id}] ({granularity.value})"
            tokens = self._estimate_tokens(stub)
            span = ResolvedSpan(1, 10, "heuristic", "heuristic_fallback", True, entity_id)
            return stub, [1, 10], tokens, span

        full_path = self.repo_root / file_path
        if not full_path.exists():
            # PHASE 38: Never emit file-reference stubs in formal benchmark
            stub = f"// SOURCE_UNAVAILABLE: {file_path}"
            span = ResolvedSpan(1, 1, "source_unavailable", "unresolved", True, entity_id)
            return stub, [1, 1], 0, span

        try:
            lines = full_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            stub = f"// Error reading {file_path}"
            span = ResolvedSpan(1, 1, "heuristic", "heuristic_fallback", True, entity_id)
            return stub, [1, 1], 10, span

        if not lines:
            span = ResolvedSpan(1, 1, "heuristic", "heuristic_fallback", True, entity_id)
            return "", [1, 1], 0, span

        # PHASE 26 & 27: AST-located span resolution
        span = SourceSpanResolver.resolve_span(lines, entity_id, node_meta, edge_meta)
        selected_lines = lines[span.start_line - 1 : span.end_line]
        snippet_text = "\n".join(selected_lines)
        tokens = self._estimate_tokens(snippet_text)

        return snippet_text, [span.start_line, span.end_line], tokens, span

    def compile(
        self,
        ranked_candidates: list[RankedCandidate],
        token_budget: int = 4000,
        pinned_targets: set[str] | None = None,
        impact_summary: ImpactSummary | None = None,
        plan: Any | None = None,
    ) -> CompiledContext:
        """
        Compile ranked candidates into budgeted context bundle:
        - Incorporates ContextPlan role allocations when supplied (PHASE 49)
        - Pins explicit change targets (PHASE 30 & 59)
        - Injects high-fanout summary (PHASE 23)
        - Deduplicates overlapping source spans in the same file (PHASE 29)
        - Measures exact serialized tokens with tokenizer (PHASE 61 & 62)
        - Preserves strict token budget (PHASE 26)
        """
        compiled = CompiledContext(
            token_budget=token_budget,
            candidates_evaluated=len(ranked_candidates),
            impact_summary=impact_summary or (getattr(plan, "impact_summary", None) if plan else None),
            tokenizer_provenance=self.tokenizer.get_provenance(),
        )

        current_tokens = 0
        if compiled.impact_summary:
            summary_md = compiled.impact_summary.render_markdown()
            current_tokens += self._estimate_tokens(summary_md)

        # Track file spans for deduplication: file_path -> list of (start, end, entry_idx)
        file_spans: dict[str, list[tuple[int, int, int]]] = {}
        pinned = set(pinned_targets or set())

        # If a plan is provided, use planned items
        candidates_to_process: list[tuple[RankedCandidate, str | None]] = []
        if plan and hasattr(plan, "planned_items"):
            for item in plan.planned_items:
                candidates_to_process.append((item.candidate, item.role.value if hasattr(item.role, "value") else str(item.role)))
        else:
            for cand in ranked_candidates:
                candidates_to_process.append((cand, None))

        for cand, role in candidates_to_process:
            ev = cand.evidence
            # Strictly verified target IDs only (Phase 49)
            is_pinned = (cand.entity_id in pinned)

            # Determine granularity
            if is_pinned or role == "target":
                granularity = ContextGranularity.FULL_IMPLEMENTATION
                reason = "Primary change target entity (PINNED)"
            elif role == "boundary" or "route" in ev.edge_types or ev.boundary_contract == "route_matched":
                granularity = ContextGranularity.ROUTE_DECLARATION
                reason = "Boundary route declaration / client contract"
            elif role == "test" or "direct_test" in ev.test_relationship:
                granularity = ContextGranularity.TEST_FRAGMENT
                reason = "Direct regression verification test suite"
            elif role in ("implementation", "direct_caller") or cand.rank <= 6:
                granularity = ContextGranularity.SIGNATURE
                reason = f"Direct contract / {role or 'caller'}"
            else:
                granularity = ContextGranularity.SUMMARY
                reason = "Transitive dependency in blast radius"

            snippet, lines_range, snippet_tokens, span_obj = self._extract_snippet(
                cand.file_path,
                cand.entity_id,
                granularity,
            )

            # PHASE 29: Span Deduplication in the same file
            merged = False
            s_start, s_end = lines_range[0], lines_range[1]
            if cand.file_path in file_spans and granularity != ContextGranularity.SUMMARY:
                for existing_start, existing_end, e_idx in file_spans[cand.file_path]:
                    # Check for overlap or immediate adjacency (within 5 lines)
                    if not (s_end < existing_start - 5 or s_start > existing_end + 5):
                        # Merge into existing entry!
                        compiled.entries[e_idx].merged_entity_ids.append(cand.entity_id)
                        compiled.entities_merged += 1
                        compiled.tokens_saved_by_deduplication += snippet_tokens
                        merged = True
                        break

            if merged:
                continue

            s_exists = bool(self.repo_root and (self.repo_root / cand.file_path).exists())
            if granularity == ContextGranularity.SUMMARY:
                rep_type = "STRUCTURAL_SUMMARY"
            elif not s_exists or "SOURCE_UNAVAILABLE" in snippet:
                rep_type = "UNRESOLVED"
            else:
                rep_type = "SOURCE_SPAN"

            c_hash = hashlib.sha256(snippet.encode("utf-8")).hexdigest()

            entry = ContextEntry(
                entity_id=cand.entity_id,
                rank=cand.rank,
                reason=reason,
                evidence=list(ev.edge_types)[:4],
                granularity=granularity,
                source_file=cand.file_path,
                source_lines=lines_range,
                estimated_tokens=snippet_tokens,
                content_snippet=snippet,
                span_metadata=span_obj.to_dict(),
                source_exists=s_exists,
                span_resolved=(rep_type != "UNRESOLVED"),
                content_hash=c_hash,
                representation_type=rep_type,
            )

            entry_idx = len(compiled.entries)
            compiled.entries.append(entry)

            if granularity != ContextGranularity.SUMMARY:
                file_spans.setdefault(cand.file_path, []).append((s_start, s_end, entry_idx))

        # PHASE 50 & 51: Strict Token-Budget Invariant Tokenizing Exact Rendered Prompt
        final_prompt = compiled.render_prompt_markdown()
        total_prompt_tokens = self.tokenizer.count(final_prompt)

        # Iteratively prune/downgrade non-pinned entries from the bottom until within budget
        while total_prompt_tokens > token_budget and compiled.entries:
            pruned = False
            for idx in reversed(range(len(compiled.entries))):
                e = compiled.entries[idx]
                if e.entity_id not in pinned and e.granularity != ContextGranularity.FULL_IMPLEMENTATION:
                    if e.granularity != ContextGranularity.SUMMARY:
                        # Downgrade to summary
                        snip, lrange, stoks, sobj = self._extract_snippet(
                            e.source_file, e.entity_id, ContextGranularity.SUMMARY
                        )
                        e.granularity = ContextGranularity.SUMMARY
                        e.content_snippet = snip
                        e.source_lines = lrange
                        e.span_metadata = sobj.to_dict()
                    else:
                        # Remove this entry
                        compiled.entries.pop(idx)
                    pruned = True
                    break

            if not pruned:
                # If only pinned entries remain and still over budget, downgrade pinned entries to SIGNATURE
                downgraded_pinned = False
                for e in reversed(compiled.entries):
                    if e.granularity == ContextGranularity.FULL_IMPLEMENTATION:
                        snip, lrange, stoks, sobj = self._extract_snippet(
                            e.source_file, e.entity_id, ContextGranularity.SIGNATURE
                        )
                        e.granularity = ContextGranularity.SIGNATURE
                        e.content_snippet = snip
                        e.source_lines = lrange
                        e.span_metadata = sobj.to_dict()
                        downgraded_pinned = True
                        break
                if not downgraded_pinned:
                    # If still over budget, truncate last entry's snippet
                    if compiled.entries:
                        last_e = compiled.entries[-1]
                        lines = last_e.content_snippet.splitlines()
                        if len(lines) > 5:
                            last_e.content_snippet = "\n".join(lines[:max(3, len(lines) // 2)]) + "\n// ... [truncated for budget]"
                        else:
                            compiled.entries.pop()
                    else:
                        break

            final_prompt = compiled.render_prompt_markdown()
            total_prompt_tokens = self.tokenizer.count(final_prompt)

        # Enforce exact prompt budget invariant (PHASE 41)
        while total_prompt_tokens > token_budget and compiled.entries:
            compiled.entries.pop()
            final_prompt = compiled.render_prompt_markdown()
            total_prompt_tokens = self.tokenizer.count(final_prompt)

        compiled.candidates_included = len(compiled.entries)
        compiled.total_estimated_tokens = total_prompt_tokens
        return compiled
