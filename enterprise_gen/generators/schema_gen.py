"""
Schema Generator — SQL migrations, Protobuf, GraphQL SDL, OpenAPI specs.
"""

import random
from pathlib import Path
from enterprise_gen.config import FEATURE_DOMAINS, ScaleConfig


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _snake_to_camel(s: str) -> str:
    return "".join(w.capitalize() for w in s.split("_"))


def generate_schemas(output_dir: Path, scale: ScaleConfig, rng: random.Random):
    """Generate SQL, Proto, GraphQL, and OpenAPI schemas."""
    schema_dir = output_dir / "shared-schema"
    proto_dir = output_dir / "shared-proto"
    total = 0

    # SQL Migrations
    migration_idx = 1
    for domain in FEATURE_DOMAINS:
        if domain.language in ("typescript", "hcl"):
            continue
        fc = max(1, int(len(domain.features) * scale.feature_multiplier * 0.3))
        for feat_id in domain.features[:fc]:
            sql = f"""-- Migration {migration_idx:04d}: Create {feat_id} table
-- Domain: {domain.name} | Service: {domain.service}

CREATE TABLE IF NOT EXISTS {feat_id} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_{feat_id}_status ON {feat_id}(status);
CREATE INDEX idx_{feat_id}_created_at ON {feat_id}(created_at);
"""
            _write(schema_dir / "migrations" / f"V{migration_idx:04d}__{feat_id}.sql", sql)
            migration_idx += 1
            total += 1

    # Protobuf definitions
    for domain in FEATURE_DOMAINS:
        if domain.language in ("typescript", "hcl", "javascript"):
            continue
        fc = max(1, int(len(domain.features) * scale.feature_multiplier * 0.2))
        for feat_id in domain.features[:fc]:
            cls = _snake_to_camel(feat_id)
            proto = f'''syntax = "proto3";
package ecp.{domain.name};
option go_package = "github.com/ecp/shared-proto/{domain.name}";
option java_package = "com.ecp.proto.{domain.name}";

message {cls}Request {{
  string id = 1;
  string timestamp = 2;
  map<string, string> metadata = 3;
}}

message {cls}Response {{
  string id = 1;
  string status = 2;
  double processing_time_ms = 3;
}}

service {cls}Service {{
  rpc Execute ({cls}Request) returns ({cls}Response);
}}
'''
            _write(proto_dir / domain.name / f"{feat_id}.proto", proto)
            total += 1

    # GraphQL SDL
    gql_types = []
    gql_queries = []
    gql_mutations = []
    for domain in FEATURE_DOMAINS:
        fc = max(1, int(len(domain.features) * scale.feature_multiplier * 0.15))
        for feat_id in domain.features[:fc]:
            cls = _snake_to_camel(feat_id)
            gql_types.append(f"type {cls} {{\n  id: ID!\n  status: String!\n  createdAt: DateTime!\n}}\n")
            gql_queries.append(f"  {feat_id}(id: ID!): {cls}")
            gql_mutations.append(f"  execute{cls}(input: JSON!): {cls}")

    gql_schema = "scalar DateTime\nscalar JSON\n\n"
    gql_schema += "\n".join(gql_types[:50])  # Cap at 50 for readability
    gql_schema += "\n\ntype Query {\n" + "\n".join(gql_queries[:50]) + "\n}\n"
    gql_schema += "\ntype Mutation {\n" + "\n".join(gql_mutations[:50]) + "\n}\n"
    _write(schema_dir / "graphql" / "schema.graphql", gql_schema)
    total += 1

    print(f"  [OK] Generated {total} schema files (SQL, Proto, GraphQL)")
    return total
