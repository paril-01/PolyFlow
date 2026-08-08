"""
Documentation Generator — ADRs, RFCs, READMEs, architecture docs.
CI/CD Generator — GitHub Actions workflows.
Technical Debt Injector — Injects realistic tech debt patterns.
Bug Seeder — Seeds intentional bugs across the codebase.
Git History Simulator — Generates simulated commit metadata.
"""

import random
import hashlib
import time as _time
from pathlib import Path
from enterprise_gen.config import (
    SERVICES, FEATURE_DOMAINS, DEVELOPERS, DEBT_TEMPLATES,
    BUG_TEMPLATES, ScaleConfig, CALL_CHAINS
)


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ============================================================================
# DOCUMENTATION GENERATOR
# ============================================================================

def generate_docs(output_dir: Path, scale: ScaleConfig, rng: random.Random):
    """Generate ADRs, RFCs, READMEs, and architecture docs."""
    docs_dir = output_dir / "docs"
    total = 0

    # ADRs
    adr_topics = [
        ("Use PostgreSQL as primary datastore", "Database", "We need ACID compliance and JSON support."),
        ("Adopt gRPC for inter-service communication", "Communication", "REST has too much overhead for internal calls."),
        ("Use JWT for authentication tokens", "Security", "Stateless auth enables horizontal scaling."),
        ("Adopt event-driven architecture for notifications", "Architecture", "Decouples notification from core flows."),
        ("Use Redis for session caching", "Performance", "In-memory caching reduces DB load by 80%."),
        ("Implement CQRS for order service", "Architecture", "Separate read/write models for scalability."),
        ("Use Terraform for infrastructure", "DevOps", "Infrastructure as code enables reproducibility."),
        ("Adopt trunk-based development", "Process", "Short-lived branches reduce merge conflicts."),
        ("Use feature flags for gradual rollouts", "Process", "Reduces risk of big-bang deployments."),
        ("Implement circuit breakers", "Resilience", "Prevents cascade failures across services."),
        ("Use Prometheus + Grafana for monitoring", "Observability", "Open-source stack with broad ecosystem."),
        ("Adopt OpenAPI for API documentation", "Documentation", "Machine-readable API specs."),
        ("Use Kubernetes for container orchestration", "Infrastructure", "Industry standard for container management."),
        ("Implement rate limiting at gateway", "Security", "Prevents abuse and DDoS."),
        ("Use Kafka for event streaming", "Architecture", "High throughput, durable event bus."),
        ("Adopt semantic versioning", "Process", "Clear versioning communicates breaking changes."),
        ("Use connection pooling for databases", "Performance", "Reduces connection overhead."),
        ("Implement structured logging", "Observability", "JSON logs enable automated parsing."),
        ("Use content-based routing in gateway", "Architecture", "Routes requests based on content type."),
        ("Adopt blue-green deployments", "DevOps", "Zero-downtime deployments."),
    ]
    adr_count = min(scale.adr_count, len(adr_topics))
    for i, (title, category, context) in enumerate(adr_topics[:adr_count], 1):
        dev = rng.choice(DEVELOPERS)
        _write(docs_dir / "adr" / f"ADR-{i:04d}-{title.lower().replace(' ','-')[:40]}.md", f"""# ADR-{i:04d}: {title}

## Status
Accepted

## Context
{context}

## Decision
We will {title.lower()}.

## Category
{category}

## Author
{dev['name']} ({dev['email']})

## Date
2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}

## Consequences
- Positive: Improves {category.lower()} capabilities
- Negative: Adds operational complexity
- Risks: Team needs training on new technology
""")
        total += 1

    # RFCs
    rfc_topics = [
        "Implement distributed tracing across all services",
        "Add support for multi-tenancy",
        "Migrate from REST to GraphQL for frontend APIs",
        "Implement data lake for analytics",
        "Add support for WebSocket real-time notifications",
    ]
    for i, topic in enumerate(rfc_topics[:max(1, scale.adr_count // 4)], 1):
        _write(docs_dir / "rfc" / f"RFC-{i:04d}.md", f"# RFC-{i:04d}: {topic}\n\n## Summary\n{topic}\n\n## Motivation\nImprove system capabilities.\n\n## Proposal\nDetailed technical proposal.\n\n## Status\nDraft\n")
        total += 1

    # Architecture docs
    _write(docs_dir / "architecture" / "overview.md", f"""# ECP Architecture Overview

## Services
{chr(10).join(f'- **{s.name}**: {s.description} ({s.language}/{s.framework})' for s in SERVICES)}

## Call Chains
{chr(10).join(f'- **{c["name"]}**: {c["description"]}' for c in CALL_CHAINS)}

## Technology Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Angular 17, Flutter |
| Gateway | Go + Chi + GraphQL |
| Backend | Spring Boot 3, FastAPI, Express |
| ML/AI | scikit-learn, Transformers, FAISS |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Queue | Kafka, Bull |
| Infrastructure | Terraform, Kubernetes, Docker |
| Monitoring | Prometheus, Grafana |
| CI/CD | GitHub Actions |
""")
    total += 1

    print(f"  [OK] Generated {total} documentation files (ADRs, RFCs, Architecture)")
    return total


# ============================================================================
# CI/CD GENERATOR
# ============================================================================

def generate_cicd(output_dir: Path, scale: ScaleConfig, rng: random.Random):
    """Generate GitHub Actions workflows."""
    gh_dir = output_dir / ".github" / "workflows"
    total = 0

    for svc in SERVICES:
        lang = svc.language
        test_cmd = {
            "python": "pytest tests/ -v --cov=app",
            "go": "go test ./... -v -race",
            "java": "./mvnw test",
            "javascript": "npm test",
            "typescript": "npm test",
            "dart": "flutter test",
        }.get(lang, "echo 'No tests'")

        _write(gh_dir / f"ci-{svc.name}.yml", f"""name: CI - {svc.name}
on:
  push:
    paths: ['{svc.name}/**']
  pull_request:
    paths: ['{svc.name}/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Run tests
      working-directory: {svc.name}
      run: {test_cmd}

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Build Docker image
      run: docker build -t ecp/{svc.name}:${{{{ github.sha }}}} ./{svc.name}
""")
        total += 1

    # Deploy workflow
    _write(gh_dir / "deploy.yml", """name: Deploy to Production
on:
  workflow_dispatch:
    inputs:
      service:
        description: 'Service to deploy'
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Deploy
      run: |
        echo "Deploying ${{ github.event.inputs.service }}"
        # kubectl apply -f kubernetes/deployments/${{ github.event.inputs.service }}.yaml
""")
    total += 1

    print(f"  [OK] Generated {total} CI/CD workflow files")
    return total


# ============================================================================
# TECHNICAL DEBT INJECTOR
# ============================================================================

def inject_technical_debt(output_dir: Path, scale: ScaleConfig, rng: random.Random):
    """Inject intentional technical debt into the generated codebase."""
    total = 0
    debt_count = scale.debt_items

    # Dead APIs
    _write(output_dir / "gateway-go" / "internal" / "handler" / "legacy_orders_v0.go", '''package handler

// DEPRECATED: This handler is no longer used. It was part of the v0 API.
// TODO: Remove in next major version (tracked in JIRA-4521)

import "net/http"

func LegacyOrdersV0Handler(w http.ResponseWriter, r *http.Request) {
\tw.Write([]byte(`{"error":"deprecated endpoint"}`))
}
''')
    total += 1

    # Duplicate utility
    _write(output_dir / "order-service-go" / "internal" / "util" / "string_utils.go", 'package util\n\nfunc TrimAndLower(s string) string { return s }\nfunc SanitizeInput(s string) string { return s }\n')
    _write(output_dir / "order-service-go" / "internal" / "util" / "string_helpers.go", 'package util\n\n// DUPLICATE: Same as string_utils.go — someone didn\'t check\nfunc TrimAndLowerCase(s string) string { return s }\nfunc CleanInput(s string) string { return s }\n')
    total += 2

    # Unreachable React page
    _write(output_dir / "frontend-react" / "src" / "pages" / "OldDashboard.tsx", '''import React from 'react';
// WARNING: This page has no route pointing to it.
// It was part of the v1 dashboard that was replaced in Sprint 23.
export const OldDashboard: React.FC = () => {
  return <div className="p-8"><h1>Old Dashboard (Unreachable)</h1></div>;
};
export default OldDashboard;
''')
    total += 1

    # Config drift
    _write(output_dir / "kubernetes" / "config" / "staging.yml", 'database_pool_size: 10\nredis_ttl: 300\nlog_level: DEBUG\nfeature_new_checkout: true\n')
    _write(output_dir / "kubernetes" / "config" / "production.yml", '# WARNING: config drift — pool_size differs from staging\ndatabase_pool_size: 25\nredis_ttl: 600\nlog_level: INFO\nfeature_new_checkout: false  # Should this still be false?\n')
    total += 2

    # Copy-pasted class
    for svc in ["payment-service-java", "order-service-go"]:
        if "java" in svc:
            _write(output_dir / svc / "src" / "main" / "java" / "com" / "ecp" / svc.replace("-","") / "util" / "OrderValidator.java",
                   f'package com.ecp.{svc.replace("-","")}.util;\n\n// COPY-PASTE: This class is duplicated across services\npublic class OrderValidator {{\n    public boolean validate(String orderId) {{\n        return orderId != null && !orderId.isEmpty();\n    }}\n}}\n')
            total += 1

    # Hidden feature flag
    _write(output_dir / "frontend-react" / "src" / "utils" / "featureFlags.ts", '''// Hidden feature flags — NOT in the flag management system
export const HIDDEN_FLAGS = {
  ENABLE_EXPERIMENTAL_CHECKOUT: process.env.REACT_APP_EXP_CHECKOUT === 'true',
  ENABLE_AI_RECOMMENDATIONS: true, // Hardcoded, should be managed
  DARK_MODE_BETA: false,
};
''')
    total += 1

    # Stale documentation
    _write(output_dir / "docs" / "api-reference" / "STALE_endpoints.md", '''# API Endpoints (STALE)

> WARNING: This document references endpoints that no longer exist.
> Last updated: 2023-01-15

- `POST /api/v0/orders/create` — REMOVED in v1.0
- `GET /api/v0/users/profile` — MOVED to `/api/v1/auth/profile`
- `DELETE /api/v0/inventory/purge` — REMOVED for safety
''')
    total += 1

    # Duplicate SQL migration
    _write(output_dir / "shared-schema" / "migrations" / "V9990__duplicate_index.sql", '-- DUPLICATE: This migration creates an index that already exists in V0003\nCREATE INDEX IF NOT EXISTS idx_order_create_status ON order_create(status);\n')
    total += 1

    print(f"  [OK] Injected {total} technical debt items")
    return total


# ============================================================================
# BUG SEEDER
# ============================================================================

def seed_bugs(output_dir: Path, scale: ScaleConfig, rng: random.Random):
    """Seed intentional bugs across the codebase."""
    total = 0
    target = scale.bug_count

    lang_svc_map = {
        "python": ["inventory-python", "pricing-python", "recommendation-python", "ai-service-python"],
        "java": ["auth-service-java", "payment-service-java", "analytics-java"],
        "go": ["gateway-go", "order-service-go"],
        "javascript": ["notification-node"],
        "typescript": ["frontend-react"],
    }

    bugs_per_lang = target // len(BUG_TEMPLATES)

    for lang, templates in BUG_TEMPLATES.items():
        services = lang_svc_map.get(lang, [])
        if not services:
            continue

        for i in range(min(bugs_per_lang, len(templates) * len(services))):
            tmpl = templates[i % len(templates)]
            svc = rng.choice(services)
            bug_id = f"bug_{lang}_{tmpl['type']}_{i+1}"

            if lang == "python":
                _write(output_dir / svc / "app" / "services" / f"_buggy_{bug_id}.py", tmpl["code"] + "\n")
            elif lang == "java":
                cls = "".join(w.capitalize() for w in bug_id.split("_"))
                pkg = svc.replace("-", "")
                _write(output_dir / svc / "src" / "main" / "java" / "com" / "ecp" / pkg / "buggy" / f"{cls}.java",
                       f'package com.ecp.{pkg}.buggy;\n\nimport java.util.*;\n\npublic class {cls} {{\n{tmpl["code"]}\n}}\n')
            elif lang == "go":
                _write(output_dir / svc / "internal" / "buggy" / f"{bug_id}.go", f'package buggy\n\nimport "os"\n\n{tmpl["code"]}\n')
            elif lang in ("javascript", "typescript"):
                ext = "ts" if lang == "typescript" else "js"
                _write(output_dir / svc / "src" / "buggy" / f"{bug_id}.{ext}", tmpl["code"] + "\n")

            total += 1
            if total >= target:
                break
        if total >= target:
            break

    print(f"  [OK] Seeded {total} intentional bugs across the codebase")
    return total


# ============================================================================
# GIT HISTORY SIMULATOR
# ============================================================================

def simulate_git_history(output_dir: Path, scale: ScaleConfig, rng: random.Random):
    """Generate simulated git history as metadata files (commits, PRs, issues)."""
    git_dir = output_dir / "docs" / "git-history"
    total = 0

    # Commit log
    commit_types = ["feat", "fix", "refactor", "chore", "docs", "test", "perf", "ci"]
    commits = []
    dev_count = min(scale.developer_count, len(DEVELOPERS))
    devs = DEVELOPERS[:dev_count]

    for i in range(scale.commit_count):
        dev = rng.choice(devs)
        ctype = rng.choice(commit_types)
        domain = rng.choice(FEATURE_DOMAINS)
        feat = rng.choice(domain.features)
        sha = hashlib.sha1(f"commit-{i}".encode()).hexdigest()[:7]
        day_offset = i * (1095 / max(scale.commit_count, 1))  # Spread over 3 years
        commits.append(f"{sha} | {ctype}: {feat.replace('_',' ')} [{domain.service}] | {dev['name']} <{dev['email']}>")

    _write(git_dir / "commit_log.txt", "\n".join(commits) + "\n")
    total += 1

    # PRs
    prs = []
    for i in range(1, scale.pr_count + 1):
        dev = rng.choice(devs)
        domain = rng.choice(FEATURE_DOMAINS)
        feat = rng.choice(domain.features)
        prs.append(f"PR-{i:04d} | {feat.replace('_',' ')} | {dev['name']} | {domain.service} | {'merged' if rng.random() > 0.15 else 'closed'}")
    _write(git_dir / "pull_requests.txt", "\n".join(prs) + "\n")
    total += 1

    # Issues
    issue_types = ["bug", "feature", "enhancement", "documentation", "performance"]
    issues = []
    for i in range(1, scale.issue_count + 1):
        dev = rng.choice(devs)
        itype = rng.choice(issue_types)
        domain = rng.choice(FEATURE_DOMAINS)
        status = rng.choice(["open", "closed", "in-progress"])
        issues.append(f"ISSUE-{i:04d} | [{itype}] {domain.name} issue | {dev['name']} | {status}")
    _write(git_dir / "issues.txt", "\n".join(issues) + "\n")
    total += 1

    print(f"  [OK] Generated simulated git history ({scale.commit_count} commits, {scale.pr_count} PRs, {scale.issue_count} issues)")
    return total


# ============================================================================
# BENCHMARK HARNESS
# ============================================================================

def generate_benchmark(output_dir: Path, scale: ScaleConfig, rng: random.Random):
    """Generate the benchmark query framework."""
    bench_dir = output_dir / "benchmark"

    _write(bench_dir / "README.md", """# ECP Benchmark Harness

Run PolyFlow against the Enterprise Commerce Platform to measure:
- **Lineage tracing**: Can PolyFlow trace a variable across 5+ languages?
- **Impact analysis**: Can PolyFlow estimate blast radius of a change?
- **Bug detection**: Can PolyFlow find seeded bugs?
- **Dead code detection**: Can PolyFlow identify unreachable endpoints?
- **Tech debt detection**: Can PolyFlow find duplicates and drift?
""")

    queries = [
        {"id": "Q001", "type": "lineage",   "query": "Where does discount_percentage originate?", "expected_services": ["pricing-python", "order-service-go", "frontend-react"]},
        {"id": "Q002", "type": "impact",     "query": "Which deployments break if PaymentService changes?", "expected_services": ["payment-service-java", "order-service-go", "notification-node"]},
        {"id": "Q003", "type": "refactor",   "query": "Rename OrderStatus to FulfillmentStatus — estimate blast radius", "expected_entities": ["order-service-go", "frontend-react", "shared-proto", "shared-schema"]},
        {"id": "Q004", "type": "bug",        "query": "Find SQL injection vulnerabilities", "expected_count": 3},
        {"id": "Q005", "type": "dead_code",  "query": "List unreachable API endpoints", "expected": ["LegacyOrdersV0Handler", "OldDashboard"]},
        {"id": "Q006", "type": "duplicate",  "query": "Find duplicate utility functions across services", "expected": ["string_utils.go", "string_helpers.go"]},
        {"id": "Q007", "type": "docs",       "query": "Which ADRs are contradicted by current implementation?", "expected": []},
        {"id": "Q008", "type": "chain",      "query": "Trace the customer_purchase_flow call chain end-to-end", "expected_languages": 5},
        {"id": "Q009", "type": "config",     "query": "Find configuration drift between staging and production", "expected": ["database_pool_size", "feature_new_checkout"]},
        {"id": "Q010", "type": "security",   "query": "Find hardcoded secrets or tokens", "expected_count": 2},
    ]

    import json
    _write(bench_dir / "queries.json", json.dumps(queries, indent=2))

    _write(bench_dir / "run_benchmark.py", '''"""ECP Benchmark Runner — Tests PolyFlow against the enterprise platform."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def main():
    with open(os.path.join(os.path.dirname(__file__), "queries.json")) as f:
        queries = json.load(f)

    print("=" * 70)
    print("ECP BENCHMARK — PolyFlow Enterprise Analysis")
    print("=" * 70)

    for q in queries:
        print(f"\\n[{q['id']}] ({q['type'].upper()}) {q['query']}")
        print(f"  Status: PENDING — Run PolyFlow analysis to evaluate")

    print(f"\\n{'=' * 70}")
    print(f"Total queries: {len(queries)}")
    print(f"Types: {', '.join(set(q['type'] for q in queries))}")

if __name__ == "__main__":
    main()
''')

    print(f"  [OK] Generated benchmark harness with {len(queries)} query templates")
    return len(queries)
