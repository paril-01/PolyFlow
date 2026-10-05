# RCIR v8.4 Canonical Graph & Entity Registry Report

**Repository**: `nextcloud-server`  
**Total Canonical Nodes**: 48,611  
**Total Evaluated Edges**: 143,225  
**Canonical URI Scheme**: `php://<Namespace>\<Class>::<symbol>`, `ts://<file>::<symbol>`, `external://<symbol>`  

## 1. Canonicalization Accuracy
- **Test Ingest Cases**: 12
- **Correct Canonical URIs**: 12
- **Canonicalization Accuracy**: **100.0%**
- **Disambiguation**: Method endpoints are never conflated with enclosing file paths; file aliases resolve cleanly to `EntityKind.FILE`.

## 2. Resolution Ledger Accounting
Every edge in the canonical graph is classified into one of 6 mutually exclusive resolution classes:
- `STATIC_EXACT`: Definite compiler-resolved symbol bindings.
- `STATIC_INFERENCE`: Inferred receivers via lexical type flow and PHPDoc types.
- `AMBIGUOUS`: Polymorphic dispatch with multiple viable candidate implementations.
- `DYNAMIC_UNRESOLVED`: Reflection, dynamic string calls (`$class->$method()`).
- `UNSUPPORTED`: Language features not yet supported by static extractors.
- `NOT_ANALYZED`: Uninspected third-party libraries.
