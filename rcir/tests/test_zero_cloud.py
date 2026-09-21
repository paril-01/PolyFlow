"""
Zero-cloud verification test (v7 §3).

Verifies the core claim: RCIR's core analysis path (graph extraction,
hierarchy building, invalidation, retrieval) runs correctly with ALL
outbound network interfaces blocked.

This is a binary test. Pass = zero-cloud claim holds. Fail = it doesn't.

Implementation: monkey-patches socket.socket to raise on any connection
attempt, then runs the full core analysis path inside the patched context.
If any code in the analysis path tries to make a network call, this test fails.
"""

import socket
import pytest
from pathlib import Path
from unittest.mock import patch

from rcir.graph.extractor import extract_graph
from rcir.hierarchy.builder import build_hierarchy
from rcir.retrieval.hybrid import hybrid_retrieve
from rcir.state.diff import diff_file


class NetworkBlockedError(Exception):
    """Raised when code attempts a network connection during zero-cloud test."""
    pass


class _BlockedSocket:
    """A socket replacement that raises on any connection attempt."""

    def __init__(self, *args, **kwargs):
        raise NetworkBlockedError(
            "ZERO-CLOUD VIOLATION: code attempted to create a network socket "
            "during the core analysis path. This violates RCIR's zero-cloud "
            "claim (v7 §3). The core analysis path must run correctly with "
            "all outbound network interfaces blocked."
        )


class TestZeroCloud:
    """Verify that RCIR's core analysis path makes zero network calls.

    Per v7 §3:
    - Graph extraction, hierarchy, invalidation, retrieval, routing signal
      computation MUST run correctly with all outbound network interfaces blocked.
    - This is binary, tested on every commit, and is the actual product claim.
    """

    def _build_test_repo(self, tmp_path: Path) -> Path:
        """Build a small on-disk Python project to analyze."""
        pkg = tmp_path / "myapp"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "models.py").write_text(
            "class User:\n"
            "    def __init__(self, name: str, email: str):\n"
            "        self.name = name\n"
            "        self.email = email\n"
            "\n"
            "    def validate(self) -> bool:\n"
            "        return '@' in self.email\n"
        )
        (pkg / "service.py").write_text(
            "from myapp.models import User\n"
            "\n"
            "def create_user(name: str, email: str) -> User:\n"
            "    user = User(name, email)\n"
            "    if not user.validate():\n"
            "        raise ValueError('Invalid email')\n"
            "    return user\n"
            "\n"
            "def get_user_by_email(email: str) -> User:\n"
            "    return User('unknown', email)\n"
        )
        (pkg / "api.py").write_text(
            "from myapp.service import create_user, get_user_by_email\n"
            "\n"
            "def handle_create_user(data: dict) -> dict:\n"
            "    user = create_user(data['name'], data['email'])\n"
            "    return {'status': 'created', 'name': user.name}\n"
            "\n"
            "def handle_get_user(email: str) -> dict:\n"
            "    user = get_user_by_email(email)\n"
            "    return {'name': user.name, 'email': user.email}\n"
        )
        return tmp_path

    def test_full_analysis_path_with_network_blocked(self, tmp_path):
        """Run the complete core analysis path with network blocked.

        This is the actual zero-cloud verification. If this test passes,
        the core analysis path makes zero network calls.
        """
        repo = self._build_test_repo(tmp_path)

        # Block ALL socket creation — if anything tries to connect, we fail
        with patch("socket.socket", _BlockedSocket):
            # Phase 1: Graph extraction
            graph = extract_graph(repo)
            assert graph["metadata"]["total_nodes"] > 0, \
                "Graph extraction should find nodes even with network blocked"

            # Phase 2: Hierarchy building
            hierarchy = build_hierarchy(graph)
            assert len(hierarchy.get("nodes", [])) > 0, \
                "Hierarchy building should work with network blocked"

            # Phase 3: Retrieval
            contract = hybrid_retrieve(
                hierarchy, "create user validate email", token_budget=2000
            )
            assert len(contract.nodes) > 0, \
                "Retrieval should return nodes with network blocked"

            # Phase 4: Invalidation (state-split diff)
            before = "def foo(x: int) -> str:\n    return str(x)\n"
            after = "def foo(x: int, y: int = 0) -> str:\n    return str(x + y)\n"
            diffs = diff_file(before, after, "test.py")
            assert len(diffs) > 0, \
                "Diff computation should work with network blocked"

    def test_network_block_actually_blocks(self, tmp_path):
        """Verify that our blocking mechanism actually works.

        This is a meta-test: if the socket patch doesn't actually prevent
        connections, the zero-cloud test is meaningless. So we verify that
        attempting a real connection inside the patch raises our error.
        """
        with patch("socket.socket", _BlockedSocket):
            with pytest.raises(NetworkBlockedError):
                # This should fail — proves the block is real
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def test_proto_parser_with_network_blocked(self, tmp_path):
        """Verify proto parsing is also zero-cloud."""
        proto_dir = tmp_path / "protos"
        proto_dir.mkdir()
        (proto_dir / "service.proto").write_text('''
service TestService {
    rpc GetItem(GetItemRequest) returns (Item) {}
}
message GetItemRequest { string id = 1; }
message Item { string name = 1; }
''')

        from rcir.graph.proto_parser import parse_proto_files

        with patch("socket.socket", _BlockedSocket):
            result = parse_proto_files(tmp_path)
            assert result.files_parsed == 1
            assert len(result.services) == 1
