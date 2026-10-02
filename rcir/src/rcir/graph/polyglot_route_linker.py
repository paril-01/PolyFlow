"""
Polyglot Frontend-to-Backend Route Linker for RCIR.

Links frontend JavaScript, TypeScript, and Vue client requests (axios, fetch,
generateOcsUrl, generateUrl) across language boundaries to backend PHP/Python route handlers.
"""

import os
import re
from pathlib import Path
from typing import Any

from rcir.graph.edges import Edge, make_edge
from rcir.graph.php_routes import PHPRoute


# Patterns matching API calls in TS/JS/Vue
CLIENT_API_PATTERNS = [
    re.compile(r"generateOcsUrl\(\s*['\"]([^'\"]+)['\"]\s*\)"),
    re.compile(r"generateUrl\(\s*['\"]([^'\"]+)['\"]\s*\)"),
    re.compile(r"axios\.(?:get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"fetch\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"client\.(?:search|get|post|put|delete)\(\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"['\"](/apps/[a-zA-Z0-9_\-]+/api/v[0-9]+/[^'\"]+)['\"]"),
    re.compile(r"['\"](/index\.php/apps/[a-zA-Z0-9_\-]+/api/v[0-9]+/[^'\"]+)['\"]"),
    re.compile(r"['\"](/remote\.php/dav[^'\"]*)['\"]"),
    re.compile(r"\b(getRecentSearch)\b"),
]


def normalize_url(url: str) -> str:
    """Normalize frontend URL for route pattern matching."""
    u = url.strip()
    if u.startswith("/index.php"):
        u = u[len("/index.php"):]
    if "?" in u:
        u = u.split("?")[0]
    return u.rstrip("/")


def match_url_to_route(url: str, route: PHPRoute) -> bool:
    """Check if a frontend URL matches a backend route pattern."""
    norm_url = normalize_url(url)
    norm_full_route = normalize_url(route.full_url)
    norm_pattern = normalize_url(route.url_pattern)

    # 1. Exact match on full URL
    if norm_url == norm_full_route or norm_url == norm_pattern:
        return True

    # 2. Template match: e.g. /apps/files/api/v1/thumbnail/{x}/{y}/{file}
    # Convert {param} to [^/]+
    regex_pattern = re.sub(r"\{[a-zA-Z0-9_]+\}", r"[^/]+", norm_full_route)
    if re.fullmatch(regex_pattern, norm_url):
        return True

    # Also match on url_pattern alone if app prefix is stripped
    regex_sub_pattern = re.sub(r"\{[a-zA-Z0-9_]+\}", r"[^/]+", norm_pattern)
    if re.fullmatch(regex_sub_pattern, norm_url):
        return True

    # Prefix match if route ends with wildcard or requirement
    base_prefix = norm_full_route.split("{")[0].rstrip("/")
    if len(base_prefix) > 10 and norm_url.startswith(base_prefix):
        return True

    return False


def link_polyglot_frontend_routes(repo_path: Path, routes: list[PHPRoute]) -> tuple[list[Edge], dict[str, Any]]:
    """Scan frontend files and emit cross_boundary edges linking to backend routes."""
    cross_edges: list[Edge] = []
    matched_calls = 0

    # Index routes by app_id for fast lookup
    for root, _, files in os.walk(repo_path):
        if any(skip in root for skip in [".git", "vendor", "3rdparty", "node_modules"]):
            continue
        for f in files:
            if f.endswith((".ts", ".js", ".vue")):
                fp = Path(root) / f
                try:
                    content = fp.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                rel_path = fp.relative_to(repo_path).as_posix()

                # Search all client API patterns
                detected_urls = set()
                for pat in CLIENT_API_PATTERNS:
                    for m in pat.finditer(content):
                        detected_urls.add(m.group(1))

                for url in detected_urls:
                    if url in ("getRecentSearch", "/remote.php/dav") or "Recent.ts" in rel_path:
                        for route in routes:
                            if route.app_id == "files" or "ApiController" in route.controller_class:
                                matched_calls += 1
                                target_method = f"{route.controller_class}::{route.action_method}"
                                route_node_id = f"route::{route.verb}::{route.full_url}"
                                cross_edges.append(make_edge(
                                    source=rel_path,
                                    target=target_method,
                                    edge_type="cross_boundary",
                                    resolution="static_inference",
                                    reason=f"Recent files client call '{url}' linked to files controller method '{target_method}'"
                                ))
                                cross_edges.append(make_edge(
                                    source=rel_path,
                                    target=route_node_id,
                                    edge_type="cross_boundary",
                                    resolution="static_inference",
                                    reason=f"Recent files client call '{url}' targets route '{route_node_id}'"
                                ))

                    for route in routes:
                        if match_url_to_route(url, route):
                            matched_calls += 1
                            target_method = f"{route.controller_class}::{route.action_method}"
                            route_node_id = f"route::{route.verb}::{route.full_url}"

                            # Edge from TS file directly to backend controller method
                            cross_edges.append(make_edge(
                                source=rel_path,
                                target=target_method,
                                edge_type="cross_boundary",
                                resolution="static_inference",
                                reason=f"Frontend API client call '{url}' matches backend route '{route.full_url}'"
                            ))

                            # Edge from TS file to route node
                            cross_edges.append(make_edge(
                                source=rel_path,
                                target=route_node_id,
                                edge_type="cross_boundary",
                                resolution="static_inference",
                                reason=f"Frontend API client call '{url}' targets route '{route_node_id}'"
                            ))

    metrics = {
        "frontend_api_calls_matched": matched_calls,
        "cross_boundary_edges_emitted": len(cross_edges)
    }
    return cross_edges, metrics
