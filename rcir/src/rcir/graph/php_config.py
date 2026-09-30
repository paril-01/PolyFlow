"""
Configuration Dependency Extractor for PHP & Framework Applications (Nextcloud).

Extracts configuration definitions from config.php, docker-compose.yml, and environment manifests,
and detects configuration access in application code ($config->getSystemValue, $config->getValue).
Emits 'config' nodes and 'config' dependency edges.
"""

import os
import re
from pathlib import Path
from typing import Any

from rcir.graph.edges import Edge, make_edge


# Config reader call patterns in PHP code
CONFIG_GET_PATTERNS = [
    re.compile(r"->getSystemValue\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"->getValue\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"->setSystemValue\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"->getAppValue\(\s*['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]"),
]


def extract_config_keys_from_php_configs(repo_path: Path) -> dict[str, list[str]]:
    """Extract known configuration keys from Nextcloud configuration files."""
    keys_to_sources: dict[str, list[str]] = {}

    config_files = list(repo_path.glob("config/*.php")) + list(repo_path.glob("tests/*.config.php")) + list(repo_path.glob("tests/preseed-config.php"))

    for cf in config_files:
        try:
            content = cf.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = cf.relative_to(repo_path).as_posix()

        # Find keys in $CONFIG array: 'key' => ...
        for m in re.finditer(r"['\"]([a-zA-Z0-9_\-\.]+)['\"]\s*=>", content):
            key = m.group(1)
            if key not in ("routes", "name", "url", "verb"):
                keys_to_sources.setdefault(key, []).append(rel)

    return keys_to_sources


def scan_php_config_dependencies(repo_path: Path) -> tuple[list[dict[str, Any]], list[Edge], dict[str, Any]]:
    """Scan codebase for config access and emit config nodes and edges."""
    config_nodes: list[dict[str, Any]] = []
    config_edges: list[Edge] = []
    keys_to_sources = extract_config_keys_from_php_configs(repo_path)

    # Add config nodes for known keys
    all_accessed_keys: set[str] = set()

    for root, _, files in os.walk(repo_path):
        if any(skip in root for skip in [".git", "vendor", "3rdparty", "node_modules"]):
            continue
        for f in files:
            if f.endswith(".php"):
                fp = Path(root) / f
                try:
                    content = fp.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                rel_path = fp.relative_to(repo_path).as_posix()

                for pat in CONFIG_GET_PATTERNS:
                    for m in pat.finditer(content):
                        key = m.group(1)
                        all_accessed_keys.add(key)
                        node_id = f"config::{key}"

                        # Edge from PHP file/service to the config key
                        config_edges.append(make_edge(
                            source=rel_path,
                            target=node_id,
                            edge_type="config",
                            resolution="static_exact",
                            reason=f"Code queries configuration key '{key}' via IConfig"
                        ))

    # Create config nodes
    for key in sorted(all_accessed_keys | set(keys_to_sources.keys())):
        sources = keys_to_sources.get(key, [])
        config_nodes.append({
            "path": f"config::{key}",
            "name": f"Config: {key}",
            "kind": "config",
            "language": "php",
            "file": sources[0] if sources else "config/config.php",
            "metadata": {
                "key": key,
                "defined_in": sources
            }
        })

    metrics = {
        "config_keys_found": len(config_nodes),
        "config_dependency_edges": len(config_edges)
    }
    return config_nodes, config_edges, metrics
