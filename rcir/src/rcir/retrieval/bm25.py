"""
RCIR v8.1 — Deterministic Code-Aware BM25 Scorer (PHASE 20).

Implements deterministic Okapi BM25 ranking with code-aware token weighting:
- Exact symbol and method name tokens (3x weight)
- Module and path tokens (1.5x weight)
- Docstrings, annotations, and argument tokens (1.0x weight)
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Any


_TOKEN_SPLIT = re.compile(r'[^a-zA-Z0-9]+')
_CAMEL_SPLIT = re.compile(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])')


def tokenize_code(text: str) -> list[str]:
    """Tokenize code text into lowercase terms with snake_case and CamelCase splitting."""
    parts = _TOKEN_SPLIT.split(text)
    tokens = []
    for part in parts:
        if not part:
            continue
        sub_parts = _CAMEL_SPLIT.split(part)
        for sp in sub_parts:
            if sp:
                tokens.append(sp.lower())
    return tokens


class BM25Scorer:
    """Okapi BM25 scorer with code-specific token weighting."""

    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_lengths: dict[str, int] = {}
        self.avg_doc_length: float = 0.0
        self.doc_freqs: dict[str, int] = defaultdict(int)
        self.doc_token_counts: dict[str, dict[str, float]] = {}
        self.num_docs: int = 0
        self.indexed: bool = False

    def build_index(self, nodes: list[dict[str, Any]]) -> None:
        """Build BM25 index from repository nodes."""
        self.doc_lengths.clear()
        self.doc_freqs.clear()
        self.doc_token_counts.clear()

        total_tokens = 0

        for node in nodes:
            path = node.get("path", "")
            if not path:
                continue

            token_weights: dict[str, float] = defaultdict(float)

            # 1. Exact symbol name (3x weight)
            name = node.get("name", "")
            if name:
                for t in tokenize_code(name):
                    token_weights[t] += 3.0

            # 2. Path tokens (1.5x weight)
            for t in tokenize_code(path):
                token_weights[t] += 1.5

            # 3. Arguments & bases (1.0x weight)
            for arg in node.get("args", []):
                for t in tokenize_code(arg.get("name", "") + " " + arg.get("annotation", "")):
                    token_weights[t] += 1.0

            for base in node.get("bases", []):
                for t in tokenize_code(base):
                    token_weights[t] += 1.0

            doc_len = sum(token_weights.values())
            self.doc_lengths[path] = max(1, int(doc_len))
            total_tokens += self.doc_lengths[path]
            self.doc_token_counts[path] = dict(token_weights)

            for token in token_weights:
                self.doc_freqs[token] += 1

        self.num_docs = len(self.doc_lengths)
        self.avg_doc_length = (total_tokens / self.num_docs) if self.num_docs > 0 else 1.0
        self.indexed = True

    def score_query(self, query: str) -> dict[str, float]:
        """Compute BM25 scores for all indexed documents matching query terms."""
        if not self.indexed or self.num_docs == 0:
            return {}

        query_terms = tokenize_code(query)
        if not query_terms:
            return {}

        scores: dict[str, float] = defaultdict(float)

        for term in query_terms:
            df = self.doc_freqs.get(term, 0)
            if df == 0:
                continue

            # Standard BM25 IDF with smoothing
            idf = math.log(1.0 + (self.num_docs - df + 0.5) / (df + 0.5))

            for doc_id, token_counts in self.doc_token_counts.items():
                if term in token_counts:
                    tf = token_counts[term]
                    doc_len = self.doc_lengths[doc_id]
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_length))
                    score_term = idf * ((tf * (self.k1 + 1.0)) / denom)
                    scores[doc_id] += score_term

        # Normalize scores to [0.0, 1.0] range
        if scores:
            max_s = max(scores.values())
            if max_s > 0:
                for k in scores:
                    scores[k] = scores[k] / max_s

        return dict(scores)

    def top_k(self, query: str, k: int = 40) -> list[tuple[str, float]]:
        """Return top-K scored documents for the query."""
        scores = self.score_query(query)
        sorted_docs = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return sorted_docs[:k]
