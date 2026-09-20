"""
Non-code artifact detection and coarse-granularity node creation.

Detects SQL files, YAML/TOML configs, Dockerfiles, Makefiles, etc.
and creates whole-file nodes flagged as 'coarse' granularity (§4.2).

These files don't have function-level AST structure, so they're
represented as single nodes in the hierarchy.
"""

from pathlib import Path
from typing import Any


# File extensions/names → artifact type mapping
COARSE_ARTIFACT_PATTERNS: dict[str, str] = {
    ".sql": "sql",
    ".yaml": "config",
    ".yml": "config",
    ".toml": "config",
    ".ini": "config",
    ".cfg": "config",
    ".json": "data",
    ".xml": "config",
    ".proto": "schema",
    ".graphql": "schema",
    ".gql": "schema",
}

COARSE_ARTIFACT_NAMES: dict[str, str] = {
    "Dockerfile": "docker",
    "docker-compose.yml": "docker",
    "docker-compose.yaml": "docker",
    "Makefile": "build",
    "CMakeLists.txt": "build",
    ".env": "config",
    ".env.example": "config",
    "requirements.txt": "dependency",
    "Pipfile": "dependency",
    "Pipfile.lock": "dependency",
    "pyproject.toml": "dependency",
    "setup.py": "dependency",
    "setup.cfg": "dependency",
    "package.json": "dependency",
    "go.mod": "dependency",
    "go.sum": "dependency",
    "Cargo.toml": "dependency",
}


def detect_coarse_artifacts(repo_path: str | Path) -> list[dict[str, Any]]:
    """Detect non-code artifacts in a repository and create coarse nodes.

    Args:
        repo_path: Path to the repository root.

    Returns:
        List of coarse-granularity node dicts.
    """
    repo_path = Path(repo_path).resolve()
    if not repo_path.is_dir():
        return []

    skip_dirs = {
        ".git", ".hg", ".svn", "__pycache__", "node_modules",
        ".tox", ".nox", "venv", ".venv", "build", "dist",
    }

    artifacts: list[dict[str, Any]] = []
    import os

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for fname in files:
            artifact_type = None

            # Check by exact name
            if fname in COARSE_ARTIFACT_NAMES:
                artifact_type = COARSE_ARTIFACT_NAMES[fname]
            else:
                # Check by extension
                suffix = Path(fname).suffix.lower()
                if suffix in COARSE_ARTIFACT_PATTERNS:
                    artifact_type = COARSE_ARTIFACT_PATTERNS[suffix]

            if artifact_type:
                full_path = Path(root) / fname
                try:
                    rel_path = full_path.relative_to(repo_path).as_posix()
                except ValueError:
                    rel_path = str(full_path)

                # Read file size for metadata
                try:
                    size_bytes = full_path.stat().st_size
                except OSError:
                    size_bytes = 0

                artifacts.append({
                    "path": rel_path,
                    "kind": "artifact",
                    "level": "file",
                    "granularity": "coarse",
                    "artifact_type": artifact_type,
                    "size_bytes": size_bytes,
                })

    return artifacts
