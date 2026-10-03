"""
RCIR v8.2 — SourceSpanResolver & AST-Located Symbol Body Extractor (PHASES 26, 27).

Resolves code spans using layered priority:
1. Parser / Graph node metadata (start_line, end_line)
2. Edge call_line for caller snippet
3. Framework adapter span
4. Explicitly-labelled heuristic fallback (balanced-body brace matching)

Every span records its origin:
- span_source: "parser" | "edge" | "adapter" | "heuristic"
- span_confidence_class: "exact_ast" | "call_site" | "inferred" | "heuristic_fallback"
- fallback_used: bool
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class ResolvedSpan:
    """Accurate AST-bounded source line range and provenance metadata."""
    start_line: int
    end_line: int
    span_source: str                 # parser | edge | adapter | heuristic
    span_confidence_class: str       # exact_ast | call_site | inferred | heuristic_fallback
    fallback_used: bool
    symbol_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_line": self.start_line,
            "end_line": self.end_line,
            "span_source": self.span_source,
            "span_confidence_class": self.span_confidence_class,
            "fallback_used": self.fallback_used,
            "symbol_name": self.symbol_name,
        }


class SourceSpanResolver:
    """Extracts exact AST and call site boundaries for repository entities."""

    @classmethod
    def resolve_span(
        cls,
        lines: list[str],
        entity_id: str,
        node_metadata: dict[str, Any] | None = None,
        edge_metadata: dict[str, Any] | None = None,
    ) -> ResolvedSpan:
        """Resolve entity start and end line with full provenance tracking."""
        total_lines = len(lines)
        if total_lines == 0:
            return ResolvedSpan(1, 1, "heuristic", "heuristic_fallback", True, entity_id)

        # Priority 1: Parser / Graph Node Metadata
        if node_metadata:
            s = node_metadata.get("start_line") or node_metadata.get("line")
            e = node_metadata.get("end_line")
            if s is not None and isinstance(s, int) and 1 <= s <= total_lines:
                end_l = e if (e is not None and isinstance(e, int) and s <= e <= total_lines) else min(total_lines, s + 30)
                return ResolvedSpan(
                    start_line=s,
                    end_line=end_l,
                    span_source="parser",
                    span_confidence_class="exact_ast",
                    fallback_used=False,
                    symbol_name=entity_id,
                )

        # Priority 2: Edge call_line for caller snippet
        if edge_metadata:
            call_line = edge_metadata.get("call_line") or edge_metadata.get("line")
            if call_line is not None and isinstance(call_line, int) and 1 <= call_line <= total_lines:
                s = max(1, call_line - 3)
                e = min(total_lines, call_line + 5)
                return ResolvedSpan(
                    start_line=s,
                    end_line=e,
                    span_source="edge",
                    span_confidence_class="call_site",
                    fallback_used=False,
                    symbol_name=entity_id,
                )

        # Priority 3: Framework Adapter / Balanced Body Scan (Phase 27)
        clean_symbol = entity_id.split("::")[-1].split("\\")[-1]
        pattern = re.compile(
            rf"\b(function|class|interface|trait)\s+{re.escape(clean_symbol)}\b|\b{re.escape(clean_symbol)}\s*\(",
            re.IGNORECASE,
        )

        found_line = None
        for idx, line in enumerate(lines, 1):
            if pattern.search(line):
                found_line = idx
                break

        if found_line is not None:
            # PHASE 27: Balanced-brace body extraction
            s = found_line
            open_braces = 0
            body_started = False
            e = s

            for idx in range(s - 1, total_lines):
                line = lines[idx]
                open_braces += line.count("{") - line.count("}")
                if "{" in line:
                    body_started = True
                if body_started and open_braces <= 0:
                    e = idx + 1
                    break
            else:
                # Cap if unclosed
                e = min(total_lines, s + 45)

            # Include docblock if present right above
            doc_start = s
            for k in range(s - 2, max(-1, s - 10), -1):
                stripped = lines[k].strip()
                if stripped.startswith("/**") or stripped.startswith("*") or stripped.startswith("*/") or stripped.startswith("//"):
                    doc_start = k + 1
                else:
                    break

            return ResolvedSpan(
                start_line=doc_start,
                end_line=e,
                span_source="adapter",
                span_confidence_class="inferred",
                fallback_used=False,
                symbol_name=clean_symbol,
            )

        # Priority 4: Explicitly-labelled heuristic fallback
        return ResolvedSpan(
            start_line=1,
            end_line=min(total_lines, 25),
            span_source="heuristic",
            span_confidence_class="heuristic_fallback",
            fallback_used=True,
            symbol_name=entity_id,
        )
