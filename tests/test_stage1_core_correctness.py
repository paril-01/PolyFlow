"""
Unit and regression tests for RCIR v8.5 Stage 1 Core Analysis Correctness.

Verifies:
- F07: PHP type flow condition polarity, closure lexical isolation, and guard clauses.
- F08: Legacy endpoint normalization idempotence and prevention of double-scheme URIs.
- F09: Context compiler metadata synchronization (content_hash, tokens, representation_type).
"""

import hashlib
import tempfile
from pathlib import Path
import pytest

from rcir.types.php_type_flow import (
    PHPTypeFlowAnalyzer,
    TypeResolutionConfidence,
)
from rcir.entities.legacy_normalizer import LegacyEndpointNormalizer
from rcir.entities.canonical import CanonicalEntityRegistry
from rcir.graph.canonical_graph import CanonicalGraph, CanonicalEdge
from rcir.context.compiler import (
    ContextCompiler,
    ContextGranularity,
)


def test_f07_negated_instanceof_does_not_narrow_in_if_or_post():
    """F07: if (!($x instanceof Foo)) must not narrow $x to Foo inside if body or after if."""
    php_code = """<?php
namespace Test;

class Demo {
    public function test($x) {
        if (!($x instanceof Foo)) {
            $x->run();
        }
        $x->run();
    }
}
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        test_file = tmp_p / "Demo.php"
        test_file.write_text(php_code, encoding="utf-8")

        analyzer = PHPTypeFlowAnalyzer(repo_root=tmp_p)
        call_sites = analyzer.analyze_file("Demo.php")

        assert len(call_sites) == 2
        # Inside if: line 7
        call_inside = call_sites[0]
        assert call_inside.line_number == 7
        assert call_inside.inferred_type != "Test\\Foo" or call_inside.confidence != TypeResolutionConfidence.PROVEN_EXACT

        # Outside if: line 9
        call_outside = call_sites[1]
        assert call_outside.line_number == 9
        assert call_outside.inferred_type != "Test\\Foo" or call_outside.confidence != TypeResolutionConfidence.PROVEN_EXACT


def test_f07_closure_parameters_do_not_leak_to_outer_scope():
    """F07: Closure parameters must not overwrite outer variable types in enclosing scope."""
    php_code = """<?php
namespace Test;

class Demo {
    public function test(Bar $x) {
        $callback = function(Foo $x) {
            $x->run();
        };
        $x->run();
    }
}
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        test_file = tmp_p / "Demo.php"
        test_file.write_text(php_code, encoding="utf-8")

        analyzer = PHPTypeFlowAnalyzer(repo_root=tmp_p)
        call_sites = analyzer.analyze_file("Demo.php")

        assert len(call_sites) == 2
        # Inside closure: $x is Foo
        call_closure = call_sites[0]
        assert call_closure.inferred_type == "Test\\Foo"
        assert call_closure.confidence == TypeResolutionConfidence.PROVEN_EXACT

        # After closure in outer scope: $x must still be Bar, NOT Foo!
        call_outer = call_sites[1]
        assert call_outer.inferred_type == "Test\\Bar"
        assert call_outer.confidence == TypeResolutionConfidence.PROVEN_EXACT


def test_f07_guard_clause_narrows_post_return():
    """F07: if (!($x instanceof Foo)) { return; } narrows $x to Foo after the guard clause."""
    php_code = """<?php
namespace Test;

class Demo {
    public function test($x) {
        if (!($x instanceof Foo)) {
            return;
        }
        $x->run();
    }
}
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        test_file = tmp_p / "Demo.php"
        test_file.write_text(php_code, encoding="utf-8")

        analyzer = PHPTypeFlowAnalyzer(repo_root=tmp_p)
        call_sites = analyzer.analyze_file("Demo.php")

        assert len(call_sites) == 1
        call_post = call_sites[0]
        assert call_post.inferred_type == "Test\\Foo"
        assert call_post.confidence == TypeResolutionConfidence.PROVEN_EXACT


def test_f08_endpoint_normalizer_idempotence_and_no_double_scheme():
    """F08: Normalizer must never output nested schemes like php://php://."""
    normalizer = LegacyEndpointNormalizer()

    # Repairing repo-local external endpoints
    r1 = normalizer.normalize_endpoint("external://OCP\\IConfig")
    assert r1 == "php://OCP\\IConfig"
    assert "php://php://" not in r1

    r2 = normalizer.normalize_endpoint("external://lib/public/IConfig.php")
    assert r2 == "php://lib/public/IConfig.php"
    assert "php://php://" not in r2

    # Idempotence: calling with an already repaired or double-scheme URI
    r3 = normalizer.normalize_endpoint("php://php://OCP\\IConfig")
    assert r3 == "php://OCP\\IConfig"

    r4 = normalizer.normalize_endpoint("php://OCP\\IConfig")
    assert r4 == "php://OCP\\IConfig"


