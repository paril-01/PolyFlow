"""
Infrastructure Generator — Terraform, Kubernetes, Helm, Docker, Prometheus, Grafana.
"""

import random
from pathlib import Path
from enterprise_gen.config import SERVICES, ScaleConfig


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_infrastructure(output_dir: Path, scale: ScaleConfig, rng: random.Random):
    """Generate Terraform, K8s manifests, Helm charts, Prometheus rules, Grafana dashboards."""
    total = 0

    # --- Terraform Modules --------------------------
    tf_dir = output_dir / "terraform"
    _write(tf_dir / "main.tf", '''terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.30" }
  }
}

provider "aws" {
  region = var.aws_region
}

module "vpc" { source = "./modules/vpc" }
module "ecs" { source = "./modules/ecs", vpc_id = module.vpc.vpc_id }
module "rds" { source = "./modules/rds", vpc_id = module.vpc.vpc_id }
module "redis" { source = "./modules/redis", vpc_id = module.vpc.vpc_id }
''')
    _write(tf_dir / "variables.tf", 'variable "aws_region" {\n  default = "us-east-1"\n}\nvariable "environment" {\n  default = "production"\n}\n')
    _write(tf_dir / "outputs.tf", 'output "vpc_id" {\n  value = module.vpc.vpc_id\n}\n')
    total += 3

    for mod in ["vpc", "ecs", "rds", "redis", "s3", "cloudfront", "iam"]:
        _write(tf_dir / "modules" / mod / "main.tf", f'# Terraform module: {mod}\nresource "aws_{mod}" "main" {{\n  # Configuration\n}}\n')
        _write(tf_dir / "modules" / mod / "variables.tf", f'variable "vpc_id" {{\n  type = string\n  default = ""\n}}\n')
        _write(tf_dir / "modules" / mod / "outputs.tf", f'output "{mod}_id" {{\n  value = "placeholder"\n}}\n')
        total += 3

    # Unused terraform module (tech debt)
    _write(tf_dir / "modules" / "unused-cdn" / "main.tf", '# DEPRECATED: This module is no longer used\nresource "aws_cloudfront_distribution" "legacy" {\n  # Old CDN config\n}\n')
    total += 1

    # --- Kubernetes Manifests -----------------------
    k8s_dir = output_dir / "kubernetes"
    for svc in SERVICES:
        if svc.port == 0:
            continue
        # Deployment
        _write(k8s_dir / "deployments" / f"{svc.name}.yaml", f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {svc.name}
  namespace: ecp
  labels:
    app: {svc.name}
    team: {svc.team}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {svc.name}
  template:
    metadata:
      labels:
        app: {svc.name}
    spec:
      containers:
      - name: {svc.name}
        image: ecp/{svc.name}:latest
        ports:
        - containerPort: {svc.port}
        env:
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: {svc.port}
          initialDelaySeconds: 30
          periodSeconds: 10
''')
        # Service
        _write(k8s_dir / "services" / f"{svc.name}-svc.yaml", f'''apiVersion: v1
kind: Service
metadata:
  name: {svc.name}
  namespace: ecp
spec:
  selector:
    app: {svc.name}
  ports:
  - port: {svc.port}
    targetPort: {svc.port}
  type: ClusterIP
''')
        total += 2

    # Ingress
    _write(k8s_dir / "ingress.yaml", '''apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ecp-ingress
  namespace: ecp
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: api.ecp.dev
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: gateway-go
            port:
              number: 8080
''')
    total += 1

    # Helm chart
    _write(k8s_dir / "helm" / "ecp" / "Chart.yaml", 'apiVersion: v2\nname: ecp\ndescription: Enterprise Commerce Platform\nversion: 1.5.0\nappVersion: "2.4.1"\n')
    _write(k8s_dir / "helm" / "ecp" / "values.yaml", 'replicaCount: 3\nimage:\n  repository: ecp\n  tag: latest\nresources:\n  limits:\n    cpu: 500m\n    memory: 512Mi\n')
    total += 2

    # --- Monitoring ---------------------------------
    mon_dir = output_dir / "monitoring"
    _write(mon_dir / "prometheus" / "rules.yaml", '''groups:
- name: ecp-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate on {{ $labels.service }}"
  - alert: HighLatency
    expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 10m
    labels:
      severity: warning
''')
    _write(mon_dir / "grafana" / "dashboard.json", '{"dashboard": {"title": "ECP Overview", "panels": [{"type": "graph", "title": "Request Rate"}]}}')
    total += 2

    print(f"  [OK] Generated {total} infrastructure files (Terraform, K8s, Helm, Monitoring)")
    return total
