"""
RCIR v8.5 — Git Object and Provenance Reader.

Provides safe, side-effect-free, commit-bound access to Git object blobs:
- read_repo_file_at_commit(repo_root, commit_sha, rel_path) -> bytes
- verify_commit_exists(repo_root, commit_sha) -> bool
- validate_safe_relative_path(rel_path) -> str
- verify_content_hash(blob_bytes, recorded_hash) -> Tuple[bool, str, str, str]
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Tuple

HEX_SHA_REGEX = re.compile(r"^[0-9a-fA-F]{40}$")


class ProvenanceReadError(RuntimeError):
    """Base error for provenance reader failures."""
    pass


class CommitNotFoundError(ProvenanceReadError):
    """Raised when a commit SHA does not exist in the Git repository."""
    pass


class FileNotFoundAtCommitError(ProvenanceReadError):
    """Raised when a path does not exist in a commit tree."""
    pass


class PathSecurityError(ProvenanceReadError):
    """Raised when a path attempts traversal, is absolute, or contains escaping patterns."""
    pass


def validate_safe_relative_path(rel_path: str | Path) -> str:
    """
    Validates that a path is safe and strictly relative within the target repo.
    Rejects:
    - Absolute paths (POSIX / or Windows drive letters like C:)
    - Parent directory traversal components ('..')
    - Empty paths
    """
    path_str = str(rel_path).replace("\\", "/").strip()
    if not path_str:
        raise PathSecurityError("Empty relative path rejected.")

    # Rejection of absolute paths
    if path_str.startswith("/"):
        raise PathSecurityError(f"Absolute path rejected: {rel_path}")

    # Check for drive letters (e.g. C:)
    if len(path_str) > 1 and path_str[1] == ":":
        raise PathSecurityError(f"Absolute path with drive letter rejected: {rel_path}")

    # Strip optional leading ./
    while path_str.startswith("./"):
        path_str = path_str[2:]

    if not path_str:
        raise PathSecurityError("Empty relative path rejected.")

    clean_parts = []
    for part in Path(path_str).parts:
        if part in ("/", "\\", "."):
            continue
        if part == "..":
            raise PathSecurityError(f"Path traversal ('..') rejected: {rel_path}")
        clean_parts.append(part)

    if not clean_parts:
        raise PathSecurityError(f"Path resolves to empty after cleaning: {rel_path}")

    clean_path = "/".join(clean_parts)
    return clean_path


def verify_commit_exists(repo_root: Path | str, commit_sha: str) -> bool:
    """Checks if a 40-character commit SHA exists as a commit object in repo_root."""
    if not isinstance(commit_sha, str) or not HEX_SHA_REGEX.match(commit_sha.strip()):
        return False

    sha = commit_sha.strip()
    try:
        subprocess.check_call(
            ["git", "-C", str(repo_root), "cat-file", "-e", f"{sha}^{{commit}}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def read_repo_file_at_commit(repo_root: Path | str, commit_sha: str, rel_path: str | Path) -> bytes:
    """
    Reads raw bytes of a file from a Git commit object without checking out the worktree.
    Enforces safe relative paths and valid commit objects.
    """
    clean_path = validate_safe_relative_path(rel_path)
    if not isinstance(commit_sha, str) or not HEX_SHA_REGEX.match(commit_sha.strip()):
        raise CommitNotFoundError(f"Invalid commit SHA format: '{commit_sha}'")

    sha = commit_sha.strip()
    repo_path = Path(repo_root).resolve()
    if not repo_path.exists():
        raise ProvenanceReadError(f"Repository directory does not exist: {repo_path}")

    if not verify_commit_exists(repo_path, sha):
        raise CommitNotFoundError(f"Commit '{sha}' does not exist in repo '{repo_path}'")

    cmd = ["git", "-C", str(repo_path), "cat-file", "-p", f"{sha}:{clean_path}"]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode("utf-8", errors="replace").strip()
        raise FileNotFoundAtCommitError(
            f"Object '{clean_path}' not found at commit '{sha}' in '{repo_path}': {err_msg}"
        ) from e


def verify_content_hash(blob_bytes: bytes, recorded_hash: str) -> Tuple[bool, str, str, str]:
    """
    Cryptographically verifies blob bytes against a recorded SHA-256 hash.

    Computes:
    - canonical_hash: SHA-256 of the exact Git blob bytes (canonical Git repository object).
    - crlf_hash: SHA-256 of blob bytes converted with standard CRLF checkout line endings.
      (Preserves historical Windows checkout compatibility without weakening integrity).

    Returns:
    - is_match: True if recorded_hash matches either canonical_hash or crlf_hash.
    - match_mode: 'CANONICAL_GIT_BLOB', 'CRLF_CHECKOUT_TRANSFORM', or 'HASH_MISMATCH'.
    - canonical_hash: Hex digest of canonical blob.
    - crlf_hash: Hex digest of CRLF checkout blob.
    """
    canonical_hash = hashlib.sha256(blob_bytes).hexdigest()
    if b"\n" in blob_bytes:
        crlf_bytes = blob_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        crlf_hash = hashlib.sha256(crlf_bytes).hexdigest()
    else:
        crlf_hash = canonical_hash

    if recorded_hash == canonical_hash:
        return True, "CANONICAL_GIT_BLOB", canonical_hash, crlf_hash
    elif recorded_hash == crlf_hash:
        return True, "CRLF_CHECKOUT_TRANSFORM", canonical_hash, crlf_hash
    else:
        return False, "HASH_MISMATCH", canonical_hash, crlf_hash