from rcir.graph.canonical_graph import CanonicalGraph, CanonicalEdge, CanonicalEdgeType


def test_f08_canonical_graph_add_edge_clean_endpoints():
    """F08: Adding edges with legacy endpoints produces clean canonical IDs in graph."""
    graph = CanonicalGraph()
    edge = CanonicalEdge(
        source_id="external://OCP\\IConfig",
        target_id="external://lib/public/IConfig.php",
        edge_type=CanonicalEdgeType.IMPLEMENTS,
    )
    graph.add_edge(edge)

    assert edge.source_id == "php://OCP\\IConfig"
    assert edge.target_id == "php://lib/public/IConfig.php"
    assert "php://php://" not in edge.source_id
    assert "php://php://" not in edge.target_id
    assert "php://OCP\\IConfig" in graph.outgoing_edges
    assert "php://lib/public/IConfig.php" in graph.incoming_edges


from rcir.retrieval.ranker import RankedCandidate, ScoreBreakdown
from rcir.retrieval.evidence_vector import EvidenceVector


def test_f09_context_compiler_metadata_synchronization():
    """F09: Truncated or downgraded context entries must have matching content_hash and representation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_p = Path(tmpdir)
        src_file = tmp_p / "Demo.php"
        src_file.write_text("<?php\nclass Demo {\n" + "    public function f() { echo 'line'; }\n" * 50 + "}\n", encoding="utf-8")

        compiler = ContextCompiler(repo_root=tmp_p)

        candidates = [
            RankedCandidate(
                rank=1,
                entity_id="php://Test\\Demo",
                file_path="Demo.php",
                total_score=1.0,
                evidence=EvidenceVector(entity_id="php://Test\\Demo", file_path="Demo.php", edge_types=["calls"]),
                breakdown=ScoreBreakdown(),
            ),
            RankedCandidate(
                rank=2,
                entity_id="php://Test\\Demo::f",
                file_path="Demo.php",
                total_score=0.9,
                evidence=EvidenceVector(entity_id="php://Test\\Demo::f", file_path="Demo.php", edge_types=["calls"]),
                breakdown=ScoreBreakdown(),
            ),
        ]

        compiled = compiler.compile(
            ranked_candidates=candidates,
            token_budget=150,  # Low budget forces downgrade to SUMMARY and pruning/truncation
            pinned_targets={"php://Test\\Demo"},
        )

        assert len(compiled.entries) > 0
        for entry in compiled.entries:
            # 1. content_hash must exactly equal SHA-256 of delivered content_snippet
            expected_hash = hashlib.sha256(entry.content_snippet.encode("utf-8")).hexdigest()
            assert entry.content_hash == expected_hash, f"Hash mismatch for {entry.entity_id}"

            # 2. If granularity is SUMMARY, representation_type must be STRUCTURAL_SUMMARY, never SOURCE_SPAN
            if entry.granularity == ContextGranularity.SUMMARY:
                assert entry.representation_type == "STRUCTURAL_SUMMARY"
            elif entry.source_exists:
                assert entry.representation_type == "SOURCE_SPAN"

            # 3. estimated_tokens must match tokenizer count
            assert entry.estimated_tokens == compiler.tokenizer.count(entry.content_snippet)
