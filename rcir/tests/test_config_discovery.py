"""
Tests for Configuration-Mediated Service Discovery (v7 §10 Tier 2).
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rcir.graph.config_discovery import (
    parse_config_services,
    config_edges_from_discovery_result,
    config_nodes_from_discovery_result,
    ConfigDiscoveryResult,
    K8sService,
    K8sDeployment,
    ComposeService,
)


def test_parse_k8s_manifests(tmp_path):
    k8s_file = tmp_path / "orders.yaml"
    k8s_file.write_text("""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  labels:
    app: order-service
spec:
  template:
    spec:
      containers:
      - name: server
        env:
        - name: PAYMENT_ADDR
          value: "payment-service:50051"
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
  labels:
    app: order-service
spec:
  selector:
    app: order-service
  ports:
  - port: 8080
    targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: payment-service
spec:
  ports:
  - port: 50051
""")

    result = parse_config_services(tmp_path)
    assert len(result.services) == 2
    assert len(result.deployments) == 1
    assert "order-service" in result.service_names
    assert "payment-service" in result.service_names

    edges = config_edges_from_discovery_result(result)
    assert len(edges) >= 2

    # Verify env mediation: order-service -> payment-service
    env_edge = next(e for e in edges if e.edge_type == "config_service")
    assert "order-service" in env_edge.source
    assert "payment-service" in env_edge.target
    assert env_edge.resolution == "static_exact"

    # Verify selector edge: Service 'order-service' selects Deployment 'order-service'
    impl_edge = next(e for e in edges if e.edge_type == "implements")
    assert "order-service" in impl_edge.source
    assert "order-service" in impl_edge.target


def test_parse_docker_compose(tmp_path):
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("""
version: '3.8'
services:
  web:
    image: web:latest
    ports:
      - "80:80"
    environment:
      - API_URL=api:8000
  api:
    image: api:latest
    ports:
      - "8000:8000"
""")

    result = parse_config_services(tmp_path)
    assert len(result.compose_services) == 2
    assert "web" in result.service_names
    assert "api" in result.service_names

    edges = config_edges_from_discovery_result(result)
    assert len(edges) >= 1
    edge = edges[0]
    assert "web" in edge.source
    assert "api" in edge.target
    assert edge.edge_type == "config_service"
