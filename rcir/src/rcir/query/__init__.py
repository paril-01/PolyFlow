"""RCIR v8 Query & Change Specification Package."""

from rcir.query.change_spec import ChangeOperation, ChangeSpecification, RequestedScope
from rcir.query.intent_parser import DeterministicIntentParser

__all__ = [
    "ChangeOperation",
    "ChangeSpecification",
    "RequestedScope",
    "DeterministicIntentParser",
]
