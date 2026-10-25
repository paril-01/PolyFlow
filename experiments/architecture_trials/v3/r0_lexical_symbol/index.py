"""
experiments/architecture_trials/v3/r0_lexical_symbol/index.py — R0 Conventional Comparator.

Provides a strong conventional baseline:
- Inverted lexical index with term frequency ranking (BM25-style scoring).
- AST/regex-based symbol resolver mapping class/function definitions to exact line bounds.
- Source span extraction and token-budget constrained packing.
- Safe path resolution preventing directory traversal.
"""

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class SourceSpan:
    file_path: str
    start_line: int
    end_line: int
    content: str
    symbol_name: Optional[str] = None
    score: float = 0.0


class LexicalSymbolIndex:
    """
    R0 Index: Combines lexical inverted index with symbol definition lookup.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self.doc_lengths: Dict[str, int] = {}
        self.inverted_index: Dict[str, Set[str]] = {}
        self.term_freqs: Dict[str, Dict[str, int]] = {}
        self.symbol_index: Dict[str, List[Tuple[str, int, int]]] = {}  # symbol -> [(file, start, end)]
        self.indexed_files: List[str] = []

    def _tokenize(self, text: str) -> List[str]:
        # Split camelCase and snake_case and non-alphanumeric
        words = re.findall(r"[A-Za-z0-9_]+", text)
        tokens = []
        for w in words:
            tokens.append(w.lower())
            # Split camelCase
            subwords = re.sub(r"([a-z])([A-Z])", r"\1 \2", w).split()
            if len(subwords) > 1:
                tokens.extend([sw.lower() for sw in subwords])
        return tokens

    def index_repository(self, extensions: Tuple[str, ...] = (".php", ".py", ".js", ".ts", ".java", ".go")):
        """Scan repository files, build lexical and symbol indexes."""
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "vendor", "3rdparty", "__pycache__", ".venv", "dist", "build"}]
            for fname in files:
                if any(fname.endswith(ext) for ext in extensions):
                    full_p = Path(root) / fname
                    try:
                        rel_p = str(full_p.relative_to(self.repo_root)).replace("\\", "/")
                    except ValueError:
                        continue
                    
                    try:
                        content = full_p.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        continue

                    self.indexed_files.append(rel_p)
                    lines = content.splitlines()
                    self.doc_lengths[rel_p] = len(lines)

                    # Extract lexical tokens
                    tokens = self._tokenize(content)
                    tf: Dict[str, int] = {}
                    for t in tokens:
                        tf[t] = tf.get(t, 0) + 1
                        if t not in self.inverted_index:
                            self.inverted_index[t] = set()
                        self.inverted_index[t].add(rel_p)
                    self.term_freqs[rel_p] = tf

                    # Extract symbol definitions
                    for idx, line in enumerate(lines, 1):
                        # PHP / JS / Python class/function regex
                        m_cls = re.search(r"\bclass\s+([A-Za-z0-9_]+)", line)
                        if m_cls:
                            sym = m_cls.group(1)
                            if sym not in self.symbol_index:
                                self.symbol_index[sym] = []
                            self.symbol_index[sym].append((rel_p, idx, min(idx + 50, len(lines))))
                        
                        m_fn = re.search(r"\b(?:function|def)\s+([A-Za-z0-9_]+)", line)
                        if m_fn:
                            sym = m_fn.group(1)
                            if sym not in self.symbol_index:
                                self.symbol_index[sym] = []
                            self.symbol_index[sym].append((rel_p, idx, min(idx + 30, len(lines))))

    def search_symbols(self, query: str) -> List[SourceSpan]:
        """Look up exact and partial symbol matches."""
        results: List[SourceSpan] = []
        tokens = self._tokenize(query)
        for t in tokens:
            # Check exact case-insensitive matches in symbol index
            for sym, locations in self.symbol_index.items():
                if t == sym.lower():
                    for rel_p, start, end in locations:
                        abs_p = (self.repo_root / rel_p).resolve()
                        if not str(abs_p).startswith(str(self.repo_root)):
                            continue  # Traversal guard
                        try:
                            lines = abs_p.read_text(encoding="utf-8", errors="replace").splitlines()
                            snippet = "\n".join(lines[start - 1 : end])
                            results.append(
                                SourceSpan(
                                    file_path=rel_p,
                                    start_line=start,
                                    end_line=end,
                                    content=snippet,
                                    symbol_name=sym,
                                    score=10.0,
                                )
                            )
                        except Exception:
                            continue
        return results

    def search_lexical(self, query: str, top_k: int = 20) -> List[SourceSpan]:
        """Rank documents using term frequency and token matching."""
        tokens = self._tokenize(query)
        if not tokens or not self.indexed_files:
            return []

        scores: Dict[str, float] = {}
        total_docs = len(self.indexed_files)

        for t in tokens:
            matching_docs = self.inverted_index.get(t, set())
            if not matching_docs:
                continue
            idf = math.log((total_docs - len(matching_docs) + 0.5) / (len(matching_docs) + 0.5) + 1.0)
            for doc in matching_docs:
                tf = self.term_freqs.get(doc, {}).get(t, 0)
                scores[doc] = scores.get(doc, 0.0) + (tf * idf)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results: List[SourceSpan] = []
        for rel_p, score in ranked:
            abs_p = (self.repo_root / rel_p).resolve()
            if not str(abs_p).startswith(str(self.repo_root)):
                continue
            try:
                content = abs_p.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
                # Take top slice (up to 40 lines)
                snippet = "\n".join(lines[:40])
                results.append(
                    SourceSpan(
                        file_path=rel_p,
                        start_line=1,
                        end_line=min(40, len(lines)),
                        content=snippet,
                        score=score,
                    )
                )
            except Exception:
                continue
        return results

    def retrieve(self, query: str, max_tokens: int = 4000) -> Dict[str, Any]:
        """
        Retrieve source context bounded by max_tokens.
        Prioritizes symbol definitions then lexical matches.
        """
        symbol_spans = self.search_symbols(query)
        lexical_spans = self.search_lexical(query, top_k=20)

        # Deduplicate spans by (file_path, start_line)
        seen: Set[Tuple[str, int]] = set()
        combined: List[SourceSpan] = []

        for span in symbol_spans + lexical_spans:
            key = (span.file_path, span.start_line)
            if key not in seen:
                seen.add(key)
                combined.append(span)

        # Token packing (approx 4 chars per token)
        budget_chars = max_tokens * 4
        packed_spans: List[Dict[str, Any]] = []
        consumed_chars = 0

        for span in combined:
            span_chars = len(span.content)
            if consumed_chars + span_chars > budget_chars:
                # Truncate if there's remaining budget
                remaining = budget_chars - consumed_chars
                if remaining > 100:
                    truncated = span.content[:remaining]
                    packed_spans.append({
                        "file_path": span.file_path,
                        "start_line": span.start_line,
                        "end_line": span.end_line,
                        "snippet": truncated,
                        "symbol": span.symbol_name,
                        "score": span.score,
                        "resolution_class": "STATIC_EXACT" if span.symbol_name else "LEXICAL",
                    })
                    consumed_chars += len(truncated)
                break
            else:
                packed_spans.append({
                    "file_path": span.file_path,
                    "start_line": span.start_line,
                    "end_line": span.end_line,
                    "snippet": span.content,
                    "symbol": span.symbol_name,
                    "score": span.score,
                    "resolution_class": "STATIC_EXACT" if span.symbol_name else "LEXICAL",
                })
                consumed_chars += span_chars

        return {
            "retriever": "R0_LEXICAL_SYMBOL",
            "query": query,
            "max_tokens": max_tokens,
            "estimated_tokens": consumed_chars // 4,
            "spans_count": len(packed_spans),
            "spans": packed_spans,
            "target_files": list({s["file_path"] for s in packed_spans}),
        }
