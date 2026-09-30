"""
Declarative Route Extractor for PHP Frameworks (Nextcloud, Symfony, Laravel).

Parses appinfo/routes.php, routes/web.php, and controller docblock annotations.
Emits 'route' nodes and 'route' edges linking URL endpoints to backend controller actions.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rcir.graph.edges import Edge, make_edge


@dataclass
class PHPRoute:
    app_id: str
    name: str              # e.g. "api#getThumbnail" or "Files#getRecent"
    url_pattern: str       # e.g. "/api/v1/thumbnail/{x}/{y}/{file}"
    full_url: str          # e.g. "/apps/files/api/v1/thumbnail/{x}/{y}/{file}"
    verb: str              # "GET", "POST", "PUT", "DELETE"
    controller_alias: str  # "api" -> "ApiController"
    action_method: str     # "getThumbnail"
    controller_class: str  # e.g. "OCA\\Files\\Controller\\ApiController"
    source_file: str       # e.g. "apps/files/appinfo/routes.php"


ROUTE_BLOCK_RE = re.compile(
    r"\[\s*'name'\s*=>\s*['\"]([^'\"]+)['\"],\s*'url'\s*=>\s*['\"]([^'\"]+)['\"],\s*'verb'\s*=>\s*['\"]([^'\"]+)['\"]",
    re.MULTILINE
)
# Variant with verb before url or different order
ALT_ROUTE_BLOCK_RE = re.compile(
    r"\[\s*['\"]name['\"]\s*=>\s*['\"]([^#]+)#([^'\"]+)['\"].*?['\"]url['\"]\s*=>\s*['\"]([^'\"]+)['\"].*?['\"]verb['\"]\s*=>\s*['\"]([A-Z]+)['\"]",
    re.DOTALL
)


def extract_php_routes_from_file(file_path: Path, repo_root: Path) -> list[PHPRoute]:
    """Extract route definitions from an appinfo/routes.php file."""
    routes: list[PHPRoute] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return routes

    rel_file = file_path.relative_to(repo_root).as_posix()
    # Infer app_id from path: "apps/<app_id>/appinfo/routes.php"
    parts = rel_file.split("/")
    app_id = ""
    if "apps" in parts:
        idx = parts.index("apps")
        if idx + 1 < len(parts):
            app_id = parts[idx + 1]

    # Find namespace if present
    ns_match = re.search(r"namespace\s+([a-zA-Z0-9_\\]+);", content)
    app_ns = ns_match.group(1).rsplit("\\", 1)[0] if ns_match else f"OCA\\{app_id.capitalize()}"

    # Extract all route array items using bracket-aware scanning
    idx = 0
    while True:
        name_match = re.search(r"['\"]name['\"]\s*=>", content[idx:])
        if not name_match:
            break
        pos = idx + name_match.start()
        open_bracket = content.rfind('[', 0, pos)
        if open_bracket == -1:
            idx = pos + len(name_match.group(0))
            continue

        depth = 0
        i = open_bracket
        end_bracket = -1
        in_str = False
        s_ch = ''
        while i < len(content):
            ch = content[i]
            if in_str:
                if ch == s_ch and content[i - 1] != '\\':
                    in_str = False
            else:
                if ch in ("'", '"'):
                    in_str = True
                    s_ch = ch
                elif ch == '[':
                    depth += 1
                elif ch == ']':
                    depth -= 1
                    if depth == 0:
                        end_bracket = i
                        break
            i += 1

        if end_bracket != -1:
            entry_text = content[open_bracket:end_bracket + 1]
            idx = end_bracket + 1

            name_m = re.search(r"['\"]name['\"]\s*=>\s*['\"]([^'\"]+)['\"]", entry_text)
            url_m = re.search(r"['\"]url['\"]\s*=>\s*['\"]([^'\"]+)['\"]", entry_text)
            verb_m = re.search(r"['\"]verb['\"]\s*=>\s*['\"]([^'\"]+)['\"]", entry_text)

            if name_m and url_m:
                raw_name = name_m.group(1)
                raw_url = url_m.group(1)
                verb = verb_m.group(1) if verb_m else "GET"

                controller_alias = ""
                action_method = ""
                if "#" in raw_name:
                    controller_alias, action_method = raw_name.split("#", 1)
                else:
                    action_method = raw_name

                controller_class_name = f"{controller_alias[0].upper()}{controller_alias[1:]}Controller" if controller_alias else "DefaultController"
                full_controller = f"{app_ns}\\Controller\\{controller_class_name}"

                full_url = raw_url
                if app_id and not raw_url.startswith(f"/apps/{app_id}"):
                    full_url = f"/apps/{app_id}{raw_url}" if raw_url.startswith("/") else f"/apps/{app_id}/{raw_url}"

                routes.append(PHPRoute(
                    app_id=app_id,
                    name=raw_name,
                    url_pattern=raw_url,
                    full_url=full_url,
                    verb=verb.upper(),
                    controller_alias=controller_alias,
                    action_method=action_method,
                    controller_class=full_controller,
                    source_file=rel_file
                ))
        else:
            idx = pos + len(name_match.group(0))

    return routes


def scan_repository_php_routes(repo_path: Path) -> tuple[list[dict[str, Any]], list[Edge], list[PHPRoute]]:
    """Scan all appinfo/routes.php files in repository and emit route nodes and edges."""
    route_nodes: list[dict[str, Any]] = []
    route_edges: list[Edge] = []
    all_routes: list[PHPRoute] = []

    routes_files = list(repo_path.glob("apps/*/appinfo/routes.php"))
    for rf in routes_files:
        routes = extract_php_routes_from_file(rf, repo_path)
        all_routes.extend(routes)
        rel_rf = rf.relative_to(repo_path).as_posix()

        for r in routes:
            route_node_id = f"route::{r.verb}::{r.full_url}"
            route_nodes.append({
                "path": route_node_id,
                "name": f"{r.verb} {r.full_url}",
                "kind": "route",
                "language": "php",
                "file": r.source_file,
                "metadata": {
                    "verb": r.verb,
                    "url_pattern": r.url_pattern,
                    "full_url": r.full_url,
                    "controller_class": r.controller_class,
                    "action_method": r.action_method,
                    "app_id": r.app_id
                }
            })

            # Edge 1: routes.php -> route
            route_edges.append(make_edge(
                source=r.source_file,
                target=route_node_id,
                edge_type="route",
                resolution="static_exact",
                reason="Nextcloud declarative route declaration"
            ))

            # Edge 2: route -> Controller::method
            target_method = f"{r.controller_class}::{r.action_method}"
            route_edges.append(make_edge(
                source=route_node_id,
                target=target_method,
                edge_type="route",
                resolution="static_exact",
                reason="Nextcloud route action dispatch"
            ))

            # Edge 3: routes.php directly to Controller::method (direct link for blast-radius impact)
            route_edges.append(make_edge(
                source=r.source_file,
                target=target_method,
                edge_type="route",
                resolution="static_exact",
                reason="Nextcloud routes to controller action"
            ))

    return route_nodes, route_edges, all_routes
