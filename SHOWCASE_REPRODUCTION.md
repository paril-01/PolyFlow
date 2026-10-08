# Showcase Reproduction & Verification Guide

**Governing Specification:** `POLYFLOW_SINGLE_FINAL_IMPLEMENTATION_PROMPT.md`  
**Execution Environment:** Windows / POSIX, Python 3.10+, Node.js 18+  
**Target Repository Commit:** `3a29cebe9732f91c60d4dd78844d8a5d0039104e` (HEAD)

---

## 1. Environment Setup

### Required Dependencies
Ensure the following core Python libraries are installed:
```bash
pip install fastapi uvicorn pydantic pytest
```

---

## 2. Running Verification & Anti-Fabrication Test Suite

Run the full automated test suite verifying feature closure, claim consistency, proof integrity, and runtime execution:

```bash
pytest tests/ -v
```

All 19+ tests will run and assert cryptographic integrity, zero synthetic passes, and empirical valid pair accounting.

---

## 3. Regenerating Evidence & Derived CSV Artifacts

To recompile all empirical JSON artifacts and generate the 9 required CSV files:

```bash
python scripts/build_showcase_data.py
python scripts/build_run_exports.py
python showcase/scripts/verify_showcase.py
```

Output files will be produced under:
- `experiments/runs/run_20261009_blind_verified/`
- `showcase/data/csv/`
- `rcir/visualizer-react/public/data/csv/`

---

## 4. Running the Showcase Application

### Option A: Unified FastAPI Backend + Minimal Live UI (Recommended)
```bash
python scripts/run_showcase.py
```
Then navigate to:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

### Option B: React Visualizer Dev Server (Optional / Secondary)
```bash
cd rcir/visualizer-react
npm run dev
```
Navigate to:
[http://localhost:5173](http://localhost:5173)

---

## 5. Live Presentation Walkthrough

1. **Tab 01 (PolyFlow)**:
   - Inspect the left column displaying 12 native ERPNext artifacts (JS, Python, DocType JSON).
   - Inspect the right column showing the unified `sales_invoice.poly` (142 LOC).
   - Hover over any native file to observe bidirectional symbol highlighting in the `.poly` specification.
   - Click **View Proof** to inspect the source file.

2. **Tab 02 (Interpreter)**:
   - Click **Run Normal Flow**: observe live SSE-driven packet animation across Parser → Schema Guard → Cell Scheduler → Polyglot Cells → Merge → Signed Receipt. Verify latency (~8 ms) and cryptographic hash.
   - Click **Run Failure Flow**: observe controlled live failure injection in `tax_calculation` (-18% out-of-bounds rate), graceful fallback activation, and honest `DEGRADED` status with verifiable receipt.

3. **Tab 03 (RCIR)**:
   - In **How it works**, execute a search query (e.g., *"Find accounting ledger entry calculation"*). Inspect the top 5 ranked files with structural dependency justifications.
   - Switch to **Tokens Comparison**: review the empirical side-by-side comparison under blind benchmark conditions (3 valid pairs, 2 timeouts, 0/5 completions on `qwen2.5-coder:1.5b`).

4. **Tab 04 (Proofs)**:
   - Review registered proof files in the allow-listed registry.
   - Click **Preview** or **Download** on any of the 9 CSV exports (`run_summary.csv`, `paired_token_usage.csv`, `feature_closure.csv`, etc.).

5. **Tab 05 (ERPNext)**:
   - Inspect the enterprise scale metrics: 840 DocType schemas, 842 Poly features, 712,940 LOC.
   - Expand the domain hierarchy and inspect structural layer coverage vs local fixture behavioral parity.
