"""
TF-IDF scoring for query-to-node relevance computation.

Simple, stdlib-only TF-IDF implementation — no external dependencies.
This is deliberately simple per the build plan's scoping: start with
TF-IDF, only upgrade to embeddings if retrieval quality requires it.

The scorer operates on node "documents" which are constructed from:
- Node path (tokenized)
- Function/class name
- Argument names and types
- Decorators
- Parent module name
"""

import math
import re
from collections import Counter, defaultdict
from typing import Any


# Tokenization
_TOKEN_SPLIT = re.compile(r'[^a-zA-Z0-9]+')
_CAMEL_SPLIT = re.compile(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])')


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase terms.

    Handles:
    - snake_case splitting (via delimiter split)
    - CamelCase splitting
    - Path separators
    """
    # First split on non-alphanumeric
    parts = _TOKEN_SPLIT.split(text)

    tokens = []
    for part in parts:
        if not part:
            continue
        # Split camelCase
        sub_parts = _CAMEL_SPLIT.split(part)
        for sp in sub_parts:
            if sp:
                tokens.append(sp.lower())

    return tokens


def _build_node_document(node: dict) -> str:
    """Build a searchable text document from a node's metadata."""
    parts = []

    # Path (tokenized)
    path = node.get("path", "")
    parts.append(path)

    # Kind
    kind = node.get("kind", "")
    parts.append(kind)

    # Arguments
    args = node.get("args", [])
    for arg in args:
        parts.append(arg.get("name", ""))
        annotation = arg.get("annotation", "")
        if annotation:
            parts.append(annotation)

    # Decorators
    decorators = node.get("decorators", [])
    for dec in decorators:
        parts.append(dec)

    # Return annotation
    ret = node.get("return_annotation", "")
    if ret:
        parts.append(ret)

    # Bases (for classes)
    bases = node.get("bases", [])
    for base in bases:
        parts.append(base)

    # Children (for file/module nodes)
    children = node.get("children", [])
    for child in children:
        parts.append(child)

    return " ".join(parts)


class TFIDFScorer:
    """TF-IDF scorer for ranking nodes against a query.

    Build the index once from all nodes, then score queries against it.
    """

    def __init__(self):
        self._documents: dict[str, list[str]] = {}  # node_path → tokens
        self._df: Counter = Counter()  # document frequency per term
        self._total_docs: int = 0

    def build_index(self, nodes: list[dict]) -> None:
        """Build the TF-IDF index from a list of hierarchy nodes."""
        self._documents.clear()
        self._df.clear()

        for node in nodes:
            path = node.get("path", "")
            if not path:
                continue

            doc_text = _build_node_document(node)
            tokens = tokenize(doc_text)
            self._documents[path] = tokens

            # Document frequency: count each term once per document
            unique_terms = set(tokens)
            for term in unique_terms:
                self._df[term] += 1

        self._total_docs = len(self._documents)

    def score(self, query: str) -> dict[str, float]:
        """Score all indexed nodes against a query.

        Returns dict of node_path → relevance score (higher = more relevant).
        """
        if self._total_docs == 0:
            return {}

        query_tokens = tokenize(query)
        if not query_tokens:
            return {}

        # Compute IDF for query terms
        idf: dict[str, float] = {}
        for term in set(query_tokens):
            df = self._df.get(term, 0)
            if df > 0:
                idf[term] = math.log(self._total_docs / df)
            else:
                idf[term] = 0.0

        # Score each document
        scores: dict[str, float] = {}
        for path, doc_tokens in self._documents.items():
            if not doc_tokens:
                scores[path] = 0.0
                continue

            # TF for this document
            tf = Counter(doc_tokens)
            doc_len = len(doc_tokens)

            score = 0.0
            for q_term in query_tokens:
                term_tf = tf.get(q_term, 0) / doc_len  # normalized TF
                term_idf = idf.get(q_term, 0.0)
                score += term_tf * term_idf

            scores[path] = round(score, 6)

        return scores

    def top_k(self, query: str, k: int = 20) -> list[tuple[str, float]]:
        """Return the top-k scoring nodes for a query.

        Returns list of (node_path, score) tuples, sorted by score descending.
        """
        scores = self.score(query)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:k]
