"""
RCIR v8.2 — Configuration Fingerprinting Engine (PHASE 61).

Computes deterministic SHA-256 hashes of benchmark configurations, traversal policies,
ranker profiles, and contracts to prevent unrecorded configuration drift.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_config_hash(obj: Any) -> str:
    """Compute 16-character hexadecimal SHA-256 fingerprint for a configuration object or dictionary."""
    if hasattr(obj, "to_dict"):
        data = obj.to_dict()
    elif hasattr(obj, "__dict__"):
        data = obj.__dict__
    elif isinstance(obj, dict):
        data = obj
    else:
        data = str(obj)

    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def get_pipeline_fingerprint(
    candidate_generator_config: Any,
    traversal_policy: Any,
    ranker_config: Any,
    context_compiler: Any,
    benchmark_contract: Any,
) -> dict[str, str]:
    """Generate complete fingerprint dictionary for benchmark artifacts."""
    return {
        "candidate_generator_config_hash": compute_config_hash(candidate_generator_config),
        "traversal_policy_hash": compute_config_hash(traversal_policy),
        "ranker_config_hash": compute_config_hash(ranker_config),
        "context_compiler_config_hash": compute_config_hash(context_compiler),
        "benchmark_contract_hash": compute_config_hash(benchmark_contract),
    }
