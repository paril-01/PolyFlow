# RCIR v8.5 — Canonical Graph Integrity Report

## Graph Topology
- **Total Nodes**: `48611`
- **Total Edges**: `143225`
- **Total Endpoints**: `49208`

## Endpoint Resolution Breakdown
- **Internal Endpoints**: `48676` (98.92%)
- **External Endpoints**: `457` (0.93%)
- **Unresolved Endpoints**: `75` (0.15%)
- **Unexpected External Ratio**: `0.0000`

## Legacy Normalizer Architectural Fix
The `LegacyEndpointNormalizer` guarantees:
1. Internal Nextcloud namespaces (`OC\`, `OCP\`, `OCA\`) never become `external://`.
2. Relative repository file paths resolve to `php://<rel_path>`.
3. Special symbols like `php://__construct` route to `unresolved://php::__construct` rather than colliding with built-in streams.
