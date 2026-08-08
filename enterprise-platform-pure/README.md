# Pure PolyFlow Enterprise Platform

This enterprise platform uses **Pure PolyFlow Architecture**.

## Architectural Highlights
- **Single Source of Truth**: **100% of feature code lives inside `.poly` files** (281 modules). There are NO redundant standalone `.go`, `.java`, `.py`, or `.ts` boilerplate files scattered across directories.
- **Fast In-Memory Native Engine**: Executes multi-language cell code directly in-memory with sub-millisecond latency (<0.1ms).
- **Embedded Security & Audit**: Guards A-F enforcement and cryptographic SHA-256 Merkle ledger block sealing are executed automatically on every feature call.

## Structure
- `features/`: All 281 `.poly` feature modules categorized by business domain.
- `engine.py`: Fast In-Memory PolyFlow Server and API Gateway (`http://localhost:9090`).

## Run & Test
```bash
# 1. Validate all .poly modules
python -m polyflow validate features/

# 2. Boot the Pure PolyFlow Engine Server
python engine.py 9090
```
