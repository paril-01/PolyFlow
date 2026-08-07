# Versioning

## Purpose
Define a consistent versioning strategy for all project artifacts.

## Semantic Versioning

All projects follow [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH

MAJOR — Breaking changes (incompatible API changes)
MINOR — New features (backward-compatible)
PATCH — Bug fixes (backward-compatible)
```

## What Constitutes a Breaking Change

- Removing a public API endpoint or function
- Changing a public API's request/response format
- Changing database schema in a non-backward-compatible way
- Changing configuration format or required settings
- Removing a feature

## Version Lifecycle

```
0.1.0 → Initial development, unstable API
0.x.y → Pre-release, API may change
1.0.0 → First stable release
1.x.y → Stable, backward-compatible changes only
2.0.0 → Breaking changes from v1
```

## Pre-release Versions

Use pre-release identifiers for testing:
- `1.0.0-alpha.1` — Early development
- `1.0.0-beta.1` — Feature complete, testing
- `1.0.0-rc.1` — Release candidate
