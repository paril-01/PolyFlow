# CLI Tool Project — Architecture Phase

## ADR-001: CLI Framework
**Decision**: Click (Python) — mature, well-documented, clean API for building CLI tools.

## ADR-002: Analysis Architecture
**Decision**: Plugin-based analyzer architecture — each analysis type (complexity, duplication, docs) is an independent plugin, making it easy to add new analyzers.

## Architecture

```mermaid
graph TD
    CLI[Click CLI Interface] --> Scanner[File Scanner]
    Scanner --> Analyzer[Analyzer Engine]
    Analyzer --> Complexity[Complexity Analyzer]
    Analyzer --> Duplication[Duplication Analyzer]
    Analyzer --> Docs[Documentation Analyzer]
    Analyzer --> Reporter[Report Generator]
    Reporter --> Terminal[Terminal Output]
    Reporter --> JSON[JSON File Output]
```
