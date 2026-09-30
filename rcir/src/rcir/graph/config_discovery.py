"""
Configuration-Mediated Service Discovery for RCIR (v7 §10 Tier 2).

Parses infrastructure manifests (Kubernetes manifests, Kustomize, Helm, and
Docker Compose) to extract service and deployment definitions, linking
services through environment variables and service-discovery hostnames.

Supported manifests:
1. Kubernetes (v1/apps/v1):
   - kind: Service (name, ports, selectors)
   - kind: Deployment (name, containers, env vars)
2. Docker Compose (compose / docker-compose.yml):
   - services.<name> (image, ports, environment)

Anti-Fabrication & Zero-Cloud Guarantee (§0.1, §3):
- Pure local YAML parsing via PyYAML with regex fallback.
- Zero external socket connections or cloud metadata API calls.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rcir.graph.edges import Edge, make_edge

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


@dataclass
class K8sPort:
    name: str
    port: int
    target_port: int | str = 0
    protocol: str = "TCP"


@dataclass
class K8sService:
    file_path: str
    name: str
    ports: list[K8sPort] = field(default_factory=list)
    selector: dict[str, str] = field(default_factory=dict)
    service_type: str = "ClusterIP"


@dataclass
class K8sDeployment:
    file_path: str
    name: str
    containers: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class ComposeService:
    file_path: str
    name: str
    ports: list[str] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    image: str = ""


@dataclass
class ConfigDiscoveryResult:
    services: list[K8sService] = field(default_factory=list)
    deployments: list[K8sDeployment] = field(default_factory=list)
    compose_services: list[ComposeService] = field(default_factory=list)
    files_scanned: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def service_names(self) -> set[str]:
        names = {s.name for s in self.services}
        names.update(c.name for c in self.compose_services)
        return names


def _strip_port(host_port: str) -> str:
    """Extract bare hostname from host:port or URL."""
    cleaned = re.sub(r"^https?://", "", host_port.strip())
    cleaned = cleaned.split("/")[0]
    return cleaned.split(":")[0]


def parse_config_services(
    repo_path: Path | str,
    exclude_dirs: set[str] | None = None,
) -> ConfigDiscoveryResult:
    """Scan a repository for Kubernetes manifests and Docker Compose files.

    Args:
        repo_path: Root of the repository.
        exclude_dirs: Optional directories to skip.

    Returns:
        ConfigDiscoveryResult containing extracted services and deployments.
    """
    repo = Path(repo_path).resolve()
    result = ConfigDiscoveryResult()

    skip_dirs = {
        ".git", "node_modules", "vendor", "bin", "obj", "__pycache__",
        "venv", ".venv", "build", "dist",
    }
    if exclude_dirs:
        skip_dirs.update(exclude_dirs)

    manifest_files: list[Path] = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        for f in files:
            if f.endswith((".yaml", ".yml")):
                manifest_files.append(Path(root) / f)

    def _manifest_sort_key(p: Path) -> tuple[int, int, str]:
        rel = p.relative_to(repo).as_posix()
        is_canonical = 0 if (
            rel.startswith("kubernetes-manifests/")
            or rel.startswith("k8s/")
            or "docker-compose" in rel
        ) else 1
        return (is_canonical, len(rel.split("/")), rel)

    manifest_files.sort(key=_manifest_sort_key)

    seen_services: set[str] = set()
    seen_deployments: set[str] = set()
    seen_compose: set[str] = set()

    for manifest_file in manifest_files:
        try:
            rel_path = manifest_file.relative_to(repo).as_posix()
            content = manifest_file.read_text(encoding="utf-8", errors="replace")

            # Quick pre-filter: only process if file mentions Kubernetes or Compose terms
            if not any(k in content for k in ("kind:", "services:", "apiVersion:")):
                continue

            result.files_scanned += 1
            _parse_manifest_content(content, rel_path, result, seen_services, seen_deployments, seen_compose)
        except Exception as e:
            result.errors.append(f"{manifest_file}: {e}")

    return result


def _parse_manifest_content(
    content: str,
    file_path: str,
    result: ConfigDiscoveryResult,
    seen_services: set[str],
    seen_deployments: set[str],
    seen_compose: set[str],
) -> None:
    """Parse YAML content using PyYAML or regex fallback."""
    if _HAS_YAML:
        try:
            documents = yaml.safe_load_all(content)
            for doc in documents:
                if not isinstance(doc, dict):
                    continue
                _process_yaml_document(doc, file_path, result, seen_services, seen_deployments, seen_compose)
            return
        except Exception:
            # Fall back to regex parsing on malformed or templated YAML
            pass

    _regex_fallback_parse(content, file_path, result, seen_services, seen_deployments)


def _process_yaml_document(
    doc: dict[str, Any],
    file_path: str,
    result: ConfigDiscoveryResult,
    seen_services: set[str],
    seen_deployments: set[str],
    seen_compose: set[str],
) -> None:
    """Process a single parsed YAML dictionary."""
    kind = doc.get("kind")
    if kind == "Service":
        name = doc.get("metadata", {}).get("name")
        if name and name not in seen_services:
            seen_services.add(name)
            spec = doc.get("spec", {})
            ports: list[K8sPort] = []
            for p in spec.get("ports", []):
                if isinstance(p, dict) and "port" in p:
                    ports.append(K8sPort(
                        name=p.get("name", ""),
                        port=int(p["port"]),
                        target_port=p.get("targetPort", 0),
                        protocol=p.get("protocol", "TCP"),
                    ))
            selector = spec.get("selector", {}) if isinstance(spec.get("selector"), dict) else {}
            svc_type = spec.get("type", "ClusterIP")
            result.services.append(K8sService(
                file_path=file_path,
                name=name,
                ports=ports,
                selector=selector,
                service_type=svc_type,
            ))

    elif kind == "Deployment":
        name = doc.get("metadata", {}).get("name")
        if name and name not in seen_deployments:
            seen_deployments.add(name)
            spec = doc.get("spec", {})
            template_spec = spec.get("template", {}).get("spec", {})
            containers = template_spec.get("containers", [])
            container_names = []
            env_vars: dict[str, str] = {}
            for c in containers:
                if isinstance(c, dict):
                    cname = c.get("name")
                    if cname:
                        container_names.append(cname)
                    for env_entry in c.get("env", []):
                        if isinstance(env_entry, dict) and "name" in env_entry and "value" in env_entry:
                            env_vars[str(env_entry["name"])] = str(env_entry["value"])

            labels = doc.get("metadata", {}).get("labels", {})
            result.deployments.append(K8sDeployment(
                file_path=file_path,
                name=name,
                containers=container_names,
                env_vars=env_vars,
                labels=labels if isinstance(labels, dict) else {},
            ))

    # Docker Compose format: top-level 'services' dict
    elif "services" in doc and isinstance(doc["services"], dict):
        for svc_name, svc_cfg in doc["services"].items():
            if isinstance(svc_cfg, dict) and svc_name not in seen_compose:
                seen_compose.add(svc_name)
                ports = [str(p) for p in svc_cfg.get("ports", [])]
                env_dict: dict[str, str] = {}
                raw_env = svc_cfg.get("environment", {})
                if isinstance(raw_env, dict):
                    env_dict = {str(k): str(v) for k, v in raw_env.items()}
                elif isinstance(raw_env, list):
                    for item in raw_env:
                        if "=" in str(item):
                            k, v = str(item).split("=", 1)
                            env_dict[k.strip()] = v.strip()
                image = str(svc_cfg.get("image", ""))
                result.compose_services.append(ComposeService(
                    file_path=file_path,
                    name=svc_name,
                    ports=ports,
                    environment=env_dict,
                    image=image,
                ))


def _regex_fallback_parse(
    content: str,
    file_path: str,
    result: ConfigDiscoveryResult,
    seen_services: set[str],
    seen_deployments: set[str],
) -> None:
    """Regex-based fallback for templated or non-standard YAML files."""
    service_matches = re.finditer(
        r'kind:\s*Service\b.*?metadata:\s*.*?name:\s*([a-zA-Z0-9_-]+)',
        content,
        re.DOTALL,
    )
    for m in service_matches:
        name = m.group(1).strip()
        if name not in seen_services:
            seen_services.add(name)
            result.services.append(K8sService(file_path=file_path, name=name))

    dep_matches = re.finditer(
        r'kind:\s*Deployment\b.*?metadata:\s*.*?name:\s*([a-zA-Z0-9_-]+)',
        content,
        re.DOTALL,
    )
    for m in dep_matches:
        name = m.group(1).strip()
        if name not in seen_deployments:
            seen_deployments.add(name)
            result.deployments.append(K8sDeployment(file_path=file_path, name=name))


def config_nodes_from_discovery_result(result: ConfigDiscoveryResult) -> list[dict]:
    """Generate hierarchy nodes from config discovery results."""
    nodes = []
    for svc in result.services:
        nodes.append({
            "path": f"{svc.file_path}::{svc.name}",
            "kind": "config_service",
            "level": "service",
            "line": 1,
            "end_line": 1,
            "ports": [p.port for p in svc.ports],
            "service_type": svc.service_type,
        })

    for dep in result.deployments:
        nodes.append({
            "path": f"{dep.file_path}::{dep.name}",
            "kind": "config_deployment",
            "level": "service",
            "line": 1,
            "end_line": 1,
            "containers": dep.containers,
        })

    for cs in result.compose_services:
        nodes.append({
            "path": f"{cs.file_path}::{cs.name}",
            "kind": "config_service",
            "level": "service",
            "line": 1,
            "end_line": 1,
            "ports": cs.ports,
        })

    return nodes


def config_edges_from_discovery_result(result: ConfigDiscoveryResult) -> list[Edge]:
    """Generate dependency graph edges from configuration mappings.

    Edges generated:
    1. Deployment -> Service (when a deployment's env var targets another service)
    2. Deployment -> Service (selector matching: Service selects Deployment pods)
    """
    edges: list[Edge] = []
    service_by_name: dict[str, K8sService] = {s.name: s for s in result.services}
    for cs in result.compose_services:
        if cs.name not in service_by_name:
            # Map compose service to a dummy K8sService for uniform resolution
            service_by_name[cs.name] = K8sService(file_path=cs.file_path, name=cs.name)

    # 1. Environment variable mediation (e.g. PRODUCT_CATALOG_SERVICE_ADDR: "productcatalogservice:3550")
    for dep in result.deployments:
        source_node = f"{dep.file_path}::{dep.name}"
        for env_name, env_val in dep.env_vars.items():
            bare_host = _strip_port(env_val)
            if bare_host in service_by_name:
                target_svc = service_by_name[bare_host]
                target_node = f"{target_svc.file_path}::{target_svc.name}"
                edges.append(make_edge(
                    source=source_node,
                    target=target_node,
                    edge_type="config_service",
                    resolution="static_exact",
                    reason=(
                        f"Config-mediated service discovery: {dep.name} configures "
                        f"{env_name}='{env_val}', targeting Service '{target_svc.name}'"
                    ),
                ))

    # Compose environment variable mediation
    for cs in result.compose_services:
        source_node = f"{cs.file_path}::{cs.name}"
        for env_name, env_val in cs.environment.items():
            bare_host = _strip_port(env_val)
            if bare_host in service_by_name and bare_host != cs.name:
                target_svc = service_by_name[bare_host]
                target_node = f"{target_svc.file_path}::{target_svc.name}"
                edges.append(make_edge(
                    source=source_node,
                    target=target_node,
                    edge_type="config_service",
                    resolution="static_exact",
                    reason=(
                        f"Docker Compose service discovery: {cs.name} configures "
                        f"{env_name}='{env_val}', targeting Service '{target_svc.name}'"
                    ),
                ))

    # 2. Service-to-Deployment selector binding (e.g. Service 'frontend' selects Deployment 'frontend')
    for svc in result.services:
        svc_node = f"{svc.file_path}::{svc.name}"
        if svc.selector:
            for dep in result.deployments:
                # Check if deployment labels match service selector
                if all(dep.labels.get(k) == v for k, v in svc.selector.items()):
                    dep_node = f"{dep.file_path}::{dep.name}"
                    edges.append(make_edge(
                        source=svc_node,
                        target=dep_node,
                        edge_type="implements",
                        resolution="static_exact",
                        reason=f"Service '{svc.name}' selects Deployment '{dep.name}' via labels {svc.selector}",
                    ))

    return edges
