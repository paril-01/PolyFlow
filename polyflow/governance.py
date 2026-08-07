"""
PolyFlow Governance, Rationale & Cryptographic Merkle Audit Ledger.

Manages @contract, @rationale, @decision, @audit, and generates SHA-256 Merkle tree verification.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

@dataclass
class LedgerNode:
    index: int
    data_hash: str
    prev_hash: str
    merkle_root: str
    timestamp: float

class MerkleLedger:
    def __init__(self):
        self.chain: List[LedgerNode] = []
        self.entries: List[Dict[str, Any]] = []

    def record_entry(self, entry_type: str, data: Dict[str, Any]) -> LedgerNode:
        timestamp = time.time()
        entry_payload = {
            "index": len(self.chain),
            "type": entry_type,
            "data": data,
            "timestamp": timestamp
        }
        self.entries.append(entry_payload)

        data_str = json.dumps(entry_payload, sort_keys=True, default=str)
        data_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest()

        prev_hash = self.chain[-1].merkle_root if self.chain else "0" * 64

        # Compute Merkle Root combining data_hash and prev_hash
        combined = f"{prev_hash}:{data_hash}"
        merkle_root = hashlib.sha256(combined.encode("utf-8")).hexdigest()

        node = LedgerNode(
            index=len(self.chain),
            data_hash=data_hash,
            prev_hash=prev_hash,
            merkle_root=merkle_root,
            timestamp=timestamp
        )
        self.chain.append(node)
        return node

    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        if not self.chain:
            return True, None

        for i in range(len(self.chain)):
            current = self.chain[i]
            entry_payload = self.entries[i]

            # Re-hash data
            data_str = json.dumps(entry_payload, sort_keys=True, default=str)
            recalculated_data_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest()

            if recalculated_data_hash != current.data_hash:
                return False, f"Data tampering detected at ledger index {i}."

            expected_prev = self.chain[i - 1].merkle_root if i > 0 else "0" * 64
            if current.prev_hash != expected_prev:
                return False, f"Previous hash mismatch at ledger index {i}."

            combined = f"{expected_prev}:{current.data_hash}"
            recalculated_root = hashlib.sha256(combined.encode("utf-8")).hexdigest()

            if recalculated_root != current.merkle_root:
                return False, f"Merkle root mismatch at ledger index {i}."

        return True, None

class PolyGovernanceEngine:
    def __init__(self):
        self.ledger = MerkleLedger()

    def audit_execution(self, filepath: str, action: str, details: Dict[str, Any]) -> LedgerNode:
        payload = {
            "filepath": filepath,
            "action": action,
            "details": details
        }
        return self.ledger.record_entry("execution_audit", payload)

    def verify_contract(self, contract: Dict[str, Any]) -> Tuple[bool, List[str]]:
        warnings = []
        if not contract.get("feature_id"):
            warnings.append("Missing 'feature_id' in @contract directive.")
        if not contract.get("owner"):
            warnings.append("Missing 'owner' in @contract directive.")
        if contract.get("classification") in ("sensitive", "restricted"):
            approvers = contract.get("approvers", [])
            if len(approvers) < 2:
                warnings.append("Sensitive feature classification requires at least 2 approvers.")
        return len(warnings) == 0, warnings
