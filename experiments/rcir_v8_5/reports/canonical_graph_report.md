# RCIR v8.5 — Canonical Graph Integrity Report

## Graph Topology
- **Total Nodes**: `NOT_MEASURED`
- **Total Edges**: `NOT_MEASURED`
- **Total Endpoints**: `NOT_MEASURED`

## Endpoint Resolution Breakdown
- **Internal Endpoints**: `NOT_MEASURED`
- **External Endpoints**: `NOT_MEASURED`
- **Unresolved Endpoints**: `NOT_MEASURED`
- **Unexpected External Ratio**: `NOT_MEASURED`

## Legacy Normalizer Architectural Fix
The `LegacyEndpointNormalizer` guarantees:
1. Internal Nextcloud namespaces (`OC\`, `OCP\`, `OCA\`) never become `external://`.
2. Relative repository file paths resolve to `php://<rel_path>`.
3. Special symbols like `php://__construct` route to `unresolved://php::__construct` rather than colliding with built-in streams.
