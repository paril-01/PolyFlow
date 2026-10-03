"""RCIR v8 Retrieval Package."""

from rcir.retrieval.candidate_generator import CandidateGenerator, CandidateRecord
from rcir.retrieval.evidence_vector import EvidenceVector, EvidenceVectorBuilder
from rcir.retrieval.hybrid import hybrid_retrieve
from rcir.retrieval.ranker import DeterministicRanker, RankedCandidate, ScoreBreakdown
from rcir.retrieval.scorer import TFIDFScorer

__all__ = [
    "CandidateGenerator",
    "CandidateRecord",
    "EvidenceVector",
    "EvidenceVectorBuilder",
    "DeterministicRanker",
    "RankedCandidate",
    "ScoreBreakdown",
    "hybrid_retrieve",
    "TFIDFScorer",
]
