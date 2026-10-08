# PolyFlow Evidence-First Showcase Application

A minimalist, high-fidelity presentation interface and FastAPI evidence server demonstrating:
1. **PolyFlow Unified Architecture**: Unifying 12 scattered native ERPNext artifacts into 1 modular `.poly` feature entry point.
2. **PolyCell Multi-Language Interpreter**: Real-time SSE-driven execution of native Python and JavaScript cells with contract validation, graceful fallback handling, and cryptographic SHA-256 receipts.
3. **RCIR Context Retrieval**: Live structural AST and dependency graph context compiler versus blind unassisted baselines (3 valid pairs, 2 timeouts, zero synthetic passes).
4. **Verified Proof Library**: Strict allow-listed proof registry with path-traversal protection and one-click downloads for 9 derived CSV datasets.
5. **ERPNext Enterprise Scale**: Comprehensive structural mapping of 840 DocType schemas, 842 Poly features, and 712,940 lines of code across 5 business domains.

---

## Architecture Overview

```text
showcase_app/
  backend/
    app.py                           # FastAPI application entry point
    schemas.py                       # Pydantic typed request & response models
    services/
      evidence_registry.py           # Path-traversal guarded proof resolver
      interpreter_service.py         # Real PolyCellRuntime execution & SSE streamer
      feature_service.py             # Feature closure & layer mapping provider
      rcir_service.py                # Structural candidate retrieval & ranking
      benchmark_service.py           # Benchmark telemetry & CSV exporter
      erpnext_service.py             # Enterprise scale tree provider
    api/
      health.py                      # GET /api/health
      features.py                    # GET /api/features/*
      interpreter.py                 # POST /api/interpreter/runs, SSE /events
      rcir.py                        # POST /api/rcir/queries, GET /pipeline
      proofs.py                      # GET /api/proofs/*, GET /api/benchmarks/*
      erpnext.py                     # GET /api/erpnext/*
  frontend/
    index.html                       # 5-tab minimalist HTML structure
    css/
      base.css                       # Color tokens, typography, dark mode
      layout.css                     # Header, navigation, and 2-column grids
      components.css                 # Metric cards, code views, workflow diagrams
      responsive.css                 # Mobile & tablet layout breakpoints
    js/
      polyflow.js                    # Tab 01: Native vs Feature View
      interpreter.js                 # Tab 02: Real-time workflow & SSE
      rcir.js                        # Tab 03: Pipeline & token telemetry
      proofs.js                      # Tab 04: CSV export hub & proof registry
      erpnext.js                     # Tab 05: Domain tree & scale explorer
      app.js                         # Application coordinator
```

---

## Quick Start

### 1. Launch the Backend Server

```bash
python scripts/run_showcase.py
```
Or directly with Uvicorn:
```bash
uvicorn showcase_app.backend.app:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser to:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

### 2. Available CSV Exports
The following 9 CSV files are generated from empirical run artifacts and served at `/data/csv/<file>` and `/api/benchmarks/...`:
- `run_summary.csv`
- `paired_token_usage.csv`
- `agent_trials.csv`
- `retrieved_files.csv`
- `feature_closure.csv`
- `source_mappings.csv`
- `interpreter_events.csv`
- `runtime_receipts.csv`
- `coverage_ledger.csv`

---

## Compliance with Rule 0
- **Zero Synthetic Numbers**: All latencies, tokens, lines of code, and hashes derive from real files and live runtime executions.
- **Fail-Closed Security**: `evidence_registry.py` strictly verifies file existence within the repository boundary and matches SHA-256 digests prior to serving.
