"""
Hash-chain versioning for RCIR nodes.

Pattern adapted from PolyFlow's Merkle-ledger (polyflow/runtime.py) but
re-implemented for a different domain: versioning AST-derived summaries
instead of .poly execution results.

Each node version is: hash(content_hash + previous_version_hash)
This creates a monotonic chain where:
- Any tampering with intermediate versions is detectable
- Snapshot isolation is natural (query at a specific version)
- Version comparison is O(1) (compare hashes)
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


GENESIS_HASH = "0" * 64  # The "zero block" — no previous version


@dataclass
class NodeVersion:
    """A single version in a node's hash chain."""
    version_hash: str
    previous_hash: str
    content_hash: str
    version_number: int
    node_path: str

    def to_dict(self) -> dict:
        return {
            "version_hash": self.version_hash,
            "previous_hash": self.previous_hash,
            "content_hash": self.content_hash,
            "version_number": self.version_number,
            "node_path": self.node_path,
        }


def _compute_content_hash(content: str | dict) -> str:
    """Hash the content of a node (summary, AST dump, etc.)."""
    if isinstance(content, dict):
        content = json.dumps(content, sort_keys=True, default=str)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _compute_version_hash(content_hash: str, previous_hash: str) -> str:
    """Compute the version hash: SHA-256(content_hash + previous_hash).

    This is the Merkle-chain link — each version depends on both its
    content and the previous version, making the chain tamper-evident.
    """
    combined = f"{content_hash}:{previous_hash}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


class VersionChain:
    """Manages the version chain for a single node.

    Each update appends a new version that links to the previous one.
    The chain is append-only — no version can be modified after creation.
    """

    def __init__(self, node_path: str):
        self.node_path = node_path
        self.versions: list[NodeVersion] = []
        self._current_hash: str = GENESIS_HASH

    @property
    def current_version(self) -> NodeVersion | None:
        """Get the latest version, or None if no versions exist."""
        return self.versions[-1] if self.versions else None

    @property
    def version_count(self) -> int:
        return len(self.versions)

    def append(self, content: str | dict) -> NodeVersion:
        """Append a new version to the chain.

        Args:
            content: The node content (summary, AST dump, etc.)

        Returns:
            The newly created NodeVersion.
        """
        content_hash = _compute_content_hash(content)
        version_hash = _compute_version_hash(content_hash, self._current_hash)

        version = NodeVersion(
            version_hash=version_hash,
            previous_hash=self._current_hash,
            content_hash=content_hash,
            version_number=len(self.versions) + 1,
            node_path=self.node_path,
        )

        self.versions.append(version)
        self._current_hash = version_hash
        return version

    def verify_chain(self) -> bool:
        """Verify the integrity of the entire chain.

        Returns True if every version's hash is consistent with its
        content hash and previous version's hash.
        """
        expected_prev = GENESIS_HASH
        for version in self.versions:
            if version.previous_hash != expected_prev:
                return False
            expected_hash = _compute_version_hash(
                version.content_hash, version.previous_hash
            )
            if version.version_hash != expected_hash:
                return False
            expected_prev = version.version_hash
        return True

    def to_dict(self) -> dict:
        return {
            "node_path": self.node_path,
            "version_count": self.version_count,
            "current_hash": self._current_hash,
            "versions": [v.to_dict() for v in self.versions],
        }


class VersionStore:
    """Manages version chains for all nodes in the graph.

    Provides snapshot isolation: queries can specify a version number
    and get consistent state across all nodes at that point.
    """

    def __init__(self):
        self._chains: dict[str, VersionChain] = {}

    def get_or_create_chain(self, node_path: str) -> VersionChain:
        """Get an existing chain or create a new one for a node."""
        if node_path not in self._chains:
            self._chains[node_path] = VersionChain(node_path)
        return self._chains[node_path]

    def update_node(self, node_path: str, content: str | dict) -> NodeVersion:
        """Update a node with new content, appending to its version chain."""
        chain = self.get_or_create_chain(node_path)
        return chain.append(content)

    def get_current_version(self, node_path: str) -> NodeVersion | None:
        """Get the current version of a node."""
        chain = self._chains.get(node_path)
        if chain:
            return chain.current_version
        return None

    def verify_all(self) -> dict[str, bool]:
        """Verify all chains. Returns dict of node_path → is_valid."""
        return {
            path: chain.verify_chain()
            for path, chain in self._chains.items()
        }

    def to_dict(self) -> dict:
        return {
            "total_nodes": len(self._chains),
            "chains": {
                path: chain.to_dict()
                for path, chain in self._chains.items()
            },
        }
